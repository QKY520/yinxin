from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.schema import (  # noqa: E402
    SchemaError,
    iter_jsonl,
    validate_record,
    write_jsonl_atomic,
)


def record() -> dict[str, object]:
    return {
        "id": "sample-1",
        "text": "甲使用乙",
        "entities": [
            {"start": 0, "end": 1, "type": "A", "span": "甲"},
            {"start": 3, "end": 4, "type": "B", "span": "乙"},
        ],
        "relations": [{"head": 0, "tail": 1, "type": "USES"}],
    }


class SchemaTest(unittest.TestCase):
    def test_valid_record(self) -> None:
        validate_record(record())

    def test_span_mismatch_fails(self) -> None:
        value = record()
        value["entities"][0]["span"] = "乙"  # type: ignore[index]
        with self.assertRaisesRegex(SchemaError, "span does not equal"):
            validate_record(value)

    def test_relation_index_fails(self) -> None:
        value = record()
        value["relations"][0]["tail"] = 2  # type: ignore[index]
        with self.assertRaisesRegex(SchemaError, "missing entity"):
            validate_record(value)

    def test_duplicate_id_does_not_replace_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            sentinel = '{"sentinel":true}\n'
            path.write_text(sentinel, encoding="utf-8")
            with self.assertRaisesRegex(SchemaError, "duplicate record id"):
                write_jsonl_atomic(path, [record(), record()])
            self.assertEqual(path.read_text(encoding="utf-8"), sentinel)

    def test_jsonl_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "records.jsonl"
            counts = write_jsonl_atomic(path, [record()])
            self.assertEqual(counts, {"records": 1, "entities": 2, "relations": 1})
            self.assertEqual(list(iter_jsonl(path)), [record()])
            parsed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(parsed["id"], "sample-1")


if __name__ == "__main__":
    unittest.main()
