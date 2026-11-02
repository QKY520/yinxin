from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_m1_paired_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("analyze_m1_paired_evidence", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class AnalyzeM1PairedEvidenceTests(unittest.TestCase):
    def test_micro_counts_use_exact_span_and_type(self) -> None:
        gold = {(0, 4, "EQUIPMENT"), (8, 12, "MODULE")}
        pred = {
            (0, 4, "EQUIPMENT"),
            (8, 12, "TECH_SCHEME"),
            (20, 24, "MODULE"),
        }
        counts = MODULE.micro_counts(gold, pred)
        self.assertEqual(counts, MODULE.Counts(tp=1, fp=2, fn=1))
        report = MODULE.metric_report(counts, passages=2)
        self.assertAlmostEqual(report["precision"], 1 / 3)
        self.assertAlmostEqual(report["recall"], 1 / 2)
        self.assertAlmostEqual(report["fdr"], 2 / 3)
        self.assertEqual(report["fp_per_passage"], 1.0)

    def test_cd_transition_accounting_is_balanced(self) -> None:
        gold = frozenset({(0, 2, "EQUIPMENT"), (4, 6, "MODULE")})
        before = frozenset({(0, 2, "EQUIPMENT"), (8, 10, "MODULE")})
        after = frozenset(
            {
                (0, 2, "EQUIPMENT"),
                (4, 6, "MODULE"),
                (12, 14, "METRIC"),
            }
        )
        result = MODULE.passage_transition(gold, before, after)
        self.assertEqual(result["tp_retained"], 1)
        self.assertEqual(result["tp_lost"], 0)
        self.assertEqual(result["tp_gained"], 1)
        self.assertEqual(result["fp_removed"], 1)
        self.assertEqual(result["fp_introduced"], 1)
        self.assertEqual(result["changed_passages"], 1)

    def test_bootstrap_is_paired_deterministic_and_zero_for_identical_runs(self) -> None:
        configs = ("A", "B")
        seeds = (1, 2)
        contrasts = (("B-A", "A", "B"),)
        vector = [MODULE.Counts(1, 0, 0), MODULE.Counts(0, 1, 1)]
        counts_by_run = {
            (config, seed): list(vector) for config in configs for seed in seeds
        }
        first = MODULE.paired_bootstrap(
            counts_by_run,
            2,
            configs=configs,
            seeds=seeds,
            contrasts=contrasts,
            replicates=50,
            random_seed=7,
        )
        second = MODULE.paired_bootstrap(
            counts_by_run,
            2,
            configs=configs,
            seeds=seeds,
            contrasts=contrasts,
            replicates=50,
            random_seed=7,
        )
        self.assertEqual(first, second)
        self.assertTrue(all(row["point_delta"] == 0 for row in first))
        self.assertTrue(all(row["ci95_lower"] == 0 for row in first))
        self.assertTrue(all(row["ci95_upper"] == 0 for row in first))

    def test_sanitizer_entity_key_accepts_normalized_and_duplicate_keys(self) -> None:
        normalized = {
            "entity": {"start": 2, "end": 5, "type": "MODULE", "span": "abc"}
        }
        duplicate = {"duplicate_key": [2, 5, "MODULE"]}
        unavailable = {"entity": {"span": "abc", "type": "MODULE", "occurrence": 9}}
        self.assertEqual(MODULE.sanitizer_entity_key(normalized), (2, 5, "MODULE"))
        self.assertEqual(MODULE.sanitizer_entity_key(duplicate), (2, 5, "MODULE"))
        self.assertIsNone(MODULE.sanitizer_entity_key(unavailable))

    def test_fixed_strata_boundaries(self) -> None:
        self.assertEqual(MODULE.text_length_bin(128), "<=128")
        self.assertEqual(MODULE.text_length_bin(129), "129-256")
        self.assertEqual(MODULE.text_length_bin(257), ">256")
        self.assertEqual(MODULE.gold_count_bin(0), "0")
        self.assertEqual(MODULE.gold_count_bin(4), "1-4")
        self.assertEqual(MODULE.gold_count_bin(5), "5-9")
        self.assertEqual(MODULE.gold_count_bin(10), ">=10")

    def test_percentile_uses_linear_interpolation(self) -> None:
        values = [0.0, 10.0, 20.0, 30.0]
        self.assertEqual(MODULE.percentile(values, 0.0), 0.0)
        self.assertEqual(MODULE.percentile(values, 1.0), 30.0)
        self.assertAlmostEqual(MODULE.percentile(values, 0.25), 7.5)


if __name__ == "__main__":
    unittest.main()
