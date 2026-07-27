#!/usr/bin/env python3
"""Validate completed P6-QA1R non-test calibration sheets.

Run only on AutoDL in GPU-free mode. This locks the blank and completed
calibration sheets plus coordinator map, checks structure and text alignment,
and computes exact span+type file concordance. It does not read existing dev
gold, frozen test, predictions, prompts, or model outputs; it does not repair
labels or establish independent human provenance.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from validate_p6_qa2_annotations import (
    BLOCKING_REVIEW,
    ENTITY_TYPES,
    HARD_ERROR,
    csv_payload,
    file_metadata,
    jsonl_payload,
    require_hash,
    score_sets,
    sha256_file,
    text_sha256,
    validate_entities,
    write_bytes_atomic,
)


EXPECTED_ROWS = 24
EXPECTED_BLANK_A_SHA256 = "a9d36939a8e91f5ee90b3b7b67740416976e3662a1eec1469e72df7abdb7bc38"
EXPECTED_BLANK_B_SHA256 = "ce6c9771bf17815280215382b67089e125362fb079a544a137e16f0d82fe3d00"
EXPECTED_COMPLETED_A_SHA256 = "36613af484210ea7b916e744e1785b37ee5c47ed7bf41149ef5ac19af230bb0a"
EXPECTED_COMPLETED_B_SHA256 = "9017bf65c8bd5e02a529bdef73f0ff845edc46d4471a84d80bb72615fc7aa8c7"
EXPECTED_MAP_SHA256 = "a42511bd41bef0666c703c8d4e6ca1eb623688bba0e3b872786f164fedb3b18b"
CSV_FIELDS = (
    "blind_id",
    "text",
    "entities_json",
    "notes",
    "uncertainty_code",
)
MAP_FIELDS = {
    "original_id",
    "annotator_a_blind_id",
    "annotator_b_blind_id",
    "text_sha256",
    "selection_bucket",
}
ALLOWED_UNCERTAINTY_CODES = {
    "TYPE_EQUIPMENT_MODULE",
    "TYPE_PHYSICAL_TECH",
    "BOUNDARY",
    "METRIC_SCOPE",
    "REPEATED_MENTION",
    "EXCLUDE_OR_TAG",
    "OTHER",
}


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


def parse_args() -> argparse.Namespace:
    root = "/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726"
    parser = argparse.ArgumentParser(
        description="Validate completed P6-QA1R non-test calibration sheets."
    )
    parser.add_argument(
        "--annotator-a-completed",
        default=f"{root}/annotator_a_calibration_completed.csv",
    )
    parser.add_argument(
        "--annotator-b-completed",
        default=f"{root}/annotator_b_calibration_completed.csv",
    )
    parser.add_argument(
        "--annotator-a-blank", default=f"{root}/annotator_a_calibration.csv"
    )
    parser.add_argument(
        "--annotator-b-blank", default=f"{root}/annotator_b_calibration.csv"
    )
    parser.add_argument("--coordinator-map", default=f"{root}/coordinator_map.jsonl")
    parser.add_argument(
        "--output-dir",
        default=(
            "/root/autodl-tmp/backup/p6/"
            "p6_qa1r_calibration_validation_20260727"
        ),
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError(f"CSV field mismatch in {path}: {reader.fieldnames}")
        rows = list(reader)
    for index, row in enumerate(rows, start=1):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"malformed CSV cells at {path}:{index}")
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
        if not blind_id or blind_id in indexed:
            raise ValueError(f"empty or duplicate blind_id in {label}: {blind_id!r}")
        indexed[blind_id] = row
    return indexed


def uncertainty_codes(value: str) -> list[str]:
    if not value.strip():
        return []
    codes = [item.strip() for item in value.split(";") if item.strip()]
    invalid = sorted(set(codes) - ALLOWED_UNCERTAINTY_CODES)
    if invalid:
        raise ValueError(f"invalid uncertainty code(s): {invalid}")
    return codes


def validate_calibration(
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
        (config.coordinator_map, expected_hashes.coordinator_map, "coordinator map"),
    )
    for path, expected_hash, label in locked_inputs:
        require_hash(path, expected_hash, label)

    blank_a_rows = read_csv(config.annotator_a_blank)
    blank_b_rows = read_csv(config.annotator_b_blank)
    completed_a_rows = read_csv(config.annotator_a_completed)
    completed_b_rows = read_csv(config.annotator_b_completed)
    map_rows = read_jsonl(config.coordinator_map)
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
    seen_a: set[str] = set()
    seen_b: set[str] = set()
    bucket_counts: Counter[str] = Counter()
    for row in map_rows:
        if set(row) != MAP_FIELDS:
            raise ValueError(f"coordinator map field mismatch: {sorted(row)}")
        original_id = row["original_id"]
        a_id = row["annotator_a_blind_id"]
        b_id = row["annotator_b_blind_id"]
        if original_id in map_by_original or a_id in seen_a or b_id in seen_b:
            raise ValueError("duplicate ID in coordinator map")
        if a_id not in completed_a or b_id not in completed_b:
            raise ValueError(f"coordinator map references missing row: {original_id}")
        a_text = completed_a[a_id]["text"]
        b_text = completed_b[b_id]["text"]
        if a_text != b_text or text_sha256(a_text) != row["text_sha256"]:
            raise ValueError(f"coordinator map text/hash mismatch: {original_id}")
        map_by_original[original_id] = row
        seen_a.add(a_id)
        seen_b.add(b_id)
        bucket_counts[row["selection_bucket"]] += 1

    issues: list[dict[str, str]] = []
    parsed_a: dict[str, set[tuple[int, int, str]]] = {}
    parsed_b: dict[str, set[tuple[int, int, str]]] = {}
    valid_a: dict[str, bool] = {}
    valid_b: dict[str, bool] = {}
    uncertainty_by_annotator: Counter[tuple[str, str]] = Counter()
    uncertainty_rows: Counter[str] = Counter()
    for original_id, mapping in sorted(map_by_original.items()):
        a_id = mapping["annotator_a_blind_id"]
        b_id = mapping["annotator_b_blind_id"]
        for annotator, row in (("A", completed_a[a_id]), ("B", completed_b[b_id])):
            codes = uncertainty_codes(row["uncertainty_code"])
            duplicate_codes = sorted(
                code for code, count in Counter(codes).items() if count > 1
            )
            if duplicate_codes:
                issues.append(
                    {
                        "severity": "warning",
                        "annotator": annotator,
                        "blind_id": row["blind_id"],
                        "original_id": original_id,
                        "code": "DUPLICATE_UNCERTAINTY_CODE",
                        "detail": f"Repeated row-level codes: {duplicate_codes}",
                    }
                )
            if codes:
                uncertainty_rows[annotator] += 1
            for code in sorted(set(codes)):
                uncertainty_by_annotator[(annotator, code)] += 1
        parsed_a[original_id], valid_a[original_id] = validate_entities(
            completed_a[a_id], annotator="A", original_id=original_id, issues=issues
        )
        parsed_b[original_id], valid_b[original_id] = validate_entities(
            completed_b[b_id], annotator="B", original_id=original_id, issues=issues
        )

    valid_ids = [
        original_id
        for original_id in sorted(map_by_original)
        if valid_a[original_id] and valid_b[original_id]
    ]
    paired = [(parsed_a[original_id], parsed_b[original_id]) for original_id in valid_ids]
    concordance = score_sets(paired)
    concordance["paired_rows"] = len(valid_ids)
    concordance["row_exact_matches"] = sum(
        parsed_a[original_id] == parsed_b[original_id] for original_id in valid_ids
    )
    concordance["row_exact_rate"] = (
        concordance["row_exact_matches"] / len(valid_ids) if valid_ids else 0.0
    )
    per_type = {entity_type: score_sets(paired, entity_type) for entity_type in ENTITY_TYPES}

    disagreements: list[dict[str, Any]] = []
    for original_id in valid_ids:
        a_only = sorted(parsed_a[original_id] - parsed_b[original_id])
        b_only = sorted(parsed_b[original_id] - parsed_a[original_id])
        if not a_only and not b_only:
            continue
        mapping = map_by_original[original_id]
        disagreements.append(
            {
                "original_id": original_id,
                "selection_bucket": mapping["selection_bucket"],
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
    non_order_hard_errors = sum(
        item["severity"] == HARD_ERROR and item["code"] != "ENTITIES_NOT_SORTED"
        for item in issues
    )
    all_rows_order_insensitive = None
    all_rows_order_insensitive_per_type = None
    if non_order_hard_errors == 0:
        all_ids = sorted(map_by_original)
        all_paired = [(parsed_a[original_id], parsed_b[original_id]) for original_id in all_ids]
        all_rows_order_insensitive = score_sets(all_paired)
        all_rows_order_insensitive["paired_rows"] = len(all_ids)
        all_rows_order_insensitive["row_exact_matches"] = sum(
            parsed_a[original_id] == parsed_b[original_id] for original_id in all_ids
        )
        all_rows_order_insensitive["row_exact_rate"] = (
            all_rows_order_insensitive["row_exact_matches"] / len(all_ids)
            if all_ids
            else 0.0
        )
        all_rows_order_insensitive_per_type = {
            entity_type: score_sets(all_paired, entity_type)
            for entity_type in ENTITY_TYPES
        }
    all_types_covered_by_both = all(
        values["annotator_a_entities"] > 0 and values["annotator_b_entities"] > 0
        for values in per_type.values()
    )
    agreement_target_met = (
        hard_errors == 0
        and blocking_reviews == 0
        and len(valid_ids) == expected_rows
        and concordance["f1"] >= 0.85
        and all_types_covered_by_both
    )
    report = {
        "phase": "P6-QA1R-CALIBRATION-VALIDATION",
        "status": "calibration_target_met" if agreement_target_met else "blocked",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "source_split": "domain_dev",
            "expected_rows": expected_rows,
            "formal_test_iaa": False,
            "old_dev_gold_read": False,
            "frozen_test_read": False,
            "predictions_read": False,
            "model_calls": False,
            "labels_modified": False,
            "human_independence_provenance_assessed_by_validator": False,
        },
        "alignment": {
            "a_rows": len(completed_a_rows),
            "b_rows": len(completed_b_rows),
            "map_rows": len(map_rows),
            "blind_ids_texts_and_hashes_matched": True,
            "selection_bucket_counts": dict(sorted(bucket_counts.items())),
        },
        "validation": {
            "hard_error_count": hard_errors,
            "non_order_hard_error_count": non_order_hard_errors,
            "blocking_review_count": blocking_reviews,
            "issue_count": len(issues),
            "severity_counts": dict(sorted(severity_counts.items())),
            "code_counts": dict(sorted(code_counts.items())),
            "valid_paired_rows": len(valid_ids),
            "all_types_covered_by_both": all_types_covered_by_both,
            "agreement_target_met": agreement_target_met,
        },
        "calibration_file_concordance": concordance,
        "calibration_per_type": per_type,
        "secondary_all_rows_order_insensitive_concordance": all_rows_order_insensitive,
        "secondary_all_rows_order_insensitive_per_type": (
            all_rows_order_insensitive_per_type
        ),
        "secondary_diagnostic_guardrail": (
            "The order-insensitive diagnostic is reported only when every hard error is "
            "ENTITIES_NOT_SORTED. It does not pass the structural gate or authorize repair."
        ),
        "uncertainty": {
            "rows_by_annotator": dict(sorted(uncertainty_rows.items())),
            "code_counts": {
                f"{annotator}:{code}": count
                for (annotator, code), count in sorted(uncertainty_by_annotator.items())
            },
        },
        "disagreement_rows": len(disagreements),
        "thresholds": {"calibration_target_f1": 0.85, "formal_test_minimum_f1": 0.80},
        "formal_human_iaa": None,
        "provenance_note": (
            "This validator measures file concordance only. Independent human provenance "
            "requires a separate coordinator audit."
        ),
    }

    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = config.output_dir.parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
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
            "phase": "P6-QA1R-CALIBRATION-VALIDATION",
            "status": report["status"],
            "created_at": report["created_at"],
            "inputs": {
                label: {"path": str(path), "sha256": sha256_file(path)}
                for path, _, label in locked_inputs
            },
            "safeguards": {
                "locked_input_hashes": True,
                "no_dev_gold_test_or_predictions": True,
                "no_model_calls": True,
                "no_label_repair": True,
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
        coordinator_map=Path(args.coordinator_map),
        output_dir=Path(args.output_dir),
    )
    report = validate_calibration(config)
    print(
        json.dumps(
            {
                "status": report["status"],
                "hard_errors": report["validation"]["hard_error_count"],
                "blocking_reviews": report["validation"]["blocking_review_count"],
                "paired_rows": report["calibration_file_concordance"]["paired_rows"],
                "file_f1": report["calibration_file_concordance"]["f1"],
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
