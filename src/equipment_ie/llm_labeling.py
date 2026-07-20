"""P2 LLM-assisted labeling helpers with strict parsing and request caching."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from equipment_ie.domain_data import text_sha256, validate_candidate
from equipment_ie.schema import SchemaError, validate_record


class LabelParseError(ValueError):
    """Raised when a model response cannot become an approved-schema proposal."""


@dataclass(frozen=True)
class ChatResult:
    content: str
    request_hash: str
    raw_output_hash: str
    cache_hit: bool
    latency_ms: float


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def strip_code_fences(value: str) -> str:
    stripped = value.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if not lines or not lines[0].startswith("```"):
        return stripped
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _occurrence_starts(text: str, span: str) -> list[int]:
    starts: list[int] = []
    cursor = 0
    while True:
        start = text.find(span, cursor)
        if start < 0:
            return starts
        starts.append(start)
        cursor = start + 1


def _allowed_schema_types(schema: Mapping[str, Any]) -> tuple[set[str], Mapping[str, Any]]:
    entity_types = schema.get("entity_types")
    relation_types = schema.get("relation_types")
    if not isinstance(entity_types, Mapping) or not isinstance(relation_types, Mapping):
        raise SchemaError("schema lacks entity or relation types")
    return set(entity_types), relation_types


def parse_model_label_output(
    raw_output: str,
    *,
    record_id: str,
    text: str,
    schema: Mapping[str, Any],
) -> dict[str, Any]:
    """Parse occurrence-based model JSON into the unified exact-offset contract."""

    try:
        value = json.loads(strip_code_fences(raw_output))
    except json.JSONDecodeError as exc:
        raise LabelParseError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"entities", "relations"}:
        raise LabelParseError("output must contain entities and relations only")
    raw_entities = value["entities"]
    raw_relations = value["relations"]
    if not isinstance(raw_entities, list) or not isinstance(raw_relations, list):
        raise LabelParseError("entities and relations must be lists")

    entity_types, relation_types = _allowed_schema_types(schema)
    original_entities: list[dict[str, Any]] = []
    seen_entities: set[tuple[int, int, str]] = set()
    for index, raw in enumerate(raw_entities):
        if not isinstance(raw, dict) or set(raw) != {"span", "type", "occurrence"}:
            raise LabelParseError(
                f"entity {index} must contain span/type/occurrence only"
            )
        span = raw["span"]
        entity_type = raw["type"]
        occurrence = raw["occurrence"]
        if not isinstance(span, str) or not span:
            raise LabelParseError(f"entity {index} span must be non-empty")
        if entity_type not in entity_types:
            raise LabelParseError(f"entity {index} has unsupported type {entity_type!r}")
        if not isinstance(occurrence, int) or isinstance(occurrence, bool) or occurrence < 1:
            raise LabelParseError(f"entity {index} occurrence must be a positive integer")
        starts = _occurrence_starts(text, span)
        if occurrence > len(starts):
            raise LabelParseError(
                f"entity {index} occurrence {occurrence} not found for {span!r}"
            )
        start = starts[occurrence - 1]
        end = start + len(span)
        key = (start, end, entity_type)
        if key in seen_entities:
            raise LabelParseError(f"entity {index} duplicates {key}")
        seen_entities.add(key)
        original_entities.append(
            {"start": start, "end": end, "type": entity_type, "span": span}
        )

    order = sorted(
        range(len(original_entities)),
        key=lambda index: (
            original_entities[index]["start"],
            original_entities[index]["end"],
            original_entities[index]["type"],
        ),
    )
    remap = {old_index: new_index for new_index, old_index in enumerate(order)}
    entities = [original_entities[index] for index in order]
    for previous, current in zip(entities, entities[1:]):
        if current["start"] < previous["end"]:
            raise LabelParseError(
                f"overlapping entities are forbidden: {previous['span']!r}, "
                f"{current['span']!r}"
            )

    relations: list[dict[str, Any]] = []
    seen_relations: set[tuple[int, int, str]] = set()
    for index, raw in enumerate(raw_relations):
        if not isinstance(raw, dict) or set(raw) != {"head", "tail", "type"}:
            raise LabelParseError(f"relation {index} must contain head/tail/type only")
        head = raw["head"]
        tail = raw["tail"]
        relation_type = raw["type"]
        if (
            not isinstance(head, int)
            or isinstance(head, bool)
            or not isinstance(tail, int)
            or isinstance(tail, bool)
            or not 0 <= head < len(original_entities)
            or not 0 <= tail < len(original_entities)
        ):
            raise LabelParseError(f"relation {index} references a missing entity")
        if head == tail:
            raise LabelParseError(f"relation {index} is self-referential")
        rule = relation_types.get(relation_type)
        if not isinstance(rule, Mapping):
            raise LabelParseError(
                f"relation {index} has unsupported type {relation_type!r}"
            )
        head_type = original_entities[head]["type"]
        tail_type = original_entities[tail]["type"]
        if head_type not in rule["head_types"] or tail_type not in rule["tail_types"]:
            raise LabelParseError(
                f"relation {index} violates the {relation_type} type matrix"
            )
        relation_key = (remap[head], remap[tail], relation_type)
        if relation_key in seen_relations:
            raise LabelParseError(f"relation {index} duplicates {relation_key}")
        seen_relations.add(relation_key)
        relations.append(
            {"head": remap[head], "tail": remap[tail], "type": relation_type}
        )
    relations.sort(key=lambda row: (row["head"], row["tail"], row["type"]))
    record = {"id": record_id, "text": text, "entities": entities, "relations": relations}
    validate_record(record)
    return record


def _entity_occurrence(text: str, entity: Mapping[str, Any]) -> int:
    starts = _occurrence_starts(text, str(entity["span"]))
    try:
        return starts.index(int(entity["start"])) + 1
    except ValueError as exc:
        raise SchemaError("example entity offset is not an exact span occurrence") from exc


def example_as_model_output(record: Mapping[str, Any]) -> dict[str, Any]:
    validate_record(record)
    return {
        "entities": [
            {
                "span": entity["span"],
                "type": entity["type"],
                "occurrence": _entity_occurrence(record["text"], entity),
            }
            for entity in record["entities"]
        ],
        "relations": record["relations"],
    }


def build_label_prompt(
    *,
    text: str,
    schema: Mapping[str, Any],
    prompt_config: Mapping[str, Any],
    examples: Sequence[Mapping[str, Any]],
    prompt_version: str,
) -> str:
    """Build a stable prompt without exposing distant-supervision suggestions."""

    entity_order = ("EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC")
    relation_order = ("USES", "HAS_METRIC", "PART_OF")
    if prompt_config.get("prompt_version") != prompt_version:
        raise SchemaError("prompt-definition version mismatch")
    if prompt_config.get("schema_version") != schema.get("version"):
        raise SchemaError("prompt definitions target a different schema")
    if set(prompt_config.get("entity_types", {})) != set(entity_order):
        raise SchemaError("prompt entity definitions differ from the schema")
    if set(prompt_config.get("relation_types", {})) != set(relation_order):
        raise SchemaError("prompt relation definitions differ from the schema")
    entity_lines = [
        f"- {name}: {prompt_config['entity_types'][name]}"
        for name in entity_order
    ]
    relation_lines = [
        f"- {name}: {prompt_config['relation_types'][name]}"
        for name in relation_order
    ]
    constraints = prompt_config["constraints"]
    extra_rules = constraints.get("additional_output_rules", [])
    blocks = [
        f"任务定义（{prompt_version}）：从装备领域文本中抽取实体和显式关系。",
        "实体类型：\n" + "\n".join(entity_lines),
        "关系类型：\n" + "\n".join(relation_lines),
        (
            "规则：只依据原文；实体必须是原文连续片段；occurrence 表示该完全相同"
            "片段在原文中从左到右第几次出现（从1开始）；实体按原文位置列出；不"
            "允许重叠实体、跨句关系、代词共指关系、否定/假设关系或常识推断。"
        ),
        (
            "输出格式：{\"entities\":[{\"span\":\"原文片段\",\"type\":"
            "\"EQUIPMENT\",\"occurrence\":1}],\"relations\":[{\"head\":0,"
            "\"tail\":1,\"type\":\"USES\"}]}。head/tail 是 entities 数组下标。"
        ),
    ]
    if constraints.get("include_relation_type_matrix"):
        matrix_lines = []
        for name in relation_order:
            relation = schema["relation_types"][name]
            heads = "/".join(relation["head_types"])
            tails = "/".join(relation["tail_types"])
            matrix_lines.append(f"- {name}: head 只能是 {heads}; tail 只能是 {tails}")
        blocks.append("关系类型矩阵：\n" + "\n".join(matrix_lines))
    if extra_rules:
        blocks.append("补充输出约束：\n" + "\n".join(f"- {rule}" for rule in extra_rules))
    for index, example in enumerate(examples, start=1):
        validate_record(example)
        blocks.append(
            f"示例{index}文本：{example['text']}\n示例{index}输出："
            f"{canonical_json(example_as_model_output(example))}"
        )
    blocks.extend(
        [
            f"待标注文本：{text}",
            prompt_config["constraints"]["output_instruction"],
        ]
    )
    return "\n\n".join(blocks)


def build_retry_prompt(prompt: str, retry_suffix: str = "只返回合法JSON") -> str:
    return f"{prompt}\n{retry_suffix}"


def build_request_envelope(
    *,
    prompt: str,
    model: str,
    generation: Mapping[str, Any],
    prompt_version: str,
    schema_sha256: str,
    prompt_config_sha256: str,
    examples_sha256: str,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": float(generation["temperature"]),
        "top_p": float(generation["top_p"]),
        "max_tokens": int(generation["max_tokens"]),
        "seed": int(generation["seed"]),
    }
    return {
        "prompt_version": prompt_version,
        "schema_sha256": schema_sha256,
        "prompt_config_sha256": prompt_config_sha256,
        "examples_sha256": examples_sha256,
        "payload": payload,
    }


def request_hash(envelope: Mapping[str, Any]) -> str:
    return sha256_text(canonical_json(envelope))


def _cache_path(cache_dir: Path, digest: str) -> Path:
    return cache_dir / digest[:2] / f"{digest}.json"


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _extract_chat_content(response: Mapping[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("vLLM response lacks choices[0].message.content") from exc
    if not isinstance(content, str):
        raise RuntimeError("vLLM chat content must be a string")
    return content


def _post_chat_completion(
    *,
    base_url: str,
    payload: Mapping[str, Any],
    timeout_seconds: int,
    api_key: str,
) -> tuple[dict[str, Any], float]:
    endpoint = f"{base_url.rstrip('/')}/v1/chat/completions"
    request = Request(
        endpoint,
        data=canonical_json(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            value = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"vLLM HTTP {exc.code}: {body[:500]}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"vLLM request failed: {type(exc).__name__}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("vLLM response must be a JSON object")
    return value, (time.monotonic() - started) * 1000.0


def chat_with_cache(
    *,
    envelope: Mapping[str, Any],
    cache_dir: Path,
    base_url: str,
    timeout_seconds: int,
    api_key: str,
) -> ChatResult:
    digest = request_hash(envelope)
    path = _cache_path(cache_dir, digest)
    if path.is_file():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("request_hash") != digest or cached.get("request") != envelope:
            raise RuntimeError(f"cache request mismatch: {path}")
        content = cached.get("content")
        if not isinstance(content, str) or cached.get("raw_output_hash") != sha256_text(content):
            raise RuntimeError(f"cache content hash mismatch: {path}")
        return ChatResult(
            content=content,
            request_hash=digest,
            raw_output_hash=cached["raw_output_hash"],
            cache_hit=True,
            latency_ms=float(cached.get("latency_ms", 0.0)),
        )
    response, latency_ms = _post_chat_completion(
        base_url=base_url,
        payload=envelope["payload"],
        timeout_seconds=timeout_seconds,
        api_key=api_key,
    )
    content = _extract_chat_content(response)
    raw_hash = sha256_text(content)
    entry = {
        "request_hash": digest,
        "request": envelope,
        "content": content,
        "raw_output_hash": raw_hash,
        "latency_ms": round(latency_ms, 3),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "response": response,
    }
    _write_json_atomic(path, entry)
    return ChatResult(
        content=content,
        request_hash=digest,
        raw_output_hash=raw_hash,
        cache_hit=False,
        latency_ms=latency_ms,
    )


def select_candidates(
    candidates: Sequence[Mapping[str, Any]],
    distant_records: Sequence[Mapping[str, Any]],
    selection: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Select all records or a deterministic source/match-diverse sanity set."""

    if len(candidates) != len(distant_records):
        raise ValueError("candidate and distant-supervision counts differ")
    paired: list[tuple[dict[str, Any], bool]] = []
    for candidate, distant in zip(candidates, distant_records, strict=True):
        validate_candidate(candidate)
        validate_record(distant)
        if candidate["id"] != distant["id"] or candidate["text"] != distant["text"]:
            raise ValueError("candidate and distant-supervision rows differ")
        paired.append((dict(candidate), bool(distant["entities"])))
    if selection["mode"] == "all":
        return [candidate for candidate, _ in paired]
    if selection["mode"] != "sanity":
        raise ValueError("unsupported selection mode")

    sample_size = int(selection["sample_size"])
    minimum_per_source = int(selection["minimum_per_source"])
    minimum_matched = int(selection["minimum_ds_matched"])
    minimum_unmatched = int(selection["minimum_ds_unmatched"])
    seed = int(selection["seed"])
    ranked = sorted(
        paired,
        key=lambda item: sha256_text(f"{seed}:{item[0]['id']}"),
    )
    selected_ids: set[str] = set()
    for source_type in ("baidu_baike", "patent", "cmnee"):
        source_rows = [item for item in ranked if item[0]["source_type"] == source_type]
        if len(source_rows) < minimum_per_source:
            raise ValueError(f"insufficient sanity rows for source {source_type}")
        selected_ids.update(item[0]["id"] for item in source_rows[:minimum_per_source])

    def selected_count(match_state: bool) -> int:
        return sum(
            candidate["id"] in selected_ids and matched == match_state
            for candidate, matched in paired
        )

    for desired, minimum in ((True, minimum_matched), (False, minimum_unmatched)):
        for candidate, matched in ranked:
            if selected_count(desired) >= minimum:
                break
            if matched == desired:
                selected_ids.add(candidate["id"])
    for candidate, _ in ranked:
        if len(selected_ids) >= sample_size:
            break
        selected_ids.add(candidate["id"])
    if len(selected_ids) != sample_size:
        raise ValueError("sanity selection did not reach the requested size")
    if selected_count(True) < minimum_matched or selected_count(False) < minimum_unmatched:
        raise ValueError("sanity selection did not satisfy match diversity")
    return [candidate for candidate, _ in paired if candidate["id"] in selected_ids]


def _entity_key(entity: Mapping[str, Any]) -> tuple[int, int, str, str]:
    return (
        int(entity["start"]),
        int(entity["end"]),
        str(entity["type"]),
        str(entity["span"]),
    )


def merge_distant_and_llm(
    distant: Mapping[str, Any],
    llm: Mapping[str, Any] | None,
    *,
    llm_error: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Union machine suggestions and preserve every disagreement for review."""

    validate_record(distant)
    if llm is not None:
        validate_record(llm)
        if distant["id"] != llm["id"] or distant["text"] != llm["text"]:
            raise SchemaError("distant and LLM proposals refer to different records")
    distant_keys = {_entity_key(entity) for entity in distant["entities"]}
    llm_keys = {_entity_key(entity) for entity in llm["entities"]} if llm else set()
    union_keys = sorted(distant_keys | llm_keys, key=lambda key: (key[0], key[1], key[2]))
    entities = [
        {"start": key[0], "end": key[1], "type": key[2], "span": key[3]}
        for key in union_keys
    ]
    key_to_index = {key: index for index, key in enumerate(union_keys)}
    provenance = [
        {
            "entity": entities[index],
            "sources": [
                source
                for source, source_keys in (
                    ("distant_supervision", distant_keys),
                    ("llm", llm_keys),
                )
                if key in source_keys
            ],
        }
        for index, key in enumerate(union_keys)
    ]
    flags: list[dict[str, Any]] = []
    for key in sorted(distant_keys - llm_keys):
        flags.append({"kind": "ENTITY_ONLY_DISTANT", "entity": key_to_index[key]})
    for key in sorted(llm_keys - distant_keys):
        flags.append({"kind": "ENTITY_ONLY_LLM", "entity": key_to_index[key]})
    by_boundary: dict[tuple[int, int, str], set[str]] = {}
    for start, end, entity_type, span in union_keys:
        by_boundary.setdefault((start, end, span), set()).add(entity_type)
    for (start, end, span), types in sorted(by_boundary.items()):
        if len(types) > 1:
            flags.append(
                {
                    "kind": "ENTITY_TYPE_CONFLICT",
                    "start": start,
                    "end": end,
                    "span": span,
                    "types": sorted(types),
                }
            )
    for left_index, left in enumerate(entities):
        for right_index in range(left_index + 1, len(entities)):
            right = entities[right_index]
            if right["start"] >= left["end"]:
                break
            if (left["start"], left["end"]) != (right["start"], right["end"]):
                flags.append(
                    {
                        "kind": "ENTITY_OVERLAP_CONFLICT",
                        "entities": [left_index, right_index],
                    }
                )
    if llm is None:
        flags.append({"kind": "LLM_PARSE_FAILURE", "error": llm_error or "unknown"})

    relations: list[dict[str, Any]] = []
    if llm is not None:
        llm_index_to_union = {
            index: key_to_index[_entity_key(entity)]
            for index, entity in enumerate(llm["entities"])
        }
        seen_relations: set[tuple[int, int, str]] = set()
        for relation in llm["relations"]:
            key = (
                llm_index_to_union[relation["head"]],
                llm_index_to_union[relation["tail"]],
                relation["type"],
            )
            if key not in seen_relations:
                seen_relations.add(key)
                relations.append({"head": key[0], "tail": key[1], "type": key[2]})
        relations.sort(key=lambda row: (row["head"], row["tail"], row["type"]))
    union = {
        "id": distant["id"],
        "text": distant["text"],
        "entities": entities,
        "relations": relations,
    }
    validate_record(union)
    return union, provenance, flags


def build_llm_review_row(
    *,
    candidate: Mapping[str, Any],
    distant: Mapping[str, Any],
    llm: Mapping[str, Any] | None,
    union: Mapping[str, Any],
    provenance: Sequence[Mapping[str, Any]],
    disagreement_flags: Sequence[Mapping[str, Any]],
    attempts: Sequence[Mapping[str, Any]],
    prompt_version: str,
    llm_error: str | None,
) -> dict[str, Any]:
    validate_candidate(candidate)
    for record in (distant, union):
        validate_record(record)
    if llm is not None:
        validate_record(llm)
    ids = {candidate["id"], distant["id"], union["id"]}
    texts = {candidate["text"], distant["text"], union["text"]}
    if llm is not None:
        ids.add(llm["id"])
        texts.add(llm["text"])
    if len(ids) != 1 or len(texts) != 1:
        raise SchemaError("LLM review components refer to different candidates")
    row = {
        "review_id": candidate["id"],
        "candidate": {
            key: candidate[key]
            for key in (
                "id",
                "text",
                "content_sha256",
                "source_type",
                "source_id",
                "source_split",
                "source_url",
                "source_revision",
                "source_license",
                "title",
            )
        },
        "prompt_version": prompt_version,
        "distant_supervision": distant,
        "llm_proposal": llm,
        "union_proposal": union,
        "entity_provenance": list(provenance),
        "disagreement_flags": list(disagreement_flags),
        "llm_execution": {
            "status": "PARSE_FAILURE" if llm is None else "OK",
            "parse_failure": llm is None,
            "error": llm_error,
            "attempts": list(attempts),
        },
        "human_annotation": {
            "status": "NOT_STARTED",
            "annotator_a": None,
            "annotator_b": None,
            "adjudication": None,
        },
    }
    validate_llm_review_row(row)
    return row


def validate_llm_review_row(row: Mapping[str, Any]) -> None:
    required = {
        "review_id",
        "candidate",
        "prompt_version",
        "distant_supervision",
        "llm_proposal",
        "union_proposal",
        "entity_provenance",
        "disagreement_flags",
        "llm_execution",
        "human_annotation",
    }
    if set(row) != required:
        raise SchemaError("LLM review row fields differ from the contract")
    candidate = row["candidate"]
    if row["review_id"] != candidate.get("id"):
        raise SchemaError("LLM review id mismatch")
    if candidate.get("content_sha256") != text_sha256(str(candidate.get("text", ""))):
        raise SchemaError("LLM review candidate hash mismatch")
    for name in ("distant_supervision", "union_proposal"):
        validate_record(row[name])
    if row["llm_proposal"] is not None:
        validate_record(row["llm_proposal"])
    if row["human_annotation"] != {
        "status": "NOT_STARTED",
        "annotator_a": None,
        "annotator_b": None,
        "adjudication": None,
    }:
        raise SchemaError("LLM review human fields must remain untouched")
    execution = row["llm_execution"]
    if execution["parse_failure"] != (row["llm_proposal"] is None):
        raise SchemaError("LLM parse status and proposal disagree")
    attempts = execution["attempts"]
    if not isinstance(attempts, list) or not 1 <= len(attempts) <= 2:
        raise SchemaError("LLM execution must contain one or two attempts")
    for attempt in attempts:
        if set(attempt) != {
            "attempt",
            "prompt_hash",
            "request_hash",
            "raw_output_hash",
            "cache_hit",
            "latency_ms",
            "parse_error",
        }:
            raise SchemaError("LLM attempt fields differ from the contract")


def _spreadsheet_safe(value: str) -> str:
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


def write_llm_review_csv_atomic(
    path: Path | str, rows: Sequence[Mapping[str, Any]]
) -> int:
    fields = [
        "review_id",
        "source_type",
        "source_id",
        "source_url",
        "source_license",
        "title_display",
        "text_display",
        "text_json",
        "prompt_version",
        "llm_status",
        "parse_failure",
        "distant_entities_json",
        "llm_entities_json",
        "llm_relations_json",
        "union_entities_json",
        "union_relations_json",
        "entity_provenance_json",
        "disagreement_flags_json",
        "attempts_json",
        "human_review_status",
        "annotator_a_entities_json",
        "annotator_a_relations_json",
        "annotator_a_notes",
        "annotator_b_entities_json",
        "annotator_b_relations_json",
        "annotator_b_notes",
        "adjudicated_entities_json",
        "adjudicated_relations_json",
        "adjudication_notes",
    ]
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
            writer.writeheader()
            for row in rows:
                validate_llm_review_row(row)
                candidate = row["candidate"]
                llm = row["llm_proposal"] or {"entities": [], "relations": []}
                execution = row["llm_execution"]
                writer.writerow(
                    {
                        "review_id": row["review_id"],
                        "source_type": candidate["source_type"],
                        "source_id": _spreadsheet_safe(str(candidate["source_id"])),
                        "source_url": candidate["source_url"],
                        "source_license": candidate["source_license"],
                        "title_display": _spreadsheet_safe(str(candidate["title"])),
                        "text_display": _spreadsheet_safe(str(candidate["text"])),
                        "text_json": json.dumps(candidate["text"], ensure_ascii=False),
                        "prompt_version": row["prompt_version"],
                        "llm_status": execution["status"],
                        "parse_failure": str(execution["parse_failure"]).lower(),
                        "distant_entities_json": canonical_json(
                            row["distant_supervision"]["entities"]
                        ),
                        "llm_entities_json": canonical_json(llm["entities"]),
                        "llm_relations_json": canonical_json(llm["relations"]),
                        "union_entities_json": canonical_json(
                            row["union_proposal"]["entities"]
                        ),
                        "union_relations_json": canonical_json(
                            row["union_proposal"]["relations"]
                        ),
                        "entity_provenance_json": canonical_json(
                            row["entity_provenance"]
                        ),
                        "disagreement_flags_json": canonical_json(
                            row["disagreement_flags"]
                        ),
                        "attempts_json": canonical_json(execution["attempts"]),
                        "human_review_status": row["human_annotation"]["status"],
                        "annotator_a_entities_json": "",
                        "annotator_a_relations_json": "",
                        "annotator_a_notes": "",
                        "annotator_b_entities_json": "",
                        "annotator_b_relations_json": "",
                        "annotator_b_notes": "",
                        "adjudicated_entities_json": "",
                        "adjudicated_relations_json": "",
                        "adjudication_notes": "",
                    }
                )
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return len(rows)
