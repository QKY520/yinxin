from __future__ import annotations

from pathlib import Path

import pytest

from equipment_ie.extraction import generate_candidate_index_lattice
from scripts.prepare_reviewer_candidate_lattice_budget_repair import (
    MAX_CONTEXT_TOKENS,
    MAX_GENERATION_TOKENS,
    MAX_INPUT_TOKENS,
    SAFETY_RESERVE_TOKENS,
    audit_lattice_coverage,
    deduplicate_lattice_windows,
    load_dev_rows,
)


class _WhitespaceTokenizer:
    def __call__(self, text: str, *, add_special_tokens: bool, **_: object) -> dict[str, list[int]]:
        return {"input_ids": list(range(max(1, len(text.split()))))}


class _CharOffsetTokenizer:
    def __call__(self, text: str, *, add_special_tokens: bool, return_offsets_mapping: bool = False, **_: object) -> dict[str, list[object]]:
        if return_offsets_mapping:
            return {"offset_mapping": [(index, index + 1) for index in range(len(text))]}
        return {"input_ids": list(range(len(text)))}


def test_character_lattice_covers_long_span_and_preserves_exact_slices() -> None:
    text = "x" * 10 + "密集阵近程武器系统计算机控制雷达制导20毫米火炮系统" + "y" * 20
    windows = generate_candidate_index_lattice(text)
    candidates = deduplicate_lattice_windows(windows)
    assert any(item["span"] == text[10:36] for item in candidates)
    assert all(text[item["start"] : item["end"]] == item["span"] for item in candidates)
    assert len({item["id"] for item in candidates}) == len(candidates)
    assert max(len(window) for window in windows) <= 2048


def test_lattice_coverage_audit_is_label_read_only_and_complete() -> None:
    text = "甲" * 80
    rows = [
        {
            "id": "domain-candidate-0001",
            "text": text,
            "entities": [{"start": 10, "end": 36, "span": text[10:36], "type": "EQUIPMENT"}],
            "relations": [],
        }
    ]
    reports, summary = audit_lattice_coverage(rows, _CharOffsetTokenizer())
    assert reports[0]["missing_gold_entities"] == []
    assert summary["coverage"] == 1.0
    assert summary["invalid_candidate_spans"] == 0


def test_budget_constants_leave_generation_and_safety_reserve() -> None:
    assert MAX_INPUT_TOKENS + MAX_GENERATION_TOKENS + SAFETY_RESERVE_TOKENS == MAX_CONTEXT_TOKENS


def test_candidate_index_examples_use_occurrence_rendering() -> None:
    from equipment_ie.extraction import build_ner_prompt

    example = {
        "id": "support-1",
        "text": "雷达系统",
        "entities": [{"start": 0, "end": 4, "span": "雷达系统", "type": "EQUIPMENT"}],
        "relations": [],
    }
    prompt = build_ner_prompt(
        query_text="测试文本",
        entity_types={"EQUIPMENT": "equipment"},
        examples=[example],
        output_mode="candidate_index",
    )
    assert '"occurrence":1' in prompt
    assert '"candidate_id"' not in prompt


def test_dev_loader_rejects_test_named_path(tmp_path: Path) -> None:
    path = tmp_path / "domain_test.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="test"):
        load_dev_rows(path)
