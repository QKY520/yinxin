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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class VerificationDryRunTest(unittest.TestCase):
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
