#!/usr/bin/env python3
"""Versioned F7 batch finalization repair; makes no model calls."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_freeze import sha256_file  # noqa: E402
from scripts.finalize_full_ie_f7 import (  # noqa: E402
    assert_absent,
    json_bytes,
    load_context,
    validate_materialized_final,
    write_exclusive,
)
from scripts.prepare_full_ie_f7 import CELL_ORDER, GATE  # noqa: E402


REPAIR_SCHEMA_VERSION = "full-ie-f7-domain-batch1-finalize-repair-v2"
EXPECTED_EXECUTION_MANIFEST_SHA256 = (
    "893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1"
)
EXPECTED_BATCH_REPORT_PATH = (
    "/root/project/results/full_ie/final_v1/batches/"
    "f7_domain_batch1_seed42_abcd.json"
)
EXPECTED_FAILURE = "AttributeError: 'str' object has no attribute 'open'"
SOURCE_LOCK_PATHS = (
    "scripts/finalize_full_ie_f7_batch_v2.py",
    "tests/test_full_ie_f7_batch_v2.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair-manifest", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def validate_repair_manifest(
    manifest: Mapping[str, Any], *, repo_root: Path
) -> None:
    required = {
        "schema_version": REPAIR_SCHEMA_VERSION,
        "status": "AUTHORIZED_NO_MODEL_FINALIZATION_REPAIR",
        "approved_gate": GATE,
        "scope": "finalize_batch_only",
        "model_calls_allowed": False,
        "gpu_required": False,
        "matrix_before": "0/60",
        "matrix_after_if_valid": "4/60",
        "batch_report_path": EXPECTED_BATCH_REPORT_PATH,
        "preserve_v1_failure": True,
        "v1_failure": EXPECTED_FAILURE,
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise ValueError(f"repair manifest {key} changed")
    execution = manifest.get("execution_manifest")
    if not isinstance(execution, Mapping):
        raise ValueError("repair execution_manifest lock missing")
    execution_path = repo_root / str(execution.get("path", ""))
    if (
        execution.get("sha256") != EXPECTED_EXECUTION_MANIFEST_SHA256
        or not execution_path.is_file()
        or sha256_file(execution_path) != EXPECTED_EXECUTION_MANIFEST_SHA256
    ):
        raise ValueError("F7 execution manifest lock mismatch")
    source_locks = manifest.get("source_locks")
    if not isinstance(source_locks, list):
        raise ValueError("repair source locks missing")
    by_path = {
        item.get("path"): item.get("sha256")
        for item in source_locks
        if isinstance(item, Mapping)
    }
    if set(by_path) != set(SOURCE_LOCK_PATHS):
        raise ValueError("repair source lock inventory changed")
    for relative in SOURCE_LOCK_PATHS:
        path = repo_root / relative
        if not path.is_file() or sha256_file(path) != by_path[relative]:
            raise ValueError(f"repair source lock mismatch for {relative}")


def finalize_batch_v2(
    context: Mapping[str, Any],
    *,
    repair_manifest_sha256: str,
    v1_failure_log_path: str,
) -> dict[str, Any]:
    output_path = Path(context["manifest"]["batch_report_path"])
    if str(output_path) != EXPECTED_BATCH_REPORT_PATH:
        raise ValueError("F7 batch report path changed")
    assert_absent(str(output_path), label="batch report")
    cells: list[dict[str, Any]] = []
    for cell_id in CELL_ORDER:
        cell = context["cells"][cell_id]["cell"]
        summary = validate_materialized_final(cell)
        final_summary_path = Path(cell["final_summary_path"])
        cells.append(
            {
                "cell_id": cell_id,
                "final_per_query_path": cell["final_per_query_path"],
                "final_per_query_sha256": summary["per_query_sha256"],
                "final_summary_path": cell["final_summary_path"],
                "final_summary_sha256": sha256_file(final_summary_path),
                "entity_micro": summary["entity_micro"],
                "relation": summary["relation"],
                "parse_failures_relation": summary["audit"][
                    "parse_failures_relation"
                ],
            }
        )
    report = {
        "schema_version": "full-ie-f7-domain-batch1-report-v2",
        "status": "COMPLETE",
        "approved_gate": GATE,
        "batch_id": context["manifest"]["batch_id"],
        "execution_manifest_sha256": context["manifest_sha256"],
        "repair_manifest_sha256": repair_manifest_sha256,
        "v1_failure_preserved": True,
        "v1_failure_log_path": v1_failure_log_path,
        "repair": "wrap_final_summary_string_path_with_Path_before_sha256",
        "model_calls_during_repair": 0,
        "cells": cells,
        "complete_cells_before": 0,
        "complete_cells_after": 4,
        "matrix_after": "4/60",
        "aggregated_seed_claims": False,
        "paper_claims_updated": False,
        "negative_results_preserved": True,
    }
    write_exclusive(output_path, json_bytes(report))
    reloaded = load_json(output_path)
    if reloaded != report:
        raise ValueError("F7 v2 batch report failed reload validation")
    return report


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    repair_path = Path(args.repair_manifest).resolve()
    repair = load_json(repair_path)
    validate_repair_manifest(repair, repo_root=repo_root)
    execution_path = repo_root / repair["execution_manifest"]["path"]
    context = load_context(
        execution_path,
        repo_root=repo_root,
        verify_freeze_files=True,
    )
    if context["manifest_sha256"] != EXPECTED_EXECUTION_MANIFEST_SHA256:
        raise ValueError("loaded execution manifest SHA256 changed")
    report = finalize_batch_v2(
        context,
        repair_manifest_sha256=sha256_file(repair_path),
        v1_failure_log_path=repair["v1_failure_log_path"],
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
