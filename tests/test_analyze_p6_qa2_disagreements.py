from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_p6_qa2_disagreements.py"
)
SPEC = importlib.util.spec_from_file_location("analyze_p6_qa2", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def item(start: int, end: int, entity_type: str) -> dict[str, object]:
    return {"start": start, "end": end, "type": entity_type}


class AnalyzeP6QA2DisagreementsTests(unittest.TestCase):
    def test_same_boundary_type_conflict_is_paired_first(self) -> None:
        result = MODULE.classify_disagreement(
            [item(0, 4, "EQUIPMENT")],
            [item(0, 4, "MODULE")],
        )
        self.assertEqual(len(result["pairs"]), 1)
        self.assertEqual(result["pairs"][0]["category"], "same_boundary_type_conflict")
        self.assertEqual(result["a_unmatched"], [])
        self.assertEqual(result["b_unmatched"], [])

    def test_overlap_prefers_same_type_before_cross_type(self) -> None:
        result = MODULE.classify_disagreement(
            [item(0, 8, "MODULE")],
            [item(1, 7, "TECH_SCHEME"), item(2, 8, "MODULE")],
        )
        self.assertEqual(result["pairs"][0]["category"], "overlap_boundary_conflict")
        self.assertEqual(result["pairs"][0]["b"], (2, 8, "MODULE"))
        self.assertEqual(result["b_unmatched"], [(1, 7, "TECH_SCHEME")])

    def test_overlap_with_different_type_and_unmatched_are_separate(self) -> None:
        result = MODULE.classify_disagreement(
            [item(0, 5, "EQUIPMENT"), item(20, 24, "MODULE")],
            [item(2, 6, "TECH_SCHEME"), item(30, 34, "MODULE")],
        )
        self.assertEqual(
            result["pairs"][0]["category"], "overlap_boundary_and_type_conflict"
        )
        self.assertEqual(result["a_unmatched"], [(20, 24, "MODULE")])
        self.assertEqual(result["b_unmatched"], [(30, 34, "MODULE")])

    def test_rejects_invalid_entity_offsets(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid disagreement entity"):
            MODULE.classify_disagreement(
                [item(4, 4, "MODULE")],
                [],
            )


if __name__ == "__main__":
    unittest.main()
