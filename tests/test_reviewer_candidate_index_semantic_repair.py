from __future__ import annotations

import pytest

from scripts.prepare_reviewer_candidate_index_semantic_repair import (
    audit_rows,
    load_rows,
    tokenizer_offsets,
)
from equipment_ie.extraction import (
    format_candidate_index_window_block,
    generate_candidate_index_windows,
)


def test_windowed_candidates_are_query_local_and_overlap_covers_long_span() -> None:
    text = "前文 ABC-14 防空导弹系统，后文"
    offsets = [(index, index + 1) for index in range(len(text))]
    windows = generate_candidate_index_windows(
        text,
        token_offsets=offsets,
        window_chars=32,
        overlap_chars=16,
        max_token_width=20,
        max_span_chars=16,
    )
    candidates = [item for window in windows for item in window]
    assert any(item["span"] == "ABC-14 防空导弹系统" for item in candidates)
    assert all(0 <= item["start"] < item["end"] <= len(text) for item in candidates)
    assert all(text[item["start"] : item["end"]] == item["span"] for item in candidates)
    assert len({item["id"] for item in candidates}) == len(candidates)


def test_compact_block_is_deterministic_and_rejects_empty_input() -> None:
    spans = [{"id": "w00c0001", "span": "雷达", "start": 0, "end": 2}]
    block = format_candidate_index_window_block(spans)
    assert block.endswith("w00c0001=雷达")
    with pytest.raises(ValueError, match="must not be empty"):
        format_candidate_index_window_block([])


def test_window_candidate_cap_fails_fast() -> None:
    with pytest.raises(ValueError, match="exceeding max_candidates_per_window"):
        generate_candidate_index_windows(
            "甲乙丙丁戊己庚辛壬癸" * 4,
            token_offsets=[(index, index + 1) for index in range(40)],
            window_chars=40,
            overlap_chars=31,
            max_token_width=20,
            max_candidates_per_window=3,
        )


class _CharTokenizer:
    def __call__(self, text: str, *, add_special_tokens: bool, return_offsets_mapping: bool = False):
        if return_offsets_mapping:
            return {"offset_mapping": [(index, index + 1) for index in range(len(text))]}
        return {"input_ids": list(range(len(text)))}


def test_preflight_audit_reports_candidate_block_budget_fields() -> None:
    report = audit_rows(
        [
            {
                "id": "domain-candidate-0001",
                "text": "雷达系统采用AGM-14。",
                "entities": [{"start": 0, "end": 4, "span": "雷达系统", "type": "EQUIPMENT"}],
            }
        ],
        _CharTokenizer(),
    )
    assert report["invalid_candidate_spans"] == 0
    assert report["max_candidate_block_tokens"] > 0
    assert report["row_reports"][0]["candidate_block_tokens"]


def test_preflight_rejects_non_dev_or_invalid_tokenizer_inputs(tmp_path) -> None:
    test_path = tmp_path / "domain_test.jsonl"
    test_path.write_text("{\"id\": \"row\", \"text\": \"x\", \"entities\": []}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="only an explicit domain_dev.jsonl"):
        load_rows(test_path)
    with pytest.raises(ValueError, match="invalid offsets"):
        tokenizer_offsets(
            lambda text, **kwargs: {"offset_mapping": [(0, 0)]},
            "x",
        )
