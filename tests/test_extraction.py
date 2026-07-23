from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


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
from equipment_ie.schema import iter_jsonl  # noqa: E402
from scripts.run_p3_extraction import main as run_main  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
