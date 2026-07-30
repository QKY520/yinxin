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

from equipment_ie.schema import sha256_file, write_jsonl_atomic
from scripts.run_m2_exact_glossary_baseline import (
    GlossarySurface,
    analyze,
    compile_glossary_surfaces,
    exact_glossary_match,
    validate_execution_scope,
)
from scripts.run_p3_extraction import build_query_plan


ENTITY_TYPES = ["EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"]


def unified(record_id: str, text: str, entities: list[dict] | None = None) -> dict:
    return {
        "id": record_id,
        "text": text,
        "entities": entities or [],
        "relations": [],
    }


class ExactGlossaryBaselineTests(unittest.TestCase):
    def test_terms_aliases_and_all_occurrences_are_matched(self) -> None:
        records = [
            {
                "term": "战斗机",
                "type": "EQUIPMENT",
                "priority": 100,
                "aliases": ["战机"],
            }
        ]
        surfaces = compile_glossary_surfaces(
            records,
            allowed_types=ENTITY_TYPES,
            min_surface_chars=2,
            include_terms=True,
            include_aliases=True,
        )
        result = exact_glossary_match(
            "战机与战斗机协同，另一架战机返航。",
            surfaces,
            type_order=ENTITY_TYPES,
        )
        self.assertEqual(
            [entity["span"] for entity in result["entities"]],
            ["战机", "战斗机", "战机"],
        )
        self.assertEqual(result["candidate_matches"], 3)
        self.assertEqual(result["overlap_dropped"], 0)

    def test_longest_first_overlap_policy_is_deterministic(self) -> None:
        surfaces = [
            GlossarySurface("最大射程", "METRIC", 80, 0, "最大射程", "term"),
            GlossarySurface("射程", "METRIC", 80, 1, "射程", "term"),
        ]
        result = exact_glossary_match(
            "最大射程为400千米。", surfaces, type_order=ENTITY_TYPES
        )
        self.assertEqual([entity["span"] for entity in result["entities"]], ["最大射程"])
        self.assertEqual(result["candidate_matches"], 2)
        self.assertEqual(result["overlap_dropped"], 1)

    def test_conflicting_surface_types_fail_loudly(self) -> None:
        records = [
            {"term": "雷达", "type": "EQUIPMENT", "priority": 1},
            {"term": "雷达", "type": "MODULE", "priority": 2},
        ]
        with self.assertRaisesRegex(ValueError, "conflicting types"):
            compile_glossary_surfaces(
                records,
                allowed_types=ENTITY_TYPES,
                min_surface_chars=2,
                include_terms=True,
                include_aliases=True,
            )

    def test_scope_rejects_frozen_test_path(self) -> None:
        config = {
            "execution": {
                "authorized": True,
                "human_gate": "M2_BASELINE_PREP_APPROVED",
                "model_calls_allowed": False,
                "gpu_required": False,
            },
            "data": {
                "dataset": "domain_dev50",
                "query_path": "/tmp/domain_test.jsonl",
                "forbidden_path_fragments": ["domain_test"],
            },
        }
        with patch(
            "scripts.run_m2_exact_glossary_baseline.gpu_visible", return_value=False
        ):
            with self.assertRaisesRegex(RuntimeError, "frozen-test"):
                validate_execution_scope(config)

    def test_integration_writes_reloadable_outputs_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            query_path = root / "domain_dev.jsonl"
            glossary_path = root / "glossary.jsonl"
            config_path = root / "config.yaml"
            output_root = root / "outputs"
            text = "战机搭载雷达。"
            gold = [
                unified(
                    "d1",
                    text,
                    [
                        {"start": 0, "end": 2, "type": "EQUIPMENT", "span": "战机"},
                        {"start": 4, "end": 6, "type": "MODULE", "span": "雷达"},
                    ],
                ),
                unified("d2", "未知文本。"),
            ]
            write_jsonl_atomic(query_path, gold)
            glossary_rows = [
                {
                    "term": "战斗机",
                    "type": "EQUIPMENT",
                    "priority": 100,
                    "aliases": ["战机"],
                },
                {"term": "雷达", "type": "MODULE", "priority": 90},
            ]
            glossary_path.write_text(
                "".join(
                    json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                    for row in glossary_rows
                ),
                encoding="utf-8",
            )
            config_path.write_text("run_id: unit-m2\n", encoding="utf-8")
            config = {
                "run_id": "unit-m2",
                "execution": {
                    "authorized": True,
                    "human_gate": "M2_BASELINE_PREP_APPROVED",
                    "model_calls_allowed": False,
                    "gpu_required": False,
                },
                "data": {
                    "dataset": "domain_dev50",
                    "query_path": str(query_path),
                    "expected_records": 2,
                    "expected_sha256": sha256_file(query_path),
                    "forbidden_path_fragments": ["domain_test"],
                },
                "glossary": {
                    "path": str(glossary_path),
                    "expected_records": 2,
                    "expected_sha256": sha256_file(glossary_path),
                },
                "schema": {"entity_types": {name: name for name in ENTITY_TYPES}},
                "matching": {
                    "case_sensitive": True,
                    "include_terms": True,
                    "include_aliases": True,
                    "min_surface_chars": 2,
                    "occurrence_policy": "all",
                    "overlap_policy": "longest_first_nonoverlap",
                    "type_order": ENTITY_TYPES,
                },
                "outputs": {
                    "predictions": str(output_root / "predictions.jsonl"),
                    "per_query": str(output_root / "per_query.jsonl"),
                    "summary": str(output_root / "summary.json"),
                    "manifest": str(output_root / "manifest.json"),
                },
            }
            with patch(
                "scripts.run_m2_exact_glossary_baseline.gpu_visible",
                return_value=False,
            ):
                summary = analyze(config, config_path)
                with self.assertRaises(FileExistsError):
                    analyze(config, config_path)
            self.assertEqual(summary["metrics"]["entity_micro"]["tp"], 2)
            self.assertEqual(summary["metrics"]["entity_micro"]["fp"], 0)
            self.assertEqual(summary["metrics"]["entity_micro"]["f1"], 1.0)
            self.assertEqual(summary["safeguards"]["model_calls"], 0)
            self.assertEqual(
                len(list(iter_json_lines(output_root / "per_query.jsonl"))), 2
            )

    def test_zero_shot_query_plan_does_not_load_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            query_path = root / "dev.jsonl"
            config_path = root / "zero.yaml"
            write_jsonl_atomic(query_path, [unified("d1", "测试文本。")])
            config_path.write_text("run_id: zero\n", encoding="utf-8")
            config = {
                "data": {"query_path": str(query_path), "support_path": None},
                "examples": {"mode": "none", "k": 0, "seed": 42},
            }
            support, queries, selector, _, _, _, metadata, _, _ = build_query_plan(
                config=config, config_path=config_path, dry_run=False
            )
            self.assertEqual(support, [])
            self.assertEqual(len(queries), 1)
            self.assertEqual(selector(queries[0]), [])
            self.assertEqual(metadata["example_ids"], [])


def iter_json_lines(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            yield json.loads(line)


if __name__ == "__main__":
    unittest.main()
