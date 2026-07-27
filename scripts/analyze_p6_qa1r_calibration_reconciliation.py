#!/usr/bin/env python3
"""Analyze the locked P6-QA1R calibration disagreements for guideline v4.

Run only on AutoDL in GPU-free mode. The output is coordinator-only diagnostic
material. It does not modify submitted labels, establish human provenance,
read dev/test gold or predictions, adjudicate examples, or generate a new
calibration set.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from analyze_p6_qa2_disagreements import classify_disagreement
from validate_p6_qa1r_calibration import (
    MAP_FIELDS,
    index_rows,
    read_csv,
    read_jsonl,
)
from validate_p6_qa2_annotations import (
    BLOCKING_REVIEW,
    HARD_ERROR,
    csv_payload,
    file_metadata,
    find_occurrences,
    jsonl_payload,
    require_hash,
    sha256_file,
    text_sha256,
    validate_entities,
    write_bytes_atomic,
)


EXPECTED_ROWS = 24
EXPECTED_A_SHA256 = "36613af484210ea7b916e744e1785b37ee5c47ed7bf41149ef5ac19af230bb0a"
EXPECTED_B_SHA256 = "9017bf65c8bd5e02a529bdef73f0ff845edc46d4471a84d80bb72615fc7aa8c7"
EXPECTED_MAP_SHA256 = "a42511bd41bef0666c703c8d4e6ca1eb623688bba0e3b872786f164fedb3b18b"
EXPECTED_REPORT_SHA256 = "f8f6d7faca763aee97e5fa160482061dd838c65640613108fd18a920bcb11f1e"

Entity = tuple[int, int, str]


@dataclass(frozen=True)
class AnalysisConfig:
    annotator_a_completed: Path
    annotator_b_completed: Path
    coordinator_map: Path
    validation_report: Path
    output_dir: Path


@dataclass(frozen=True)
class ExpectedHashes:
    annotator_a_completed: str = EXPECTED_A_SHA256
    annotator_b_completed: str = EXPECTED_B_SHA256
    coordinator_map: str = EXPECTED_MAP_SHA256
    validation_report: str = EXPECTED_REPORT_SHA256


def parse_args() -> argparse.Namespace:
    calibration_root = "/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726"
    validation_root = (
        "/root/autodl-tmp/backup/p6/"
        "p6_qa1r_calibration_validation_20260727_r2"
    )
    parser = argparse.ArgumentParser(
        description="Analyze locked calibration disagreements for guideline v4."
    )
    parser.add_argument(
        "--annotator-a-completed",
        default=f"{calibration_root}/annotator_a_calibration_completed.csv",
    )
    parser.add_argument(
        "--annotator-b-completed",
        default=f"{calibration_root}/annotator_b_calibration_completed.csv",
    )
    parser.add_argument(
        "--coordinator-map", default=f"{calibration_root}/coordinator_map.jsonl"
    )
    parser.add_argument(
        "--validation-report", default=f"{validation_root}/validation_report.json"
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "/root/autodl-tmp/backup/p6/"
            "p6_qa1r_guideline_reconciliation_20260727_r2"
        ),
    )
    return parser.parse_args()


def entity_dict(entity: Entity, text: str) -> dict[str, Any]:
    start, end, entity_type = entity
    return {
        "start": start,
        "end": end,
        "type": entity_type,
        "span": text[start:end],
    }


def context_for(text: str, entities: list[Entity], radius: int = 28) -> str:
    if not entities:
        return text[: radius * 2]
    start = max(0, min(item[0] for item in entities) - radius)
    end = min(len(text), max(item[1] for item in entities) + radius)
    return text[start:end]


def repeated_mention_candidate(
    text: str,
    entity: Entity,
    other_entities: set[Entity],
) -> bool:
    """Return true for a missing occurrence of a surface/type marked elsewhere."""

    start, end, entity_type = entity
    surface = text[start:end]
    if len(find_occurrences(text, surface)) < 2:
        return False
    return any(
        other_type == entity_type and text[other_start:other_end] == surface
        for other_start, other_end, other_type in other_entities
    )


def classify_row(
    text: str,
    a_entities: set[Entity],
    b_entities: set[Entity],
) -> dict[str, Any]:
    exact = a_entities & b_entities
    a_only = a_entities - b_entities
    b_only = b_entities - a_entities
    classified = classify_disagreement(
        [entity_dict(item, text) for item in sorted(a_only)],
        [entity_dict(item, text) for item in sorted(b_only)],
    )
    events: list[dict[str, Any]] = []

    for pair in classified["pairs"]:
        a_entity = tuple(pair["a"])
        b_entity = tuple(pair["b"])
        category = pair["category"]
        if category == "same_boundary_type_conflict":
            rule_signal = "TYPE_POLICY"
        elif category == "overlap_boundary_conflict":
            rule_signal = "BOUNDARY_POLICY"
        else:
            rule_signal = "BOUNDARY_AND_TYPE_POLICY"
        events.append(
            {
                "category": category,
                "rule_signal": rule_signal,
                "a": entity_dict(a_entity, text),
                "b": entity_dict(b_entity, text),
                "context": context_for(text, [a_entity, b_entity]),
            }
        )

    for side, unmatched, other in (
        ("a", classified["a_unmatched"], b_entities),
        ("b", classified["b_unmatched"], a_entities),
    ):
        for raw_entity in unmatched:
            entity = tuple(raw_entity)
            repeated = repeated_mention_candidate(text, entity, other)
            category = (
                f"{side}_only_repeated_mention_candidate"
                if repeated
                else f"{side}_unmatched"
            )
            events.append(
                {
                    "category": category,
                    "rule_signal": "REPEATED_MENTION" if repeated else "SCOPE_POLICY",
                    "a": entity_dict(entity, text) if side == "a" else None,
                    "b": entity_dict(entity, text) if side == "b" else None,
                    "context": context_for(text, [entity]),
                }
            )

    return {
        "exact": [entity_dict(item, text) for item in sorted(exact)],
        "a_only": [entity_dict(item, text) for item in sorted(a_only)],
        "b_only": [entity_dict(item, text) for item in sorted(b_only)],
        "events": events,
    }


def event_csv_row(
    original_id: str,
    bucket: str,
    event: dict[str, Any],
) -> dict[str, Any]:
    a_entity = event["a"] or {}
    b_entity = event["b"] or {}
    return {
        "original_id": original_id,
        "selection_bucket": bucket,
        "category": event["category"],
        "rule_signal": event["rule_signal"],
        "a_start": a_entity.get("start", ""),
        "a_end": a_entity.get("end", ""),
        "a_type": a_entity.get("type", ""),
        "a_span": a_entity.get("span", ""),
        "b_start": b_entity.get("start", ""),
        "b_end": b_entity.get("end", ""),
        "b_type": b_entity.get("type", ""),
        "b_span": b_entity.get("span", ""),
        "context": event["context"],
    }


def analyze(
    config: AnalysisConfig,
    *,
    expected_hashes: ExpectedHashes = ExpectedHashes(),
    expected_rows: int = EXPECTED_ROWS,
) -> dict[str, Any]:
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output: {config.output_dir}")

    locked_inputs = (
        (
            config.annotator_a_completed,
            expected_hashes.annotator_a_completed,
            "A completed",
        ),
        (
            config.annotator_b_completed,
            expected_hashes.annotator_b_completed,
            "B completed",
        ),
        (config.coordinator_map, expected_hashes.coordinator_map, "coordinator map"),
        (
            config.validation_report,
            expected_hashes.validation_report,
            "validation report",
        ),
    )
    for path, expected_hash, label in locked_inputs:
        require_hash(path, expected_hash, label)

    report = json.loads(config.validation_report.read_text(encoding="utf-8"))
    if report.get("status") != "blocked" or report.get("formal_human_iaa") is not None:
        raise ValueError("expected blocked calibration report with null formal_human_iaa")
    if report.get("validation", {}).get("non_order_hard_error_count") != 0:
        raise ValueError("reconciliation requires ordering-only hard errors")

    a_rows = index_rows(read_csv(config.annotator_a_completed), "A completed")
    b_rows = index_rows(read_csv(config.annotator_b_completed), "B completed")
    map_rows = read_jsonl(config.coordinator_map)
    if not (len(a_rows) == len(b_rows) == len(map_rows) == expected_rows):
        raise ValueError("calibration row counts do not match the locked expected count")

    validation_issues: list[dict[str, str]] = []
    row_outputs: list[dict[str, Any]] = []
    event_outputs: list[dict[str, Any]] = []
    event_counts: Counter[str] = Counter()
    rule_signal_counts: Counter[str] = Counter()
    type_confusions: Counter[str] = Counter()
    bucket_disagreement_rows: Counter[str] = Counter()
    bucket_event_counts: Counter[str] = Counter()
    exact_rows = 0
    total_a = 0
    total_b = 0
    total_exact = 0
    seen_a: set[str] = set()
    seen_b: set[str] = set()

    for mapping in sorted(map_rows, key=lambda item: item["original_id"]):
        if set(mapping) != MAP_FIELDS:
            raise ValueError(f"coordinator map field mismatch: {sorted(mapping)}")
        original_id = mapping["original_id"]
        a_id = mapping["annotator_a_blind_id"]
        b_id = mapping["annotator_b_blind_id"]
        if a_id in seen_a or b_id in seen_b or a_id not in a_rows or b_id not in b_rows:
            raise ValueError(f"invalid coordinator mapping for {original_id}")
        seen_a.add(a_id)
        seen_b.add(b_id)
        a_row = a_rows[a_id]
        b_row = b_rows[b_id]
        text = a_row["text"]
        if text != b_row["text"] or text_sha256(text) != mapping["text_sha256"]:
            raise ValueError(f"text/hash mismatch for {original_id}")

        a_entities, _ = validate_entities(
            a_row,
            annotator="A",
            original_id=original_id,
            issues=validation_issues,
        )
        b_entities, _ = validate_entities(
            b_row,
            annotator="B",
            original_id=original_id,
            issues=validation_issues,
        )
        hard_codes = {
            item["code"]
            for item in validation_issues
            if item["original_id"] == original_id and item["severity"] == HARD_ERROR
        }
        if hard_codes - {"ENTITIES_NOT_SORTED"}:
            raise ValueError(f"non-order hard error for {original_id}: {sorted(hard_codes)}")

        classified = classify_row(text, a_entities, b_entities)
        bucket = mapping["selection_bucket"]
        if not classified["a_only"] and not classified["b_only"]:
            exact_rows += 1
        else:
            bucket_disagreement_rows[bucket] += 1
        total_a += len(a_entities)
        total_b += len(b_entities)
        total_exact += len(classified["exact"])

        row_issue_codes = sorted(
            {
                item["code"]
                for item in validation_issues
                if item["original_id"] == original_id
            }
        )
        row_outputs.append(
            {
                "original_id": original_id,
                "selection_bucket": bucket,
                "text": text,
                "annotator_a_blind_id": a_id,
                "annotator_b_blind_id": b_id,
                "annotator_a_entities": [
                    entity_dict(item, text) for item in sorted(a_entities)
                ],
                "annotator_b_entities": [
                    entity_dict(item, text) for item in sorted(b_entities)
                ],
                "annotator_a_notes": a_row["notes"],
                "annotator_b_notes": b_row["notes"],
                "annotator_a_uncertainty_code": a_row["uncertainty_code"],
                "annotator_b_uncertainty_code": b_row["uncertainty_code"],
                "exact_matches": classified["exact"],
                "annotator_a_only": classified["a_only"],
                "annotator_b_only": classified["b_only"],
                "validation_issue_codes": row_issue_codes,
                "event_categories": [item["category"] for item in classified["events"]],
            }
        )
        for event in classified["events"]:
            event_counts[event["category"]] += 1
            rule_signal_counts[event["rule_signal"]] += 1
            bucket_event_counts[bucket] += 1
            if event["category"] == "same_boundary_type_conflict":
                type_confusions[f"{event['a']['type']}->{event['b']['type']}"] += 1
            event_outputs.append(event_csv_row(original_id, bucket, event))

    issue_counts = Counter(item["code"] for item in validation_issues)
    severity_counts = Counter(item["severity"] for item in validation_issues)
    if severity_counts[HARD_ERROR] != report["validation"]["hard_error_count"]:
        raise ValueError("recomputed hard-error count differs from locked report")
    if severity_counts[BLOCKING_REVIEW] != report["validation"]["blocking_review_count"]:
        raise ValueError("recomputed blocking-review count differs from locked report")

    summary = {
        "phase": "P6-QA1R-GUIDELINE-RECONCILIATION",
        "status": "guideline_evidence_only",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "source_split": "domain_dev_calibration",
            "submitted_labels_modified": False,
            "gold_or_predictions_read": False,
            "adjudication_performed": False,
            "new_calibration_generated": False,
            "model_calls": False,
            "formal_human_iaa": None,
        },
        "source_validation": {
            "status": report["status"],
            "strict_f1": report["calibration_file_concordance"]["f1"],
            "order_insensitive_f1": report[
                "secondary_all_rows_order_insensitive_concordance"
            ]["f1"],
            "rows": expected_rows,
        },
        "order_insensitive_counts": {
            "annotator_a_entities": total_a,
            "annotator_b_entities": total_b,
            "exact_matches": total_exact,
            "exact_rows": exact_rows,
            "disagreement_rows": expected_rows - exact_rows,
        },
        "source_validation_issue_counts": report["validation"]["code_counts"],
        "recomputed_entity_issue_counts": dict(sorted(issue_counts.items())),
        "event_category_counts": dict(sorted(event_counts.items())),
        "rule_signal_counts": dict(sorted(rule_signal_counts.items())),
        "same_boundary_type_confusions": dict(sorted(type_confusions.items())),
        "disagreement_rows_by_bucket": dict(sorted(bucket_disagreement_rows.items())),
        "events_by_bucket": dict(sorted(bucket_event_counts.items())),
        "interpretation_guardrail": (
            "These outputs diagnose a completed calibration round for guideline repair. "
            "They are not gold adjudication, a rescored independent round, or formal IAA."
        ),
    }

    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = config.output_dir.parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        summary_path = staging / "summary.json"
        events_path = staging / "reconciliation_events.csv"
        rows_path = staging / "reconciliation_rows.jsonl"
        write_bytes_atomic(
            summary_path,
            (json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        write_bytes_atomic(
            events_path,
            csv_payload(
                event_outputs,
                (
                    "original_id",
                    "selection_bucket",
                    "category",
                    "rule_signal",
                    "a_start",
                    "a_end",
                    "a_type",
                    "a_span",
                    "b_start",
                    "b_end",
                    "b_type",
                    "b_span",
                    "context",
                ),
            ),
        )
        write_bytes_atomic(rows_path, jsonl_payload(row_outputs))
        final_paths = {
            "summary": config.output_dir / summary_path.name,
            "events": config.output_dir / events_path.name,
            "rows": config.output_dir / rows_path.name,
        }
        manifest = {
            "phase": summary["phase"],
            "status": summary["status"],
            "created_at": summary["created_at"],
            "inputs": {
                label: {"path": str(path), "sha256": sha256_file(path)}
                for path, _, label in locked_inputs
            },
            "safeguards": {
                "locked_input_hashes": True,
                "coordinator_only_output": True,
                "no_label_repair_or_adjudication": True,
                "no_gold_test_predictions_or_models": True,
                "no_new_calibration_generation": True,
                "existing_output_overwrite_refused": True,
            },
            "outputs": {
                "summary": file_metadata(summary_path, "coordinator_only")
                | {"path": str(final_paths["summary"])},
                "events": file_metadata(
                    events_path, "coordinator_only", len(event_outputs)
                )
                | {"path": str(final_paths["events"])},
                "rows": file_metadata(rows_path, "coordinator_only", len(row_outputs))
                | {"path": str(final_paths["rows"])},
            },
        }
        manifest_path = staging / "manifest.json"
        write_bytes_atomic(
            manifest_path,
            (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        for path in (summary_path, events_path, rows_path, manifest_path):
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
        coordinator_map=Path(args.coordinator_map),
        validation_report=Path(args.validation_report),
        output_dir=Path(args.output_dir),
    )
    summary = analyze(config)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "disagreement_rows": summary["order_insensitive_counts"][
                    "disagreement_rows"
                ],
                "events": sum(summary["event_category_counts"].values()),
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
