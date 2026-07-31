"""Pure Stage R, exact-relation, and relation-aware verification helpers."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from equipment_ie.extraction import ExtractionParseError, MicroCounts
from equipment_ie.llm_labeling import canonical_json, extract_first_json_object
from equipment_ie.schema import validate_record


DEFAULT_RELATION_TYPES: dict[str, dict[str, Any]] = {
    "USES": {
        "definition": "head explicitly uses, carries, mounts, deploys, or adopts tail.",
        "head_types": ("EQUIPMENT", "MODULE"),
        "tail_types": ("EQUIPMENT", "MODULE", "TECH_SCHEME"),
    },
    "HAS_METRIC": {
        "definition": "tail explicitly states a metric or technical attribute of head.",
        "head_types": ("EQUIPMENT", "MODULE"),
        "tail_types": ("METRIC", "TECH_SCHEME"),
    },
    "PART_OF": {
        "definition": "head is an explicit constituent of tail; direction is part to whole.",
        "head_types": ("EQUIPMENT", "MODULE"),
        "tail_types": ("EQUIPMENT", "MODULE"),
    },
}

# Chinese semicolons commonly separate clauses in one equipment-list sentence.
_SENTENCE_BOUNDARIES = frozenset("。！？!?\n\r")
RelationKey = tuple[int, int, str, str, int, int, str]


@dataclass(frozen=True)
class VerificationApplication:
    """Result and audit trail from deletion-only atomic verification."""

    record: dict[str, Any]
    dropped_entity_indices: tuple[int, ...]
    dropped_relation_indices: tuple[int, ...]
    cascade_dropped_relation_indices: tuple[int, ...]
    invalid_decisions: int


def normalize_relation_rules(
    relation_types: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Validate and normalize a directed relation type matrix."""

    if not relation_types:
        raise ValueError("relation_types must not be empty")
    normalized: dict[str, dict[str, Any]] = {}
    for relation_type, raw_rule in relation_types.items():
        if not isinstance(relation_type, str) or not relation_type:
            raise ValueError("relation type names must be non-empty strings")
        if not isinstance(raw_rule, Mapping):
            raise ValueError(f"relation rule {relation_type} must be an object")
        definition = raw_rule.get("definition")
        head_types = raw_rule.get("head_types")
        tail_types = raw_rule.get("tail_types")
        if not isinstance(definition, str) or not definition.strip():
            raise ValueError(f"relation rule {relation_type} needs a definition")
        if not isinstance(head_types, Sequence) or isinstance(head_types, str):
            raise ValueError(f"relation rule {relation_type} head_types must be a list")
        if not isinstance(tail_types, Sequence) or isinstance(tail_types, str):
            raise ValueError(f"relation rule {relation_type} tail_types must be a list")
        normalized_heads = tuple(str(value) for value in head_types)
        normalized_tails = tuple(str(value) for value in tail_types)
        if not normalized_heads or not normalized_tails or any(
            not value for value in normalized_heads + normalized_tails
        ):
            raise ValueError(f"relation rule {relation_type} has an empty type set")
        normalized[relation_type] = {
            "definition": definition.strip(),
            "head_types": normalized_heads,
            "tail_types": normalized_tails,
        }
    return normalized


def validate_approved_relation_matrix(
    relation_types: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Require the approved v3 relation names, endpoint types, and directions."""

    rules = normalize_relation_rules(relation_types)
    approved = normalize_relation_rules(DEFAULT_RELATION_TYPES)
    if set(rules) != set(approved):
        raise ValueError(
            "relation types must exactly match the approved v3 inventory "
            f"{sorted(approved)}"
        )
    for relation_type, expected in approved.items():
        actual = rules[relation_type]
        if (
            actual["head_types"] != expected["head_types"]
            or actual["tail_types"] != expected["tail_types"]
        ):
            raise ValueError(
                f"relation {relation_type} does not match the approved v3 direction/type matrix"
            )
    return rules


def sentence_index(text: str, offset: int) -> int:
    """Return the deterministic sentence index containing a character offset."""

    if not isinstance(offset, int) or isinstance(offset, bool) or not 0 <= offset <= len(text):
        raise ValueError("offset is outside text")
    return sum(character in _SENTENCE_BOUNDARIES for character in text[:offset])


def same_sentence(text: str, head: Mapping[str, Any], tail: Mapping[str, Any]) -> bool:
    return sentence_index(text, int(head["start"])) == sentence_index(text, int(tail["start"]))


def compatible_relation_pairs(
    record: Mapping[str, Any],
    relation_types: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int, str]]:
    """Enumerate allowed directed, same-sentence endpoint/type combinations."""

    validate_record(record)
    rules = normalize_relation_rules(relation_types)
    pairs: list[tuple[int, int, str]] = []
    for relation_type, rule in rules.items():
        for head_index, head in enumerate(record["entities"]):
            if head["type"] not in rule["head_types"]:
                continue
            for tail_index, tail in enumerate(record["entities"]):
                if head_index == tail_index or tail["type"] not in rule["tail_types"]:
                    continue
                if same_sentence(str(record["text"]), head, tail):
                    pairs.append((head_index, tail_index, relation_type))
    return sorted(pairs)


def stage_r_skip_reason(
    record: Mapping[str, Any],
    relation_types: Mapping[str, Mapping[str, Any]],
) -> str | None:
    """Return why Stage R can deterministically skip a model request."""

    validate_record(record)
    if len(record["entities"]) < 2:
        return "fewer_than_two_entities"
    if not compatible_relation_pairs(record, relation_types):
        return "no_type_compatible_same_sentence_pair"
    return None


def _relation_schema_block(rules: Mapping[str, Mapping[str, Any]]) -> str:
    lines: list[str] = []
    for relation_type, rule in rules.items():
        heads = "/".join(rule["head_types"])
        tails = "/".join(rule["tail_types"])
        lines.append(
            f"- {relation_type}: {rule['definition']} Allowed direction: {heads} -> {tails}."
        )
    return "\n".join(lines)


def _stage_r_example_block(index: int, record: Mapping[str, Any]) -> str:
    validate_record(record)
    entities = [dict(entity) for entity in record["entities"]]
    relations = [dict(relation) for relation in record["relations"]]
    return "\n".join(
        [
            f"示例{index}实体列表：{canonical_json(entities)}",
            f"示例{index}文本：{record['text']}",
            f"示例{index}输出：{canonical_json({'relations': relations})}",
        ]
    )


def build_stage_r_prompt(
    *,
    stage_n_record: Mapping[str, Any],
    relation_types: Mapping[str, Mapping[str, Any]],
    examples: Sequence[Mapping[str, Any]],
    glossary_entries: Sequence[str] | None = None,
    rag_passages: Sequence[str] | None = None,
    output_instruction: str = "只返回JSON,不要任何解释,不要markdown代码块",
) -> str:
    """Build the fixed relation-only prompt without changing Stage N entities."""

    validate_record(stage_n_record)
    if stage_n_record["relations"]:
        raise ValueError("Stage R input must contain Stage N entities and no relations")
    rules = normalize_relation_rules(relation_types)
    blocks = [
        "任务定义：只抽取原文同一句内明确表达的有向关系；不得依赖常识、代词或跨句推断。",
        "Stage N实体列表（数组下标即head/tail；必须逐项原样保留，不得新增、删除、改名、改类型或改边界）：\n"
        + canonical_json([dict(entity) for entity in stage_n_record["entities"]]),
        "关系Schema与方向：\n" + _relation_schema_block(rules),
    ]
    if glossary_entries:
        blocks.append("领域术语表：\n" + "\n".join(f"- {entry}" for entry in glossary_entries))
    if rag_passages:
        blocks.append("参考资料（仅辅助判断，关系仍须由原文同一句明确支持）：\n" + "\n".join(
            f"- {passage}" for passage in rag_passages
        ))
    for index, example in enumerate(examples, start=1):
        blocks.append(_stage_r_example_block(index, example))
    blocks.extend(
        [
            f"待抽取文本：{stage_n_record['text']}",
            "输出格式：{\"relations\":[{\"head\":0,\"tail\":1,\"type\":\"USES\"}]}。"
            "最外层只能包含relations；head/tail是Stage N实体列表的零基下标；"
            f"无关系时返回空数组。\n{output_instruction}",
        ]
    )
    return "\n\n".join(blocks)


def build_stage_r_retry_prompt(
    *,
    base_prompt: str,
    parse_error: str,
    retry_suffix: str = "只返回合法JSON",
) -> str:
    return (
        f"{base_prompt}\n\n上次关系输出未通过解析，错误是：{parse_error}\n"
        "只修正关系JSON：不得改变实体；head/tail必须是现有零基下标；关系必须满足"
        "同句、类型矩阵和方向；删除重复或非法关系；不要解释或输出markdown。\n"
        f"{retry_suffix}"
    )


def parse_stage_r_output(
    raw_output: str,
    *,
    stage_n_record: Mapping[str, Any],
    relation_types: Mapping[str, Mapping[str, Any]],
    drop_invalid_relations: bool = False,
    sanitization_flags: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Parse relation-only JSON and preserve the Stage N entity array exactly."""

    validate_record(stage_n_record)
    if stage_n_record["relations"]:
        raise ValueError("Stage R input must not already contain relations")
    rules = normalize_relation_rules(relation_types)
    try:
        value = json.loads(extract_first_json_object(raw_output))
    except json.JSONDecodeError as exc:
        raise ExtractionParseError(f"invalid relation JSON: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"relations"}:
        raise ExtractionParseError("Stage R output must contain relations only")
    raw_relations = value["relations"]
    if not isinstance(raw_relations, list):
        raise ExtractionParseError("relations must be a list")

    def invalid(index: int, reason: str, raw: Any) -> bool:
        if not drop_invalid_relations:
            raise ExtractionParseError(reason)
        if sanitization_flags is not None:
            sanitization_flags.append(
                {
                    "kind": "RELATION_DROPPED_INVALID_UNIT",
                    "relation_raw_index": index,
                    "reason": reason,
                    "raw_relation": raw,
                }
            )
        return True

    entities = [dict(entity) for entity in stage_n_record["entities"]]
    relations: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for index, raw in enumerate(raw_relations):
        if not isinstance(raw, Mapping) or set(raw) != {"head", "tail", "type"}:
            if invalid(index, f"relation {index} must contain head/tail/type only", raw):
                continue
        head = raw["head"]
        tail = raw["tail"]
        relation_type = raw["type"]
        if (
            not isinstance(head, int)
            or isinstance(head, bool)
            or not isinstance(tail, int)
            or isinstance(tail, bool)
            or not 0 <= head < len(entities)
            or not 0 <= tail < len(entities)
        ):
            if invalid(index, f"relation {index} references a missing entity", raw):
                continue
        if head == tail:
            if invalid(index, f"relation {index} cannot be self-referential", raw):
                continue
        if not isinstance(relation_type, str) or not relation_type:
            if invalid(index, f"relation {index} type must be a non-empty string", raw):
                continue
        rule = rules.get(relation_type)
        if rule is None:
            if invalid(index, f"relation {index} has unsupported type {relation_type!r}", raw):
                continue
        head_entity = entities[head]
        tail_entity = entities[tail]
        if head_entity["type"] not in rule["head_types"] or tail_entity["type"] not in rule["tail_types"]:
            if invalid(index, f"relation {index} violates the directed type matrix", raw):
                continue
        if not same_sentence(str(stage_n_record["text"]), head_entity, tail_entity):
            if invalid(index, f"relation {index} crosses a sentence boundary", raw):
                continue
        key = (head, tail, relation_type)
        if key in seen:
            if sanitization_flags is not None:
                sanitization_flags.append(
                    {
                        "kind": "RELATION_DROPPED_DUPLICATE",
                        "relation_raw_index": index,
                        "relation": dict(raw),
                    }
                )
            continue
        seen.add(key)
        relations.append({"head": head, "tail": tail, "type": relation_type})

    relations.sort(key=lambda relation: (relation["head"], relation["tail"], relation["type"]))
    record = {
        "id": stage_n_record["id"],
        "text": stage_n_record["text"],
        "entities": entities,
        "relations": relations,
    }
    validate_record(record)
    return record


def canonical_relation_keys(record: Mapping[str, Any]) -> set[RelationKey]:
    """Canonicalize exact directed triples using endpoint span and type."""

    validate_record(record)
    keys: set[RelationKey] = set()
    for relation in record["relations"]:
        head = record["entities"][relation["head"]]
        tail = record["entities"][relation["tail"]]
        keys.add(
            (
                head["start"],
                head["end"],
                head["type"],
                relation["type"],
                tail["start"],
                tail["end"],
                tail["type"],
            )
        )
    return keys


def _records_by_id(records: Sequence[Mapping[str, Any]], *, role: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        validate_record(record)
        record_id = str(record["id"])
        if record_id in indexed:
            raise ValueError(f"duplicate {role} record id {record_id}")
        indexed[record_id] = record
    return indexed


def _micro_from_sets(gold: set[RelationKey], pred: set[RelationKey]) -> MicroCounts:
    return MicroCounts(len(gold & pred), len(pred - gold), len(gold - pred))


def relation_micro_counts(
    gold_records: Sequence[Mapping[str, Any]],
    pred_records: Sequence[Mapping[str, Any]],
) -> MicroCounts:
    """Compute end-to-end exact directed relation-triple micro counts."""

    gold_by_id = _records_by_id(gold_records, role="gold")
    pred_by_id = _records_by_id(pred_records, role="prediction")
    if set(gold_by_id) != set(pred_by_id):
        missing = sorted(set(gold_by_id) - set(pred_by_id))
        extra = sorted(set(pred_by_id) - set(gold_by_id))
        raise ValueError(f"gold/prediction id mismatch: missing={missing}, extra={extra}")
    counts = MicroCounts(0, 0, 0)
    for record_id, gold in gold_by_id.items():
        pred = pred_by_id[record_id]
        if pred["text"] != gold["text"]:
            raise ValueError(f"{record_id}: gold/prediction text mismatch")
        row_counts = _micro_from_sets(canonical_relation_keys(gold), canonical_relation_keys(pred))
        counts = MicroCounts(
            counts.true_positive + row_counts.true_positive,
            counts.false_positive + row_counts.false_positive,
            counts.false_negative + row_counts.false_negative,
        )
    return counts


def _report_with_fdr(counts: MicroCounts) -> dict[str, float | int]:
    report = counts.report()
    report["gold"] = counts.true_positive + counts.false_negative
    predicted = counts.true_positive + counts.false_positive
    report["predicted"] = predicted
    report["fdr"] = counts.false_positive / predicted if predicted else 0.0
    return report


def relation_evaluation_report(
    gold_records: Sequence[Mapping[str, Any]],
    pred_records: Sequence[Mapping[str, Any]],
    *,
    relation_types: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Return exact RE metrics plus endpoint-coverage and zero-gold diagnostics."""

    gold_by_id = _records_by_id(gold_records, role="gold")
    pred_by_id = _records_by_id(pred_records, role="prediction")
    if set(gold_by_id) != set(pred_by_id):
        raise ValueError("gold/prediction id mismatch")

    all_gold: set[tuple[str, RelationKey]] = set()
    all_pred: set[tuple[str, RelationKey]] = set()
    covered_gold: set[tuple[str, RelationKey]] = set()
    pred_on_gold_endpoints: set[tuple[str, RelationKey]] = set()
    zero_gold_passages = 0
    zero_gold_with_predictions = 0
    predicted_on_zero_gold = 0
    for record_id, gold in gold_by_id.items():
        pred = pred_by_id[record_id]
        if pred["text"] != gold["text"]:
            raise ValueError(f"{record_id}: gold/prediction text mismatch")
        gold_keys = canonical_relation_keys(gold)
        pred_keys = canonical_relation_keys(pred)
        all_gold.update((record_id, key) for key in gold_keys)
        all_pred.update((record_id, key) for key in pred_keys)
        pred_entity_keys = {
            (entity["start"], entity["end"], entity["type"])
            for entity in pred["entities"]
        }
        gold_entity_keys = {
            (entity["start"], entity["end"], entity["type"])
            for entity in gold["entities"]
        }
        for key in gold_keys:
            head_key = (key[0], key[1], key[2])
            tail_key = (key[4], key[5], key[6])
            if head_key in pred_entity_keys and tail_key in pred_entity_keys:
                covered_gold.add((record_id, key))
        for key in pred_keys:
            head_key = (key[0], key[1], key[2])
            tail_key = (key[4], key[5], key[6])
            if head_key in gold_entity_keys and tail_key in gold_entity_keys:
                pred_on_gold_endpoints.add((record_id, key))
        if not gold_keys:
            zero_gold_passages += 1
            if pred_keys:
                zero_gold_with_predictions += 1
                predicted_on_zero_gold += len(pred_keys)

    exact_counts = _micro_from_sets(all_gold, all_pred)  # type: ignore[arg-type]
    conditional_counts = _micro_from_sets(
        covered_gold,
        pred_on_gold_endpoints,
    )  # type: ignore[arg-type]
    known_types = sorted(
        set(relation_types or ()) | {key[1][3] for key in all_gold | all_pred}
    )
    by_type: dict[str, dict[str, float | int]] = {}
    for relation_type in known_types:
        gold_subset = {item for item in all_gold if item[1][3] == relation_type}
        pred_subset = {item for item in all_pred if item[1][3] == relation_type}
        by_type[relation_type] = _report_with_fdr(
            _micro_from_sets(gold_subset, pred_subset)  # type: ignore[arg-type]
        )
    total_gold = len(all_gold)
    return {
        "exact_relation_micro": _report_with_fdr(exact_counts),
        "by_type": by_type,
        "gold_endpoint_coverage": {
            "covered": len(covered_gold),
            "total": total_gold,
            "rate": len(covered_gold) / total_gold if total_gold else 0.0,
        },
        "conditional_on_covered_gold_endpoints": _report_with_fdr(conditional_counts),
        "zero_relation_passages": {
            "gold_zero": zero_gold_passages,
            "with_predictions": zero_gold_with_predictions,
            "predicted_relations": predicted_on_zero_gold,
        },
    }


def parse_atomic_verifier_answer(content: str) -> str:
    normalized = content.strip().lower()
    if normalized in {"yes", "yes.", "是", "是。"}:
        return "yes"
    if normalized in {"no", "no.", "否", "否。"}:
        return "no"
    return "invalid"


def build_full_ie_entity_verification_prompt(
    *,
    text: str,
    entity: Mapping[str, Any],
    entity_type_definition: str,
    evidence_passages: Sequence[str],
    output_instruction: str = "只回答yes或no",
) -> str:
    evidence = "\n".join(f"- {passage}" for passage in evidence_passages) or "无"
    return "\n\n".join(
        [
            "任务：只判断给定实体的原文边界和类型是否明确成立，不新增或修正实体。",
            f"原文：{text}",
            f"候选实体：{canonical_json(dict(entity))}",
            f"类型定义：{entity_type_definition}",
            f"参考资料（仅为次要背景，原文优先）：\n{evidence}",
            "仅在边界或类型明确错误时回答no；不确定或参考资料缺失时回答yes。",
            output_instruction,
        ]
    )


def build_relation_verification_prompt(
    *,
    record: Mapping[str, Any],
    relation_index: int,
    relation_types: Mapping[str, Mapping[str, Any]],
    evidence_passages: Sequence[str],
    output_instruction: str = "只回答yes或no",
) -> str:
    """Build a source-first prompt for one directed relation atom."""

    validate_record(record)
    rules = normalize_relation_rules(relation_types)
    if not 0 <= relation_index < len(record["relations"]):
        raise ValueError("relation_index is out of range")
    relation = record["relations"][relation_index]
    rule = rules.get(relation["type"])
    if rule is None:
        raise ValueError(f"unsupported relation type {relation['type']!r}")
    head = record["entities"][relation["head"]]
    tail = record["entities"][relation["tail"]]
    evidence = "\n".join(f"- {passage}" for passage in evidence_passages) or "无"
    return "\n\n".join(
        [
            "任务：只判断给定有向关系是否被原文同一句明确支持，不新增、反转或改写关系。",
            f"原文：{record['text']}",
            f"有向关系：head={canonical_json(dict(head))} -> {relation['type']} -> tail={canonical_json(dict(tail))}",
            f"关系定义与方向：{relation['type']}: {rule['definition']} "
            f"Allowed: {'/'.join(rule['head_types'])} -> {'/'.join(rule['tail_types'])}.",
            f"参考资料（仅为次要背景，原文优先）：\n{evidence}",
            "仅当原文未明确支持该类型或方向、端点不成立、关系跨句或仅由常识推断时回答no；不确定时回答yes。",
            output_instruction,
        ]
    )


def apply_atomic_verifier_decisions(
    pred_raw: Mapping[str, Any],
    *,
    decisions: Sequence[Mapping[str, Any]],
) -> VerificationApplication:
    """Apply valid-no deletions and cascade removed entities to relations."""

    validate_record(pred_raw)
    entity_drops: set[int] = set()
    relation_drops: set[int] = set()
    seen_units: set[tuple[str, int]] = set()
    invalid_decisions = 0
    for raw_decision in decisions:
        kind = raw_decision.get("unit_kind")
        raw_index = raw_decision.get("unit_index")
        if raw_index is None:
            raw_index = raw_decision.get("entity_index" if kind == "entity" else "relation_index")
        if kind not in {"entity", "relation"}:
            raise ValueError(f"unsupported verifier unit kind {kind!r}")
        if not isinstance(raw_index, int) or isinstance(raw_index, bool):
            raise ValueError("verifier unit index must be an integer")
        limit = len(pred_raw["entities"] if kind == "entity" else pred_raw["relations"])
        if not 0 <= raw_index < limit:
            raise ValueError(f"{kind} verifier unit index is out of range")
        unit_key = (kind, raw_index)
        if unit_key in seen_units:
            raise ValueError(f"duplicate verifier decision for {kind} {raw_index}")
        seen_units.add(unit_key)
        decision = raw_decision.get("decision")
        valid_answer = raw_decision.get("valid_answer")
        if decision not in {"yes", "no", "invalid"}:
            raise ValueError("decision must be yes, no, or invalid")
        if not isinstance(valid_answer, bool):
            raise ValueError("valid_answer must be boolean")
        if (decision in {"yes", "no"}) != valid_answer:
            raise ValueError("decision and valid_answer are inconsistent")
        if not valid_answer:
            invalid_decisions += 1
            continue
        if decision == "no":
            (entity_drops if kind == "entity" else relation_drops).add(raw_index)

    old_to_new: dict[int, int] = {}
    entities: list[dict[str, Any]] = []
    for old_index, entity in enumerate(pred_raw["entities"]):
        if old_index in entity_drops:
            continue
        old_to_new[old_index] = len(entities)
        entities.append(dict(entity))

    relations: list[dict[str, Any]] = []
    cascade_relation_drops: set[int] = set()
    for relation_index, relation in enumerate(pred_raw["relations"]):
        if relation["head"] in entity_drops or relation["tail"] in entity_drops:
            cascade_relation_drops.add(relation_index)
            continue
        if relation_index in relation_drops:
            continue
        relations.append(
            {
                "head": old_to_new[relation["head"]],
                "tail": old_to_new[relation["tail"]],
                "type": relation["type"],
            }
        )

    verified = {
        "id": pred_raw["id"],
        "text": pred_raw["text"],
        "entities": entities,
        "relations": relations,
    }
    validate_record(verified)
    return VerificationApplication(
        record=verified,
        dropped_entity_indices=tuple(sorted(entity_drops)),
        dropped_relation_indices=tuple(sorted(relation_drops)),
        cascade_dropped_relation_indices=tuple(sorted(cascade_relation_drops)),
        invalid_decisions=invalid_decisions,
    )
