from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.domain_data import (  # noqa: E402
    chunk_text,
    extract_seed_terms,
    iter_json_object_values,
    match_seed_entities,
    ngram_containment,
    normalized_ngrams,
    prelabel_candidate,
    select_quotas_with_dedup,
)


def candidate(source_type: str, suffix: str, text: str, score: int = 1) -> dict:
    from equipment_ie.domain_data import text_sha256

    return {
        "source_candidate_id": f"{source_type}-{suffix}",
        "text": text,
        "source_type": source_type,
        "source_id": suffix,
        "source_split": "test",
        "source_url": "https://example.test",
        "source_revision": "rev",
        "source_license": "MIT",
        "title": suffix,
        "selection_score": score,
        "content_sha256": text_sha256(text),
    }


class DomainDataTest(unittest.TestCase):
    def test_chunk_text_respects_bounds(self) -> None:
        text = "甲" * 90 + "。" + "乙" * 90 + "。" + "丙" * 90 + "。"
        chunks = chunk_text(text, min_chars=100, max_chars=200)
        self.assertTrue(chunks)
        self.assertTrue(all(100 <= len(chunk) <= 200 for chunk in chunks))

    def test_ngram_containment_detects_near_duplicate(self) -> None:
        left = normalized_ngrams("甲乙丙丁戊己庚辛壬癸", 8)
        right = normalized_ngrams("甲乙丙丁戊己庚辛壬癸甲", 8)
        self.assertGreaterEqual(ngram_containment(left, right), 0.8)

    def test_extract_seed_terms_deduplicates_names(self) -> None:
        rows = [
            {"_id": {"$oid": "1"}, "名称": "雷达甲", "大类": "电子", "类型": "雷达"},
            {"_id": {"$oid": "2"}, "名称": "雷达甲", "大类": "电子", "类型": "雷达"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "military.json"
            path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            terms = extract_seed_terms(path, "revision")
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0]["term"], "雷达甲")

    def test_json_object_values_supports_patent_test_format(self) -> None:
        value = {"CN1": {"body": {"title": "甲"}}, "CN2": {"body": {"title": "乙"}}}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.json"
            path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            rows = list(iter_json_object_values(path))
        self.assertEqual([row["body"]["title"] for row in rows], ["甲", "乙"])

    def test_seed_matching_prefers_longest_nonoverlap(self) -> None:
        entities = match_seed_entities("歼-20战斗机采用雷达。", ["歼-20", "战斗机", "歼-20战斗机"])
        self.assertEqual(
            [(entity["span"], entity["start"], entity["end"]) for entity in entities],
            [("歼-20战斗机", 0, 7)],
        )

    def test_prelabel_is_valid_unified_record(self) -> None:
        row = {"id": "c1", "text": "某型雷达甲用于目标探测。"}
        record = prelabel_candidate(row, ["雷达甲"])
        self.assertEqual(record["entities"][0]["span"], "雷达甲")

    def test_quota_selection_is_deterministic_and_deduplicated(self) -> None:
        base = "甲" * 100
        pools = {
            "baidu_baike": [candidate("baidu_baike", "1", base)],
            "patent": [candidate("patent", "1", "乙" * 100)],
            "cmnee": [
                candidate("cmnee", "duplicate", "乙" * 100, score=2),
                candidate("cmnee", "unique", "丙" * 100),
            ],
        }
        quotas = {"baidu_baike": 1, "patent": 1, "cmnee": 1}
        first, removed = select_quotas_with_dedup(
            pools, quotas, seed=42, ngram_size=8, containment_threshold=0.8
        )
        second, _ = select_quotas_with_dedup(
            pools, quotas, seed=42, ngram_size=8, containment_threshold=0.8
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertEqual(len(removed), 1)


if __name__ == "__main__":
    unittest.main()
