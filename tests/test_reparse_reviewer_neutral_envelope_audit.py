import json
from pathlib import Path

from scripts.reparse_reviewer_neutral_envelope_audit import reparse_row


def test_neutral_reparse_accepts_entities_only_first_attempt(tmp_path: Path) -> None:
    request_hash = "a" * 64
    cache = tmp_path / "aa"
    cache.mkdir()
    (cache / f"{request_hash}.json").write_text(
        json.dumps({"content": '{"entities":[{"span":"雷达","type":"MODULE","occurrence":1}]}', "raw_output_hash": "b" * 64}),
        encoding="utf-8",
    )
    row = {
        "id": "q1",
        "gold": {"id": "q1", "text": "雷达", "entities": [], "relations": []},
        "attempts": [{"request_hash": request_hash}],
    }
    result = reparse_row(row, tmp_path)
    assert result["parse_failure"] is False
    assert result["accepted_attempt"] == 1
    assert result["pred_raw"]["entities"][0]["span"] == "雷达"
    assert result["sanitization_flags"][0]["kind"] == "NER_RELATIONS_DEFAULTED"


def test_neutral_reparse_preserves_invalid_json_failure(tmp_path: Path) -> None:
    request_hash = "c" * 64
    cache = tmp_path / "cc"
    cache.mkdir()
    (cache / f"{request_hash}.json").write_text(
        json.dumps({"content": '{"entities":[', "raw_output_hash": "d" * 64}), encoding="utf-8"
    )
    row = {
        "id": "q1",
        "gold": {"id": "q1", "text": "雷达", "entities": [], "relations": []},
        "attempts": [{"request_hash": request_hash}],
    }
    result = reparse_row(row, tmp_path)
    assert result["parse_failure"] is True
    assert "invalid JSON" in result["attempt_errors_before_acceptance"][0]
