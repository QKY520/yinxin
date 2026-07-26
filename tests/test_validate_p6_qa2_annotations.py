from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_p6_qa2_annotations.py"
SPEC = importlib.util.spec_from_file_location("validate_p6_qa2", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MODULE.CSV_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entity(text: str, span: str, entity_type: str, occurrence: int = 0) -> dict[str, object]:
    start = -1
    cursor = 0
    for _ in range(occurrence + 1):
        start = text.index(span, cursor)
        cursor = start + len(span)
    return {"start": start, "end": start + len(span), "type": entity_type, "span": span}


class ValidateP6QA2AnnotationsTests(unittest.TestCase):
    def make_package(
        self,
        root: Path,
        *,
        a_entities: list[list[dict[str, object]]] | None = None,
        b_entities: list[list[dict[str, object]]] | None = None,
        b_blank_index: int | None = None,
    ) -> tuple[MODULE.ValidationConfig, MODULE.ExpectedHashes]:
        texts = ["甲雷达工作，甲雷达停机。", "乙模块采用丙技术。"]
        default_entities = [
            [
                entity(texts[0], "甲雷达", "EQUIPMENT", 0),
                entity(texts[0], "甲雷达", "EQUIPMENT", 1),
            ],
            [
                entity(texts[1], "乙模块", "MODULE"),
                entity(texts[1], "丙技术", "TECH_SCHEME"),
            ],
        ]
        a_entities = a_entities if a_entities is not None else default_entities
        b_entities = b_entities if b_entities is not None else default_entities
        a_blank_rows = [
            {"blind_id": f"P6QA0-A-{index:04d}", "text": text, "entities_json": "", "notes": ""}
            for index, text in enumerate(texts, start=1)
        ]
        b_blank_rows = [
            {"blind_id": f"P6QA0-B-{index:04d}", "text": text, "entities_json": "", "notes": ""}
            for index, text in enumerate(reversed(texts), start=1)
        ]
        b_id_by_text = {row["text"]: row["blind_id"] for row in b_blank_rows}
        a_completed_rows = [
            row
            | {"entities_json": json.dumps(a_entities[index], ensure_ascii=False)}
            for index, row in enumerate(a_blank_rows)
        ]
        b_entities_by_text = {text: b_entities[index] for index, text in enumerate(texts)}
        b_completed_rows = [
            row
            | {
                "entities_json": json.dumps(b_entities_by_text[row["text"]], ensure_ascii=False)
            }
            for row in b_blank_rows
        ]
        if b_blank_index is not None:
            target_text = texts[b_blank_index]
            for row in b_completed_rows:
                if row["text"] == target_text:
                    row["entities_json"] = ""

        input_dir = root / "inputs"
        paths = {
            "a_blank": input_dir / "a_blank.csv",
            "b_blank": input_dir / "b_blank.csv",
            "a_completed": input_dir / "a_completed.csv",
            "b_completed": input_dir / "b_completed.csv",
            "map": input_dir / "map.jsonl",
        }
        write_csv(paths["a_blank"], a_blank_rows)
        write_csv(paths["b_blank"], b_blank_rows)
        write_csv(paths["a_completed"], a_completed_rows)
        write_csv(paths["b_completed"], b_completed_rows)
        map_rows = [
            {
                "original_id": f"original-{index}",
                "annotator_a_blind_id": a_blank_rows[index - 1]["blind_id"],
                "annotator_b_blind_id": b_id_by_text[text],
                "text_sha256": MODULE.text_sha256(text),
                "source_type": "test",
                "prior_label_source": "test",
            }
            for index, text in enumerate(texts, start=1)
        ]
        write_jsonl(paths["map"], map_rows)
        config = MODULE.ValidationConfig(
            annotator_a_completed=paths["a_completed"],
            annotator_b_completed=paths["b_completed"],
            annotator_a_blank=paths["a_blank"],
            annotator_b_blank=paths["b_blank"],
            blind_map=paths["map"],
            output_dir=root / "output",
        )
        hashes = MODULE.ExpectedHashes(
            annotator_a_completed=sha(paths["a_completed"]),
            annotator_b_completed=sha(paths["b_completed"]),
            annotator_a_blank=sha(paths["a_blank"]),
            annotator_b_blank=sha(paths["b_blank"]),
            blind_map=sha(paths["map"]),
        )
        return config, hashes

    def test_valid_package_scores_exact_file_concordance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config, hashes = self.make_package(Path(temporary))
            report = MODULE.validate_qa2(config, expected_hashes=hashes, expected_rows=2)
            self.assertEqual(report["status"], "file_quality_passed")
            self.assertEqual(report["validation"]["issue_count"], 0)
            self.assertEqual(report["diagnostic_file_concordance"]["paired_rows"], 2)
            self.assertEqual(report["diagnostic_file_concordance"]["f1"], 1.0)
            self.assertIsNone(report["formal_human_iaa"])

    def test_blank_and_unresolved_repeated_mention_block_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            text = "甲雷达工作，甲雷达停机。"
            incomplete_a = [
                [entity(text, "甲雷达", "EQUIPMENT", 0)],
                [entity("乙模块采用丙技术。", "乙模块", "MODULE")],
            ]
            config, hashes = self.make_package(
                root,
                a_entities=incomplete_a,
                b_blank_index=1,
            )
            report = MODULE.validate_qa2(config, expected_hashes=hashes, expected_rows=2)
            self.assertEqual(report["status"], "blocked")
            self.assertEqual(report["validation"]["hard_error_count"], 1)
            self.assertGreaterEqual(report["validation"]["blocking_review_count"], 1)
            codes = report["validation"]["code_counts"]
            self.assertEqual(codes["EMPTY_ENTITIES_FIELD"], 1)
            self.assertEqual(codes["REPEATED_MENTION_UNRESOLVED"], 1)

    def test_type_disagreement_is_counted_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            text_two = "乙模块采用丙技术。"
            b_entities = [
                [
                    entity("甲雷达工作，甲雷达停机。", "甲雷达", "EQUIPMENT", 0),
                    entity("甲雷达工作，甲雷达停机。", "甲雷达", "EQUIPMENT", 1),
                ],
                [
                    entity(text_two, "乙模块", "EQUIPMENT"),
                    entity(text_two, "丙技术", "TECH_SCHEME"),
                ],
            ]
            config, hashes = self.make_package(root, b_entities=b_entities)
            report = MODULE.validate_qa2(config, expected_hashes=hashes, expected_rows=2)
            score = report["diagnostic_file_concordance"]
            self.assertEqual(score["annotator_a_entities"], 4)
            self.assertEqual(score["annotator_b_entities"], 4)
            self.assertEqual(score["exact_matches"], 3)
            self.assertEqual(score["f1"], 0.75)
            self.assertEqual(report["disagreement_rows"], 1)

    def test_rejects_hash_mismatch_and_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_package(root)
            wrong = MODULE.ExpectedHashes(
                annotator_a_completed="0" * 64,
                annotator_b_completed=hashes.annotator_b_completed,
                annotator_a_blank=hashes.annotator_a_blank,
                annotator_b_blank=hashes.annotator_b_blank,
                blind_map=hashes.blind_map,
            )
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                MODULE.validate_qa2(config, expected_hashes=wrong, expected_rows=2)
            MODULE.validate_qa2(config, expected_hashes=hashes, expected_rows=2)
            with self.assertRaises(FileExistsError):
                MODULE.validate_qa2(config, expected_hashes=hashes, expected_rows=2)


if __name__ == "__main__":
    unittest.main()
