#!/usr/bin/env python3
"""Classify P6-QA2 file disagreements for annotation-guideline repair.

Run only on AutoDL in GPU-free mode. The inputs are the already locked QA2
diagnostic artifacts and submitted A/B CSVs. The outputs are diagnostic only:
they do not establish human provenance, repair annotations, read frozen gold or
predictions, or authorize adjudication.
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


EXPECTED_A_SHA256 = "f07a650688c9cafcf4d16f5be906a0f45a3623838994cc9af2954385eb2183b7"
EXPECTED_B_SHA256 = "90e8e2458de3dd1f847a730759a353efb0a493bbbe385bbaa88fecf6acccd8ef"
EXPECTED_REPORT_SHA256 = (
    "aa614ad12cf9b7babf0ebb0e950ec44b960cb259226027142c7a0180acef6292"
)
EXPECTED_ISSUES_SHA256 = (
    "c66181a7af82e796d2bb2de00c872c438a1ac1ee47c19eec8b3097658f746e18"
)
EXPECTED_DISAGREEMENTS_SHA256 = (
    "19192b8880dc3acadd2312cb63afd41b2b0048619f621f6cd237f7f2910ada5c"
)
CSV_FIELDS = ("blind_id", "text", "entities_json", "notes")


@dataclass(frozen=True)
class AnalysisConfig:
    annotator_a_completed: Path
    annotator_b_completed: Path
    validation_report: Path
    issues_csv: Path
    disagreements_jsonl: Path
    output_dir: Path


@dataclass(frozen=True)
class ExpectedHashes:
    annotator_a_completed: str = EXPECTED_A_SHA256
    annotator_b_completed: str = EXPECTED_B_SHA256
    validation_report: str = EXPECTED_REPORT_SHA256
    issues_csv: str = EXPECTED_ISSUES_SHA256
    disagreements_jsonl: str = EXPECTED_DISAGREEMENTS_SHA256


def parse_args() -> argparse.Namespace:
    qa2_input_root = "/root/autodl-tmp/backup/p6/p6_qa2_inputs_20260726"
    qa2_root = "/root/autodl-tmp/backup/p6/p6_qa2_annotation_validation_20260726"
    parser = argparse.ArgumentParser(
        description="Classify existing P6-QA2 diagnostic disagreements."
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
        "--validation-report", default=f"{qa2_root}/validation_report.json"
    )
    parser.add_argument("--issues-csv", default=f"{qa2_root}/issues.csv")
    parser.add_argument(
        "--disagreements-jsonl", default=f"{qa2_root}/disagreements.jsonl"
    )
    parser.add_argument(
        "--output-dir",
        default="/root/autodl-tmp/backup/p6/p6_qa1r_diagnosis_20260726",
    )
    return parser.parse_args()


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ValueError(f"CSV field mismatch in {path}: {reader.fieldnames}")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"malformed CSV cells in {path}")
    return rows


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(value)
    return rows


def index_csv(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        blind_id = row["blind_id"]
        if not blind_id or blind_id in indexed:
            raise ValueError(f"empty or duplicate blind_id in {label}: {blind_id!r}")
        indexed[blind_id] = row
    return indexed


def entity_key(entity: dict[str, Any]) -> tuple[int, int, str]:
    start = entity.get("start")
    end = entity.get("end")
    entity_type = entity.get("type")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or not isinstance(entity_type, str)
        or start < 0
        or end <= start
    ):
        raise ValueError(f"invalid disagreement entity: {entity!r}")
    return start, end, entity_type


def overlaps(left: tuple[int, int, str], right: tuple[int, int, str]) -> bool:
    return max(left[0], right[0]) < min(left[1], right[1])


def overlap_iou(left: tuple[int, int, str], right: tuple[int, int, str]) -> float:
    intersection = max(0, min(left[1], right[1]) - max(left[0], right[0]))
    union = max(left[1], right[1]) - min(left[0], right[0])
    return intersection / union if union else 0.0


def classify_disagreement(
    a_only_raw: list[dict[str, Any]],
    b_only_raw: list[dict[str, Any]],
) -> dict[str, Any]:
    """Pair exact-boundary and overlapping disagreements deterministically."""

    a_entities = [entity_key(entity) for entity in a_only_raw]
    b_entities = [entity_key(entity) for entity in b_only_raw]
    remaining_a = set(range(len(a_entities)))
    remaining_b = set(range(len(b_entities)))
    pairs: list[dict[str, Any]] = []

    for a_index in sorted(remaining_a):
        a_entity = a_entities[a_index]
        candidates = [
            b_index
            for b_index in remaining_b
            if a_entity[:2] == b_entities[b_index][:2]
        ]
        if not candidates:
            continue
        b_index = min(candidates, key=lambda index: b_entities[index][2])
        pairs.append(
            {
                "category": "same_boundary_type_conflict",
                "a": a_entity,
                "b": b_entities[b_index],
            }
        )
        remaining_a.remove(a_index)
        remaining_b.remove(b_index)

    overlap_candidates: list[tuple[int, float, int, int]] = []
    for a_index in remaining_a:
        for b_index in remaining_b:
            a_entity = a_entities[a_index]
            b_entity = b_entities[b_index]
            if overlaps(a_entity, b_entity):
                same_type_priority = 0 if a_entity[2] == b_entity[2] else 1
                overlap_candidates.append(
                    (same_type_priority, -overlap_iou(a_entity, b_entity), a_index, b_index)
                )
    for _, _, a_index, b_index in sorted(overlap_candidates):
        if a_index not in remaining_a or b_index not in remaining_b:
            continue
        a_entity = a_entities[a_index]
        b_entity = b_entities[b_index]
        category = (
            "overlap_boundary_conflict"
            if a_entity[2] == b_entity[2]
            else "overlap_boundary_and_type_conflict"
        )
        pairs.append({"category": category, "a": a_entity, "b": b_entity})
        remaining_a.remove(a_index)
        remaining_b.remove(b_index)

    return {
        "pairs": pairs,
        "a_unmatched": [a_entities[index] for index in sorted(remaining_a)],
        "b_unmatched": [b_entities[index] for index in sorted(remaining_b)],
    }


def csv_payload(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


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


def file_metadata(path: Path, rows: int | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "role": "coordinator_only",
    }
    if rows is not None:
        metadata["rows"] = rows
    return metadata


def analyze(config: AnalysisConfig, expected: ExpectedHashes = ExpectedHashes()) -> dict[str, Any]:
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {config.output_dir}")

    locked_inputs = (
        (config.annotator_a_completed, expected.annotator_a_completed, "A completed"),
        (config.annotator_b_completed, expected.annotator_b_completed, "B completed"),
        (config.validation_report, expected.validation_report, "validation report"),
        (config.issues_csv, expected.issues_csv, "issues"),
        (config.disagreements_jsonl, expected.disagreements_jsonl, "disagreements"),
    )
    for path, expected_hash, label in locked_inputs:
        require_hash(path, expected_hash, label)

    report = read_json(config.validation_report)
    if report.get("status") != "blocked" or report.get("formal_human_iaa") is not None:
        raise ValueError("expected blocked QA2 report with null formal_human_iaa")
    disagreements = read_jsonl(config.disagreements_jsonl)
    a_rows = index_csv(read_csv(config.annotator_a_completed), "A")
    b_rows = index_csv(read_csv(config.annotator_b_completed), "B")
    with config.issues_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        issues = list(csv.DictReader(handle))

    category_counts: Counter[str] = Counter()
    category_rows: Counter[str] = Counter()
    type_confusions: Counter[tuple[str, str]] = Counter()
    row_table: list[dict[str, Any]] = []
    pair_table: list[dict[str, Any]] = []

    for disagreement in disagreements:
        original_id = disagreement.get("original_id")
        a_blind_id = disagreement.get("annotator_a_blind_id")
        b_blind_id = disagreement.get("annotator_b_blind_id")
        if not all(isinstance(value, str) and value for value in (original_id, a_blind_id, b_blind_id)):
            raise ValueError(f"invalid disagreement identity: {disagreement!r}")
        if a_blind_id not in a_rows or b_blind_id not in b_rows:
            raise ValueError(f"blind ID missing from completed CSV for {original_id}")
        text_a = a_rows[a_blind_id]["text"]
        text_b = b_rows[b_blind_id]["text"]
        if text_a != text_b:
            raise ValueError(f"A/B text mismatch for {original_id}")
        a_only = disagreement.get("annotator_a_only")
        b_only = disagreement.get("annotator_b_only")
        if not isinstance(a_only, list) or not isinstance(b_only, list):
            raise ValueError(f"invalid disagreement entity lists for {original_id}")
        classified = classify_disagreement(a_only, b_only)
        row_counts: Counter[str] = Counter()
        for pair in classified["pairs"]:
            category = pair["category"]
            category_counts[category] += 1
            row_counts[category] += 1
            a_start, a_end, a_type = pair["a"]
            b_start, b_end, b_type = pair["b"]
            type_confusions[(a_type, b_type)] += 1
            pair_table.append(
                {
                    "original_id": original_id,
                    "category": category,
                    "a_start": a_start,
                    "a_end": a_end,
                    "a_type": a_type,
                    "a_span": text_a[a_start:a_end],
                    "b_start": b_start,
                    "b_end": b_end,
                    "b_type": b_type,
                    "b_span": text_a[b_start:b_end],
                }
            )
        for side, unmatched in (
            ("a_unmatched", classified["a_unmatched"]),
            ("b_unmatched", classified["b_unmatched"]),
        ):
            category_counts[side] += len(unmatched)
            row_counts[side] += len(unmatched)
            for start, end, entity_type in unmatched:
                pair_table.append(
                    {
                        "original_id": original_id,
                        "category": side,
                        "a_start": start if side == "a_unmatched" else "",
                        "a_end": end if side == "a_unmatched" else "",
                        "a_type": entity_type if side == "a_unmatched" else "",
                        "a_span": text_a[start:end] if side == "a_unmatched" else "",
                        "b_start": start if side == "b_unmatched" else "",
                        "b_end": end if side == "b_unmatched" else "",
                        "b_type": entity_type if side == "b_unmatched" else "",
                        "b_span": text_a[start:end] if side == "b_unmatched" else "",
                    }
                )
        for category in row_counts:
            category_rows[category] += 1
        row_table.append(
            {
                "original_id": original_id,
                "same_boundary_type_conflict": row_counts["same_boundary_type_conflict"],
                "overlap_boundary_conflict": row_counts["overlap_boundary_conflict"],
                "overlap_boundary_and_type_conflict": row_counts[
                    "overlap_boundary_and_type_conflict"
                ],
                "a_unmatched": row_counts["a_unmatched"],
                "b_unmatched": row_counts["b_unmatched"],
            }
        )

    issue_code_counts = Counter(row.get("code", "") for row in issues)
    issue_annotator_counts = Counter(
        (row.get("annotator", ""), row.get("code", "")) for row in issues
    )
    summary = {
        "phase": "P6-QA1R-DIAGNOSIS",
        "status": "diagnostic_only_not_human_iaa",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "old_frozen_gold_read": False,
            "predictions_read": False,
            "model_calls": False,
            "labels_modified": False,
            "adjudication_performed": False,
        },
        "source_qa2": {
            "status": report["status"],
            "formal_human_iaa": report["formal_human_iaa"],
            "diagnostic_f1": report["diagnostic_file_concordance"]["f1"],
            "paired_rows": report["diagnostic_file_concordance"]["paired_rows"],
            "disagreement_rows": len(disagreements),
        },
        "issue_code_counts": dict(sorted(issue_code_counts.items())),
        "issue_by_annotator": {
            f"{annotator}:{code}": count
            for (annotator, code), count in sorted(issue_annotator_counts.items())
        },
        "entity_disagreement_counts": dict(sorted(category_counts.items())),
        "rows_affected_by_category": dict(sorted(category_rows.items())),
        "same_or_overlapping_type_confusions": {
            f"{a_type}->{b_type}": count
            for (a_type, b_type), count in sorted(type_confusions.items())
        },
        "interpretation_guardrail": (
            "These are file-disagreement diagnostics from provenance-invalid inputs, "
            "not independent human disagreement rates or formal IAA."
        ),
    }

    output_parent = config.output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = output_parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        summary_path = staging / "summary.json"
        row_path = staging / "taxonomy_by_row.csv"
        pair_path = staging / "disagreement_pairs.csv"
        write_atomic(
            summary_path,
            (json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        write_atomic(
            row_path,
            csv_payload(
                row_table,
                (
                    "original_id",
                    "same_boundary_type_conflict",
                    "overlap_boundary_conflict",
                    "overlap_boundary_and_type_conflict",
                    "a_unmatched",
                    "b_unmatched",
                ),
            ),
        )
        write_atomic(
            pair_path,
            csv_payload(
                pair_table,
                (
                    "original_id",
                    "category",
                    "a_start",
                    "a_end",
                    "a_type",
                    "a_span",
                    "b_start",
                    "b_end",
                    "b_type",
                    "b_span",
                ),
            ),
        )
        final_paths = {
            "summary": config.output_dir / summary_path.name,
            "taxonomy_by_row": config.output_dir / row_path.name,
            "disagreement_pairs": config.output_dir / pair_path.name,
        }
        manifest = {
            "phase": "P6-QA1R-DIAGNOSIS",
            "status": summary["status"],
            "created_at": summary["created_at"],
            "inputs": {
                label: {"path": str(path), "sha256": sha256_file(path)}
                for path, _, label in locked_inputs
            },
            "safeguards": {
                "locked_input_hashes": True,
                "diagnostic_only": True,
                "no_gold_or_predictions": True,
                "no_model_calls": True,
                "no_label_repair": True,
                "existing_output_overwrite_refused": True,
            },
            "outputs": {
                "summary": file_metadata(summary_path)
                | {"path": str(final_paths["summary"])},
                "taxonomy_by_row": file_metadata(row_path, len(row_table))
                | {"path": str(final_paths["taxonomy_by_row"])},
                "disagreement_pairs": file_metadata(pair_path, len(pair_table))
                | {"path": str(final_paths["disagreement_pairs"])},
            },
        }
        manifest_path = staging / "manifest.json"
        write_atomic(
            manifest_path,
            (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        for path in (summary_path, row_path, pair_path, manifest_path):
            os.chmod(path, 0o600)
        os.replace(staging, config.output_dir)
        os.chmod(config.output_dir, 0o700)
        return summary
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    config = AnalysisConfig(
        annotator_a_completed=Path(args.annotator_a_completed),
        annotator_b_completed=Path(args.annotator_b_completed),
        validation_report=Path(args.validation_report),
        issues_csv=Path(args.issues_csv),
        disagreements_jsonl=Path(args.disagreements_jsonl),
        output_dir=Path(args.output_dir),
    )
    summary = analyze(config)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "diagnostic_f1": summary["source_qa2"]["diagnostic_f1"],
                "disagreement_rows": summary["source_qa2"]["disagreement_rows"],
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
