"""Materialize an isolated span-index reviewer baseline diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


VARIANTS = ("zero_shot", "glossary_only", "bm25_only", "rag_only")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--query-path", required=True)
    args = parser.parse_args()
    source_dir, output_dir = Path(args.source_dir), Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        config = yaml.safe_load((source_dir / f"domain_{variant}_seed42.yaml").read_text(encoding="utf-8"))
        config["run_id"] = f"domain_{variant}_span_index_diagnostic_seed42"
        config["config_name"] = f"reviewer_domain_{variant}_span_index_diagnostic_seed42"
        config["execution"] = {
            "phase": "REVIEWER_BASELINE_B1_SPAN_INDEX_DIAGNOSTIC",
            "authorized": True,
            "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_SPAN_INDEX_DIAGNOSTIC_APPROVED",
            "model_calls_allowed": True,
            "gpu_required": True,
        }
        config["data"]["query_path"] = args.query_path
        config["data"]["pilot_scope"] = "20 fresh non-test domain_dev rows; no frozen-test read"
        config["generation"]["response_format"] = {"type": "json_object"}
        config["prompt"]["output_instruction"] = "只返回JSON；entities仅使用start、end、type；不要输出span或occurrence；不要任何解释或markdown"
        config["prompt"]["retry_suffix"] = "只返回合法JSON；每个实体只含start、end、type"
        config["parsing"]["output_mode"] = "span_index"
        config["cache"] = {"dir": f"/root/autodl-tmp/reviewer_baselines_20260828_span_index/cache/{variant}"}
        for key, value in config["outputs"].items():
            config["outputs"][key] = value.replace(
                "/root/autodl-tmp/reviewer_baselines_20260828_parse_stability20",
                "/root/autodl-tmp/reviewer_baselines_20260828_span_index",
            )
        (output_dir / f"domain_{variant}_seed42.yaml").write_text(
            yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
