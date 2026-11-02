#!/usr/bin/env python3
"""Authorize the single locked glossary-only 170-row formal cell."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/reviewer_qwen_glossary_only_20260918/glossary_only.yaml"
RUNTIME = ROOT / "configs/reviewer_qwen_glossary_only_20260918/runtime_formal_authorized"
GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_FORMAL_EXECUTION_APPROVED"
PHASE = "REVIEWER_GLOSSARY_ONLY_FORMAL_EXECUTION"
OUTPUT = "/root/autodl-tmp/reviewer_qwen_glossary_only_formal_20260918"


def authorize(config: dict, gate: str) -> dict:
    if gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    result = copy.deepcopy(config)
    if result["data"]["dataset"] != "domain_test" or result["query_limit"] != 170:
        raise ValueError("formal source must remain the locked 170-row domain_test config")
    result["run_id"] = "reviewer-qwen-glossary-only-formal-20260918"
    result["config_name"] = "reviewer_qwen_glossary_only_formal_20260918"
    result["execution"] = {
        "phase": PHASE,
        "authorized": True,
        "human_gate": GATE,
        "model_calls_allowed": True,
        "gpu_required": True,
    }
    result["cache"] = {"dir": f"{OUTPUT}/cache"}
    result["outputs"] = {
        "dry_run_prompts": f"{OUTPUT}/dry_run_prompts.jsonl",
        "manifest": f"{OUTPUT}/manifest.json",
        "per_query": f"{OUTPUT}/per_query.jsonl",
        "summary": f"{OUTPUT}/summary.json",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-gate", required=True)
    args = parser.parse_args()
    if RUNTIME.exists():
        raise FileExistsError(f"refusing to overwrite {RUNTIME}")
    source = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    config = authorize(source, args.human_gate)
    RUNTIME.mkdir(parents=True, exist_ok=False)
    (RUNTIME / "glossary_only.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
