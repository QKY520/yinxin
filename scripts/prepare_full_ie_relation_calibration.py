#!/usr/bin/env python3
"""Prepare isolated, relation-only calibration sheets from locked P6 entities.

Run only on AutoDL in GPU-free mode under the explicit preparation gate. The
script consumes the two previously locked human entity submissions and their
coordinator map. It never reads domain_test, model outputs, prompts, or relation
labels, and it leaves all relation annotation fields blank.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


GATE_NAME = "FULL_IE_RELATION_CALIBRATION_PREP_APPROVED"
EXPECTED_A_SHA256 = (
    "6906142d5894c3a4f1332bed326258b4f9c35958baa17f8e8475339b435f8877"
)
EXPECTED_B_SHA256 = (
    "40428a8ed642685dd7940c60e3dc08af929dcaa4e71c0b7530e89eaa7dbb732e"
)
EXPECTED_COORDINATOR_MAP_SHA256 = (
    "6a902ab6e2063b52c1d8103cf777ed25dc2def31371a3f26866f51d3d9664e18"
)
EXPECTED_GUIDELINE_SHA256 = (
    "912b0949cc0abf9937725162220f7dc7771a288f54f114e30b5b2366c2197072"
)
EXPECTED_A_INSTRUCTIONS_SHA256 = (
    "b5df8f426686ac594610bb4660158b34320605245315a01e4527fd0ec8cf5b21"
)
EXPECTED_B_INSTRUCTIONS_SHA256 = (
    "cbd22cb14ddc884e1b51bc920208920f24077c67223545e0d3e27acf0589b5d9"
)
EXPECTED_ROWS = 20
INPUT_CSV_FIELDS = (
    "blind_id",
    "text",
    "entities_json",
    "notes",
    "uncertainty_code",
)
OUTPUT_CSV_FIELDS = (
    "blind_id",
    "text",
    "entities_json_locked",
    "entity_index_guide",
    "relations_json",
    "relation_notes",
    "relation_uncertainty_code",
)
MAP_FIELDS = {
    "original_id",
    "annotator_a_blind_id",
    "annotator_b_blind_id",
    "text_sha256",
    "selection_bucket",
}
ENTITY_FIELDS = {"start", "end", "type", "span"}
ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
GUIDELINE_NAME = "FULL_IE_RELATION_CALIBRATION_GUIDELINE_V1_20260730.md"
A_INSTRUCTIONS_NAME = (
    "FULL_IE_RELATION_CALIBRATION_ANNOTATOR_A_INSTRUCTIONS_20260730.md"
)
B_INSTRUCTIONS_NAME = (
    "FULL_IE_RELATION_CALIBRATION_ANNOTATOR_B_INSTRUCTIONS_20260730.md"
)
A_SHEET_NAME = "annotator_a_relation_calibration.csv"
B_SHEET_NAME = "annotator_b_relation_calibration.csv"
COORDINATOR_MAP_NAME = "relation_calibration_map.jsonl"


@dataclass(frozen=True)
class RelationCalibrationConfig:
    annotator_a_entities: Path
    annotator_b_entities: Path
    coordinator_map: Path
    guideline: Path
    annotator_a_instructions: Path
    annotator_b_instructions: Path
    output_dir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare isolated FULL-IE relation calibration sheets."
    )
    source_root = (
        "/root/autodl-tmp/backup/p6/"
        "p6_qa1r_fresh_calibration_validation_inputs_20260727_r2"
    )
    parser.add_argument(
        "--annotator-a-entities",
        default=f"{source_root}/annotator_a_fresh_calibration_completed.csv",
    )
    parser.add_argument(
        "--annotator-b-entities",
        default=f"{source_root}/annotator_b_fresh_calibration_completed.csv",
    )
    parser.add_argument(
        "--coordinator-map",
        default=(
            "/root/autodl-tmp/backup/p6/"
            "p6_qa1r_fresh_calibration_20260727/coordinator_only/"
            "coordinator_map.jsonl"
        ),
    )
    parser.add_argument(
        "--guideline", default=f"/root/project/docs/{GUIDELINE_NAME}"
    )
    parser.add_argument(
        "--annotator-a-instructions",
        default=f"/root/project/docs/{A_INSTRUCTIONS_NAME}",
    )
    parser.add_argument(
        "--annotator-b-instructions",
        default=f"/root/project/docs/{B_INSTRUCTIONS_NAME}",
    )
    parser.add_argument(
        "--output-dir",
        default="/root/autodl-tmp/backup/full_ie/f2_relation_calibration_20260730",
    )
    parser.add_argument(
        "--audit-only",
        action="store_true",
        help="Read and validate an existing prepared package without changing it.",
    )
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA256 mismatch: expected {expected}, got {actual}")


def require_gate() -> None:
    if os.environ.get(GATE_NAME) != "1":
        raise PermissionError(f"set {GATE_NAME}=1 for this bounded preparation gate")


def reject_domain_test_path(path: Path, label: str) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if "domain_test" in normalized:
        raise ValueError(f"{label} must not reference domain_test")


def validate_entities(
    entities_json: str, text: str, *, role: str, blind_id: str
) -> list[dict[str, Any]]:
    try:
        entities = json.loads(entities_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{role} {blind_id} entities_json is invalid JSON") from exc
    if not isinstance(entities, list):
        raise ValueError(f"{role} {blind_id} entities_json must be an array")

    seen: set[tuple[int, int, str]] = set()
    for index, entity in enumerate(entities):
        prefix = f"{role} {blind_id} entity {index}"
        if not isinstance(entity, dict) or set(entity) != ENTITY_FIELDS:
            raise ValueError(f"{prefix} fields must equal {sorted(ENTITY_FIELDS)}")
        start = entity["start"]
        end = entity["end"]
        entity_type = entity["type"]
        span = entity["span"]
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or end > len(text)
        ):
            raise ValueError(f"{prefix} has invalid offsets")
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"{prefix} has invalid type {entity_type!r}")
        if not isinstance(span, str) or not span or text[start:end] != span:
            raise ValueError(f"{prefix} span does not match text offsets")
        key = (start, end, entity_type)
        if key in seen:
            raise ValueError(f"{role} {blind_id} has a duplicate entity")
        seen.add(key)
    return entities


def read_locked_entities(
    path: Path,
    *,
    role: str,
    expected_sha256: str,
    expected_rows: int,
) -> list[dict[str, Any]]:
    require_hash(path, expected_sha256, f"annotator {role} locked entities")
    rows: list[dict[str, Any]] = []
    expected_prefix = f"P6FRESH-{role}-"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != INPUT_CSV_FIELDS:
            raise ValueError(f"annotator {role} CSV field mismatch")
        for row_number, row in enumerate(reader, start=2):
            if set(row) != set(INPUT_CSV_FIELDS) or any(
                row[field] is None for field in INPUT_CSV_FIELDS
            ):
                raise ValueError(f"annotator {role} malformed CSV row {row_number}")
            blind_id = row["blind_id"]
            text = row["text"]
            entities_json = row["entities_json"]
            if not blind_id.startswith(expected_prefix):
                raise ValueError(f"annotator {role} invalid blind ID at row {row_number}")
            if not text or "\x00" in text or text.startswith(FORMULA_PREFIXES):
                raise ValueError(f"annotator {role} invalid text at row {row_number}")
            if not entities_json:
                raise ValueError(
                    f"annotator {role} missing locked entities at row {row_number}"
                )
            entities = validate_entities(
                entities_json, text, role=role, blind_id=blind_id
            )
            rows.append(
                {
                    "blind_id": blind_id,
                    "text": text,
                    "text_sha256": sha256_text(text),
                    "entities_json": entities_json,
                    "entities_sha256": sha256_text(entities_json),
                    "entities": entities,
                }
            )
    if len(rows) != expected_rows:
        raise ValueError(
            f"annotator {role} expected {expected_rows} rows, got {len(rows)}"
        )
    blind_ids = [row["blind_id"] for row in rows]
    text_hashes = [row["text_sha256"] for row in rows]
    if len(set(blind_ids)) != len(blind_ids):
        raise ValueError(f"annotator {role} contains duplicate blind IDs")
    if len(set(text_hashes)) != len(text_hashes):
        raise ValueError(f"annotator {role} contains duplicate texts")
    return rows


def read_coordinator_map(
    path: Path, *, expected_sha256: str, expected_rows: int
) -> list[dict[str, str]]:
    require_hash(path, expected_sha256, "coordinator map")
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank coordinator-map line {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != MAP_FIELDS:
                raise ValueError(f"coordinator-map field mismatch at line {line_number}")
            if not all(isinstance(row[field], str) and row[field] for field in MAP_FIELDS):
                raise ValueError(f"coordinator-map value mismatch at line {line_number}")
            digest = row["text_sha256"]
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError(f"invalid coordinator text hash at line {line_number}")
            rows.append(row)
    if len(rows) != expected_rows:
        raise ValueError(f"coordinator map expected {expected_rows} rows, got {len(rows)}")
    for field in (
        "original_id",
        "annotator_a_blind_id",
        "annotator_b_blind_id",
        "text_sha256",
    ):
        values = [row[field] for row in rows]
        if len(set(values)) != len(values):
            raise ValueError(f"coordinator map contains duplicate {field}")
    return rows


def validate_alignment(
    a_rows: list[dict[str, Any]],
    b_rows: list[dict[str, Any]],
    map_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    a_by_id = {row["blind_id"]: row for row in a_rows}
    b_by_id = {row["blind_id"]: row for row in b_rows}
    used_a: set[str] = set()
    used_b: set[str] = set()
    aligned: list[dict[str, Any]] = []
    for map_row in map_rows:
        a_id = map_row["annotator_a_blind_id"]
        b_id = map_row["annotator_b_blind_id"]
        if a_id not in a_by_id or b_id not in b_by_id:
            raise ValueError("coordinator map references an unknown annotator blind ID")
        a_row = a_by_id[a_id]
        b_row = b_by_id[b_id]
        expected_text_hash = map_row["text_sha256"]
        if (
            a_row["text_sha256"] != expected_text_hash
            or b_row["text_sha256"] != expected_text_hash
            or a_row["text"] != b_row["text"]
        ):
            raise ValueError(f"aligned text mismatch for {map_row['original_id']}")
        used_a.add(a_id)
        used_b.add(b_id)
        aligned.append(
            {
                **map_row,
                "annotator_a_entities_sha256": a_row["entities_sha256"],
                "annotator_b_entities_sha256": b_row["entities_sha256"],
                "annotator_a_entity_count": len(a_row["entities"]),
                "annotator_b_entity_count": len(b_row["entities"]),
            }
        )
    if used_a != set(a_by_id) or used_b != set(b_by_id):
        raise ValueError("coordinator map does not cover every annotator row exactly once")
    return aligned


def make_entity_index_guide(entities: list[dict[str, Any]]) -> str:
    if not entities:
        return "(none)"
    return " || ".join(
        f"[{index}] {entity['type']} | {entity['span']}"
        for index, entity in enumerate(entities)
    )


def make_delivery_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "blind_id": row["blind_id"],
            "text": row["text"],
            "entities_json_locked": row["entities_json"],
            "entity_index_guide": make_entity_index_guide(row["entities"]),
            "relations_json": "",
            "relation_notes": "",
            "relation_uncertainty_code": "",
        }
        for row in rows
    ]


def csv_payload(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=OUTPUT_CSV_FIELDS,
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def json_payload(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def jsonl_payload(rows: list[dict[str, Any]]) -> bytes:
    return (
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in rows
        )
        + "\n"
    ).encode("utf-8")


def write_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{uuid4().hex}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def file_metadata(
    path: Path, *, relative_path: str, role: str, rows: int | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": relative_path,
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if rows is not None:
        result["rows"] = rows
    return result


def delivery_manifest(
    *,
    role: str,
    sheet: Path,
    sheet_name: str,
    guideline: Path,
    instructions: Path,
    instructions_name: str,
    source_sha256: str,
    rows: int,
) -> dict[str, Any]:
    return {
        "phase": "FULL-IE-F2-RELATION-CALIBRATION-PREP",
        "gate": GATE_NAME,
        "role": f"annotator_{role.lower()}_only",
        "status": "prepared_blank_not_started",
        "records": rows,
        "task": "exact_directed_relation_annotation",
        "locked_entity_source_sha256": source_sha256,
        "csv_fields": list(OUTPUT_CSV_FIELDS),
        "read_only_fields": list(OUTPUT_CSV_FIELDS[:4]),
        "editable_after_next_gate": list(OUTPUT_CSV_FIELDS[4:]),
        "files": {
            "sheet": file_metadata(
                sheet,
                relative_path=sheet_name,
                role=f"annotator_{role.lower()}_only",
                rows=rows,
            ),
            "guideline": file_metadata(
                guideline,
                relative_path=GUIDELINE_NAME,
                role="shared_locked_guideline",
            ),
            "instructions": file_metadata(
                instructions,
                relative_path=instructions_name,
                role=f"annotator_{role.lower()}_only",
            ),
        },
        "forbidden": [
            f"annotator {'B' if role == 'A' else 'A'} delivery",
            "coordinator map or original IDs",
            "dev gold or prior relation labels",
            "model predictions, prompts, or scores",
            "AI/LLM or automatic relation labeling",
        ],
        "annotation_authorized": False,
        "next_gate": "FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED",
    }


def read_delivery_sheet(
    path: Path, *, role: str, expected_rows: int
) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != OUTPUT_CSV_FIELDS:
            raise ValueError(f"annotator {role} delivery CSV field mismatch")
        rows = list(reader)
    if len(rows) != expected_rows:
        raise ValueError(
            f"annotator {role} delivery expected {expected_rows} rows, got {len(rows)}"
        )
    if any(
        set(row) != set(OUTPUT_CSV_FIELDS)
        or any(row[field] is None for field in OUTPUT_CSV_FIELDS)
        for row in rows
    ):
        raise ValueError(f"annotator {role} delivery contains malformed rows")
    return rows


def audit_relation_calibration(
    config: RelationCalibrationConfig,
    *,
    expected_a_sha256: str = EXPECTED_A_SHA256,
    expected_b_sha256: str = EXPECTED_B_SHA256,
    expected_coordinator_map_sha256: str = EXPECTED_COORDINATOR_MAP_SHA256,
    expected_guideline_sha256: str = EXPECTED_GUIDELINE_SHA256,
    expected_a_instructions_sha256: str = EXPECTED_A_INSTRUCTIONS_SHA256,
    expected_b_instructions_sha256: str = EXPECTED_B_INSTRUCTIONS_SHA256,
    expected_rows: int = EXPECTED_ROWS,
) -> dict[str, Any]:
    require_gate()
    if not config.output_dir.is_dir():
        raise FileNotFoundError(f"prepared package not found: {config.output_dir}")
    for label, path in (
        ("annotator A input", config.annotator_a_entities),
        ("annotator B input", config.annotator_b_entities),
        ("coordinator map", config.coordinator_map),
        ("output", config.output_dir),
    ):
        reject_domain_test_path(path, label)

    require_hash(config.guideline, expected_guideline_sha256, "locked guideline")
    require_hash(
        config.annotator_a_instructions,
        expected_a_instructions_sha256,
        "annotator A instructions",
    )
    require_hash(
        config.annotator_b_instructions,
        expected_b_instructions_sha256,
        "annotator B instructions",
    )
    a_source = read_locked_entities(
        config.annotator_a_entities,
        role="A",
        expected_sha256=expected_a_sha256,
        expected_rows=expected_rows,
    )
    b_source = read_locked_entities(
        config.annotator_b_entities,
        role="B",
        expected_sha256=expected_b_sha256,
        expected_rows=expected_rows,
    )
    source_map = read_coordinator_map(
        config.coordinator_map,
        expected_sha256=expected_coordinator_map_sha256,
        expected_rows=expected_rows,
    )
    expected_aligned = validate_alignment(a_source, b_source, source_map)
    expected_a_rows = make_delivery_rows(a_source)
    expected_b_rows = make_delivery_rows(b_source)

    a_delivery = config.output_dir / "annotator_a_delivery"
    b_delivery = config.output_dir / "annotator_b_delivery"
    coordinator_only = config.output_dir / "coordinator_only"
    expected_a_files = {
        A_SHEET_NAME,
        GUIDELINE_NAME,
        A_INSTRUCTIONS_NAME,
        "delivery_manifest.json",
    }
    expected_b_files = {
        B_SHEET_NAME,
        GUIDELINE_NAME,
        B_INSTRUCTIONS_NAME,
        "delivery_manifest.json",
    }
    if {path.name for path in a_delivery.iterdir()} != expected_a_files:
        raise ValueError("annotator A delivery file inventory mismatch")
    if {path.name for path in b_delivery.iterdir()} != expected_b_files:
        raise ValueError("annotator B delivery file inventory mismatch")
    if {path.name for path in coordinator_only.iterdir()} != {COORDINATOR_MAP_NAME}:
        raise ValueError("coordinator-only file inventory mismatch")
    if {path.name for path in config.output_dir.iterdir()} != {
        "annotator_a_delivery",
        "annotator_b_delivery",
        "coordinator_only",
        "manifest.json",
    }:
        raise ValueError("package root file inventory mismatch")

    a_sheet = a_delivery / A_SHEET_NAME
    b_sheet = b_delivery / B_SHEET_NAME
    actual_a_rows = read_delivery_sheet(
        a_sheet, role="A", expected_rows=expected_rows
    )
    actual_b_rows = read_delivery_sheet(
        b_sheet, role="B", expected_rows=expected_rows
    )
    if actual_a_rows != expected_a_rows:
        raise ValueError("annotator A delivery does not match locked source entities")
    if actual_b_rows != expected_b_rows:
        raise ValueError("annotator B delivery does not match locked source entities")
    if [row["text"] for row in actual_a_rows] == [
        row["text"] for row in actual_b_rows
    ]:
        raise ValueError("annotator A/B delivery orders unexpectedly match")

    copied_files = (
        (a_delivery / GUIDELINE_NAME, config.guideline, "A guideline"),
        (b_delivery / GUIDELINE_NAME, config.guideline, "B guideline"),
        (
            a_delivery / A_INSTRUCTIONS_NAME,
            config.annotator_a_instructions,
            "A instructions",
        ),
        (
            b_delivery / B_INSTRUCTIONS_NAME,
            config.annotator_b_instructions,
            "B instructions",
        ),
    )
    for copied, source, label in copied_files:
        if copied.read_bytes() != source.read_bytes():
            raise ValueError(f"{label} copy mismatch")

    coordinator_path = coordinator_only / COORDINATOR_MAP_NAME
    with coordinator_path.open("r", encoding="utf-8") as handle:
        actual_aligned = [json.loads(line) for line in handle if line.strip()]
    if actual_aligned != expected_aligned:
        raise ValueError("coordinator-only relation map mismatch")

    a_manifest_path = a_delivery / "delivery_manifest.json"
    b_manifest_path = b_delivery / "delivery_manifest.json"
    root_manifest_path = config.output_dir / "manifest.json"
    a_manifest = json.loads(a_manifest_path.read_text(encoding="utf-8"))
    b_manifest = json.loads(b_manifest_path.read_text(encoding="utf-8"))
    root_manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))
    for role, manifest, sheet in (
        ("A", a_manifest, a_sheet),
        ("B", b_manifest, b_sheet),
    ):
        expected_instruction_name = (
            A_INSTRUCTIONS_NAME if role == "A" else B_INSTRUCTIONS_NAME
        )
        expected_instruction_path = (
            config.annotator_a_instructions
            if role == "A"
            else config.annotator_b_instructions
        )
        expected_source_hash = (
            sha256_file(config.annotator_a_entities)
            if role == "A"
            else sha256_file(config.annotator_b_entities)
        )
        if (
            manifest.get("gate") != GATE_NAME
            or manifest.get("status") != "prepared_blank_not_started"
            or manifest.get("annotation_authorized") is not False
            or manifest.get("records") != expected_rows
            or manifest.get("locked_entity_source_sha256") != expected_source_hash
            or manifest.get("csv_fields") != list(OUTPUT_CSV_FIELDS)
            or manifest.get("read_only_fields") != list(OUTPUT_CSV_FIELDS[:4])
            or manifest.get("editable_after_next_gate")
            != list(OUTPUT_CSV_FIELDS[4:])
            or manifest.get("next_gate")
            != "FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED"
            or manifest.get("files", {}).get("sheet", {}).get("sha256")
            != sha256_file(sheet)
            or manifest.get("files", {}).get("guideline", {}).get("sha256")
            != sha256_file(config.guideline)
            or manifest.get("files", {}).get("instructions", {}).get("path")
            != expected_instruction_name
            or manifest.get("files", {}).get("instructions", {}).get("sha256")
            != sha256_file(expected_instruction_path)
        ):
            raise ValueError(f"annotator {role} delivery manifest mismatch")
    locked_inputs = root_manifest.get("locked_inputs", {})
    expected_locked_inputs = {
        "annotator_a_entities": (
            sha256_file(config.annotator_a_entities),
            expected_rows,
        ),
        "annotator_b_entities": (
            sha256_file(config.annotator_b_entities),
            expected_rows,
        ),
        "coordinator_map": (
            sha256_file(config.coordinator_map),
            expected_rows,
        ),
    }
    for key, (digest, rows) in expected_locked_inputs.items():
        if (
            locked_inputs.get(key, {}).get("sha256") != digest
            or locked_inputs.get(key, {}).get("rows") != rows
        ):
            raise ValueError(f"root manifest locked input mismatch: {key}")
    for key, source_path in (
        ("guideline", config.guideline),
        ("annotator_a_instructions", config.annotator_a_instructions),
        ("annotator_b_instructions", config.annotator_b_instructions),
    ):
        if locked_inputs.get(key, {}).get("sha256") != sha256_file(source_path):
            raise ValueError(f"root manifest locked input mismatch: {key}")
    scope = root_manifest.get("scope", {})
    false_scope_flags = (
        "annotation_started",
        "domain_test_read",
        "real_prompt_generation",
        "model_or_api_calls",
        "vllm_used",
        "gpu_used",
        "dev_gold_exported",
        "prior_relations_exported",
        "paper_modified",
        "github_sync",
        "formal_frozen_test_iaa",
    )
    validation = root_manifest.get("validation", {})
    output_manifest = root_manifest.get("outputs", {})
    if (
        root_manifest.get("gate") != GATE_NAME
        or root_manifest.get("status") != "prepared_blank_not_started"
        or any(scope.get(flag) is not False for flag in false_scope_flags)
        or scope.get("records_per_annotator") != expected_rows
        or validation.get("aligned_texts") != expected_rows
        or validation.get("all_map_rows_consumed") is not True
        or validation.get("annotator_orders_differ") is not True
        or validation.get("locked_entity_cells_preserved") is not True
        or validation.get("relation_fields_blank") is not True
        or validation.get("delivery_directories_physically_isolated") is not True
        or validation.get("coordinator_map_in_delivery_directories") is not False
        or output_manifest.get("annotator_a_delivery_manifest", {}).get("sha256")
        != sha256_file(a_manifest_path)
        or output_manifest.get("annotator_b_delivery_manifest", {}).get("sha256")
        != sha256_file(b_manifest_path)
        or output_manifest.get("coordinator_map", {}).get("sha256")
        != sha256_file(coordinator_path)
        or root_manifest.get("next_gate")
        != "FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED"
        or root_manifest.get("returned_file_validation_gate")
        != "FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED"
    ):
        raise ValueError("root preparation manifest mismatch")

    forbidden_name_tokens = (
        "domain_test",
        "prompt",
        "prediction",
        "gold",
        "model",
        "vllm",
    )
    file_names = [
        str(path.relative_to(config.output_dir)).lower()
        for path in config.output_dir.rglob("*")
        if path.is_file()
    ]
    forbidden_hits = [
        name
        for name in file_names
        if any(token in name for token in forbidden_name_tokens)
    ]
    if forbidden_hits:
        raise ValueError(f"forbidden delivery filename(s): {forbidden_hits}")

    return {
        "status": "passed",
        "records_per_annotator": expected_rows,
        "aligned_texts": len(actual_aligned),
        "blank_relation_rows": sum(
            not row["relations_json"] for row in actual_a_rows + actual_b_rows
        ),
        "annotator_orders_differ": True,
        "locked_entity_cells_preserved": True,
        "isolated_file_inventory": True,
        "forbidden_filename_hits": 0,
        "annotator_a_sheet_sha256": sha256_file(a_sheet),
        "annotator_b_sheet_sha256": sha256_file(b_sheet),
        "root_manifest_sha256": sha256_file(root_manifest_path),
    }


def prepare_relation_calibration(
    config: RelationCalibrationConfig,
    *,
    expected_a_sha256: str = EXPECTED_A_SHA256,
    expected_b_sha256: str = EXPECTED_B_SHA256,
    expected_coordinator_map_sha256: str = EXPECTED_COORDINATOR_MAP_SHA256,
    expected_guideline_sha256: str = EXPECTED_GUIDELINE_SHA256,
    expected_a_instructions_sha256: str = EXPECTED_A_INSTRUCTIONS_SHA256,
    expected_b_instructions_sha256: str = EXPECTED_B_INSTRUCTIONS_SHA256,
    expected_rows: int = EXPECTED_ROWS,
) -> dict[str, Any]:
    require_gate()
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {config.output_dir}")
    if expected_rows <= 0:
        raise ValueError("expected row count must be positive")
    for label, path in (
        ("annotator A input", config.annotator_a_entities),
        ("annotator B input", config.annotator_b_entities),
        ("coordinator map", config.coordinator_map),
        ("output", config.output_dir),
    ):
        reject_domain_test_path(path, label)

    require_hash(config.guideline, expected_guideline_sha256, "locked guideline")
    require_hash(
        config.annotator_a_instructions,
        expected_a_instructions_sha256,
        "annotator A instructions",
    )
    require_hash(
        config.annotator_b_instructions,
        expected_b_instructions_sha256,
        "annotator B instructions",
    )
    a_rows = read_locked_entities(
        config.annotator_a_entities,
        role="A",
        expected_sha256=expected_a_sha256,
        expected_rows=expected_rows,
    )
    b_rows = read_locked_entities(
        config.annotator_b_entities,
        role="B",
        expected_sha256=expected_b_sha256,
        expected_rows=expected_rows,
    )
    map_rows = read_coordinator_map(
        config.coordinator_map,
        expected_sha256=expected_coordinator_map_sha256,
        expected_rows=expected_rows,
    )
    aligned_rows = validate_alignment(a_rows, b_rows, map_rows)
    a_delivery_rows = make_delivery_rows(a_rows)
    b_delivery_rows = make_delivery_rows(b_rows)
    if [row["text"] for row in a_delivery_rows] == [
        row["text"] for row in b_delivery_rows
    ]:
        raise ValueError("annotator A/B source orders unexpectedly match")

    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = config.output_dir.parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        a_delivery = staging / "annotator_a_delivery"
        b_delivery = staging / "annotator_b_delivery"
        coordinator_only = staging / "coordinator_only"
        for directory in (a_delivery, b_delivery, coordinator_only):
            directory.mkdir(mode=0o700)

        a_sheet = a_delivery / A_SHEET_NAME
        b_sheet = b_delivery / B_SHEET_NAME
        a_guideline = a_delivery / GUIDELINE_NAME
        b_guideline = b_delivery / GUIDELINE_NAME
        a_instructions = a_delivery / A_INSTRUCTIONS_NAME
        b_instructions = b_delivery / B_INSTRUCTIONS_NAME
        coordinator_output = coordinator_only / COORDINATOR_MAP_NAME

        write_atomic(a_sheet, csv_payload(a_delivery_rows))
        write_atomic(b_sheet, csv_payload(b_delivery_rows))
        write_atomic(a_guideline, config.guideline.read_bytes())
        write_atomic(b_guideline, config.guideline.read_bytes())
        write_atomic(a_instructions, config.annotator_a_instructions.read_bytes())
        write_atomic(b_instructions, config.annotator_b_instructions.read_bytes())
        write_atomic(coordinator_output, jsonl_payload(aligned_rows))

        a_manifest = delivery_manifest(
            role="A",
            sheet=a_sheet,
            sheet_name=A_SHEET_NAME,
            guideline=a_guideline,
            instructions=a_instructions,
            instructions_name=A_INSTRUCTIONS_NAME,
            source_sha256=sha256_file(config.annotator_a_entities),
            rows=len(a_rows),
        )
        b_manifest = delivery_manifest(
            role="B",
            sheet=b_sheet,
            sheet_name=B_SHEET_NAME,
            guideline=b_guideline,
            instructions=b_instructions,
            instructions_name=B_INSTRUCTIONS_NAME,
            source_sha256=sha256_file(config.annotator_b_entities),
            rows=len(b_rows),
        )
        a_manifest_path = a_delivery / "delivery_manifest.json"
        b_manifest_path = b_delivery / "delivery_manifest.json"
        write_atomic(a_manifest_path, json_payload(a_manifest))
        write_atomic(b_manifest_path, json_payload(b_manifest))

        root_manifest = {
            "phase": "FULL-IE-F2-RELATION-CALIBRATION-PREP",
            "gate": GATE_NAME,
            "status": "prepared_blank_not_started",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scope": {
                "source": "locked_fresh_non_test_human_entity_submissions",
                "records_per_annotator": expected_rows,
                "task": "exact_directed_relation_annotation",
                "annotators_independent": True,
                "annotation_started": False,
                "domain_test_read": False,
                "real_prompt_generation": False,
                "model_or_api_calls": False,
                "vllm_used": False,
                "gpu_used": False,
                "dev_gold_exported": False,
                "prior_relations_exported": False,
                "paper_modified": False,
                "github_sync": False,
                "formal_frozen_test_iaa": False,
            },
            "locked_inputs": {
                "annotator_a_entities": {
                    "path": str(config.annotator_a_entities),
                    "sha256": sha256_file(config.annotator_a_entities),
                    "rows": len(a_rows),
                },
                "annotator_b_entities": {
                    "path": str(config.annotator_b_entities),
                    "sha256": sha256_file(config.annotator_b_entities),
                    "rows": len(b_rows),
                },
                "coordinator_map": {
                    "path": str(config.coordinator_map),
                    "sha256": sha256_file(config.coordinator_map),
                    "rows": len(map_rows),
                },
                "guideline": {
                    "path": str(config.guideline),
                    "sha256": sha256_file(config.guideline),
                },
                "annotator_a_instructions": {
                    "path": str(config.annotator_a_instructions),
                    "sha256": sha256_file(config.annotator_a_instructions),
                },
                "annotator_b_instructions": {
                    "path": str(config.annotator_b_instructions),
                    "sha256": sha256_file(config.annotator_b_instructions),
                },
            },
            "validation": {
                "aligned_texts": len(aligned_rows),
                "all_map_rows_consumed": True,
                "annotator_orders_differ": True,
                "locked_entity_cells_preserved": True,
                "relation_fields_blank": True,
                "delivery_directories_physically_isolated": True,
                "coordinator_map_in_delivery_directories": False,
            },
            "outputs": {
                "annotator_a_delivery_manifest": file_metadata(
                    a_manifest_path,
                    relative_path="annotator_a_delivery/delivery_manifest.json",
                    role="annotator_a_only",
                ),
                "annotator_b_delivery_manifest": file_metadata(
                    b_manifest_path,
                    relative_path="annotator_b_delivery/delivery_manifest.json",
                    role="annotator_b_only",
                ),
                "coordinator_map": file_metadata(
                    coordinator_output,
                    relative_path=f"coordinator_only/{COORDINATOR_MAP_NAME}",
                    role="coordinator_only",
                    rows=len(aligned_rows),
                ),
            },
            "next_gate": "FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED",
            "returned_file_validation_gate": (
                "FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED"
            ),
        }
        root_manifest_path = staging / "manifest.json"
        write_atomic(root_manifest_path, json_payload(root_manifest))

        for path in staging.rglob("*"):
            os.chmod(path, 0o700 if path.is_dir() else 0o600)
        os.replace(staging, config.output_dir)
        os.chmod(config.output_dir, 0o700)
        return root_manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    config = RelationCalibrationConfig(
        annotator_a_entities=Path(args.annotator_a_entities),
        annotator_b_entities=Path(args.annotator_b_entities),
        coordinator_map=Path(args.coordinator_map),
        guideline=Path(args.guideline),
        annotator_a_instructions=Path(args.annotator_a_instructions),
        annotator_b_instructions=Path(args.annotator_b_instructions),
        output_dir=Path(args.output_dir),
    )
    if args.audit_only:
        report = audit_relation_calibration(config)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0

    manifest = prepare_relation_calibration(config)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "records_per_annotator": manifest["scope"]["records_per_annotator"],
                "output_dir": str(config.output_dir),
                "next_gate": manifest["next_gate"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
