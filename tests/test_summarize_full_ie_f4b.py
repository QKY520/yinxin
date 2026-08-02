from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import summarize_full_ie_f4b as module
from equipment_ie.llm_labeling import request_hash, sha256_text


def record(record_id: str, entities: list[dict]) -> dict:
    return {
        "id": record_id,
        "text": "abcd",
        "entities": entities,
        "relations": [],
    }


def entity(start: int, end: int, entity_type: str) -> dict:
    return {
        "start": start,
        "end": end,
        "type": entity_type,
        "span": "abcd"[start:end],
    }


class FullIEF4bSummaryTest(unittest.TestCase):
    def test_nearest_rank_percentile(self) -> None:
        self.assertEqual(module.nearest_rank_percentile([1, 2, 3, 4], 0.5), 2)
        self.assertEqual(module.nearest_rank_percentile([4, 1, 3, 2], 0.95), 4)
        with self.assertRaises(ValueError):
            module.nearest_rank_percentile([], 0.95)

    def test_drop_statistics_uses_exact_gold_membership(self) -> None:
        rows = [
            {
                "id": "q1",
                "source_config": "C",
                "gold": record("q1", [entity(0, 1, "name")]),
                "pred_raw": record(
                    "q1", [entity(0, 1, "name"), entity(1, 2, "company")]
                ),
                "verifier_decisions": [
                    {
                        "unit_index": 0,
                        "decision": "no",
                        "valid_answer": True,
                    },
                    {
                        "unit_index": 1,
                        "decision": "no",
                        "valid_answer": True,
                    },
                ],
            }
        ]
        audit = module.build_entity_drop_audit(rows, config="E-prime")
        self.assertEqual([item["correct_drop"] for item in audit], [False, True])
        self.assertEqual(module.drop_statistics(audit)["correct_drop_rate"], 0.5)

    def test_verified_contract_drops_only_valid_no(self) -> None:
        raw = record(
            "q1",
            [
                entity(0, 1, "name"),
                entity(1, 2, "company"),
                entity(2, 3, "scene"),
            ],
        )
        decisions = [
            {
                "unit_kind": "entity",
                "unit_index": 0,
                "decision": "no",
                "valid_answer": True,
                "evidence_mode": "source_text_only",
                "evidence_count": 0,
                "latency_ms": 1.0,
                "prompt_hash": "a",
            },
            {
                "unit_kind": "entity",
                "unit_index": 1,
                "decision": "yes",
                "valid_answer": True,
                "evidence_mode": "source_text_only",
                "evidence_count": 0,
                "latency_ms": 2.0,
                "prompt_hash": "b",
            },
            {
                "unit_kind": "entity",
                "unit_index": 2,
                "decision": None,
                "valid_answer": False,
                "evidence_mode": "source_text_only",
                "evidence_count": 0,
                "latency_ms": 3.0,
                "prompt_hash": "c",
            },
        ]
        verified = dict(raw)
        verified["entities"] = raw["entities"][1:]
        row = {
            "id": "q1",
            "pred_raw": raw,
            "pred_verified": verified,
            "verifier_decisions": decisions,
            "verifier_prompt_hashes": ["a", "b", "c"],
            "latency_verifier_ms": 6.0,
        }
        module.validate_verified_contract(
            row, evidence_mode="source_text_only", evidence_count=0
        )

    def test_verified_contract_rejects_invalid_answer_drop(self) -> None:
        raw = record("q1", [entity(0, 1, "name")])
        row = {
            "id": "q1",
            "pred_raw": raw,
            "pred_verified": record("q1", []),
            "verifier_decisions": [
                {
                    "unit_kind": "entity",
                    "unit_index": 0,
                    "decision": None,
                    "valid_answer": False,
                    "evidence_mode": "source_text_only",
                    "evidence_count": 0,
                    "latency_ms": 1.0,
                    "prompt_hash": "a",
                }
            ],
            "verifier_prompt_hashes": ["a"],
            "latency_verifier_ms": 1.0,
        }
        with self.assertRaisesRegex(ValueError, "changed more than valid-no drops"):
            module.validate_verified_contract(
                row, evidence_mode="source_text_only", evidence_count=0
            )

    def test_validate_cache_entry_checks_prompt_and_raw_response(self) -> None:
        prompt = "test prompt"
        raw = "yes"
        envelope = {
            "run_id": "test",
            "config_hash": "0" * 64,
            "payload": {
                "model": "model",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "top_p": 1.0,
                "max_tokens": 8,
                "seed": 42,
            },
        }
        digest = request_hash(envelope)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / digest[:2] / f"{digest}.json"
            path.parent.mkdir()
            path.write_text(
                json.dumps(
                    {
                        "request_hash": digest,
                        "request": envelope,
                        "content": raw,
                        "raw_output_hash": sha256_text(raw),
                        "latency_ms": 1.0,
                        "created_at": "2026-08-02T00:00:00+00:00",
                        "response": {"choices": [{"message": {"content": raw}}]},
                    }
                ),
                encoding="utf-8",
            )
            result = module.validate_cache_entry(
                cache_root=root,
                request_digest=digest,
                raw_digest=sha256_text(raw),
                expected_prompt_digest=module.prompt_hash(prompt),
                phase="verification",
            )
        self.assertEqual(result["request_hash"], digest)
        self.assertEqual(result["prompt_hash"], module.prompt_hash(prompt))


if __name__ == "__main__":
    unittest.main()
