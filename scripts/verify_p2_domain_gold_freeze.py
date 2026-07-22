#!/usr/bin/env python3
"""Verify P2 domain gold freeze artifacts.

Run on AutoDL in GPU-free mode after ``build_p2_domain_gold.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.schema import sha256_file, validate_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="/root/autodl-tmp/data")
    parser.add_argument("--project-data-root", default="/root/project/data")
    parser.add_argument("--log-root", default="/root/project/logs")
    parser.add_argument("--expected-gold", type=int, default=250)
    parser.add_argument("--expected-support", type=int, default=30)
    parser.add_argument("--expected-dev", type=int, default=50)
    parser.add_argument("--expected-test", type=int, default=170)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root)
    project_data_root = Path(args.project_data_root)
    log_root = Path(args.log_root)

    paths = {
        "gold": data_root / "domain_gold_250.jsonl",
        "support": data_root / "domain_support.jsonl",
        "dev": data_root / "domain_dev.jsonl",
        "test": data_root / "domain_test.jsonl",
    }
    expected = {
        "gold": args.expected_gold,
        "support": args.expected_support,
        "dev": args.expected_dev,
        "test": args.expected_test,
    }
    counts: dict[str, dict[str, int]] = {}
    for name, path in paths.items():
        counts[name] = validate_jsonl(path)
        if counts[name]["records"] != expected[name]:
            raise ValueError(f"{name}: expected {expected[name]} records, got {counts[name]['records']}")

    frozen_paths = {
        "data_frozen": data_root / "FROZEN",
        "project_frozen": project_data_root / "FROZEN",
    }
    for name, path in frozen_paths.items():
        if not path.is_file():
            raise ValueError(f"{name}: missing {path}")

    dedup_path = log_root / "dedup.json"
    repair_log_path = log_root / "p2_domain_gold_repair_log.json"
    manifest_path = log_root / "p2_domain_gold_manifest.json"
    dedup = read_json(dedup_path)
    repair_log = read_json(repair_log_path)
    manifest = read_json(manifest_path)

    if manifest.get("gate", {}).get("support_dev_test_exist") is not True:
        raise ValueError("manifest gate support_dev_test_exist is not true")
    if manifest.get("gate", {}).get("test_size_at_least_100") is not True:
        raise ValueError("manifest gate test_size_at_least_100 is not true")
    if manifest.get("gate", {}).get("frozen_marker_present") is not True:
        raise ValueError("manifest gate frozen_marker_present is not true")
    if manifest.get("gate", {}).get("dedup_log_present") is not True:
        raise ValueError("manifest gate dedup_log_present is not true")

    for name, item in manifest.get("files", {}).items():
        path = Path(str(item["path"]))
        if not path.is_file():
            raise ValueError(f"manifest file {name} missing: {path}")
        digest = sha256_file(path)
        if digest != item["sha256"]:
            raise ValueError(f"manifest file {name} sha256 mismatch")

    result = {
        "status": "ok",
        "counts": counts,
        "dedup": {
            "removed_count": dedup.get("removed_count"),
            "rag_corpus_records": dedup.get("rag_corpus_records"),
        },
        "repairs": repair_log.get("summary"),
        "manifest_sha256": sha256_file(manifest_path),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
