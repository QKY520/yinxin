#!/usr/bin/env python3
"""Summarize P3 verification outputs and prepare dropped-unit audit sheets."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import entity_micro_counts
from equipment_ie.schema import iter_jsonl, sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-query", required=True)
    parser.add_argument("--expected-rows", type=int, default=50)
    parser.add_argument("--summary-out", required=True)
    parser.add_argument("--audit-md", required=True)
    parser.add_argument("--audit-limit", type=int, default=20)
    return parser.parse_args()


def entity_key(entity: dict[str, Any]) -> tuple[int, int, str]:
    return (int(entity["start"]), int(entity["end"]), str(entity["type"]))


def clip(value: str, limit: int = 80) -> str:
    clean = " ".join(value.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def hallucination_rate(report: dict[str, Any]) -> float:
    predicted = int(report["tp"]) + int(report["fp"])
    return int(report["fp"]) / predicted if predicted else 0.0


def write_audit_md(
    path: Path,
    *,
    rows: list[dict[str, Any]],
    dropped_units: list[dict[str, Any]],
    limit: int,
) -> None:
    row_by_id = {row["id"]: row for row in rows}
    selected = dropped_units[:limit]
    lines = [
        "# P3 Domain Dev50 E Verification Dropped-Unit Audit",
        "",
        "Fill `human_label` with `wrong_drop`, `correct_drop`, or `unclear`.",
        "",
        "| # | id | span | type | exact_gold_match | text | evidence | human_label | note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, unit in enumerate(selected, start=1):
        row = row_by_id[unit["id"]]
        evidence = row.get("rag_passages") or []
        evidence_text = " / ".join(str(item) for item in evidence[:2])
        lines.append(
            "| {index} | `{id}` | {span} | `{type}` | {gold_match} | {text} | {evidence} |  |  |".format(
                index=index,
                id=unit["id"],
                span=str(unit["span"]).replace("|", "\\|"),
                type=unit["type"],
                gold_match=str(unit["exact_gold_match"]).lower(),
                text=clip(str(row["pred_raw"]["text"])).replace("|", "\\|"),
                evidence=clip(evidence_text).replace("|", "\\|"),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    args = parse_args()
    per_query = Path(args.per_query)
    rows = [dict(row) for row in iter_jsonl(per_query, validate=False)]
    if len(rows) != args.expected_rows:
        raise ValueError(f"expected {args.expected_rows} rows, got {len(rows)}")

    gold_records = [row["gold"] for row in rows]
    raw_records = [row["pred_raw"] for row in rows]
    verified_records = [row["pred_verified"] for row in rows]
    raw_report = entity_micro_counts(gold_records, raw_records).report()
    verified_report = entity_micro_counts(gold_records, verified_records).report()

    dropped_units: list[dict[str, Any]] = []
    invalid_units = 0
    decision_counts: Counter[str] = Counter()
    type_drop_counts: Counter[str] = Counter()
    for row in rows:
        gold_keys = {entity_key(entity) for entity in row["gold"]["entities"]}
        raw_entities = row["pred_raw"]["entities"]
        for decision in row.get("verifier_decisions", []):
            decision_value = str(decision["decision"])
            decision_counts[decision_value] += 1
            if not decision.get("valid_answer", False):
                invalid_units += 1
            if decision_value == "no" and decision.get("valid_answer", False):
                entity = raw_entities[int(decision["entity_index"])]
                exact_gold_match = entity_key(entity) in gold_keys
                dropped_units.append(
                    {
                        "id": row["id"],
                        "span": entity["span"],
                        "type": entity["type"],
                        "start": entity["start"],
                        "end": entity["end"],
                        "exact_gold_match": exact_gold_match,
                    }
                )
                type_drop_counts[str(entity["type"])] += 1

    dropped_gold_matches = sum(1 for unit in dropped_units if unit["exact_gold_match"])
    summary = {
        "status": "ok",
        "per_query": str(per_query),
        "per_query_sha256": sha256_file(per_query),
        "rows": len(rows),
        "raw_entity_micro": raw_report,
        "verified_entity_micro": verified_report,
        "raw_hallucination_rate": hallucination_rate(raw_report),
        "verified_hallucination_rate": hallucination_rate(verified_report),
        "decision_counts": dict(sorted(decision_counts.items())),
        "dropped_units": len(dropped_units),
        "dropped_exact_gold_matches": dropped_gold_matches,
        "dropped_exact_gold_match_rate": dropped_gold_matches / len(dropped_units) if dropped_units else 0.0,
        "invalid_units": invalid_units,
        "type_drop_counts": dict(sorted(type_drop_counts.items())),
        "audit_md": args.audit_md,
    }

    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_audit_md(Path(args.audit_md), rows=rows, dropped_units=dropped_units, limit=args.audit_limit)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
