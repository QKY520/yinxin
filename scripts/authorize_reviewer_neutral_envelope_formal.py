#!/usr/bin/env python3
"""Create formal runtime copies only after the exact paid execution gate."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/reviewer_qwen_neutral_envelope_formal_20260917"
RUNTIME = SOURCE / "runtime_authorized"
GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_EXECUTION_APPROVED"
PHASE = "REVIEWER_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_EXECUTION"
SYSTEMS = ("zero_shot", "bm25_only", "rag_only", "ec_fsie_full")


def authorize(config: dict, gate: str) -> dict:
    if gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    result = copy.deepcopy(config)
    result["execution"] = {
        "phase": PHASE,
        "authorized": True,
        "human_gate": GATE,
        "model_calls_allowed": True,
        "gpu_required": True,
    }
    result["run_id"] = str(result["run_id"]).removesuffix("-prep")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-gate", required=True)
    args = parser.parse_args()
    RUNTIME.mkdir(parents=True, exist_ok=False)
    for system in SYSTEMS:
        config = yaml.safe_load((SOURCE / f"{system}.yaml").read_text(encoding="utf-8"))
        (RUNTIME / f"{system}.yaml").write_text(
            yaml.safe_dump(authorize(config, args.human_gate), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
