from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.schema import iter_jsonl  # noqa: E402
from scripts.run_p3_verification import main as run_main  # noqa: E402
from scripts.run_p3_verification import (  # noqa: E402
    build_entity_verification_prompt,
    drop_entities_by_unit_decisions,
    parse_verifier_answer,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class VerificationDryRunTest(unittest.TestCase):
    def test_parse_verifier_answer_accepts_only_atomic_yes_no(self) -> None:
        self.assertEqual(parse_verifier_answer("yes"), "yes")
        self.assertEqual(parse_verifier_answer("No."), "no")
        self.assertEqual(parse_verifier_answer("是。"), "yes")
        self.assertEqual(parse_verifier_answer("否"), "no")
        self.assertEqual(parse_verifier_answer("yes, because evidence supports it"), "invalid")

    def test_drop_entities_by_unit_decisions_keeps_yes_and_invalid(self) -> None:
        pred_raw = {
            "id": "q1",
            "text": "Carrier uses radar.",
            "entities": [
                {"start": 0, "end": 7, "type": "EQUIPMENT", "span": "Carrier"},
                {"start": 13, "end": 18, "type": "MODULE", "span": "radar"},
                {"start": 0, "end": 18, "type": "TECH_SCHEME", "span": "Carrier uses radar"},
            ],
            "relations": [],
        }
        verified = drop_entities_by_unit_decisions(
            pred_raw,
            decisions=[
                {"entity_index": 0, "decision": "yes", "valid_answer": True},
                {"entity_index": 1, "decision": "no", "valid_answer": True},
                {"entity_index": 2, "decision": "invalid", "valid_answer": False},
            ],
        )
        self.assertEqual([entity["span"] for entity in verified["entities"]], ["Carrier", "Carrier uses radar"])

    def test_execution_requires_model_calls_allowed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "run_id: unit-exec-guard",
                        "config_name: E",
                        "execution:",
                        "  authorized: true",
                        "  model_calls_allowed: false",
                        "  human_gate: P3_VERIFICATION_SANITY_APPROVED",
                    ]
                ),
                encoding="utf-8",
            )
            argv = sys.argv
            sys.argv = ["run_p3_verification.py", "--config", str(config)]
            try:
                with self.assertRaisesRegex(RuntimeError, "model_calls_allowed"):
                    run_main()
            finally:
                sys.argv = argv

    def test_entity_verification_prompt_is_source_first(self) -> None:
        prompt = build_entity_verification_prompt(
            text="P-8A海神海上巡逻机配备声纳系统。",
            entity={"start": 0, "end": 10, "type": "EQUIPMENT", "span": "P-8A海神海上巡逻机"},
            evidence_passages=["参考资料没有该实体。"],
            output_instruction="只回答yes或no",
        )
        self.assertIn("最终判断以原文为准", prompt)
        self.assertIn("不要因为参考资料没有提到它就回答 no", prompt)
        self.assertIn("如果有任何不确定，回答 yes", prompt)
        self.assertIn("EQUIPMENT", prompt)

    def test_verification_dry_run_uses_source_text_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            per_query = root / "per_query.jsonl"
            prompts = root / "prompts.jsonl"
            manifest = root / "manifest.json"
            write_jsonl(
                per_query,
                [
                    {
                        "id": "q1",
                        "pred_raw": {
                            "id": "q1",
                            "text": "Carrier uses radar.",
                            "entities": [
                                {"start": 0, "end": 7, "type": "EQUIPMENT", "span": "Carrier"},
                                {"start": 13, "end": 18, "type": "MODULE", "span": "radar"},
                            ],
                            "relations": [],
                        },
                    }
                ],
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "run_id: unit-eprime-verif-dry",
                        "config_name: E_prime",
                        "input:",
                        f"  per_query_path: {per_query.as_posix()}",
                        "  expected_rows: 1",
                        "evidence:",
                        "  mode: source_text_only",
                        "prompt:",
                        "  output_instruction: 只回答yes或no",
                        "model:",
                        "  name: unit-model",
                        "generation:",
                        "  temperature: 0.0",
                        "  top_p: 1.0",
                        "  max_tokens: 8",
                        "  seed: 42",
                        "outputs:",
                        f"  dry_run_prompts: {prompts.as_posix()}",
                        f"  manifest: {manifest.as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )
            argv = sys.argv
            sys.argv = ["run_p3_verification.py", "--config", str(config), "--dry-run"]
            try:
                self.assertEqual(run_main(), 0)
            finally:
                sys.argv = argv

            saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved_manifest["atomic_units"], 2)
            self.assertFalse(saved_manifest["api_called"])
            saved_prompts = list(iter_jsonl(prompts, validate=False))
            self.assertEqual(saved_prompts[0]["evidence_mode"], "source_text_only")
            self.assertEqual(saved_prompts[0]["evidence_count"], 0)

    def test_verification_dry_run_reuses_extraction_rag_passages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            per_query = root / "per_query.jsonl"
            prompts = root / "prompts.jsonl"
            manifest = root / "manifest.json"
            write_jsonl(
                per_query,
                [
                    {
                        "id": "q1",
                        "rag_passages": ["Carrier evidence.", "Radar evidence."],
                        "pred_raw": {
                            "id": "q1",
                            "text": "Carrier uses radar.",
                            "entities": [
                                {"start": 0, "end": 7, "type": "EQUIPMENT", "span": "Carrier"},
                            ],
                            "relations": [],
                        },
                    }
                ],
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "run_id: unit-e-verif-dry",
                        "config_name: E",
                        "input:",
                        f"  per_query_path: {per_query.as_posix()}",
                        "  expected_rows: 1",
                        "evidence:",
                        "  mode: use_extraction_rag_passages",
                        "  max_passages: 2",
                        "prompt:",
                        "  output_instruction: 只回答yes或no",
                        "model:",
                        "  name: unit-model",
                        "generation:",
                        "  temperature: 0.0",
                        "  top_p: 1.0",
                        "  max_tokens: 8",
                        "  seed: 42",
                        "outputs:",
                        f"  dry_run_prompts: {prompts.as_posix()}",
                        f"  manifest: {manifest.as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )
            argv = sys.argv
            sys.argv = ["run_p3_verification.py", "--config", str(config), "--dry-run"]
            try:
                self.assertEqual(run_main(), 0)
            finally:
                sys.argv = argv

            saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved_manifest["atomic_units"], 1)
            saved_prompts = list(iter_jsonl(prompts, validate=False))
            self.assertEqual(saved_prompts[0]["evidence_mode"], "use_extraction_rag_passages")
            self.assertEqual(saved_prompts[0]["evidence_count"], 2)


if __name__ == "__main__":
    unittest.main()
