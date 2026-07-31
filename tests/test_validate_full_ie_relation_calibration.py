from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "validate_full_ie_relation_calibration.py"
)
SPEC = importlib.util.spec_from_file_location(
    "validate_full_ie_relation_calibration", SCRIPT_PATH
)
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


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def entity(text: str, span: str, entity_type: str) -> dict[str, object]:
    start = text.index(span)
    return {
        "start": start,
        "end": start + len(span),
        "type": entity_type,
        "span": span,
    }


def relation(value: list[dict[str, object]]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class ValidateFullIERelationCalibrationTests(unittest.TestCase):
    def make_package(
        self,
        root: Path,
        *,
        b_relation: list[dict[str, object]] | None = None,
        b_tail_type: str = "MODULE",
        a_relations_value: str | None = None,
        b_relations_value: str | None = None,
        b_uncertainty: str = "",
        b_notes: str = "",
    ) -> tuple[MODULE.ValidationConfig, MODULE.ExpectedHashes]:
        texts = ["甲雷达搭载乙模块。", "丙模块完成测试。"]
        a_entities = [
            [
                entity(texts[0], "甲雷达", "EQUIPMENT"),
                entity(texts[0], "乙模块", "MODULE"),
            ],
            [entity(texts[1], "丙模块", "MODULE")],
        ]
        b_entities = [
            [
                entity(texts[0], "甲雷达", "EQUIPMENT"),
                entity(texts[0], "乙模块", b_tail_type),
            ],
            [entity(texts[1], "丙模块", "MODULE")],
        ]
        base_relation = [{"head": 0, "tail": 1, "type": "USES"}]
        if b_relation is None:
            b_relation = base_relation

        a_rows_by_original: list[dict[str, str]] = []
        b_rows_by_original: list[dict[str, str]] = []
        for index, text in enumerate(texts, start=1):
            a_entity_json = json.dumps(a_entities[index - 1], ensure_ascii=False)
            b_entity_json = json.dumps(b_entities[index - 1], ensure_ascii=False)
            a_rows_by_original.append(
                {
                    "blind_id": f"P6FRESH-A-{index:03d}",
                    "text": text,
                    "entities_json_locked": a_entity_json,
                    "entity_index_guide": f"A guide {index}",
                    "relations_json": "",
                    "relation_notes": "",
                    "relation_uncertainty_code": "",
                }
            )
            b_rows_by_original.append(
                {
                    "blind_id": f"P6FRESH-B-{index:03d}",
                    "text": text,
                    "entities_json_locked": b_entity_json,
                    "entity_index_guide": f"B guide {index}",
                    "relations_json": "",
                    "relation_notes": "",
                    "relation_uncertainty_code": "",
                }
            )

        blank_a = a_rows_by_original
        blank_b = list(reversed(b_rows_by_original))
        completed_a = [dict(row) for row in blank_a]
        completed_b = [dict(row) for row in blank_b]
        completed_a[0]["relations_json"] = (
            a_relations_value if a_relations_value is not None else relation(base_relation)
        )
        completed_a[1]["relations_json"] = "[]"
        b_first_id = b_rows_by_original[0]["blind_id"]
        for row in completed_b:
            if row["blind_id"] == b_first_id:
                row["relations_json"] = (
                    b_relations_value
                    if b_relations_value is not None
                    else relation(b_relation)
                )
                row["relation_uncertainty_code"] = b_uncertainty
                row["relation_notes"] = b_notes
            else:
                row["relations_json"] = "[]"

        paths = {
            "a_blank": root / "inputs" / "a_blank.csv",
            "b_blank": root / "inputs" / "b_blank.csv",
            "a_completed": root / "inputs" / "a_completed.csv",
            "b_completed": root / "inputs" / "b_completed.csv",
            "map": root / "inputs" / "map.jsonl",
        }
        write_csv(paths["a_blank"], blank_a)
        write_csv(paths["b_blank"], blank_b)
        write_csv(paths["a_completed"], completed_a)
        write_csv(paths["b_completed"], completed_b)
        map_rows: list[dict[str, object]] = []
        for index, text in enumerate(texts, start=1):
            a_row = a_rows_by_original[index - 1]
            b_row = b_rows_by_original[index - 1]
            map_rows.append(
                {
                    "original_id": f"non-test-{index}",
                    "annotator_a_blind_id": a_row["blind_id"],
                    "annotator_b_blind_id": b_row["blind_id"],
                    "text_sha256": MODULE.sha256_text(text),
                    "selection_bucket": "SYNTHETIC",
                    "annotator_a_entities_sha256": MODULE.sha256_text(
                        a_row["entities_json_locked"]
                    ),
                    "annotator_b_entities_sha256": MODULE.sha256_text(
                        b_row["entities_json_locked"]
                    ),
                    "annotator_a_entity_count": len(a_entities[index - 1]),
                    "annotator_b_entity_count": len(b_entities[index - 1]),
                }
            )
        write_jsonl(paths["map"], map_rows)
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

    def validate(
        self,
        config: MODULE.ValidationConfig,
        hashes: MODULE.ExpectedHashes,
    ) -> dict[str, object]:
        with patch.dict(os.environ, {MODULE.GATE_NAME: "1"}, clear=False):
            return MODULE.validate_relation_calibration(
                config, expected_hashes=hashes, expected_rows=2
            )

    def test_exact_directed_identical_annotations_complete_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary))
            report = self.validate(config, hashes)
            score = report["exact_directed_file_concordance"]
            self.assertEqual(report["status"], "completed_diagnostic")
            self.assertEqual(score["true_positive"], 1)
            self.assertEqual(score["f1"], 1.0)
            self.assertEqual(score["row_exact_matches"], 2)
            self.assertIsNone(report["formal_human_iaa"])

    def test_reversed_direction_counts_as_false_positive_and_false_negative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(
                Path(temporary),
                b_relation=[{"head": 1, "tail": 0, "type": "USES"}],
            )
            report = self.validate(config, hashes)
            score = report["exact_directed_file_concordance"]
            self.assertEqual(report["status"], "completed_diagnostic")
            self.assertEqual(score["true_positive"], 0)
            self.assertEqual(score["false_positive"], 1)
            self.assertEqual(score["false_negative"], 1)

    def test_endpoint_type_difference_is_exact_disagreement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(
                Path(temporary), b_tail_type="TECH_SCHEME"
            )
            report = self.validate(config, hashes)
            score = report["exact_directed_file_concordance"]
            self.assertEqual(report["status"], "completed_diagnostic")
            self.assertEqual(score["f1"], 0.0)
            self.assertEqual(report["disagreement_rows"], 1)

    def test_duplicate_and_illegal_type_matrix_are_structural_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            duplicate = [
                {"head": 0, "tail": 1, "type": "USES"},
                {"head": 0, "tail": 1, "type": "USES"},
            ]
            config, hashes = self.make_package(Path(temporary), b_relation=duplicate)
            report = self.validate(config, hashes)
            self.assertEqual(report["status"], "blocked_structural_errors")
            self.assertEqual(
                report["validation"]["issue_code_counts"]["RELATION_DUPLICATE"], 1
            )

        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(
                Path(temporary),
                b_relation=[{"head": 0, "tail": 1, "type": "HAS_METRIC"}],
            )
            report = self.validate(config, hashes)
            self.assertEqual(report["status"], "blocked_structural_errors")
            self.assertEqual(
                report["validation"]["issue_code_counts"]["RELATION_TYPE_MATRIX"], 1
            )

    def test_blank_invalid_json_and_invalid_uncertainty_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(
                Path(temporary),
                a_relations_value="",
                b_relations_value="not-json",
                b_uncertainty="BAD_CODE",
            )
            report = self.validate(config, hashes)
            codes = report["validation"]["issue_code_counts"]
            self.assertEqual(report["status"], "blocked_structural_errors")
            self.assertEqual(codes["RELATIONS_MISSING"], 1)
            self.assertEqual(codes["RELATIONS_INVALID_JSON"], 1)
            self.assertEqual(codes["UNCERTAINTY_INVALID"], 1)

    def test_gate_read_only_fields_hashes_and_existing_output_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_package(root)
            with self.assertRaises(PermissionError):
                MODULE.validate_relation_calibration(
                    config, expected_hashes=hashes, expected_rows=2
                )

            rows = MODULE.read_csv(config.annotator_a_completed)
            rows[0]["text"] += "改"
            write_csv(config.annotator_a_completed, rows)
            changed_hashes = MODULE.ExpectedHashes(
                annotator_a_completed=sha(config.annotator_a_completed),
                annotator_b_completed=hashes.annotator_b_completed,
                annotator_a_blank=hashes.annotator_a_blank,
                annotator_b_blank=hashes.annotator_b_blank,
                coordinator_map=hashes.coordinator_map,
            )
            with patch.dict(os.environ, {MODULE.GATE_NAME: "1"}, clear=False):
                with self.assertRaisesRegex(ValueError, "read-only field text changed"):
                    MODULE.validate_relation_calibration(
                        config, expected_hashes=changed_hashes, expected_rows=2
                    )

        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary))
            self.validate(config, hashes)
            with self.assertRaises(FileExistsError):
                self.validate(config, hashes)

    def test_revised_profile_has_separate_gate_and_locked_hashes(self) -> None:
        revised_gate, revised_hashes = MODULE.INPUT_PROFILES[
            MODULE.REVISED_INPUT_PROFILE
        ]
        self.assertEqual(revised_gate, MODULE.REVALIDATION_GATE_NAME)
        self.assertEqual(
            revised_hashes.annotator_a_completed,
            MODULE.EXPECTED_REVISED_COMPLETED_A_SHA256,
        )
        self.assertEqual(
            revised_hashes.annotator_b_completed,
            MODULE.EXPECTED_REVISED_COMPLETED_B_SHA256,
        )

        with tempfile.TemporaryDirectory() as temporary:
            config, synthetic_hashes = self.make_package(Path(temporary))
            with patch.dict(os.environ, {MODULE.GATE_NAME: "1"}, clear=True):
                with self.assertRaises(PermissionError):
                    MODULE.validate_relation_calibration(
                        config,
                        expected_hashes=synthetic_hashes,
                        expected_rows=2,
                        gate_name=MODULE.REVALIDATION_GATE_NAME,
                        input_profile=MODULE.REVISED_INPUT_PROFILE,
                    )

            with patch.dict(
                os.environ, {MODULE.REVALIDATION_GATE_NAME: "1"}, clear=True
            ):
                report = MODULE.validate_relation_calibration(
                    config,
                    expected_hashes=synthetic_hashes,
                    expected_rows=2,
                    gate_name=MODULE.REVALIDATION_GATE_NAME,
                    input_profile=MODULE.REVISED_INPUT_PROFILE,
                )

            self.assertEqual(report["gate"], MODULE.REVALIDATION_GATE_NAME)
            self.assertEqual(report["input_profile"], MODULE.REVISED_INPUT_PROFILE)
            self.assertTrue(
                report["scope"]["input_annotations_revised_after_prior_validation"]
            )
            self.assertTrue(report["scope"]["prior_failed_validation_preserved"])
            manifest = json.loads((config.output_dir / "manifest.json").read_text())
            self.assertEqual(manifest["gate"], MODULE.REVALIDATION_GATE_NAME)
            self.assertEqual(manifest["input_profile"], MODULE.REVISED_INPUT_PROFILE)


if __name__ == "__main__":
    unittest.main()
