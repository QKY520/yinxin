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

    def test_validate_execution_gate_accepts_p5_replication_gate(self) -> None:
        validate_execution_gate(
            {
                "authorized": True,
                "model_calls_allowed": True,
                "phase": "P5_DOMAIN_REPLICATION",
                "human_gate": "P5_DOMAIN_REPLICATION_APPROVED",
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
