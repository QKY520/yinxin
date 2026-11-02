#!/usr/bin/env python3
"""Create execution copies only after the exact paid pilot gate is supplied."""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "configs/reviewer_qwen_occurrence_sanitized_20260917"
RUNTIME_DIR = SOURCE_DIR / "runtime_authorized"
GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_OCCURRENCE_SANITIZED_DEV_PILOT_APPROVED"
PHASE = "REVIEWER_BASELINE_QWEN_OCCURRENCE_SANITIZED_DEV_PILOT"
FILES = (
    "zero_shot_sentinel5.yaml",
    "zero_shot_pilot20.yaml",
    "bm25_only_pilot20.yaml",
    "rag_only_pilot20.yaml",
    "ec_fsie_full_pilot20.yaml",
)


def authorize(config: dict, supplied_gate: str) -> dict:
    if supplied_gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    cfg = copy.deepcopy(config)
    cfg["execution"] = {
        "phase": PHASE,
        "authorized": True,
        "human_gate": GATE,
        "model_calls_allowed": True,
        "gpu_required": True,
    }
    cfg["run_id"] = str(cfg["run_id"]).removesuffix("-prep")
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-gate", required=True)
    args = parser.parse_args()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=False)
    for name in FILES:
        source = SOURCE_DIR / name
        config = yaml.safe_load(source.read_text(encoding="utf-8"))
        runtime = authorize(config, args.human_gate)
        (RUNTIME_DIR / name).write_text(
            yaml.safe_dump(runtime, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
