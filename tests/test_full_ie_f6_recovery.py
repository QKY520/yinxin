from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.run_full_ie_f6_cluener_recovery import (
    RECOVERY_GATE,
    RECOVERY_VERSION,
    validate_guard,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = PROJECT_ROOT / "configs/full_ie_f6_cluener_recovery_20260803/recovery_guard.json"


class FullIEF6RecoveryGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guard = json.loads(GUARD_PATH.read_text(encoding="utf-8"))

    def test_guard_validates_locked_base_and_sources(self) -> None:
        base, base_path = validate_guard(
            self.guard,
            guard_path=GUARD_PATH,
            repo_root=PROJECT_ROOT,
        )
        self.assertEqual(self.guard["version"], RECOVERY_VERSION)
        self.assertEqual(self.guard["human_gate"], RECOVERY_GATE)
        self.assertEqual(base_path.name, "replay_inputs.json")
        self.assertEqual(base["resources"]["cluener_query"]["rows"], 1343)

    def test_guard_rejects_price_or_scope_changes(self) -> None:
        altered = copy.deepcopy(self.guard)
        altered["gpu"]["hourly_price_cny"] = 2.7
        with self.assertRaisesRegex(ValueError, "GPU recovery guard"):
            validate_guard(altered, guard_path=GUARD_PATH, repo_root=PROJECT_ROOT)

    def test_guard_forbids_model_and_later_phase_actions(self) -> None:
        forbidden = self.guard["forbidden"]
        self.assertTrue(all(forbidden.values()))
        self.assertFalse(self.guard["gpu"]["execution_allowed"])
        self.assertEqual(self.guard["retrieval"]["device"], "cpu")
        self.assertFalse(self.guard["retrieval"]["use_fp16"])


if __name__ == "__main__":
    unittest.main()
