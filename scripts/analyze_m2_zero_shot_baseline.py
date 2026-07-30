#!/usr/bin/env python3
"""Audit and package the completed M2 schema-only zero-shot dev run."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping, Sequence
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.schema import iter_jsonl, sha256_file  # noqa: E402
from scripts.run_m2_exact_glossary_baseline import evaluate_records  # noqa: E402


M2_GATE = "M2_DOMAIN_DEV_Z_APPROVED"
M2_PHASE = "M2_DOMAIN_DEV_Z_EXECUTION"
LOCKED_CONFIG_SHA256 = (
    "2ad29153ca0d5bc377d8cd3618fb3880566a3fa190a883a975f54d91b13267a0"
)
ENTITY_TYPES = ("EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--locked-config", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--test-file", required=True)
    parser.add_argument("--per-query", required=True)
    parser.add_argument("--runner-summary", required=True)
    parser.add_argument("--execution-log", required=True)
    parser.add_argument("--vllm-log", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required for config loading") from exc
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def entity_keys(record: Mapping[str, Any]) -> set[tuple[int, int, str]]:
    return {
        (int(entity["start"]), int(entity["end"]), str(entity["type"]))
        for entity in record["entities"]
    }


def analyze_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) != 50:
        raise ValueError(f"expected 50 per-query rows, found {len(rows)}")
    ids = [str(row["id"]) for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("per-query IDs must be unique")

    gold_records: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    for row in rows:
        if row.get("dataset") != "domain_dev50":
            raise ValueError("all rows must be domain_dev50")
        if int(row.get("k", -1)) != 0:
            raise ValueError("all rows must use k=0")
        if row.get("example_ids") != []:
            raise ValueError("zero-shot rows must have no example IDs")
        if row.get("glossary_terms") != []:
            raise ValueError("zero-shot rows must have no glossary terms")
        if row.get("rag_passage_ids") != [] or row.get("rag_passages") != []:
            raise ValueError("zero-shot rows must have no RAG passages")
        if row.get("pred_verified") is not None:
            raise ValueError("verification output must be absent")
        gold = dict(row["gold"])
        prediction = dict(row["pred_raw"])
        if gold.get("id") != row.get("id") or prediction.get("id") != row.get("id"):
            raise ValueError("row, gold, and prediction IDs must match")
        if gold.get("text") != prediction.get("text"):
            raise ValueError("gold and prediction text must match")
        gold_records.append(gold)
        predictions.append(prediction)

    metrics = evaluate_records(gold_records, predictions, entity_types=ENTITY_TYPES)
    attempts = [attempt for row in rows for attempt in row["attempts"]]
    request_hashes = [str(attempt["request_hash"]) for attempt in attempts]
    if len(set(request_hashes)) != len(request_hashes):
        raise ValueError("request hashes must be unique in this one-time run")

    initial_parse_errors = Counter(
        str(row["attempts"][0]["parse_error"])
        for row in rows
        if row["attempts"][0].get("parse_error") is not None
    )
    sanitization_kinds = Counter(
        str(flag["kind"])
        for row in rows
        for flag in row.get("sanitization_flags", [])
    )
    predicted_types = Counter(
        str(entity["type"]) for record in predictions for entity in record["entities"]
    )
    gold_types = Counter(
        str(entity["type"]) for record in gold_records for entity in record["entities"]
    )

    passages_with_tp = passages_with_fp = passages_with_fn = 0
    for gold, prediction in zip(gold_records, predictions, strict=True):
        gold_set = entity_keys(gold)
        pred_set = entity_keys(prediction)
        passages_with_tp += bool(gold_set & pred_set)
        passages_with_fp += bool(pred_set - gold_set)
        passages_with_fn += bool(gold_set - pred_set)

    return {
        "metrics": metrics,
        "counts": {
            "query_records": len(rows),
            "gold_entities": sum(gold_types.values()),
            "predicted_entities": sum(predicted_types.values()),
            "passages_with_tp": passages_with_tp,
            "passages_with_fp": passages_with_fp,
            "passages_with_fn": passages_with_fn,
            "gold_type_distribution": dict(sorted(gold_types.items())),
            "predicted_type_distribution": dict(sorted(predicted_types.items())),
        },
        "requests": {
            "total_attempts": len(attempts),
            "rows_retried": sum(len(row["attempts"]) > 1 for row in rows),
            "initial_parse_failures": sum(initial_parse_errors.values()),
            "initial_parse_error_messages": dict(sorted(initial_parse_errors.items())),
            "final_parse_failures": sum(bool(row["parse_failure"]) for row in rows),
            "cache_hits": sum(bool(attempt["cache_hit"]) for attempt in attempts),
            "unique_request_hashes": len(set(request_hashes)),
            "request_hashes": request_hashes,
        },
        "sanitization": {
            "events": sum(sanitization_kinds.values()),
            "affected_passages": sum(bool(row.get("sanitization_flags")) for row in rows),
            "by_kind": dict(sorted(sanitization_kinds.items())),
        },
        "gold_records": gold_records,
    }


def require_protocol(config: Mapping[str, Any], locked: Mapping[str, Any]) -> None:
    if {key: value for key, value in config.items() if key != "execution"} != {
        key: value for key, value in locked.items() if key != "execution"
    }:
        raise ValueError("execution config differs from locked protocol outside execution")
    execution = config.get("execution", {})
    if execution.get("authorized") is not True:
        raise ValueError("execution config is not authorized")
    if execution.get("model_calls_allowed") is not True:
        raise ValueError("execution config does not allow the approved model calls")
    if execution.get("human_gate") != M2_GATE or execution.get("phase") != M2_PHASE:
        raise ValueError("unexpected M2 execution gate or phase")
    data = config.get("data", {})
    if data.get("dataset") != "domain_dev50" or "domain_test" in str(
        data.get("query_path", "")
    ).lower():
        raise ValueError("execution must be limited to domain_dev50")
    if data.get("support_path") is not None:
        raise ValueError("zero-shot execution must not read support data")
    if config.get("examples", {}).get("mode") != "none" or int(
        config.get("examples", {}).get("k", -1)
    ) != 0:
        raise ValueError("zero-shot execution requires examples.mode=none and k=0")
    if "glossary" in config or "rag" in config:
        raise ValueError("zero-shot execution must not configure glossary or RAG")
    if config.get("schema", {}).get("relation_types") != {}:
        raise ValueError("M2 Z is NER-only")


def file_record(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": sha256_file(path)}


def package(args: argparse.Namespace) -> dict[str, Any]:
    paths = {
        "config_execute.yaml": Path(args.config),
        "config_protocol_locked.yaml": Path(args.locked_config),
        "runner.py": Path(args.runner),
        "test_extraction.py": Path(args.test_file),
        "per_query.jsonl": Path(args.per_query),
        "runner_summary.json": Path(args.runner_summary),
        "execution.log": Path(args.execution_log),
        "vllm.log": Path(args.vllm_log),
        "analysis_script.py": Path(__file__),
    }
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"{name}: missing source file {path}")

    config = load_yaml(paths["config_execute.yaml"])
    locked = load_yaml(paths["config_protocol_locked.yaml"])
    if sha256_file(paths["config_protocol_locked.yaml"]) != LOCKED_CONFIG_SHA256:
        raise ValueError("locked protocol SHA256 mismatch")
    require_protocol(config, locked)

    query_path = Path(str(config["data"]["query_path"]))
    if sha256_file(query_path) != str(config["data"]["expected_sha256"]):
        raise ValueError("domain_dev SHA256 mismatch")
    query_records = list(iter_jsonl(query_path))
    if len(query_records) != int(config["data"]["expected_records"]):
        raise ValueError("domain_dev record count mismatch")
    paths["domain_dev.jsonl"] = query_path

    rows = list(iter_jsonl(paths["per_query.jsonl"], validate=False))
    row_analysis = analyze_rows(rows)
    if row_analysis.pop("gold_records") != query_records:
        raise ValueError("embedded per-query gold differs from domain_dev")

    runner_summary = load_json(paths["runner_summary.json"])
    if runner_summary.get("config_sha256") != sha256_file(paths["config_execute.yaml"]):
        raise ValueError("runner summary config SHA256 mismatch")
    if runner_summary.get("per_query_sha256") != sha256_file(paths["per_query.jsonl"]):
        raise ValueError("runner summary per-query SHA256 mismatch")
    recomputed = row_analysis["metrics"]["entity_micro"]
    for key in ("tp", "fp", "fn", "precision", "recall", "f1"):
        if runner_summary["entity_micro"][key] != recomputed[key]:
            raise ValueError(f"runner summary metric mismatch for {key}")

    cache_dir = Path(args.cache_dir)
    expected_cache_paths = {
        cache_dir / request_hash[:2] / f"{request_hash}.json"
        for request_hash in row_analysis["requests"]["request_hashes"]
    }
    actual_cache_paths = set(cache_dir.glob("*/*.json"))
    if actual_cache_paths != expected_cache_paths:
        raise ValueError("cache files do not exactly match per-query request hashes")

    vllm_text = paths["vllm.log"].read_text(encoding="utf-8", errors="replace")
    post_count = vllm_text.count("POST /v1/chat/completions")
    ok_count = sum(
        "200 OK" in line
        for line in vllm_text.splitlines()
        if "POST /v1/chat/completions" in line
    )
    if post_count != row_analysis["requests"]["total_attempts"] or ok_count != post_count:
        raise ValueError("vLLM log request count/status mismatch")

    dry_run_path = Path(str(config["outputs"]["dry_run_prompts"]))
    if dry_run_path.exists():
        raise ValueError("B001 dry-run prompt artifact unexpectedly exists")

    analysis = {
        "phase": "M2",
        "stage": "schema_only_zero_shot_domain_dev_audit",
        "status": "complete",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": config["run_id"],
        "config_sha256": sha256_file(paths["config_execute.yaml"]),
        "locked_protocol_sha256": LOCKED_CONFIG_SHA256,
        "query_sha256": sha256_file(query_path),
        **row_analysis,
        "runner": {
            "elapsed_seconds": runner_summary["elapsed_seconds"],
            "timing_totals_ms": runner_summary["timing_totals_ms"],
            "timing_means_ms": runner_summary["timing_means_ms"],
        },
        "vllm": {"completion_requests": post_count, "http_200_responses": ok_count},
        "safeguards": {
            "human_gate": M2_GATE,
            "dataset": "domain_dev50",
            "support_read": False,
            "glossary_enabled": False,
            "rag_enabled": False,
            "verification_enabled": False,
            "dry_run_artifact_exists": False,
            "cache_hits": row_analysis["requests"]["cache_hits"],
            "domain_test_configured": False,
            "labels_modified": False,
            "predictions_modified": False,
            "latex_modified": False,
        },
    }

    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = output_dir.parent / f".{output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        for name, source in paths.items():
            shutil.copy2(source, staging / name)
        shutil.copytree(cache_dir, staging / "cache")
        write_json(staging / "analysis.json", analysis)
        manifest_files = {
            path.relative_to(staging).as_posix(): file_record(path)
            for path in sorted(staging.rglob("*"))
            if path.is_file()
        }
        manifest = {
            "phase": "M2",
            "status": "complete",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": manifest_files,
            "file_count": len(manifest_files),
            "safeguards": analysis["safeguards"],
        }
        write_json(staging / "manifest.json", manifest)
        os.replace(staging, output_dir)
        os.chmod(output_dir, 0o700)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    print(json.dumps(analysis, ensure_ascii=False, sort_keys=True))
    return analysis


def main() -> int:
    package(parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
