from __future__ import annotations

import csv
import hashlib
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
    extract_first_json_object,
    merge_distant_and_llm,
    parse_model_label_output,
    request_hash,
    select_candidates,
    strip_code_fences,
    write_llm_review_csv_atomic,
)
from equipment_ie.schema import iter_jsonl  # noqa: E402
from scripts import run_p2_llm_labeling as llm_runner  # noqa: E402


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

    def test_extract_first_json_object_ignores_extra_closing_brace(self) -> None:
        raw = '{"entities":[],"relations":[]}}'
        self.assertEqual(extract_first_json_object(raw), '{"entities":[],"relations":[]}')
        parsed = parse_model_label_output(raw, record_id="r1", text="无实体。", schema=self.schema)
        self.assertEqual(parsed["entities"], [])

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

    def test_prompt_v2_adds_relation_matrix_and_strict_json_rules(self) -> None:
        prompt_config = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_llm_prompt_v2.yaml").read_text(
                encoding="utf-8"
            )
        )
        prompt = build_label_prompt(
            text="待处理文本。",
            schema=self.schema,
            prompt_config=prompt_config,
            examples=self.examples,
            prompt_version="p2-llm-label-v2",
        )
        self.assertIn("关系类型矩阵", prompt)
        self.assertIn("每个实体对象必须且只能包含span、type、occurrence三个键", prompt)
        self.assertIn("不要输出第二个JSON或任何多余字符", prompt)

    def test_prompt_v3_adds_negative_relation_event_rules(self) -> None:
        prompt_config = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_llm_prompt_v3.yaml").read_text(
                encoding="utf-8"
            )
        )
        prompt = build_label_prompt(
            text="待处理文本。",
            schema=self.schema,
            prompt_config=prompt_config,
            examples=self.examples,
            prompt_version="p2-llm-label-v3",
        )
        self.assertIn("两个EQUIPMENT之间不要输出PART_OF", prompt)
        self.assertIn("发射、试射、部署、验证、集成、提供能力、奠定基础不是组成关系", prompt)

    def test_prompt_v4_tightens_overlap_and_part_of_rules(self) -> None:
        prompt_config = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_llm_prompt_v4.yaml").read_text(
                encoding="utf-8"
            )
        )
        prompt = build_label_prompt(
            text="dummy text",
            schema=self.schema,
            prompt_config=prompt_config,
            examples=self.examples,
            prompt_version="p2-llm-label-v4",
        )
        self.assertIn("删除任何重叠实体", prompt)
        self.assertIn("PART_OF的head必须是MODULE", prompt)
        self.assertIn("两个EQUIPMENT之间绝对不要输出PART_OF", prompt)

    def test_checked_in_llm_configs_keep_sanity_only_gate(self) -> None:
        expected = {
            "p2_llm_label_sanity.yaml": {
                "run_id": "p2-llm-label-sanity-v5",
                "config_sha256": "a6367a671b21ef7c94ade908806d300c88b421a92bef7f275f8460ea03b23d0c",
                "dry_run_name": "p2_llm_label_sanity_v5_dry_run.json",
                "prompt_sha256": "75993fba42169fe0670c5148a4d075184d1cd1a8d8b5fff49c248a8633deee72",
                "authorized": True,
                "approval_status": "fixed_10_record_sanity_v5_retry_only",
            },
            "p2_llm_label_full.yaml": {
                "run_id": "p2-llm-label-full-v2",
                "config_sha256": "809b3183b8c9bdced5334030fe8dce866f4d4e384ded27fa5c1d09109573fdf5",
                "dry_run_name": "p2_llm_label_full_v2_dry_run.json",
                "prompt_sha256": "d1a2569ad6a93122937c493d5b5d1b66fbb216716c4e27590c7e5a5056f7c739",
                "authorized": False,
                "approval_status": None,
            },
        }
        for name, pinned in expected.items():
            path = PROJECT_ROOT / "configs" / name
            config = yaml.safe_load(
                path.read_text(encoding="utf-8")
            )
            self.assertEqual(config["run_id"], pinned["run_id"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(),
                pinned["config_sha256"],
            )
            self.assertEqual(config["execution"]["authorized"], pinned["authorized"])
            if pinned["approval_status"]:
                self.assertEqual(
                    config["execution"]["approval_record"]["scope"],
                    pinned["approval_status"],
                )
                self.assertFalse(
                    config["execution"]["approval_record"]["full_run_authorized"]
                )
                self.assertFalse(
                    config["execution"]["approval_record"][
                        "human_annotation_authorized"
                    ]
                )
                self.assertFalse(
                    config["execution"]["approval_record"][
                        "split_or_freeze_authorized"
                    ]
                )
                self.assertEqual(
                    config["execution"]["approval_record"][
                        "live_gpu_price_cny_per_hour"
                    ],
                    2.7,
                )
                self.assertEqual(
                    config["execution"]["approval_record"]["gpu_hour_cap"], 0.25
                )
            else:
                self.assertIsNone(config["execution"]["approval_record"])
            self.assertTrue(config["execution"]["dry_run_requires_gpu_free"])
            self.assertTrue(config["execution"]["actual_run_requires_gpu"])
            self.assertFalse(config["prompt"]["include_distant_supervision_in_prompt"])
            self.assertFalse(config["guards"]["human_annotation_allowed"])
            self.assertFalse(config["guards"]["split_or_freeze_allowed"])
            self.assertEqual(
                config["schema"]["sha256"],
                "a3b2e8dcb81a6223058e028cdadcc6aecb87a10968d8ff0454aa7e535102ac56",
            )
            self.assertEqual(
                config["prompt"]["definitions_sha256"],
                pinned["prompt_sha256"],
            )
            self.assertEqual(
                Path(config["outputs"]["dry_run_manifest"]).name,
                pinned["dry_run_name"],
            )

        sanity = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_llm_label_sanity.yaml").read_text(
                encoding="utf-8"
            )
        )
        full = yaml.safe_load(
            (PROJECT_ROOT / "configs" / "p2_llm_label_full.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(sanity["selection"]["mode"], "sanity")
        self.assertEqual(sanity["selection"]["sample_size"], 10)
        self.assertEqual(sanity["server"]["request_timeout_seconds"], 300)
        self.assertEqual(sanity["budget"]["sanity_gpu_hour_cap"], 0.25)
        self.assertTrue(sanity["budget"]["live_price_required_before_launch"])
        self.assertEqual(full["selection"]["mode"], "all")
        self.assertIsNone(full["budget"]["full_gpu_hour_cap"])
        self.assertTrue(full["budget"]["full_run_estimate_requires_sanity_measurement"])

    def test_deployment_manifest_keeps_v2_active_and_v1_superseded(self) -> None:
        manifest = json.loads(
            (PROJECT_ROOT / "docs" / "p2_llm_dry_run_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            manifest["status"],
            "gpu_free_dry_run_complete_awaiting_sanity_only_approval",
        )
        self.assertEqual(
            manifest["guards"],
            {
                "execution_authorized": False,
                "gpu_device_present": False,
                "api_called": False,
                "model_weights_loaded": False,
                "paid_gpu_used": False,
                "cache_files": 0,
                "actual_output_files": 0,
                "human_annotation_started": False,
                "dataset_split_or_frozen": False,
            },
        )
        self.assertEqual(
            [row["run_id"] for row in manifest["active_v2"]],
            ["p2-llm-label-sanity-v2", "p2-llm-label-full-v2"],
        )
        self.assertEqual(
            [row["records"] for row in manifest["active_v2"]], [10, 400]
        )
        self.assertEqual(
            [row["run_id"] for row in manifest["superseded_v1"]],
            ["p2-llm-label-sanity-v1", "p2-llm-label-full-v1"],
        )
        self.assertEqual(manifest["next_gate"]["scope"], "fixed_10_record_sanity_only")
        self.assertFalse(manifest["next_gate"]["full_run_authorized"])

    def test_unapproved_execute_stops_before_server_access(self) -> None:
        context = {
            "config": {
                "execution": {
                    "authorized": False,
                    "approval_record": None,
                }
            }
        }
        with patch.object(llm_runner, "_check_server") as server_check:
            with self.assertRaisesRegex(PermissionError, "explicit human approval"):
                llm_runner.execute(context)
        server_check.assert_not_called()

    def test_gpu_guard_accepts_nonzero_device_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            device_root = Path(directory)
            (device_root / "nvidiactl").touch()
            (device_root / "nvidia-uvm").touch()
            self.assertFalse(llm_runner._gpu_device_present(device_root))
            (device_root / "nvidia4").touch()
            self.assertTrue(llm_runner._gpu_device_present(device_root))

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
