#!/usr/bin/env python3
"""Verify one P3 per-query sanity result file."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-query", required=True)
    parser.add_argument("--expected-rows", type=int, default=20)
    parser.add_argument("--max-type-share", type=float, default=0.90)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = 0
    parse_failures = 0
    pred_entities = 0
    type_counts: Counter[str] = Counter()
    with Path(args.per_query).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            row: dict[str, Any] = json.loads(line)
            rows += 1
            parse_failures += int(bool(row["parse_failure"]))
            pred_raw = row["pred_raw"]
            if set(pred_raw) != {"id", "text", "entities", "relations"}:
                raise ValueError(f"line {line_number}: pred_raw contract mismatch")
            for entity in pred_raw["entities"]:
                type_counts[str(entity["type"])] += 1
                pred_entities += 1
    if rows != args.expected_rows:
        raise ValueError(f"expected {args.expected_rows} rows, got {rows}")
    max_share = max(type_counts.values()) / pred_entities if pred_entities else 0.0
    if max_share > args.max_type_share:
        raise ValueError(f"max type share {max_share:.4f} exceeds {args.max_type_share}")
    result = {
        "status": "ok",
        "rows": rows,
        "parse_failures": parse_failures,
        "pred_entities": pred_entities,
        "type_counts": dict(sorted(type_counts.items())),
        "max_type_share": max_share,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
