"""Few-shot extraction helpers for P3+ inference runs."""

from __future__ import annotations

import json
import random
import re
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


def _record_char_bio_labels(record: Mapping[str, Any]) -> list[str]:
    """Encode one validated record as one BIO label per Python character."""

    validate_record(record)
    text = str(record["text"])
    labels = ["O"] * len(text)
    for entity in record["entities"]:
        start = int(entity["start"])
        end = int(entity["end"])
        entity_type = str(entity["type"])
        if start < 0 or end <= start or end > len(text) or text[start:end] != entity["span"]:
            raise SchemaError("entity offsets do not match the record text")
        if any(label != "O" for label in labels[start:end]):
            raise SchemaError("overlapping entities cannot be encoded as BIO")
        labels[start] = f"B-{entity_type}"
        for index in range(start + 1, end):
            labels[index] = f"I-{entity_type}"
    return labels


def record_as_model_json(
    record: Mapping[str, Any],
    *,
    include_relations: bool,
    output_mode: str = "occurrence",
) -> dict[str, Any]:
    """Represent one gold record in the selected model JSON format."""

    validate_record(record)
    if output_mode == "char_bio":
        return {"labels": _record_char_bio_labels(record), "relations": []}
    if output_mode == "span_index":
        entities = [
            {
                "start": int(entity["start"]),
                "end": int(entity["end"]),
                "type": entity["type"],
            }
            for entity in record["entities"]
        ]
    elif output_mode == "occurrence":
        entities = [
            {
                "span": entity["span"],
                "type": entity["type"],
                "occurrence": occurrence_index(record["text"], entity["span"], entity["start"]),
            }
            for entity in record["entities"]
        ]
    else:
        raise ValueError(f"unsupported example output_mode {output_mode!r}")
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


def select_glossary_entries(
    query_text: str,
    glossary_records: Sequence[Mapping[str, Any]],
    *,
    max_entries: int = 20,
) -> list[str]:
    """Select query-matched glossary entries for prompt injection."""

    if max_entries <= 0:
        raise ValueError("max_entries must be positive")
    candidates: list[tuple[int, int, int, int, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(glossary_records):
        term = raw.get("term")
        entity_type = raw.get("type")
        if not isinstance(term, str) or not term.strip():
            continue
        if not isinstance(entity_type, str) or not entity_type.strip():
            continue
        aliases = raw.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        if not isinstance(aliases, Sequence):
            aliases = []
        matched_terms = [term]
        matched_terms.extend(alias for alias in aliases if isinstance(alias, str))
        matched = [candidate for candidate in matched_terms if candidate and candidate in query_text]
        if not matched:
            continue
        display = f"{term}（{entity_type}）"
        if display in seen:
            continue
        priority = raw.get("priority", 0)
        try:
            priority_value = int(priority)
        except (TypeError, ValueError):
            priority_value = 0
        candidates.append(
            (
                priority_value,
                max(len(candidate) for candidate in matched),
                len(term),
                index,
                display,
            )
        )
    candidates.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3], item[4]))
    selected: list[str] = []
    for _, _, _, _, display in candidates:
        if display in seen:
            continue
        seen.add(display)
        selected.append(display)
        if len(selected) >= max_entries:
            break
    return selected


def build_ner_prompt(
    *,
    query_text: str,
    entity_types: Mapping[str, str],
    examples: Sequence[Mapping[str, Any]],
    include_relations: bool = False,
    glossary_entries: Sequence[str] | None = None,
    rag_passages: Sequence[str] | None = None,
    output_instruction: str = "只返回JSON,不要任何解释,不要markdown代码块",
    output_mode: str = "occurrence",
    reference_instruction: str | None = None,
    occurrence_contract_version: str | None = None,
    anchored_contract_version: str | None = None,
    candidate_spans: Sequence[Mapping[str, Any]] | None = None,
    example_output_mode: str | None = None,
    compact_candidate_index: bool = False,
    candidate_index_lattice: Mapping[str, int] | None = None,
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
        reference_block = "参考资料（仅供判断，不得直接复制实体）：\n" + "\n".join(
            f"- {passage}" for passage in rag_passages
        )
        if reference_instruction:
            reference_block += f"\n\n{reference_instruction}"
        blocks.append(reference_block)
    if output_mode == "span_index":
        blocks.append(
            "NER 实体专用输出格式：顶层 JSON 只允许以下两种形式："
            '{"entities":[{"start":0,"end":2,"type":"实体类型"}]} 或 '
            '{"entities":[{"start":0,"end":2,"type":"实体类型"}],"relations":[]}。'
            "禁止其它顶层字段；若省略未使用的 relations，程序仅在 NER-only 模式确定性补充空列表。"
            "start/end 是原文字符下标，start 包含、end 不包含；程序会从原文切片生成 span。"
        )
    elif output_mode == "anchored_span_index":
        blocks.append(
            "Anchored span-index NER output:\n"
            "Each entity must contain exactly start, end, span, and type. start/end are Python Unicode character indices; start is inclusive and end is exclusive.\n"
            "The span must equal text[start:end] character-for-character, including punctuation, brackets, slashes, hyphens, spaces, and suffixes. Do not use tokenizer or byte offsets, aliases, paraphrases, or reference-only text. If unsure, omit the entity.\n"
            "Synthetic example: for query text '雷达A：测试，雷达A：测试', an entity may be {\"start\":0,\"end\":3,\"span\":\"雷达A\",\"type\":\"EQUIPMENT\"}; relations must be []."
        )
    elif output_mode == "occurrence":
        blocks.append(
            "输出格式："
            '{"entities":[{"span":"原文片段","type":"实体类型","occurrence":1}],'
            '"relations":[]}'
            "。occurrence 表示该完全相同片段在原文中从左到右第几次出现，从1开始。"
        )
    elif output_mode == "candidate_index":
        blocks.append(
            "Candidate-index NER output: return candidate_id and type only; candidate_id must be selected from the listed query-local candidates."
        )
    elif output_mode == "char_bio":
        blocks.append(
            "CHAR_BIO_NER_CONTRACT:\n"
            f"Return one JSON label for each Python Unicode character in the final query; labels length must be exactly {len(query_text)}.\n"
            "Allowed labels are exactly O, B-<SCHEMA_TYPE>, and I-<SCHEMA_TYPE>. A B label starts an entity, matching I labels continue it, and O marks non-entity characters.\n"
            "The top-level JSON must contain labels and may contain relations only when relations is an empty array. Do not return spans, offsets, occurrence numbers, candidate IDs, or entities."
        )
    else:
        raise ValueError(f"unsupported output_mode {output_mode!r}")
    if output_mode == "occurrence" and occurrence_contract_version == "occurrence_ner_envelope_v2":
        blocks.append(
            "OCCURRENCE_NER_ENVELOPE_V2_CONTRACT:\n"
            "This is NER-only output. The top-level JSON must contain an entities array; an empty relations array may be omitted. If relations is present, it must be []. Each entity contains only span, type, and occurrence.\n"
            "Copy span character-for-character from the final query text. occurrence counts identical copies from left to right starting at 1. Do not copy entities from reference passages. If unsure, omit the entity."
        )
    if output_mode == "occurrence" and occurrence_contract_version == "occurrence_copy_v2":
        blocks.append(
            "OCCURRENCE_COPY_V2_LITERAL_CONTRACT:\n"
            "The span must be copied character-for-character from the final query text; preserve punctuation, brackets, slashes, hyphens, spaces, and suffixes.\n"
            "Occurrence counts identical copies from left to right starting at 1. Do not output aliases, paraphrases, translations, or text found only in references. If unsure, omit the entity instead of guessing.\n"
            "Synthetic example: query text '雷达A：测试，雷达A：测试' requires two entities with span '雷达A' and occurrence 1 and 2, followed by relations: []. Each entity object has only span/type/occurrence."
        )
    if output_mode == "span_index":
        blocks.append(
            "硬性输出约束：每个实体只输出 start、end、type；start/end 必须是最终待抽取文本的"
            " Python Unicode 字符下标，start 包含、end 不包含。禁止 occurrence、span、候选编号、"
            "重叠或嵌套实体；type 必须逐字等于 Schema 中的英文类型；不确定时宁可省略。"
        )
    elif output_mode != "char_bio":
        blocks.append(
            "硬性输出约束：type 必须逐字等于 Schema 中列出的英文类型之一；禁止输出"
            " Schema 之外的类型，例如 event、person、location、ORG、PER；如果没有"
            "把握或片段不在原文中，宁可不输出；occurrence 不能超过该片段在原文中"
            "实际出现的次数；禁止重叠或嵌套实体；当职位/身份词和人名相邻时，"
            "分别输出 position 与 name，不要输出包含两者的整体片段。"
        )
    if output_mode == "char_bio":
        blocks.append(
            "CHAR_BIO_STRICT_OUTPUT:\n"
            "The label sequence is the only localization channel. Every entity must be a contiguous B-TYPE followed by zero or more matching I-TYPE labels. An I-TYPE without its matching open B-TYPE is invalid."
        )
    if output_mode == "anchored_span_index":
        blocks.append(
            "ANCHORED_SPAN_INDEX_OVERRIDE: occurrence字段在此模式中禁止输出；只输出start、end、span、type。"
            "不要使用occurrence编号。任何start/end与span不一致的实体都不要输出。"
        )
    rendered_example_mode = example_output_mode or ("occurrence" if output_mode == "candidate_index" else output_mode)
    for index, example in enumerate(examples, start=1):
        blocks.append(
            f"示例{index}文本：{example['text']}\n示例{index}输出："
            f"{canonical_json(record_as_model_json(example, include_relations=include_relations, output_mode=rendered_example_mode))}"
        )
    if candidate_spans is not None:
        candidate_entries = (
            "|".join(f"{item['id']}={item['start']}:{item['end']}" for item in candidate_spans)
            if compact_candidate_index
            else "\n".join(f"{item['id']}: {item['span']}" for item in candidate_spans)
        )
        blocks.append(
            "CANDIDATE_INDEX_CONTRACT:\nOnly choose candidate_id values listed below; "
            "the parser maps them to exact query spans.\n"
            + ("Each entry is candidate_id=start:end in Python character offsets.\n" if compact_candidate_index else "")
            + candidate_entries
        )
    if candidate_index_lattice is not None:
        required = {"start", "end", "max_span_chars"}
        if not required.issubset(candidate_index_lattice):
            raise ValueError("candidate_index_lattice requires start, end, and max_span_chars")
        blocks.append(
            "CANDIDATE_INDEX_LATTICE_CONTRACT:\n"
            "Candidate IDs are implicit query-local coordinates in the form cSSSS_EEEE. "
            "Choose only a candidate whose start/end satisfy the declared window and whose "
            "span is the exact final-query slice; the parser validates membership and slicing.\n"
            f"window_start={int(candidate_index_lattice['start'])}; "
            f"window_end={int(candidate_index_lattice['end'])}; "
            f"max_span_chars={int(candidate_index_lattice['max_span_chars'])}"
        )
    blocks.extend([f"待抽取文本：{query_text}", output_instruction])
    return "\n\n".join(blocks)


def _parse_char_bio_output(
    value: Any,
    *,
    record_id: str,
    text: str,
    entity_types: set[str],
    max_entities: int | None = None,
) -> dict[str, Any]:
    """Parse a character-level BIO sequence into exact unified entities."""

    if not isinstance(value, dict) or set(value) not in ({"labels"}, {"labels", "relations"}):
        raise ExtractionParseError("char_bio output must contain labels and optional relations only")
    labels = value["labels"]
    if not isinstance(labels, list) or len(labels) != len(text):
        raise ExtractionParseError(
            f"char_bio labels length must equal query character count ({len(text)})"
        )
    if "relations" in value:
        relations = value["relations"]
        if not isinstance(relations, list) or relations:
            raise ExtractionParseError("char_bio relations must be an empty list when present")

    allowed_labels = {"O"}
    allowed_labels.update(f"{prefix}-{entity_type}" for prefix in ("B", "I") for entity_type in entity_types)
    entities: list[dict[str, Any]] = []
    active_type: str | None = None
    active_start: int | None = None

    def close_active(end: int) -> None:
        nonlocal active_type, active_start
        if active_type is None or active_start is None:
            return
        if end <= active_start or end > len(text):
            raise ExtractionParseError("char_bio entity boundary is invalid")
        span = text[active_start:end]
        if not span:
            raise ExtractionParseError("char_bio entity span must be non-empty")
        entities.append(
            {
                "start": active_start,
                "end": end,
                "type": active_type,
                "span": span,
            }
        )
        active_type = None
        active_start = None

    for index, label in enumerate(labels):
        if not isinstance(label, str) or label not in allowed_labels:
            raise ExtractionParseError(f"char_bio label {index} is invalid: {label!r}")
        if label == "O":
            close_active(index)
            continue
        prefix, entity_type = label.split("-", 1)
        if prefix == "B":
            close_active(index)
            active_type = entity_type
            active_start = index
            continue
        if active_type is None or active_start is None or active_type != entity_type:
            raise ExtractionParseError(
                f"char_bio label {index} is an I label without a matching open B label"
            )
    close_active(len(labels))

    if max_entities is not None:
        if max_entities <= 0:
            raise ValueError("max_entities must be positive")
        if len(entities) > max_entities:
            raise ExtractionParseError(
                f"char_bio entity count exceeds max_entities={max_entities}"
            )

    seen: set[tuple[int, int, str]] = set()
    for entity in entities:
        start, end, entity_type = entity["start"], entity["end"], entity["type"]
        key = (start, end, entity_type)
        if key in seen:
            raise ExtractionParseError(f"char_bio duplicate entity {key}")
        seen.add(key)
        if start < 0 or end <= start or end > len(text) or text[start:end] != entity["span"]:
            raise ExtractionParseError(f"char_bio entity boundary does not match query text: {key}")
    for previous, current in zip(entities, entities[1:]):
        if current["start"] < previous["end"]:
            raise ExtractionParseError("char_bio entities overlap")
    record = {"id": record_id, "text": text, "entities": entities, "relations": []}
    validate_record(record)
    return record


def parse_extraction_output(
    raw_output: str,
    *,
    record_id: str,
    text: str,
    entity_types: set[str],
    relation_types: Mapping[str, Mapping[str, Sequence[str]]] | None = None,
    drop_invalid_entities: bool = False,
    sanitization_flags: list[dict[str, Any]] | None = None,
    output_mode: str = "occurrence",
    ner_only_envelope_policy: str = "strict",
    candidate_spans: Sequence[Mapping[str, Any]] | None = None,
    candidate_index_lattice: Mapping[str, int] | None = None,
    max_entities: int | None = None,
) -> dict[str, Any]:
    """Parse extraction JSON into the unified schema."""

    try:
        value = json.loads(extract_first_json_object(raw_output))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(f"invalid JSON: {exc}") from exc
    if output_mode == "char_bio":
        if relation_types:
            raise ExtractionParseError("char_bio is NER-only and cannot enable relations")
        return _parse_char_bio_output(
            value,
            record_id=record_id,
            text=text,
            entity_types=entity_types,
            max_entities=max_entities,
        )
    # NER-only span-index responses may omit the unused relations member.  This
    # narrowly normalizes that one envelope shape; occurrence mode remains
    # strict for historical reproducibility.
    ner_only = not relation_types
    if (
        output_mode == "span_index"
        and ner_only
        and isinstance(value, dict)
        and set(value) == {"entities"}
    ):
        value = dict(value)
        value["relations"] = []
        if sanitization_flags is not None:
            sanitization_flags.append(
                {
                    "kind": "NER_RELATIONS_DEFAULTED",
                    "reason": "NER-only envelope omitted unused relations field",
                }
            )
    if (
        output_mode == "occurrence"
        and ner_only
        and ner_only_envelope_policy == "entities_or_entities_relations_v2"
        and isinstance(value, dict)
        and set(value) == {"entities"}
    ):
        value = dict(value)
        value["relations"] = []
        if sanitization_flags is not None:
            sanitization_flags.append(
                {
                    "kind": "NER_RELATIONS_DEFAULTED",
                    "reason": "v2 NER-only envelope omitted unused relations field",
                }
            )
    if (
        output_mode == "candidate_index"
        and ner_only
        and isinstance(value, dict)
        and set(value) == {"entities"}
    ):
        value = dict(value)
        value["relations"] = []
    if not isinstance(value, dict) or set(value) != {"entities", "relations"}:
        raise ExtractionParseError("output must contain entities and relations only")
    raw_entities = value["entities"]
    raw_relations = value["relations"]
    if not isinstance(raw_entities, list) or not isinstance(raw_relations, list):
        raise ExtractionParseError("entities and relations must be lists")

    def flag(kind: str, **details: Any) -> None:
        if sanitization_flags is not None:
            sanitization_flags.append({"kind": kind, **details})

    def drop_or_raise_entity(index: int, reason: str, raw: Any, **details: Any) -> bool:
        if not drop_invalid_entities:
            raise ExtractionParseError(reason)
        flag(
            "ENTITY_DROPPED_INVALID_UNIT",
            entity_raw_index=index,
            reason=reason,
            detail=reason,
            entity=raw if isinstance(raw, dict) else None,
            raw_entity=raw,
            **details,
        )
        return True

    if output_mode == "candidate_index" and candidate_spans is not None and candidate_index_lattice is not None:
        raise ValueError("candidate_spans and candidate_index_lattice are mutually exclusive")
    lattice_bounds: tuple[int, int, int] | None = None
    if candidate_index_lattice is not None:
        required = {"start", "end", "max_span_chars"}
        if not required.issubset(candidate_index_lattice):
            raise ValueError("candidate_index_lattice requires start, end, and max_span_chars")
        window_start = candidate_index_lattice["start"]
        window_end = candidate_index_lattice["end"]
        max_span_chars = candidate_index_lattice["max_span_chars"]
        if (
            not isinstance(window_start, int)
            or isinstance(window_start, bool)
            or not isinstance(window_end, int)
            or isinstance(window_end, bool)
            or not isinstance(max_span_chars, int)
            or isinstance(max_span_chars, bool)
            or not 0 <= window_start < window_end <= len(text)
            or max_span_chars <= 0
            or max_span_chars > window_end - window_start
        ):
            raise ValueError("candidate_index_lattice window bounds are invalid")
        lattice_bounds = (window_start, window_end, max_span_chars)
    explicit_candidate_lookup = {str(item["id"]): item for item in (candidate_spans or [])}
    lattice_candidate_lookup: dict[str, Mapping[str, Any]] = {}
    if lattice_bounds is not None:
        window_start, window_end, max_span_chars = lattice_bounds
        lattice_candidate_lookup = {
            str(item["id"]): item
            for item in materialize_candidate_index_window(
                text,
                window_start=window_start,
                window_end=window_end,
                max_span_chars=max_span_chars,
            )
        }
    parsed_entities: list[tuple[int, dict[str, Any]]] = []
    seen_entities: set[tuple[int, int, str]] = set()
    for index, raw in enumerate(raw_entities):
        if output_mode == "span_index":
            if not isinstance(raw, dict) or set(raw) != {"start", "end", "type"}:
                if drop_or_raise_entity(index, f"entity {index} must contain start/end/type only", raw):
                    continue
            start = raw["start"]
            end = raw["end"]
            entity_type = raw["type"]
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end <= start
                or end > len(text)
            ):
                if drop_or_raise_entity(index, f"entity {index} start/end must be valid text offsets", raw):
                    continue
            span = text[start:end]
        elif output_mode == "anchored_span_index":
            if not isinstance(raw, dict) or set(raw) != {"start", "end", "span", "type"}:
                if drop_or_raise_entity(index, f"entity {index} must contain start/end/span/type only", raw):
                    continue
            start = raw["start"]
            end = raw["end"]
            span = raw["span"]
            entity_type = raw["type"]
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end <= start
                or end > len(text)
            ):
                if drop_or_raise_entity(index, f"entity {index} start/end must be valid text offsets", raw):
                    continue
            if not isinstance(span, str) or not span:
                if drop_or_raise_entity(index, f"entity {index} span must be non-empty", raw):
                    continue
            if text[start:end] != span:
                if drop_or_raise_entity(
                    index,
                    f"entity {index} span does not match text[start:end]",
                    raw,
                    expected_span=text[start:end],
                    reported_span=span,
                ):
                    continue
        elif output_mode == "occurrence":
            if not isinstance(raw, dict) or set(raw) != {"span", "type", "occurrence"}:
                if drop_or_raise_entity(index, f"entity {index} must contain span/type/occurrence only", raw):
                    continue
            span = raw["span"]
            entity_type = raw["type"]
            occurrence = raw["occurrence"]
            if not isinstance(span, str) or not span:
                if drop_or_raise_entity(index, f"entity {index} span must be non-empty", raw):
                    continue
        elif output_mode == "candidate_index":
            if not isinstance(raw, dict) or set(raw) != {"candidate_id", "type"}:
                if drop_or_raise_entity(index, f"entity {index} must contain candidate_id/type only", raw):
                    continue
            candidate_id = raw["candidate_id"]
            item: Mapping[str, Any] | None = (
                explicit_candidate_lookup.get(candidate_id) or lattice_candidate_lookup.get(candidate_id)
                if isinstance(candidate_id, str)
                else None
            )
            if item is None:
                if drop_or_raise_entity(index, f"entity {index} candidate_id is unknown", raw):
                    continue
            start, end, span, entity_type = int(item["start"]), int(item["end"]), str(item["span"]), raw["type"]
        else:
            raise ValueError(f"unsupported output_mode {output_mode!r}")
        if entity_type not in entity_types:
            if drop_or_raise_entity(index, f"entity {index} has unsupported type {entity_type!r}", raw):
                continue
        if output_mode == "occurrence":
            if not isinstance(occurrence, int) or isinstance(occurrence, bool) or occurrence < 1:
                if drop_or_raise_entity(index, f"entity {index} occurrence must be a positive integer", raw):
                    continue
            starts = _occurrence_starts(text, span)
            if occurrence > len(starts):
                if drop_or_raise_entity(
                    index,
                    f"entity {index} occurrence not found for {span!r}",
                    raw,
                    occurrence_requested=occurrence,
                    occurrence_available=len(starts),
                    occurrence_starts=starts,
                ):
                    continue
            start = starts[occurrence - 1]
            end = start + len(span)
        key = (start, end, entity_type)
        if key in seen_entities:
            if drop_or_raise_entity(index, f"entity {index} duplicates {key}", raw, duplicate_key=key):
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
    response_format = generation.get("response_format")
    if response_format is not None:
        if not isinstance(response_format, Mapping):
            raise ValueError("generation.response_format must be a mapping")
        payload["response_format"] = dict(response_format)
    return {
        "run_id": run_id,
        "config_hash": config_hash,
        "payload": payload,
    }


def build_ner_span_index_response_format(
    entity_types: Sequence[str],
    text_length: int,
    *,
    max_entities: int = 12,
) -> dict[str, Any]:
    """Build a strict, per-query JSON schema for NER span-index output.

    The schema constrains only the transport envelope and numeric bounds.  The
    canonical parser remains responsible for start<end, exact span slicing,
    duplicates, overlaps, and all other semantic checks.  ``max_entities`` is
    an output-budget guard against pathological repeated-entity loops; it is
    deliberately explicit and must be chosen by the caller.
    """

    if not entity_types:
        raise ValueError("entity_types must not be empty")
    if text_length <= 0:
        raise ValueError("text_length must be positive")
    if max_entities <= 0:
        raise ValueError("max_entities must be positive")
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": int(max_entities),
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "integer", "minimum": 0, "maximum": text_length - 1},
                        "end": {"type": "integer", "minimum": 1, "maximum": text_length},
                        "type": {"type": "string", "enum": sorted(str(value) for value in entity_types)},
                    },
                    "required": ["start", "end", "type"],
                    "additionalProperties": False,
                },
            },
            "relations": {"type": "array", "maxItems": 0},
        },
        "required": ["entities"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "ner_span_index_output",
            "strict": True,
            "schema": schema,
        },
    }


def build_ner_anchored_span_index_response_format(
    entity_types: Sequence[str],
    text_length: int,
    *,
    max_entities: int = 12,
) -> dict[str, Any]:
    """Build a strict NER schema carrying numeric offsets and a span echo.

    Unlike legacy ``span_index``, the model must return ``span`` as an anchor;
    the parser independently checks that it is exactly ``text[start:end]``.
    This prevents numeric offsets from silently hiding boundary mistakes.
    """

    if not entity_types:
        raise ValueError("entity_types must not be empty")
    if text_length <= 0:
        raise ValueError("text_length must be positive")
    if max_entities <= 0:
        raise ValueError("max_entities must be positive")
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": int(max_entities),
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "integer", "minimum": 0, "maximum": text_length - 1},
                        "end": {"type": "integer", "minimum": 1, "maximum": text_length},
                        "span": {"type": "string", "minLength": 1},
                        "type": {"type": "string", "enum": sorted(str(value) for value in entity_types)},
                    },
                    "required": ["start", "end", "span", "type"],
                    "additionalProperties": False,
                },
            },
            "relations": {"type": "array", "maxItems": 0},
        },
        "required": ["entities", "relations"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "ner_anchored_span_index_output",
            "strict": True,
            "schema": schema,
        },
    }


def build_ner_occurrence_response_format(
    entity_types: Sequence[str],
    *,
    max_entities: int = 12,
) -> dict[str, Any]:
    """Build a strict JSON schema for occurrence-based NER output.

    Occurrence mode keeps localization deterministic: the model emits the
    exact surface form and 1-based occurrence, while the parser computes
    character offsets from the query text. Relations are required as an empty
    array so NER-only runs cannot silently change envelope shape.
    """

    if not entity_types:
        raise ValueError("entity_types must not be empty")
    if max_entities <= 0:
        raise ValueError("max_entities must be positive")
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": int(max_entities),
                "items": {
                    "type": "object",
                    "properties": {
                        "span": {"type": "string", "minLength": 1},
                        "type": {
                            "type": "string",
                            "enum": sorted(str(value) for value in entity_types),
                        },
                        "occurrence": {"type": "integer", "minimum": 1},
                    },
                    "required": ["span", "type", "occurrence"],
                    "additionalProperties": False,
                },
            },
            "relations": {"type": "array", "maxItems": 0},
        },
        "required": ["entities", "relations"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "ner_occurrence_output",
            "strict": True,
            "schema": schema,
        },
    }


def build_ner_char_bio_response_format(
    entity_types: Sequence[str],
    text_length: int,
) -> dict[str, Any]:
    """Build the strict transport schema for character-level BIO NER."""

    if not entity_types:
        raise ValueError("entity_types must not be empty")
    if text_length <= 0:
        raise ValueError("text_length must be positive")
    labels = ["O"]
    labels.extend(
        f"{prefix}-{entity_type}"
        for entity_type in sorted(str(value) for value in entity_types)
        for prefix in ("B", "I")
    )
    schema = {
        "type": "object",
        "properties": {
            "labels": {
                "type": "array",
                "minItems": int(text_length),
                "maxItems": int(text_length),
                "items": {"type": "string", "enum": labels},
            },
            "relations": {"type": "array", "maxItems": 0},
        },
        "required": ["labels"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "ner_char_bio_output",
            "strict": True,
            "schema": schema,
        },
    }


def build_ner_occurrence_ner_only_response_format(
    entity_types: Sequence[str],
    *,
    max_entities: int = 24,
) -> dict[str, Any]:
    """Build the v2 NER-only occurrence envelope.

    The unused relations field is optional at transport level but, when
    present, is constrained to an empty list. The canonical parser still
    enforces every entity and derives exact character offsets from the query.
    """

    if not entity_types:
        raise ValueError("entity_types must not be empty")
    if max_entities <= 0:
        raise ValueError("max_entities must be positive")
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": int(max_entities),
                "items": {
                    "type": "object",
                    "properties": {
                        "span": {"type": "string", "minLength": 1},
                        "type": {
                            "type": "string",
                            "enum": sorted(str(value) for value in entity_types),
                        },
                        "occurrence": {"type": "integer", "minimum": 1},
                    },
                    "required": ["span", "type", "occurrence"],
                    "additionalProperties": False,
                },
            },
            "relations": {"type": "array", "maxItems": 0},
        },
        "required": ["entities"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "ner_occurrence_ner_only_output_v2",
            "strict": True,
            "schema": schema,
        },
    }


def build_ner_candidate_index_response_format(
    entity_types: Sequence[str], candidate_ids: Sequence[str], *, max_entities: int = 12
) -> dict[str, Any]:
    if not entity_types or not candidate_ids or max_entities <= 0:
        raise ValueError("entity_types, candidate_ids, and max_entities must be non-empty/positive")
    schema = {
        "type": "object",
        "properties": {
            "entities": {"type": "array", "maxItems": int(max_entities), "items": {
                "type": "object", "properties": {
                    "candidate_id": {"type": "string", "enum": [str(v) for v in candidate_ids]},
                    "type": {"type": "string", "enum": sorted(str(v) for v in entity_types)},
                }, "required": ["candidate_id", "type"], "additionalProperties": False,
            }},
            "relations": {"type": "array", "maxItems": 0},
        }, "required": ["entities"], "additionalProperties": False,
    }
    return {"type": "json_schema", "json_schema": {"name": "ner_candidate_index_output", "strict": True, "schema": schema}}


def build_ner_compact_candidate_index_response_format(
    entity_types: Sequence[str], *, max_entities: int = 12
) -> dict[str, Any]:
    """Build a bounded candidate-index schema without a per-query enum.

    Candidate membership remains enforced by the parser against the query-local
    candidate set.  The compact schema avoids duplicating hundreds of candidate
    IDs in the request's JSON schema while retaining a deterministic ID shape.
    """

    if not entity_types or max_entities <= 0:
        raise ValueError("entity_types and max_entities must be non-empty/positive")
    schema = {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "maxItems": int(max_entities),
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate_id": {"type": "string", "pattern": r"^c[0-9]{4}_[0-9]{4}$"},
                        "type": {"type": "string", "enum": sorted(str(v) for v in entity_types)},
                    },
                    "required": ["candidate_id", "type"],
                    "additionalProperties": False,
                },
            },
            "relations": {"type": "array", "maxItems": 0},
        },
        "required": ["entities"],
        "additionalProperties": False,
    }
    return {
        "type": "json_schema",
        "json_schema": {"name": "ner_compact_candidate_index_output", "strict": True, "schema": schema},
    }


def generate_candidate_spans(text: str, *, max_candidates: int = 256) -> list[dict[str, Any]]:
    if not text or max_candidates <= 0:
        raise ValueError("text and max_candidates must be positive")
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"[A-Za-z0-9一-龥]+", text):
        start, end = match.span(); length = end - start
        spans.append((start, end))
        for width in range(2, min(8, length) + 1):
            spans.extend((pos, pos + width) for pos in range(start, end - width + 1))
    seen: set[tuple[int, int]] = set(); out: list[dict[str, Any]] = []
    for start, end in sorted(spans, key=lambda pair: (pair[0], -(pair[1]-pair[0]), pair[1])):
        if (start, end) in seen: continue
        seen.add((start, end)); out.append({"id": f"c{len(out)+1:04d}", "start": start, "end": end, "span": text[start:end]})
        if len(out) >= max_candidates: break
    if not out: raise ValueError("no candidate spans generated")
    return out


# The legacy generator above is retained for historical diagnostics.  The
# windowed generator below is an opt-in preparation helper for the reviewer
# candidate-index semantic-repair protocol.  It deliberately accepts token
# offsets from the caller so that importing this module does not load a model
# tokenizer and the old single-prompt path remains unchanged.
_CANDIDATE_INDEX_SUFFIXES = (
    "系统", "装置", "武器", "组件", "模块", "传感器", "激光器", "导引头",
    "环境", "炸弹", "导弹", "炮弹", "飞机", "飞行器", "直升机", "无人机",
    "雷达", "弹药", "终端", "设备", "平台", "武器系统", "导弹系统",
    "机", "弹", "器", "件", "舱", "炮", "枪", "头", "体", "架", "台",
    "车", "船",
)


def generate_candidate_index_windows(
    text: str,
    *,
    token_offsets: Sequence[tuple[int, int]],
    window_chars: int = 64,
    overlap_chars: int = 31,
    max_token_width: int = 20,
    suffix_context_chars: int = 20,
    ascii_radius_chars: int = 6,
    max_span_chars: int = 31,
    max_candidates_per_window: int = 2048,
) -> list[list[dict[str, Any]]]:
    """Generate bounded, query-local candidate windows for semantic repair.

    Each window contains every span made from up to ``max_token_width``
    contiguous tokenizer offsets, plus deterministic character-boundary
    expansions around equipment-like suffixes and ASCII/model runs.  Windows
    overlap by at least the maximum accepted span length so a span fitting in
    the query can be represented in at least one window.  The function never
    consults labels or support records.
    """

    if not text:
        raise ValueError("text must not be empty")
    if (
        window_chars <= 0
        or max_span_chars <= 0
        or window_chars < max_span_chars
        or overlap_chars < max_span_chars
        or overlap_chars >= window_chars
    ):
        raise ValueError("window_chars/overlap_chars are invalid")
    if max_token_width <= 0 or suffix_context_chars <= 0:
        raise ValueError("candidate bounds must be positive")
    if ascii_radius_chars < 0 or max_candidates_per_window <= 0:
        raise ValueError("candidate bounds are invalid")

    normalized_offsets = sorted(
        {
            (int(start), int(end))
            for start, end in token_offsets
            if 0 <= int(start) < int(end) <= len(text)
        }
    )
    if not normalized_offsets:
        raise ValueError("token_offsets must contain at least one valid span")

    step = window_chars - overlap_chars
    starts = list(range(0, max(1, len(text) - window_chars + 1), step))
    if starts[-1] + window_chars < len(text):
        starts.append(len(text) - window_chars)
    if not starts:
        starts = [0]

    ascii_runs = [
        (match.start(), match.end())
        for match in re.finditer(r"[A-Za-z0-9][A-Za-z0-9_./\\-]*", text)
    ]
    windows: list[list[dict[str, Any]]] = []
    for window_index, window_start in enumerate(starts):
        window_end = min(len(text), window_start + window_chars)
        offsets = [
            (start, end)
            for start, end in normalized_offsets
            if window_start <= start < end <= window_end
        ]
        candidates: set[tuple[int, int]] = set()
        for index, (start, _) in enumerate(offsets):
            for end_index in range(index, min(len(offsets), index + max_token_width)):
                end = offsets[end_index][1]
                if end - start <= max_span_chars:
                    candidates.add((start, end))

        for suffix in _CANDIDATE_INDEX_SUFFIXES:
            cursor = window_start
            while True:
                found = text.find(suffix, cursor, window_end)
                if found < 0:
                    break
                end = found + len(suffix)
                for start in range(max(window_start, end - suffix_context_chars), end):
                    if end > start and end - start <= max_span_chars:
                        candidates.add((start, end))
                cursor = found + 1

        for run_start, run_end in ascii_runs:
            if run_start < window_start or run_end > window_end:
                continue
            for start in range(max(window_start, run_start - ascii_radius_chars), run_start + 1):
                for end in range(run_end, min(window_end, run_end + ascii_radius_chars + 1)):
                    if end > start and end - start <= max_span_chars:
                        candidates.add((start, end))

        ordered = sorted(candidates, key=lambda item: (item[0], item[1]))
        if len(ordered) > max_candidates_per_window:
            raise ValueError(
                f"candidate window {window_index} has {len(ordered)} candidates, "
                f"exceeding max_candidates_per_window={max_candidates_per_window}"
            )
        windows.append(
            [
                {
                    "id": f"w{window_index:02d}c{candidate_index:04d}",
                    "window_index": window_index,
                    "window_start": window_start,
                    "window_end": window_end,
                    "start": start,
                    "end": end,
                    "span": text[start:end],
                }
                for candidate_index, (start, end) in enumerate(ordered, start=1)
            ]
        )
    return windows


def generate_candidate_index_lattice(
    text: str,
    *,
    window_chars: int = 64,
    overlap_chars: int = 31,
    max_span_chars: int = 31,
    max_candidates_per_window: int = 2048,
) -> list[list[dict[str, Any]]]:
    """Generate a complete bounded character-span lattice for candidate-index NER.

    This opt-in helper is independent of labels and tokenization.  Every
    contiguous character span up to ``max_span_chars`` is enumerated in at
    least one overlapping window.  Candidate IDs are deterministic and carry
    the exact character offsets used by the parser.  The caller may globally
    deduplicate spans before partitioning them into request-sized chunks.
    """

    if not text:
        raise ValueError("text must not be empty")
    if (
        window_chars <= 0
        or max_span_chars <= 0
        or window_chars < max_span_chars
        or overlap_chars < max_span_chars
        or overlap_chars >= window_chars
    ):
        raise ValueError("window_chars/overlap_chars are invalid")
    if max_candidates_per_window <= 0:
        raise ValueError("max_candidates_per_window must be positive")

    step = window_chars - overlap_chars
    starts = list(range(0, max(1, len(text) - window_chars + 1), step))
    if starts[-1] + window_chars < len(text):
        starts.append(len(text) - window_chars)
    if not starts:
        starts = [0]

    windows: list[list[dict[str, Any]]] = []
    for window_index, window_start in enumerate(starts):
        window_end = min(len(text), window_start + window_chars)
        spans = [
            (start, end)
            for start in range(window_start, window_end)
            for end in range(start + 1, min(window_end, start + max_span_chars) + 1)
        ]
        if len(spans) > max_candidates_per_window:
            raise ValueError(
                f"candidate lattice window {window_index} has {len(spans)} candidates, "
                f"exceeding max_candidates_per_window={max_candidates_per_window}"
            )
        windows.append(
            [
                {
                    "id": f"l{window_index:02d}c{candidate_index:04d}",
                    "window_index": window_index,
                    "window_start": window_start,
                    "window_end": window_end,
                    "start": start,
                    "end": end,
                    "span": text[start:end],
                }
                for candidate_index, (start, end) in enumerate(spans, start=1)
            ]
        )
    return windows


def materialize_candidate_index_window(
    text: str,
    *,
    window_start: int,
    window_end: int,
    max_span_chars: int = 31,
) -> list[dict[str, Any]]:
    """Materialize the implicit ``cSSSS_EEEE`` IDs for one runtime window.

    The prompt carries only the window coordinates.  Runtime parsing expands
    that declaration into the exact query-local character slices and then
    delegates membership, type, duplicate, and overlap checks to
    :func:`parse_extraction_output`.
    """

    if not isinstance(text, str) or not text:
        raise ValueError("text must not be empty")
    if (
        not isinstance(window_start, int)
        or isinstance(window_start, bool)
        or not isinstance(window_end, int)
        or isinstance(window_end, bool)
        or not 0 <= window_start < window_end <= len(text)
        or not isinstance(max_span_chars, int)
        or isinstance(max_span_chars, bool)
        or max_span_chars <= 0
        or max_span_chars > window_end - window_start
    ):
        raise ValueError("window bounds or max_span_chars are invalid")
    return [
        {
            "id": f"c{start:04d}_{end:04d}",
            "start": start,
            "end": end,
            "span": text[start:end],
            "window_start": window_start,
            "window_end": window_end,
        }
        for start in range(window_start, window_end)
        for end in range(start + 1, min(window_end, start + max_span_chars) + 1)
    ]


def merge_candidate_index_records(
    records: Sequence[Mapping[str, Any]],
    *,
    record_id: str,
    text: str,
    entity_types: set[str],
) -> dict[str, Any]:
    """Merge parsed candidate-index window records with exact-span deduplication.

    Overlapping windows can emit the same entity more than once.  Exact
    ``(start, end, type)`` duplicates are collapsed; distinct overlapping
    entities remain a hard parser error so a window boundary cannot silently
    alter the unified non-overlap contract.
    """

    if not records:
        raise ValueError("records must not be empty")
    entities_by_key: dict[tuple[int, int, str], dict[str, Any]] = {}
    for record in records:
        if str(record.get("text")) != text:
            raise ExtractionParseError("candidate-index window text mismatch")
        if record.get("relations") != []:
            raise ExtractionParseError("candidate-index window relations must be empty")
        for entity in record.get("entities", []):
            if not isinstance(entity, Mapping):
                raise ExtractionParseError("candidate-index window entity must be an object")
            start, end, entity_type, span = (
                entity.get("start"),
                entity.get("end"),
                entity.get("type"),
                entity.get("span"),
            )
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or not 0 <= start < end <= len(text)
                or not isinstance(entity_type, str)
                or entity_type not in entity_types
                or not isinstance(span, str)
                or text[start:end] != span
            ):
                raise ExtractionParseError("candidate-index window entity is not an exact typed slice")
            key = (start, end, entity_type)
            entities_by_key.setdefault(key, {
                "start": start,
                "end": end,
                "type": entity_type,
                "span": span,
            })
    entities = [
        entities_by_key[key]
        for key in sorted(entities_by_key, key=lambda item: (item[0], item[1], item[2]))
    ]
    for previous, current in zip(entities, entities[1:]):
        if current["start"] < previous["end"]:
            raise ExtractionParseError("overlapping entities across candidate windows")
    merged = {"id": record_id, "text": text, "entities": entities, "relations": []}
    validate_record(merged)
    return merged


def format_candidate_index_window_block(
    candidate_spans: Sequence[Mapping[str, Any]],
) -> str:
    """Format a compact candidate map used by the windowed preflight."""

    if not candidate_spans:
        raise ValueError("candidate_spans must not be empty")
    entries = []
    for item in candidate_spans:
        candidate_id = str(item["id"])
        span = item.get("span")
        if not candidate_id or not isinstance(span, str) or not span:
            raise ValueError("candidate spans require non-empty id and span")
        entries.append(f"{candidate_id}={span}")
    return (
        "CANDIDATE_INDEX_WINDOW_V1:\n"
        "Choose only an ID from this window; the parser maps it to the exact query span.\n"
        + "|".join(entries)
    )


def prompt_hash(prompt: str) -> str:
    return sha256_text(prompt)


def build_error_retry_prompt(
    *,
    base_prompt: str,
    parse_error: str,
    output_mode: str = "occurrence",
    retry_suffix: str = "只返回合法JSON",
) -> str:
    """Ask the model to fix a concrete parser failure without changing task scope."""

    if output_mode == "char_bio":
        mode_contract = (
            "Character BIO retry rule: return labels only; labels must contain exactly one "
            "label per Python Unicode character in the query, using only O, B-TYPE, and "
            "matching I-TYPE labels.\n"
        )
    elif output_mode == "anchored_span_index":
        mode_contract = (
            "Anchored retry rule: every entity must contain start, end, span, and type; "
            "start is inclusive, end is exclusive, and span must equal text[start:end].\n"
        )
    else:
        mode_contract = ""
    output_contract = (
        "Return only the labels JSON object; do not return spans, offsets, occurrence numbers, "
        "candidate IDs, or relations with items.\n"
        if output_mode == "char_bio"
        else ""
    )
    repair_instruction = (
        "Please repair only this parser error: do not add explanations or markdown; return one "
        "label per query character, use only O/B-TYPE/I-TYPE, and keep relations empty.\n"
        if output_mode == "char_bio"
        else (
            "请只修正这个错误：不要增加解释，不要输出markdown代码块；"
            "实体span必须逐字来自原文，type必须来自Schema，occurrence必须有效；"
            "实体之间不得重叠或嵌套。\n"
        )
    )
    return (
        f"{base_prompt}\n\n"
        f"{mode_contract}{output_contract}"
        f"上次输出未通过解析，错误是：{parse_error}\n"
        f"{repair_instruction}"
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
