"""Few-shot extraction helpers for P3+ inference runs."""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from equipment_ie.llm_labeling import (
    canonical_json,
    extract_first_json_object,
    sha256_text,
)
from equipment_ie.schema import SchemaError, validate_record


class ExtractionParseError(ValueError):
    """Raised when model output cannot be parsed into the unified schema."""


@dataclass(frozen=True)
class MicroCounts:
    true_positive: int
    false_positive: int
    false_negative: int

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        precision = self.precision
        recall = self.recall
        denominator = precision + recall
        return 2 * precision * recall / denominator if denominator else 0.0

    def report(self) -> dict[str, float | int]:
        return {
            "tp": self.true_positive,
            "fp": self.false_positive,
            "fn": self.false_negative,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
        }


def occurrence_index(text: str, span: str, start: int) -> int:
    """Return the 1-based occurrence index for a span start."""

    cursor = 0
    occurrence = 0
    while True:
        found = text.find(span, cursor)
        if found < 0:
            raise SchemaError(f"span {span!r} does not occur in text")
        occurrence += 1
        if found == start:
            return occurrence
        cursor = found + 1


def record_as_model_json(record: Mapping[str, Any], *, include_relations: bool) -> dict[str, Any]:
    """Represent one gold record in the occurrence-based model JSON format."""

    validate_record(record)
    entities = [
        {
            "span": entity["span"],
            "type": entity["type"],
            "occurrence": occurrence_index(record["text"], entity["span"], entity["start"]),
        }
        for entity in record["entities"]
    ]
    relations = list(record["relations"]) if include_relations else []
    return {"entities": entities, "relations": relations}


def select_fixed_random_examples(
    support_records: Sequence[Mapping[str, Any]], *, k: int, seed: int
) -> list[dict[str, Any]]:
    """Select one deterministic fixed-random K-shot example set."""

    if k <= 0:
        raise ValueError("k must be positive")
    candidates = [dict(record) for record in support_records if record.get("entities")]
    if len(candidates) < k:
        raise ValueError(f"need at least {k} support records with entities")
    rng = random.Random(seed)
    selected = rng.sample(candidates, k)
    return sorted(selected, key=lambda record: str(record["id"]))


def build_ner_prompt(
    *,
    query_text: str,
    entity_types: Mapping[str, str],
    examples: Sequence[Mapping[str, Any]],
    include_relations: bool = False,
    glossary_entries: Sequence[str] | None = None,
    rag_passages: Sequence[str] | None = None,
    output_instruction: str = "只返回JSON,不要任何解释,不要markdown代码块",
) -> str:
    """Build the P3 prompt blocks in the required order."""

    if not entity_types:
        raise ValueError("entity_types must not be empty")
    blocks = [
        "任务定义：从给定文本中抽取命名实体，实体必须是原文中的连续片段。",
        "Schema：\n"
        + "\n".join(f"- {name}: {description}" for name, description in entity_types.items()),
    ]
    if glossary_entries:
        blocks.append("领域术语表：\n" + "\n".join(f"- {entry}" for entry in glossary_entries))
    if rag_passages:
        blocks.append("参考资料：\n" + "\n".join(f"- {passage}" for passage in rag_passages))
    blocks.append(
        "输出格式："
        '{"entities":[{"span":"原文片段","type":"实体类型","occurrence":1}],'
        '"relations":[]}'
        "。occurrence 表示该完全相同片段在原文中从左到右第几次出现，从1开始。"
    )
    blocks.append(
        "硬性输出约束：type 必须逐字等于 Schema 中列出的英文类型之一；禁止输出"
        " Schema 之外的类型，例如 event、person、location、ORG、PER；如果没有"
        "把握或片段不在原文中，宁可不输出；occurrence 不能超过该片段在原文中"
        "实际出现的次数；禁止重叠或嵌套实体；当职位/身份词和人名相邻时，"
        "分别输出 position 与 name，不要输出包含两者的整体片段。"
    )
    for index, example in enumerate(examples, start=1):
        blocks.append(
            f"示例{index}文本：{example['text']}\n示例{index}输出："
            f"{canonical_json(record_as_model_json(example, include_relations=include_relations))}"
        )
    blocks.extend([f"待抽取文本：{query_text}", output_instruction])
    return "\n\n".join(blocks)


def parse_extraction_output(
    raw_output: str,
    *,
    record_id: str,
    text: str,
    entity_types: set[str],
    relation_types: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
    drop_invalid_entities: bool = False,
    sanitization_flags: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Parse occurrence-based extraction JSON into the unified schema."""

    try:
        value = json.loads(extract_first_json_object(raw_output))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"entities", "relations"}:
        raise ExtractionParseError("output must contain entities and relations only")
    raw_entities = value["entities"]
    raw_relations = value["relations"]
    if not isinstance(raw_entities, list) or not isinstance(raw_relations, list):
        raise ExtractionParseError("entities and relations must be lists")

    def flag(kind: str, **details: Any) -> None:
        if sanitization_flags is not None:
            sanitization_flags.append({"kind": kind, **details})

    def drop_or_raise_entity(index: int, reason: str, raw: Any) -> bool:
        if not drop_invalid_entities:
            raise ExtractionParseError(reason)
        flag(
            "ENTITY_DROPPED_INVALID_UNIT",
            entity_raw_index=index,
            reason=reason,
            raw_entity=raw,
        )
        return True

    parsed_entities: list[tuple[int, dict[str, Any]]] = []
    seen_entities: set[tuple[int, int, str]] = set()
    for index, raw in enumerate(raw_entities):
        if not isinstance(raw, dict) or set(raw) != {"span", "type", "occurrence"}:
            if drop_or_raise_entity(index, f"entity {index} must contain span/type/occurrence only", raw):
                continue
        span = raw["span"]
        entity_type = raw["type"]
        occurrence = raw["occurrence"]
        if not isinstance(span, str) or not span:
            if drop_or_raise_entity(index, f"entity {index} span must be non-empty", raw):
                continue
        if entity_type not in entity_types:
            if drop_or_raise_entity(index, f"entity {index} has unsupported type {entity_type!r}", raw):
                continue
        if not isinstance(occurrence, int) or isinstance(occurrence, bool) or occurrence < 1:
            if drop_or_raise_entity(index, f"entity {index} occurrence must be a positive integer", raw):
                continue
        starts = _occurrence_starts(text, span)
        if occurrence > len(starts):
            if drop_or_raise_entity(index, f"entity {index} occurrence not found for {span!r}", raw):
                continue
        start = starts[occurrence - 1]
        end = start + len(span)
        key = (start, end, entity_type)
        if key in seen_entities:
            if drop_or_raise_entity(index, f"entity {index} duplicates {key}", raw):
                continue
        seen_entities.add(key)
        parsed_entities.append((index, {"start": start, "end": end, "type": entity_type, "span": span}))

    if drop_invalid_entities:
        kept: list[tuple[int, dict[str, Any]]] = []
        for raw_index, entity in sorted(
            parsed_entities,
            key=lambda item: (
                -(item[1]["end"] - item[1]["start"]),
                item[1]["start"],
                item[1]["end"],
                item[1]["type"],
            ),
        ):
            if any(
                entity["start"] < kept_entity["end"] and kept_entity["start"] < entity["end"]
                for _, kept_entity in kept
            ):
                flag(
                    "ENTITY_DROPPED_OVERLAP",
                    entity_raw_index=raw_index,
                    reason="overlapping entities are forbidden",
                    entity=entity,
                )
                continue
            kept.append((raw_index, entity))
        parsed_entities = kept

    sort_order = sorted(
        range(len(parsed_entities)),
        key=lambda index: (
            parsed_entities[index][1]["start"],
            parsed_entities[index][1]["end"],
            parsed_entities[index][1]["type"],
        ),
    )
    raw_index_to_sorted = {
        parsed_entities[raw_position][0]: sorted_index
        for sorted_index, raw_position in enumerate(sort_order)
    }
    entities = [parsed_entities[index][1] for index in sort_order]
    for previous, current in zip(entities, entities[1:]):
        if current["start"] < previous["end"]:
            raise ExtractionParseError("overlapping entities are forbidden")

    relation_rules = relation_types or {}
    relations: list[dict[str, Any]] = []
    seen_relations: set[tuple[int, int, str]] = set()
    if raw_relations and not relation_rules:
        if drop_invalid_entities:
            flag(
                "RELATIONS_DROPPED_DISABLED_FOR_CONFIG",
                count=len(raw_relations),
                reason="relations are not enabled for this config",
            )
            raw_relations = []
        else:
            raise ExtractionParseError("relations are not enabled for this config")
    for index, raw in enumerate(raw_relations):
        if not isinstance(raw, dict) or set(raw) != {"head", "tail", "type"}:
            raise ExtractionParseError(f"relation {index} must contain head/tail/type only")
        head = raw["head"]
        tail = raw["tail"]
        relation_type = raw["type"]
        if (
            not isinstance(head, int)
            or isinstance(head, bool)
            or not isinstance(tail, int)
            or isinstance(tail, bool)
            or not 0 <= head < len(raw_entities)
            or not 0 <= tail < len(raw_entities)
        ):
            raise ExtractionParseError(f"relation {index} references a missing entity")
        rule = relation_rules.get(relation_type)
        if rule is None:
            raise ExtractionParseError(f"relation {index} has unsupported type {relation_type!r}")
        if head not in raw_index_to_sorted or tail not in raw_index_to_sorted:
            if drop_invalid_entities:
                flag(
                    "RELATION_DROPPED_REMOVED_ENTITY",
                    relation_raw_index=index,
                    reason="relation endpoint was removed during entity sanitization",
                    raw_relation=raw,
                )
                continue
            raise ExtractionParseError(f"relation {index} references a removed entity")
        sorted_head = raw_index_to_sorted[head]
        sorted_tail = raw_index_to_sorted[tail]
        head_type = entities[sorted_head]["type"]
        tail_type = entities[sorted_tail]["type"]
        if head_type not in rule["head_types"] or tail_type not in rule["tail_types"]:
            raise ExtractionParseError(f"relation {index} violates type matrix")
        key = (sorted_head, sorted_tail, relation_type)
        if key in seen_relations:
            continue
        seen_relations.add(key)
        relations.append({"head": sorted_head, "tail": sorted_tail, "type": relation_type})

    record = {"id": record_id, "text": text, "entities": entities, "relations": relations}
    validate_record(record)
    return record


def entity_micro_counts(
    gold_records: Sequence[Mapping[str, Any]], pred_records: Sequence[Mapping[str, Any]]
) -> MicroCounts:
    """Compute exact span-plus-type entity micro counts."""

    pred_by_id = {record["id"]: record for record in pred_records}
    tp = fp = fn = 0
    for gold in gold_records:
        pred = pred_by_id.get(gold["id"], {"entities": []})
        gold_set = {
            (entity["start"], entity["end"], entity["type"])
            for entity in gold["entities"]
        }
        pred_set = {
            (entity["start"], entity["end"], entity["type"])
            for entity in pred["entities"]
        }
        tp += len(gold_set & pred_set)
        fp += len(pred_set - gold_set)
        fn += len(gold_set - pred_set)
    return MicroCounts(tp, fp, fn)


def build_request_envelope(
    *,
    prompt: str,
    model: str,
    generation: Mapping[str, Any],
    run_id: str,
    config_hash: str,
) -> dict[str, Any]:
    """Build a cache-keyed OpenAI-compatible chat request envelope."""

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(generation["temperature"]),
        "top_p": float(generation["top_p"]),
        "max_tokens": int(generation["max_tokens"]),
        "seed": int(generation["seed"]),
    }
    return {
        "run_id": run_id,
        "config_hash": config_hash,
        "payload": payload,
    }


def prompt_hash(prompt: str) -> str:
    return sha256_text(prompt)


def build_error_retry_prompt(
    *,
    base_prompt: str,
    parse_error: str,
    retry_suffix: str = "只返回合法JSON",
) -> str:
    """Ask the model to fix a concrete parser failure without changing task scope."""

    return (
        f"{base_prompt}\n\n"
        f"上次输出未通过解析，错误是：{parse_error}\n"
        "请只修正这个错误：不要增加解释，不要输出markdown代码块；"
        "实体span必须逐字来自原文，type必须来自Schema，occurrence必须有效，"
        "实体之间不得重叠或嵌套。\n"
        f"{retry_suffix}"
    )


def _occurrence_starts(text: str, span: str) -> list[int]:
    starts: list[int] = []
    cursor = 0
    while True:
        start = text.find(span, cursor)
        if start < 0:
            return starts
        starts.append(start)
        cursor = start + 1
