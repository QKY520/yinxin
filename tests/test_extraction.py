from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (  # noqa: E402
    build_error_retry_prompt,
    build_ner_prompt,
    entity_micro_counts,
    parse_extraction_output,
    select_fixed_random_examples,
    select_glossary_entries,
)
from equipment_ie.llm_labeling import ChatResult  # noqa: E402
from equipment_ie.schema import iter_jsonl  # noqa: E402
from scripts.build_rag_replay_manifest import build_manifest as build_rag_replay_manifest  # noqa: E402
from scripts.build_rag_replay_manifest import (  # noqa: E402
    build_manifest_from_per_query as build_rag_replay_manifest_from_per_query,
)
from scripts.run_p3_extraction import build_rag_selector  # noqa: E402
from scripts.run_p3_extraction import main as run_main  # noqa: E402
from scripts.run_p3_extraction import run_execute  # noqa: E402
from scripts.run_p3_extraction import validate_execution_gate  # noqa: E402


def record(record_id: str, text: str, start: int, end: int, entity_type: str) -> dict:
    return {
        "id": record_id,
        "text": text,
        "entities": [
            {
                "start": start,
                "end": end,
                "type": entity_type,
                "span": text[start:end],
            }
        ],
        "relations": [],
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class ExtractionTest(unittest.TestCase):
    def test_span_index_prompt_documents_ner_only_envelopes(self) -> None:
        prompt = build_ner_prompt(
            query_text="AB", entity_types={"EQUIPMENT": "equipment"},
            examples=[], output_mode="span_index",
        )
        self.assertIn('"entities":[{"start":0,"end":2,"type":"实体类型"}]}', prompt)
        self.assertIn('"relations":[]', prompt)
        self.assertIn("禁止其它顶层字段", prompt)

    def test_prompt_order_and_output_instruction(self) -> None:
        example = record("ex1", "张三去了北京。", 0, 2, "name")
        prompt = build_ner_prompt(
            query_text="李四去了上海。",
            entity_types={"name": "人名", "address": "地点"},
            examples=[example],
        )
        self.assertLess(prompt.index("任务定义"), prompt.index("Schema"))
        self.assertLess(prompt.index("Schema"), prompt.index("示例1文本"))
        self.assertLess(prompt.index("示例1文本"), prompt.index("待抽取文本"))
        self.assertTrue(prompt.endswith("只返回JSON,不要任何解释,不要markdown代码块"))

    def test_occurrence_copy_v2_contract_is_opt_in_and_before_query(self) -> None:
        prompt = build_ner_prompt(
            query_text="雷达A：测试，雷达A：测试",
            entity_types={"EQUIPMENT": "equipment"},
            examples=[],
            output_mode="occurrence",
            occurrence_contract_version="occurrence_copy_v2",
            output_instruction="JSON_ONLY",
        )
        self.assertIn("OCCURRENCE_COPY_V2_LITERAL_CONTRACT", prompt)
        self.assertIn("character-for-character", prompt)
        self.assertIn("occurrence 1 and 2", prompt)
        self.assertLess(
            prompt.index("OCCURRENCE_COPY_V2_LITERAL_CONTRACT"),
            prompt.index("雷达A：测试，雷达A：测试"),
        )
        self.assertTrue(prompt.endswith("JSON_ONLY"))

        legacy = build_ner_prompt(
            query_text="AB",
            entity_types={"EQUIPMENT": "equipment"},
            examples=[],
            output_mode="occurrence",
            output_instruction="JSON_ONLY",
        )
        self.assertNotIn("OCCURRENCE_COPY_V2_LITERAL_CONTRACT", legacy)

    def test_anchored_span_index_prompt_documents_span_echo_contract(self) -> None:
        prompt = build_ner_prompt(
            query_text="AB/CD",
            entity_types={"EQUIPMENT": "equipment"},
            examples=[],
            output_mode="anchored_span_index",
            output_instruction="JSON_ONLY",
        )
        self.assertIn("Anchored span-index NER output", prompt)
        self.assertIn("text[start:end]", prompt)
        self.assertIn("Python Unicode character indices", prompt)
        self.assertLess(prompt.index("Anchored span-index NER output"), prompt.rfind("AB/CD"))
        self.assertTrue(prompt.endswith("JSON_ONLY"))
        self.assertIn("occurrence字段在此模式中禁止输出", prompt)
        self.assertLess(prompt.index("ANCHORED_SPAN_INDEX_OVERRIDE"), prompt.rfind("AB/CD"))

    def test_prompt_places_glossary_before_examples(self) -> None:
        example = record("ex1", "歼-16战机采用后掠翼。", 0, 6, "EQUIPMENT")
        prompt = build_ner_prompt(
            query_text="歼-20战斗机采用隐身设计。",
            entity_types={"EQUIPMENT": "装备", "TECH_SCHEME": "技术体制"},
            examples=[example],
            glossary_entries=["战斗机（EQUIPMENT）", "隐身设计（TECH_SCHEME）"],
        )
        self.assertLess(prompt.index("Schema"), prompt.index("领域术语表"))
        self.assertLess(prompt.index("领域术语表"), prompt.index("示例1文本"))

    def test_prompt_places_rag_after_glossary_before_examples(self) -> None:
        example = record("ex1", "Jet uses radar.", 0, 3, "EQUIPMENT")
        prompt = build_ner_prompt(
            query_text="Carrier strike group uses EOTS.",
            entity_types={"EQUIPMENT": "equipment", "MODULE": "module"},
            examples=[example],
            glossary_entries=["carrier（EQUIPMENT）"],
            rag_passages=["EOTS is an electro optical targeting system."],
        )
        self.assertLess(prompt.index("Schema"), prompt.index("领域术语表"))
        self.assertLess(prompt.index("领域术语表"), prompt.index("参考资料"))
        self.assertLess(prompt.index("参考资料"), prompt.index("示例1文本"))

    def test_select_glossary_entries_matches_query_substrings(self) -> None:
        selected = select_glossary_entries(
            "歼-16战机的最大飞行速度和机长是多少？",
            [
                {"term": "雷达", "type": "MODULE", "priority": 90},
                {"term": "歼-16战机", "type": "EQUIPMENT", "priority": 100, "aliases": ["歼16"]},
                {"term": "最大飞行速度", "type": "METRIC", "priority": 80},
                {"term": "机长", "type": "METRIC", "priority": 80},
            ],
            max_entries=3,
        )
        self.assertEqual(len(selected), 3)
        self.assertIn("歼-16战机（EQUIPMENT）", selected)
        self.assertIn("最大飞行速度（METRIC）", selected)
        self.assertIn("机长（METRIC）", selected)

    def test_parse_occurrence_based_output(self) -> None:
        text = "北京欢迎北京游客。"
        parsed = parse_extraction_output(
            json.dumps(
                {
                    "entities": [{"span": "北京", "type": "address", "occurrence": 2}],
                    "relations": [],
                },
                ensure_ascii=False,
            ),
            record_id="q1",
            text=text,
            entity_types={"address"},
        )
        self.assertEqual(parsed["entities"][0]["start"], 4)
        self.assertEqual(parsed["entities"][0]["span"], "北京")

    def test_sanitization_flag_records_entity_and_detail(self) -> None:
        flags: list[dict] = []
        parsed = parse_extraction_output(
            json.dumps(
                {
                    "entities": [{"span": "北京", "type": "ORG", "occurrence": 1}],
                    "relations": [],
                },
                ensure_ascii=False,
            ),
            record_id="q1",
            text="北京欢迎你。",
            entity_types={"address"},
            drop_invalid_entities=True,
            sanitization_flags=flags,
        )
        self.assertEqual(parsed["entities"], [])
        self.assertEqual(flags[0]["kind"], "ENTITY_DROPPED_INVALID_UNIT")
        self.assertEqual(flags[0]["entity"]["type"], "ORG")
        self.assertIn("unsupported type", flags[0]["detail"])

    def test_occurrence_sanitization_flag_records_counts_and_starts(self) -> None:
        flags: list[dict] = []
        parsed = parse_extraction_output(
            json.dumps(
                {
                    "entities": [{"span": "AB", "type": "address", "occurrence": 3}],
                    "relations": [],
                },
                ensure_ascii=False,
            ),
            record_id="q1",
            text="ABxxAByy",
            entity_types={"address"},
            drop_invalid_entities=True,
            sanitization_flags=flags,
        )
        self.assertEqual(parsed["entities"], [])
        self.assertEqual(flags[0]["kind"], "ENTITY_DROPPED_INVALID_UNIT")
        self.assertEqual(flags[0]["occurrence_requested"], 3)
        self.assertEqual(flags[0]["occurrence_available"], 2)
        self.assertEqual(flags[0]["occurrence_starts"], [0, 4])

    def test_validate_execution_gate_accepts_p5_pilot_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "P5_CONFIG_DRAFT",
                "human_gate": "P5_DOMAIN_PILOT_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_reviewer_parse_diagnostic_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_PARSE_DIAGNOSTIC",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_PARSE_DIAGNOSTIC_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_reviewer_parse_stability_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_PARSE_STABILITY_20",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_PARSE_STABILITY_20_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_ner_envelope_smoke_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_NER_ENVELOPE_SMOKE_TEST",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_NER_ENVELOPE_SMOKE_TEST_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_domain_schema_smoke_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_DOMAIN_SCHEMA_COMPATIBILITY_SMOKE",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_DOMAIN_SCHEMA_COMPATIBILITY_SMOKE_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_output_budget_repair_smoke_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_OUTPUT_BUDGET_REPAIR_SMOKE",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_OUTPUT_BUDGET_REPAIR_SMOKE_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_output_schema_bounded_smoke_15_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_OUTPUT_SCHEMA_BOUNDED_SMOKE_15",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_OUTPUT_SCHEMA_BOUNDED_SMOKE_15_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_formal_b1_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_B1_FORMAL",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_B1_FORMAL_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_qwen_parser_correction_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_QWEN_PARSER_CORRECTION",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_QWEN_PARSER_CORRECTION_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_occurrence_repair_pilot_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_REPAIR_PILOT_APPROVED",
                "phase": "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_REPAIR_PILOT",
            }
        )

    def test_candidate_index_maps_only_query_local_candidates(self) -> None:
        from equipment_ie.extraction import generate_candidate_spans
        candidates = generate_candidate_spans("雷达A测试")
        parsed = parse_extraction_output(
            '{"entities":[{"candidate_id":"c0001","type":"EQUIPMENT"}]}',
            record_id="candidate", text="雷达A测试", entity_types={"EQUIPMENT"},
            output_mode="candidate_index", candidate_spans=candidates,
        )
        self.assertEqual(parsed["entities"][0]["span"], candidates[0]["span"])

    def test_validate_execution_gate_accepts_anchored_span_index_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "REVIEWER_BASELINE_MAIN_ANCHORED_SPAN_INDEX_CORRECTION",
                "human_gate": "JISE_ECFSIE_REVIEW_BASELINE_MAIN_ANCHORED_SPAN_INDEX_CORRECTION_APPROVED",
            }
        )

    def test_span_index_output_is_converted_to_exact_entities(self) -> None:
        from equipment_ie.extraction import parse_extraction_output

        parsed = parse_extraction_output(
            '{"entities":[{"start":0,"end":2,"type":"EQUIPMENT"}],"relations":[]}',
            record_id="q1",
            text="坦克系统",
            entity_types={"EQUIPMENT"},
            output_mode="span_index",
        )
        self.assertEqual(parsed["entities"], [{"start": 0, "end": 2, "type": "EQUIPMENT", "span": "坦克"}])

    def test_anchored_span_index_requires_exact_span_echo(self) -> None:
        from equipment_ie.extraction import (
            build_ner_anchored_span_index_response_format,
            parse_extraction_output,
        )

        parsed = parse_extraction_output(
            '{"entities":[{"start":0,"end":2,"span":"AB","type":"EQUIPMENT"}],"relations":[]}',
            record_id="q1", text="ABCD", entity_types={"EQUIPMENT"},
            output_mode="anchored_span_index",
        )
        self.assertEqual(parsed["entities"][0]["span"], "AB")
        with self.assertRaisesRegex(ValueError, "does not match"):
            parse_extraction_output(
                '{"entities":[{"start":0,"end":2,"span":"AC","type":"EQUIPMENT"}],"relations":[]}',
                record_id="q1", text="ABCD", entity_types={"EQUIPMENT"},
                output_mode="anchored_span_index",
            )
        response = build_ner_anchored_span_index_response_format(["EQUIPMENT"], 4)
        item = response["json_schema"]["schema"]["properties"]["entities"]["items"]
        self.assertEqual(item["required"], ["start", "end", "span", "type"])
        self.assertEqual(response["json_schema"]["name"], "ner_anchored_span_index_output")

    def test_anchored_span_index_rejects_boolean_offsets(self) -> None:
        from equipment_ie.extraction import parse_extraction_output

        with self.assertRaisesRegex(ValueError, "valid text offsets"):
            parse_extraction_output(
                '{"entities":[{"start":true,"end":2,"span":"AB","type":"EQUIPMENT"}],"relations":[]}',
                record_id="q1", text="ABCD", entity_types={"EQUIPMENT"},
                output_mode="anchored_span_index",
            )

    def test_anchored_span_index_rejects_missing_relations_and_unknown_keys(self) -> None:
        from equipment_ie.extraction import parse_extraction_output

        for payload in (
            '{"entities":[]}',
            '{"entities":[],"relations":[],"extra":1}',
            '{"entities":[{"start":0,"end":2,"span":"AB","type":"EQUIPMENT","extra":1}],"relations":[]}',
        ):
            with self.assertRaises(ValueError):
                parse_extraction_output(
                    payload,
                    record_id="q1",
                    text="ABCD",
                    entity_types={"EQUIPMENT"},
                    output_mode="anchored_span_index",
                )

    def test_span_index_output_rejects_out_of_bounds_offsets(self) -> None:
        from equipment_ie.extraction import parse_extraction_output

        with self.assertRaisesRegex(ValueError, "valid text offsets"):
            parse_extraction_output(
                '{"entities":[{"start":0,"end":9,"type":"EQUIPMENT"}],"relations":[]}',
                record_id="q1",
                text="坦克",
                entity_types={"EQUIPMENT"},
                output_mode="span_index",
            )

    def test_ner_span_index_response_schema_is_bounded_and_strict(self) -> None:
        from equipment_ie.extraction import build_ner_span_index_response_format

        response_format = build_ner_span_index_response_format(
            ["MODULE", "EQUIPMENT"], 17, max_entities=12
        )
        self.assertEqual(response_format["type"], "json_schema")
        schema = response_format["json_schema"]["schema"]
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["entities"]["maxItems"], 12)
        item = schema["properties"]["entities"]["items"]
        self.assertFalse(item["additionalProperties"])
        self.assertEqual(item["properties"]["start"]["maximum"], 16)
        self.assertEqual(item["properties"]["end"]["maximum"], 17)
        self.assertEqual(item["properties"]["type"]["enum"], ["EQUIPMENT", "MODULE"])
        self.assertEqual(schema["properties"]["relations"]["maxItems"], 0)

    def test_ner_span_index_response_schema_rejects_invalid_budget(self) -> None:
        from equipment_ie.extraction import build_ner_span_index_response_format

        with self.assertRaisesRegex(ValueError, "max_entities"):
            build_ner_span_index_response_format(["EQUIPMENT"], 5, max_entities=0)

    def test_ner_span_index_omitted_relations_are_deterministically_defaulted(self) -> None:
        flags: list[dict] = []
        parsed = parse_extraction_output(
            '{"entities":[{"start":0,"end":2,"type":"EQUIPMENT"}]}',
            record_id="q1", text="ABCD", entity_types={"EQUIPMENT"},
            output_mode="span_index", sanitization_flags=flags,
        )
        self.assertEqual(parsed["relations"], [])
        self.assertEqual(flags[0]["kind"], "NER_RELATIONS_DEFAULTED")

    def test_relation_enabled_span_index_still_requires_relations(self) -> None:
        with self.assertRaisesRegex(ValueError, "entities and relations only"):
            parse_extraction_output(
                '{"entities":[]}', record_id="q1", text="AB",
                entity_types={"EQUIPMENT"},
                relation_types={"USES": {"head_types": ["EQUIPMENT"], "tail_types": ["EQUIPMENT"]}},
                output_mode="span_index",
            )

    def test_occurrence_mode_still_requires_relations_envelope(self) -> None:
        with self.assertRaisesRegex(ValueError, "entities and relations only"):
            parse_extraction_output(
                '{"entities":[]}', record_id="q1", text="AB",
                entity_types={"EQUIPMENT"}, output_mode="occurrence",
            )

    def test_ner_span_index_rejects_unknown_or_nonempty_relations(self) -> None:
        for payload in (
            '{"entities":[],"extra":1}',
            '{"entities":[],"relations":[{"head":0,"tail":0,"type":"USES"}]}',
        ):
            with self.assertRaisesRegex(ValueError, "output must contain entities and relations only|relations are not enabled"):
                parse_extraction_output(
                    payload, record_id="q1", text="AB", entity_types={"EQUIPMENT"},
                    output_mode="span_index",
                )

    def test_span_index_rejects_invalid_entity_units(self) -> None:
        payloads = (
            '{"entities":[{"start":0,"end":1,"type":"UNKNOWN"}],"relations":[]}',
            '{"entities":[{"start":0,"end":0,"type":"EQUIPMENT"}],"relations":[]}',
            '{"entities":[{"start":0,"end":1,"type":"EQUIPMENT"},{"start":0,"end":1,"type":"EQUIPMENT"}],"relations":[]}',
            '{"entities":[{"start":0,"end":2,"type":"EQUIPMENT"},{"start":1,"end":3,"type":"EQUIPMENT"}],"relations":[]}',
        )
        for payload in payloads:
            with self.assertRaises(ValueError):
                parse_extraction_output(
                    payload, record_id="q1", text="ABCD", entity_types={"EQUIPMENT"},
                    output_mode="span_index",
                )

    def test_span_index_rejects_malformed_json_and_wrong_entity_shape(self) -> None:
        for payload in ("{not-json", '{"entities":[{"start":0,"end":1}],"relations":[]}'):
            with self.assertRaises(ValueError):
                parse_extraction_output(
                    payload, record_id="q1", text="AB", entity_types={"EQUIPMENT"},
                    output_mode="span_index",
                )

    def test_request_envelope_can_enable_json_response_format(self) -> None:
        from equipment_ie.extraction import build_request_envelope

        envelope = build_request_envelope(
            prompt="prompt",
            model="model",
            generation={
                "temperature": 0,
                "top_p": 1,
                "max_tokens": 100,
                "seed": 42,
                "response_format": {"type": "json_object"},
            },
            run_id="run",
            config_hash="hash",
        )
        self.assertEqual(envelope["payload"]["response_format"], {"type": "json_object"})

    def test_validate_execution_gate_accepts_p5_replication_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "P5_DOMAIN_REPLICATION",
                "human_gate": "P5_DOMAIN_REPLICATION_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_m2_domain_dev_z_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "M2_DOMAIN_DEV_Z_EXECUTION",
                "human_gate": "M2_DOMAIN_DEV_Z_APPROVED",
            }
        )

    def test_validate_execution_gate_accepts_public_cluener_final_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "NER_PUBLIC_CLUENER_FINAL",
                "human_gate": "NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED",
            }
        )

    def test_validate_execution_gate_rejects_public_cluener_wrong_phase(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "requires execution.phase"):
            validate_execution_gate(
                {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "NER_PUBLIC_CLUENER_OTHER",
                    "human_gate": "NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED",
                }
            )

    def test_validate_execution_gate_rejects_m2_gate_for_other_phase(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "requires execution.phase"):
            validate_execution_gate(
                {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "M2_OTHER",
                    "human_gate": "M2_DOMAIN_DEV_Z_APPROVED",
                }
            )

    def test_validate_execution_gate_requires_model_calls_allowed(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "model_calls_allowed"):
            validate_execution_gate(
                {
                    "authorized": True,
                    "model_calls_allowed": False,
                    "phase": "P5_CONFIG_DRAFT",
                    "human_gate": "P5_DOMAIN_PILOT_APPROVED",
                }
            )

    def test_error_retry_prompt_includes_parser_error(self) -> None:
        retry = build_error_retry_prompt(
            base_prompt="BASE_PROMPT",
            parse_error="ExtractionParseError: unsupported type 'event'",
        )
        self.assertIn("BASE_PROMPT", retry)
        self.assertIn("unsupported type", retry)
        self.assertIn("type必须来自Schema", retry)
        self.assertTrue(retry.endswith("只返回合法JSON"))

    def test_fixed_random_examples_are_deterministic(self) -> None:
        rows = [
            record(f"r{index}", f"实体{index}文本", 0, 3, "name")
            for index in range(10)
        ]
        first = select_fixed_random_examples(rows, k=3, seed=42)
        second = select_fixed_random_examples(rows, k=3, seed=42)
        self.assertEqual([row["id"] for row in first], [row["id"] for row in second])

    def test_entity_micro_counts(self) -> None:
        gold = [record("q1", "张三去了北京。", 0, 2, "name")]
        pred = [record("q1", "张三去了北京。", 0, 2, "name")]
        self.assertEqual(entity_micro_counts(gold, pred).report()["f1"], 1.0)

    def test_p3_runner_dry_run_writes_manifest_without_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            support = root / "support.jsonl"
            query = root / "query.jsonl"
            rows = [
                record(f"s{index}", f"张三{index}去了北京。", 0, 3, "name")
                for index in range(1, 8)
            ]
            write_jsonl(support, rows)
            write_jsonl(query, rows[:3])
            config = root / "config.yaml"
            prompt_rows = root / "prompts.jsonl"
            manifest = root / "manifest.json"
            config.write_text(
                "\n".join(
                    [
                        "run_id: unit-p3-dry",
                        "config_name: A",
                        "data:",
                        "  dataset: unit",
                        f"  support_path: {support.as_posix()}",
                        f"  query_path: {query.as_posix()}",
                        "schema:",
                        "  entity_types:",
                        "    name: 人名",
                        "  relation_types: {}",
                        "examples:",
                        "  mode: fixed_random",
                        "  k: 2",
                        "  seed: 7",
                        "prompt:",
                        "  output_instruction: 只返回JSON,不要任何解释,不要markdown代码块",
                        "model:",
                        "  name: unit-model",
                        "  base_url: http://127.0.0.1:8000",
                        "  timeout_seconds: 1",
                        "generation:",
                        "  temperature: 0.0",
                        "  top_p: 1.0",
                        "  max_tokens: 64",
                        "  seed: 7",
                        "cache:",
                        f"  dir: {(root / 'cache').as_posix()}",
                        "dry_run:",
                        "  max_queries: 2",
                        "outputs:",
                        f"  dry_run_prompts: {prompt_rows.as_posix()}",
                        f"  manifest: {manifest.as_posix()}",
                        f"  per_query: {(root / 'per_query.jsonl').as_posix()}",
                        f"  summary: {(root / 'summary.json').as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )

            argv = sys.argv
            sys.argv = ["run_p3_extraction.py", "--config", str(config), "--dry-run"]
            try:
                self.assertEqual(run_main(), 0)
            finally:
                sys.argv = argv

            saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved_manifest["model_calls"], 0)
            self.assertFalse(saved_manifest["api_called"])
            self.assertEqual(len(list(iter_jsonl(prompt_rows, validate=False))), 2)

    def test_p3_runner_dry_run_replays_knn_examples_and_glossary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            support = root / "support.jsonl"
            query = root / "query.jsonl"
            replay = root / "replay.jsonl"
            glossary = root / "glossary.jsonl"
            prompt_rows = root / "prompts.jsonl"
            manifest = root / "manifest.json"
            write_jsonl(
                support,
                [
                    record("s1", "歼-20战斗机采用隐身设计。", 0, 7, "EQUIPMENT"),
                    record("s2", "雷达系统完成目标探测。", 0, 4, "MODULE"),
                    record("s3", "后掠翼提升高速性能。", 0, 3, "TECH_SCHEME"),
                ],
            )
            write_jsonl(
                query,
                [
                    record("q1", "歼-16战机采用后掠翼。", 0, 6, "EQUIPMENT"),
                    record("q2", "雷达系统的最大探测距离提升。", 0, 4, "MODULE"),
                ],
            )
            write_jsonl(
                replay,
                [
                    {"id": "q1", "example_ids": ["s2", "s1"]},
                    {"id": "q2", "example_ids": ["s1", "s3"]},
                ],
            )
            write_jsonl(
                glossary,
                [
                    {"term": "歼-16战机", "type": "EQUIPMENT", "priority": 100},
                    {"term": "后掠翼", "type": "TECH_SCHEME", "priority": 90},
                    {"term": "雷达系统", "type": "MODULE", "priority": 100},
                ],
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "run_id: unit-p3-c-dry",
                        "config_name: C",
                        "data:",
                        "  dataset: unit",
                        f"  support_path: {support.as_posix()}",
                        f"  query_path: {query.as_posix()}",
                        "schema:",
                        "  entity_types:",
                        "    EQUIPMENT: 装备",
                        "    MODULE: 部件",
                        "    TECH_SCHEME: 技术体制",
                        "  relation_types: {}",
                        "examples:",
                        "  mode: knn_replay",
                        "  k: 2",
                        "  seed: 42",
                        f"  source_per_query_path: {replay.as_posix()}",
                        "glossary:",
                        f"  path: {glossary.as_posix()}",
                        "  max_entries: 2",
                        "prompt:",
                        "  output_instruction: 只返回JSON,不要任何解释,不要markdown代码块",
                        "model:",
                        "  name: unit-model",
                        "  base_url: http://127.0.0.1:8000",
                        "  timeout_seconds: 1",
                        "generation:",
                        "  temperature: 0.0",
                        "  top_p: 1.0",
                        "  max_tokens: 64",
                        "  seed: 42",
                        "cache:",
                        f"  dir: {(root / 'cache').as_posix()}",
                        "outputs:",
                        f"  dry_run_prompts: {prompt_rows.as_posix()}",
                        f"  manifest: {manifest.as_posix()}",
                        f"  per_query: {(root / 'per_query.jsonl').as_posix()}",
                        f"  summary: {(root / 'summary.json').as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )

            argv = sys.argv
            sys.argv = ["run_p3_extraction.py", "--config", str(config), "--dry-run"]
            try:
                self.assertEqual(run_main(), 0)
            finally:
                sys.argv = argv

            saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved_manifest["example_selection"]["mode"], "knn_replay")
            self.assertTrue(saved_manifest["glossary_selection"]["enabled"])
            saved_prompts = list(iter_jsonl(prompt_rows, validate=False))
            self.assertEqual(saved_prompts[0]["example_ids"], ["s2", "s1"])
            self.assertIn("歼-16战机（EQUIPMENT）", saved_prompts[0]["glossary_terms"])
            self.assertIn("后掠翼（TECH_SCHEME）", saved_prompts[0]["glossary_terms"])


    def test_p3_runner_dry_run_writes_rag_preview_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            support = root / "support.jsonl"
            query = root / "query.jsonl"
            corpus = root / "rag.jsonl"
            prompt_rows = root / "prompts.jsonl"
            manifest = root / "manifest.json"
            write_jsonl(
                support,
                [
                    record("s1", "Carrier uses radar.", 0, 7, "EQUIPMENT"),
                    record("s2", "Missile uses seeker.", 0, 7, "EQUIPMENT"),
                    record("s3", "Radar tracks aircraft.", 0, 5, "MODULE"),
                ],
            )
            write_jsonl(
                query,
                [
                    record("q1", "Carrier strike group uses EOTS targeting system.", 0, 7, "EQUIPMENT"),
                ],
            )
            write_jsonl(
                corpus,
                [
                    {
                        "id": "q1",
                        "title": "Self leak",
                        "source_type": "unit",
                        "text": "Carrier strike group uses EOTS targeting system.",
                    },
                    {
                        "id": "p1",
                        "title": "Carrier strike group",
                        "source_type": "unit",
                        "text": "Carrier strike group has radar and EOTS targeting evidence.",
                    },
                    {
                        "id": "p2",
                        "title": "Unrelated",
                        "source_type": "unit",
                        "text": "Cooking equipment patent text.",
                    },
                ],
            )
            config = root / "config.yaml"
            config.write_text(
                "\n".join(
                    [
                        "run_id: unit-p3-d-rag-dry",
                        "config_name: D",
                        "data:",
                        "  dataset: unit",
                        f"  support_path: {support.as_posix()}",
                        f"  query_path: {query.as_posix()}",
                        "schema:",
                        "  entity_types:",
                        "    EQUIPMENT: equipment",
                        "    MODULE: module",
                        "  relation_types: {}",
                        "examples:",
                        "  mode: fixed_random",
                        "  k: 2",
                        "  seed: 42",
                        "rag:",
                        "  enabled: true",
                        "  mode: lexical_preview",
                        f"  corpus_path: {corpus.as_posix()}",
                        f"  exclude_source_ids_path: {query.as_posix()}",
                        "  top_k: 1",
                        "  retrieve_top_k: 2",
                        "  chunk_chars: 120",
                        "  overlap_chars: 0",
                        "prompt:",
                        "  output_instruction: 只返回JSON,不要任何解释,不要markdown代码块",
                        "model:",
                        "  name: unit-model",
                        "  base_url: http://127.0.0.1:8000",
                        "  timeout_seconds: 1",
                        "generation:",
                        "  temperature: 0.0",
                        "  top_p: 1.0",
                        "  max_tokens: 64",
                        "  seed: 42",
                        "cache:",
                        f"  dir: {(root / 'cache').as_posix()}",
                        "outputs:",
                        f"  dry_run_prompts: {prompt_rows.as_posix()}",
                        f"  manifest: {manifest.as_posix()}",
                        f"  per_query: {(root / 'per_query.jsonl').as_posix()}",
                        f"  summary: {(root / 'summary.json').as_posix()}",
                    ]
                ),
                encoding="utf-8",
            )

            argv = sys.argv
            sys.argv = ["run_p3_extraction.py", "--config", str(config), "--dry-run"]
            try:
                self.assertEqual(run_main(), 0)
            finally:
                sys.argv = argv

            saved_manifest = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertTrue(saved_manifest["rag_selection"]["enabled"])
            self.assertEqual(saved_manifest["rag_selection"]["mode"], "lexical_preview")
            self.assertEqual(saved_manifest["rag_selection"]["excluded_source_ids"], 1)
            self.assertEqual(saved_manifest["rag_selection"]["raw_chunk_count"], 3)
            self.assertEqual(saved_manifest["rag_selection"]["chunk_count"], 2)
            saved_prompts = list(iter_jsonl(prompt_rows, validate=False))
            self.assertEqual(saved_prompts[0]["rag_passage_ids"], ["p1#chunk-0"])
            self.assertIn("Carrier strike group", saved_prompts[0]["rag_passages"][0])

    def test_run_execute_records_nonsemantic_timing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            per_query = root / "per_query.jsonl"
            summary = root / "summary.json"
            query_record = record("q1", "Carrier uses radar.", 0, 7, "EQUIPMENT")
            support_record = record("s1", "Carrier has radar.", 0, 7, "EQUIPMENT")
            config = {
                "run_id": "unit-execute-timing",
                "config_name": "unit",
                "execution": {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "P3_UNIT",
                    "human_gate": "P3_GPU_SANITY_APPROVED",
                },
                "data": {"dataset": "unit"},
                "schema": {"entity_types": {"EQUIPMENT": "equipment"}, "relation_types": {}},
                "examples": {"mode": "fixed_random", "k": 1, "seed": 42},
                "prompt": {
                    "output_instruction": "JSON_ONLY",
                },
                "model": {
                    "name": "unit-model",
                    "base_url": "http://127.0.0.1:8000",
                    "timeout_seconds": 1,
                    "api_key": "EMPTY",
                },
                "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 64, "seed": 42},
                "cache": {"dir": (root / "cache").as_posix()},
                "outputs": {
                    "per_query": per_query.as_posix(),
                    "summary": summary.as_posix(),
                },
            }

            def select_examples(_record: dict) -> list[dict]:
                return [support_record]

            def select_glossary(_record: dict) -> list[str]:
                return ["Carrier(EQUIPMENT)"]

            def select_rag(_record: dict) -> list[dict]:
                return [{"id": "p1#chunk-0", "display": "Carrier evidence."}]

            def fake_chat_with_cache(**_kwargs: object) -> ChatResult:
                return ChatResult(
                    content=json.dumps(
                        {
                            "entities": [
                                {"span": "Carrier", "type": "EQUIPMENT", "occurrence": 1}
                            ],
                            "relations": [],
                        }
                    ),
                    request_hash="request-hash",
                    raw_output_hash="raw-hash",
                    cache_hit=True,
                    latency_ms=12.5,
                )

            with (
                patch("scripts.run_p3_extraction.gpu_visible", return_value=True),
                patch(
                    "scripts.run_p3_extraction.build_query_plan",
                    return_value=(
                        [support_record],
                        [query_record],
                        select_examples,
                        select_glossary,
                        select_rag,
                        "config-hash",
                        {"mode": "mock"},
                        {"enabled": True},
                        {"enabled": True},
                    ),
                ),
                patch("scripts.run_p3_extraction.chat_with_cache", side_effect=fake_chat_with_cache),
            ):
                self.assertEqual(run_execute(config, root / "config.yaml"), 0)

            saved_rows = list(iter_jsonl(per_query, validate=False))
            self.assertEqual(len(saved_rows), 1)
            row = saved_rows[0]
            self.assertEqual(row["latency_ms"], 12.5)
            self.assertEqual(row["llm_latency_ms"], 12.5)
            self.assertEqual(row["accepted_entity_count"], 1)
            self.assertEqual(row["invalid_unit_drops"], 0)
            self.assertEqual(row["overlap_drops"], 0)
            self.assertEqual(row["raw_candidate_entity_count"], 1)
            for field in (
                "example_selection_ms",
                "glossary_selection_ms",
                "rag_selection_ms",
                "prompt_build_ms",
                "total_record_ms",
            ):
                self.assertIsInstance(row[field], float)
                self.assertGreaterEqual(row[field], 0.0)

            saved_summary = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(saved_summary["timing_totals_ms"]["llm_latency_ms"], 12.5)
            self.assertIn("rag_selection_ms", saved_summary["timing_means_ms"])
            self.assertEqual(saved_summary["entity_micro"]["tp"], 1)
            self.assertEqual(saved_summary["sanitization_counts"]["all_unit_events"], 0)
            self.assertEqual(saved_summary["entity_audit_counts"]["accepted_entities"], 1)
            self.assertEqual(
                saved_summary["entity_audit_counts"]["raw_candidate_entities_observed"], 1
            )
            self.assertEqual(saved_summary["entity_audit_counts"]["rows_with_unknown_raw_candidates"], 0)

    def test_run_execute_logs_unit_drops_without_offset_repair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            per_query = root / "per_query.jsonl"
            summary = root / "summary.json"
            query_record = record("q1", "Radar and carrier.", 0, 5, "EQUIPMENT")
            config = {
                "run_id": "unit-execute-drop-audit",
                "config_name": "unit-drop-audit",
                "execution": {
                    "authorized": True,
                    "model_calls_allowed": True,
                    "phase": "P3_UNIT",
                    "human_gate": "P3_GPU_SANITY_APPROVED",
                },
                "data": {"dataset": "unit"},
                "schema": {"entity_types": {"EQUIPMENT": "equipment"}, "relation_types": {}},
                "examples": {"mode": "none", "k": 0, "seed": 42},
                "prompt": {"output_instruction": "JSON_ONLY"},
                "model": {
                    "name": "unit-model",
                    "base_url": "http://127.0.0.1:8000",
                    "timeout_seconds": 1,
                    "api_key": "EMPTY",
                },
                "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 64, "seed": 42},
                "cache": {"dir": (root / "cache").as_posix()},
                "outputs": {"per_query": per_query.as_posix(), "summary": summary.as_posix()},
                "parsing": {
                    "drop_invalid_entities": True,
                    "output_mode": "occurrence",
                    "constrained_json_schema": False,
                    "max_entities": 12,
                },
            }

            def fake_chat_with_cache(**_kwargs: object) -> ChatResult:
                return ChatResult(
                    content=json.dumps(
                        {
                            "entities": [
                                {"span": "Radar", "type": "EQUIPMENT", "occurrence": 1},
                                {"span": "not-in-text", "type": "EQUIPMENT", "occurrence": 1},
                            ],
                            "relations": [],
                        }
                    ),
                    request_hash="request-drop",
                    raw_output_hash="raw-drop",
                    cache_hit=True,
                    latency_ms=1.0,
                )

            with (
                patch("scripts.run_p3_extraction.gpu_visible", return_value=True),
                patch(
                    "scripts.run_p3_extraction.build_query_plan",
                    return_value=(
                        [],
                        [query_record],
                        lambda _r: [],
                        lambda _r: [],
                        lambda _r: [],
                        "hash",
                        {},
                        {"enabled": False},
                        {"enabled": False},
                    ),
                ),
                patch("scripts.run_p3_extraction.chat_with_cache", side_effect=fake_chat_with_cache),
            ):
                self.assertEqual(run_execute(config, root / "config.yaml"), 0)

            saved_rows = list(iter_jsonl(per_query, validate=False))
            self.assertEqual(saved_rows[0]["pred_raw"]["entities"][0]["span"], "Radar")
            self.assertEqual(saved_rows[0]["accepted_entity_count"], 1)
            self.assertEqual(saved_rows[0]["invalid_unit_drops"], 1)
            self.assertEqual(saved_rows[0]["raw_candidate_entity_count"], 2)
            self.assertEqual(saved_rows[0]["sanitization_flags"][0]["kind"], "ENTITY_DROPPED_INVALID_UNIT")
            saved_summary = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(saved_summary["sanitization_counts"]["invalid_unit_drops"], 1)
            self.assertEqual(saved_summary["entity_audit_counts"]["raw_candidate_entities_observed"], 2)

    def test_rag_replay_manifest_round_trip_preserves_passages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            query = root / "query.jsonl"
            corpus = root / "rag.jsonl"
            config_path = root / "config.yaml"
            replay_path = root / "rag_replay.json"
            write_jsonl(
                query,
                [
                    record("q1", "Carrier strike group uses EOTS targeting system.", 0, 7, "EQUIPMENT"),
                ],
            )
            write_jsonl(
                corpus,
                [
                    {
                        "id": "q1",
                        "title": "Self leak",
                        "source_type": "unit",
                        "text": "Carrier strike group uses EOTS targeting system.",
                    },
                    {
                        "id": "p1",
                        "title": "Carrier evidence",
                        "source_type": "unit",
                        "text": "Carrier strike group has radar and EOTS targeting evidence.",
                    },
                    {
                        "id": "p2",
                        "title": "Other",
                        "source_type": "unit",
                        "text": "Unrelated cooking equipment.",
                    },
                ],
            )
            config_path.write_text("unit config for replay manifest\n", encoding="utf-8")
            config = {
                "data": {"query_path": query.as_posix()},
                "rag": {
                    "enabled": True,
                    "mode": "lexical_preview",
                    "corpus_path": corpus.as_posix(),
                    "exclude_source_ids_path": query.as_posix(),
                    "top_k": 1,
                    "retrieve_top_k": 2,
                    "chunk_chars": 120,
                    "overlap_chars": 0,
                    "max_passage_chars": 160,
                },
            }

            manifest = build_rag_replay_manifest(
                config,
                config_path=config_path,
                output_path=replay_path,
            )
            self.assertFalse(manifest["api_called"])
            self.assertEqual(manifest["model_calls"], 0)
            self.assertEqual(manifest["rows"][0]["rag_passage_ids"], ["p1#chunk-0"])
            self.assertTrue(replay_path.is_file())

            replay_config = {
                "data": {"query_path": query.as_posix()},
                "rag": {
                    "enabled": True,
                    "mode": "replay_manifest",
                    "replay_manifest_path": replay_path.as_posix(),
                },
            }
            select_rag, metadata = build_rag_selector(replay_config)
            selected = select_rag({"id": "q1", "text": "Carrier strike group uses EOTS."})
            self.assertEqual(metadata["mode"], "replay_manifest")
            self.assertEqual([passage["id"] for passage in selected], ["p1#chunk-0"])
            self.assertEqual(
                [passage["display"] for passage in selected],
                manifest["rows"][0]["rag_passages"],
            )

    def test_rag_replay_manifest_can_be_built_from_existing_per_query(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            query = root / "query.jsonl"
            per_query = root / "per_query.jsonl"
            config_path = root / "config.yaml"
            replay_path = root / "rag_replay.json"
            write_jsonl(query, [record("q1", "Carrier uses radar.", 0, 7, "EQUIPMENT")])
            write_jsonl(
                per_query,
                [
                    {
                        "id": "q1",
                        "rag_passage_ids": ["p1#chunk-0"],
                        "rag_passages": ["Carrier evidence | unit | p1#chunk-0: Carrier text"],
                    }
                ],
            )
            config_path.write_text("unit config for per-query replay\n", encoding="utf-8")
            config = {"data": {"query_path": query.as_posix()}}

            manifest = build_rag_replay_manifest_from_per_query(
                config,
                config_path=config_path,
                output_path=replay_path,
                source_per_query_path=per_query,
            )
            self.assertEqual(manifest["source_rag_mode"], "per_query_replay")
            self.assertEqual(manifest["query_records"], 1)

            replay_config = {
                "data": {"query_path": query.as_posix()},
                "rag": {
                    "enabled": True,
                    "mode": "replay_manifest",
                    "replay_manifest_path": replay_path.as_posix(),
                },
            }
            select_rag, _metadata = build_rag_selector(replay_config)
            selected = select_rag({"id": "q1", "text": "Carrier uses radar."})
            self.assertEqual(selected, manifest["rows"][0]["selected_passages"])


if __name__ == "__main__":
    unittest.main()
