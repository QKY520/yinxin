#!/usr/bin/env python3
"""Run the bounded F6 CLUENER replay recovery with an immutable guard."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie import full_ie_f6 as f6_runtime  # noqa: E402
from equipment_ie.full_ie_f6 import (  # noqa: E402
    load_json,
    read_cgroup_memory_limit_bytes,
    sha256_file,
    validate_f6_inputs,
    write_json_atomic,
    write_text_atomic,
)


RECOVERY_GATE = "FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED"
RECOVERY_VERSION = "full-ie-f6-cluener-recovery-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guard", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--progress-every", type=int, default=50)
    return parser.parse_args()


def _object(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def validate_guard(
    guard: dict[str, Any],
    *,
    guard_path: Path,
    repo_root: Path,
) -> tuple[dict[str, Any], Path]:
    if guard.get("version") != RECOVERY_VERSION:
        raise ValueError("recovery guard version mismatch")
    if guard.get("date") != "2026-08-03":
        raise ValueError("recovery guard date mismatch")
    if guard.get("human_gate") != RECOVERY_GATE:
        raise ValueError("recovery gate mismatch")

    gpu = _object(guard.get("gpu"), label="gpu")
    if gpu != {
        "boot_purpose": "memory_unlock_only",
        "execution_allowed": False,
        "expected_model": "NVIDIA GeForce RTX 4090",
        "hourly_price_cny": 2.8,
    }:
        raise ValueError("GPU recovery guard is not the approved 4090 memory-only scope")

    retrieval = _object(guard.get("retrieval"), label="retrieval")
    if retrieval != {
        "dataset": "cluener",
        "device": "cpu",
        "expected_rows": 1343,
        "use_fp16": False,
    }:
        raise ValueError("recovery retrieval scope changed")

    forbidden = _object(guard.get("forbidden"), label="forbidden")
    expected_forbidden = {
        "aggregation": True,
        "api_calls": True,
        "domain_test": True,
        "final_metrics": True,
        "github_sync": True,
        "paper_edits": True,
        "qwen": True,
        "stage_n": True,
        "stage_r": True,
        "vllm": True,
    }
    if forbidden != expected_forbidden:
        raise ValueError("recovery forbidden-action guard changed")

    base = _object(guard.get("base_config"), label="base_config")
    relative_base = base.get("path")
    if not isinstance(relative_base, str) or Path(relative_base).is_absolute():
        raise ValueError("base_config.path must be repo-relative")
    expected_base_sha = base.get("sha256")
    base_path = (repo_root / relative_base).resolve()
    if not isinstance(expected_base_sha, str) or sha256_file(base_path) != expected_base_sha:
        raise ValueError("locked F6 base config SHA256 changed")

    base_inputs = load_json(base_path)
    validate_f6_inputs(base_inputs, repo_root=repo_root, verify_files=True)
    base_models = _object(base_inputs.get("models"), label="base_config.models")
    if base_models.get("device") != "cpu" or base_models.get("use_fp16") is not False:
        raise ValueError("base F6 config must remain CPU FP32")
    base_auth = _object(base_inputs.get("authorization"), label="base_config.authorization")
    if any(base_auth.get(key) is not False for key in base_auth):
        raise ValueError("base F6 config contains an enabled authorization")

    source_hashes = _object(guard.get("source_hashes"), label="source_hashes")
    for relative, expected in source_hashes.items():
        path = (repo_root / relative).resolve()
        if not isinstance(expected, str) or sha256_file(path) != expected:
            raise ValueError(f"recovery source SHA256 changed: {relative}")
    if guard_path.resolve() == base_path:
        raise ValueError("recovery guard must not replace the F6 base config")
    return base_inputs, base_path


def _run_base_prepare(
    *,
    base_config: Path,
    repo_root: Path,
    output_dir: Path,
    progress_every: int,
) -> int:
    import equipment_ie.full_ie_f6 as f6_module
    import scripts.prepare_full_ie_f6 as prepare_module

    from scripts.prepare_full_ie_f6 import main as prepare_main

    original_f6_gpu_visible = f6_module.gpu_visible
    original_prepare_gpu_visible = prepare_module.gpu_visible
    # The paid GPU is a memory-capacity unlock only. Mask device presence in
    # the legacy no-card runner while retaining its CPU-FP32 configuration.
    f6_module.gpu_visible = lambda: False
    prepare_module.gpu_visible = lambda: False
    saved_argv = sys.argv
    sys.argv = [
        "prepare_full_ie_f6.py",
        "--config",
        str(base_config),
        "--repo-root",
        str(repo_root),
        "--output-dir",
        str(output_dir),
        "--dataset",
        "cluener",
        "--progress-every",
        str(progress_every),
    ]
    try:
        return int(prepare_main())
    finally:
        sys.argv = saved_argv
        f6_module.gpu_visible = original_f6_gpu_visible
        prepare_module.gpu_visible = original_prepare_gpu_visible


def _recovery_lock(output_dir: Path) -> Path:
    names = [
        "recovery_runtime_preflight.json",
        "cluener_rag_replay.json",
        "cluener_rag_replay_rows.jsonl",
        "cluener_rag_replay_checkpoint.json",
        "cluener_memory_preflight.json",
        "SOURCE_SHA256.txt",
        "RESOURCE_SHA256.txt",
        "f6_prepare_report.json",
        "PREPARE_ARTIFACT_SHA256.txt",
        "f6_recovery_report.json",
    ]
    paths = [output_dir / name for name in names]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"missing recovery artifacts: {missing}")
    lock_path = output_dir / "RECOVERY_ARTIFACT_SHA256.txt"
    write_text_atomic(
        lock_path,
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in paths),
    )
    return lock_path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    guard_path = Path(args.guard).resolve()
    output_dir = Path(args.output_dir).resolve()
    guard = load_json(guard_path)
    base_inputs, base_config = validate_guard(
        guard,
        guard_path=guard_path,
        repo_root=repo_root,
    )
    gpu_device_visible = f6_runtime.gpu_visible()
    cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if gpu_device_visible and cuda_visible_devices not in {"", "-1"}:
        raise RuntimeError("recovery guard requires CUDA_VISIBLE_DEVICES to be empty")
    if args.progress_every <= 0:
        raise ValueError("progress-every must be positive")

    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    write_json_atomic(
        output_dir / "recovery_runtime_preflight.json",
        {
            "base_config_sha256": sha256_file(base_config),
            "cgroup_memory_limit_bytes": read_cgroup_memory_limit_bytes(),
            "cuda_visible_devices": cuda_visible_devices,
            "gpu_device_visible": gpu_device_visible,
            "gpu_execution_allowed": False,
            "gpu_hourly_price_cny": guard["gpu"]["hourly_price_cny"],
            "human_gate": RECOVERY_GATE,
            "started_at": started_at,
            "use_fp16": base_inputs["models"]["use_fp16"],
            "version": RECOVERY_VERSION,
        },
    )

    try:
        result = _run_base_prepare(
            base_config=base_config,
            repo_root=repo_root,
            output_dir=output_dir,
            progress_every=args.progress_every,
        )
        if result != 0:
            raise RuntimeError(f"base F6 preparation exited with status {result}")
        base_report_path = output_dir / "f6_prepare_report.json"
        base_report = load_json(base_report_path)
        validation = _object(base_report.get("validation"), label="f6_prepare_report.validation")
        cluener_validation = _object(validation.get("cluener"), label="cluener validation")
        if cluener_validation.get("rows") != 1343:
            raise ValueError("CLUENER recovery did not validate all 1343 rows")
        report = {
            "base_config_sha256": sha256_file(base_config),
            "base_prepare_report_sha256": sha256_file(base_report_path),
            "dataset": "cluener",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "gpu_execution_allowed": False,
            "gpu_hourly_price_cny": guard["gpu"]["hourly_price_cny"],
            "human_gate": RECOVERY_GATE,
            "llm_calls": 0,
            "model_calls": 0,
            "paid_gpu_cost_cny_estimate": round(
                (time.monotonic() - started) / 3600.0 * guard["gpu"]["hourly_price_cny"],
                6,
            ),
            "recovery_guard_sha256": sha256_file(guard_path),
            "rows": cluener_validation["rows"],
            "stage": "F6_CLUENER_REPLAY_RECOVERY",
            "status": "DONE",
            "version": RECOVERY_VERSION,
        }
        write_json_atomic(output_dir / "f6_recovery_report.json", report)
        _recovery_lock(output_dir)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except BaseException as exc:
        write_json_atomic(
            output_dir / "f6_recovery_failure.json",
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "gpu_execution_allowed": False,
                "gpu_hourly_price_cny": guard["gpu"]["hourly_price_cny"],
                "human_gate": RECOVERY_GATE,
                "stage": "F6_CLUENER_REPLAY_RECOVERY",
                "status": "FAILED",
                "version": RECOVERY_VERSION,
            },
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
