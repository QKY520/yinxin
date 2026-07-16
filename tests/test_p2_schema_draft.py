from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_ROOT))

from equipment_ie.schema import iter_jsonl  # noqa: E402


class P2SchemaDraftTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        config_path = PROJECT_ROOT / "configs" / "p2_schema_draft.yaml"
        cls.schema = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        example_path = PROJECT_ROOT / "docs" / "p2_schema_examples_draft.jsonl"
        cls.examples = list(iter_jsonl(example_path))

    def test_schema_records_pause_a_approval(self) -> None:
        self.assertEqual(self.schema["status"], "approved")
        self.assertEqual(self.schema["approval_gate"], "P2_PAUSE_A")
        self.assertEqual(self.schema["approval"]["approved_by"], "human_project_owner")
        self.assertEqual(self.schema["approval"]["approved_at"], "2026-07-16")
        self.assertEqual(
            self.schema["approval"]["decision_record"], "docs/P2_DECISION_LOG.md"
        )

    def test_expected_types_are_fixed(self) -> None:
        self.assertEqual(
            set(self.schema["entity_types"]),
            {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"},
        )
        self.assertEqual(
            set(self.schema["relation_types"]),
            {"USES", "HAS_METRIC", "PART_OF"},
        )

    def test_ten_examples_have_valid_types_and_directions(self) -> None:
        self.assertEqual(len(self.examples), 10)
        self.assertEqual(
            [row["id"] for row in self.examples],
            [f"synthetic-{index:02d}" for index in range(1, 11)],
        )
        entity_types = set(self.schema["entity_types"])
        relation_types = self.schema["relation_types"]
        for record in self.examples:
            for entity in record["entities"]:
                self.assertIn(entity["type"], entity_types)
            for relation in record["relations"]:
                rule = relation_types[relation["type"]]
                head_type = record["entities"][relation["head"]]["type"]
                tail_type = record["entities"][relation["tail"]]["type"]
                self.assertIn(head_type, rule["head_types"])
                self.assertIn(tail_type, rule["tail_types"])

    def test_backup_manifest_stays_at_candidate_stage(self) -> None:
        manifest_path = PROJECT_ROOT / "docs" / "p2_candidate_backup_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["stage"], "candidate_collection_before_pause_a")
        self.assertFalse(manifest["gpu_device_present"])
        self.assertFalse(manifest["paid_gpu_used"])
        self.assertFalse(manifest["collection"]["formal_annotation_started"])
        self.assertEqual(manifest["collection"]["candidate_records"], 400)
        self.assertEqual(manifest["archive"]["entries"], 373)
        self.assertEqual(
            manifest["archive"]["sha256"],
            "6879810924e417f58b6c2ef32932a526c39c7da74f4dedbf849c0d202afa26ce",
        )


if __name__ == "__main__":
    unittest.main()
