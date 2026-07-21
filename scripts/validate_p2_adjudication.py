#!/usr/bin/env python3
"""Validate a completed P2 adjudication sheet.

Run on AutoDL in GPU-free mode. This script validates only adjudicated fields;
it does not create splits or freeze data.
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
    parser.add_argument("--input", default="data/annotation/adjudication_sheet.csv")
    parser.add_argument("--report-out", default="logs/p2_adjudication_validation_report.json")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json_field(row: dict[str, str], field: str) -> tuple[Any, str | None]:
    raw = row.get(field, "")
    if raw.strip() == "":
        return [], f"{field} is empty"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [], f"{field} JSON parse error: {exc}"
    if not isinstance(value, list):
        return [], f"{field} must be a JSON array"
    return value, None


def load_text(row: dict[str, str]) -> tuple[str, str | None]:
    raw = row.get("text_json", "")
    if raw.strip():
        try:
            value = json.loads(raw)
            if isinstance(value, str):
                return value, None
            return row.get("text_display", ""), "text_json is not a JSON string"
        except json.JSONDecodeError as exc:
            return row.get("text_display", ""), f"text_json JSON parse error: {exc}"
    return row.get("text_display", ""), None


def relation_context(text: str, head: dict[str, Any], tail: dict[str, Any]) -> str:
    left = max(0, min(int(head["start"]), int(tail["start"])) - 40)
    right = min(len(text), max(int(head["end"]), int(tail["end"])) + 40)
    return text[left:right]


def trigger_hits(context: str) -> tuple[list[str], list[str]]:
    uses = [kw for kw in USES_TRIGGERS if kw in context]
    part = [kw for kw in PART_OF_TRIGGERS if kw in context]
    if any(rx.search(context) for rx in PART_OF_REGEXES):
        part.append("由...组成/是...的一部分")
    return uses, sorted(set(part))


def validate_row(row: dict[str, str]) -> tuple[list[str], list[str], Counter[str]]:
    rid = row.get("review_id", "<missing-review-id>")
    errors: list[str] = []
    warnings: list[str] = []
    stats: Counter[str] = Counter()

    text, text_error = load_text(row)
    if text_error:
        errors.append(f"{rid}: {text_error}")

    entities, entity_error = load_json_field(row, "adjudicated_entities_json")
    relations, relation_error = load_json_field(row, "adjudicated_relations_json")
    if entity_error:
        errors.append(f"{rid}: {entity_error}")
    if relation_error:
        errors.append(f"{rid}: {relation_error}")
    if entity_error or relation_error:
        return errors, warnings, stats

    stats["rows_filled"] += 1
    stats["entities_total"] += len(entities)
    stats["relations_total"] += len(relations)

    for idx, ent in enumerate(entities):
        if not isinstance(ent, dict):
            errors.append(f"{rid}: entity[{idx}] must be object")
            continue
        missing = {"start", "end", "type", "span"} - set(ent)
        if missing:
            errors.append(f"{rid}: entity[{idx}] missing {sorted(missing)}")
            continue
        try:
            start = int(ent["start"])
            end = int(ent["end"])
        except (TypeError, ValueError):
            errors.append(f"{rid}: entity[{idx}] offsets must be integers")
            continue
        etype = str(ent["type"])
        span = str(ent["span"])
        if etype not in ENTITY_TYPES:
            errors.append(f"{rid}: entity[{idx}] invalid type {etype}")
        if start < 0 or end < start or end > len(text):
            errors.append(f"{rid}: entity[{idx}] invalid offsets {start}:{end}")
            continue
        expected = text[start:end]
        if expected != span:
            errors.append(
                f"{rid}: entity[{idx}] span mismatch {start}:{end}; "
                f"expected={expected!r}; actual={span!r}"
            )

    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            a = entities[i]
            b = entities[j]
            try:
                if int(a["start"]) < int(b["end"]) and int(b["start"]) < int(a["end"]):
                    errors.append(
                        f"{rid}: overlapping entities {i}/{j}: "
                        f"{a.get('span')} / {b.get('span')}"
                    )
            except (KeyError, TypeError, ValueError):
                continue

    seen_relations: set[tuple[int, int, str]] = set()
    for idx, rel in enumerate(relations):
        if not isinstance(rel, dict):
            errors.append(f"{rid}: relation[{idx}] must be object")
            continue
        missing = {"head", "tail", "type"} - set(rel)
        if missing:
            errors.append(f"{rid}: relation[{idx}] missing {sorted(missing)}")
            continue
        try:
            head_idx = int(rel["head"])
            tail_idx = int(rel["tail"])
        except (TypeError, ValueError):
            errors.append(f"{rid}: relation[{idx}] head/tail must be integers")
            continue
        rel_type = str(rel["type"])
        if rel_type not in RELATION_TYPES:
            errors.append(f"{rid}: relation[{idx}] invalid type {rel_type}")
            continue
        if head_idx < 0 or head_idx >= len(entities) or tail_idx < 0 or tail_idx >= len(entities):
            errors.append(f"{rid}: relation[{idx}] invalid entity index {head_idx}->{tail_idx}")
            continue
        key = (head_idx, tail_idx, rel_type)
        if key in seen_relations:
            warnings.append(f"{rid}: duplicate relation {key}")
        seen_relations.add(key)

        head = entities[head_idx]
        tail = entities[tail_idx]
        head_type = str(head["type"])
        tail_type = str(tail["type"])
        matrix = RELATION_MATRIX[rel_type]
        if head_type not in matrix["head"] or tail_type not in matrix["tail"]:
            errors.append(
                f"{rid}: relation[{idx}] matrix violation "
                f"{head_type}->{tail_type} {rel_type}"
            )

        stats[f"relation_type_{rel_type}"] += 1
        if rel_type == "PART_OF" and head_type == "EQUIPMENT" and tail_type == "EQUIPMENT":
            stats["equip_equip_part_of"] += 1
            context = relation_context(text, head, tail)
            uses, part = trigger_hits(context)
            if uses and not part:
                errors.append(
                    f"{rid}: relation[{idx}] EQUIPMENT->EQUIPMENT PART_OF has "
                    f"USES trigger(s) {uses} without composition trigger; "
                    f"head={head.get('span')} tail={tail.get('span')}"
                )
                stats["equip_equip_part_of_with_uses_trigger_only"] += 1
            elif not part:
                warnings.append(
                    f"{rid}: relation[{idx}] EQUIPMENT->EQUIPMENT PART_OF has no "
                    f"explicit composition trigger in local context; "
                    f"head={head.get('span')} tail={tail.get('span')}"
                )
                stats["equip_equip_part_of_without_composition_trigger"] += 1
            else:
                stats["equip_equip_part_of_with_composition_trigger"] += 1

    return errors, warnings, stats


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    report_path = Path(args.report_out)
    with input_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    all_errors: list[str] = []
    all_warnings: list[str] = []
    stats: Counter[str] = Counter()

    for row in rows:
        errors, warnings, row_stats = validate_row(row)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        stats.update(row_stats)

    missing_notes = [
        row.get("review_id", "")
        for row in rows
        if row.get("adjudication_notes", "").strip() == ""
    ]
    report = {
        "phase": "P2",
        "stage": "adjudication_validation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path": str(input_path),
            "rows": len(rows),
            "sha256": sha256_file(input_path),
        },
        "stats": dict(sorted(stats.items())),
        "notes": {
            "empty_adjudication_notes_count": len(missing_notes),
            "empty_adjudication_notes_preview": missing_notes[:30],
        },
        "errors_count": len(all_errors),
        "errors_preview": all_errors[:80],
        "warnings_count": len(all_warnings),
        "warnings_preview": all_warnings[:120],
        "gate": {
            "validation_passed": len(all_errors) == 0,
            "warning_free": len(all_warnings) == 0,
            "split_or_freeze_allowed": False,
            "next_action": (
                "Fix validation errors before any split/freeze."
                if all_errors
                else "Review warnings, then ask human approval before split/freeze."
            ),
        },
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = report_path.with_suffix(report_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    tmp.replace(report_path)

    print(json.dumps({
        "rows": len(rows),
        "sha256": report["input"]["sha256"],
        "errors_count": len(all_errors),
        "warnings_count": len(all_warnings),
        "stats": report["stats"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if len(all_errors) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
