from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_p6_qa1r_calibration_reconciliation.py"
)
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location(
    "analyze_p6_qa1r_calibration_reconciliation", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AnalyzeP6QA1RCalibrationReconciliationTests(unittest.TestCase):
    def test_exact_entities_produce_no_events(self) -> None:
        entities = {(0, 2, "EQUIPMENT")}
        result = MODULE.classify_row("雷达工作", entities, set(entities))
        self.assertEqual(len(result["exact"]), 1)
        self.assertEqual(result["events"], [])

    def test_same_boundary_type_conflict_routes_to_type_policy(self) -> None:
        result = MODULE.classify_row(
            "雷达工作",
            {(0, 2, "EQUIPMENT")},
            {(0, 2, "MODULE")},
        )
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["events"][0]["category"], "same_boundary_type_conflict")
        self.assertEqual(result["events"][0]["rule_signal"], "TYPE_POLICY")

    def test_overlap_same_type_routes_to_boundary_policy(self) -> None:
        result = MODULE.classify_row(
            "先进雷达系统工作",
            {(0, 6, "EQUIPMENT")},
            {(2, 6, "EQUIPMENT")},
        )
        self.assertEqual(result["events"][0]["category"], "overlap_boundary_conflict")
        self.assertEqual(result["events"][0]["rule_signal"], "BOUNDARY_POLICY")

    def test_missing_second_occurrence_is_repeated_mention_candidate(self) -> None:
        text = "雷达启动，雷达停止"
        result = MODULE.classify_row(
            text,
            {(0, 2, "EQUIPMENT"), (5, 7, "EQUIPMENT")},
            {(0, 2, "EQUIPMENT")},
        )
        self.assertEqual(
            result["events"][0]["category"],
            "a_only_repeated_mention_candidate",
        )
        self.assertEqual(result["events"][0]["rule_signal"], "REPEATED_MENTION")

    def test_single_unmatched_entity_routes_to_scope_policy(self) -> None:
        result = MODULE.classify_row(
            "雷达启动",
            {(0, 2, "EQUIPMENT")},
            set(),
        )
        self.assertEqual(result["events"][0]["category"], "a_unmatched")
        self.assertEqual(result["events"][0]["rule_signal"], "SCOPE_POLICY")

    def test_classification_does_not_mutate_input_sets(self) -> None:
        a_entities = {(0, 2, "EQUIPMENT"), (5, 7, "EQUIPMENT")}
        b_entities = {(0, 2, "EQUIPMENT")}
        before_a = set(a_entities)
        before_b = set(b_entities)
        MODULE.classify_row("雷达启动，雷达停止", a_entities, b_entities)
        self.assertEqual(a_entities, before_a)
        self.assertEqual(b_entities, before_b)


if __name__ == "__main__":
    unittest.main()
