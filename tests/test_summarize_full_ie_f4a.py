from __future__ import annotations

import unittest

from scripts.summarize_full_ie_f4a import (
    assert_metric_tree_matches,
    audit_statistics,
    build_drop_audit,
    recompute_reports,
    select_even_sample,
)


def record(record_id: str, entities: list[dict], relations: list[dict]) -> dict:
    return {
        "id": record_id,
        "text": "radar uses missile module",
        "entities": entities,
        "relations": relations,
    }


class FullIEF4aSummaryTest(unittest.TestCase):
    def test_drop_audit_scores_entities_relations_and_cascade(self) -> None:
        radar = {"start": 0, "end": 5, "type": "EQUIPMENT", "span": "radar"}
        missile = {"start": 11, "end": 18, "type": "EQUIPMENT", "span": "missile"}
        module = {"start": 19, "end": 25, "type": "MODULE", "span": "module"}
        gold = record("q1", [radar, missile], [{"head": 0, "tail": 1, "type": "USES"}])
        pred = record(
            "q1",
            [radar, missile, module],
            [
                {"head": 0, "tail": 1, "type": "USES"},
                {"head": 1, "tail": 0, "type": "USES"},
                {"head": 2, "tail": 0, "type": "USES"},
            ],
        )
        decisions = [
            {"unit_kind": "entity", "unit_index": 0, "decision": "no", "valid_answer": True},
            {"unit_kind": "entity", "unit_index": 2, "decision": "no", "valid_answer": True},
            {"unit_kind": "relation", "unit_index": 0, "decision": "no", "valid_answer": True},
            {"unit_kind": "relation", "unit_index": 1, "decision": "no", "valid_answer": True},
        ]
        rows = [
            {
                "id": "q1",
                "gold": gold,
                "pred_raw": pred,
                "verifier_decisions": decisions,
                "verifier_cascade_dropped_relation_indices": [2],
            }
        ]

        audit = build_drop_audit(rows, "E-prime")
        self.assertEqual(len(audit), 5)
        entity_rows = [row for row in audit if row["unit_class"] == "entity"]
        relation_rows = [row for row in audit if row["unit_class"] == "relation"]
        self.assertEqual([row["correct_drop"] for row in entity_rows], [False, True])
        self.assertEqual([row["correct_drop"] for row in relation_rows], [False, True, True])
        self.assertEqual(relation_rows[-1]["drop_mode"], "entity_cascade")

    def test_statistics_and_even_sample(self) -> None:
        audit = [
            {
                "config": "E-prime",
                "unit_class": "entity",
                "drop_mode": "verifier_no",
                "correct_drop": value,
            }
            for value in (True, True, True, False)
        ]
        stats = audit_statistics(audit)
        self.assertEqual(stats["E-prime"]["entity"]["correct_drop_rate"], 0.75)
        self.assertTrue(stats["E-prime"]["entity"]["passes_70_percent"])
        self.assertEqual(select_even_sample(list(range(10)), 3), [0, 4, 9])

    def test_recomputes_entity_and_exact_directed_relation_metrics(self) -> None:
        radar = {"start": 0, "end": 5, "type": "EQUIPMENT", "span": "radar"}
        missile = {"start": 11, "end": 18, "type": "EQUIPMENT", "span": "missile"}
        gold = record("q1", [radar, missile], [{"head": 0, "tail": 1, "type": "USES"}])
        pred = record("q1", [radar, missile], [{"head": 1, "tail": 0, "type": "USES"}])
        entity, relation = recompute_reports(
            [{"gold": gold, "pred_raw": pred}],
            prediction_field="pred_raw",
            include_relations=True,
        )
        self.assertEqual(entity["f1"], 1.0)
        self.assertEqual(relation["exact_relation_micro"]["tp"], 0)
        self.assertEqual(relation["exact_relation_micro"]["fp"], 1)
        self.assertEqual(relation["exact_relation_micro"]["fn"], 1)

    def test_summary_metric_mismatch_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "recomputed"):
            assert_metric_tree_matches(
                {"tp": 1, "f1": 1.0},
                {"tp": 0, "f1": 0.0},
                label="synthetic",
            )

    def test_duplicate_verifier_decision_fails(self) -> None:
        radar = {"start": 0, "end": 5, "type": "EQUIPMENT", "span": "radar"}
        gold = record("q1", [radar], [])
        decision = {
            "unit_kind": "entity",
            "unit_index": 0,
            "decision": "no",
            "valid_answer": True,
        }
        rows = [
            {
                "id": "q1",
                "gold": gold,
                "pred_raw": gold,
                "verifier_decisions": [decision, decision],
                "verifier_cascade_dropped_relation_indices": [],
            }
        ]
        with self.assertRaisesRegex(ValueError, "duplicate verifier decision"):
            build_drop_audit(rows, "E-prime")


if __name__ == "__main__":
    unittest.main()
