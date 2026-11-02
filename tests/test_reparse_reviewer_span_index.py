from __future__ import annotations

import json

from equipment_ie.llm_labeling import sha256_text
from scripts.reparse_reviewer_span_index import reparse


def test_offline_reparse_counts_missing_relations_and_residual_failure(tmp_path):
    good = '{"entities":[{"start":0,"end":2,"type":"EQUIPMENT"}]}'
    bad = '{"entities":[{"start":0,"end":9,"type":"EQUIPMENT"}]}'
    cache = tmp_path / "cache"
    cache.mkdir()
    rows = []
    for index, raw in enumerate((good, bad), start=1):
        digest = sha256_text(raw)
        (cache / f"{index}.json").write_text(
            json.dumps({"content": raw, "raw_output_hash": digest}), encoding="utf-8"
        )
        rows.append(
            {
                "id": f"q{index}",
                "gold": {"text": "ABCD"},
                "parse_failure": True,
                "attempts": [{"raw_output_hash": digest}],
            }
        )
    per_query = tmp_path / "per_query.jsonl"
    per_query.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )

    report = reparse(per_query, cache)
    assert report["counts"]["original_parse_failures"] == 2
    assert report["counts"]["original_missing_relations_failures"] == 2
    assert report["counts"]["normalized_successes"] == 1
    assert report["counts"]["normalized_parse_failures"] == 1
    assert any("valid text offsets" in reason for reason in report["counts"]["failure_reasons"])
