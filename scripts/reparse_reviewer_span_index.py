"""Offline re-parse of cached reviewer span-index responses.

This script never calls a model.  It joins the preserved per-query rows with
their cached raw response (by SHA256), applies the strict NER-only envelope
normalization, and writes an auditable row-level report plus aggregate counts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from equipment_ie.extraction import ExtractionParseError, parse_extraction_output
from equipment_ie.llm_labeling import sha256_text


ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}


def _load_cache(cache_root: Path) -> dict[str, str]:
    by_hash: dict[str, str] = {}
    for path in cache_root.rglob("*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        content = value.get("content") if isinstance(value, dict) else None
        digest = value.get("raw_output_hash") if isinstance(value, dict) else None
        if isinstance(content, str) and isinstance(digest, str) and sha256_text(content) == digest:
            by_hash[digest] = content
    return by_hash


def reparse(per_query_path: Path, cache_root: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in per_query_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    cache = _load_cache(cache_root)
    report_rows: list[dict[str, Any]] = []
    counts = {
        "rows": len(rows),
        "original_parse_failures": 0,
        "original_missing_relations_failures": 0,
        "normalized_parse_failures": 0,
        "normalized_successes": 0,
        "cache_missing": 0,
        "failure_reasons": {},
    }
    for row in rows:
        original_failure = bool(row.get("parse_failure"))
        counts["original_parse_failures"] += int(original_failure)
        attempts = row.get("attempts") or []
        raw_hash = str((attempts[-1] if attempts else {}).get("raw_output_hash") or row.get("raw_llm_output_hash") or "")
        raw = cache.get(raw_hash)
        if raw is None:
            counts["cache_missing"] += 1
            counts["normalized_parse_failures"] += 1
            reason = "cached raw output not found"
            counts["failure_reasons"][reason] = counts["failure_reasons"].get(reason, 0) + 1
            report_rows.append({"id": row.get("id"), "raw_output_hash": raw_hash, "original_parse_failure": original_failure, "normalized": False, "reason": reason})
            continue
        try:
            parsed = json.loads(raw)
            missing_relations = isinstance(parsed, dict) and set(parsed) == {"entities"}
        except json.JSONDecodeError:
            missing_relations = False
        counts["original_missing_relations_failures"] += int(original_failure and missing_relations)
        try:
            prediction = parse_extraction_output(
                raw,
                record_id=str(row["id"]),
                text=str(row["gold"]["text"]),
                entity_types=ENTITY_TYPES,
                output_mode="span_index",
            )
        except Exception as exc:  # preserve every residual parser failure
            counts["normalized_parse_failures"] += 1
            reason = f"{type(exc).__name__}: {exc}"
            counts["failure_reasons"][reason] = counts["failure_reasons"].get(reason, 0) + 1
            report_rows.append({"id": row.get("id"), "raw_output_hash": raw_hash, "original_parse_failure": original_failure, "missing_relations": missing_relations, "normalized": False, "reason": reason})
            continue
        counts["normalized_successes"] += 1
        report_rows.append({"id": row.get("id"), "raw_output_hash": raw_hash, "original_parse_failure": original_failure, "missing_relations": missing_relations, "normalized": True, "prediction": prediction})
    return {"counts": counts, "rows": report_rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = reparse(args.per_query, args.cache_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["counts"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
