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
    / "prepare_p6_qa1r_calibration.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_p6_qa1r_calibration", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PrepareP6QA1RCalibrationTests(unittest.TestCase):
    def make_dev(self, path: Path) -> list[dict[str, object]]:
        texts = [
            "甲雷达最大探测距离100公里。",
            "乙平台采用脉冲压缩技术。",
            "丙系统包含信号处理模块。",
            "丁雷达工作，丁雷达停机。",
            "戊装置重量20千克。",
            "己平台采用导航算法。",
            "庚系统安装通信单元。",
            "辛天线连接辛天线控制器。",
        ]
        rows = [
            {
                "id": f"dev-{index}",
                "text": text,
                "entities": [{"secret": f"gold-{index}"}],
                "relations": [{"secret": f"relation-{index}"}],
            }
            for index, text in enumerate(texts, start=1)
        ]
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return rows

    def test_text_bucket_detection(self) -> None:
        self.assertIn("METRIC", MODULE.text_buckets("最大射程100公里"))
        self.assertIn("TECH_SCHEME", MODULE.text_buckets("采用脉冲压缩技术"))
        self.assertIn("EQUIPMENT_MODULE", MODULE.text_buckets("信号处理模块"))
        self.assertIn("REPEATED_MENTION", MODULE.text_buckets("雷达连接雷达"))

    def test_package_strips_existing_labels_and_blinds_orders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dev_path = root / "data" / "dev.jsonl"
            dev_path.parent.mkdir()
            self.make_dev(dev_path)
            digest = hashlib.sha256(dev_path.read_bytes()).hexdigest()
            config = MODULE.CalibrationConfig(
                dev_jsonl=dev_path,
                output_dir=root / "backup" / "calibration",
                selection_seed=1,
                annotator_a_seed=2,
                annotator_b_seed=3,
            )
            manifest = MODULE.prepare_calibration(
                config,
                expected_dev_sha256=digest,
                expected_dev_rows=8,
                calibration_rows=8,
            )
            self.assertEqual(manifest["status"], "prepared_not_annotated")
            self.assertFalse(manifest["scope"]["existing_dev_labels_exported"])
            a_bytes = (config.output_dir / "annotator_a_calibration.csv").read_bytes()
            b_bytes = (config.output_dir / "annotator_b_calibration.csv").read_bytes()
            self.assertNotIn(b"gold-", a_bytes)
            self.assertNotIn(b"relation-", a_bytes)
            self.assertNotIn(b"gold-", b_bytes)
            with (config.output_dir / "annotator_a_calibration.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                a_rows = list(csv.DictReader(handle))
            with (config.output_dir / "annotator_b_calibration.csv").open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                b_rows = list(csv.DictReader(handle))
            self.assertTrue(all(row["entities_json"] == "" for row in a_rows + b_rows))
            self.assertNotEqual(
                [row["text"] for row in a_rows], [row["text"] for row in b_rows]
            )

    def test_rejects_hash_mismatch_and_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dev_path = root / "data" / "dev.jsonl"
            dev_path.parent.mkdir()
            self.make_dev(dev_path)
            config = MODULE.CalibrationConfig(
                dev_jsonl=dev_path,
                output_dir=root / "backup" / "calibration",
            )
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                MODULE.prepare_calibration(
                    config,
                    expected_dev_sha256="0" * 64,
                    expected_dev_rows=8,
                    calibration_rows=4,
                )
            digest = hashlib.sha256(dev_path.read_bytes()).hexdigest()
            MODULE.prepare_calibration(
                config,
                expected_dev_sha256=digest,
                expected_dev_rows=8,
                calibration_rows=4,
            )
            with self.assertRaises(FileExistsError):
                MODULE.prepare_calibration(
                    config,
                    expected_dev_sha256=digest,
                    expected_dev_rows=8,
                    calibration_rows=4,
                )


if __name__ == "__main__":
    unittest.main()
