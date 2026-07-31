from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie import DEFAULT_RELATION_TYPES  # noqa: E402
from equipment_ie.full_ie_f3 import (  # noqa: E402
    CLUENER_ENTITY_TYPES,
    F3_GATE,
    build_labels_stripped_rag_corpus,
    build_support_glossary,
    prepare_f3_package,
    select_coverage_records,
    validate_f3_manifest,
)
from equipment_ie import full_ie_f3  # noqa: E402


def make_record(record_id: str, entity_type: str) -> dict:
    digest = hashlib.sha256(record_id.encode("utf-8")).hexdigest()
    span = digest[:10]
    text = f"{span}{digest[10:]}"
    return {
        "id": record_id,
        "text": text,
        "entities": [
            {
                "start": 0,
                "end": len(span),
                "type": entity_type,
                "span": span,
            }
        ],
        "relations": [],
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


class FullIEF3Test(unittest.TestCase):
    def test_final_dev_blocklist_discards_gold_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cluener_dev.jsonl"
            write_jsonl(path, [make_record("dev-1", "name")])
            self.assertEqual(
                full_ie_f3._load_text_blocklist(path),
                [{"id": "dev-1", "text": make_record("dev-1", "name")["text"]}],
            )

    def test_coverage_selection_is_deterministic_and_covers_all_types(self) -> None:
        types = tuple(CLUENER_ENTITY_TYPES)
        rows = [make_record(f"train-{index}", types[index % len(types)]) for index in range(80)]
        first = select_coverage_records(rows, size=30, seed=42, required_types=types)
        second = select_coverage_records(rows, size=30, seed=42, required_types=types)
        self.assertEqual([row["id"] for row in first], [row["id"] for row in second])
        self.assertEqual(len(first), 30)
        self.assertEqual(
            {entity["type"] for row in first for entity in row["entities"]},
            set(types),
        )

    def test_support_glossary_omits_type_conflicts(self) -> None:
        rows = [make_record("a", "name"), make_record("b", "book")]
        rows[0]["entities"][0]["span"] = "共享词"
        rows[0]["entities"][0]["end"] = 3
        rows[0]["text"] = "共享词甲"
        rows[1]["entities"][0]["span"] = "共享词"
        rows[1]["entities"][0]["end"] = 3
        rows[1]["text"] = "共享词乙"
        unique = make_record("c", "name")
        glossary, report = build_support_glossary([*rows, unique])
        self.assertNotIn("共享词", {row["term"] for row in glossary})
        self.assertEqual(report["conflicting_surfaces_omitted"], 1)

    def test_rag_corpus_strips_labels_and_removes_blocked_overlap(self) -> None:
        kept = make_record("train-keep", "name")
        support = make_record("train-support", "book")
        near_duplicate = make_record("train-near", "scene")
        blocked = make_record("dev-block", "company")
        near_duplicate["text"] = blocked["text"]
        rag, report = build_labels_stripped_rag_corpus(
            [kept, support, near_duplicate],
            support_records=[support],
            tune_records=[],
            evaluation_blocklist_records=[blocked],
        )
        self.assertEqual([row["id"] for row in rag], ["train-keep"])
        self.assertNotIn("entities", rag[0])
        self.assertNotIn("relations", rag[0])
        self.assertEqual(report["removed_count"], 2)

    def test_complete_package_is_unauthorized_hash_valid_and_has_12_cells(self) -> None:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - environment contract
            self.fail(f"pyyaml unavailable: {exc}")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            domain_types = ("EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC")
            domain_support = root / "domain_support.jsonl"
            domain_dev = root / "domain_dev.jsonl"
            write_jsonl(
                domain_support,
                [make_record(f"domain-support-{index}", domain_types[index % 4]) for index in range(30)],
            )
            write_jsonl(
                domain_dev,
                [make_record(f"domain-dev-{index}", domain_types[index % 4]) for index in range(50)],
            )
            domain_glossary = root / "domain_dict.jsonl"
            write_jsonl(
                domain_glossary,
                [{"term": "装备", "type": "EQUIPMENT", "source": "synthetic"}],
            )
            domain_rag = root / "domain_rag_corpus.jsonl"
            write_jsonl(domain_rag, [{"id": "rag-1", "text": "合成装备参考资料"}])
            domain_schema = root / "domain_schema.yaml"
            domain_schema.write_text(
                yaml.safe_dump(
                    {
                        "entity_types": {
                            name: {"definition": f"synthetic {name}"}
                            for name in domain_types
                        },
                        "relation_types": DEFAULT_RELATION_TYPES,
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            cluener_types = tuple(CLUENER_ENTITY_TYPES)
            train_pool = root / "cluener_train_pool.jsonl"
            tune = root / "cluener_tune.jsonl"
            dev = root / "cluener_dev.jsonl"
            write_jsonl(
                train_pool,
                [make_record(f"train-{index}", cluener_types[index % 10]) for index in range(80)],
            )
            write_jsonl(
                tune,
                [make_record(f"tune-{index}", cluener_types[index % 10]) for index in range(60)],
            )
            write_jsonl(
                dev,
                [make_record(f"dev-{index}", cluener_types[index % 10]) for index in range(20)],
            )
            artifact_root = root / "artifacts"
            with patch("equipment_ie.full_ie_f3.gpu_visible", return_value=False):
                report = prepare_f3_package(
                    human_gate=F3_GATE,
                    domain_support_path=domain_support,
                    domain_dev_path=domain_dev,
                    domain_glossary_path=domain_glossary,
                    domain_rag_corpus_path=domain_rag,
                    domain_schema_path=domain_schema,
                    cluener_train_pool_path=train_pool,
                    cluener_tune_path=tune,
                    cluener_dev_blocklist_path=dev,
                    resource_root=root / "resources",
                    config_root=root / "configs",
                    artifact_root=artifact_root,
                )
            validation = validate_f3_manifest(artifact_root / "f3_manifest.json")
            self.assertEqual(report["reported_dev_tune_cells"], 12)
            self.assertEqual(report["runner_configs"], 16)
            self.assertEqual(validation["status"], "ok")
            self.assertTrue(validation["config_validation"]["all_configs_unauthorized"])
            self.assertFalse(any(artifact_root.rglob("*prompts*")))


if __name__ == "__main__":
    unittest.main()
