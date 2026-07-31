#!/usr/bin/env python3
"""Validate and score the locked FULL-IE relation calibration returns.

Run only on AutoDL in GPU-free mode under the explicit validation gate. The
validator compares each completed sheet with its prepared blank sheet, aligns
the two annotators through the coordinator-only map, and computes exact
directed endpoint/type relation concordance. It does not read domain_test,
generate prompts, call a model, repair labels, or establish human provenance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie import (
    DEFAULT_RELATION_TYPES,
    canonical_relation_keys,
    same_sentence,
)  # noqa: E402


GATE_NAME = "FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED"
REVALIDATION_GATE_NAME = "FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED"
INITIAL_INPUT_PROFILE = "initial_v1"
REVISED_INPUT_PROFILE = "revised_v2"
EXPECTED_ROWS = 20
EXPECTED_COMPLETED_A_SHA256 = (
    "444f46428f8b3d3bc61c39cda7bd1330ab80b4ebd6d1fc4f83b92fb31083726a"
)
EXPECTED_COMPLETED_B_SHA256 = (
    "5489aa8128494e12655893dc54a6124250535f5116ed11417ed19733cab46066"
)
EXPECTED_REVISED_COMPLETED_A_SHA256 = (
    "579a1a368e492fa1f3d49f13f3fb4dabe4129eb4ac8b6ecfeea9829d92a63fe3"
)
EXPECTED_REVISED_COMPLETED_B_SHA256 = (
    "4acc4b05358027cb61b4e9ddd3e0d72c10b48468547ad9e06db49f727a24861f"
)
EXPECTED_BLANK_A_SHA256 = (
    "44157617b377178aba0a1a6a2881cfb759b9927526dbbd536deb1dc04dc57411"
)
EXPECTED_BLANK_B_SHA256 = (
    "3986d2e1654af3340abaf1cc81a5c41dbb94f261c9a419c61ec82c327842554d"
)
EXPECTED_MAP_SHA256 = (
    "0369b2a6837205440a61a95a3932d8db1e164ac20e9083118ed7db32a51e9489"
)
CSV_FIELDS = (
    "blind_id",
    "text",
    "entities_json_locked",
    "entity_index_guide",
    "relations_json",
    "relation_notes",
    "relation_uncertainty_code",
)
READ_ONLY_FIELDS = CSV_FIELDS[:4]
MAP_FIELDS = {
    "original_id",
    "annotator_a_blind_id",
    "annotator_b_blind_id",
    "text_sha256",
    "selection_bucket",
    "annotator_a_entities_sha256",
    "annotator_b_entities_sha256",
    "annotator_a_entity_count",
    "annotator_b_entity_count",
}
ENTITY_FIELDS = {"start", "end", "type", "span"}
ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}
RELATION_FIELDS = {"head", "tail", "type"}
RELATION_TYPES = tuple(sorted(DEFAULT_RELATION_TYPES))
ALLOWED_UNCERTAINTY_CODES = {
    "DIRECTION",
    "TYPE_MATRIX",
    "USES_VS_PART_OF",
    "EXPLICITNESS",
    "SAME_SENTENCE",
    "NEGATION_HYPOTHETICAL",
    "ENDPOINT_ENTITY",
    "OTHER",
}
ISSUE_FIELDS = (
    "severity",
    "annotator",
    "blind_id",
    "original_id",
    "code",
    "detail",
)
RelationKey = tuple[int, int, str, str, int, int, str]


@dataclass(frozen=True)
class ValidationConfig:
    annotator_a_completed: Path
    annotator_b_completed: Path
    annotator_a_blank: Path
    annotator_b_blank: Path
    coordinator_map: Path
    output_dir: Path


@dataclass(frozen=True)
class ExpectedHashes:
    annotator_a_completed: str = EXPECTED_COMPLETED_A_SHA256
    annotator_b_completed: str = EXPECTED_COMPLETED_B_SHA256
    annotator_a_blank: str = EXPECTED_BLANK_A_SHA256
    annotator_b_blank: str = EXPECTED_BLANK_B_SHA256
    coordinator_map: str = EXPECTED_MAP_SHA256


INPUT_PROFILES = {
    INITIAL_INPUT_PROFILE: (
        GATE_NAME,
        ExpectedHashes(),
    ),
    REVISED_INPUT_PROFILE: (
        REVALIDATION_GATE_NAME,
        ExpectedHashes(
            annotator_a_completed=EXPECTED_REVISED_COMPLETED_A_SHA256,
            annotator_b_completed=EXPECTED_REVISED_COMPLETED_B_SHA256,
        ),
    ),
}


def parse_args() -> argparse.Namespace:
    prepared = "/root/autodl-tmp/backup/full_ie/f2_relation_calibration_20260730"
    returned = (
        "/root/autodl-tmp/backup/full_ie/"
        "f2_relation_calibration_completed_20260730/returned"
    )
    parser = argparse.ArgumentParser(
        description="Validate completed FULL-IE relation calibration sheets."
    )
    parser.add_argument(
        "--annotator-a-completed",
        default=f"{returned}/annotator_a_relation_calibration_completed.csv",
    )
    parser.add_argument(
        "--annotator-b-completed",
        default=f"{returned}/annotator_b_relation_calibration_completed.csv",
    )
    parser.add_argument(
        "--annotator-a-blank",
        default=f"{prepared}/annotator_a_delivery/annotator_a_relation_calibration.csv",
    )
    parser.add_argument(
        "--annotator-b-blank",
        default=f"{prepared}/annotator_b_delivery/annotator_b_relation_calibration.csv",
    )
    parser.add_argument(
        "--coordinator-map",
        default=f"{prepared}/coordinator_only/relation_calibration_map.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "/root/autodl-tmp/backup/full_ie/"
            "f2_relation_calibration_validation_20260731"
        ),
    )
    parser.add_argument(
        "--input-profile",
        choices=tuple(INPUT_PROFILES),
        default=INITIAL_INPUT_PROFILE,
        help="Select a versioned, hard-locked returned-file hash profile.",
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


def require_gate(gate_name: str) -> None:
    if os.environ.get(gate_name) != "1":
        raise PermissionError(f"set {gate_name}=1 for this bounded validation gate")


def reject_forbidden_path(path: Path, label: str) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if "domain_test" in normalized:
        raise ValueError(f"{label} must not reference domain_test")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError(f"CSV field mismatch in {path}: {reader.fieldnames}")
        rows = list(reader)
    for row_number, row in enumerate(rows, start=2):
        if set(row) != set(CSV_FIELDS) or any(row[field] is None for field in CSV_FIELDS):
            raise ValueError(f"malformed CSV row at {path}:{row_number}")
    return rows


def read_map(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank coordinator-map line {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != MAP_FIELDS:
                raise ValueError(f"coordinator-map field mismatch at line {line_number}")
            rows.append(row)
    return rows


def index_rows(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        blind_id = row["blind_id"]
        if not blind_id or blind_id in indexed:
            raise ValueError(f"empty or duplicate blind_id in {label}: {blind_id!r}")
        indexed[blind_id] = row
    return indexed


def validate_locked_entities(
    value: str, text: str, *, annotator: str, blind_id: str
) -> list[dict[str, Any]]:
    try:
        entities = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{annotator} {blind_id} locked entities are invalid JSON") from exc
    if not isinstance(entities, list):
        raise ValueError(f"{annotator} {blind_id} locked entities must be an array")
    seen: set[tuple[int, int, str]] = set()
    for index, entity in enumerate(entities):
        prefix = f"{annotator} {blind_id} entity {index}"
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
            raise ValueError(f"{annotator} {blind_id} contains duplicate entities")
        seen.add(key)
    return entities


def add_issue(
    issues: list[dict[str, str]],
    *,
    annotator: str,
    blind_id: str,
    original_id: str,
    code: str,
    detail: str,
) -> None:
    issues.append(
        {
            "severity": "hard_error",
            "annotator": annotator,
            "blind_id": blind_id,
            "original_id": original_id,
            "code": code,
            "detail": detail,
        }
    )


def parse_uncertainty_codes(
    value: str,
    *,
    notes: str,
    annotator: str,
    blind_id: str,
    original_id: str,
    issues: list[dict[str, str]],
) -> tuple[list[str], bool]:
    if not value.strip():
        return [], True
    raw_codes = value.split(";")
    codes = [item.strip() for item in raw_codes]
    valid = True
    if any(not code for code in codes):
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="UNCERTAINTY_FORMAT",
            detail="uncertainty codes contain an empty semicolon-delimited item",
        )
        valid = False
    invalid = sorted(set(codes) - ALLOWED_UNCERTAINTY_CODES - {""})
    if invalid:
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="UNCERTAINTY_INVALID",
            detail=f"invalid uncertainty codes: {invalid}",
        )
        valid = False
    duplicates = sorted(code for code, count in Counter(codes).items() if code and count > 1)
    if duplicates:
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="UNCERTAINTY_DUPLICATE",
            detail=f"duplicate uncertainty codes: {duplicates}",
        )
        valid = False
    if "ENDPOINT_ENTITY" in codes and not notes.strip():
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="ENDPOINT_ENTITY_NOTE_MISSING",
            detail="ENDPOINT_ENTITY requires a short relation_notes explanation",
        )
        valid = False
    return [code for code in codes if code], valid


def parse_relations(
    row: dict[str, str],
    entities: list[dict[str, Any]],
    *,
    annotator: str,
    original_id: str,
    issues: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], bool]:
    blind_id = row["blind_id"]
    value = row["relations_json"]
    if not value.strip():
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="RELATIONS_MISSING",
            detail="relations_json is blank; use [] for no relation",
        )
        return [], False
    try:
        raw_relations = json.loads(value)
    except json.JSONDecodeError as exc:
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="RELATIONS_INVALID_JSON",
            detail=str(exc),
        )
        return [], False
    if not isinstance(raw_relations, list):
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="RELATIONS_NOT_ARRAY",
            detail="relations_json must be a JSON array",
        )
        return [], False

    parsed: list[dict[str, Any]] = []
    relation_keys: list[tuple[int, int, str]] = []
    valid = True
    for index, relation in enumerate(raw_relations):
        prefix = f"relation {index}"
        if not isinstance(relation, dict):
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_NOT_OBJECT",
                detail=f"{prefix} must be an object",
            )
            valid = False
            continue
        if set(relation) != RELATION_FIELDS:
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_FIELDS",
                detail=f"{prefix} fields must equal {sorted(RELATION_FIELDS)}",
            )
            valid = False
            continue
        head = relation["head"]
        tail = relation["tail"]
        relation_type = relation["type"]
        if (
            isinstance(head, bool)
            or isinstance(tail, bool)
            or not isinstance(head, int)
            or not isinstance(tail, int)
            or head < 0
            or tail < 0
            or head >= len(entities)
            or tail >= len(entities)
        ):
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_INDEX",
                detail=f"{prefix} has an out-of-range or non-integer endpoint",
            )
            valid = False
            continue
        if head == tail:
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_SELF",
                detail=f"{prefix} is self-referential",
            )
            valid = False
            continue
        if relation_type not in DEFAULT_RELATION_TYPES:
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_TYPE",
                detail=f"{prefix} has invalid type {relation_type!r}",
            )
            valid = False
            continue
        rule = DEFAULT_RELATION_TYPES[relation_type]
        head_entity = entities[head]
        tail_entity = entities[tail]
        if (
            head_entity["type"] not in rule["head_types"]
            or tail_entity["type"] not in rule["tail_types"]
        ):
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_TYPE_MATRIX",
                detail=(
                    f"{prefix} {relation_type} does not allow "
                    f"{head_entity['type']} -> {tail_entity['type']}"
                ),
            )
            valid = False
            continue
        if not same_sentence(row["text"], head_entity, tail_entity):
            add_issue(
                issues,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="RELATION_CROSS_SENTENCE",
                detail=f"{prefix} endpoints are not in the same sentence",
            )
            valid = False
            continue
        key = (head, tail, relation_type)
        relation_keys.append(key)
        parsed.append({"head": head, "tail": tail, "type": relation_type})

    duplicates = sorted(key for key, count in Counter(relation_keys).items() if count > 1)
    if duplicates:
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="RELATION_DUPLICATE",
            detail=f"duplicate relations: {duplicates}",
        )
        valid = False
    if relation_keys != sorted(relation_keys):
        add_issue(
            issues,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="RELATIONS_NOT_SORTED",
            detail="relations must be sorted by (head, tail, type)",
        )
        valid = False
    return parsed, valid


def relation_record(
    *,
    original_id: str,
    text: str,
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": original_id,
        "text": text,
        "entities": entities,
        "relations": relations,
    }


def score_pairs(
    pairs: Iterable[tuple[set[RelationKey], set[RelationKey]]],
    relation_type: str | None = None,
) -> dict[str, int | float]:
    true_positive = 0
    false_positive = 0
    false_negative = 0
    annotator_a_relations = 0
    annotator_b_relations = 0
    paired_rows = 0
    row_exact_matches = 0
    for a_keys, b_keys in pairs:
        if relation_type is not None:
            a_keys = {key for key in a_keys if key[3] == relation_type}
            b_keys = {key for key in b_keys if key[3] == relation_type}
        true_positive += len(a_keys & b_keys)
        false_positive += len(b_keys - a_keys)
        false_negative += len(a_keys - b_keys)
        annotator_a_relations += len(a_keys)
        annotator_b_relations += len(b_keys)
        paired_rows += 1
        row_exact_matches += a_keys == b_keys
    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "annotator_a_relations": annotator_a_relations,
        "annotator_b_relations": annotator_b_relations,
        "paired_rows": paired_rows,
        "row_exact_matches": row_exact_matches,
        "row_exact_rate": row_exact_matches / paired_rows if paired_rows else 0.0,
    }


def relation_key_payload(key: RelationKey) -> dict[str, Any]:
    return {
        "head_start": key[0],
        "head_end": key[1],
        "head_type": key[2],
        "relation_type": key[3],
        "tail_start": key[4],
        "tail_end": key[5],
        "tail_type": key[6],
    }


def csv_payload(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fields,
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
    if not rows:
        return b""
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


def file_metadata(path: Path, *, final_path: Path, rows: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(final_path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "role": "coordinator_only",
    }
    if rows is not None:
        result["rows"] = rows
    return result


def validate_relation_calibration(
    config: ValidationConfig,
    *,
    expected_hashes: ExpectedHashes = ExpectedHashes(),
    expected_rows: int = EXPECTED_ROWS,
    gate_name: str = GATE_NAME,
    input_profile: str = INITIAL_INPUT_PROFILE,
) -> dict[str, Any]:
    require_gate(gate_name)
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output: {config.output_dir}")
    locked_inputs = (
        (
            config.annotator_a_completed,
            expected_hashes.annotator_a_completed,
            "annotator_a_completed",
        ),
        (
            config.annotator_b_completed,
            expected_hashes.annotator_b_completed,
            "annotator_b_completed",
        ),
        (config.annotator_a_blank, expected_hashes.annotator_a_blank, "annotator_a_blank"),
        (config.annotator_b_blank, expected_hashes.annotator_b_blank, "annotator_b_blank"),
        (config.coordinator_map, expected_hashes.coordinator_map, "coordinator_map"),
    )
    for path, expected_hash, label in locked_inputs:
        reject_forbidden_path(path, label)
        require_hash(path, expected_hash, label)
    reject_forbidden_path(config.output_dir, "output_dir")

    blank_a_rows = read_csv(config.annotator_a_blank)
    blank_b_rows = read_csv(config.annotator_b_blank)
    completed_a_rows = read_csv(config.annotator_a_completed)
    completed_b_rows = read_csv(config.annotator_b_completed)
    map_rows = read_map(config.coordinator_map)
    for label, rows in (
        ("A blank", blank_a_rows),
        ("B blank", blank_b_rows),
        ("A completed", completed_a_rows),
        ("B completed", completed_b_rows),
        ("coordinator map", map_rows),
    ):
        if len(rows) != expected_rows:
            raise ValueError(f"{label} expected {expected_rows} rows, got {len(rows)}")

    blank_a = index_rows(blank_a_rows, "A blank")
    blank_b = index_rows(blank_b_rows, "B blank")
    completed_a = index_rows(completed_a_rows, "A completed")
    completed_b = index_rows(completed_b_rows, "B completed")
    if [row["blind_id"] for row in blank_a_rows] != [
        row["blind_id"] for row in completed_a_rows
    ]:
        raise ValueError("A completed row order or blind IDs changed")
    if [row["blind_id"] for row in blank_b_rows] != [
        row["blind_id"] for row in completed_b_rows
    ]:
        raise ValueError("B completed row order or blind IDs changed")
    for annotator, blank, completed in (
        ("A", blank_a, completed_a),
        ("B", blank_b, completed_b),
    ):
        if set(blank) != set(completed):
            raise ValueError(f"{annotator} completed blind IDs differ from blank sheet")
        for blind_id, completed_row in completed.items():
            for field in READ_ONLY_FIELDS:
                if completed_row[field] != blank[blind_id][field]:
                    raise ValueError(
                        f"{annotator} read-only field {field} changed for {blind_id}"
                    )

    map_by_original: dict[str, dict[str, Any]] = {}
    seen_a: set[str] = set()
    seen_b: set[str] = set()
    bucket_counts: Counter[str] = Counter()
    for row in map_rows:
        original_id = row["original_id"]
        a_id = row["annotator_a_blind_id"]
        b_id = row["annotator_b_blind_id"]
        if (
            not isinstance(original_id, str)
            or not original_id
            or original_id in map_by_original
            or a_id in seen_a
            or b_id in seen_b
        ):
            raise ValueError("coordinator map contains empty or duplicate IDs")
        if a_id not in completed_a or b_id not in completed_b:
            raise ValueError(f"coordinator map references a missing row: {original_id}")
        a_row = completed_a[a_id]
        b_row = completed_b[b_id]
        if (
            a_row["text"] != b_row["text"]
            or sha256_text(a_row["text"]) != row["text_sha256"]
        ):
            raise ValueError(f"coordinator map text/hash mismatch: {original_id}")
        for annotator, completed_row in (("a", a_row), ("b", b_row)):
            entity_hash = sha256_text(completed_row["entities_json_locked"])
            if entity_hash != row[f"annotator_{annotator}_entities_sha256"]:
                raise ValueError(
                    f"coordinator map entity hash mismatch: {original_id} annotator {annotator}"
                )
            entities = validate_locked_entities(
                completed_row["entities_json_locked"],
                completed_row["text"],
                annotator=annotator.upper(),
                blind_id=completed_row["blind_id"],
            )
            if len(entities) != row[f"annotator_{annotator}_entity_count"]:
                raise ValueError(
                    f"coordinator map entity count mismatch: {original_id} annotator {annotator}"
                )
        map_by_original[original_id] = row
        seen_a.add(a_id)
        seen_b.add(b_id)
        bucket_counts[str(row["selection_bucket"])] += 1
    if seen_a != set(completed_a) or seen_b != set(completed_b):
        raise ValueError("coordinator map does not cover every completed row exactly once")

    issues: list[dict[str, str]] = []
    uncertainty_counts: Counter[tuple[str, str]] = Counter()
    uncertainty_rows: Counter[str] = Counter()
    valid_by_role: dict[str, dict[str, bool]] = {"A": {}, "B": {}}
    keys_by_role: dict[str, dict[str, set[RelationKey]]] = {"A": {}, "B": {}}
    zero_relation_rows: Counter[str] = Counter()
    relation_counts: dict[str, Counter[str]] = {"A": Counter(), "B": Counter()}

    for original_id, mapping in sorted(map_by_original.items()):
        for annotator, row in (
            ("A", completed_a[mapping["annotator_a_blind_id"]]),
            ("B", completed_b[mapping["annotator_b_blind_id"]]),
        ):
            entities = validate_locked_entities(
                row["entities_json_locked"],
                row["text"],
                annotator=annotator,
                blind_id=row["blind_id"],
            )
            codes, uncertainty_valid = parse_uncertainty_codes(
                row["relation_uncertainty_code"],
                notes=row["relation_notes"],
                annotator=annotator,
                blind_id=row["blind_id"],
                original_id=original_id,
                issues=issues,
            )
            if codes:
                uncertainty_rows[annotator] += 1
            for code in set(codes):
                uncertainty_counts[(annotator, code)] += 1
            relations, relations_valid = parse_relations(
                row,
                entities,
                annotator=annotator,
                original_id=original_id,
                issues=issues,
            )
            valid = uncertainty_valid and relations_valid
            valid_by_role[annotator][original_id] = valid
            if valid:
                record = relation_record(
                    original_id=original_id,
                    text=row["text"],
                    entities=entities,
                    relations=relations,
                )
                keys = canonical_relation_keys(record)
                keys_by_role[annotator][original_id] = keys
                if not keys:
                    zero_relation_rows[annotator] += 1
                relation_counts[annotator].update(key[3] for key in keys)
            else:
                keys_by_role[annotator][original_id] = set()

    valid_ids = [
        original_id
        for original_id in sorted(map_by_original)
        if valid_by_role["A"][original_id] and valid_by_role["B"][original_id]
    ]
    pairs = [
        (keys_by_role["A"][original_id], keys_by_role["B"][original_id])
        for original_id in valid_ids
    ]
    concordance = score_pairs(pairs)
    per_type = {
        relation_type: score_pairs(pairs, relation_type)
        for relation_type in RELATION_TYPES
    }

    disagreements: list[dict[str, Any]] = []
    for original_id in valid_ids:
        a_keys = keys_by_role["A"][original_id]
        b_keys = keys_by_role["B"][original_id]
        if a_keys == b_keys:
            continue
        mapping = map_by_original[original_id]
        disagreements.append(
            {
                "original_id": original_id,
                "selection_bucket": mapping["selection_bucket"],
                "annotator_a_blind_id": mapping["annotator_a_blind_id"],
                "annotator_b_blind_id": mapping["annotator_b_blind_id"],
                "annotator_a_only": [
                    relation_key_payload(key) for key in sorted(a_keys - b_keys)
                ],
                "annotator_b_only": [
                    relation_key_payload(key) for key in sorted(b_keys - a_keys)
                ],
            }
        )

    issue_counts = Counter(issue["code"] for issue in issues)
    completed = len(issues) == 0 and len(valid_ids) == expected_rows
    created_at = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {
        "phase": "FULL-IE-F2-RELATION-CALIBRATION-VALIDATION",
        "status": "completed_diagnostic" if completed else "blocked_structural_errors",
        "created_at": created_at,
        "gate": gate_name,
        "input_profile": input_profile,
        "scope": {
            "source": "locked_fresh_20_text_non_test_human_entity_submissions",
            "expected_rows_per_annotator": expected_rows,
            "task": "exact_directed_relation_calibration",
            "domain_test_read": False,
            "support_dev_test_prompt_generated": False,
            "model_or_api_calls": False,
            "vllm_used": False,
            "gpu_used": False,
            "labels_modified_or_repaired": False,
            "input_annotations_revised_after_prior_validation": (
                input_profile == REVISED_INPUT_PROFILE
            ),
            "prior_failed_validation_preserved": (
                input_profile == REVISED_INPUT_PROFILE
            ),
            "formal_frozen_test_iaa": False,
            "human_independence_provenance_assessed_by_validator": False,
        },
        "input_integrity": {
            "annotator_a_rows": len(completed_a_rows),
            "annotator_b_rows": len(completed_b_rows),
            "coordinator_map_rows": len(map_rows),
            "read_only_fields_preserved": True,
            "row_orders_preserved": True,
            "blind_ids_texts_entity_hashes_and_counts_aligned": True,
            "selection_bucket_counts": dict(sorted(bucket_counts.items())),
        },
        "validation": {
            "structural_error_count": len(issues),
            "issue_code_counts": dict(sorted(issue_counts.items())),
            "valid_paired_rows": len(valid_ids),
            "all_rows_complete_and_structurally_valid": completed,
        },
        "exact_directed_file_concordance": concordance,
        "exact_directed_file_concordance_per_type": per_type,
        "relation_counts": {
            "annotator_a_total": sum(relation_counts["A"].values()),
            "annotator_b_total": sum(relation_counts["B"].values()),
            "annotator_a_by_type": dict(sorted(relation_counts["A"].items())),
            "annotator_b_by_type": dict(sorted(relation_counts["B"].items())),
            "annotator_a_zero_relation_rows": zero_relation_rows["A"],
            "annotator_b_zero_relation_rows": zero_relation_rows["B"],
        },
        "uncertainty": {
            "rows_by_annotator": dict(sorted(uncertainty_rows.items())),
            "code_counts": {
                f"{annotator}:{code}": count
                for (annotator, code), count in sorted(uncertainty_counts.items())
            },
        },
        "disagreement_rows": len(disagreements),
        "success_criterion": {
            "predefined_f1_threshold": None,
            "required": "zero structural errors and a fully disclosed diagnostic",
            "low_agreement_policy": "retain unchanged; it weakens the relation-quality claim",
        },
        "formal_human_iaa": None,
        "provenance_note": (
            "This validator measures locked-file concordance only. Independent two-human "
            "annotation without AI, scripts, discussion, or cross-file access requires "
            "separate coordinator attestation and is not inferred from file contents."
        ),
    }

    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = config.output_dir.parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        report_path = staging / "validation_report.json"
        issues_path = staging / "issues.csv"
        disagreements_path = staging / "disagreements.jsonl"
        write_atomic(report_path, json_payload(report))
        write_atomic(issues_path, csv_payload(issues, ISSUE_FIELDS))
        write_atomic(disagreements_path, jsonl_payload(disagreements))
        final_paths = {
            "validation_report": config.output_dir / report_path.name,
            "issues": config.output_dir / issues_path.name,
            "disagreements": config.output_dir / disagreements_path.name,
        }
        manifest = {
            "phase": report["phase"],
            "gate": gate_name,
            "input_profile": input_profile,
            "status": report["status"],
            "created_at": created_at,
            "inputs": {
                label: {"path": str(path), "sha256": sha256_file(path)}
                for path, _, label in locked_inputs
            },
            "safeguards": {
                "locked_input_hashes": True,
                "no_domain_test_or_prompt_data": True,
                "no_model_api_vllm_or_gpu": True,
                "no_label_repair": True,
                "existing_output_overwrite_refused": True,
                "coordinator_only_output": True,
                "human_provenance_not_inferred": True,
            },
            "outputs": {
                "validation_report": file_metadata(
                    report_path, final_path=final_paths["validation_report"]
                ),
                "issues": file_metadata(
                    issues_path, final_path=final_paths["issues"], rows=len(issues)
                ),
                "disagreements": file_metadata(
                    disagreements_path,
                    final_path=final_paths["disagreements"],
                    rows=len(disagreements),
                ),
            },
        }
        manifest_path = staging / "manifest.json"
        write_atomic(manifest_path, json_payload(manifest))
        for path in (report_path, issues_path, disagreements_path, manifest_path):
            os.chmod(path, 0o600)
        os.replace(staging, config.output_dir)
        os.chmod(config.output_dir, 0o700)
        return report
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    gate_name, expected_hashes = INPUT_PROFILES[args.input_profile]
    config = ValidationConfig(
        annotator_a_completed=Path(args.annotator_a_completed),
        annotator_b_completed=Path(args.annotator_b_completed),
        annotator_a_blank=Path(args.annotator_a_blank),
        annotator_b_blank=Path(args.annotator_b_blank),
        coordinator_map=Path(args.coordinator_map),
        output_dir=Path(args.output_dir),
    )
    report = validate_relation_calibration(
        config,
        expected_hashes=expected_hashes,
        gate_name=gate_name,
        input_profile=args.input_profile,
    )
    concordance = report["exact_directed_file_concordance"]
    print(
        json.dumps(
            {
                "status": report["status"],
                "structural_errors": report["validation"]["structural_error_count"],
                "paired_rows": concordance["paired_rows"],
                "true_positive": concordance["true_positive"],
                "false_positive": concordance["false_positive"],
                "false_negative": concordance["false_negative"],
                "precision": concordance["precision"],
                "recall": concordance["recall"],
                "f1": concordance["f1"],
                "input_profile": args.input_profile,
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
