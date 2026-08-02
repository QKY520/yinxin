#!/usr/bin/env python3
"""Build F6 no-card leakage-safe RAG replay artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_f6 import (  # noqa: E402
    F6_GATE,
    F6_VERSION,
    build_cluener_replay_manifest,
    build_domain_consensus_manifest,
    build_source_locks,
    gpu_visible,
    inspect_cpu_model_memory,
    load_json,
    read_cgroup_memory_limit_bytes,
    sha256_file,
    validate_f6_inputs,
    validate_replay_manifest,
    write_json_atomic,
    write_text_atomic,
)
from scripts.run_p3_extraction import build_rag_selector  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--dataset", choices=("domain", "cluener", "all"), default="all")
    parser.add_argument("--progress-every", type=int, default=25)
    return parser.parse_args()


def artifact_lines(paths: list[Path]) -> str:
    return "".join(f"{sha256_file(path)}  {path.name}\n" for path in paths)


def resource_lines(inputs: dict[str, Any]) -> str:
    locks = [dict(value) for _, value in sorted(inputs["resources"].items())]
    locks.extend(sorted(inputs["domain_consensus_sources"], key=lambda item: int(item["seed"])))
    return "".join(f"{lock['sha256']}  {lock['path']}\n" for lock in locks)


def main() -> int:
    args = parse_args()
    if gpu_visible():
        raise RuntimeError("F6 replay preparation requires AutoDL no-card mode")
    repo_root = Path(args.repo_root).resolve()
    config_path = Path(args.config).resolve()
    output_dir = Path(args.output_dir).resolve()
    inputs = load_json(config_path)
    input_report = validate_f6_inputs(inputs, repo_root=repo_root, verify_files=True)
    config_sha256 = sha256_file(config_path)
    source_locks = build_source_locks(repo_root, inputs["source_paths"])
    output_dir.mkdir(parents=True, exist_ok=True)

    domain_path = output_dir / "domain_rag_replay.json"
    cluener_path = output_dir / "cluener_rag_replay.json"
    checkpoint_path = output_dir / "cluener_rag_replay_rows.jsonl"
    checkpoint_metadata_path = output_dir / "cluener_rag_replay_checkpoint.json"
    memory_preflight_path = output_dir / "cluener_memory_preflight.json"
    source_lock_path = output_dir / "SOURCE_SHA256.txt"
    resource_lock_path = output_dir / "RESOURCE_SHA256.txt"
    report_path = output_dir / "f6_prepare_report.json"
    artifact_lock_path = output_dir / "PREPARE_ARTIFACT_SHA256.txt"

    write_text_atomic(
        source_lock_path,
        "".join(f"{lock['sha256']}  {lock['path']}\n" for lock in source_locks),
    )
    write_text_atomic(resource_lock_path, resource_lines(inputs))

    validation: dict[str, Any] = {}
    if args.dataset in {"domain", "all"}:
        domain_manifest = build_domain_consensus_manifest(
            inputs,
            output_path=domain_path,
            config_sha256=config_sha256,
        )
        validation["domain"] = validate_replay_manifest(
            domain_manifest,
            inputs,
            dataset="domain",
            config_sha256=config_sha256,
        )

    if args.dataset in {"cluener", "all"}:
        memory_report = inspect_cpu_model_memory(
            inputs,
            memory_limit_bytes=read_cgroup_memory_limit_bytes(),
        )
        write_json_atomic(memory_preflight_path, memory_report)
        if memory_report["sufficient"] is not True:
            raise RuntimeError(
                "CLUENER CPU replay cannot load the frozen embedding and reranker "
                f"weights: cgroup limit={memory_report['cgroup_memory_limit_bytes']}, "
                f"minimum weight bytes={memory_report['minimum_model_weight_bytes']}"
            )
        cluener_manifest = build_cluener_replay_manifest(
            inputs,
            output_path=cluener_path,
            checkpoint_path=checkpoint_path,
            checkpoint_metadata_path=checkpoint_metadata_path,
            config_sha256=config_sha256,
            selector_builder=build_rag_selector,
            progress_every=args.progress_every,
        )
        validation["cluener"] = validate_replay_manifest(
            cluener_manifest,
            inputs,
            dataset="cluener",
            config_sha256=config_sha256,
        )

    report = {
        "stage": "F6_REPLAY_PREP",
        "version": F6_VERSION,
        "human_gate": F6_GATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_scope": args.dataset,
        "config_path": str(config_path),
        "config_sha256": config_sha256,
        "input_report": input_report,
        "source_locks": len(source_locks),
        "validation": validation,
        "gpu_device_present": False,
        "api_called": False,
        "llm_calls": 0,
        "paid_gpu_cost_cny": 0,
    }
    write_json_atomic(report_path, report)
    artifact_paths = [source_lock_path, resource_lock_path, report_path]
    for path in (
        domain_path,
        cluener_path,
        checkpoint_path,
        checkpoint_metadata_path,
        memory_preflight_path,
    ):
        if path.is_file():
            artifact_paths.append(path)
    write_text_atomic(artifact_lock_path, artifact_lines(artifact_paths))
    report["prepare_artifact_lock_sha256"] = sha256_file(artifact_lock_path)
    report["prepare_report_sha256"] = sha256_file(report_path)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
