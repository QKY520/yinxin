from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_manifest import (  # noqa: E402
    aggregate_manifest_metrics,
    build_planned_manifest,
    expected_full_ie_cells,
    validate_full_ie_manifest,
)
from scripts.validate_full_ie_manifest import main as manifest_main  # noqa: E402


def metric_block(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def complete_manifest() -> dict:
    manifest = build_planned_manifest()
    for cell in manifest["cells"]:
        cell["status"] = "DONE"
        cell["stage_n"] = {"status": "DONE", "artifact_sha256": "a" * 64}
        if cell["dataset"] == "domain":
            cell["stage_r"] = {"status": "DONE", "artifact_sha256": "b" * 64}
        tp = int(cell["seed"]) - 41
        cell["metrics"] = {
            "entity": metric_block(tp, 1, 0),
            "relation": metric_block(tp, 0, 1)
            if cell["dataset"] == "domain"
            else None,
        }
    return manifest


class FullIEManifestTest(unittest.TestCase):
    def test_expected_inventory_is_literal_30_plus_30(self) -> None:
        cells = expected_full_ie_cells()
        self.assertEqual(len(cells), 60)
        self.assertEqual(len({cell["cell_id"] for cell in cells}), 60)
        self.assertEqual(sum(cell["dataset"] == "domain" for cell in cells), 30)
        self.assertEqual(sum(cell["dataset"] == "cluener" for cell in cells), 30)

    def test_planned_manifest_validates(self) -> None:
        report = validate_full_ie_manifest(build_planned_manifest())
        self.assertEqual(report["cells"], 60)
        self.assertEqual(report["status_counts"], {"PLANNED": 60})
        self.assertFalse(report["complete"])

    def test_existing_12_domain_stage_n_cells_are_partial_only(self) -> None:
        manifest = build_planned_manifest()
        for cell in manifest["cells"]:
            if (
                cell["dataset"] == "domain"
                and cell["config"] in {"A", "B", "C", "D"}
                and cell["k"] == 5
            ):
                cell["status"] = "STAGE_N_DONE"
                cell["stage_n"] = {
                    "status": "DONE",
                    "artifact_sha256": "c" * 64,
                }
        report = validate_full_ie_manifest(manifest)
        self.assertEqual(report["status_counts"]["STAGE_N_DONE"], 12)
        self.assertEqual(report["status_counts"]["PLANNED"], 48)
        self.assertFalse(report["complete"])

    def test_manifest_rejects_missing_and_duplicate_cells(self) -> None:
        missing = build_planned_manifest()
        missing["cells"].pop()
        with self.assertRaisesRegex(ValueError, "missing 1 fixed cells"):
            validate_full_ie_manifest(missing)

        duplicate = build_planned_manifest()
        duplicate["cells"].append(copy.deepcopy(duplicate["cells"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate cell"):
            validate_full_ie_manifest(duplicate)

    def test_manifest_rejects_inconsistent_status_and_bad_hash(self) -> None:
        manifest = build_planned_manifest()
        cell = manifest["cells"][0]
        cell["status"] = "STAGE_N_DONE"
        cell["stage_n"] = {"status": "DONE", "artifact_sha256": "not-a-hash"}
        with self.assertRaisesRegex(ValueError, "lowercase SHA256"):
            validate_full_ie_manifest(manifest)

        blocked = build_planned_manifest()
        blocked["cells"][0]["status"] = "BLOCKED"
        with self.assertRaisesRegex(ValueError, "requires a blocked stage"):
            validate_full_ie_manifest(blocked)

    def test_complete_manifest_metrics_recompute_and_aggregate(self) -> None:
        manifest = complete_manifest()
        report = validate_full_ie_manifest(manifest, require_complete=True)
        self.assertTrue(report["complete"])
        aggregates = aggregate_manifest_metrics(manifest)
        self.assertEqual(len(aggregates), 20)
        self.assertEqual(aggregates[0]["seeds"], [42, 43, 44])
        self.assertEqual(aggregates[0]["metrics"]["entity"]["tp"]["sd"], 1.0)

    def test_manifest_rejects_metric_not_recomputed_from_counts(self) -> None:
        manifest = complete_manifest()
        manifest["cells"][0]["metrics"]["entity"]["f1"] = 0.123
        with self.assertRaisesRegex(ValueError, "does not recompute"):
            validate_full_ie_manifest(manifest, require_complete=True)

    def test_cli_writes_and_validates_planned_template(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            report_path = root / "report.json"
            original_argv = sys.argv
            try:
                sys.argv = [
                    "validate_full_ie_manifest.py",
                    "--write-planned",
                    str(manifest_path),
                    "--report-output",
                    str(report_path),
                ]
                self.assertEqual(manifest_main(), 0)
            finally:
                sys.argv = original_argv
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(len(saved["cells"]), 60)
            self.assertEqual(report["domain_cells"], 30)


if __name__ == "__main__":
    unittest.main()
