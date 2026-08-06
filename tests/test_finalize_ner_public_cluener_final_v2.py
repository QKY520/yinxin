from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "finalize_ner_public_cluener_final_v2.py"
)
SPEC = importlib.util.spec_from_file_location("finalize_ner_public_cluener_final_v2", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FinalizeNerPublicCluenerV2Tests(unittest.TestCase):
    def test_normalize_json_value_converts_duplicate_key_tuple(self) -> None:
        flag = {
            "kind": "ENTITY_DROPPED_INVALID_UNIT",
            "duplicate_key": (9, 12, "scene"),
        }
        self.assertEqual(
            MODULE.normalize_json_value(flag),
            {
                "kind": "ENTITY_DROPPED_INVALID_UNIT",
                "duplicate_key": [9, 12, "scene"],
            },
        )

    def test_single_attempt_matches_json_normalized_flags(self) -> None:
        reparsed = [{"kind": "ENTITY_DROPPED_INVALID_UNIT", "duplicate_key": (9, 12, "scene")}]
        recorded = [{"kind": "ENTITY_DROPPED_INVALID_UNIT", "duplicate_key": [9, 12, "scene"]}]
        self.assertTrue(MODULE.sanitizer_events_match(reparsed, recorded, 1))

    def test_retry_matches_only_final_attempt_suffix(self) -> None:
        reparsed = [{"kind": "ENTITY_DROPPED_OVERLAP", "entity_raw_index": 2}]
        recorded = [
            {"kind": "ENTITY_DROPPED_INVALID_UNIT", "entity_raw_index": 0},
            {"kind": "ENTITY_DROPPED_OVERLAP", "entity_raw_index": 2},
        ]
        self.assertTrue(MODULE.sanitizer_events_match(reparsed, recorded, 2))


if __name__ == "__main__":
    unittest.main()
