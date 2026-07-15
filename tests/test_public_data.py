from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.public_data import (  # noqa: E402
    ConversionAudit,
    choose_support_ids,
    cmnee_row_to_record,
    convert_cluener,
    duie_row_to_record,
    fewnerd_row_to_record,
    iter_selected_records,
)
from equipment_ie.schema import validate_record, write_jsonl_atomic  # noqa: E402


class PublicDataConverterTest(unittest.TestCase):
    def test_cluener_inclusive_end_becomes_exclusive(self) -> None:
        source_row = {
            "text": "北京银行",
            "label": {"company": {"北京银行": [[0, 3]]}},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.json"
            path.write_text(
                json.dumps(source_row, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            audit = ConversionAudit()
            records = list(
                convert_cluener(path, "train", labeled=True, audit=audit)
            )
        self.assertEqual(records[0]["entities"][0]["end"], 4)
        self.assertEqual(records[0]["entities"][0]["span"], "北京银行")
        validate_record(records[0])

    def test_fewnerd_joins_contiguous_tokens_of_one_type(self) -> None:
        value = fewnerd_row_to_record(
            ["New", "York", "hosts", "UN"],
            [1, 1, 0, 2],
            ["O", "location-GPE", "organization-other"],
            "fewnerd-train-1",
        )
        self.assertEqual(value["text"], "New York hosts UN")
        self.assertEqual(
            [(entity["span"], entity["type"]) for entity in value["entities"]],
            [("New York", "location-GPE"), ("UN", "organization-other")],
        )
        validate_record(value)

    def test_duie_repeated_surfaces_use_nearest_pair(self) -> None:
        raw = {
            "text": "甲远乙近甲乙",
            "spo_list": [
                {
                    "subject": "甲",
                    "subject_type": "人物",
                    "predicate": "关联",
                    "object": {"@value": "乙"},
                    "object_type": {"@value": "人物"},
                }
            ],
        }
        audit = ConversionAudit()
        value = duie_row_to_record(raw, "duie-train-1", audit=audit)
        self.assertEqual(
            [(entity["start"], entity["span"]) for entity in value["entities"]],
            [(4, "甲"), (5, "乙")],
        )
        self.assertEqual(value["relations"], [{"head": 0, "tail": 1, "type": "关联"}])
        self.assertEqual(audit.counters["ambiguous_subject_surfaces"], 1)
        self.assertEqual(audit.counters["ambiguous_object_surfaces"], 1)
        validate_record(value)

    def test_duie_complex_object_key_is_preserved_in_relation_type(self) -> None:
        raw = {
            "text": "甲在乙作品中配音丙",
            "spo_list": [
                {
                    "subject": "甲",
                    "subject_type": "人物",
                    "predicate": "配音",
                    "object": {"@value": "丙", "inWork": "乙作品"},
                    "object_type": {"@value": "人物", "inWork": "影视作品"},
                }
            ],
        }
        value = duie_row_to_record(raw, "duie-train-2", audit=ConversionAudit())
        self.assertEqual(
            {relation["type"] for relation in value["relations"]},
            {"配音", "配音:inWork"},
        )
        validate_record(value)

    def test_cmnee_preserves_trigger_argument_and_coreference(self) -> None:
        raw = {
            "id": "7",
            "text": "甲执行任务，甲返回。",
            "event_list": [
                {
                    "event_type": "Manoeuvre",
                    "trigger": {"text": "执行", "offset": [1, 3]},
                    "arguments": [
                        {"role": "Subject", "text": "甲", "offset": [0, 1]},
                        {"role": "Content", "text": "任务", "offset": [3, 5]},
                    ],
                }
            ],
            "coref_arguments": [
                [
                    {"text": "甲", "offset": [0, 1]},
                    {"text": "甲", "offset": [6, 7]},
                ]
            ],
        }
        value = cmnee_row_to_record(raw, "train", audit=ConversionAudit())
        self.assertIn(
            {"head": 0, "tail": 1, "type": "HAS_ARGUMENT:Subject"},
            value["relations"],
        )
        self.assertIn("COREF", {relation["type"] for relation in value["relations"]})
        validate_record(value)

    def test_support_sampling_is_seeded_and_per_type(self) -> None:
        records = []
        for index in range(20):
            label = "A" if index % 2 == 0 else "B"
            records.append(
                {
                    "id": f"r{index}",
                    "text": "甲",
                    "entities": [
                        {"start": 0, "end": 1, "type": label, "span": "甲"}
                    ],
                    "relations": [],
                }
            )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "train.jsonl"
            write_jsonl_atomic(path, records)
            first = choose_support_ids(path, k=5, seed=42)
            second = choose_support_ids(path, k=5, seed=42)
            selected = list(iter_selected_records(path, first.selected_ids))
        self.assertEqual(first, second)
        self.assertEqual(len(first.selected_by_type["A"]), 5)
        self.assertEqual(len(first.selected_by_type["B"]), 5)
        self.assertEqual({record["id"] for record in selected}, set(first.selected_ids))


if __name__ == "__main__":
    unittest.main()
