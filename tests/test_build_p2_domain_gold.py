from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.schema import iter_jsonl  # noqa: E402
from scripts.build_p2_domain_gold import main as build_main  # noqa: E402


FIELDS = [
    "review_id",
    "source_type",
    "source_id",
    "source_url",
    "source_license",
    "title_display",
    "text_display",
    "text_json",
    "annotator_a_entities_json",
    "annotator_a_relations_json",
    "adjudicated_entities_json",
    "adjudicated_relations_json",
]


def text_for(index: int) -> str:
    return f"Equipment {index:04d} uses Module {index:04d} with Metric {index:04d}."


def row_for(index: int) -> dict[str, str]:
    text = text_for(index)
    equipment = f"Equipment {index:04d}"
    module = f"Module {index:04d}"
    metric = f"Metric {index:04d}"
    entities = [
        {"start": text.index(equipment), "end": text.index(equipment) + len(equipment), "type": "EQUIPMENT", "span": equipment},
        {"start": text.index(module), "end": text.index(module) + len(module), "type": "MODULE", "span": module},
        {"start": text.index(metric), "end": text.index(metric) + len(metric), "type": "METRIC", "span": metric},
    ]
    relations = [
        {"head": 0, "tail": 1, "type": "USES"},
        {"head": 0, "tail": 2, "type": "HAS_METRIC"},
    ]
    return {
        "review_id": f"domain-candidate-{index:04d}",
        "source_type": "unit",
        "source_id": str(index),
        "source_url": "https://example.test",
        "source_license": "MIT",
        "title_display": f"title {index}",
        "text_display": text,
        "text_json": json.dumps(text),
        "annotator_a_entities_json": json.dumps(entities),
        "annotator_a_relations_json": json.dumps(relations),
        "adjudicated_entities_json": json.dumps(entities),
        "adjudicated_relations_json": json.dumps(relations),
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class BuildP2DomainGoldTest(unittest.TestCase):
    def test_builds_freeze_outputs_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [row_for(index) for index in range(1, 251)]
            row_150 = rows[149]
            text_150 = row_150["text_display"]
            long_span = "Equipment 0150 uses Module 0150"
            short_span = "Module 0150"
            metric_span = "Metric 0150"
            row_150["annotator_a_entities_json"] = json.dumps(
                [
                    {
                        "start": text_150.index(long_span),
                        "end": text_150.index(long_span) + len(long_span),
                        "type": "TECH_SCHEME",
                        "span": long_span,
                    },
                    {
                        "start": text_150.index(short_span),
                        "end": text_150.index(short_span) + len(short_span),
                        "type": "MODULE",
                        "span": short_span,
                    },
                    {
                        "start": text_150.index(metric_span),
                        "end": text_150.index(metric_span) + len(metric_span),
                        "type": "METRIC",
                        "span": metric_span,
                    },
                ]
            )
            row_150["annotator_a_relations_json"] = json.dumps(
                [{"head": 1, "tail": 2, "type": "HAS_METRIC"}]
            )
            annotator_a = root / "annotator_a_250.csv"
            adjudication = root / "adjudication_sheet.csv"
            candidates = root / "domain_candidates.jsonl"
            write_csv(annotator_a, rows)
            write_csv(adjudication, rows[:100])
            with candidates.open("w", encoding="utf-8", newline="\n") as handle:
                for index in range(1, 251):
                    handle.write(
                        json.dumps(
                            {
                                "id": f"domain-candidate-{index:04d}",
                                "text": text_for(index),
                                "source_type": "unit",
                                "source_id": str(index),
                            }
                        )
                        + "\n"
                    )

            argv = sys.argv
            sys.argv = [
                "build_p2_domain_gold.py",
                "--annotator-a",
                str(annotator_a),
                "--adjudication",
                str(adjudication),
                "--candidates",
                str(candidates),
                "--data-root",
                str(root / "data_root"),
                "--project-data-root",
                str(root / "project_data"),
                "--log-root",
                str(root / "logs"),
            ]
            try:
                self.assertEqual(build_main(), 0)
            finally:
                sys.argv = argv

            self.assertEqual(len(list(iter_jsonl(root / "data_root" / "domain_support.jsonl"))), 30)
            self.assertEqual(len(list(iter_jsonl(root / "data_root" / "domain_dev.jsonl"))), 50)
            self.assertEqual(len(list(iter_jsonl(root / "data_root" / "domain_test.jsonl"))), 170)
            self.assertTrue((root / "data_root" / "FROZEN").is_file())
            self.assertTrue((root / "project_data" / "FROZEN").is_file())
            gold_by_id = {
                record["id"]: record
                for record in iter_jsonl(root / "data_root" / "domain_gold_250.jsonl")
            }
            self.assertEqual(gold_by_id["domain-candidate-0150"]["relations"], [])

            dedup = json.loads((root / "logs" / "dedup.json").read_text(encoding="utf-8"))
            self.assertEqual(dedup["removed_count"], 170)
            self.assertEqual(dedup["rag_corpus_records"], 80)

            repair_log = json.loads(
                (root / "logs" / "p2_domain_gold_repair_log.json").read_text(encoding="utf-8")
            )
            self.assertEqual(repair_log["summary"]["affected_record_ids"], ["domain-candidate-0150"])
            self.assertEqual(repair_log["summary"]["event_counts"]["ENTITY_NESTED_OVERLAP_DROPPED"], 1)
            self.assertEqual(repair_log["summary"]["event_counts"]["RELATION_DROPPED_REMOVED_ENTITY"], 1)

            manifest = json.loads(
                (root / "logs" / "p2_domain_gold_manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["label_sources"]["adjudicated_double_annotation"], 100)
            self.assertEqual(manifest["label_sources"]["annotator_a_single_annotation"], 150)
            self.assertNotIn("manifest", manifest["files"])
            self.assertEqual(manifest["repairs"]["affected_record_ids"], ["domain-candidate-0150"])
            self.assertIn("repair_log", manifest["files"])


if __name__ == "__main__":
    unittest.main()
