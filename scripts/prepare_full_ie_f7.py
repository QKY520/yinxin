#!/usr/bin/env python3
"""Prepare the authorized F7 domain batch without making model calls."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_freeze import (  # noqa: E402
    canonical_sha256,
    sha256_file,
    validate_freeze_manifest,
)
from equipment_ie.schema import validate_record  # noqa: E402


GATE = "FULL_IE_DOMAIN_FINAL_BATCH_APPROVED"
PHASE = "FULL_IE_DOMAIN_FINAL_BATCH"
BATCH_CONTRACT_SHA256 = (
    "0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973"
)
FREEZE_MANIFEST_SHA256 = (
    "592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e"
)
FREEZE_CANONICAL_SHA256 = (
    "e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae"
)
CELL_INVENTORY_SHA256 = (
    "dec872aa139289e3cc0bcfe32d75f93dfb45e1f7431af8bda6f791e52aa5cc09"
)
CELL_ORDER = (
    "domain:A:k5:s42",
    "domain:B:k5:s42",
    "domain:C:k5:s42",
    "domain:D:k5:s42",
)
LEGACY_CONFIGS = {
    "A": "A_fixed_random_domain_test_p5_draft",
    "B": "B_knn_domain_test_p5_draft",
    "C": "C_knn_glossary_domain_test_p5_draft",
    "D": "D_knn_glossary_rag_domain_test_p5_draft",
}
TEMPLATE_PATHS = {
    config: f"configs/full_ie_f4a_domain_dev_r1_20260731/domain_{config.lower()}_stage_r.yaml"
    for config in "ABCD"
}
SCOPED_SOURCE_PATHS = (
    "scripts/prepare_full_ie_f7.py",
    "scripts/finalize_full_ie_f7.py",
    "tests/test_full_ie_f7.py",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-contract", required=True)
    parser.add_argument("--freeze-manifest", required=True)
    parser.add_argument("--cell-inventory", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--output-config-dir", required=True)
    parser.add_argument("--view-output-dir", required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--approved-gate", required=True)
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


def jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    return b"".join(
        (
            json.dumps(dict(row), ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        for row in rows
    )


def sha256_bytes(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        raise


def validate_batch_contract(contract: Mapping[str, Any]) -> None:
    scope = contract.get("scope")
    if not isinstance(scope, Mapping):
        raise ValueError("batch contract scope must be an object")
    if list(scope.get("execution_order", [])) != list(CELL_ORDER):
        raise ValueError("batch contract cell order changed")
    expected_scope = {
        "dataset": "domain",
        "split": "domain_test",
        "rows_per_cell": 170,
        "reported_cells": 4,
        "stage_work": "stage_r_only",
        "reuse_stage_n": True,
        "rerun_stage_n": False,
        "run_verification": False,
    }
    for key, expected in expected_scope.items():
        if scope.get(key) != expected:
            raise ValueError(f"batch contract scope.{key} changed")
    if contract.get("required_gate") != GATE:
        raise ValueError("batch contract gate changed")


def compatibility_view_rows(
    rows: Sequence[Mapping[str, Any]], *, config: str, expected_rows: int = 170
) -> list[dict[str, Any]]:
    if config not in LEGACY_CONFIGS:
        raise ValueError(f"unsupported F7 source config {config!r}")
    if len(rows) != expected_rows:
        raise ValueError(f"{config}: expected {expected_rows} source rows, found {len(rows)}")
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in rows:
        row = dict(raw)
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise ValueError(f"{config}: source IDs must be unique non-empty strings")
        seen.add(record_id)
        if (
            row.get("dataset") != "domain_test"
            or row.get("config") != LEGACY_CONFIGS[config]
            or row.get("k") != 5
            or row.get("seed") != 42
        ):
            raise ValueError(f"{config}/{record_id}: legacy Stage N metadata changed")
        gold = row.get("gold")
        prediction = row.get("pred_raw")
        if not isinstance(gold, Mapping) or not isinstance(prediction, Mapping):
            raise ValueError(f"{config}/{record_id}: gold/pred_raw must be objects")
        validate_record(gold)
        validate_record(prediction)
        if gold["id"] != record_id or prediction["id"] != record_id:
            raise ValueError(f"{config}/{record_id}: record ID mismatch")
        if gold["text"] != prediction["text"] or prediction["relations"]:
            raise ValueError(f"{config}/{record_id}: invalid Stage N prediction")
        if row.get("pred_verified") is not None or row.get("parse_failure") is not False:
            raise ValueError(f"{config}/{record_id}: Stage N status changed")
        expected = copy.deepcopy(row)
        expected["dataset"] = "domain"
        expected["config"] = config
        output.append(expected)
    return output


def validate_template_against_node(
    template: Mapping[str, Any], node: Mapping[str, Any], *, config: str
) -> None:
    if template.get("config_name") != config:
        raise ValueError(f"{config}: template config_name mismatch")
    if template.get("protocol_revision") != node["parsing"]["protocol_revision"]:
        raise ValueError(f"{config}: parser revision mismatch")
    if template.get("replay", {}).get("reuse_stage_n_metadata") is not True:
        raise ValueError(f"{config}: template replay contract changed")
    if template.get("prompt", {}).get("version") != node["prompt_version"]:
        raise ValueError(f"{config}: prompt version mismatch")
    if template.get("parsing", {}).get("drop_invalid_relations") is not True:
        raise ValueError(f"{config}: relation sanitizer changed")
    if template.get("generation") != node["generation"]:
        raise ValueError(f"{config}: generation settings changed")


def build_execution_config(
    *,
    template: Mapping[str, Any],
    config: str,
    cell: Mapping[str, Any],
    stage_r_node: Mapping[str, Any],
    view_path: Path,
    view_sha256: str,
    support_lock: Mapping[str, Any],
) -> dict[str, Any]:
    value = copy.deepcopy(dict(template))
    value["run_id"] = f"full-ie-f7-domain-{config.lower()}-k5-seed42"
    value["prepared_under_gate"] = GATE
    value["execution"] = {
        "phase": PHASE,
        "authorized": True,
        "human_gate": GATE,
        "approval_record": "Human-approved in conversation on 2026-08-03 under the exact F7 batch gate.",
        "model_calls_allowed": True,
        "gpu_required": True,
        "explicit_exclusions": [
            "stage_n_rerun",
            "E_or_E-prime",
            "K1_or_K10",
            "seed43_or_seed44",
            "cluener",
            "F8_or_F9",
            "aggregation",
            "paper_edits",
            "github_sync",
        ],
    }
    value["input"] = {
        "stage_n_per_query_path": str(view_path),
        "support_path": str(support_lock["path"]),
        "expected_rows": 170,
    }
    value["cache"] = {"dir": stage_r_node["cache_dir"]}
    value["outputs"] = {
        "per_query": stage_r_node["per_query_path"],
        "summary": stage_r_node["summary_path"],
    }
    value["resource_lock"] = {
        "support": dict(support_lock),
        "original_stage_n": {
            "path": cell["stage_n_path"],
            "sha256": cell["stage_n_sha256"],
            "rows": 170,
        },
        "compatibility_view": {
            "path": str(view_path),
            "sha256": view_sha256,
            "rows": 170,
            "transform": "dataset_domain_test_to_domain_and_legacy_config_to_canonical_only",
        },
        "freeze_manifest": {
            "sha256": FREEZE_MANIFEST_SHA256,
            "canonical_sha256": FREEZE_CANONICAL_SHA256,
        },
    }
    value["f7_contract"] = {
        "batch_id": "full-ie-f7-domain-final-b01-k5-seed42-abcd",
        "cell_id": cell["cell_id"],
        "config_id": cell["config_id"],
        "config_contract_sha256": cell["config_contract_sha256"],
        "stage_work": "stage_r_only",
        "rerun_stage_n": False,
        "run_verification": False,
    }
    return value


def main() -> int:
    args = parse_args()
    if args.approved_gate != GATE:
        raise RuntimeError(f"--approved-gate must equal {GATE}")
    repo_root = Path(args.repo_root).resolve()
    batch_path = Path(args.batch_contract).resolve()
    freeze_path = Path(args.freeze_manifest).resolve()
    inventory_path = Path(args.cell_inventory).resolve()
    output_dir = Path(args.output_config_dir).resolve()
    view_dir = Path(args.view_output_dir).resolve()
    if output_dir.exists() or view_dir.exists():
        raise FileExistsError("F7 config and view output directories must both be absent")
    if sha256_file(batch_path) != BATCH_CONTRACT_SHA256:
        raise ValueError("F7 batch contract SHA256 mismatch")
    if sha256_file(freeze_path) != FREEZE_MANIFEST_SHA256:
        raise ValueError("F5 freeze manifest SHA256 mismatch")
    if sha256_file(inventory_path) != CELL_INVENTORY_SHA256:
        raise ValueError("F5 cell inventory SHA256 mismatch")

    contract = load_json(batch_path)
    freeze = load_json(freeze_path)
    validate_batch_contract(contract)
    validate_freeze_manifest(freeze, repo_root=repo_root, verify_files=True)
    if canonical_sha256(freeze) != FREEZE_CANONICAL_SHA256:
        raise ValueError("F5 canonical manifest SHA256 mismatch")

    source_locks = {item["path"]: item["sha256"] for item in freeze["source_locks"]}
    for path_text in SCOPED_SOURCE_PATHS:
        path = repo_root / path_text
        if not path.is_file():
            raise FileNotFoundError(path)

    frozen_cells = {
        cell["cell_id"]: cell for cell in freeze["run_manifest"]["cells"]
    }
    stage_r_nodes = {
        node["node_id"]: node for node in freeze["execution_nodes"]["stage_r"]
    }
    proposal_cells = {cell["cell_id"]: cell for cell in contract["cells"]}
    support_lock = freeze["resources"]["domain_support"]
    prepared_cells: list[dict[str, Any]] = []
    pending_writes: list[tuple[Path, bytes]] = []

    import yaml

    for cell_id in CELL_ORDER:
        proposal = proposal_cells[cell_id]
        frozen = frozen_cells[cell_id]
        config = str(frozen["config"])
        if proposal["config_contract_sha256"] != frozen["config_contract_sha256"]:
            raise ValueError(f"{cell_id}: frozen config contract mismatch")
        if proposal["stage_n_sha256"] != frozen["stage_n"]["artifact_sha256"]:
            raise ValueError(f"{cell_id}: frozen Stage N artifact mismatch")
        node = stage_r_nodes[frozen["execution"]["stage_r_node"]]
        template_rel = TEMPLATE_PATHS[config]
        template_path = repo_root / template_rel
        if source_locks.get(template_rel) != sha256_file(template_path):
            raise ValueError(f"{cell_id}: F4a Stage R template lock mismatch")
        template = yaml.safe_load(template_path.read_text(encoding="utf-8"))
        if not isinstance(template, dict):
            raise ValueError(f"{template_path}: expected YAML object")
        validate_template_against_node(template, node, config=config)

        original_path = Path(proposal["stage_n_path"])
        if sha256_file(original_path) != proposal["stage_n_sha256"]:
            raise ValueError(f"{cell_id}: source Stage N SHA256 mismatch")
        view_path = view_dir / f"domain_{config.lower()}_k5_seed42_stage_n_view.jsonl"
        view_rows = compatibility_view_rows(load_jsonl(original_path), config=config)
        view_payload = jsonl_bytes(view_rows)
        view_sha256 = sha256_bytes(view_payload)
        pending_writes.append((view_path, view_payload))

        config_value = build_execution_config(
            template=template,
            config=config,
            cell=proposal,
            stage_r_node=node,
            view_path=view_path,
            view_sha256=view_sha256,
            support_lock=support_lock,
        )
        config_payload = yaml.safe_dump(
            config_value,
            allow_unicode=True,
            sort_keys=False,
        ).encode("utf-8")
        config_path = output_dir / f"domain_{config.lower()}_stage_r.yaml"
        pending_writes.append((config_path, config_payload))
        prepared_cells.append(
            {
                "cell_id": cell_id,
                "config": config,
                "config_id": proposal["config_id"],
                "config_contract_sha256": proposal["config_contract_sha256"],
                "execution_config_path": config_path.relative_to(repo_root).as_posix(),
                "execution_config_sha256": sha256_bytes(config_payload),
                "template_path": template_rel,
                "template_sha256": source_locks[template_rel],
                "original_stage_n_path": str(original_path),
                "original_stage_n_sha256": proposal["stage_n_sha256"],
                "compatibility_view_path": str(view_path),
                "compatibility_view_sha256": view_sha256,
                "rows": 170,
                "cache_dir": node["cache_dir"],
                "stage_r_per_query_path": node["per_query_path"],
                "stage_r_summary_path": node["summary_path"],
                "final_per_query_path": frozen["execution"]["final_per_query_path"],
                "final_summary_path": frozen["execution"]["final_summary_path"],
            }
        )

    source_lock_values = [
        {"path": path, "sha256": sha256_file(repo_root / path)}
        for path in SCOPED_SOURCE_PATHS
    ]
    manifest = {
        "schema_version": "full-ie-f7-domain-batch1-execution-v1",
        "batch_id": "full-ie-f7-domain-final-b01-k5-seed42-abcd",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "status": "AUTHORIZED_PREINFERENCE",
        "approved_gate": GATE,
        "base_commit": args.base_commit,
        "authorization": {
            "authorized": True,
            "final_evaluation_allowed": True,
            "gpu_required_for_model_calls": True,
            "model_calls_allowed": True,
            "stage_n_rerun_allowed": False,
            "verification_allowed": False,
        },
        "scope": {
            "dataset": "domain",
            "split": "domain_test",
            "k": 5,
            "seed": 42,
            "rows_per_cell": 170,
            "cell_order": list(CELL_ORDER),
            "stage_work": "stage_r_only",
        },
        "batch_contract": {
            "path": batch_path.relative_to(repo_root).as_posix(),
            "sha256": BATCH_CONTRACT_SHA256,
        },
        "freeze": {
            "manifest_path": freeze_path.relative_to(repo_root).as_posix(),
            "manifest_sha256": FREEZE_MANIFEST_SHA256,
            "canonical_sha256": FREEZE_CANONICAL_SHA256,
            "cell_inventory_path": inventory_path.relative_to(repo_root).as_posix(),
            "cell_inventory_sha256": CELL_INVENTORY_SHA256,
            "support_path": support_lock["path"],
            "support_sha256": support_lock["sha256"],
        },
        "source_locks": source_lock_values,
        "cells": prepared_cells,
        "batch_report_path": "/root/project/results/full_ie/final_v1/batches/f7_domain_batch1_seed42_abcd.json",
        "stop_conditions": list(contract["stop_conditions"]),
        "forbidden": list(contract["forbidden"]),
        "matrix_before": "0/60",
        "matrix_after_if_all_cells_validate": "4/60",
    }
    manifest_payload = json_bytes(manifest)
    manifest_path = output_dir / "execution_manifest.json"
    pending_writes.append((manifest_path, manifest_payload))
    report = {
        "status": "AUTHORIZED_PREINFERENCE_PREPARED",
        "approved_gate": GATE,
        "cells": len(prepared_cells),
        "rows_per_cell": 170,
        "model_calls": 0,
        "gpu_used": False,
        "execution_manifest_path": manifest_path.relative_to(repo_root).as_posix(),
        "execution_manifest_sha256": sha256_bytes(manifest_payload),
        "compatibility_transform_fields": ["dataset", "config"],
        "original_stage_n_predictions_changed": False,
        "matrix_complete_cells": 0,
    }
    pending_writes.append((output_dir / "preparation_report.json", json_bytes(report)))

    for path, _payload in pending_writes:
        if path.exists():
            raise FileExistsError(path)
    output_dir.mkdir(parents=True, exist_ok=False)
    view_dir.mkdir(parents=True, exist_ok=False)
    for path, payload in pending_writes:
        write_exclusive(path, payload)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
