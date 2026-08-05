#!/usr/bin/env python3
"""Run the locked public-NER cells sequentially with stop-condition checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


GATE = "NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED"
PHASE = "NER_PUBLIC_CLUENER_FINAL"
VARIANTS = "ABCD"
SEEDS = (42, 43, 44)
CELL_ORDER = tuple(
    f"cluener:{variant}:k5:s{seed}" for seed in SEEDS for variant in VARIANTS
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-manifest", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--start-cell", required=True, choices=CELL_ORDER)
    parser.add_argument("--hard-stop-at", required=True)
    parser.add_argument("--events", required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def append_event(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def utc_now() -> str:
    return datetime.now().astimezone().isoformat()


def count_nonempty_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_completed(entry: Mapping[str, Any]) -> dict[str, Any]:
    cell_id = str(entry["cell_id"])
    per_query_path = Path(str(entry["per_query_path"]))
    summary_path = Path(str(entry["summary_path"]))
    if not per_query_path.is_file() or not summary_path.is_file():
        raise FileNotFoundError(f"{cell_id}: completed output pair is missing")
    if count_nonempty_lines(per_query_path) != 1343:
        raise ValueError(f"{cell_id}: per-query file does not contain 1343 rows")
    summary = load_json(summary_path)
    if summary.get("query_records") != 1343:
        raise ValueError(f"{cell_id}: summary does not report 1343 rows")
    if summary.get("per_query_sha256") != sha256_file(per_query_path):
        raise ValueError(f"{cell_id}: per-query hash mismatch")
    parse_rate = float(summary.get("parse_failure_rate", 1.0))
    if parse_rate >= 0.05:
        raise RuntimeError(f"{cell_id}: parse-failure stop threshold reached: {parse_rate}")
    return {
        "cell_id": cell_id,
        "parse_failures": int(summary.get("parse_failures", -1)),
        "parse_failure_rate": parse_rate,
        "elapsed_seconds": float(summary.get("elapsed_seconds", 0.0)),
        "f1": float(summary.get("entity_micro", {}).get("f1", 0.0)),
        "per_query_sha256": summary["per_query_sha256"],
        "summary_sha256": sha256_file(summary_path),
    }


def check_health() -> None:
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"vLLM health status is {response.status}")


def validate_manifest(manifest: Mapping[str, Any], runner: Path) -> list[dict[str, Any]]:
    if (
        manifest.get("approved_gate") != GATE
        or manifest.get("phase") != PHASE
        or manifest.get("status") != "AUTHORIZED_PREINFERENCE"
    ):
        raise ValueError("execution manifest authorization changed")
    cells = manifest.get("cells")
    if not isinstance(cells, list) or [cell.get("cell_id") for cell in cells] != list(CELL_ORDER):
        raise ValueError("execution manifest does not contain the exact ordered 12 cells")
    if manifest.get("locks", {}).get("execution_runner_sha256") != sha256_file(runner):
        raise ValueError("execution runner hash changed")
    for entry in cells:
        config_path = Path(str(entry["execution_config_path"]))
        if sha256_file(config_path) != entry.get("execution_config_sha256"):
            raise ValueError(f"{entry.get('cell_id')}: execution config hash changed")
        config = load_yaml(config_path)
        if (
            config.get("execution", {}).get("human_gate") != GATE
            or config.get("execution", {}).get("phase") != PHASE
            or config.get("execution", {}).get("authorized") is not True
            or config.get("execution", {}).get("model_calls_allowed") is not True
        ):
            raise ValueError(f"{entry.get('cell_id')}: execution authorization changed")
    return [dict(cell) for cell in cells]


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.execution_manifest).resolve()
    runner_path = Path(args.runner).resolve()
    events_path = Path(args.events).resolve()
    hard_stop = datetime.fromisoformat(args.hard_stop_at)
    if hard_stop.tzinfo is None:
        raise ValueError("hard-stop timestamp must include a timezone")
    cells = validate_manifest(load_json(manifest_path), runner_path)
    start_index = CELL_ORDER.index(args.start_cell)

    for entry in cells[:start_index]:
        validate_completed(entry)
    append_event(
        events_path,
        {
            "event": "SEQUENCE_STARTED",
            "at": utc_now(),
            "start_cell": args.start_cell,
            "hard_stop_at": hard_stop.isoformat(),
        },
    )

    for entry in cells[start_index:]:
        cell_id = str(entry["cell_id"])
        variant = str(entry["config"])
        seed = int(entry["seed"])
        now = datetime.now().astimezone()
        remaining_seconds = (hard_stop - now).total_seconds()
        if remaining_seconds <= 0:
            append_event(events_path, {"event": "HARD_STOP", "at": utc_now(), "cell_id": cell_id})
            return 2
        if variant in "CD":
            dependency = cells[CELL_ORDER.index(f"cluener:B:k5:s{seed}")]
            validate_completed(dependency)
        per_query_path = Path(str(entry["per_query_path"]))
        summary_path = Path(str(entry["summary_path"]))
        log_path = Path(str(entry["log_path"]))
        if per_query_path.exists() or summary_path.exists() or log_path.exists():
            raise FileExistsError(f"{cell_id}: refusing output or log collision")
        check_health()
        append_event(
            events_path,
            {
                "event": "CELL_STARTED",
                "at": utc_now(),
                "cell_id": cell_id,
                "remaining_seconds": round(remaining_seconds, 3),
            },
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, str(runner_path), "--config", str(entry["execution_config_path"])]
        try:
            with log_path.open("xb") as log_handle:
                completed = subprocess.run(
                    command,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    check=False,
                    timeout=max(1.0, remaining_seconds),
                )
        except subprocess.TimeoutExpired:
            append_event(events_path, {"event": "HARD_STOP_DURING_CELL", "at": utc_now(), "cell_id": cell_id})
            return 2
        if completed.returncode != 0:
            append_event(
                events_path,
                {
                    "event": "CELL_FAILED",
                    "at": utc_now(),
                    "cell_id": cell_id,
                    "returncode": completed.returncode,
                },
            )
            return completed.returncode or 1
        report = validate_completed(entry)
        append_event(events_path, {"event": "CELL_COMPLETED", "at": utc_now(), **report})

    append_event(events_path, {"event": "SEQUENCE_COMPLETED", "at": utc_now(), "cells": len(cells)})
    print(json.dumps({"status": "DONE", "cells": len(cells)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
