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
    / "prepare_p6_qa0_blind_annotation.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_p6_qa0", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PrepareP6QA0BlindAnnotationTests(unittest.TestCase):
    def make_inputs(self, root: Path) -> tuple[Path, Path, Path, list[dict[str, object]]]:
        records: list[dict[str, object]] = [
            {
                "id": f"record-{index}",
                "text": text,
                "entities": [{"start": 0, "end": 1, "type": "EQUIPMENT", "span": text[0]}],
                "relations": [],
            }
            for index, text in enumerate(
                ["甲型系统采用导航技术。", "乙型雷达探测距离较远。", "丙型平台含控制模块。"],
                start=1,
            )
        ]
        test_path = root / "inputs" / "data" / "domain_test.jsonl"
        source_map_path = root / "inputs" / "data" / "domain_gold_source_map.jsonl"
        frozen_path = root / "inputs" / "data" / "FROZEN"
        write_jsonl(test_path, records)
        source_rows = [
            {
                "id": row["id"],
                "split": "test",
                "source_type": "cmnee",
                "label_source": (
                    "adjudicated_double_annotation"
                    if index == 1
                    else "annotator_a_single_annotation"
                ),
                "text_sha256": MODULE.text_sha256(str(row["text"])),
                "title": "must-not-leak",
            }
            for index, row in enumerate(records, start=1)
        ]
        source_rows.append(
            {
                "id": "record-dev",
                "split": "dev",
                "source_type": "patent",
                "label_source": "annotator_a_single_annotation",
                "text_sha256": "0" * 64,
            }
        )
        write_jsonl(source_map_path, source_rows)
        frozen_path.write_text(
            json.dumps({"phase": "P2", "test_size": len(records)}),
            encoding="utf-8",
        )
        return test_path, source_map_path, frozen_path, records

    def prepare(self, root: Path, output_name: str = "package") -> tuple[Path, dict[str, object]]:
        test_path, source_map_path, frozen_path, records = self.make_inputs(root)
        output_dir = root / "outputs" / output_name
        config = MODULE.PreparationConfig(
            test_jsonl=test_path,
            source_map_jsonl=source_map_path,
            frozen_marker=frozen_path,
            output_dir=output_dir,
            annotator_a_seed=101,
            annotator_b_seed=202,
        )
        manifest = MODULE.prepare_annotation_package(
            config,
            expected_test_sha256=file_sha256(test_path),
            expected_test_rows=len(records),
        )
        return output_dir, manifest

    def read_csv(self, path: Path) -> tuple[list[str], list[dict[str, str]]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            return list(reader.fieldnames or []), rows

    def test_prepares_blank_independently_shuffled_sheets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_dir, manifest = self.prepare(root)
            a_path = output_dir / "annotator_a_blind.csv"
            b_path = output_dir / "annotator_b_blind.csv"
            fields_a, rows_a = self.read_csv(a_path)
            fields_b, rows_b = self.read_csv(b_path)

            self.assertEqual(fields_a, list(MODULE.CSV_FIELDS))
            self.assertEqual(fields_b, list(MODULE.CSV_FIELDS))
            self.assertEqual(len(rows_a), 3)
            self.assertEqual(len(rows_b), 3)
            self.assertNotEqual([row["text"] for row in rows_a], [row["text"] for row in rows_b])
            self.assertEqual({row["text"] for row in rows_a}, {row["text"] for row in rows_b})
            self.assertTrue(all(row["entities_json"] == "" for row in rows_a + rows_b))
            self.assertTrue(all(row["notes"] == "" for row in rows_a + rows_b))
            self.assertTrue(all(row["blind_id"].startswith("P6QA0-A-") for row in rows_a))
            self.assertTrue(all(row["blind_id"].startswith("P6QA0-B-") for row in rows_b))
            self.assertTrue(a_path.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertEqual(
                a_path.read_text(encoding="utf-8-sig").splitlines()[0],
                '"blind_id","text","entities_json","notes"',
            )
            self.assertTrue(manifest["blind_generation"]["orders_differ"])
            self.assertFalse(manifest["scope"]["relations_in_scope"])

    def test_coordinator_map_contains_only_required_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir, _ = self.prepare(Path(temporary))
            rows = MODULE.read_jsonl(output_dir / "blind_id_map.jsonl")
            expected_fields = {
                "original_id",
                "annotator_a_blind_id",
                "annotator_b_blind_id",
                "text_sha256",
                "source_type",
                "prior_label_source",
            }
            self.assertEqual(len(rows), 3)
            self.assertTrue(all(set(row) == expected_fields for row in rows))
            self.assertTrue(all("text" not in row for row in rows))
            self.assertTrue(all("entities" not in row for row in rows))
            self.assertTrue(all("title" not in row for row in rows))

    def test_generation_is_deterministic_for_same_inputs_and_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root_one = Path(temporary) / "one"
            root_two = Path(temporary) / "two"
            output_one, _ = self.prepare(root_one)
            output_two, _ = self.prepare(root_two)
            for filename in (
                "annotator_a_blind.csv",
                "annotator_b_blind.csv",
                "blind_id_map.jsonl",
            ):
                self.assertEqual(
                    (output_one / filename).read_bytes(),
                    (output_two / filename).read_bytes(),
                )

    def test_rejects_wrong_hash_missing_marker_equal_seeds_and_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            test_path, source_map_path, frozen_path, records = self.make_inputs(root)
            base = MODULE.PreparationConfig(
                test_jsonl=test_path,
                source_map_jsonl=source_map_path,
                frozen_marker=frozen_path,
                output_dir=root / "outputs" / "package",
                annotator_a_seed=101,
                annotator_b_seed=202,
            )
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                MODULE.prepare_annotation_package(
                    base,
                    expected_test_sha256="0" * 64,
                    expected_test_rows=len(records),
                )

            frozen_path.unlink()
            with self.assertRaises(FileNotFoundError):
                MODULE.prepare_annotation_package(
                    base,
                    expected_test_sha256=file_sha256(test_path),
                    expected_test_rows=len(records),
                )
            frozen_path.write_text(
                json.dumps({"phase": "P2", "test_size": len(records)}),
                encoding="utf-8",
            )

            equal_seed = MODULE.PreparationConfig(
                test_jsonl=test_path,
                source_map_jsonl=source_map_path,
                frozen_marker=frozen_path,
                output_dir=root / "outputs" / "equal-seed",
                annotator_a_seed=1,
                annotator_b_seed=1,
            )
            with self.assertRaisesRegex(ValueError, "must be distinct"):
                MODULE.prepare_annotation_package(
                    equal_seed,
                    expected_test_sha256=file_sha256(test_path),
                    expected_test_rows=len(records),
                )

            MODULE.prepare_annotation_package(
                base,
                expected_test_sha256=file_sha256(test_path),
                expected_test_rows=len(records),
            )
            with self.assertRaises(FileExistsError):
                MODULE.prepare_annotation_package(
                    base,
                    expected_test_sha256=file_sha256(test_path),
                    expected_test_rows=len(records),
                )


if __name__ == "__main__":
    unittest.main()
