#!/usr/bin/env python3
"""No-card preflight for implicit candidate-lattice runtime parsing.

The script reads only the non-test ``domain_dev.jsonl`` and exercises the
candidate-index parser with synthetic responses.  It never loads a model,
starts vLLM, initializes retrieval, or writes predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from equipment_ie.extraction import (
    ExtractionParseError,
    generate_candidate_index_lattice,
    materialize_candidate_index_window,
    merge_candidate_index_records,
    parse_extraction_output,
)
from equipment_ie.schema import iter_jsonl, validate_record


GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_"
    "CANDIDATE_LATTICE_RUNTIME_PARSER_INTEGRATION_PREFLIGHT_READONLY_APPROVED"
)
PROTOCOL = "candidate_lattice_runtime_parser_integration_preflight_v1"
EXPECTED_DEV_ROWS = 50
PILOT_ROWS = 20
WINDOW_CHARS = 64
OVERLAP_CHARS = 31
MAX_SPAN_CHARS = 31
MAX_CANDIDATES_PER_WINDOW = 2048
ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_dev_rows(path: Path) -> list[dict[str, Any]]:
    resolved = path.resolve(strict=True)
    if resolved.name != "domain_dev.jsonl":
        raise ValueError("query input must be an explicit non-test domain_dev.jsonl")
    if any("test" in part.lower() for part in resolved.parts):
        raise ValueError(f"query path mentions test and is forbidden: {resolved}")
    rows = [dict(row) for row in iter_jsonl(resolved)]
    if len(rows) != EXPECTED_DEV_ROWS:
        raise ValueError(f"domain_dev row count must be {EXPECTED_DEV_ROWS}, got {len(rows)}")
    for row in rows:
        if "test" in str(row.get("id", "")).lower():
            raise ValueError(f"query row ID mentions test: {row.get('id')}")
        validate_record(row)
    return rows


def _window_ranges(text: str) -> list[dict[str, int]]:
    windows = generate_candidate_index_lattice(
        text,
        window_chars=WINDOW_CHARS,
        overlap_chars=OVERLAP_CHARS,
        max_span_chars=MAX_SPAN_CHARS,
        max_candidates_per_window=MAX_CANDIDATES_PER_WINDOW,
    )
    return [
        {
            "start": int(window[0]["window_start"]),
            "end": int(window[0]["window_end"]),
        }
        for window in windows
        if window
    ]


def audit_coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = covered = invalid = 0
    max_window_candidates = 0
    max_unique_candidates = 0
    missing: list[dict[str, Any]] = []
    for row in rows:
        text = str(row["text"])
        windows = generate_candidate_index_lattice(
            text,
            window_chars=WINDOW_CHARS,
            overlap_chars=OVERLAP_CHARS,
            max_span_chars=MAX_SPAN_CHARS,
            max_candidates_per_window=MAX_CANDIDATES_PER_WINDOW,
        )
        coords: set[tuple[int, int]] = set()
        for window in windows:
            max_window_candidates = max(max_window_candidates, len(window))
            for item in window:
                start, end = int(item["start"]), int(item["end"])
                coords.add((start, end))
                if not (0 <= start < end <= len(text)) or text[start:end] != item["span"]:
                    invalid += 1
        max_unique_candidates = max(max_unique_candidates, len(coords))
        for entity in row["entities"]:
            total += 1
            key = (int(entity["start"]), int(entity["end"]))
            if key in coords:
                covered += 1
            else:
                missing.append({"id": row["id"], "start": key[0], "end": key[1]})
    return {
        "rows": len(rows),
        "gold_entities": total,
        "covered_gold_entities": covered,
        "coverage": covered / total if total else 0.0,
        "invalid_candidate_spans": invalid,
        "max_window_candidates": max_window_candidates,
        "max_unique_candidates": max_unique_candidates,
        "missing_gold_entities": missing,
    }


def _parse_window(
    *,
    row: Mapping[str, Any],
    window: Mapping[str, int],
    entities: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    raw = json.dumps({"entities": list(entities)}, ensure_ascii=False)
    return parse_extraction_output(
        raw,
        record_id=str(row["id"]),
        text=str(row["text"]),
        entity_types=ENTITY_TYPES,
        output_mode="candidate_index",
        candidate_index_lattice={
            "start": int(window["start"]),
            "end": int(window["end"]),
            "max_span_chars": MAX_SPAN_CHARS,
        },
    )


def runtime_checks(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    mapping_checked = 0
    mapping_invalid = 0
    duplicate_checked = False
    duplicate_deduplicated = False
    duplicate_detail: dict[str, Any] = {}
    overlap_rejected = False
    unknown_rejected = False
    omitted_relations_normalized = False

    for row in rows:
        text = str(row["text"])
        ranges = _window_ranges(text)
        for window in ranges:
            materialized = materialize_candidate_index_window(
                text,
                window_start=window["start"],
                window_end=window["end"],
                max_span_chars=MAX_SPAN_CHARS,
            )
            mapping_checked += len(materialized)
            mapping_invalid += sum(
                1
                for item in materialized
                if text[int(item["start"]) : int(item["end"])] != item["span"]
                or item["id"] != f"c{int(item['start']):04d}_{int(item['end']):04d}"
            )

        if not duplicate_checked:
            for left_index, left in enumerate(ranges):
                for right in ranges[left_index + 1 :]:
                    overlap_start = max(left["start"], right["start"])
                    overlap_end = min(left["end"], right["end"])
                    if overlap_end - overlap_start >= 2:
                        start, end = overlap_start, overlap_start + 1
                        candidate_id = f"c{start:04d}_{end:04d}"
                        left_record = _parse_window(
                            row=row,
                            window=left,
                            entities=[{"candidate_id": candidate_id, "type": "EQUIPMENT"}],
                        )
                        right_record = _parse_window(
                            row=row,
                            window=right,
                            entities=[{"candidate_id": candidate_id, "type": "EQUIPMENT"}],
                        )
                        merged = merge_candidate_index_records(
                            [left_record, right_record],
                            record_id=str(row["id"]),
                            text=text,
                            entity_types=ENTITY_TYPES,
                        )
                        duplicate_checked = True
                        duplicate_deduplicated = len(merged["entities"]) == 1
                        duplicate_detail = {
                            "query_id": str(row["id"]),
                            "candidate_id": candidate_id,
                            "window_count": 2,
                            "merged_entity_count": len(merged["entities"]),
                        }
                        break
                if duplicate_checked:
                    break
        if duplicate_checked and overlap_rejected and unknown_rejected and omitted_relations_normalized:
            break

    if not rows:
        raise ValueError("domain_dev rows must not be empty")
    probe_row = rows[0]
    probe_text = str(probe_row["text"])
    probe_window = _window_ranges(probe_text)[0]
    try:
        _parse_window(
            row=probe_row,
            window=probe_window,
            entities=[{"candidate_id": "c9999_9999", "type": "EQUIPMENT"}],
        )
    except ExtractionParseError:
        unknown_rejected = True

    if len(probe_text) < 3:
        raise ValueError("probe domain_dev text is too short for overlap probe")
    valid_a = "c0000_0002"
    valid_b = "c0001_0003"
    try:
        _parse_window(
            row=probe_row,
            window=probe_window,
            entities=[
                {"candidate_id": valid_a, "type": "EQUIPMENT"},
                {"candidate_id": valid_b, "type": "MODULE"},
            ],
        )
    except ExtractionParseError:
        overlap_rejected = True

    parsed_without_relations = _parse_window(
        row=probe_row,
        window=probe_window,
        entities=[],
    )
    omitted_relations_normalized = parsed_without_relations["relations"] == []

    return {
        "mapping_checked_candidates": mapping_checked,
        "mapping_invalid_candidates": mapping_invalid,
        "cross_window_duplicate_checked": duplicate_checked,
        "cross_window_duplicate_deduplicated": duplicate_deduplicated,
        "cross_window_duplicate_detail": duplicate_detail,
        "overlapping_entities_rejected": overlap_rejected,
        "unknown_candidate_rejected": unknown_rejected,
        "omitted_relations_normalized": omitted_relations_normalized,
    }


def run_preflight(*, query_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output_dir}")
    rows = load_dev_rows(query_path)
    pilot_coverage = audit_coverage(rows[:PILOT_ROWS])
    all_coverage = audit_coverage(rows)
    runtime = runtime_checks(rows)
    checks = {
        "pilot_coverage_complete": pilot_coverage["coverage"] == 1.0,
        "all_dev_coverage_complete": all_coverage["coverage"] == 1.0,
        "candidate_span_integrity": all_coverage["invalid_candidate_spans"] == 0,
        "runtime_mapping_exact": runtime["mapping_invalid_candidates"] == 0,
        "cross_window_duplicate_deduplicated": runtime["cross_window_duplicate_deduplicated"],
        "unknown_candidate_rejected": runtime["unknown_candidate_rejected"],
        "overlapping_entities_rejected": runtime["overlapping_entities_rejected"],
        "omitted_relations_normalized": runtime["omitted_relations_normalized"],
        "no_model_or_gpu": True,
        "frozen_test_not_read": True,
    }
    report = {
        "gate": GATE,
        "protocol": PROTOCOL,
        "model_calls_allowed": False,
        "gpu_required": False,
        "query_path": str(query_path.resolve()),
        "query_sha256": sha256_file(query_path),
        "pilot_rows": PILOT_ROWS,
        "expected_dev_rows": EXPECTED_DEV_ROWS,
        "lattice": {
            "window_chars": WINDOW_CHARS,
            "overlap_chars": OVERLAP_CHARS,
            "max_span_chars": MAX_SPAN_CHARS,
            "max_candidates_per_window": MAX_CANDIDATES_PER_WINDOW,
        },
        "pilot_coverage": pilot_coverage,
        "all_dev_coverage": all_coverage,
        "runtime_checks": runtime,
        "checks": checks,
        "preflight_checks_passed": all(checks.values()),
        "pilot_ready": False,
        "decision": (
            "candidate_lattice_runtime_parser_preflight_passed"
            if all(checks.values())
            else "candidate_lattice_runtime_parser_preflight_blocked"
        ),
        "fail_fast": [
            "refuse an existing output directory",
            "accept only explicit non-test domain_dev.jsonl queries",
            "reject test-like query paths and IDs",
            "require complete pilot and all-dev candidate coverage",
            "require exact implicit-coordinate mapping to final-query slices",
            "reject unknown candidate IDs and overlapping entities",
            "deduplicate exact entities repeated across overlapping windows",
            "normalize the NER-only omitted-relations envelope to relations=[]",
            "do not initialize a model, vLLM, dense retrieval model, or GPU",
        ],
    }
    output_dir.mkdir(parents=True)
    (output_dir / "preflight_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(run_preflight(**vars(args)), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
