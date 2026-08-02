#!/usr/bin/env python3
"""Prepare the F5 no-card protocol-freeze artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_freeze import (  # noqa: E402
    FREEZE_STATUS,
    FREEZE_VERSION,
    build_freeze_manifest,
    build_source_locks,
    canonical_sha256,
    sha256_file,
    validate_freeze_inputs,
    validate_freeze_manifest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    return parser.parse_args()


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, value: Any) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    write_text_atomic(path, content)


def write_csv_atomic(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    fields = [
        "cell_id",
        "dataset",
        "config",
        "k",
        "seed",
        "status",
        "config_id",
        "source_config",
        "stage_n_node",
        "stage_r_node",
        "verification_node",
        "required_future_gate",
        "config_contract_sha256",
    ]
    try:
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field) for field in fields})
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def lock_lines(values: Iterable[Mapping[str, Any]], *, path_key: str = "path") -> str:
    return "".join(f"{value['sha256']}  {value[path_key]}\n" for value in values)


def cell_inventory(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in manifest["run_manifest"]["cells"]:
        execution = cell["execution"]
        rows.append(
            {
                "cell_id": cell["cell_id"],
                "dataset": cell["dataset"],
                "config": cell["config"],
                "k": cell["k"],
                "seed": cell["seed"],
                "status": cell["status"],
                "config_id": execution["config_id"],
                "source_config": execution["source_config"],
                "stage_n_node": execution["stage_n_node"],
                "stage_r_node": execution["stage_r_node"],
                "verification_node": execution["verification_node"],
                "required_future_gate": execution["required_future_gate"],
                "config_contract_sha256": cell["config_contract_sha256"],
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    if gpu_visible():
        raise RuntimeError("F5 protocol freeze requires no-card mode")
    inputs_path = Path(args.inputs).resolve()
    output_dir = Path(args.output_dir).resolve()
    repo_root = Path(args.repo_root).resolve()
    inputs = load_json(inputs_path)
    input_report = validate_freeze_inputs(inputs, verify_files=True)
    source_locks = build_source_locks(repo_root, inputs["source_paths"])
    manifest = build_freeze_manifest(inputs, source_locks=source_locks)
    validation = validate_freeze_manifest(
        manifest,
        repo_root=repo_root,
        verify_files=True,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "freeze_manifest.json"
    inventory_path = output_dir / "cell_inventory.csv"
    source_path = output_dir / "SOURCE_SHA256.txt"
    resource_path = output_dir / "RESOURCE_SHA256.txt"
    reuse_path = output_dir / "REUSED_STAGE_N_SHA256.txt"
    report_path = output_dir / "freeze_report.json"
    artifact_path = output_dir / "FREEZE_ARTIFACT_SHA256.txt"

    write_json_atomic(manifest_path, manifest)
    write_csv_atomic(inventory_path, cell_inventory(manifest))
    write_text_atomic(source_path, lock_lines(manifest["source_locks"]))
    write_text_atomic(
        resource_path,
        lock_lines(
            [
                {"path": value["path"], "sha256": value["sha256"]}
                for _, value in sorted(manifest["resources"].items())
            ]
        ),
    )
    write_text_atomic(
        reuse_path,
        lock_lines(manifest["reused_stage_n"]),
    )
    report = {
        **validation,
        "freeze_version": FREEZE_VERSION,
        "status": FREEZE_STATUS,
        "input_report": input_report,
        "freeze_manifest_sha256": sha256_file(manifest_path),
        "freeze_manifest_canonical_sha256": canonical_sha256(manifest),
        "cell_inventory_sha256": sha256_file(inventory_path),
        "source_lock_file_sha256": sha256_file(source_path),
        "resource_lock_file_sha256": sha256_file(resource_path),
        "reuse_lock_file_sha256": sha256_file(reuse_path),
        "model_calls": 0,
        "paid_gpu_cost_cny": 0,
    }
    write_json_atomic(report_path, report)
    artifacts = [
        manifest_path,
        inventory_path,
        source_path,
        resource_path,
        reuse_path,
        report_path,
        inputs_path,
    ]
    write_text_atomic(
        artifact_path,
        "".join(
            f"{sha256_file(path)}  {path.name}\n"
            for path in artifacts
        ),
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
