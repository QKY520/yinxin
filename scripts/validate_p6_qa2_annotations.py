#!/usr/bin/env python3
"""Validate P6-QA2 completed blind NER annotation sheets.

Run only on AutoDL in GPU-free mode. This validator uses the QA0 blank sheets
and coordinator map to align A/B submissions. It never reads frozen gold,
model predictions, prompts, or experiment results, and it never repairs labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


EXPECTED_ROWS = 170
EXPECTED_BLANK_A_SHA256 = "3a36082631b45339d8b8e6ecd724ca3bbb7f74196531339ddb4621c4a72e1171"
EXPECTED_BLANK_B_SHA256 = "39b5ee7755ee48bd1c0d762e1ecdfd8c6a4251bdf8a0e1cf82a4c7ad149ae685"
EXPECTED_MAP_SHA256 = "d39d2252400cdc17a37eef78ed3a276c1f86c804d65e03f43cef31d752e38eb1"
EXPECTED_COMPLETED_A_SHA256 = "f07a650688c9cafcf4d16f5be906a0f45a3623838994cc9af2954385eb2183b7"
EXPECTED_COMPLETED_B_SHA256 = "90e8e2458de3dd1f847a730759a353efb0a493bbbe385bbaa88fecf6acccd8ef"
CSV_FIELDS = ("blind_id", "text", "entities_json", "notes")
MAP_FIELDS = {
    "original_id",
    "annotator_a_blind_id",
    "annotator_b_blind_id",
    "text_sha256",
    "source_type",
    "prior_label_source",
}
ENTITY_FIELDS = {"start", "end", "type", "span"}
ENTITY_TYPES = ("EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC")
HARD_ERROR = "error"
BLOCKING_REVIEW = "blocking_review"


@dataclass(frozen=True)
class ValidationConfig:
    annotator_a_completed: Path
    annotator_b_completed: Path
    annotator_a_blank: Path
    annotator_b_blank: Path
    blind_map: Path
    output_dir: Path


@dataclass(frozen=True)
class ExpectedHashes:
    annotator_a_completed: str = EXPECTED_COMPLETED_A_SHA256
    annotator_b_completed: str = EXPECTED_COMPLETED_B_SHA256
    annotator_a_blank: str = EXPECTED_BLANK_A_SHA256
    annotator_b_blank: str = EXPECTED_BLANK_B_SHA256
    blind_map: str = EXPECTED_MAP_SHA256


def parse_args() -> argparse.Namespace:
    qa0_root = "/root/autodl-tmp/backup/p6/p6_qa0_blind_annotation_20260725"
    qa2_input_root = "/root/autodl-tmp/backup/p6/p6_qa2_inputs_20260726"
    parser = argparse.ArgumentParser(
        description="Validate P6-QA2 blind NER annotation submissions."
    )
    parser.add_argument(
        "--annotator-a-completed",
        default=f"{qa2_input_root}/annotator_a_completed.csv",
    )
    parser.add_argument(
        "--annotator-b-completed",
        default=f"{qa2_input_root}/annotator_b_completed.csv",
    )
    parser.add_argument(
        "--annotator-a-blank",
        default=f"{qa0_root}/annotator_a_blind.csv",
    )
    parser.add_argument(
        "--annotator-b-blank",
        default=f"{qa0_root}/annotator_b_blind.csv",
    )
    parser.add_argument("--blind-map", default=f"{qa0_root}/blind_id_map.jsonl")
    parser.add_argument(
        "--output-dir",
        default=(
            "/root/autodl-tmp/backup/p6/"
            "p6_qa2_annotation_validation_20260726"
        ),
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA256 mismatch: expected {expected}, got {actual}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError(f"CSV field mismatch in {path}: {reader.fieldnames}")
        rows = list(reader)
    for index, row in enumerate(rows, start=1):
        if None in row:
            raise ValueError(f"extra CSV cells at {path} row {index}")
        if any(value is None for value in row.values()):
            raise ValueError(f"missing CSV cells at {path} row {index}")
    return rows


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(row)
    return rows


def index_rows(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        blind_id = row["blind_id"]
        if not blind_id:
            raise ValueError(f"empty blind_id in {label}")
        if blind_id in indexed:
            raise ValueError(f"duplicate blind_id in {label}: {blind_id}")
        indexed[blind_id] = row
    return indexed


def issue(
    issues: list[dict[str, str]],
    *,
    severity: str,
    annotator: str,
    blind_id: str,
    original_id: str,
    code: str,
    detail: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "annotator": annotator,
            "blind_id": blind_id,
            "original_id": original_id,
            "code": code,
            "detail": detail,
        }
    )


def find_occurrences(text: str, span: str) -> list[tuple[int, int]]:
    occurrences: list[tuple[int, int]] = []
    start = 0
    while True:
        index = text.find(span, start)
        if index < 0:
            return occurrences
        occurrences.append((index, index + len(span)))
        start = index + 1


def validate_entities(
    row: dict[str, str],
    *,
    annotator: str,
    original_id: str,
    issues: list[dict[str, str]],
) -> tuple[set[tuple[int, int, str]], bool]:
    blind_id = row["blind_id"]
    text = row["text"]
    serialized = row["entities_json"]
    if not serialized.strip():
        issue(
            issues,
            severity=HARD_ERROR,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="EMPTY_ENTITIES_FIELD",
            detail="Use [] for a completed zero-entity decision; blank is incomplete.",
        )
        return set(), False
    try:
        entities = json.loads(serialized)
    except json.JSONDecodeError as exc:
        issue(
            issues,
            severity=HARD_ERROR,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="INVALID_ENTITIES_JSON",
            detail=f"{exc.msg} at character {exc.pos}",
        )
        return set(), False
    if not isinstance(entities, list):
        issue(
            issues,
            severity=HARD_ERROR,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="ENTITIES_NOT_LIST",
            detail="entities_json must decode to a JSON array.",
        )
        return set(), False

    parsed: list[tuple[int, int, str, str]] = []
    row_valid = True
    for entity_index, entity in enumerate(entities):
        prefix = f"entity[{entity_index}]"
        if not isinstance(entity, dict):
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="ENTITY_NOT_OBJECT",
                detail=f"{prefix} must be an object.",
            )
            row_valid = False
            continue
        if set(entity) != ENTITY_FIELDS:
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="ENTITY_FIELD_MISMATCH",
                detail=f"{prefix} fields are {sorted(entity)}.",
            )
            row_valid = False
            continue
        start = entity["start"]
        end = entity["end"]
        entity_type = entity["type"]
        span = entity["span"]
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
        ):
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="NON_INTEGER_OFFSET",
                detail=f"{prefix} start/end must be integers.",
            )
            row_valid = False
            continue
        if not isinstance(entity_type, str) or entity_type not in ENTITY_TYPES:
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="INVALID_ENTITY_TYPE",
                detail=f"{prefix} type is {entity_type!r}.",
            )
            row_valid = False
            continue
        if not isinstance(span, str) or not span:
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="INVALID_SPAN_VALUE",
                detail=f"{prefix} span must be a non-empty string.",
            )
            row_valid = False
            continue
        if not (0 <= start < end <= len(text)):
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="OFFSET_OUT_OF_RANGE",
                detail=f"{prefix} has [{start},{end}) for text length {len(text)}.",
            )
            row_valid = False
            continue
        if text[start:end] != span:
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="SPAN_TEXT_MISMATCH",
                detail=f"{prefix} [{start},{end}) does not equal its span.",
            )
            row_valid = False
            continue
        parsed.append((start, end, entity_type, span))

    keys = [(start, end, entity_type) for start, end, entity_type, _ in parsed]
    duplicate_keys = [key for key, count in Counter(keys).items() if count > 1]
    for start, end, entity_type in duplicate_keys:
        issue(
            issues,
            severity=HARD_ERROR,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="DUPLICATE_ENTITY",
            detail=f"Duplicate ({start},{end},{entity_type}).",
        )
        row_valid = False

    sorted_parsed = sorted(parsed, key=lambda item: (item[0], item[1], item[2], item[3]))
    if parsed != sorted_parsed:
        issue(
            issues,
            severity=HARD_ERROR,
            annotator=annotator,
            blind_id=blind_id,
            original_id=original_id,
            code="ENTITIES_NOT_SORTED",
            detail="Entities must be sorted by start/end/type.",
        )
        row_valid = False

    for previous, current in zip(sorted_parsed, sorted_parsed[1:]):
        if current[0] < previous[1] and current[:3] != previous[:3]:
            issue(
                issues,
                severity=HARD_ERROR,
                annotator=annotator,
                blind_id=blind_id,
                original_id=original_id,
                code="OVERLAPPING_ENTITIES",
                detail=(
                    f"[{previous[0]},{previous[1]}) overlaps "
                    f"[{current[0]},{current[1]})."
                ),
            )
            row_valid = False

    if row_valid:
        intervals = [(start, end) for start, end, _, _ in parsed]
        surfaces = sorted({span for _, _, _, span in parsed})
        reported: set[tuple[str, int, int]] = set()
        for surface in surfaces:
            for start, end in find_occurrences(text, surface):
                covered = any(left <= start and end <= right for left, right in intervals)
                candidate = (surface, start, end)
                if covered or candidate in reported:
                    continue
                reported.add(candidate)
                issue(
                    issues,
                    severity=BLOCKING_REVIEW,
                    annotator=annotator,
                    blind_id=blind_id,
                    original_id=original_id,
                    code="REPEATED_MENTION_UNRESOLVED",
                    detail=f"Surface {surface!r} also occurs at [{start},{end}) uncovered.",
                )

    return set(keys), row_valid


def score_sets(
    paired: list[tuple[set[tuple[int, int, str]], set[tuple[int, int, str]]]],
    entity_type: str | None = None,
) -> dict[str, Any]:
    a_count = 0
    b_count = 0
    matches = 0
    for a_entities, b_entities in paired:
        if entity_type is not None:
            a_entities = {item for item in a_entities if item[2] == entity_type}
            b_entities = {item for item in b_entities if item[2] == entity_type}
        a_count += len(a_entities)
        b_count += len(b_entities)
        matches += len(a_entities & b_entities)
    precision = matches / b_count if b_count else (1.0 if a_count == 0 else 0.0)
    recall = matches / a_count if a_count else (1.0 if b_count == 0 else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "annotator_a_entities": a_count,
        "annotator_b_entities": b_count,
        "exact_matches": matches,
        "precision_b_vs_a": precision,
        "recall_b_vs_a": recall,
        "f1": f1,
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


def jsonl_payload(rows: list[dict[str, Any]]) -> bytes:
    return (
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in rows
        )
        + ("\n" if rows else "")
    ).encode("utf-8")


def write_bytes_atomic(path: Path, payload: bytes) -> None:
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


def file_metadata(path: Path, role: str, rows: int | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "path": str(path),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if rows is not None:
        metadata["rows"] = rows
    return metadata


def validate_qa2(
    config: ValidationConfig,
    *,
    expected_hashes: ExpectedHashes = ExpectedHashes(),
    expected_rows: int = EXPECTED_ROWS,
) -> dict[str, Any]:
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output: {config.output_dir}")
    locked_inputs = (
        (config.annotator_a_completed, expected_hashes.annotator_a_completed, "A completed"),
        (config.annotator_b_completed, expected_hashes.annotator_b_completed, "B completed"),
        (config.annotator_a_blank, expected_hashes.annotator_a_blank, "A blank"),
        (config.annotator_b_blank, expected_hashes.annotator_b_blank, "B blank"),
        (config.blind_map, expected_hashes.blind_map, "blind map"),
    )
    for path, expected_hash, label in locked_inputs:
        require_hash(path, expected_hash, label)

    blank_a_rows = read_csv(config.annotator_a_blank)
    blank_b_rows = read_csv(config.annotator_b_blank)
    completed_a_rows = read_csv(config.annotator_a_completed)
    completed_b_rows = read_csv(config.annotator_b_completed)
    map_rows = read_jsonl(config.blind_map)
    for label, rows in (
        ("A blank", blank_a_rows),
        ("B blank", blank_b_rows),
        ("A completed", completed_a_rows),
        ("B completed", completed_b_rows),
        ("blind map", map_rows),
    ):
        if len(rows) != expected_rows:
            raise ValueError(f"{label} expected {expected_rows} rows, got {len(rows)}")

    blank_a = index_rows(blank_a_rows, "A blank")
    blank_b = index_rows(blank_b_rows, "B blank")
    completed_a = index_rows(completed_a_rows, "A completed")
    completed_b = index_rows(completed_b_rows, "B completed")
    if set(blank_a) != set(completed_a):
        raise ValueError("A completed blind IDs do not match A blank sheet")
    if set(blank_b) != set(completed_b):
        raise ValueError("B completed blind IDs do not match B blank sheet")
    for blind_id, completed in completed_a.items():
        if completed["text"] != blank_a[blind_id]["text"]:
            raise ValueError(f"A completed text changed for {blind_id}")
    for blind_id, completed in completed_b.items():
        if completed["text"] != blank_b[blind_id]["text"]:
            raise ValueError(f"B completed text changed for {blind_id}")

    map_by_original: dict[str, dict[str, Any]] = {}
    seen_a_ids: set[str] = set()
    seen_b_ids: set[str] = set()
    for row in map_rows:
        if set(row) != MAP_FIELDS:
            raise ValueError(f"blind map field mismatch: {sorted(row)}")
        original_id = row["original_id"]
        a_id = row["annotator_a_blind_id"]
        b_id = row["annotator_b_blind_id"]
        if original_id in map_by_original or a_id in seen_a_ids or b_id in seen_b_ids:
            raise ValueError("duplicate ID in blind map")
        if a_id not in completed_a or b_id not in completed_b:
            raise ValueError(f"blind map references missing completed row: {original_id}")
        a_text = completed_a[a_id]["text"]
        b_text = completed_b[b_id]["text"]
        if a_text != b_text or text_sha256(a_text) != row["text_sha256"]:
            raise ValueError(f"blind map text/hash mismatch: {original_id}")
        map_by_original[original_id] = row
        seen_a_ids.add(a_id)
        seen_b_ids.add(b_id)

    issues: list[dict[str, str]] = []
    parsed_a: dict[str, set[tuple[int, int, str]]] = {}
    parsed_b: dict[str, set[tuple[int, int, str]]] = {}
    valid_a: dict[str, bool] = {}
    valid_b: dict[str, bool] = {}
    for original_id, mapping in sorted(map_by_original.items()):
        a_id = mapping["annotator_a_blind_id"]
        b_id = mapping["annotator_b_blind_id"]
        parsed_a[original_id], valid_a[original_id] = validate_entities(
            completed_a[a_id],
            annotator="A",
            original_id=original_id,
            issues=issues,
        )
        parsed_b[original_id], valid_b[original_id] = validate_entities(
            completed_b[b_id],
            annotator="B",
            original_id=original_id,
            issues=issues,
        )

    core_valid_ids = [
        original_id
        for original_id in sorted(map_by_original)
        if valid_a[original_id] and valid_b[original_id]
    ]
    paired = [(parsed_a[original_id], parsed_b[original_id]) for original_id in core_valid_ids]
    diagnostic = score_sets(paired)
    diagnostic["paired_rows"] = len(core_valid_ids)
    diagnostic["row_exact_matches"] = sum(
        parsed_a[original_id] == parsed_b[original_id] for original_id in core_valid_ids
    )
    diagnostic["row_exact_rate"] = (
        diagnostic["row_exact_matches"] / len(core_valid_ids) if core_valid_ids else 0.0
    )
    per_type = {entity_type: score_sets(paired, entity_type) for entity_type in ENTITY_TYPES}

    disagreements: list[dict[str, Any]] = []
    for original_id in core_valid_ids:
        a_only = sorted(parsed_a[original_id] - parsed_b[original_id])
        b_only = sorted(parsed_b[original_id] - parsed_a[original_id])
        if not a_only and not b_only:
            continue
        mapping = map_by_original[original_id]
        disagreements.append(
            {
                "original_id": original_id,
                "annotator_a_blind_id": mapping["annotator_a_blind_id"],
                "annotator_b_blind_id": mapping["annotator_b_blind_id"],
                "annotator_a_only": [
                    {"start": start, "end": end, "type": entity_type}
                    for start, end, entity_type in a_only
                ],
                "annotator_b_only": [
                    {"start": start, "end": end, "type": entity_type}
                    for start, end, entity_type in b_only
                ],
            }
        )

    severity_counts = Counter(item["severity"] for item in issues)
    code_counts = Counter(item["code"] for item in issues)
    hard_errors = severity_counts[HARD_ERROR]
    blocking_reviews = severity_counts[BLOCKING_REVIEW]
    full_file_concordance_computable = hard_errors == 0
    file_quality_gate_passed = (
        hard_errors == 0
        and blocking_reviews == 0
        and diagnostic["paired_rows"] == expected_rows
        and diagnostic["f1"] >= 0.80
    )
    report = {
        "phase": "P6-QA2",
        "status": "file_quality_passed" if file_quality_gate_passed else "blocked",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "task": "NER",
            "expected_rows": expected_rows,
            "old_gold_read": False,
            "predictions_read": False,
            "model_calls": False,
            "labels_modified": False,
            "human_independence_provenance_assessed_by_validator": False,
        },
        "inputs": {
            label: {"path": str(path), "sha256": sha256_file(path)}
            for path, _, label in locked_inputs
        },
        "alignment": {
            "map_rows": len(map_rows),
            "a_rows": len(completed_a_rows),
            "b_rows": len(completed_b_rows),
            "blind_ids_and_text_hashes_matched": True,
        },
        "validation": {
            "hard_error_count": hard_errors,
            "blocking_review_count": blocking_reviews,
            "issue_count": len(issues),
            "severity_counts": dict(sorted(severity_counts.items())),
            "code_counts": dict(sorted(code_counts.items())),
            "core_valid_paired_rows": len(core_valid_ids),
            "full_file_concordance_computable": full_file_concordance_computable,
            "file_quality_gate_passed": file_quality_gate_passed,
        },
        "diagnostic_file_concordance": diagnostic,
        "diagnostic_per_type": per_type,
        "formal_human_iaa": None,
        "formal_human_iaa_reason": (
            "File validation cannot establish independent human provenance; "
            "the coordinator must assess provenance separately."
        ),
        "disagreement_rows": len(disagreements),
        "thresholds": {"minimum_f1": 0.80, "preferred_f1": 0.85},
    }

    output_parent = config.output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = output_parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        report_path = staging / "validation_report.json"
        issues_path = staging / "issues.csv"
        disagreements_path = staging / "disagreements.jsonl"
        write_bytes_atomic(
            report_path,
            (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        write_bytes_atomic(
            issues_path,
            csv_payload(
                issues,
                ("severity", "annotator", "blind_id", "original_id", "code", "detail"),
            ),
        )
        write_bytes_atomic(disagreements_path, jsonl_payload(disagreements))
        final_paths = {
            "validation_report": config.output_dir / report_path.name,
            "issues": config.output_dir / issues_path.name,
            "disagreements": config.output_dir / disagreements_path.name,
        }
        manifest = {
            "phase": "P6-QA2",
            "status": report["status"],
            "created_at": report["created_at"],
            "safeguards": {
                "locked_input_hashes": True,
                "no_old_gold_or_predictions": True,
                "no_model_calls": True,
                "no_silent_repair": True,
                "existing_output_overwrite_refused": True,
                "coordinator_only_output": True,
            },
            "outputs": {
                "validation_report": file_metadata(report_path, "coordinator_only")
                | {"path": str(final_paths["validation_report"])},
                "issues": file_metadata(issues_path, "coordinator_only", len(issues))
                | {"path": str(final_paths["issues"])},
                "disagreements": file_metadata(
                    disagreements_path, "coordinator_only", len(disagreements)
                )
                | {"path": str(final_paths["disagreements"])},
            },
        }
        manifest_path = staging / "manifest.json"
        write_bytes_atomic(
            manifest_path,
            (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
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
    config = ValidationConfig(
        annotator_a_completed=Path(args.annotator_a_completed),
        annotator_b_completed=Path(args.annotator_b_completed),
        annotator_a_blank=Path(args.annotator_a_blank),
        annotator_b_blank=Path(args.annotator_b_blank),
        blind_map=Path(args.blind_map),
        output_dir=Path(args.output_dir),
    )
    report = validate_qa2(config)
    print(
        json.dumps(
            {
                "status": report["status"],
                "hard_errors": report["validation"]["hard_error_count"],
                "blocking_reviews": report["validation"]["blocking_review_count"],
                "paired_rows": report["diagnostic_file_concordance"]["paired_rows"],
                "diagnostic_f1": report["diagnostic_file_concordance"]["f1"],
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
