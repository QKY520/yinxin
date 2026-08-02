from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_freeze import (  # noqa: E402
    FREEZE_STATUS,
    FREEZE_VERSION,
    P5_REUSED_STAGE_N_CONFIG_NAMES,
    PER_QUERY_REQUIRED_FIELDS,
    REQUIRED_SOURCE_PATHS,
    build_freeze_manifest,
    build_source_locks,
    validate_freeze_inputs,
    validate_freeze_manifest,
)


INPUT_PATH = (
    PROJECT_ROOT
    / "configs"
    / "full_ie_f5_freeze_20260802"
    / "freeze_inputs.json"
)


def load_inputs() -> dict:
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def fake_source_locks() -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": f"{index + 1:064x}"}
        for index, path in enumerate(sorted(REQUIRED_SOURCE_PATHS))
    ]


def build_manifest() -> dict:
    return build_freeze_manifest(load_inputs(), source_locks=fake_source_locks())


class FullIEF5FreezeTest(unittest.TestCase):
    def test_p5_reuse_keeps_legacy_row_metadata_behind_canonical_cells(self) -> None:
        self.assertEqual(
            P5_REUSED_STAGE_N_CONFIG_NAMES,
            {
                "A": "A_fixed_random_domain_test_p5_draft",
                "B": "B_knn_domain_test_p5_draft",
                "C": "C_knn_glossary_domain_test_p5_draft",
                "D": "D_knn_glossary_rag_domain_test_p5_draft",
            },
        )
        cell_ids = {cell["cell_id"] for cell in build_manifest()["run_manifest"]["cells"]}
        self.assertIn("domain:A:k5:s42", cell_ids)
        self.assertNotIn("domain_test:A_fixed_random_domain_test_p5_draft:k5:s42", cell_ids)

    def test_inputs_lock_exact_resources_reuse_and_sources(self) -> None:
        report = validate_freeze_inputs(load_inputs())
        self.assertEqual(report["resources"], 13)
        self.assertEqual(report["reused_stage_n"], 12)
        self.assertEqual(report["source_paths"], len(REQUIRED_SOURCE_PATHS))

    def test_source_lock_builder_hashes_fixed_repo_files(self) -> None:
        locks = build_source_locks(PROJECT_ROOT, REQUIRED_SOURCE_PATHS)
        self.assertEqual(len(locks), len(REQUIRED_SOURCE_PATHS))
        self.assertEqual({lock["path"] for lock in locks}, set(REQUIRED_SOURCE_PATHS))
        self.assertTrue(all(len(lock["sha256"]) == 64 for lock in locks))

    def test_manifest_freezes_literal_inventory_and_dependency_counts(self) -> None:
        manifest = build_manifest()
        report = validate_freeze_manifest(manifest)
        self.assertEqual(report["freeze_version"], FREEZE_VERSION)
        self.assertEqual(report["status"], FREEZE_STATUS)
        self.assertEqual(report["cells"], 60)
        self.assertEqual(report["domain_cells"], 30)
        self.assertEqual(report["cluener_cells"], 30)
        self.assertEqual(report["stage_n_done_cells"], 12)
        self.assertEqual(report["planned_cells"], 48)
        self.assertEqual(report["stage_n_nodes"], 48)
        self.assertEqual(report["stage_n_reused"], 12)
        self.assertEqual(report["stage_n_planned"], 36)
        self.assertEqual(report["stage_r_nodes"], 24)
        self.assertEqual(report["verification_nodes"], 24)
        self.assertEqual(report["unique_config_ids"], 60)
        self.assertEqual(report["unique_final_output_paths"], 120)
        self.assertFalse(report["model_calls_allowed"])
        self.assertFalse(report["gpu_required"])

    def test_verifier_policy_is_original_and_negative_rows_remain(self) -> None:
        manifest = build_manifest()
        verification = manifest["protocol_contract"]["verification"]
        self.assertEqual(
            verification["policy"],
            "original_atomic_valid_no_deletion_only",
        )
        self.assertFalse(verification["type_gate_enabled"])
        self.assertFalse(verification["current_positive_cove_claim_supported"])
        self.assertTrue(verification["negative_and_mixed_rows_retained"])
        self.assertAlmostEqual(
            verification["f4b_observed_drop_precision"]["E"],
            25 / 36,
        )
        self.assertAlmostEqual(
            verification["f4b_observed_drop_precision"]["E-prime"],
            25 / 38,
        )

    def test_cells_share_only_declared_source_nodes(self) -> None:
        manifest = build_manifest()
        cells = {cell["cell_id"]: cell for cell in manifest["run_manifest"]["cells"]}
        d = cells["domain:D:k5:s42"]["execution"]
        e = cells["domain:E:k5:s42"]["execution"]
        c = cells["domain:C:k5:s42"]["execution"]
        eprime = cells["domain:E-prime:k5:s42"]["execution"]
        self.assertEqual(e["stage_n_node"], d["stage_n_node"])
        self.assertEqual(e["stage_r_node"], d["stage_r_node"])
        self.assertEqual(eprime["stage_n_node"], c["stage_n_node"])
        self.assertEqual(eprime["stage_r_node"], c["stage_r_node"])
        self.assertIsNotNone(e["verification_node"])
        self.assertIsNotNone(eprime["verification_node"])

    def test_required_row_contract_matches_approved_plan(self) -> None:
        manifest = build_manifest()
        fields = manifest["protocol_contract"]["per_query_required_fields"]
        self.assertEqual(tuple(fields), PER_QUERY_REQUIRED_FIELDS)
        self.assertIn("pred_relations_stage_r", fields)
        self.assertIn("verifier_decisions", fields)
        self.assertIn("parse_failure_relation", fields)

    def test_manifest_rejects_type_gate_positive_claim_and_output_collision(self) -> None:
        type_gate = build_manifest()
        type_gate["protocol_contract"]["verification"]["type_gate_enabled"] = True
        with self.assertRaisesRegex(ValueError, "type-gated verification"):
            validate_freeze_manifest(type_gate)

        positive = build_manifest()
        positive["claim_boundary"]["positive_cove_claim"] = True
        with self.assertRaisesRegex(ValueError, "unsupported result claim"):
            validate_freeze_manifest(positive)

        collision = build_manifest()
        cells = collision["run_manifest"]["cells"]
        cells[1]["execution"]["final_per_query_path"] = cells[0]["execution"][
            "final_per_query_path"
        ]
        cells[1]["config_contract_sha256"] = cells[0]["config_contract_sha256"]
        with self.assertRaisesRegex(ValueError, "duplicate or invalid final output"):
            validate_freeze_manifest(collision)


if __name__ == "__main__":
    unittest.main()
