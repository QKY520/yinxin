#!/usr/bin/env python3
"""Independently validate F6 replay artifacts and write the final lock."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_f6 import (  # noqa: E402
    F6_GATE,
    F6_VERSION,
    gpu_visible,
    load_json,
    sha256_file,
    validate_f6_inputs,
    validate_replay_manifest,
    write_json_atomic,
    write_text_atomic,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--artifact-dir", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if gpu_visible():
        raise RuntimeError("F6 replay validation requires AutoDL no-card mode")
    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    inputs = load_json(config_path)
    input_report = validate_f6_inputs(inputs, repo_root=repo_root, verify_files=True)
    config_sha256 = sha256_file(config_path)
    domain_path = artifact_dir / "domain_rag_replay.json"
    cluener_path = artifact_dir / "cluener_rag_replay.json"
    domain_report = validate_replay_manifest(
        load_json(domain_path),
        inputs,
        dataset="domain",
        config_sha256=config_sha256,
    )
    cluener_report = validate_replay_manifest(
        load_json(cluener_path),
        inputs,
        dataset="cluener",
        config_sha256=config_sha256,
    )
    report_path = artifact_dir / "f6_validation_report.json"
    report = {
        "stage": "F6_REPLAY_VALIDATION",
        "version": F6_VERSION,
        "human_gate": F6_GATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_sha256,
        "input_report": input_report,
        "domain": domain_report,
        "cluener": cluener_report,
        "gpu_device_present": False,
        "api_called": False,
        "llm_calls": 0,
        "paid_gpu_cost_cny": 0,
    }
    write_json_atomic(report_path, report)

    artifact_names = [
        "domain_rag_replay.json",
        "cluener_rag_replay.json",
        "cluener_rag_replay_rows.jsonl",
        "cluener_rag_replay_checkpoint.json",
        "cluener_memory_preflight.json",
        "SOURCE_SHA256.txt",
        "RESOURCE_SHA256.txt",
        "f6_prepare_report.json",
        "PREPARE_ARTIFACT_SHA256.txt",
        "f6_validation_report.json",
    ]
    paths = [artifact_dir / name for name in artifact_names]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise ValueError(f"missing F6 artifacts: {missing}")
    lock_path = artifact_dir / "F6_ARTIFACT_SHA256.txt"
    write_text_atomic(
        lock_path,
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in paths),
    )
    report["validation_report_sha256"] = sha256_file(report_path)
    report["artifact_lock_sha256"] = sha256_file(lock_path)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
