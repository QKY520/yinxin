#!/usr/bin/env python3
"""Evaluate P2 annotation agreement and flag EQUIPMENT->EQUIPMENT relation confusion.

This script is intentionally GPU-free. Run it on AutoDL, not on the local
Windows control workspace.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}
RELATION_TYPES = {"USES", "HAS_METRIC", "PART_OF"}
RELATION_MATRIX = {
    "USES": {
        "head": {"EQUIPMENT", "MODULE"},
        "tail": {"EQUIPMENT", "MODULE", "TECH_SCHEME"},
    },
    "HAS_METRIC": {
        "head": {"EQUIPMENT", "MODULE"},
        "tail": {"METRIC", "TECH_SCHEME"},
    },
    "PART_OF": {
        "head": {"EQUIPMENT", "MODULE"},
        "tail": {"EQUIPMENT", "MODULE"},
    },
}

USES_TRIGGERS = ("搭载", "部署", "挂载", "装备", "配装", "携带", "装载", "加装")
PART_OF_TRIGGERS = ("组成", "包括", "包含", "构成", "一部分", "归属", "隶属", "下辖")
PART_OF_REGEXES = (re.compile(r"由.{0,40}组成"), re.compile(r"是.{0,20}的一部分"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", default="data/annotation/annotator_a_250.csv")
    parser.add_argument("--annotator-b", default="data/annotation/annotator_b_100.csv")
    parser.add_argument("--agreement-ids", default="data/annotation/agreement_sample_ids.json")
    parser.add_argument("--report-out", default="logs/p2_annotation_agreement_report.json")
    parser.add_argument("--adjudication-out", default="data/annotation/adjudication_sheet.csv")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json_field(row: dict[str, str], field: str) -> tuple[Any, str | None]:
    raw = row.get(field, "")
    if raw == "":
        return [], None
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return [], f"{field}: {exc}"


def load_text(row: dict[str, str]) -> tuple[str, str | None]:
    raw = row.get("text_json", "")
    if raw:
        try:
            value = json.loads(raw)
            if isinstance(value, str):
                return value, None
        except json.JSONDecodeError as exc:
            return row.get("text_display", ""), f"text_json: {exc}"
    return row.get("text_display", ""), None


def entity_key(ent: dict[str, Any]) -> tuple[int, int, str]:
    return (int(ent["start"]), int(ent["end"]), str(ent["type"]))


def relation_key(
    rel: dict[str, Any],
    entities: list[dict[str, Any]],
) -> tuple[int, int, str, str, int, int, str]:
    head = entities[int(rel["head"])]
    tail = entities[int(rel["tail"])]
    return (
        int(head["start"]),
        int(head["end"]),
        str(head["type"]),
        str(rel["type"]),
        int(tail["start"]),
        int(tail["end"]),
        str(tail["type"]),
    )


def prf(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def validate_annotation(
    review_id: str,
    annotator: str,
    text: str,
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    seen_spans: set[tuple[int, int]] = set()

    for idx, ent in enumerate(entities):
        try:
            start = int(ent["start"])
            end = int(ent["end"])
            etype = str(ent["type"])
            span = str(ent["span"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{review_id}:{annotator}:entity[{idx}] malformed: {exc}")
            continue
        if etype not in ENTITY_TYPES:
            errors.append(f"{review_id}:{annotator}:entity[{idx}] invalid type {etype}")
        if start < 0 or end < start or end > len(text):
            errors.append(f"{review_id}:{annotator}:entity[{idx}] invalid offsets {start}:{end}")
        elif text[start:end] != span:
            errors.append(
                f"{review_id}:{annotator}:entity[{idx}] span mismatch "
                f"{start}:{end} expected={text[start:end]!r} actual={span!r}"
            )
        span_key = (start, end)
        if span_key in seen_spans:
            errors.append(f"{review_id}:{annotator}:duplicate entity offsets {start}:{end}")
        seen_spans.add(span_key)

    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            a = entities[i]
            b = entities[j]
            if int(a["start"]) < int(b["end"]) and int(b["start"]) < int(a["end"]):
                errors.append(f"{review_id}:{annotator}:overlapping entities {i},{j}")

    for idx, rel in enumerate(relations):
        try:
            head_idx = int(rel["head"])
            tail_idx = int(rel["tail"])
            rel_type = str(rel["type"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{review_id}:{annotator}:relation[{idx}] malformed: {exc}")
            continue
        if rel_type not in RELATION_TYPES:
            errors.append(f"{review_id}:{annotator}:relation[{idx}] invalid type {rel_type}")
            continue
        if head_idx < 0 or head_idx >= len(entities) or tail_idx < 0 or tail_idx >= len(entities):
            errors.append(f"{review_id}:{annotator}:relation[{idx}] invalid entity index")
            continue
        head_type = str(entities[head_idx]["type"])
        tail_type = str(entities[tail_idx]["type"])
        matrix = RELATION_MATRIX[rel_type]
        if head_type not in matrix["head"] or tail_type not in matrix["tail"]:
            errors.append(
                f"{review_id}:{annotator}:relation[{idx}] matrix violation "
                f"{head_type}->{tail_type} {rel_type}"
            )

    return errors


def relation_context(text: str, head: dict[str, Any], tail: dict[str, Any]) -> str:
    left = max(0, min(int(head["start"]), int(tail["start"])) - 30)
    right = min(len(text), max(int(head["end"]), int(tail["end"])) + 30)
    return text[left:right]


def classify_equip_equip_partof(
    text: str,
    head: dict[str, Any],
    tail: dict[str, Any],
) -> dict[str, Any]:
    context = relation_context(text, head, tail)
    use_hits = [trigger for trigger in USES_TRIGGERS if trigger in context]
    part_hits = [trigger for trigger in PART_OF_TRIGGERS if trigger in context]
    if any(rx.search(context) for rx in PART_OF_REGEXES):
        part_hits.append("由...组成/是...的一部分")

    if use_hits and not part_hits:
        decision_hint = "LIKELY_USES_NOT_PART_OF"
    elif use_hits and part_hits:
        decision_hint = "AMBIGUOUS_MIXED_TRIGGERS"
    elif part_hits:
        decision_hint = "LIKELY_TRUE_PART_OF"
    else:
        decision_hint = "NO_EXPLICIT_COMPOSITION_TRIGGER"

    return {
        "context": context,
        "uses_triggers": use_hits,
        "part_of_triggers": sorted(set(part_hits)),
        "decision_hint": decision_hint,
    }


def audit_relations(
    rows: list[dict[str, str]],
    entity_field: str,
    relation_field: str,
    annotator: str,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]], list[str]]:
    stats = Counter()
    by_review: dict[str, list[dict[str, Any]]] = {}
    errors: list[str] = []

    for row in rows:
        review_id = row["review_id"]
        text, text_error = load_text(row)
        if text_error:
            errors.append(f"{review_id}:{annotator}:{text_error}")
        entities, ent_error = load_json_field(row, entity_field)
        relations, rel_error = load_json_field(row, relation_field)
        if ent_error:
            errors.append(f"{review_id}:{annotator}:{ent_error}")
        if rel_error:
            errors.append(f"{review_id}:{annotator}:{rel_error}")
        if not isinstance(entities, list) or not isinstance(relations, list):
            errors.append(f"{review_id}:{annotator}:annotation fields must be JSON arrays")
            continue

        for idx, rel in enumerate(relations):
            stats["relations_total"] += 1
            try:
                head = entities[int(rel["head"])]
                tail = entities[int(rel["tail"])]
                rel_type = str(rel["type"])
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            stats[f"relation_type_{rel_type}"] += 1
            if rel_type == "PART_OF" and head["type"] == "EQUIPMENT" and tail["type"] == "EQUIPMENT":
                stats["equip_equip_part_of"] += 1
                info = classify_equip_equip_partof(text, head, tail)
                stats[f"equip_equip_part_of_{info['decision_hint']}"] += 1
                if info["decision_hint"] != "LIKELY_TRUE_PART_OF":
                    stats["equip_equip_part_of_needs_adjudication"] += 1
                    by_review.setdefault(review_id, []).append(
                        {
                            "annotator": annotator,
                            "relation_index": idx,
                            "head_span": head["span"],
                            "tail_span": tail["span"],
                            **info,
                        }
                    )

    total = stats["equip_equip_part_of"]
    confused = stats["equip_equip_part_of_LIKELY_USES_NOT_PART_OF"]
    stats["equip_equip_part_of_likely_confusion_rate"] = confused / total if total else 0.0
    return dict(stats), by_review, errors


def summarize_difference(
    a_entities: list[dict[str, Any]],
    a_relations: list[dict[str, Any]],
    b_entities: list[dict[str, Any]],
    b_relations: list[dict[str, Any]],
) -> tuple[str, str, bool]:
    a_entity_set = {entity_key(ent) for ent in a_entities}
    b_entity_set = {entity_key(ent) for ent in b_entities}
    a_relation_set = {relation_key(rel, a_entities) for rel in a_relations}
    b_relation_set = {relation_key(rel, b_entities) for rel in b_relations}

    entity_summary = (
        f"A={len(a_entity_set)} B={len(b_entity_set)} "
        f"A_only={len(a_entity_set - b_entity_set)} B_only={len(b_entity_set - a_entity_set)}"
    )
    relation_summary = (
        f"A={len(a_relation_set)} B={len(b_relation_set)} "
        f"A_only={len(a_relation_set - b_relation_set)} B_only={len(b_relation_set - a_relation_set)}"
    )
    differs = a_entity_set != b_entity_set or a_relation_set != b_relation_set
    return entity_summary, relation_summary, differs


def main() -> int:
    args = parse_args()
    a_path = Path(args.annotator_a)
    b_path = Path(args.annotator_b)
    ids_path = Path(args.agreement_ids)
    report_path = Path(args.report_out)
    adjudication_path = Path(args.adjudication_out)

    a_rows = read_csv(a_path)
    b_rows = read_csv(b_path)
    with ids_path.open(encoding="utf-8") as f:
        agreement_ids = set(json.load(f)["review_ids"])

    a_by_id = {row["review_id"]: row for row in a_rows}
    b_by_id = {row["review_id"]: row for row in b_rows}

    validation_errors: list[str] = []
    validation_by_review: dict[str, list[str]] = {}
    entity_tp = entity_fp = entity_fn = 0
    relation_tp = relation_fp = relation_fn = 0
    per_row: list[dict[str, Any]] = []
    adjudication_rows: list[dict[str, str]] = []

    for review_id in sorted(agreement_ids):
        a_row = a_by_id.get(review_id)
        b_row = b_by_id.get(review_id)
        if a_row is None or b_row is None:
            validation_errors.append(f"{review_id}:missing A or B row")
            continue

        text, text_error = load_text(a_row)
        if text_error:
            validation_errors.append(f"{review_id}:A:{text_error}")
        a_entities, err = load_json_field(a_row, "annotator_a_entities_json")
        if err:
            validation_errors.append(f"{review_id}:A:{err}")
        a_relations, err = load_json_field(a_row, "annotator_a_relations_json")
        if err:
            validation_errors.append(f"{review_id}:A:{err}")
        b_entities, err = load_json_field(b_row, "annotator_b_entities_json")
        if err:
            validation_errors.append(f"{review_id}:B:{err}")
        b_relations, err = load_json_field(b_row, "annotator_b_relations_json")
        if err:
            validation_errors.append(f"{review_id}:B:{err}")

        row_validation_errors = validate_annotation(
            review_id, "A", text, a_entities, a_relations
        )
        row_validation_errors.extend(
            validate_annotation(review_id, "B", text, b_entities, b_relations)
        )
        if row_validation_errors:
            validation_by_review.setdefault(review_id, []).extend(row_validation_errors)
            validation_errors.extend(row_validation_errors)

        a_entity_set = {entity_key(ent) for ent in a_entities}
        b_entity_set = {entity_key(ent) for ent in b_entities}
        a_relation_set = {relation_key(rel, a_entities) for rel in a_relations}
        b_relation_set = {relation_key(rel, b_entities) for rel in b_relations}

        e_tp = len(a_entity_set & b_entity_set)
        e_fp = len(b_entity_set - a_entity_set)
        e_fn = len(a_entity_set - b_entity_set)
        r_tp = len(a_relation_set & b_relation_set)
        r_fp = len(b_relation_set - a_relation_set)
        r_fn = len(a_relation_set - b_relation_set)

        entity_tp += e_tp
        entity_fp += e_fp
        entity_fn += e_fn
        relation_tp += r_tp
        relation_fp += r_fp
        relation_fn += r_fn

        entity_summary, relation_summary, differs = summarize_difference(
            a_entities, a_relations, b_entities, b_relations
        )
        per_row.append(
            {
                "review_id": review_id,
                "entity_a": len(a_entity_set),
                "entity_b": len(b_entity_set),
                "entity_tp": e_tp,
                "entity_fp": e_fp,
                "entity_fn": e_fn,
                "relation_a": len(a_relation_set),
                "relation_b": len(b_relation_set),
                "relation_tp": r_tp,
                "relation_fp": r_fp,
                "relation_fn": r_fn,
            }
        )
        if differs:
            adjudication_rows.append(
                {
                    "review_id": review_id,
                    "source_type": a_row.get("source_type", ""),
                    "title_display": a_row.get("title_display", ""),
                    "text_display": a_row.get("text_display", ""),
                    "reason_flags": "A_B_DISAGREEMENT",
                    "trigger_flags_json": "[]",
                    "validation_errors_json": "[]",
                    "entity_diff_summary": entity_summary,
                    "relation_diff_summary": relation_summary,
                    "annotator_a_entities_json": a_row.get("annotator_a_entities_json", ""),
                    "annotator_a_relations_json": a_row.get("annotator_a_relations_json", ""),
                    "annotator_b_entities_json": b_row.get("annotator_b_entities_json", ""),
                    "annotator_b_relations_json": b_row.get("annotator_b_relations_json", ""),
                    "adjudicated_entities_json": "",
                    "adjudicated_relations_json": "",
                    "adjudication_notes": "",
                }
            )

    audit_a, flagged_a, audit_errors_a = audit_relations(
        a_rows, "annotator_a_entities_json", "annotator_a_relations_json", "A"
    )
    audit_b, flagged_b, audit_errors_b = audit_relations(
        b_rows, "annotator_b_entities_json", "annotator_b_relations_json", "B"
    )
    validation_errors.extend(audit_errors_a)
    validation_errors.extend(audit_errors_b)

    existing_adjudication_ids = {row["review_id"] for row in adjudication_rows}
    for review_id in sorted(set(flagged_a) | set(flagged_b)):
        a_row = a_by_id.get(review_id)
        b_row = b_by_id.get(review_id)
        if a_row is None:
            continue
        trigger_flags = flagged_a.get(review_id, []) + flagged_b.get(review_id, [])
        reason = "EQUIP_EQUIP_PART_OF_TRIGGER_AUDIT"
        if review_id in existing_adjudication_ids:
            reason = "A_B_DISAGREEMENT;EQUIP_EQUIP_PART_OF_TRIGGER_AUDIT"
            for row in adjudication_rows:
                if row["review_id"] == review_id:
                    row["reason_flags"] = reason
                    row["trigger_flags_json"] = json.dumps(trigger_flags, ensure_ascii=False)
                    break
            continue
        adjudication_rows.append(
            {
                "review_id": review_id,
                "source_type": a_row.get("source_type", ""),
                "title_display": a_row.get("title_display", ""),
                "text_display": a_row.get("text_display", ""),
                "reason_flags": reason,
                "trigger_flags_json": json.dumps(trigger_flags, ensure_ascii=False),
                "validation_errors_json": "[]",
                "entity_diff_summary": "not_in_double_annotation_sample",
                "relation_diff_summary": "trigger_audit_only",
                "annotator_a_entities_json": a_row.get("annotator_a_entities_json", ""),
                "annotator_a_relations_json": a_row.get("annotator_a_relations_json", ""),
                "annotator_b_entities_json": b_row.get("annotator_b_entities_json", "") if b_row else "",
                "annotator_b_relations_json": b_row.get("annotator_b_relations_json", "") if b_row else "",
                "adjudicated_entities_json": "",
                "adjudicated_relations_json": "",
                "adjudication_notes": "",
            }
        )

    existing_by_id = {row["review_id"]: row for row in adjudication_rows}
    for review_id, errors in sorted(validation_by_review.items()):
        existing = existing_by_id.get(review_id)
        if existing is not None:
            reasons = [part for part in existing["reason_flags"].split(";") if part]
            if "SCHEMA_VALIDATION_ERROR" not in reasons:
                reasons.append("SCHEMA_VALIDATION_ERROR")
            existing["reason_flags"] = ";".join(reasons)
            existing["validation_errors_json"] = json.dumps(errors, ensure_ascii=False)
            continue
        a_row = a_by_id.get(review_id)
        b_row = b_by_id.get(review_id)
        if a_row is None:
            continue
        adjudication_rows.append(
            {
                "review_id": review_id,
                "source_type": a_row.get("source_type", ""),
                "title_display": a_row.get("title_display", ""),
                "text_display": a_row.get("text_display", ""),
                "reason_flags": "SCHEMA_VALIDATION_ERROR",
                "trigger_flags_json": "[]",
                "validation_errors_json": json.dumps(errors, ensure_ascii=False),
                "entity_diff_summary": "schema_validation_error",
                "relation_diff_summary": "schema_validation_error",
                "annotator_a_entities_json": a_row.get("annotator_a_entities_json", ""),
                "annotator_a_relations_json": a_row.get("annotator_a_relations_json", ""),
                "annotator_b_entities_json": b_row.get("annotator_b_entities_json", "") if b_row else "",
                "annotator_b_relations_json": b_row.get("annotator_b_relations_json", "") if b_row else "",
                "adjudicated_entities_json": "",
                "adjudicated_relations_json": "",
                "adjudication_notes": "",
            }
        )

    fieldnames = [
        "review_id",
        "source_type",
        "title_display",
        "text_display",
        "reason_flags",
        "trigger_flags_json",
        "validation_errors_json",
        "entity_diff_summary",
        "relation_diff_summary",
        "annotator_a_entities_json",
        "annotator_a_relations_json",
        "annotator_b_entities_json",
        "annotator_b_relations_json",
        "adjudicated_entities_json",
        "adjudicated_relations_json",
        "adjudication_notes",
    ]
    adjudication_path.parent.mkdir(parents=True, exist_ok=True)
    with adjudication_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(adjudication_rows, key=lambda r: r["review_id"]))

    scripts_warning = [
        str(path)
        for path in (Path("scripts/p2_annotate.py"), Path("scripts/p2_annotate_v2.py"))
        if path.exists()
    ]
    report = {
        "phase": "P2",
        "stage": "annotation_agreement_with_relation_trigger_audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "annotator_a_250": {
                "path": str(a_path),
                "rows": len(a_rows),
                "sha256": sha256_file(a_path),
            },
            "annotator_b_100": {
                "path": str(b_path),
                "rows": len(b_rows),
                "sha256": sha256_file(b_path),
            },
            "agreement_sample_ids": {
                "path": str(ids_path),
                "review_ids": len(agreement_ids),
                "sha256": sha256_file(ids_path),
            },
        },
        "coverage": {
            "agreement_ids": len(agreement_ids),
            "missing_in_a": sorted(agreement_ids - set(a_by_id)),
            "missing_in_b": sorted(agreement_ids - set(b_by_id)),
            "filled_a_on_agreement": sum(
                1 for rid in agreement_ids if a_by_id.get(rid, {}).get("annotator_a_entities_json", "") != ""
            ),
            "filled_b_on_agreement": sum(
                1 for rid in agreement_ids if b_by_id.get(rid, {}).get("annotator_b_entities_json", "") != ""
            ),
        },
        "entity_micro": prf(entity_tp, entity_fp, entity_fn),
        "relation_micro": prf(relation_tp, relation_fp, relation_fn),
        "relation_trigger_audit": {
            "rule": {
                "uses_triggers": list(USES_TRIGGERS),
                "part_of_triggers": list(PART_OF_TRIGGERS) + ["由...组成", "是...的一部分"],
                "decision": "搭载/部署/挂载/装备/配装等搭载性语言裁决为 USES；组成/包括/一部分/归属等组成性语言裁决为 PART_OF。",
            },
            "annotator_a_all_250": audit_a,
            "annotator_b_100": audit_b,
        },
        "adjudication": {
            "path": str(adjudication_path),
            "rows": len(adjudication_rows),
            "reason_counts": dict(Counter(row["reason_flags"] for row in adjudication_rows)),
            "sha256": sha256_file(adjudication_path),
        },
        "validation_errors_count": len(validation_errors),
        "validation_errors_preview": validation_errors[:50],
        "gate": {
            "entity_f1_minimum": 0.80,
            "entity_f1_passed": prf(entity_tp, entity_fp, entity_fn)["f1"] >= 0.80,
            "schema_validation_passed": len(validation_errors) == 0,
            "freeze_allowed": False,
            "freeze_blockers": [
                "Adjudication sheet must be completed before gold split/freeze.",
                "True human provenance must be confirmed because pseudo-annotation scripts were found previously.",
            ],
        },
        "provenance_warning": {
            "pseudo_annotation_scripts_present": scripts_warning,
            "meaning": "If these scripts generated A/B labels, this report is diagnostic only and cannot satisfy the human agreement gate.",
        },
        "per_row_preview": per_row[:20],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(report_path)

    print(json.dumps(report["entity_micro"], ensure_ascii=False, sort_keys=True))
    print(json.dumps(report["relation_trigger_audit"], ensure_ascii=False, sort_keys=True))
    print(json.dumps(report["adjudication"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
