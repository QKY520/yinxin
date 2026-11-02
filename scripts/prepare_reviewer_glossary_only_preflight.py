#!/usr/bin/env python3
"""Prepare one locked, non-executable glossary-only formal config."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_PREFLIGHT_APPROVED"
SOURCE = ROOT / "configs/reviewer_qwen_neutral_envelope_formal_20260917/zero_shot.yaml"
TARGET = ROOT / "configs/reviewer_qwen_glossary_only_20260918"
QUERY = Path("/root/autodl-tmp/data/domain_test.jsonl")
GLOSSARY = ROOT / "data/domain_dict.jsonl"
OUTPUT_ROOT = Path("/root/autodl-tmp/reviewer_qwen_glossary_only_20260918")
EXPECTED_QUERY_SHA256 = "42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0"
EXPECTED_GLOSSARY_SHA256 = "01b857822894bb09268cbb7fb14ad0988630137bb7efae0b9d90f7d75a2f3ef6"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_config(source: dict) -> dict:
    if source["data"]["query_path"] != str(QUERY):
        raise ValueError("accepted zero-shot query path changed")
    if source["examples"] != {"mode": "none", "k": 0, "seed": 42}:
        raise ValueError("accepted zero-shot example policy changed")
    if "glossary" in source or "rag" in source:
        raise ValueError("accepted zero-shot source unexpectedly contains evidence")
    if source["generation"] != {
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 768,
        "seed": 42,
    }:
        raise ValueError("accepted zero-shot generation policy changed")
    if source["parsing"].get("ner_only_envelope_policy") != "entities_or_entities_relations_v2":
        raise ValueError("accepted neutral envelope changed")

    config = copy.deepcopy(source)
    config["run_id"] = "reviewer-qwen-glossary-only-20260918-prep"
    config["config_name"] = "reviewer_qwen_glossary_only_20260918"
    config["execution"] = {
        "phase": "REVIEWER_QWEN_GLOSSARY_ONLY_PREFLIGHT",
        "authorized": False,
        "human_gate": GATE,
        "model_calls_allowed": False,
        "gpu_required": True,
    }
    config["glossary"] = {
        "path": str(GLOSSARY),
        "max_entries": 20,
        "match_mode": "substring",
    }
    config["protocol"]["system"] = "glossary_only"
    config["protocol"]["run_order"] = ["glossary_only"]
    config["protocol"]["source_formal_system"] = "zero_shot"
    config["protocol"]["only_intended_change"] = "frozen_query_matched_glossary"
    config["cache"] = {"dir": str(OUTPUT_ROOT / "cache")}
    config["outputs"] = {
        "dry_run_prompts": str(OUTPUT_ROOT / "dry_run_prompts.jsonl"),
        "manifest": str(OUTPUT_ROOT / "manifest.json"),
        "per_query": str(OUTPUT_ROOT / "per_query.jsonl"),
        "summary": str(OUTPUT_ROOT / "summary.json"),
    }
    config["dry_run"] = {"max_queries": 170}
    config["query_limit"] = 170
    return config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-gate", required=True)
    args = parser.parse_args()
    if args.human_gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    if TARGET.exists():
        raise FileExistsError(f"refusing to overwrite {TARGET}")
    if sha256(QUERY) != EXPECTED_QUERY_SHA256:
        raise ValueError("frozen query hash mismatch")
    if sha256(GLOSSARY) != EXPECTED_GLOSSARY_SHA256:
        raise ValueError("frozen glossary hash mismatch")

    source = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    config = build_config(source)
    TARGET.mkdir(parents=True, exist_ok=False)
    config_path = TARGET / "glossary_only.yaml"
    config_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    report = {
        "gate": GATE,
        "source_config": str(SOURCE),
        "source_config_sha256": sha256(SOURCE),
        "config": str(config_path),
        "config_sha256": sha256(config_path),
        "query_sha256": sha256(QUERY),
        "glossary_sha256": sha256(GLOSSARY),
        "query_records_expected": 170,
        "model_calls": 0,
        "authorized": False,
        "only_intended_change": "frozen_query_matched_glossary",
    }
    (TARGET / "preflight_build_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
