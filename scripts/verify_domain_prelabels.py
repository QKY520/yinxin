#!/usr/bin/env python3
"""Independently verify P2 distant-supervision outputs and untouched review fields."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.domain_data import (  # noqa: E402
    iter_objects_jsonl,
    validate_distant_supervision_review_row,
)
from equipment_ie.schema import iter_jsonl, sha256_file  # noqa: E402


HUMAN_COLUMNS = (
    "annotator_a_entities_json",
    "annotator_a_relations_json",
    "annotator_a_notes",
    "annotator_b_entities_json",
    "annotator_b_relations_json",
    "annotator_b_notes",
    "adjudicated_entities_json",
    "adjudicated_relations_json",
    "adjudication_notes",
)


def verify(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    report_path = Path(config["outputs"]["report"])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["config_sha256"] != sha256_file(config_path):
        raise AssertionError("report config hash mismatch")
    if report["guards"] != {
        "dataset_split_or_frozen": False,
        "gpu_device_present": False,
        "human_annotation_started": False,
        "llm_disagreement_computed": False,
        "llm_used": False,
        "paid_gpu_used": False,
    }:
        raise AssertionError("report guards do not prove the approved scope")

    proposal_path = Path(config["outputs"]["proposals_jsonl"])
    review_jsonl_path = Path(config["outputs"]["review_jsonl"])
    review_csv_path = Path(config["outputs"]["review_csv"])
    path_by_output = {
        "proposals_jsonl": proposal_path,
        "review_jsonl": review_jsonl_path,
        "review_csv": review_csv_path,
    }
    for name, path in path_by_output.items():
        artifact = report["outputs"][name]
        if artifact["path"] != str(path):
            raise AssertionError(f"{name} path mismatch")
        if artifact["bytes"] != path.stat().st_size:
            raise AssertionError(f"{name} byte count mismatch")
        if artifact["sha256"] != sha256_file(path):
            raise AssertionError(f"{name} hash mismatch")

    proposals = list(iter_jsonl(proposal_path))
    reviews = list(iter_objects_jsonl(review_jsonl_path))
    with review_csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    expected_records = int(config["inputs"]["candidates"]["expected_records"])
    if not len(proposals) == len(reviews) == len(csv_rows) == expected_records:
        raise AssertionError("prelabel output record counts differ")

    proposal_ids = [row["id"] for row in proposals]
    review_ids = [row["review_id"] for row in reviews]
    csv_ids = [row["review_id"] for row in csv_rows]
    if proposal_ids != review_ids or proposal_ids != csv_ids:
        raise AssertionError("prelabel output order or ids differ")
    if len(set(proposal_ids)) != expected_records:
        raise AssertionError("duplicate prelabel output id")

    matched_records = 0
    proposed_entities = 0
    proposed_relations = 0
    spans: set[str] = set()
    source_records: Counter[str] = Counter()
    source_matched: Counter[str] = Counter()
    for proposal, review, csv_row in zip(proposals, reviews, csv_rows, strict=True):
        validate_distant_supervision_review_row(review)
        suggestion = review["machine_suggestion"]
        if proposal["text"] != review["candidate"]["text"]:
            raise AssertionError("proposal and review text differ")
        if proposal["entities"] != suggestion["entities"]:
            raise AssertionError("proposal and review entities differ")
        if proposal["relations"] != suggestion["relations"]:
            raise AssertionError("proposal and review relations differ")
        if csv_row["human_review_status"] != "NOT_STARTED":
            raise AssertionError("CSV human review status is not untouched")
        if csv_row["disagreement_status"] != "NOT_COMPUTED_LLM_NOT_RUN":
            raise AssertionError("CSV LLM disagreement is not untouched")
        if any(csv_row[column] for column in HUMAN_COLUMNS):
            raise AssertionError("CSV contains a non-empty human annotation cell")
        entities = proposal["entities"]
        relations = proposal["relations"]
        source_type = review["candidate"]["source_type"]
        source_records[source_type] += 1
        if entities:
            matched_records += 1
            source_matched[source_type] += 1
        proposed_entities += len(entities)
        proposed_relations += len(relations)
        spans.update(entity["span"] for entity in entities)

    statistics = {
        "candidate_records": expected_records,
        "matched_records": matched_records,
        "unmatched_records": expected_records - matched_records,
        "match_coverage": matched_records / expected_records,
        "proposed_entities": proposed_entities,
        "proposed_relations": proposed_relations,
        "unique_matched_spans": len(spans),
        "source_records": dict(sorted(source_records.items())),
        "source_matched_records": dict(sorted(source_matched.items())),
    }
    if statistics != report["statistics"]:
        raise AssertionError("independent statistics differ from report")
    return {
        "status": "ok",
        "statistics": statistics,
        "artifact_hashes": {
            name: report["outputs"][name]["sha256"] for name in path_by_output
        },
        "human_annotation_started": False,
        "llm_used": False,
        "paid_gpu_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "p2_distant_supervision.yaml",
    )
    args = parser.parse_args()
    print(json.dumps(verify(args.config.resolve()), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
