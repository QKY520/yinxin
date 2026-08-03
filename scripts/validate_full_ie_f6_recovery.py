#!/usr/bin/env python3
"""Independently validate a completed F6 CLUENER recovery package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_f6 import (  # noqa: E402
    load_json,
    sha256_file,
    validate_replay_manifest,
    write_json_atomic,
)
from scripts.run_full_ie_f6_cluener_recovery import (  # noqa: E402
    RECOVERY_GATE,
    RECOVERY_VERSION,
    validate_guard,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guard", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--artifact-dir", required=True)
    return parser.parse_args()


def _object(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _verify_lock(artifact_dir: Path) -> int:
    lock_path = artifact_dir / "RECOVERY_ARTIFACT_SHA256.txt"
    entries = []
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        path = artifact_dir / relative
        if sha256_file(path) != digest:
            raise ValueError(f"recovery artifact SHA256 mismatch: {relative}")
        entries.append(relative)
    if len(entries) != 10:
        raise ValueError(f"expected 10 recovery artifact lock entries, got {len(entries)}")
    return len(entries)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    guard_path = Path(args.guard).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    guard = load_json(guard_path)
    base_inputs, base_config = validate_guard(
        guard,
        guard_path=guard_path,
        repo_root=repo_root,
    )
    config_sha256 = sha256_file(base_config)
    manifest = load_json(artifact_dir / "cluener_rag_replay.json")
    replay = validate_replay_manifest(
        manifest,
        base_inputs,
        dataset="cluener",
        config_sha256=config_sha256,
    )
    preflight = load_json(artifact_dir / "cluener_memory_preflight.json")
    if preflight.get("sufficient") is not True:
        raise ValueError("CLUENER memory preflight is not sufficient")
    if preflight.get("device") != "cpu" or preflight.get("use_fp16") is not False:
        raise ValueError("CLUENER recovery is not CPU FP32")
    runtime = load_json(artifact_dir / "recovery_runtime_preflight.json")
    if runtime.get("gpu_execution_allowed") is not False:
        raise ValueError("recovery runtime preflight enables GPU execution")
    if runtime.get("gpu_device_visible") is True and runtime.get("cuda_visible_devices") not in {
        "",
        "-1",
    }:
        raise ValueError("visible GPU was not masked by CUDA_VISIBLE_DEVICES")
    report = load_json(artifact_dir / "f6_recovery_report.json")
    if report.get("version") != RECOVERY_VERSION:
        raise ValueError("recovery report version mismatch")
    if report.get("human_gate") != RECOVERY_GATE or report.get("status") != "DONE":
        raise ValueError("recovery report is not a successful approved run")
    if report.get("rows") != 1343 or report.get("llm_calls") != 0:
        raise ValueError("recovery report row/call contract mismatch")
    if report.get("gpu_execution_allowed") is not False:
        raise ValueError("recovery report enables GPU execution")
    if report.get("recovery_guard_sha256") != sha256_file(guard_path):
        raise ValueError("recovery guard SHA256 mismatch")
    locked_entries = _verify_lock(artifact_dir)
    output = {
        "artifact_lock_entries": locked_entries,
        "config_sha256": config_sha256,
        "dataset": "cluener",
        "gpu_execution_allowed": False,
        "human_gate": RECOVERY_GATE,
        "llm_calls": 0,
        "replay": replay,
        "status": "VALID",
        "version": RECOVERY_VERSION,
    }
    write_json_atomic(artifact_dir / "f6_recovery_validation_report.json", output)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
