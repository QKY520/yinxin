#!/usr/bin/env python3
"""No-card audit for the windowed candidate-index semantic-repair protocol.

This script reads only non-test development rows and a local tokenizer.  It
materializes no model prompts, predictions, or runtime outputs; the report is
an immutable design/preflight artifact for a later, separately gated pilot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer

from equipment_ie.extraction import (
    format_candidate_index_window_block,
    generate_candidate_index_windows,
)


GATE = "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_CANDIDATE_INDEX_SEMANTIC_REPAIR_PREFLIGHT_READONLY_APPROVED"
PROTOCOL = "candidate_index_semantic_repair_preflight_v1"
PILOT_ROWS = 20
EXPECTED_DEV_ROWS = 50
MAX_CONTEXT_TOKENS = 8192
MAX_GENERATION_TOKENS = 2048
MAX_CANDIDATES_PER_WINDOW = 2048


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, Any]]:
    resolved_path = path.resolve(strict=True)
    if resolved_path.name != "domain_dev.jsonl":
        raise ValueError("candidate preflight accepts only an explicit domain_dev.jsonl path")
    if any("test" in part.lower() for part in resolved_path.parts):
        raise ValueError("candidate preflight refuses query paths that mention test")
    rows = [
        json.loads(line)
        for line in resolved_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"no rows found in {resolved_path}")
    if any("test" in str(row.get("id", "")).lower() for row in rows):
        raise ValueError("candidate preflight refuses rows whose IDs mention test")
    return rows


def tokenizer_offsets(tokenizer: Any, text: str) -> list[tuple[int, int]]:
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    offsets = [(int(start), int(end)) for start, end in encoded["offset_mapping"]]
    invalid = [pair for pair in offsets if not (0 <= pair[0] < pair[1] <= len(text))]
    if invalid:
        raise ValueError(f"tokenizer returned invalid offsets: {invalid[:5]}")
    return offsets


def audit_rows(rows: list[dict[str, Any]], tokenizer: Any) -> dict[str, Any]:
    row_reports: list[dict[str, Any]] = []
    total_entities = 0
    covered_entities = 0
    invalid_candidate_spans = 0
    for row in rows:
        text = str(row["text"])
        windows = generate_candidate_index_windows(
            text,
            token_offsets=tokenizer_offsets(tokenizer, text),
            max_candidates_per_window=MAX_CANDIDATES_PER_WINDOW,
        )
        row_invalid_candidate_spans = 0
        for window in windows:
            for item in window:
                start, end = int(item["start"]), int(item["end"])
                if not (0 <= start < end <= len(text)) or text[start:end] != item["span"]:
                    row_invalid_candidate_spans += 1
        invalid_candidate_spans += row_invalid_candidate_spans
        candidate_union = {
            (int(item["start"]), int(item["end"]))
            for window in windows
            for item in window
        }
        missing = []
        for entity in row.get("entities", []):
            total_entities += 1
            key = (int(entity["start"]), int(entity["end"]))
            if key in candidate_union:
                covered_entities += 1
            else:
                missing.append({"start": key[0], "end": key[1], "span": entity["span"]})
        candidate_block_tokens = []
        for window in windows:
            block = format_candidate_index_window_block(window)
            candidate_block_tokens.append(
                len(tokenizer(block, add_special_tokens=False)["input_ids"])
            )
        row_reports.append(
            {
                "id": row["id"],
                "text_chars": len(text),
                "window_count": len(windows),
                "candidate_counts": [len(window) for window in windows],
                "candidate_block_tokens": candidate_block_tokens,
                "invalid_candidate_spans": row_invalid_candidate_spans,
                "gold_entities": len(row.get("entities", [])),
                "covered_gold_entities": len(row.get("entities", [])) - len(missing),
                "missing_gold_entities": missing,
            }
        )
    return {
        "rows": len(rows),
        "gold_entities": total_entities,
        "covered_gold_entities": covered_entities,
        "coverage": covered_entities / total_entities if total_entities else 0.0,
        "invalid_candidate_spans": invalid_candidate_spans,
        "max_window_candidates": max(
            max(report["candidate_counts"]) for report in row_reports
        ),
        "p95_window_candidates": _percentile(
            [count for report in row_reports for count in report["candidate_counts"]], 0.95
        ),
        "max_candidate_block_tokens": max(
            max(report["candidate_block_tokens"]) for report in row_reports
        ),
        "p95_candidate_block_tokens": _percentile(
            [count for report in row_reports for count in report["candidate_block_tokens"]], 0.95
        ),
        "row_reports": row_reports,
    }


def _percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int((len(ordered) - 1) * fraction)))
    return int(ordered[index])


def run_preflight(*, query_path: Path, tokenizer_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output_dir}")
    resolved_query_path = query_path.resolve(strict=True)
    rows = load_rows(query_path)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True, use_fast=True)
    pilot_subset = audit_rows(rows[:PILOT_ROWS], tokenizer)
    all_dev = audit_rows(rows, tokenizer)
    max_context_tokens = MAX_CONTEXT_TOKENS
    max_generation_tokens = MAX_GENERATION_TOKENS
    maximum_candidate_block_tokens = max(
        pilot_subset["max_candidate_block_tokens"], all_dev["max_candidate_block_tokens"]
    )
    checks = {
        "dev_row_count": {
            "expected": EXPECTED_DEV_ROWS,
            "actual": len(rows),
            "passed": len(rows) == EXPECTED_DEV_ROWS,
        },
        "pilot_row_count": {
            "expected": PILOT_ROWS,
            "actual": len(rows[:PILOT_ROWS]),
            "passed": len(rows) >= PILOT_ROWS,
        },
        "pilot_candidate_coverage": {
            "covered": pilot_subset["covered_gold_entities"],
            "gold": pilot_subset["gold_entities"],
            "passed": pilot_subset["coverage"] == 1.0,
        },
        "all_dev_candidate_coverage": {
            "covered": all_dev["covered_gold_entities"],
            "gold": all_dev["gold_entities"],
            "passed": all_dev["coverage"] == 1.0,
        },
        "candidate_span_integrity": {
            "invalid": pilot_subset["invalid_candidate_spans"] + all_dev["invalid_candidate_spans"],
            "passed": pilot_subset["invalid_candidate_spans"] == 0
            and all_dev["invalid_candidate_spans"] == 0,
        },
        "candidate_count_cap": {
            "limit": MAX_CANDIDATES_PER_WINDOW,
            "observed": max(pilot_subset["max_window_candidates"], all_dev["max_window_candidates"]),
            "passed": max(pilot_subset["max_window_candidates"], all_dev["max_window_candidates"])
            <= MAX_CANDIDATES_PER_WINDOW,
        },
        "candidate_block_plus_generation_context": {
            "context_limit": MAX_CONTEXT_TOKENS,
            "candidate_block_tokens": maximum_candidate_block_tokens,
            "generation_tokens": MAX_GENERATION_TOKENS,
            "passed": maximum_candidate_block_tokens + MAX_GENERATION_TOKENS
            <= MAX_CONTEXT_TOKENS,
        },
    }
    preflight_checks_passed = all(check["passed"] for check in checks.values())
    pilot_blockers = [name for name, check in checks.items() if not check["passed"]]
    pilot_blockers.append("full_future_request_budget_unverified")
    report = {
        "gate": GATE,
        "protocol": PROTOCOL,
        "model_calls_allowed": False,
        "gpu_required": False,
        "query_path": str(resolved_query_path),
        "query_sha256": sha256_file(resolved_query_path),
        "tokenizer_path": str(tokenizer_path),
        "pilot_rows": PILOT_ROWS,
        "preflight_checks_passed": preflight_checks_passed,
        "pilot_ready": False,
        "checks": checks,
        "pilot_blockers": pilot_blockers,
        "candidate_block_budget": {
            "max_context_tokens": max_context_tokens,
            "max_generation_tokens": max_generation_tokens,
            "maximum_candidate_block_tokens": maximum_candidate_block_tokens,
            "maximum_candidate_block_plus_generation_tokens": (
                maximum_candidate_block_tokens + max_generation_tokens
            ),
            "necessarily_exceeds_context": (
                maximum_candidate_block_tokens + max_generation_tokens > max_context_tokens
            ),
            "scope": "candidate map only; excludes task, schema, query text, instructions, evidence, and demonstrations",
        },
        "full_future_request_budget": {
            "verified": False,
            "reason": "This preflight measures candidate-map tokenization only; a later model-pilot gate must measure the complete request and reserve the 2048-token generation budget.",
        },
        "pilot_subset": pilot_subset,
        "all_dev": all_dev,
        "decision": (
            "candidate_windows_require_a_new_model_pilot_gate"
            if preflight_checks_passed
            else "candidate_index_preflight_blocked"
        ),
        "fail_fast": [
            "refuse existing output directory",
            "accept only a non-test domain_dev.jsonl path and reject test-like query IDs",
            "reject empty or out-of-range tokenizer offsets",
            f"reject any candidate window over {MAX_CANDIDATES_PER_WINDOW} candidates",
            "record every missing gold span as unreachable by the generator",
            "record whether the candidate block plus the fixed generation budget necessarily exceeds the 8192-token context",
            "require a later complete-request budget audit before any model pilot",
        ],
    }
    output_dir.mkdir(parents=True)
    (output_dir / "preflight_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-path", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(run_preflight(**vars(args)), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
