import json
import tempfile
import unittest
from pathlib import Path


from equipment_ie.full_ie_freeze import sha256_file
from scripts.finalize_full_ie_f7_batch_v2 import (
    EXPECTED_BATCH_REPORT_PATH,
    finalize_batch_v2,
)
from scripts.prepare_full_ie_f7 import CELL_ORDER


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class FullIEF7BatchV2Test(unittest.TestCase):
    def test_string_summary_paths_are_hashed_as_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cells = {}
            expected_hashes = {}
            for index, cell_id in enumerate(CELL_ORDER):
                per_query = root / f"cell_{index}.jsonl"
                per_query.write_text("{}\n", encoding="utf-8")
                summary_path = root / f"cell_{index}_summary.json"
                summary = {
                    "status": "COMPLETE",
                    "cell_id": cell_id,
                    "rows": 170,
                    "per_query_sha256": sha256_file(per_query),
                    "entity_micro": {"f1": float(index)},
                    "relation": {"exact_relation_micro": {"f1": 0.0}},
                    "audit": {"parse_failures_relation": index},
                }
                write_json(summary_path, summary)
                expected_hashes[cell_id] = sha256_file(summary_path)
                cells[cell_id] = {
                    "cell": {
                        "cell_id": cell_id,
                        "final_per_query_path": str(per_query),
                        "final_summary_path": str(summary_path),
                    }
                }
            batch_path = Path(EXPECTED_BATCH_REPORT_PATH)
            context = {
                "manifest": {
                    "batch_report_path": str(batch_path),
                    "batch_id": "synthetic-f7-batch",
                },
                "manifest_sha256": "execution-hash",
                "cells": cells,
            }
            original_expected = EXPECTED_BATCH_REPORT_PATH
            try:
                import scripts.finalize_full_ie_f7_batch_v2 as module

                module.EXPECTED_BATCH_REPORT_PATH = str(root / "batch.json")
                context["manifest"]["batch_report_path"] = module.EXPECTED_BATCH_REPORT_PATH
                report = finalize_batch_v2(
                    context,
                    repair_manifest_sha256="repair-hash",
                    v1_failure_log_path="failed.log",
                )
                self.assertEqual(report["status"], "COMPLETE")
                self.assertEqual(report["matrix_after"], "4/60")
                self.assertEqual(
                    {item["cell_id"]: item["final_summary_sha256"] for item in report["cells"]},
                    expected_hashes,
                )
                with self.assertRaises(FileExistsError):
                    finalize_batch_v2(
                        context,
                        repair_manifest_sha256="repair-hash",
                        v1_failure_log_path="failed.log",
                    )
            finally:
                module.EXPECTED_BATCH_REPORT_PATH = original_expected


if __name__ == "__main__":
    unittest.main()
