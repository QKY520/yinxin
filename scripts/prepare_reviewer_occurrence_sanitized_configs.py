#!/usr/bin/env python3
"""Materialize locked non-executable occurrence-sanitized reviewer configs."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/reviewer_qwen_occurrence_sanitized_20260917/zero_shot_sentinel5.yaml"
OUT = ROOT / "configs/reviewer_qwen_occurrence_sanitized_20260917"
PREP_GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_RAW_RESPONSE_AND_P5_PROTOCOL_AUDIT_APPROVED"
REMOTE_ROOT = Path("/root/autodl-tmp/reviewer_qwen_occurrence_sanitized_20260917/pilot20")
BM25_REPLAY = "/root/autodl-tmp/reviewer_baselines_main_unified_bio_20260907/replay_manifests/domain/bm25_top3/replay_manifest.json"
DENSE_REPLAY = "/root/autodl-tmp/reviewer_baselines_main_unified_bio_20260909_repair_preflight/dense_repair/replay_manifest.json"
EXAMPLE_REPLAY = "/root/project/results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_per_query.jsonl"


def build(system: str, base: dict) -> dict:
    cfg = copy.deepcopy(base)
    cfg["run_id"] = f"reviewer-qwen-occurrence-sanitized-{system}-pilot20-prep"
    cfg["config_name"] = f"reviewer_qwen_occurrence_sanitized_{system}_pilot20"
    cfg["query_limit"] = 20
    cfg["dry_run"]["max_queries"] = 20
    cfg["protocol"].update({"system": system, "run_order": ["zero_shot", "bm25_only", "rag_only", "ec_fsie_full"]})
    cfg["execution"] = {
        "phase": "REVIEWER_QWEN_OCCURRENCE_SANITIZED_PREP",
        "authorized": False,
        "human_gate": PREP_GATE,
        "model_calls_allowed": False,
        "gpu_required": True,
    }
    cfg["data"]["support_path"] = None
    cfg["examples"] = {"mode": "none", "k": 0, "seed": 42}
    cfg.pop("rag", None)
    cfg.pop("glossary", None)
    if system == "bm25_only":
        cfg["rag"] = {"enabled": True, "mode": "replay_manifest", "replay_manifest_path": BM25_REPLAY}
    elif system == "rag_only":
        cfg["rag"] = {"enabled": True, "mode": "replay_manifest", "replay_manifest_path": DENSE_REPLAY}
    elif system == "ec_fsie_full":
        cfg["data"]["support_path"] = "/root/autodl-tmp/data/domain_support.jsonl"
        cfg["examples"] = {"mode": "knn_replay", "k": 5, "seed": 42, "source_per_query_path": EXAMPLE_REPLAY}
        cfg["glossary"] = {"path": "/root/project/data/domain_dict.jsonl", "max_entries": 20, "match_mode": "substring"}
        cfg["rag"] = {"enabled": True, "mode": "replay_manifest", "replay_manifest_path": DENSE_REPLAY}
    out = REMOTE_ROOT / system
    cfg["cache"]["dir"] = str(out / "cache")
    cfg["outputs"] = {
        "dry_run_prompts": str(out / "dry_run_prompts.jsonl"),
        "manifest": str(out / "manifest.json"),
        "per_query": str(out / "per_query.jsonl"),
        "summary": str(out / "summary.json"),
    }
    return cfg


def main() -> int:
    base = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
    for system in ("zero_shot", "bm25_only", "rag_only", "ec_fsie_full"):
        path = OUT / f"{system}_pilot20.yaml"
        path.write_text(yaml.safe_dump(build(system, base), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
