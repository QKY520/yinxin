from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import entity_micro_counts  # noqa: E402
from equipment_ie.full_ie import (  # noqa: E402
    DEFAULT_RELATION_TYPES,
    relation_evaluation_report,
    stage_r_skip_reason,
)
from equipment_ie.full_ie_freeze import sha256_file  # noqa: E402
from scripts.finalize_full_ie_f7 import (  # noqa: E402
    finalize_cell,
    validate_stage_artifacts,
    write_exclusive,
)
from scripts.prepare_full_ie_f7 import compatibility_view_rows  # noqa: E402


def entity(span: str) -> dict:
    return {"start": 0, "end": len(span), "type": "EQUIPMENT", "span": span}


def record(record_id: str, text: str) -> dict:
    return {
        "id": record_id,
        "text": text,
        "entities": [entity(text)],
        "relations": [],
    }


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


class FullIEF7Test(unittest.TestCase):
    def source_rows(self, count: int = 170) -> list[dict]:
        rows: list[dict] = []
        for index in range(count):
            record_id = f"q{index:03d}"
            gold = record(record_id, f"item{index:03d}")
            rows.append(
                {
                    "id": record_id,
                    "dataset": "domain_test",
                    "config": "A_fixed_random_domain_test_p5_draft",
                    "k": 5,
                    "seed": 42,
                    "gold": gold,
                    "pred_raw": dict(gold),
                    "pred_verified": None,
                    "example_ids": [f"s{item}" for item in range(5)],
                    "glossary_terms": [],
                    "rag_passage_ids": [],
                    "rag_passages": [],
                    "parse_failure": False,
                    "latency_ms": 1.0,
                    "prompt_hash": "ner-prompt",
                    "raw_llm_output_hash": "ner-output",
                    "sanitization_flags": [],
                }
            )
        return rows

    def test_compatibility_view_changes_only_dataset_and_config(self) -> None:
        source = self.source_rows(2)
        view = compatibility_view_rows(source, config="A", expected_rows=2)
        self.assertEqual([row["dataset"] for row in view], ["domain", "domain"])
        self.assertEqual([row["config"] for row in view], ["A", "A"])
        for raw, adapted in zip(source, view):
            expected = dict(raw)
            expected["dataset"] = "domain"
            expected["config"] = "A"
            self.assertEqual(adapted, expected)
        self.assertEqual(source[0]["dataset"], "domain_test")

    def test_compatibility_view_rejects_prediction_changes(self) -> None:
        source = self.source_rows(1)
        source[0]["pred_raw"]["relations"] = [
            {"head": 0, "tail": 0, "type": "USES"}
        ]
        with self.assertRaisesRegex(ValueError, "invalid Stage N prediction"):
            compatibility_view_rows(source, config="A", expected_rows=1)

    def test_validate_and_materialize_deterministic_skip_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            support_path = root / "support.jsonl"
            support = [record(f"s{index}", f"support{index}") for index in range(5)]
            write_jsonl(support_path, support)
            source_rows = self.source_rows()
            view_rows = compatibility_view_rows(source_rows, config="A")
            view_path = root / "view.jsonl"
            write_jsonl(view_path, view_rows)
            config_path = root / "config.yaml"
            config_path.write_text("locked: true\n", encoding="utf-8")
            stage_path = root / "stage.jsonl"
            stage_summary_path = root / "stage_summary.json"
            final_path = root / "final.jsonl"
            final_summary_path = root / "final_summary.json"
            cache_dir = root / "cache"
            skip_reason = stage_r_skip_reason(
                view_rows[0]["pred_raw"], DEFAULT_RELATION_TYPES
            )
            self.assertIsNotNone(skip_reason)
            stage_rows: list[dict] = []
            for source in view_rows:
                prediction = dict(source["pred_raw"])
                stage_rows.append(
                    {
                        "id": source["id"],
                        "dataset": "domain",
                        "config": "A",
                        "k": 5,
                        "seed": 42,
                        "gold": source["gold"],
                        "pred_entities_stage_n": prediction["entities"],
                        "pred_relations_stage_r": [],
                        "pred_raw": prediction,
                        "pred_verified": None,
                        "ner_prompt_hash": source["prompt_hash"],
                        "relation_prompt_hash": None,
                        "verifier_prompt_hashes": [],
                        "raw_ner_output_hash": source["raw_llm_output_hash"],
                        "raw_relation_output_hash": None,
                        "example_ids": source["example_ids"],
                        "glossary_terms": [],
                        "rag_passage_ids": [],
                        "rag_passages": [],
                        "parse_failure_ner": False,
                        "parse_failure_relation": False,
                        "relation_skip_reason": skip_reason,
                        "sanitization_flags": [],
                        "verifier_decisions": [],
                        "latency_ner_ms": 1.0,
                        "latency_relation_ms": 0.0,
                        "latency_verifier_ms": 0.0,
                        "relation_attempts": [],
                    }
                )
            write_jsonl(stage_path, stage_rows)
            gold = [row["gold"] for row in stage_rows]
            predictions = [row["pred_raw"] for row in stage_rows]
            config_hash = sha256_file(config_path)
            write_json(
                stage_summary_path,
                {
                    "config_sha256": config_hash,
                    "source_stage_n_sha256": sha256_file(view_path),
                    "per_query_sha256": sha256_file(stage_path),
                    "rows": 170,
                    "model_requests": 0,
                    "deterministic_skips": 170,
                    "parse_failures_relation": 0,
                    "entity_micro": entity_micro_counts(gold, predictions).report(),
                    "relation": relation_evaluation_report(
                        gold,
                        predictions,
                        relation_types=tuple(DEFAULT_RELATION_TYPES),
                    ),
                },
            )
            cell = {
                "cell_id": "domain:A:k5:s42",
                "config": "A",
                "config_id": "full-ie-final-v1-domain-a-k5-seed42",
                "config_contract_sha256": "contract",
                "execution_config_path": str(config_path),
                "execution_config_sha256": config_hash,
                "original_stage_n_path": str(root / "original.jsonl"),
                "original_stage_n_sha256": "original-hash",
                "compatibility_view_path": str(view_path),
                "compatibility_view_sha256": sha256_file(view_path),
                "stage_r_per_query_path": str(stage_path),
                "stage_r_summary_path": str(stage_summary_path),
                "final_per_query_path": str(final_path),
                "final_summary_path": str(final_summary_path),
                "cache_dir": str(cache_dir),
            }
            config = {
                "run_id": "synthetic-f7-a",
                "input": {"support_path": str(support_path)},
                "schema": {"relation_types": DEFAULT_RELATION_TYPES},
                "prompt": {
                    "output_instruction": "unused-for-skip",
                    "retry_suffix": "unused-for-skip",
                },
                "generation": {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_tokens": 768,
                    "seed": 42,
                },
                "model": {"name": "synthetic"},
            }
            prepared = {
                "cell": cell,
                "config": config,
                "config_path": config_path,
                "view_rows": view_rows,
            }
            audit = validate_stage_artifacts(prepared)
            self.assertEqual(audit["rows"], 170)
            self.assertEqual(audit["deterministic_skips"], 170)
            self.assertEqual(audit["model_requests"], 0)
            context = {
                "manifest": {"batch_id": "synthetic-batch"},
                "cells": {"domain:A:k5:s42": prepared},
            }
            result = finalize_cell(context, "domain:A:k5:s42")
            self.assertEqual(result["status"], "COMPLETE")
            self.assertEqual(final_path.read_bytes(), stage_path.read_bytes())
            with self.assertRaises(FileExistsError):
                finalize_cell(context, "domain:A:k5:s42")

    def test_exclusive_writer_refuses_existing_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "locked.txt"
            write_exclusive(path, b"first")
            with self.assertRaises(FileExistsError):
                write_exclusive(path, b"second")
            self.assertEqual(path.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
