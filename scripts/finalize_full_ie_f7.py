#!/usr/bin/env python3
"""Preflight, validate, and materialize the bounded F7 domain batch."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (  # noqa: E402
    build_request_envelope,
    entity_micro_counts,
    prompt_hash,
)
from equipment_ie.full_ie import (  # noqa: E402
    build_stage_r_retry_prompt,
    relation_evaluation_report,
    validate_approved_relation_matrix,
)
from equipment_ie.full_ie_freeze import (  # noqa: E402
    PER_QUERY_REQUIRED_FIELDS,
    canonical_sha256,
    sha256_file,
    validate_freeze_manifest,
)
from equipment_ie.llm_labeling import (  # noqa: E402
    request_hash,
    sha256_text,
)
from equipment_ie.schema import validate_record  # noqa: E402
from scripts import run_stage_r  # noqa: E402
from scripts.prepare_full_ie_f7 import (  # noqa: E402
    BATCH_CONTRACT_SHA256,
    CELL_INVENTORY_SHA256,
    CELL_ORDER,
    FREEZE_CANONICAL_SHA256,
    FREEZE_MANIFEST_SHA256,
    GATE,
    LEGACY_CONFIGS,
    PHASE,
    compatibility_view_rows,
)


SCHEMA_VERSION = "full-ie-f7-domain-batch1-execution-v1"
EXPECTED_ROWS = 170
EXPECTED_K = 5
EXPECTED_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight-batch", "preflight-cell", "finalize-cell"):
        child = subparsers.add_parser(command)
        child.add_argument("--manifest", required=True)
        child.add_argument("--repo-root", default=str(PROJECT_ROOT))
        if command != "preflight-batch":
            child.add_argument("--cell-id", required=True, choices=CELL_ORDER)
    child = subparsers.add_parser("finalize-batch")
    child.add_argument("--manifest", required=True)
    child.add_argument("--repo-root", default=str(PROJECT_ROOT))
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def assert_metric_tree_matches(expected: Any, actual: Any, *, label: str) -> None:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        if set(expected) != set(actual):
            raise ValueError(f"{label}: metric keys differ")
        for key in expected:
            assert_metric_tree_matches(expected[key], actual[key], label=f"{label}.{key}")
        return
    if (
        isinstance(expected, (int, float))
        and not isinstance(expected, bool)
        and isinstance(actual, (int, float))
        and not isinstance(actual, bool)
    ):
        if not math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"{label}: expected {expected}, found {actual}")
        return
    if expected != actual:
        raise ValueError(f"{label}: expected {expected!r}, found {actual!r}")


def percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1))
    return float(ordered[index])


def latency_report(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {"mean_ms": 0.0, "median_ms": 0.0, "p95_ms": 0.0, "max_ms": 0.0}
    return {
        "mean_ms": statistics.fmean(values),
        "median_ms": statistics.median(values),
        "p95_ms": percentile(values, 0.95),
        "max_ms": max(values),
    }


def validate_execution_config(
    config: Mapping[str, Any],
    *,
    cell: Mapping[str, Any],
    frozen_cell: Mapping[str, Any],
    stage_r_node: Mapping[str, Any],
    support_lock: Mapping[str, Any],
) -> None:
    config_name = cell["config"]
    if config.get("config_name") != config_name:
        raise ValueError(f"{cell['cell_id']}: execution config name mismatch")
    execution = config.get("execution")
    if not isinstance(execution, Mapping):
        raise ValueError(f"{cell['cell_id']}: execution block missing")
    required_execution = {
        "phase": PHASE,
        "authorized": True,
        "human_gate": GATE,
        "model_calls_allowed": True,
        "gpu_required": True,
    }
    for key, expected in required_execution.items():
        if execution.get(key) != expected:
            raise ValueError(f"{cell['cell_id']}: execution.{key} changed")
    if config.get("data") != {"dataset": "domain"}:
        raise ValueError(f"{cell['cell_id']}: dataset contract changed")
    if config.get("replay", {}).get("reuse_stage_n_metadata") is not True:
        raise ValueError(f"{cell['cell_id']}: Stage N replay disabled")
    input_config = config.get("input")
    if not isinstance(input_config, Mapping):
        raise ValueError(f"{cell['cell_id']}: input block missing")
    if (
        input_config.get("stage_n_per_query_path") != cell["compatibility_view_path"]
        or input_config.get("support_path") != support_lock["path"]
        or input_config.get("expected_rows") != EXPECTED_ROWS
    ):
        raise ValueError(f"{cell['cell_id']}: Stage R inputs changed")
    if config.get("generation") != stage_r_node["generation"]:
        raise ValueError(f"{cell['cell_id']}: generation settings changed")
    if config.get("prompt", {}).get("version") != stage_r_node["prompt_version"]:
        raise ValueError(f"{cell['cell_id']}: prompt version changed")
    if config.get("prompt", {}).get("output_instruction") != run_stage_r.FIXED_OUTPUT_INSTRUCTION:
        raise ValueError(f"{cell['cell_id']}: output instruction changed")
    if config.get("prompt", {}).get("retry_suffix") != run_stage_r.FIXED_RETRY_SUFFIX:
        raise ValueError(f"{cell['cell_id']}: retry suffix changed")
    parsing = config.get("parsing", {})
    if parsing.get("drop_invalid_relations") is not True:
        raise ValueError(f"{cell['cell_id']}: relation sanitizer changed")
    model = config.get("model", {})
    required_model = {
        "name": "/root/autodl-tmp/models/qwen2.5-7b",
        "base_url": "http://127.0.0.1:8000",
        "timeout_seconds": 300,
        "api_key": "EMPTY",
    }
    if model != required_model:
        raise ValueError(f"{cell['cell_id']}: model endpoint contract changed")
    if config.get("cache") != {"dir": cell["cache_dir"]}:
        raise ValueError(f"{cell['cell_id']}: cache path changed")
    expected_outputs = {
        "per_query": cell["stage_r_per_query_path"],
        "summary": cell["stage_r_summary_path"],
    }
    if config.get("outputs") != expected_outputs:
        raise ValueError(f"{cell['cell_id']}: Stage R output paths changed")
    relation_types = config.get("schema", {}).get("relation_types")
    validate_approved_relation_matrix(relation_types)
    lock = config.get("resource_lock", {})
    if lock.get("support", {}).get("sha256") != support_lock["sha256"]:
        raise ValueError(f"{cell['cell_id']}: support lock changed")
    if lock.get("original_stage_n", {}).get("sha256") != cell["original_stage_n_sha256"]:
        raise ValueError(f"{cell['cell_id']}: original Stage N lock changed")
    if lock.get("compatibility_view", {}).get("sha256") != cell["compatibility_view_sha256"]:
        raise ValueError(f"{cell['cell_id']}: compatibility view lock changed")
    f7_contract = config.get("f7_contract", {})
    expected_f7 = {
        "batch_id": "full-ie-f7-domain-final-b01-k5-seed42-abcd",
        "cell_id": cell["cell_id"],
        "config_id": cell["config_id"],
        "config_contract_sha256": cell["config_contract_sha256"],
        "stage_work": "stage_r_only",
        "rerun_stage_n": False,
        "run_verification": False,
    }
    if f7_contract != expected_f7:
        raise ValueError(f"{cell['cell_id']}: F7 cell contract changed")
    if frozen_cell["execution"]["config_id"] != cell["config_id"]:
        raise ValueError(f"{cell['cell_id']}: frozen config ID mismatch")


def load_context(
    manifest_path: Path, *, repo_root: Path, verify_freeze_files: bool = True
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("F7 execution manifest schema changed")
    if manifest.get("status") != "AUTHORIZED_PREINFERENCE":
        raise ValueError("F7 execution manifest status changed")
    if manifest.get("approved_gate") != GATE:
        raise ValueError("F7 execution gate changed")
    expected_authorization = {
        "authorized": True,
        "final_evaluation_allowed": True,
        "gpu_required_for_model_calls": True,
        "model_calls_allowed": True,
        "stage_n_rerun_allowed": False,
        "verification_allowed": False,
    }
    if manifest.get("authorization") != expected_authorization:
        raise ValueError("F7 execution authorization changed")
    scope = manifest.get("scope", {})
    if scope.get("cell_order") != list(CELL_ORDER):
        raise ValueError("F7 cell order changed")
    if (
        scope.get("dataset") != "domain"
        or scope.get("split") != "domain_test"
        or scope.get("k") != EXPECTED_K
        or scope.get("seed") != EXPECTED_SEED
        or scope.get("rows_per_cell") != EXPECTED_ROWS
        or scope.get("stage_work") != "stage_r_only"
    ):
        raise ValueError("F7 scope changed")

    batch_path = repo_root / manifest["batch_contract"]["path"]
    freeze_path = repo_root / manifest["freeze"]["manifest_path"]
    inventory_path = repo_root / manifest["freeze"]["cell_inventory_path"]
    if (
        manifest["batch_contract"]["sha256"] != BATCH_CONTRACT_SHA256
        or sha256_file(batch_path) != BATCH_CONTRACT_SHA256
    ):
        raise ValueError("F7 batch contract lock mismatch")
    if (
        manifest["freeze"]["manifest_sha256"] != FREEZE_MANIFEST_SHA256
        or sha256_file(freeze_path) != FREEZE_MANIFEST_SHA256
    ):
        raise ValueError("F5 freeze file lock mismatch")
    if (
        manifest["freeze"]["cell_inventory_sha256"] != CELL_INVENTORY_SHA256
        or sha256_file(inventory_path) != CELL_INVENTORY_SHA256
    ):
        raise ValueError("F5 cell inventory lock mismatch")
    freeze = load_json(freeze_path)
    validate_freeze_manifest(
        freeze,
        repo_root=repo_root,
        verify_files=verify_freeze_files,
    )
    if canonical_sha256(freeze) != FREEZE_CANONICAL_SHA256:
        raise ValueError("F5 canonical lock mismatch")

    for source_lock in manifest.get("source_locks", []):
        path = repo_root / source_lock["path"]
        if not path.is_file() or sha256_file(path) != source_lock["sha256"]:
            raise ValueError(f"F7 source lock mismatch for {source_lock['path']}")

    frozen_cells = {
        item["cell_id"]: item for item in freeze["run_manifest"]["cells"]
    }
    stage_r_nodes = {
        item["node_id"]: item for item in freeze["execution_nodes"]["stage_r"]
    }
    support_lock = freeze["resources"]["domain_support"]
    cells = manifest.get("cells")
    if not isinstance(cells, list) or [item.get("cell_id") for item in cells] != list(CELL_ORDER):
        raise ValueError("F7 manifest cells changed")

    import yaml

    prepared: dict[str, dict[str, Any]] = {}
    for cell in cells:
        cell_id = cell["cell_id"]
        frozen = frozen_cells[cell_id]
        if (
            cell["config_contract_sha256"] != frozen["config_contract_sha256"]
            or cell["original_stage_n_sha256"] != frozen["stage_n"]["artifact_sha256"]
        ):
            raise ValueError(f"{cell_id}: F5 cell locks changed")
        original_path = Path(cell["original_stage_n_path"])
        view_path = Path(cell["compatibility_view_path"])
        if sha256_file(original_path) != cell["original_stage_n_sha256"]:
            raise ValueError(f"{cell_id}: original Stage N SHA256 mismatch")
        if sha256_file(view_path) != cell["compatibility_view_sha256"]:
            raise ValueError(f"{cell_id}: compatibility view SHA256 mismatch")
        original_rows = load_jsonl(original_path)
        view_rows = load_jsonl(view_path)
        expected_view = compatibility_view_rows(
            original_rows,
            config=cell["config"],
            expected_rows=EXPECTED_ROWS,
        )
        if view_rows != expected_view:
            raise ValueError(f"{cell_id}: compatibility view changed beyond metadata")
        config_path = repo_root / cell["execution_config_path"]
        if sha256_file(config_path) != cell["execution_config_sha256"]:
            raise ValueError(f"{cell_id}: execution config SHA256 mismatch")
        config_value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if not isinstance(config_value, dict):
            raise ValueError(f"{config_path}: expected YAML object")
        node = stage_r_nodes[frozen["execution"]["stage_r_node"]]
        validate_execution_config(
            config_value,
            cell=cell,
            frozen_cell=frozen,
            stage_r_node=node,
            support_lock=support_lock,
        )
        prepared[cell_id] = {
            "cell": cell,
            "frozen_cell": frozen,
            "stage_r_node": node,
            "config_path": config_path,
            "config": config_value,
            "original_rows": original_rows,
            "view_rows": view_rows,
        }
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "manifest_sha256": sha256_file(manifest_path),
        "freeze": freeze,
        "support_lock": support_lock,
        "cells": prepared,
    }


def assert_absent(path_text: str, *, label: str) -> None:
    path = Path(path_text)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"{label}: output collision at {path}")


def validate_materialized_final(cell: Mapping[str, Any]) -> dict[str, Any]:
    per_query = Path(cell["final_per_query_path"])
    summary_path = Path(cell["final_summary_path"])
    if not per_query.is_file() or not summary_path.is_file():
        raise ValueError(f"{cell['cell_id']}: final cell is incomplete")
    summary = load_json(summary_path)
    if (
        summary.get("status") != "COMPLETE"
        or summary.get("cell_id") != cell["cell_id"]
        or summary.get("rows") != EXPECTED_ROWS
        or summary.get("per_query_sha256") != sha256_file(per_query)
    ):
        raise ValueError(f"{cell['cell_id']}: final materialization validation failed")
    return summary


def preflight_batch(context: Mapping[str, Any]) -> dict[str, Any]:
    for prepared in context["cells"].values():
        cell = prepared["cell"]
        for field in (
            "stage_r_per_query_path",
            "stage_r_summary_path",
            "final_per_query_path",
            "final_summary_path",
            "cache_dir",
        ):
            assert_absent(cell[field], label=cell["cell_id"])
    assert_absent(context["manifest"]["batch_report_path"], label="batch report")
    return {
        "status": "PASS",
        "command": "preflight-batch",
        "cells": 4,
        "rows": 680,
        "model_calls": 0,
        "manifest_sha256": context["manifest_sha256"],
        "all_output_and_cache_targets_absent": True,
    }


def preflight_cell(context: Mapping[str, Any], cell_id: str) -> dict[str, Any]:
    target_index = CELL_ORDER.index(cell_id)
    for index, identifier in enumerate(CELL_ORDER):
        cell = context["cells"][identifier]["cell"]
        if index < target_index:
            validate_materialized_final(cell)
            if not Path(cell["stage_r_per_query_path"]).is_file() or not Path(
                cell["stage_r_summary_path"]
            ).is_file():
                raise ValueError(f"{identifier}: prior Stage R artifacts missing")
            continue
        for field in (
            "stage_r_per_query_path",
            "stage_r_summary_path",
            "final_per_query_path",
            "final_summary_path",
            "cache_dir",
        ):
            assert_absent(cell[field], label=identifier)
    return {
        "status": "PASS",
        "command": "preflight-cell",
        "cell_id": cell_id,
        "prior_cells_validated": target_index,
        "current_and_future_targets_absent": True,
        "model_calls": 0,
    }


def relation_matrix_check(
    record: Mapping[str, Any], relation_types: Mapping[str, Mapping[str, Any]]
) -> None:
    for index, relation in enumerate(record["relations"]):
        rule = relation_types.get(relation["type"])
        if rule is None:
            raise ValueError(f"unsupported relation type at index {index}")
        head_type = record["entities"][relation["head"]]["type"]
        tail_type = record["entities"][relation["tail"]]["type"]
        if head_type not in rule["head_types"] or tail_type not in rule["tail_types"]:
            raise ValueError(f"relation type matrix violation at index {index}")


def validate_cache_entry(
    *, cache_dir: Path, digest: str, expected_envelope: Mapping[str, Any], raw_hash: str
) -> None:
    path = cache_dir / digest[:2] / f"{digest}.json"
    entry = load_json(path)
    content = entry.get("content")
    if (
        entry.get("request_hash") != digest
        or entry.get("request") != expected_envelope
        or not isinstance(content, str)
        or entry.get("raw_output_hash") != raw_hash
        or sha256_text(content) != raw_hash
        or not isinstance(entry.get("response"), Mapping)
    ):
        raise ValueError(f"cache entry validation failed: {path}")


def validate_stage_artifacts(prepared: Mapping[str, Any]) -> dict[str, Any]:
    cell = prepared["cell"]
    config = prepared["config"]
    config_path = prepared["config_path"]
    view_rows = prepared["view_rows"]
    stage_path = Path(cell["stage_r_per_query_path"])
    summary_path = Path(cell["stage_r_summary_path"])
    if not stage_path.is_file() or not summary_path.is_file():
        raise ValueError(f"{cell['cell_id']}: Stage R artifacts are incomplete")
    stage_rows = load_jsonl(stage_path)
    summary = load_json(summary_path)
    if len(stage_rows) != EXPECTED_ROWS:
        raise ValueError(f"{cell['cell_id']}: expected 170 Stage R rows")
    if [row.get("id") for row in stage_rows] != [row.get("id") for row in view_rows]:
        raise ValueError(f"{cell['cell_id']}: Stage R row order or IDs changed")

    relation_types = validate_approved_relation_matrix(
        config["schema"]["relation_types"]
    )
    support_by_id = run_stage_r.load_support_by_id(config["input"]["support_path"])
    cache_dir = Path(cell["cache_dir"])
    request_hashes: set[str] = set()
    gold_records: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    parse_failures = 0
    deterministic_skips = 0
    model_requests = 0
    retries = 0
    latency_values: list[float] = []
    sanitizer_counts: Counter[str] = Counter()

    for source, row in zip(view_rows, stage_rows):
        record_id = source["id"]
        missing = set(PER_QUERY_REQUIRED_FIELDS) - set(row)
        if missing:
            raise ValueError(f"{cell['cell_id']}/{record_id}: missing fields {sorted(missing)}")
        if (
            row.get("dataset") != "domain"
            or row.get("config") != cell["config"]
            or row.get("k") != EXPECTED_K
            or row.get("seed") != EXPECTED_SEED
        ):
            raise ValueError(f"{cell['cell_id']}/{record_id}: output metadata changed")
        if row.get("gold") != source.get("gold"):
            raise ValueError(f"{cell['cell_id']}/{record_id}: gold changed")
        prediction = row.get("pred_raw")
        if not isinstance(prediction, Mapping):
            raise ValueError(f"{cell['cell_id']}/{record_id}: pred_raw missing")
        validate_record(prediction)
        if (
            prediction["id"] != record_id
            or prediction["text"] != source["pred_raw"]["text"]
            or prediction["entities"] != source["pred_raw"]["entities"]
            or row.get("pred_entities_stage_n") != source["pred_raw"]["entities"]
            or row.get("pred_relations_stage_r") != prediction["relations"]
            or row.get("pred_verified") is not None
        ):
            raise ValueError(f"{cell['cell_id']}/{record_id}: Stage N or prediction changed")
        if (
            row.get("example_ids") != source.get("example_ids")
            or row.get("glossary_terms") != source.get("glossary_terms")
            or row.get("rag_passage_ids") != source.get("rag_passage_ids")
            or row.get("rag_passages") != source.get("rag_passages")
            or row.get("ner_prompt_hash") != source.get("prompt_hash")
            or row.get("raw_ner_output_hash") != source.get("raw_llm_output_hash")
            or row.get("parse_failure_ner") != source.get("parse_failure")
            or row.get("verifier_decisions") != []
            or row.get("verifier_prompt_hashes") != []
        ):
            raise ValueError(f"{cell['cell_id']}/{record_id}: replay metadata changed")
        relation_matrix_check(prediction, relation_types)
        plan = run_stage_r.build_stage_r_row_plan(
            row=source,
            support_by_id=support_by_id,
            relation_types=relation_types,
            output_instruction=config["prompt"]["output_instruction"],
        )
        run_stage_r.validate_source_resource_contract(cell["config"], plan)
        expected_prompt_hash = prompt_hash(plan["prompt"]) if plan["prompt"] is not None else None
        if row.get("relation_prompt_hash") != expected_prompt_hash:
            raise ValueError(f"{cell['cell_id']}/{record_id}: relation prompt hash mismatch")
        attempts = row.get("relation_attempts")
        if not isinstance(attempts, list) or len(attempts) > 2:
            raise ValueError(f"{cell['cell_id']}/{record_id}: invalid relation attempts")
        if plan["skip_reason"] is not None:
            deterministic_skips += 1
            if attempts or row.get("relation_skip_reason") != plan["skip_reason"]:
                raise ValueError(f"{cell['cell_id']}/{record_id}: deterministic skip changed")
            if prediction["relations"] or row.get("raw_relation_output_hash") is not None:
                raise ValueError(f"{cell['cell_id']}/{record_id}: skipped row has model output")
        else:
            if not attempts or row.get("relation_skip_reason") is not None:
                raise ValueError(f"{cell['cell_id']}/{record_id}: model attempt missing")
            attempt_prompt = str(plan["prompt"])
            for index, attempt in enumerate(attempts, start=1):
                if attempt.get("attempt") != index:
                    raise ValueError(f"{cell['cell_id']}/{record_id}: attempt numbering changed")
                envelope = build_request_envelope(
                    prompt=attempt_prompt,
                    model=config["model"]["name"],
                    generation=config["generation"],
                    run_id=config["run_id"],
                    config_hash=cell["execution_config_sha256"],
                )
                digest = request_hash(envelope)
                if attempt.get("request_hash") != digest:
                    raise ValueError(f"{cell['cell_id']}/{record_id}: request hash mismatch")
                raw_hash = attempt.get("raw_output_hash")
                if not isinstance(raw_hash, str):
                    raise ValueError(f"{cell['cell_id']}/{record_id}: raw output hash missing")
                validate_cache_entry(
                    cache_dir=cache_dir,
                    digest=digest,
                    expected_envelope=envelope,
                    raw_hash=raw_hash,
                )
                request_hashes.add(digest)
                if index == 1 and len(attempts) == 2:
                    parse_error = attempt.get("parse_error")
                    if not isinstance(parse_error, str) or not parse_error:
                        raise ValueError(f"{cell['cell_id']}/{record_id}: retry lacks parser error")
                    attempt_prompt = build_stage_r_retry_prompt(
                        base_prompt=str(plan["prompt"]),
                        parse_error=parse_error,
                        retry_suffix=config["prompt"]["retry_suffix"],
                    )
            if row.get("raw_relation_output_hash") != attempts[-1]["raw_output_hash"]:
                raise ValueError(f"{cell['cell_id']}/{record_id}: final raw hash mismatch")
        final_parse_error = attempts[-1].get("parse_error") if attempts else None
        expected_parse_failure = final_parse_error is not None
        if bool(row.get("parse_failure_relation")) != expected_parse_failure:
            raise ValueError(f"{cell['cell_id']}/{record_id}: parse-failure flag mismatch")
        if expected_parse_failure:
            parse_failures += 1
            if prediction["relations"]:
                raise ValueError(f"{cell['cell_id']}/{record_id}: failed parse kept relations")
        model_requests += len(attempts)
        retries += max(0, len(attempts) - 1)
        latency = float(row.get("latency_relation_ms", 0.0))
        latency_values.append(latency)
        if not math.isclose(
            latency,
            sum(float(attempt.get("latency_ms", 0.0)) for attempt in attempts),
            rel_tol=0.0,
            abs_tol=0.002,
        ):
            raise ValueError(f"{cell['cell_id']}/{record_id}: relation latency mismatch")
        flags = row.get("sanitization_flags")
        if not isinstance(flags, list):
            raise ValueError(f"{cell['cell_id']}/{record_id}: sanitizer flags invalid")
        for flag in flags:
            if not isinstance(flag, Mapping):
                raise ValueError(f"{cell['cell_id']}/{record_id}: sanitizer flag invalid")
            kind = str(flag.get("kind", ""))
            if kind.startswith("RELATION_DROPPED_"):
                sanitizer_counts[kind] += 1
        gold_records.append(dict(row["gold"]))
        predictions.append(dict(prediction))

    cache_files = {path.stem for path in cache_dir.glob("*/*.json")}
    if cache_files != request_hashes:
        raise ValueError(f"{cell['cell_id']}: cache inventory does not match request hashes")
    per_query_sha256 = sha256_file(stage_path)
    entity_report = entity_micro_counts(gold_records, predictions).report()
    relation_report = relation_evaluation_report(
        gold_records,
        predictions,
        relation_types=tuple(relation_types),
    )
    if summary.get("config_sha256") != cell["execution_config_sha256"]:
        raise ValueError(f"{cell['cell_id']}: summary config hash mismatch")
    if summary.get("source_stage_n_sha256") != cell["compatibility_view_sha256"]:
        raise ValueError(f"{cell['cell_id']}: summary source view hash mismatch")
    if summary.get("per_query_sha256") != per_query_sha256:
        raise ValueError(f"{cell['cell_id']}: summary per-query hash mismatch")
    expected_counts = {
        "rows": EXPECTED_ROWS,
        "model_requests": model_requests,
        "deterministic_skips": deterministic_skips,
        "parse_failures_relation": parse_failures,
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            raise ValueError(f"{cell['cell_id']}: summary {key} mismatch")
    assert_metric_tree_matches(summary.get("entity_micro"), entity_report, label="entity_micro")
    assert_metric_tree_matches(summary.get("relation"), relation_report, label="relation")
    return {
        "rows": EXPECTED_ROWS,
        "per_query_sha256": per_query_sha256,
        "stage_r_summary_sha256": sha256_file(summary_path),
        "entity_micro": entity_report,
        "relation": relation_report,
        "entity_false_positives": entity_report["fp"],
        "parse_failures_relation": parse_failures,
        "parse_failure_rate_relation": parse_failures / EXPECTED_ROWS,
        "model_requests": model_requests,
        "deterministic_skips": deterministic_skips,
        "retry_count": retries,
        "relation_sanitizer_events": dict(sorted(sanitizer_counts.items())),
        "unsupported_entity_or_relation_types": 0,
        "relation_type_matrix_violations": 0,
        "latency_relation": latency_report(latency_values),
        "cache_entries": len(cache_files),
        "prompt_request_hashes": len(request_hashes),
        "verification_run": False,
        "negative_results_preserved": True,
    }


def finalize_cell(context: Mapping[str, Any], cell_id: str) -> dict[str, Any]:
    prepared = context["cells"][cell_id]
    cell = prepared["cell"]
    for field in ("final_per_query_path", "final_summary_path"):
        assert_absent(cell[field], label=cell_id)
    audit = validate_stage_artifacts(prepared)
    if audit["parse_failure_rate_relation"] >= 0.10:
        raise RuntimeError(f"{cell_id}: relation parse-failure stop condition reached")
    stage_path = Path(cell["stage_r_per_query_path"])
    final_path = Path(cell["final_per_query_path"])
    final_summary_path = Path(cell["final_summary_path"])
    final_summary = {
        "schema_version": "full-ie-final-cell-v1",
        "status": "COMPLETE",
        "approved_gate": GATE,
        "batch_id": context["manifest"]["batch_id"],
        "cell_id": cell_id,
        "config_id": cell["config_id"],
        "config": cell["config"],
        "dataset": "domain",
        "k": EXPECTED_K,
        "seed": EXPECTED_SEED,
        "rows": EXPECTED_ROWS,
        "source_stage_n_path": cell["original_stage_n_path"],
        "source_stage_n_sha256": cell["original_stage_n_sha256"],
        "compatibility_view_path": cell["compatibility_view_path"],
        "compatibility_view_sha256": cell["compatibility_view_sha256"],
        "stage_r_per_query_path": cell["stage_r_per_query_path"],
        "stage_r_per_query_sha256": audit["per_query_sha256"],
        "stage_r_summary_path": cell["stage_r_summary_path"],
        "stage_r_summary_sha256": audit["stage_r_summary_sha256"],
        "execution_config_path": cell["execution_config_path"],
        "execution_config_sha256": cell["execution_config_sha256"],
        "final_per_query_path": cell["final_per_query_path"],
        "per_query_sha256": audit["per_query_sha256"],
        "entity_micro": audit["entity_micro"],
        "relation": audit["relation"],
        "audit": {key: value for key, value in audit.items() if key not in {"entity_micro", "relation"}},
        "matrix_complete_cell": True,
        "claim_promotion_allowed": False,
    }
    write_exclusive(final_path, stage_path.read_bytes())
    write_exclusive(final_summary_path, json_bytes(final_summary))
    validate_materialized_final(cell)
    return final_summary


def finalize_batch(context: Mapping[str, Any]) -> dict[str, Any]:
    output_path = Path(context["manifest"]["batch_report_path"])
    assert_absent(str(output_path), label="batch report")
    cells: list[dict[str, Any]] = []
    for cell_id in CELL_ORDER:
        cell = context["cells"][cell_id]["cell"]
        summary = validate_materialized_final(cell)
        cells.append(
            {
                "cell_id": cell_id,
                "final_per_query_path": cell["final_per_query_path"],
                "final_per_query_sha256": summary["per_query_sha256"],
                "final_summary_path": cell["final_summary_path"],
                "final_summary_sha256": sha256_file(cell["final_summary_path"]),
                "entity_micro": summary["entity_micro"],
                "relation": summary["relation"],
                "parse_failures_relation": summary["audit"]["parse_failures_relation"],
            }
        )
    report = {
        "schema_version": "full-ie-f7-domain-batch1-report-v1",
        "status": "COMPLETE",
        "approved_gate": GATE,
        "batch_id": context["manifest"]["batch_id"],
        "execution_manifest_sha256": context["manifest_sha256"],
        "cells": cells,
        "complete_cells_before": 0,
        "complete_cells_after": 4,
        "matrix_after": "4/60",
        "aggregated_seed_claims": False,
        "paper_claims_updated": False,
        "negative_results_preserved": True,
    }
    write_exclusive(output_path, json_bytes(report))
    return report


def main() -> int:
    args = parse_args()
    context = load_context(
        Path(args.manifest).resolve(),
        repo_root=Path(args.repo_root).resolve(),
        verify_freeze_files=True,
    )
    if args.command == "preflight-batch":
        result = preflight_batch(context)
    elif args.command == "preflight-cell":
        result = preflight_cell(context, args.cell_id)
    elif args.command == "finalize-cell":
        result = finalize_cell(context, args.cell_id)
    elif args.command == "finalize-batch":
        result = finalize_batch(context)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
