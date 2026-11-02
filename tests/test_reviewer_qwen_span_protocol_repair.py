from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import build_ner_prompt, record_as_model_json
from scripts.run_reviewer_candidate_lattice_semantic_dev_pilot import (
    GATE,
    PARSER_FAILURE_CEILING,
    PILOT_ROWS,
    parser_ceiling_is_unrecoverable,
)


def _record() -> dict:
    return {
        "id": "example",
        "text": "雷达模块工作。",
        "entities": [
            {"start": 0, "end": 2, "span": "雷达", "type": "EQUIPMENT"},
            {"start": 2, "end": 4, "span": "模块", "type": "MODULE"},
        ],
        "relations": [],
    }


def test_span_index_examples_match_requested_output_protocol() -> None:
    rendered = record_as_model_json(_record(), include_relations=False, output_mode="span_index")
    assert rendered == {
        "entities": [
            {"start": 0, "end": 2, "type": "EQUIPMENT"},
            {"start": 2, "end": 4, "type": "MODULE"},
        ],
        "relations": [],
    }

    prompt = build_ner_prompt(
        query_text="雷达模块工作。",
        entity_types={"EQUIPMENT": "equipment", "MODULE": "module"},
        examples=[_record()],
        output_mode="span_index",
        example_output_mode="span_index",
        output_instruction="JSON_ONLY",
    )
    example_json = prompt.split("示例1输出：", 1)[1].split("\n\n待抽取文本", 1)[0]
    assert json.loads(example_json) == rendered
    assert "禁止 occurrence" in prompt
    assert '"occurrence"' not in example_json


def test_approved_gate_and_final_parser_ceiling() -> None:
    assert GATE == "JISE_ECFSIE_REVIEW_BASELINE_QWEN_SPAN_PROTOCOL_REPAIR_DEV_PILOT_APPROVED"
    assert PARSER_FAILURE_CEILING == 0.25
    assert PILOT_ROWS == 20


def test_parser_ceiling_waits_until_final_threshold_is_unrecoverable() -> None:
    assert not parser_ceiling_is_unrecoverable(parser_failures=1)
    assert not parser_ceiling_is_unrecoverable(parser_failures=5)
    assert parser_ceiling_is_unrecoverable(parser_failures=6)
