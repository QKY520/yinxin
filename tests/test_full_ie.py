from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import ExtractionParseError  # noqa: E402
from equipment_ie.full_ie import (  # noqa: E402
    DEFAULT_RELATION_TYPES,
    apply_atomic_verifier_decisions,
    build_relation_verification_prompt,
    build_stage_r_prompt,
    parse_atomic_verifier_answer,
    parse_stage_r_output,
    relation_evaluation_report,
    relation_micro_counts,
    stage_r_skip_reason,
    validate_approved_relation_matrix,
)
from scripts.run_p3_verification import (  # noqa: E402
    drop_entities_by_unit_decisions,
)


def make_entity(text: str, span: str, entity_type: str, occurrence: int = 1) -> dict:
    start = -1
    cursor = 0
    for _ in range(occurrence):
        start = text.index(span, cursor)
        cursor = start + 1
    return {
        "start": start,
        "end": start + len(span),
        "type": entity_type,
        "span": span,
    }


def make_record(
    record_id: str,
    text: str,
    entity_specs: list[tuple[str, str]],
    relations: list[dict] | None = None,
) -> dict:
    return {
        "id": record_id,
        "text": text,
        "entities": [
            make_entity(text, span, entity_type)
            for span, entity_type in entity_specs
        ],
        "relations": list(relations or []),
    }


class FullIECoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.query = make_record(
            "q1",
            "甲平台采用乙模块。",
            [("甲平台", "EQUIPMENT"), ("乙模块", "MODULE")],
        )
        self.example = make_record(
            "s1",
            "丙平台装有丁模块。",
            [("丙平台", "EQUIPMENT"), ("丁模块", "MODULE")],
            [{"head": 0, "tail": 1, "type": "USES"}],
        )

    def test_stage_r_prompt_has_fixed_order_and_final_instruction(self) -> None:
        prompt = build_stage_r_prompt(
            stage_n_record=self.query,
            relation_types=DEFAULT_RELATION_TYPES,
            examples=[self.example],
            glossary_entries=["模块（MODULE）"],
            rag_passages=["合成参考资料。"],
        )
        labels = [
            "任务定义",
            "Stage N实体列表",
            "关系Schema与方向",
            "领域术语表",
            "参考资料",
            "示例1实体列表",
            "待抽取文本",
            "输出格式",
        ]
        positions = [prompt.index(label) for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(prompt.endswith("只返回JSON,不要任何解释,不要markdown代码块"))

    def test_stage_r_deterministic_skip_reasons(self) -> None:
        one_entity = make_record(
            "q2",
            "仅有甲平台。",
            [("甲平台", "EQUIPMENT")],
        )
        self.assertEqual(
            stage_r_skip_reason(one_entity, DEFAULT_RELATION_TYPES),
            "fewer_than_two_entities",
        )
        incompatible = make_record(
            "q3",
            "甲指标和乙指标。",
            [("甲指标", "METRIC"), ("乙指标", "METRIC")],
        )
        self.assertEqual(
            stage_r_skip_reason(incompatible, DEFAULT_RELATION_TYPES),
            "no_type_compatible_same_sentence_pair",
        )

    def test_approved_relation_matrix_rejects_direction_drift(self) -> None:
        changed = {name: dict(rule) for name, rule in DEFAULT_RELATION_TYPES.items()}
        changed["HAS_METRIC"]["head_types"] = ("METRIC",)
        with self.assertRaisesRegex(ValueError, "approved v3 direction/type matrix"):
            validate_approved_relation_matrix(changed)

    def test_stage_r_parser_deduplicates_relations_and_preserves_entities(self) -> None:
        flags: list[dict] = []
        parsed = parse_stage_r_output(
            json.dumps(
                {
                    "relations": [
                        {"head": 0, "tail": 1, "type": "USES"},
                        {"head": 0, "tail": 1, "type": "USES"},
                    ]
                }
            ),
            stage_n_record=self.query,
            relation_types=DEFAULT_RELATION_TYPES,
            sanitization_flags=flags,
        )
        self.assertEqual(parsed["entities"], self.query["entities"])
        self.assertEqual(
            parsed["relations"],
            [{"head": 0, "tail": 1, "type": "USES"}],
        )
        self.assertEqual(flags[0]["kind"], "RELATION_DROPPED_DUPLICATE")

    def test_stage_r_parser_rejects_direction_error(self) -> None:
        metric_record = make_record(
            "q4",
            "甲平台最大速度为乙指标。",
            [("甲平台", "EQUIPMENT"), ("乙指标", "METRIC")],
        )
        with self.assertRaisesRegex(ExtractionParseError, "directed type matrix"):
            parse_stage_r_output(
                '{"relations":[{"head":1,"tail":0,"type":"HAS_METRIC"}]}',
                stage_n_record=metric_record,
                relation_types=DEFAULT_RELATION_TYPES,
            )

    def test_stage_r_parser_handles_illegal_triples(self) -> None:
        cross_sentence = make_record(
            "q5",
            "甲平台工作。乙模块启动。",
            [("甲平台", "EQUIPMENT"), ("乙模块", "MODULE")],
        )
        invalid_outputs = [
            (self.query, '{"relations":[{"head":0,"tail":9,"type":"USES"}]}'),
            (self.query, '{"relations":[{"head":0,"tail":1,"type":"UNKNOWN"}]}'),
            (self.query, '{"relations":[{"head":0,"tail":1,"type":[]}]}'),
            (self.query, '{"relations":[{"head":0,"tail":0,"type":"USES"}]}'),
            (
                cross_sentence,
                '{"relations":[{"head":0,"tail":1,"type":"USES"}]}',
            ),
        ]
        for record, raw_output in invalid_outputs:
            with self.subTest(raw_output=raw_output):
                with self.assertRaises(ExtractionParseError):
                    parse_stage_r_output(
                        raw_output,
                        stage_n_record=record,
                        relation_types=DEFAULT_RELATION_TYPES,
                    )
                flags: list[dict] = []
                parsed = parse_stage_r_output(
                    raw_output,
                    stage_n_record=record,
                    relation_types=DEFAULT_RELATION_TYPES,
                    drop_invalid_relations=True,
                    sanitization_flags=flags,
                )
                self.assertEqual(parsed["relations"], [])
                self.assertEqual(flags[0]["kind"], "RELATION_DROPPED_INVALID_UNIT")

    def test_exact_relation_metric_counts_reversed_direction_as_fp_and_fn(self) -> None:
        gold = dict(self.query)
        gold["relations"] = [{"head": 0, "tail": 1, "type": "USES"}]
        pred = dict(self.query)
        pred["relations"] = [{"head": 1, "tail": 0, "type": "USES"}]
        counts = relation_micro_counts([gold], [pred])
        self.assertEqual(
            (counts.true_positive, counts.false_positive, counts.false_negative),
            (0, 1, 1),
        )

    def test_conditional_relation_metric_excludes_false_entity_endpoints(self) -> None:
        text = "甲平台使用乙模块和丙模块。"
        gold = make_record(
            "q6",
            text,
            [("甲平台", "EQUIPMENT"), ("乙模块", "MODULE")],
            [{"head": 0, "tail": 1, "type": "USES"}],
        )
        pred = make_record(
            "q6",
            text,
            [
                ("甲平台", "EQUIPMENT"),
                ("乙模块", "MODULE"),
                ("丙模块", "MODULE"),
            ],
            [
                {"head": 0, "tail": 1, "type": "USES"},
                {"head": 0, "tail": 2, "type": "USES"},
            ],
        )
        report = relation_evaluation_report([gold], [pred])
        self.assertEqual(report["exact_relation_micro"]["fp"], 1)
        self.assertEqual(
            report["conditional_on_covered_gold_endpoints"]["fp"],
            0,
        )
        self.assertEqual(report["gold_endpoint_coverage"]["rate"], 1.0)

    def test_invalid_verifier_output_keeps_atom_and_entity_drop_cascades(self) -> None:
        pred = make_record(
            "q7",
            "甲平台含乙模块和丙模块。",
            [
                ("甲平台", "EQUIPMENT"),
                ("乙模块", "MODULE"),
                ("丙模块", "MODULE"),
            ],
            [
                {"head": 0, "tail": 1, "type": "USES"},
                {"head": 1, "tail": 2, "type": "USES"},
            ],
        )
        decisions = [
            {"unit_kind": "entity", "unit_index": 0, "decision": "yes", "valid_answer": True},
            {"unit_kind": "entity", "unit_index": 1, "decision": "no", "valid_answer": True},
            {"unit_kind": "entity", "unit_index": 2, "decision": "invalid", "valid_answer": False},
            {"unit_kind": "relation", "unit_index": 0, "decision": "no", "valid_answer": True},
            {"unit_kind": "relation", "unit_index": 1, "decision": "yes", "valid_answer": True},
        ]
        result = apply_atomic_verifier_decisions(pred, decisions=decisions)
        self.assertEqual(result.dropped_entity_indices, (1,))
        self.assertEqual(result.dropped_relation_indices, (0,))
        self.assertEqual(result.cascade_dropped_relation_indices, (0, 1))
        self.assertEqual(result.invalid_decisions, 1)
        self.assertEqual([entity["span"] for entity in result.record["entities"]], ["甲平台", "丙模块"])
        self.assertEqual(result.record["relations"], [])

    def test_entity_drop_remaps_surviving_relation_indices(self) -> None:
        pred = make_record(
            "q8",
            "甲平台、乙模块和丙模块。",
            [
                ("甲平台", "EQUIPMENT"),
                ("乙模块", "MODULE"),
                ("丙模块", "MODULE"),
            ],
            [{"head": 0, "tail": 2, "type": "USES"}],
        )
        result = apply_atomic_verifier_decisions(
            pred,
            decisions=[
                {
                    "unit_kind": "entity",
                    "unit_index": 1,
                    "decision": "no",
                    "valid_answer": True,
                }
            ],
        )
        self.assertEqual(
            result.record["relations"],
            [{"head": 0, "tail": 1, "type": "USES"}],
        )

    def test_relation_verifier_is_direction_explicit(self) -> None:
        pred = dict(self.query)
        pred["relations"] = [{"head": 0, "tail": 1, "type": "USES"}]
        prompt = build_relation_verification_prompt(
            record=pred,
            relation_index=0,
            relation_types=DEFAULT_RELATION_TYPES,
            evidence_passages=[],
        )
        self.assertIn("有向关系", prompt)
        self.assertIn("head=", prompt)
        self.assertIn("-> USES -> tail=", prompt)
        self.assertIn("同一句", prompt)

    def test_invalid_verifier_answers_are_conservative(self) -> None:
        self.assertEqual(parse_atomic_verifier_answer("yes"), "yes")
        self.assertEqual(parse_atomic_verifier_answer("否。"), "no")
        self.assertEqual(parse_atomic_verifier_answer("maybe"), "invalid")

    def test_legacy_ner_only_entity_deletion_is_compatible(self) -> None:
        pred = self.query
        old_decisions = [
            {"entity_index": 0, "decision": "yes", "valid_answer": True},
            {"entity_index": 1, "decision": "no", "valid_answer": True},
        ]
        legacy = drop_entities_by_unit_decisions(pred, decisions=old_decisions)
        full_ie_decisions = [
            {
                **decision,
                "unit_kind": "entity",
                "unit_index": decision["entity_index"],
            }
            for decision in old_decisions
        ]
        current = apply_atomic_verifier_decisions(
            pred,
            decisions=full_ie_decisions,
        ).record
        self.assertEqual(current, legacy)


if __name__ == "__main__":
    unittest.main()
