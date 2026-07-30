from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie import DEFAULT_RELATION_TYPES  # noqa: E402
from equipment_ie.llm_labeling import ChatResult  # noqa: E402
from scripts import run_full_ie_verification, run_stage_r  # noqa: E402


def entity(text: str, span: str, entity_type: str) -> dict:
    start = text.index(span)
    return {
        "start": start,
        "end": start + len(span),
        "type": entity_type,
        "span": span,
    }


def record(record_id: str, *, with_relation: bool) -> dict:
    text = "甲平台采用乙模块。"
    return {
        "id": record_id,
        "text": text,
        "entities": [
            entity(text, "甲平台", "EQUIPMENT"),
            entity(text, "乙模块", "MODULE"),
        ],
        "relations": (
            [{"head": 0, "tail": 1, "type": "USES"}]
            if with_relation
            else []
        ),
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class FullIERunnerTest(unittest.TestCase):
    def test_f1_implementation_gate_cannot_authorize_stage_r_model_calls(self) -> None:
        config = {
            "execution": {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "FULL_IE_IMPLEMENTATION",
                "human_gate": "FULL_IE_IMPLEMENTATION_APPROVED",
            }
        }
        with self.assertRaisesRegex(RuntimeError, "human_gate"):
            run_stage_r.run_execute(config, Path("unused-config.yaml"))

    def test_future_stage_r_gate_requires_matching_phase(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "requires execution.phase"):
            run_stage_r.validate_execution_gate(
                {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "WRONG_PHASE",
                    "human_gate": "FULL_IE_DOMAIN_DEV_SANITY_APPROVED",
                }
            )
        run_stage_r.validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "FULL_IE_DOMAIN_DEV_SANITY",
                "human_gate": "FULL_IE_DOMAIN_DEV_SANITY_APPROVED",
            }
        )

    def test_f1_implementation_gate_cannot_authorize_verifier_model_calls(self) -> None:
        config = {
            "execution": {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "FULL_IE_IMPLEMENTATION",
                "human_gate": "FULL_IE_IMPLEMENTATION_APPROVED",
            }
        }
        with self.assertRaisesRegex(RuntimeError, "human_gate"):
            run_full_ie_verification.run_execute(
                config,
                Path("unused-config.yaml"),
            )

    def test_e_and_eprime_evidence_modes_are_locked(self) -> None:
        row = {"id": "q1", "rag_passages": ["r1", "r2", "r3"]}
        self.assertEqual(
            run_full_ie_verification.select_evidence(
                row,
                config_name="E",
                evidence_config={
                    "mode": "reuse_stage_r_rag_passages",
                    "max_passages": 3,
                },
            ),
            ["r1", "r2", "r3"],
        )
        self.assertEqual(
            run_full_ie_verification.select_evidence(
                row,
                config_name="E-prime",
                evidence_config={"mode": "source_text_only"},
            ),
            [],
        )
        with self.assertRaisesRegex(ValueError, "E-prime requires"):
            run_full_ie_verification.select_evidence(
                row,
                config_name="E-prime",
                evidence_config={"mode": "reuse_stage_r_rag_passages"},
            )
        with self.assertRaisesRegex(ValueError, "max_passages=3"):
            run_full_ie_verification.select_evidence(
                row,
                config_name="E",
                evidence_config={
                    "mode": "reuse_stage_r_rag_passages",
                    "max_passages": 2,
                },
            )

    def test_stage_r_resource_contract_preserves_clean_ablations(self) -> None:
        clean = {"glossary_entries": [], "rag_passages": []}
        run_stage_r.validate_source_resource_contract("A", clean)
        with self.assertRaisesRegex(ValueError, "may not inject glossary"):
            run_stage_r.validate_source_resource_contract(
                "B",
                {"glossary_entries": ["term"], "rag_passages": []},
            )
        with self.assertRaisesRegex(ValueError, "may not inject RAG"):
            run_stage_r.validate_source_resource_contract(
                "C",
                {"glossary_entries": ["term"], "rag_passages": ["evidence"]},
            )

    def test_stage_r_runner_uses_only_synthetic_recorded_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage_n_path = root / "stage_n.jsonl"
            support_path = root / "support.jsonl"
            output_path = root / "stage_r.jsonl"
            summary_path = root / "stage_r_summary.json"
            config_path = root / "stage_r_config.yaml"
            source = record("q1", with_relation=False)
            gold = record("q1", with_relation=True)
            support = record("s1", with_relation=True)
            write_jsonl(support_path, [support])
            write_jsonl(
                stage_n_path,
                [
                    {
                        "id": "q1",
                        "dataset": "domain",
                        "config": "A",
                        "k": 1,
                        "seed": 42,
                        "gold": gold,
                        "pred_raw": source,
                        "example_ids": ["s1"],
                        "glossary_terms": [],
                        "rag_passage_ids": [],
                        "rag_passages": [],
                        "parse_failure": False,
                        "latency_ms": 1.0,
                        "prompt_hash": "ner-prompt-hash",
                        "raw_llm_output_hash": "ner-output-hash",
                        "sanitization_flags": [],
                    }
                ],
            )
            config_path.write_text("synthetic: true\n", encoding="utf-8")
            config = {
                "run_id": "synthetic-stage-r",
                "config_name": "A",
                "execution": {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "FULL_IE_DOMAIN_DEV_SANITY",
                    "human_gate": "FULL_IE_DOMAIN_DEV_SANITY_APPROVED",
                },
                "data": {"dataset": "domain"},
                "replay": {"reuse_stage_n_metadata": True},
                "input": {
                    "stage_n_per_query_path": str(stage_n_path),
                    "support_path": str(support_path),
                    "expected_rows": 1,
                },
                "schema": {"relation_types": DEFAULT_RELATION_TYPES},
                "prompt": {},
                "parsing": {"drop_invalid_relations": False},
                "generation": {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_tokens": 64,
                    "seed": 42,
                },
                "cache": {"dir": str(root / "cache")},
                "model": {
                    "name": "synthetic-model",
                    "base_url": "http://invalid.local",
                    "timeout_seconds": 1,
                },
                "outputs": {
                    "per_query": str(output_path),
                    "summary": str(summary_path),
                },
            }
            response = ChatResult(
                content='{"relations":[{"head":0,"tail":1,"type":"USES"}]}',
                request_hash="request-hash",
                raw_output_hash="output-hash",
                cache_hit=False,
                latency_ms=2.0,
            )
            with (
                patch.object(run_stage_r, "gpu_visible", return_value=True),
                patch.object(run_stage_r, "chat_with_cache", return_value=response),
                patch("builtins.print"),
            ):
                self.assertEqual(run_stage_r.run_execute(config, config_path), 0)
            output_row = json.loads(output_path.read_text(encoding="utf-8").strip())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(output_row["pred_raw"]["entities"], source["entities"])
            self.assertEqual(output_row["pred_relations_stage_r"], gold["relations"])
            self.assertEqual(summary["model_requests"], 1)
            self.assertEqual(summary["relation"]["exact_relation_micro"]["f1"], 1.0)

    def test_relation_aware_verifier_runner_keeps_invalid_and_cascades(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "full_ie_source.jsonl"
            output_path = root / "verified.jsonl"
            summary_path = root / "verified_summary.json"
            config_path = root / "verify_config.yaml"
            pred_raw = record("q1", with_relation=True)
            write_jsonl(
                input_path,
                [
                    {
                        "id": "q1",
                        "dataset": "domain",
                        "config": "C",
                        "k": 5,
                        "seed": 42,
                        "gold": pred_raw,
                        "pred_raw": pred_raw,
                        "rag_passages": [],
                    }
                ],
            )
            config_path.write_text("synthetic: true\n", encoding="utf-8")
            config = {
                "run_id": "synthetic-eprime",
                "config_name": "E-prime",
                "source_config": "C",
                "execution": {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "FULL_IE_DOMAIN_DEV_SANITY",
                    "human_gate": "FULL_IE_DOMAIN_DEV_SANITY_APPROVED",
                },
                "data": {"dataset": "domain"},
                "input": {"per_query_path": str(input_path), "expected_rows": 1},
                "schema": {
                    "entity_types": {
                        "EQUIPMENT": "synthetic equipment",
                        "MODULE": "synthetic module",
                    },
                    "relation_types": DEFAULT_RELATION_TYPES,
                },
                "evidence": {"mode": "source_text_only"},
                "prompt": {},
                "generation": {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_tokens": 8,
                    "seed": 42,
                },
                "cache": {"dir": str(root / "cache")},
                "model": {
                    "name": "synthetic-model",
                    "base_url": "http://invalid.local",
                    "timeout_seconds": 1,
                },
                "outputs": {
                    "per_query": str(output_path),
                    "summary": str(summary_path),
                },
            }
            responses = [
                ChatResult("yes", "r1", "o1", False, 1.0),
                ChatResult("no", "r2", "o2", False, 1.0),
                ChatResult("maybe", "r3", "o3", False, 1.0),
            ]
            with (
                patch.object(
                    run_full_ie_verification,
                    "gpu_visible",
                    return_value=True,
                ),
                patch.object(
                    run_full_ie_verification,
                    "chat_with_cache",
                    side_effect=responses,
                ),
                patch("builtins.print"),
            ):
                self.assertEqual(
                    run_full_ie_verification.run_execute(config, config_path),
                    0,
                )
            output_row = json.loads(output_path.read_text(encoding="utf-8").strip())
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(output_row["config"], "E-prime")
            self.assertEqual(len(output_row["pred_verified"]["entities"]), 1)
            self.assertEqual(output_row["pred_verified"]["relations"], [])
            self.assertEqual(summary["invalid_units_kept"], 1)
            self.assertEqual(summary["valid_no_entities"], 1)
            self.assertEqual(summary["cascade_dropped_relations"], 1)


if __name__ == "__main__":
    unittest.main()
