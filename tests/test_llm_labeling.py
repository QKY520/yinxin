from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.domain_data import text_sha256  # noqa: E402
from equipment_ie.llm_labeling import (  # noqa: E402
    LabelParseError,
    build_label_prompt,
    build_llm_review_row,
    build_request_envelope,
    canonical_json,
    chat_with_cache,
    merge_distant_and_llm,
    parse_model_label_output,
    request_hash,
    select_candidates,
    strip_code_fences,
    write_llm_review_csv_atomic,
)
from equipment_ie.schema import iter_jsonl  # noqa: E402


def candidate(record_id: str, source_type: str, text: str) -> dict:
    return {
        "id": record_id,
        "source_candidate_id": f"source-{record_id}",
        "text": text,
        "source_type": source_type,
        "source_id": record_id,
        "source_split": "train",
        "source_url": "https://example.test",
        "source_revision": "revision",
        "source_license": "MIT",
        "title": record_id,
        "content_sha256": text_sha256(text),
    }


def record(record_id: str, text: str, entities: list[dict] | None = None) -> dict:
    return {
        "id": record_id,
        "text": text,
        "entities": entities or [],
        "relations": [],
    }


class LlmLabelingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_schema_draft.yaml").read_text(
                encoding="utf-8"
            )
        )
        cls.prompt_config = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_llm_prompt_v1.yaml").read_text(
                encoding="utf-8"
            )
        )
        cls.examples = list(
            iter_jsonl(PROJECT_ROOT / "docs" / "p2_schema_examples_draft.jsonl")
        )

    def test_strip_fences_and_parse_occurrence_output(self) -> None:
        text = "雷达甲采用惯性导航。"
        raw = """```json
{"entities":[{"span":"惯性导航","type":"TECH_SCHEME","occurrence":1},{"span":"雷达甲","type":"EQUIPMENT","occurrence":1}],"relations":[{"head":1,"tail":0,"type":"USES"}]}
```"""
        parsed = parse_model_label_output(
            raw, record_id="r1", text=text, schema=self.schema
        )
        self.assertEqual(strip_code_fences(raw)[0], "{")
        self.assertEqual([entity["span"] for entity in parsed["entities"]], ["雷达甲", "惯性导航"])
        self.assertEqual(parsed["relations"], [{"head": 0, "tail": 1, "type": "USES"}])

    def test_parser_rejects_overlap_and_invalid_type_matrix(self) -> None:
        overlap = canonical_json(
            {
                "entities": [
                    {"span": "雷达甲", "type": "EQUIPMENT", "occurrence": 1},
                    {"span": "雷达", "type": "EQUIPMENT", "occurrence": 1},
                ],
                "relations": [],
            }
        )
        with self.assertRaises(LabelParseError):
            parse_model_label_output(
                overlap, record_id="r1", text="雷达甲工作正常。", schema=self.schema
            )
        invalid_relation = canonical_json(
            {
                "entities": [
                    {"span": "航程100公里", "type": "METRIC", "occurrence": 1},
                    {"span": "惯性导航", "type": "TECH_SCHEME", "occurrence": 1},
                ],
                "relations": [{"head": 0, "tail": 1, "type": "USES"}],
            }
        )
        with self.assertRaises(LabelParseError):
            parse_model_label_output(
                invalid_relation,
                record_id="r2",
                text="航程100公里，采用惯性导航。",
                schema=self.schema,
            )

    def test_prompt_uses_approved_examples_without_distant_suggestions(self) -> None:
        prompt = build_label_prompt(
            text="待处理文本。",
            schema=self.schema,
            prompt_config=self.prompt_config,
            examples=self.examples,
            prompt_version="p2-llm-label-v1",
        )
        self.assertIn("示例10文本", prompt)
        self.assertIn("occurrence", prompt)
        self.assertNotIn("远程监督建议", prompt)
        self.assertTrue(prompt.endswith("只返回JSON,不要任何解释,不要markdown代码块"))

    def test_checked_in_llm_configs_cannot_execute(self) -> None:
        for name in ("p2_llm_label_sanity.yaml", "p2_llm_label_full.yaml"):
            config = yaml.safe_load(
                (PROJECT_ROOT / "configs" / name).read_text(encoding="utf-8")
            )
            self.assertFalse(config["execution"]["authorized"])
            self.assertIsNone(config["execution"]["approval_record"])
            self.assertTrue(config["execution"]["dry_run_requires_gpu_free"])
            self.assertTrue(config["execution"]["actual_run_requires_gpu"])
            self.assertFalse(config["prompt"]["include_distant_supervision_in_prompt"])
            self.assertFalse(config["guards"]["human_annotation_allowed"])

    def test_request_hash_changes_with_generation_settings(self) -> None:
        base = build_request_envelope(
            prompt="prompt",
            model="model",
            generation={"temperature": 0, "top_p": 1, "max_tokens": 100, "seed": 42},
            prompt_version="v1",
            schema_sha256="a",
            prompt_config_sha256="p",
            examples_sha256="b",
        )
        changed = build_request_envelope(
            prompt="prompt",
            model="model",
            generation={"temperature": 0, "top_p": 1, "max_tokens": 101, "seed": 42},
            prompt_version="v1",
            schema_sha256="a",
            prompt_config_sha256="p",
            examples_sha256="b",
        )
        self.assertEqual(request_hash(base), request_hash(json.loads(json.dumps(base))))
        self.assertNotEqual(request_hash(base), request_hash(changed))

    def test_chat_cache_prevents_duplicate_request(self) -> None:
        envelope = build_request_envelope(
            prompt="prompt",
            model="model",
            generation={"temperature": 0, "top_p": 1, "max_tokens": 100, "seed": 42},
            prompt_version="v1",
            schema_sha256="a",
            prompt_config_sha256="p",
            examples_sha256="b",
        )
        response = {"choices": [{"message": {"content": '{"entities":[],"relations":[]}'}}]}
        with tempfile.TemporaryDirectory() as directory:
            with patch(
                "equipment_ie.llm_labeling._post_chat_completion",
                return_value=(response, 12.5),
            ) as mocked:
                first = chat_with_cache(
                    envelope=envelope,
                    cache_dir=Path(directory),
                    base_url="http://127.0.0.1:8000",
                    timeout_seconds=10,
                    api_key="EMPTY",
                )
                second = chat_with_cache(
                    envelope=envelope,
                    cache_dir=Path(directory),
                    base_url="http://127.0.0.1:8000",
                    timeout_seconds=10,
                    api_key="EMPTY",
                )
        self.assertEqual(mocked.call_count, 1)
        self.assertFalse(first.cache_hit)
        self.assertTrue(second.cache_hit)
        self.assertEqual(first.raw_output_hash, second.raw_output_hash)

    def test_sanity_selection_covers_sources_and_match_states(self) -> None:
        candidates: list[dict] = []
        distant: list[dict] = []
        for source in ("baidu_baike", "patent", "cmnee"):
            for index in range(4):
                record_id = f"{source}-{index}"
                text = (record_id + "甲" * 120)[:120]
                row = candidate(record_id, source, text)
                candidates.append(row)
                entities = (
                    [{"start": 0, "end": 1, "type": "EQUIPMENT", "span": text[0]}]
                    if index % 2 == 0
                    else []
                )
                distant.append(record(record_id, text, entities))
        selected = select_candidates(
            candidates,
            distant,
            {
                "mode": "sanity",
                "sample_size": 6,
                "minimum_per_source": 1,
                "minimum_ds_matched": 2,
                "minimum_ds_unmatched": 2,
                "seed": 42,
            },
        )
        selected_ids = {row["id"] for row in selected}
        self.assertEqual(len(selected), 6)
        self.assertEqual({row["source_type"] for row in selected}, {"baidu_baike", "patent", "cmnee"})
        match_by_id = {row["id"]: bool(row["entities"]) for row in distant}
        self.assertGreaterEqual(sum(match_by_id[row_id] for row_id in selected_ids), 2)
        self.assertGreaterEqual(sum(not match_by_id[row_id] for row_id in selected_ids), 2)

    def test_merge_and_review_preserve_disagreement_and_blank_human_fields(self) -> None:
        text = "雷达甲采用惯性导航。" + "甲" * 100
        distant = record(
            "r1",
            text,
            [{"start": 0, "end": 3, "type": "EQUIPMENT", "span": "雷达甲"}],
        )
        llm = {
            "id": "r1",
            "text": text,
            "entities": [
                {"start": 0, "end": 3, "type": "EQUIPMENT", "span": "雷达甲"},
                {"start": 5, "end": 9, "type": "TECH_SCHEME", "span": "惯性导航"},
            ],
            "relations": [{"head": 0, "tail": 1, "type": "USES"}],
        }
        union, provenance, flags = merge_distant_and_llm(distant, llm)
        self.assertEqual(len(union["entities"]), 2)
        self.assertTrue(any(flag["kind"] == "ENTITY_ONLY_LLM" for flag in flags))
        row = build_llm_review_row(
            candidate=candidate("r1", "cmnee", text),
            distant=distant,
            llm=llm,
            union=union,
            provenance=provenance,
            disagreement_flags=flags,
            attempts=[
                {
                    "attempt": 1,
                    "prompt_hash": "p",
                    "request_hash": "r",
                    "raw_output_hash": "o",
                    "cache_hit": False,
                    "latency_ms": 1.0,
                    "parse_error": None,
                }
            ],
            prompt_version="v1",
            llm_error=None,
        )
        self.assertEqual(row["human_annotation"]["status"], "NOT_STARTED")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.csv"
            write_llm_review_csv_atomic(path, [row])
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                saved = list(csv.DictReader(handle))[0]
        self.assertEqual(saved["human_review_status"], "NOT_STARTED")
        self.assertEqual(saved["annotator_a_entities_json"], "")


if __name__ == "__main__":
    unittest.main()
