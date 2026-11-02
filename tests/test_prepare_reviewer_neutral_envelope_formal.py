from scripts.prepare_reviewer_neutral_envelope_formal import bm25_rows, grams


def test_chinese_bigram_tokenization_is_deterministic() -> None:
    assert grams("雷达 系统") == ["雷达", "达系", "系统"]


def test_okapi_bm25_prefers_matching_passage() -> None:
    queries = [{"id": "q1", "text": "雷达系统"}]
    passages = [
        {"id": "p1", "text": "烹饪设备", "display": "p1"},
        {"id": "p2", "text": "相控阵雷达系统", "display": "p2"},
        {"id": "p3", "text": "其他装备", "display": "p3"},
    ]
    rows = bm25_rows(queries, passages)
    assert rows[0]["selected_passages"][0]["id"] == "p2"
