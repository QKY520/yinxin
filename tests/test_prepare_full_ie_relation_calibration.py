from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "prepare_full_ie_relation_calibration.py"
)
SPEC = importlib.util.spec_from_file_location(
    "prepare_full_ie_relation_calibration", SCRIPT_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class PrepareFullIERelationCalibrationTests(unittest.TestCase):
    def entity(self, text: str, span: str, entity_type: str) -> dict[str, object]:
        start = text.index(span)
        return {
            "start": start,
            "end": start + len(span),
            "type": entity_type,
            "span": span,
        }

    def write_csv(self, path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=MODULE.INPUT_CSV_FIELDS,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    def digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def make_fixture(
        self, root: Path
    ) -> tuple[
        object,
        dict[str, str],
        list[dict[str, str]],
        list[dict[str, str]],
        list[dict[str, str]],
    ]:
        texts = [
            "苍穹无人机搭载雷达。",
            "海岳雷达包含处理模块。",
            "导航系统射程100公里。",
            "北辰平台采用惯性制导技术。",
        ]
        entities = {
            texts[0]: [
                self.entity(texts[0], "苍穹无人机", "EQUIPMENT"),
                self.entity(texts[0], "雷达", "MODULE"),
            ],
            texts[1]: [
                self.entity(texts[1], "海岳雷达", "EQUIPMENT"),
                self.entity(texts[1], "处理模块", "MODULE"),
            ],
            texts[2]: [
                self.entity(texts[2], "导航系统", "EQUIPMENT"),
                self.entity(texts[2], "射程100公里", "METRIC"),
            ],
            texts[3]: [
                self.entity(texts[3], "北辰平台", "EQUIPMENT"),
                self.entity(texts[3], "惯性制导技术", "TECH_SCHEME"),
            ],
        }
        a_order = [0, 1, 2, 3]
        b_order = [2, 0, 3, 1]
        a_rows: list[dict[str, str]] = []
        b_rows: list[dict[str, str]] = []
        a_ids: dict[str, str] = {}
        b_ids: dict[str, str] = {}
        for position, text_index in enumerate(a_order, start=1):
            text = texts[text_index]
            blind_id = f"P6FRESH-A-{position:03d}"
            a_ids[text] = blind_id
            a_rows.append(
                {
                    "blind_id": blind_id,
                    "text": text,
                    "entities_json": json.dumps(
                        entities[text], ensure_ascii=False, separators=(",", ":")
                    ),
                    "notes": f"PRIVATE-A-NOTE-{position}",
                    "uncertainty_code": "OLD_ENTITY_CODE",
                }
            )
        for position, text_index in enumerate(b_order, start=1):
            text = texts[text_index]
            blind_id = f"P6FRESH-B-{position:03d}"
            b_ids[text] = blind_id
            b_entities = entities[text][:-1] if text_index == 0 else entities[text]
            b_rows.append(
                {
                    "blind_id": blind_id,
                    "text": text,
                    "entities_json": json.dumps(b_entities, ensure_ascii=False),
                    "notes": f"PRIVATE-B-NOTE-{position}",
                    "uncertainty_code": "",
                }
            )

        map_rows = [
            {
                "original_id": f"synthetic-{index:02d}",
                "annotator_a_blind_id": a_ids[text],
                "annotator_b_blind_id": b_ids[text],
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "selection_bucket": "SYNTHETIC",
            }
            for index, text in enumerate(texts, start=1)
        ]

        source = root / "locked_inputs"
        docs = root / "docs"
        source.mkdir(parents=True)
        docs.mkdir(parents=True)
        a_path = source / "annotator_a.csv"
        b_path = source / "annotator_b.csv"
        map_path = source / "coordinator_map.jsonl"
        self.write_csv(a_path, a_rows)
        self.write_csv(b_path, b_rows)
        with map_path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in map_rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

        guideline = docs / MODULE.GUIDELINE_NAME
        a_instructions = docs / MODULE.A_INSTRUCTIONS_NAME
        b_instructions = docs / MODULE.B_INSTRUCTIONS_NAME
        guideline.write_text("synthetic locked guideline\n", encoding="utf-8")
        a_instructions.write_text("synthetic A instructions\n", encoding="utf-8")
        b_instructions.write_text("synthetic B instructions\n", encoding="utf-8")
        config = MODULE.RelationCalibrationConfig(
            annotator_a_entities=a_path,
            annotator_b_entities=b_path,
            coordinator_map=map_path,
            guideline=guideline,
            annotator_a_instructions=a_instructions,
            annotator_b_instructions=b_instructions,
            output_dir=root / "backup" / "relation_calibration",
        )
        hashes = {
            "a": self.digest(a_path),
            "b": self.digest(b_path),
            "map": self.digest(map_path),
            "guideline": self.digest(guideline),
            "a_instructions": self.digest(a_instructions),
            "b_instructions": self.digest(b_instructions),
        }
        return config, hashes, a_rows, b_rows, map_rows

    def prepare(
        self,
        config: object,
        hashes: dict[str, str],
        **overrides: object,
    ) -> dict[str, object]:
        kwargs: dict[str, object] = {
            "expected_a_sha256": hashes["a"],
            "expected_b_sha256": hashes["b"],
            "expected_coordinator_map_sha256": hashes["map"],
            "expected_guideline_sha256": hashes["guideline"],
            "expected_a_instructions_sha256": hashes["a_instructions"],
            "expected_b_instructions_sha256": hashes["b_instructions"],
            "expected_rows": 4,
        }
        kwargs.update(overrides)
        with mock.patch.dict(os.environ, {MODULE.GATE_NAME: "1"}, clear=False):
            return MODULE.prepare_relation_calibration(config, **kwargs)

    def audit(
        self, config: object, hashes: dict[str, str]
    ) -> dict[str, object]:
        with mock.patch.dict(os.environ, {MODULE.GATE_NAME: "1"}, clear=False):
            return MODULE.audit_relation_calibration(
                config,
                expected_a_sha256=hashes["a"],
                expected_b_sha256=hashes["b"],
                expected_coordinator_map_sha256=hashes["map"],
                expected_guideline_sha256=hashes["guideline"],
                expected_a_instructions_sha256=hashes["a_instructions"],
                expected_b_instructions_sha256=hashes["b_instructions"],
                expected_rows=4,
            )

    def rewrite_map(self, path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def test_prepares_blank_isolated_packages_and_preserves_entity_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, a_source, b_source, _ = self.make_fixture(root)
            manifest = self.prepare(config, hashes)

            self.assertEqual(manifest["status"], "prepared_blank_not_started")
            self.assertFalse(manifest["scope"]["annotation_started"])
            self.assertFalse(manifest["scope"]["domain_test_read"])
            self.assertFalse(manifest["scope"]["model_or_api_calls"])
            self.assertFalse(manifest["scope"]["gpu_used"])
            self.assertEqual(
                manifest["next_gate"],
                "FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED",
            )

            a_delivery = config.output_dir / "annotator_a_delivery"
            b_delivery = config.output_dir / "annotator_b_delivery"
            coordinator = config.output_dir / "coordinator_only"
            a_rows = self.read_csv(a_delivery / MODULE.A_SHEET_NAME)
            b_rows = self.read_csv(b_delivery / MODULE.B_SHEET_NAME)
            self.assertEqual(tuple(a_rows[0]), MODULE.OUTPUT_CSV_FIELDS)
            self.assertEqual(
                [row["text"] for row in a_rows], [row["text"] for row in a_source]
            )
            self.assertEqual(
                [row["text"] for row in b_rows], [row["text"] for row in b_source]
            )
            self.assertNotEqual(
                [row["text"] for row in a_rows], [row["text"] for row in b_rows]
            )

            for output_rows, source_rows in ((a_rows, a_source), (b_rows, b_source)):
                source_by_id = {row["blind_id"]: row for row in source_rows}
                for row in output_rows:
                    self.assertEqual(
                        row["entities_json_locked"],
                        source_by_id[row["blind_id"]]["entities_json"],
                    )
                    self.assertTrue(row["entity_index_guide"].startswith("[0]"))
                    self.assertEqual(row["relations_json"], "")
                    self.assertEqual(row["relation_notes"], "")
                    self.assertEqual(row["relation_uncertainty_code"], "")

            a_files = {path.name for path in a_delivery.iterdir()}
            b_files = {path.name for path in b_delivery.iterdir()}
            self.assertEqual(
                a_files,
                {
                    MODULE.A_SHEET_NAME,
                    MODULE.GUIDELINE_NAME,
                    MODULE.A_INSTRUCTIONS_NAME,
                    "delivery_manifest.json",
                },
            )
            self.assertEqual(
                b_files,
                {
                    MODULE.B_SHEET_NAME,
                    MODULE.GUIDELINE_NAME,
                    MODULE.B_INSTRUCTIONS_NAME,
                    "delivery_manifest.json",
                },
            )
            self.assertFalse((a_delivery / MODULE.B_SHEET_NAME).exists())
            self.assertFalse((b_delivery / MODULE.A_SHEET_NAME).exists())
            self.assertFalse((a_delivery / MODULE.COORDINATOR_MAP_NAME).exists())
            self.assertFalse((b_delivery / MODULE.COORDINATOR_MAP_NAME).exists())
            self.assertTrue((coordinator / MODULE.COORDINATOR_MAP_NAME).exists())

            a_bytes = (a_delivery / MODULE.A_SHEET_NAME).read_bytes()
            b_bytes = (b_delivery / MODULE.B_SHEET_NAME).read_bytes()
            self.assertNotIn(b"PRIVATE-A-NOTE", a_bytes)
            self.assertNotIn(b"PRIVATE-B-NOTE", b_bytes)
            a_manifest = json.loads(
                (a_delivery / "delivery_manifest.json").read_text(encoding="utf-8")
            )
            b_manifest = json.loads(
                (b_delivery / "delivery_manifest.json").read_text(encoding="utf-8")
            )
            self.assertFalse(a_manifest["annotation_authorized"])
            self.assertFalse(b_manifest["annotation_authorized"])
            self.assertEqual(a_manifest["records"], 4)
            self.assertEqual(b_manifest["records"], 4)
            audit = self.audit(config, hashes)
            self.assertEqual(audit["status"], "passed")
            self.assertEqual(audit["blank_relation_rows"], 8)
            self.assertTrue(audit["locked_entity_cells_preserved"])

    def test_requires_exact_gate_and_rejects_domain_test_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, _, _, _ = self.make_fixture(root)
            with mock.patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(PermissionError, MODULE.GATE_NAME):
                    MODULE.prepare_relation_calibration(
                        config,
                        expected_a_sha256=hashes["a"],
                        expected_b_sha256=hashes["b"],
                        expected_coordinator_map_sha256=hashes["map"],
                        expected_guideline_sha256=hashes["guideline"],
                        expected_a_instructions_sha256=hashes["a_instructions"],
                        expected_b_instructions_sha256=hashes["b_instructions"],
                        expected_rows=4,
                    )

            forbidden_config = MODULE.RelationCalibrationConfig(
                annotator_a_entities=config.annotator_a_entities,
                annotator_b_entities=config.annotator_b_entities,
                coordinator_map=config.coordinator_map,
                guideline=config.guideline,
                annotator_a_instructions=config.annotator_a_instructions,
                annotator_b_instructions=config.annotator_b_instructions,
                output_dir=root / "domain_test_outputs",
            )
            with self.assertRaisesRegex(ValueError, "domain_test"):
                self.prepare(forbidden_config, hashes)

    def test_rejects_each_locked_input_hash_mismatch(self) -> None:
        cases = (
            ("expected_a_sha256", "annotator A locked entities"),
            ("expected_b_sha256", "annotator B locked entities"),
            ("expected_coordinator_map_sha256", "coordinator map"),
        )
        for argument, message in cases:
            with self.subTest(argument=argument):
                with tempfile.TemporaryDirectory() as temporary:
                    config, hashes, _, _, _ = self.make_fixture(Path(temporary))
                    with self.assertRaisesRegex(ValueError, message):
                        self.prepare(config, hashes, **{argument: "0" * 64})

    def test_rejects_misalignment_unknown_ids_and_invalid_entities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, _, _, map_rows = self.make_fixture(root)
            swapped = [dict(row) for row in map_rows]
            swapped[0]["text_sha256"], swapped[1]["text_sha256"] = (
                swapped[1]["text_sha256"],
                swapped[0]["text_sha256"],
            )
            self.rewrite_map(config.coordinator_map, swapped)
            hashes["map"] = self.digest(config.coordinator_map)
            with self.assertRaisesRegex(ValueError, "aligned text mismatch"):
                self.prepare(config, hashes)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, _, _, map_rows = self.make_fixture(root)
            unknown = [dict(row) for row in map_rows]
            unknown[0]["annotator_b_blind_id"] = "P6FRESH-B-999"
            self.rewrite_map(config.coordinator_map, unknown)
            hashes["map"] = self.digest(config.coordinator_map)
            with self.assertRaisesRegex(ValueError, "unknown annotator blind ID"):
                self.prepare(config, hashes)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, a_rows, _, _ = self.make_fixture(root)
            malformed = json.loads(a_rows[0]["entities_json"])
            malformed[0]["span"] = "错误词面"
            a_rows[0]["entities_json"] = json.dumps(malformed, ensure_ascii=False)
            self.write_csv(config.annotator_a_entities, a_rows)
            hashes["a"] = self.digest(config.annotator_a_entities)
            with self.assertRaisesRegex(ValueError, "span does not match"):
                self.prepare(config, hashes)

    def test_refuses_to_overwrite_existing_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, _, _, _ = self.make_fixture(root)
            self.prepare(config, hashes)
            with self.assertRaises(FileExistsError):
                self.prepare(config, hashes)

    def test_audit_rejects_a_tampered_delivery_sheet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config, hashes, _, _, _ = self.make_fixture(root)
            self.prepare(config, hashes)
            sheet = (
                config.output_dir
                / "annotator_a_delivery"
                / MODULE.A_SHEET_NAME
            )
            rows = self.read_csv(sheet)
            rows[0]["relations_json"] = "[]"
            with sheet.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=MODULE.OUTPUT_CSV_FIELDS,
                    quoting=csv.QUOTE_ALL,
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "does not match locked"):
                self.audit(config, hashes)


if __name__ == "__main__":
    unittest.main()
