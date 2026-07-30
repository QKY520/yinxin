from __future__ import annotations

import unittest

from scripts.analyze_m2_zero_shot_baseline import analyze_rows


def record(record_id: str, entities: list[dict]) -> dict:
    return {"id": record_id, "text": "AB", "entities": entities, "relations": []}


class AnalyzeM2ZeroShotBaselineTest(unittest.TestCase):
    def test_analyze_rows_recomputes_metrics_and_attempts(self) -> None:
        rows = []
        for index in range(50):
            entity = {"start": 0, "end": 1, "type": "EQUIPMENT", "span": "A"}
            gold = record(f"q{index}", [entity] if index == 0 else [])
            prediction = record(f"q{index}", [entity] if index in (0, 1) else [])
            attempts = [
                {
                    "request_hash": f"{index:064x}",
                    "cache_hit": False,
                    "parse_error": "parse error" if index == 0 else None,
                }
            ]
            if index == 0:
                attempts.append(
                    {
                        "request_hash": f"{index + 100:064x}",
                        "cache_hit": False,
                        "parse_error": None,
                    }
                )
            rows.append(
                {
                    "id": f"q{index}",
                    "dataset": "domain_dev50",
                    "k": 0,
                    "gold": gold,
                    "pred_raw": prediction,
                    "pred_verified": None,
                    "parse_failure": False,
                    "example_ids": [],
                    "glossary_terms": [],
                    "rag_passage_ids": [],
                    "rag_passages": [],
                    "attempts": attempts,
                    "sanitization_flags": [],
                }
            )

        result = analyze_rows(rows)
        overall = result["metrics"]["entity_micro"]
        self.assertEqual((overall["tp"], overall["fp"], overall["fn"]), (1, 1, 0))
        self.assertEqual(result["requests"]["total_attempts"], 51)
        self.assertEqual(result["requests"]["rows_retried"], 1)
        self.assertEqual(result["requests"]["initial_parse_failures"], 1)
        self.assertEqual(result["requests"]["final_parse_failures"], 0)


if __name__ == "__main__":
    unittest.main()
