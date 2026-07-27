from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_p6_qa1r_calibration.py"
)
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location("validate_p6_qa1r_calibration", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MODULE.CSV_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def entity(text: str, span: str, entity_type: str, occurrence: int = 0) -> dict[str, object]:
    cursor = 0
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(span, cursor)
        cursor = start + len(span)
    return {"start": start, "end": start + len(span), "type": entity_type, "span": span}


class ValidateP6QA1RCalibrationTests(unittest.TestCase):
    def make_package(
        self,
        root: Path,
        *,
        b_type: str = "EQUIPMENT",
        omit_second_a: bool = False,
        invalid_uncertainty: bool = False,
        duplicate_uncertainty: bool = False,
        unsorted_b: bool = False,
    ) -> tuple[MODULE.ValidationConfig, MODULE.ExpectedHashes]:
        texts = ["甲雷达工作，甲雷达停机。", "乙模块采用丙技术，指标值10公里。"]
        a_entities = [
            [entity(texts[0], "甲雷达", "EQUIPMENT", 0)],
            [
                entity(texts[1], "乙模块", "MODULE"),
                entity(texts[1], "丙技术", "TECH_SCHEME"),
                entity(texts[1], "指标值10公里", "METRIC"),
            ],
        ]
        if not omit_second_a:
            a_entities[0].append(entity(texts[0], "甲雷达", "EQUIPMENT", 1))
        b_entities = [
            [
                entity(texts[0], "甲雷达", b_type, 0),
                entity(texts[0], "甲雷达", b_type, 1),
            ],
            a_entities[1],
        ]
        if unsorted_b:
            b_entities[1] = list(reversed(b_entities[1]))
        a_blank = [
            {
                "blind_id": f"P6CAL-A-{index:03d}",
                "text": text,
                "entities_json": "",
                "notes": "",
                "uncertainty_code": "",
            }
            for index, text in enumerate(texts, start=1)
        ]
        b_blank = [
            {
                "blind_id": f"P6CAL-B-{index:03d}",
                "text": text,
                "entities_json": "",
                "notes": "",
                "uncertainty_code": "",
            }
            for index, text in enumerate(texts, start=1)
        ]
        a_completed = [
            row
            | {
                "entities_json": json.dumps(a_entities[index], ensure_ascii=False),
                "uncertainty_code": (
                    "BAD"
                    if invalid_uncertainty and index == 0
                    else (
                        "TYPE_EQUIPMENT_MODULE;TYPE_EQUIPMENT_MODULE"
                        if duplicate_uncertainty and index == 0
                        else ""
                    )
                ),
            }
            for index, row in enumerate(a_blank)
        ]
        b_completed = [
            row | {"entities_json": json.dumps(b_entities[index], ensure_ascii=False)}
            for index, row in enumerate(b_blank)
        ]
        paths = {
            "a_blank": root / "inputs" / "a_blank.csv",
            "b_blank": root / "inputs" / "b_blank.csv",
            "a_completed": root / "inputs" / "a_completed.csv",
            "b_completed": root / "inputs" / "b_completed.csv",
            "map": root / "inputs" / "map.jsonl",
        }
        write_csv(paths["a_blank"], a_blank)
        write_csv(paths["b_blank"], b_blank)
        write_csv(paths["a_completed"], a_completed)
        write_csv(paths["b_completed"], b_completed)
        write_jsonl(
            paths["map"],
            [
                {
                    "original_id": f"dev-{index}",
                    "annotator_a_blind_id": a_blank[index - 1]["blind_id"],
                    "annotator_b_blind_id": b_blank[index - 1]["blind_id"],
                    "text_sha256": MODULE.text_sha256(text),
                    "selection_bucket": "TEST",
                }
                for index, text in enumerate(texts, start=1)
            ],
        )
        config = MODULE.ValidationConfig(
            annotator_a_completed=paths["a_completed"],
            annotator_b_completed=paths["b_completed"],
            annotator_a_blank=paths["a_blank"],
            annotator_b_blank=paths["b_blank"],
            coordinator_map=paths["map"],
            output_dir=root / "output",
        )
        hashes = MODULE.ExpectedHashes(
            annotator_a_completed=sha(paths["a_completed"]),
            annotator_b_completed=sha(paths["b_completed"]),
            annotator_a_blank=sha(paths["a_blank"]),
            annotator_b_blank=sha(paths["b_blank"]),
            coordinator_map=sha(paths["map"]),
        )
        return config, hashes

    def test_exact_calibration_package_meets_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary))
            report = MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            self.assertEqual(report["status"], "calibration_target_met")
            self.assertEqual(report["calibration_file_concordance"]["f1"], 1.0)
            self.assertTrue(report["validation"]["all_types_covered_by_both"])
            self.assertIsNone(report["formal_human_iaa"])

    def test_repeated_mention_warning_blocks_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary), omit_second_a=True)
            report = MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["validation"]["blocking_review_count"], 1)
            self.assertEqual(
                report["validation"]["code_counts"]["REPEATED_MENTION_UNRESOLVED"], 1
            )

    def test_type_disagreement_is_scored_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary), b_type="MODULE")
            report = MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            self.assertLess(report["calibration_file_concordance"]["f1"], 1.0)
            self.assertEqual(report["disagreement_rows"], 1)

    def test_duplicate_uncertainty_code_is_warning_not_label_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(
                Path(temporary), duplicate_uncertainty=True
            )
            report = MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            self.assertEqual(report["status"], "calibration_target_met")
            self.assertEqual(
                report["validation"]["code_counts"]["DUPLICATE_UNCERTAINTY_CODE"], 1
            )

    def test_unsorted_entities_get_secondary_order_insensitive_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary), unsorted_b=True)
            report = MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["validation"]["hard_error_count"], 1)
            self.assertEqual(report["validation"]["non_order_hard_error_count"], 0)
            self.assertEqual(
                report["secondary_all_rows_order_insensitive_concordance"]["f1"], 1.0
            )

    def test_invalid_uncertainty_code_and_existing_output_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_package(root, invalid_uncertainty=True)
            with self.assertRaisesRegex(ValueError, "invalid uncertainty"):
                MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            config, hashes = self.make_package(root / "valid")
            MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)
            with self.assertRaises(FileExistsError):
                MODULE.validate_calibration(config, expected_hashes=hashes, expected_rows=2)


if __name__ == "__main__":
    unittest.main()
