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
    / "prepare_p6_qa1r_fresh_calibration.py"
)
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location(
    "prepare_p6_qa1r_fresh_calibration", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PrepareP6QA1RFreshCalibrationTests(unittest.TestCase):
    def write_dev(self, path: Path) -> list[dict[str, object]]:
        texts = [
            "旧指标最大射程10公里。",
            "旧方案采用跟踪技术。",
            "旧系统包含处理模块。",
            "旧雷达连接旧雷达。",
            "甲指标最大射程100公里。",
            "乙指标重量20千克。",
            "采用脉冲压缩技术。",
            "采用自适应控制方法。",
            "信号处理模块正在运行。",
            "传感器装置已启动。",
            "甲雷达与甲雷达同时工作。",
            "乙平台连接乙平台控制器。",
        ]
        rows = [
            {
                "id": f"dev-{index:02d}",
                "text": text,
                "entities": [{"secret": f"gold-{index}"}],
                "relations": [{"secret": f"relation-{index}"}],
            }
            for index, text in enumerate(texts, start=1)
        ]
        path.parent.mkdir(parents=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return rows

    def write_retired_map(
        self, path: Path, rows: list[dict[str, object]], *, unknown: bool = False
    ) -> None:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for index, row in enumerate(rows[:4], start=1):
                text = str(row["text"])
                digest = MODULE.text_sha256(text)
                original_id = str(row["id"])
                if unknown and index == 1:
                    digest = "f" * 64
                    original_id = "unknown-dev"
                payload = {
                    "original_id": original_id,
                    "annotator_a_blind_id": f"OLD-A-{index:03d}",
                    "annotator_b_blind_id": f"OLD-B-{index:03d}",
                    "text_sha256": digest,
                    "selection_bucket": "OLD",
                }
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def make_config(
        self, root: Path, *, unknown_retired: bool = False
    ) -> tuple[object, dict[str, str]]:
        dev = root / "data" / "domain_dev.jsonl"
        rows = self.write_dev(dev)
        retired_map = root / "retired_map.jsonl"
        self.write_retired_map(retired_map, rows, unknown=unknown_retired)
        guideline = root / MODULE.GUIDELINE_NAME
        a_instructions = root / MODULE.A_INSTRUCTIONS_NAME
        b_instructions = root / MODULE.B_INSTRUCTIONS_NAME
        guideline.write_text("locked guideline\n", encoding="utf-8")
        a_instructions.write_text("A instructions\n", encoding="utf-8")
        b_instructions.write_text("B instructions\n", encoding="utf-8")
        config = MODULE.FreshCalibrationConfig(
            dev_jsonl=dev,
            retired_map=retired_map,
            guideline=guideline,
            annotator_a_instructions=a_instructions,
            annotator_b_instructions=b_instructions,
            output_dir=root / "backup" / "fresh",
            selection_seed=11,
            annotator_a_seed=12,
            annotator_b_seed=13,
        )
        hashes = {
            "dev": hashlib.sha256(dev.read_bytes()).hexdigest(),
            "retired": hashlib.sha256(retired_map.read_bytes()).hexdigest(),
            "guideline": hashlib.sha256(guideline.read_bytes()).hexdigest(),
            "a_instructions": hashlib.sha256(a_instructions.read_bytes()).hexdigest(),
            "b_instructions": hashlib.sha256(b_instructions.read_bytes()).hexdigest(),
        }
        return config, hashes

    def prepare(self, config: object, hashes: dict[str, str]) -> dict[str, object]:
        return MODULE.prepare_fresh_calibration(
            config,
            expected_dev_sha256=hashes["dev"],
            expected_dev_rows=12,
            expected_retired_map_sha256=hashes["retired"],
            expected_retired_rows=4,
            expected_unused_rows=8,
            expected_guideline_sha256=hashes["guideline"],
            expected_a_instructions_sha256=hashes["a_instructions"],
            expected_b_instructions_sha256=hashes["b_instructions"],
            calibration_rows=4,
            per_bucket=1,
        )

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_fresh_package_excludes_retired_and_separates_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_config(root)
            manifest = self.prepare(config, hashes)

            self.assertEqual(manifest["status"], "prepared_blank_not_started")
            self.assertEqual(manifest["scope"]["retired_rows_excluded"], 4)
            self.assertEqual(manifest["scope"]["selected_rows"], 4)
            self.assertEqual(manifest["scope"]["reserve_rows"], 4)
            self.assertEqual(
                manifest["selection"]["selected_bucket_counts"],
                {
                    "METRIC": 1,
                    "TECH_SCHEME": 1,
                    "EQUIPMENT_MODULE": 1,
                    "REPEATED_MENTION": 1,
                },
            )
            self.assertEqual(manifest["selection"]["retired_overlap_rows"], 0)

            a_delivery = config.output_dir / "annotator_a_delivery"
            b_delivery = config.output_dir / "annotator_b_delivery"
            a_rows = self.read_csv(a_delivery / MODULE.A_SHEET_NAME)
            b_rows = self.read_csv(b_delivery / MODULE.B_SHEET_NAME)
            self.assertEqual({row["text"] for row in a_rows}, {row["text"] for row in b_rows})
            self.assertNotEqual(
                [row["text"] for row in a_rows], [row["text"] for row in b_rows]
            )
            self.assertTrue(
                all(
                    row["entities_json"] == ""
                    and row["notes"] == ""
                    and row["uncertainty_code"] == ""
                    for row in a_rows + b_rows
                )
            )
            self.assertTrue(all(row["blind_id"].startswith("P6FRESH-A-") for row in a_rows))
            self.assertTrue(all(row["blind_id"].startswith("P6FRESH-B-") for row in b_rows))

            old_texts = {
                "旧指标最大射程10公里。",
                "旧方案采用跟踪技术。",
                "旧系统包含处理模块。",
                "旧雷达连接旧雷达。",
            }
            self.assertFalse({row["text"] for row in a_rows} & old_texts)
            self.assertNotIn(b"gold-", (a_delivery / MODULE.A_SHEET_NAME).read_bytes())
            self.assertNotIn(b"relation-", (b_delivery / MODULE.B_SHEET_NAME).read_bytes())
            self.assertFalse((a_delivery / MODULE.B_SHEET_NAME).exists())
            self.assertFalse((b_delivery / MODULE.A_SHEET_NAME).exists())
            self.assertFalse((a_delivery / "coordinator_map.jsonl").exists())
            self.assertFalse((b_delivery / "coordinator_map.jsonl").exists())
            self.assertEqual(
                (a_delivery / MODULE.A_INSTRUCTIONS_NAME).read_text(encoding="utf-8"),
                "A instructions\n",
            )
            self.assertEqual(
                (b_delivery / MODULE.B_INSTRUCTIONS_NAME).read_text(encoding="utf-8"),
                "B instructions\n",
            )

    def test_rejects_unknown_retired_row_and_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_config(root, unknown_retired=True)
            with self.assertRaisesRegex(ValueError, "not a subset"):
                self.prepare(config, hashes)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_config(root)
            hashes["guideline"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "locked guideline SHA256 mismatch"):
                self.prepare(config, hashes)

    def test_rejects_existing_output_and_equal_seeds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_config(root)
            self.prepare(config, hashes)
            with self.assertRaises(FileExistsError):
                self.prepare(config, hashes)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes = self.make_config(root)
            equal_seed_config = MODULE.FreshCalibrationConfig(
                dev_jsonl=config.dev_jsonl,
                retired_map=config.retired_map,
                guideline=config.guideline,
                annotator_a_instructions=config.annotator_a_instructions,
                annotator_b_instructions=config.annotator_b_instructions,
                output_dir=config.output_dir,
                selection_seed=11,
                annotator_a_seed=12,
                annotator_b_seed=12,
            )
            with self.assertRaisesRegex(ValueError, "seeds must differ"):
                self.prepare(equal_seed_config, hashes)

    def test_balanced_selection_fails_without_bucket_capacity(self) -> None:
        records = [
            {"original_id": "x", "text": "仅有射程100公里。"},
            {"original_id": "y", "text": "另有重量20千克。"},
        ]
        with self.assertRaisesRegex(ValueError, "insufficient unused candidates"):
            MODULE.select_balanced_records(records, per_bucket=1, seed=1)


if __name__ == "__main__":
    unittest.main()
