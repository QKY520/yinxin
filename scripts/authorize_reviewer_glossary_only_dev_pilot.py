#!/usr/bin/env python3
"""Create one authorized 20-row glossary-only dev pilot config."""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/reviewer_qwen_glossary_only_20260918/glossary_only.yaml"
RUNTIME = ROOT / "configs/reviewer_qwen_glossary_only_20260918/runtime_dev_authorized"
GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_DEV_PILOT_APPROVED"
PHASE = "REVIEWER_GLOSSARY_ONLY_DEV_PILOT"
DEV = "/root/autodl-tmp/data/domain_dev.jsonl"
OUTPUT = "/root/autodl-tmp/reviewer_qwen_glossary_only_dev_pilot_20260918"


def authorize(config: dict, gate: str) -> dict:
    if gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    result = copy.deepcopy(config)
    result["run_id"] = "reviewer-qwen-glossary-only-dev-pilot-20260918"
    result["config_name"] = "reviewer_qwen_glossary_only_dev_pilot_20260918"
    result["execution"] = {
        "phase": PHASE,
        "authorized": True,
        "human_gate": GATE,
        "model_calls_allowed": True,
        "gpu_required": True,
    }
    result["data"]["dataset"] = "domain_dev"
    result["data"]["query_path"] = DEV
    result["data"].pop("expected_records", None)
    result["data"].pop("expected_sha256", None)
    result["query_limit"] = 20
    result["dry_run"] = {"max_queries": 20}
    result["protocol"]["parser_failure_ceiling"] = 0.20
    result["protocol"]["semantic_f1_must_be_positive"] = True
    result["protocol"]["accepted_entities_must_be_positive"] = True
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
