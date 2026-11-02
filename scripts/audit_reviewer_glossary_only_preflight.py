#!/usr/bin/env python3
"""Audit the glossary-only dry run without making model calls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import yaml
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_p3_extraction import build_query_plan
from equipment_ie.extraction import build_ner_prompt


GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_PREFLIGHT_APPROVED"
SOURCE = ROOT / "configs/reviewer_qwen_neutral_envelope_formal_20260917/zero_shot.yaml"
TARGET = ROOT / "configs/reviewer_qwen_glossary_only_20260918/glossary_only.yaml"
DRY_MANIFEST = Path("/root/autodl-tmp/reviewer_qwen_glossary_only_20260918/manifest.json")
REPORT = ROOT / "configs/reviewer_qwen_glossary_only_20260918/preflight_audit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def comparable(config: dict) -> dict:
    result = copy.deepcopy(config)
    for key in ("run_id", "config_name", "execution", "cache", "outputs", "dry_run", "query_limit"):
        result.pop(key, None)
    protocol = result.get("protocol", {})
    for key in ("system", "run_order", "source_formal_system", "only_intended_change"):
        protocol.pop(key, None)
    result.pop("glossary", None)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human-gate", required=True)
    args = parser.parse_args()
    if args.human_gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    if REPORT.exists():
        raise FileExistsError(f"refusing to overwrite {REPORT}")

    source = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    target = yaml.safe_load(TARGET.read_text(encoding="utf-8"))
    if comparable(source) != comparable(target):
        raise ValueError("glossary-only config differs from zero-shot beyond allowed identity/glossary fields")
    if target.get("rag") is not None or target["examples"] != {"mode": "none", "k": 0, "seed": 42}:
        raise ValueError("glossary-only contains forbidden demonstrations or RAG")

    manifest = json.loads(DRY_MANIFEST.read_text(encoding="utf-8"))
    if manifest["model_calls"] != 0 or manifest["api_called"] is not False:
        raise ValueError("dry run unexpectedly called the model API")
    if manifest["query_records"] != 170 or manifest["rag_selection"] != {"enabled": False}:
        raise ValueError("dry-run query count or RAG policy mismatch")

    (_, records, select_examples, select_glossary, select_rag, _, _, _, _) = build_query_plan(
        config=target,
        config_path=TARGET,
        dry_run=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(target["model"]["name"], local_files_only=True)
    token_counts, glossary_counts = [], []
    for record in records:
        examples = select_examples(record)
        glossary = select_glossary(record)
        rag = select_rag(record)
        if examples or rag:
            raise ValueError(f"{record['id']}: forbidden evidence present")
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=target["schema"]["entity_types"],
            examples=examples,
            glossary_entries=glossary,
            rag_passages=[],
            include_relations=False,
            output_instruction=target["prompt"]["output_instruction"],
            output_mode=target["parsing"]["output_mode"],
            reference_instruction=target["prompt"].get("reference_instruction"),
        )
        rendered = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True,
            add_generation_prompt=True,
        )
        token_counts.append(len(rendered))
        glossary_counts.append(len(glossary))
    max_input = max(token_counts)
    max_total = max_input + int(target["generation"]["max_tokens"])
    if max_total > 8192:
        raise ValueError(f"context budget exceeded: {max_total} > 8192")

    report = {
        "gate": GATE,
        "source_config_sha256": sha256(SOURCE),
        "target_config_sha256": sha256(TARGET),
        "dry_manifest_sha256": sha256(DRY_MANIFEST),
        "query_records": len(records),
        "model_calls": 0,
        "only_allowed_config_change": True,
        "examples_present": False,
        "rag_present": False,
        "glossary_enabled": True,
        "glossary_entries_min": min(glossary_counts),
        "glossary_entries_max": max(glossary_counts),
        "queries_with_glossary": sum(value > 0 for value in glossary_counts),
        "max_input_tokens": max_input,
        "max_input_plus_generation_tokens": max_total,
        "context_limit": 8192,
        "passed": True,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
