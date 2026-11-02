#!/usr/bin/env python3
"""No-card preflight for complete candidate-lattice request budgeting.

The preflight is deliberately limited to non-test ``domain_dev.jsonl`` rows.
It builds candidate-index prompts for the four Qwen reviewer systems, but it
never calls a model, starts vLLM, performs dense retrieval, or writes a runtime
prediction.  Candidate spans are generated from a bounded character lattice;
the complete prompt plus an estimated response-schema budget is then greedily
partitioned so every future request fits the fixed context reserve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from transformers import AutoTokenizer

from equipment_ie.extraction import (
    build_ner_compact_candidate_index_response_format,
    build_ner_prompt,
    build_request_envelope,
    generate_candidate_index_lattice,
    prompt_hash,
    select_glossary_entries,
)
from equipment_ie.llm_labeling import request_hash
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record


GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_"
    "CANDIDATE_LATTICE_COVERAGE_BUDGET_REPAIR_PREFLIGHT_READONLY_APPROVED"
)
PROTOCOL = "candidate_lattice_coverage_budget_repair_preflight_v1"
PILOT_ROWS = 20
EXPECTED_DEV_ROWS = 50
MAX_CONTEXT_TOKENS = 8192
MAX_GENERATION_TOKENS = 2048
SAFETY_RESERVE_TOKENS = 256
MAX_INPUT_TOKENS = MAX_CONTEXT_TOKENS - MAX_GENERATION_TOKENS - SAFETY_RESERVE_TOKENS
ENTRY_COST_UPPER_BOUND = 32
MAX_ENTITIES = 12
LATTICE_WINDOW_CHARS = 64
LATTICE_OVERLAP_CHARS = 31
LATTICE_MAX_SPAN_CHARS = 31
LATTICE_MAX_TOKEN_WIDTH = 20
LATTICE_SUFFIX_CONTEXT_CHARS = 31
LATTICE_ASCII_RADIUS_CHARS = 6
LATTICE_MAX_CANDIDATES_PER_WINDOW = 2048
SYSTEMS = ("ec_fsie_full", "zero_shot", "bm25_only", "rag_only")
DOMAIN_ENTITY_TYPES = {
    "EQUIPMENT": "complete equipment, weapon, platform, system, or model name",
    "MODULE": "equipment component, subsystem, sensor, payload, or functional module",
    "TECH_SCHEME": "technology, guidance, operation, test, improvement, or capability scheme",
    "METRIC": "numeric performance indicator, parameter, range, speed, mass, time, or count",
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reject_test_path(path: Path, *, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if any("test" in part.lower() for part in resolved.parts):
        raise ValueError(f"{label} path mentions test and is forbidden: {resolved}")
    return resolved


def load_dev_rows(path: Path) -> list[dict[str, Any]]:
    resolved = _reject_test_path(path, label="query")
    if resolved.name != "domain_dev.jsonl":
        raise ValueError("query input must be an explicit non-test domain_dev.jsonl")
    rows = [dict(row) for row in iter_jsonl(resolved)]
    if len(rows) != EXPECTED_DEV_ROWS:
        raise ValueError(f"domain_dev row count must be {EXPECTED_DEV_ROWS}, got {len(rows)}")
    for row in rows:
        if "test" in str(row.get("id", "")).lower():
            raise ValueError(f"query row ID mentions test: {row.get('id')}")
        validate_record(row)
    return rows


def load_records(path: Path, *, label: str, validate_entities: bool = False) -> list[dict[str, Any]]:
    resolved = _reject_test_path(path, label=label)
    rows = [dict(row) for row in iter_jsonl(resolved, validate=validate_entities)]
    if not rows:
        raise ValueError(f"{label} file is empty: {resolved}")
    return rows


def deduplicate_lattice_windows(
    windows: Sequence[Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Return one stable candidate ID for each unique character span."""

    by_span: dict[tuple[int, int], dict[str, Any]] = {}
    for window in windows:
        for raw in window:
            start, end = int(raw["start"]), int(raw["end"])
            item = {
                "id": f"c{start:04d}_{end:04d}",
                "start": start,
                "end": end,
                "span": str(raw["span"]),
            }
            by_span.setdefault((start, end), item)
    return [by_span[key] for key in sorted(by_span)]


def audit_lattice_coverage(
    rows: Sequence[Mapping[str, Any]],
    tokenizer: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    total_gold = covered_gold = 0
    max_window_candidates = 0
    for row in rows:
        text = str(row["text"])
        encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        invalid_offsets = [
            (int(start), int(end))
            for start, end in encoded["offset_mapping"]
            if not (0 <= int(start) < int(end) <= len(text))
        ]
        if invalid_offsets:
            raise ValueError(f"tokenizer returned invalid offsets for {row['id']}: {invalid_offsets[:5]}")
        windows = generate_candidate_index_lattice(
            text,
            window_chars=LATTICE_WINDOW_CHARS,
            overlap_chars=LATTICE_OVERLAP_CHARS,
            max_span_chars=LATTICE_MAX_SPAN_CHARS,
            max_candidates_per_window=LATTICE_MAX_CANDIDATES_PER_WINDOW,
        )
        candidates = deduplicate_lattice_windows(windows)
        invalid = [
            item
            for item in candidates
            if not (0 <= int(item["start"]) < int(item["end"]) <= len(text))
            or text[int(item["start"]) : int(item["end"])] != item["span"]
        ]
        candidate_spans = {(int(item["start"]), int(item["end"])) for item in candidates}
        missing = []
        for entity in row["entities"]:
            total_gold += 1
            key = (int(entity["start"]), int(entity["end"]))
            if key in candidate_spans:
                covered_gold += 1
            else:
                missing.append(
                    {"start": key[0], "end": key[1], "span": str(entity["span"]), "type": str(entity["type"])}
                )
        counts = [len(window) for window in windows]
        max_window_candidates = max(max_window_candidates, max(counts, default=0))
        reports.append(
            {
                "id": str(row["id"]),
                "text_chars": len(text),
                "window_count": len(windows),
                "window_candidate_counts": counts,
                "unique_candidate_count": len(candidates),
                "invalid_candidate_spans": len(invalid),
                "gold_entities": len(row["entities"]),
                "covered_gold_entities": len(row["entities"]) - len(missing),
                "missing_gold_entities": missing,
                "candidates": candidates,
            }
        )
    summary = {
        "rows": len(rows),
        "gold_entities": total_gold,
        "covered_gold_entities": covered_gold,
        "coverage": covered_gold / total_gold if total_gold else 0.0,
        "invalid_candidate_spans": sum(int(report["invalid_candidate_spans"]) for report in reports),
        "max_window_candidates": max_window_candidates,
        "max_unique_candidates": max(
            (int(report["unique_candidate_count"]) for report in reports), default=0
        ),
    }
    return reports, summary


def _token_count(tokenizer: Any, text: str) -> int:
    encoded = tokenizer(text, add_special_tokens=False)
    return len(encoded["input_ids"])


def _chat_template_count(tokenizer: Any, prompt: str) -> int:
    """Count the actual Qwen user request when the tokenizer exposes a template."""

    try:
        encoded = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True,
            add_generation_prompt=True,
        )
        return len(encoded)
    except (AttributeError, TypeError, ValueError):
        # The raw prompt count plus a fixed conservative wrapper allowance is
        # still deterministic for tokenizers without a chat template.
        return _token_count(tokenizer, prompt) + 16


def _format_passage(row: Mapping[str, Any], *, max_chars: int = 300) -> str:
    text = str(row.get("text", ""))
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "..."
    source_id = str(row.get("id") or row.get("source_id") or "unknown")
    title = str(row.get("title") or row.get("source_id") or source_id)
    source_type = str(row.get("source_type") or "unknown")
    return f"{title} | {source_type} | {source_id}: {text}"


def _longest_passages(corpus_rows: Sequence[Mapping[str, Any]], count: int = 3) -> list[str]:
    # Longest passages provide a deterministic upper-bound evidence block. No
    # dense embedding or retrieval model is initialized in this preflight.
    selected = sorted(
        corpus_rows,
        key=lambda row: (-len(str(row.get("text", ""))), str(row.get("id", ""))),
    )[:count]
    return [_format_passage(row) for row in selected]


def _longest_examples(support_rows: Sequence[Mapping[str, Any]], count: int = 5) -> list[dict[str, Any]]:
    selected = sorted(
        (dict(row) for row in support_rows if row.get("entities")),
        key=lambda row: (-len(str(row.get("text", ""))), str(row.get("id", ""))),
    )[:count]
    if len(selected) != count:
        raise ValueError(f"support set has fewer than {count} rows with entities")
    return selected


def _system_components(
    system: str,
    *,
    query: Mapping[str, Any],
    support_rows: Sequence[Mapping[str, Any]],
    corpus_rows: Sequence[Mapping[str, Any]],
    glossary_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[str], str]:
    if system not in SYSTEMS:
        raise ValueError(f"unknown system: {system}")
    examples = _longest_examples(support_rows) if system == "ec_fsie_full" else []
    glossary = (
        select_glossary_entries(str(query["text"]), glossary_rows, max_entries=20)
        if system == "ec_fsie_full"
        else []
    )
    rag = _longest_passages(corpus_rows) if system in {"ec_fsie_full", "bm25_only", "rag_only"} else []
    rag_mode = "deterministic_longest_budget_bound" if rag else "disabled"
    return examples, glossary, rag, rag_mode


def build_budgeted_request_chunks(
    *,
    tokenizer: Any,
    query: Mapping[str, Any],
    system: str,
    candidates: Sequence[Mapping[str, Any]],
    examples: Sequence[Mapping[str, Any]],
    glossary: Sequence[str],
    rag: Sequence[str],
    row_index: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Greedily partition candidates using the complete request budget."""

    chunks: list[dict[str, Any]] = []
    template_probe = "candidate-budget-probe"
    chat_template_overhead = _chat_template_count(tokenizer, template_probe) - _token_count(tokenizer, template_probe)
    empty_prompt = build_ner_prompt(
        query_text=str(query["text"]),
        entity_types=DOMAIN_ENTITY_TYPES,
        examples=examples,
        include_relations=False,
        glossary_entries=glossary,
        rag_passages=rag,
        output_instruction="Return JSON only. Do not include explanations or markdown.",
        output_mode="candidate_index",
        reference_instruction=(
            "Reference passages are evidence only. Copy entities only from the final query text, "
            "never from a reference passage."
        ),
        candidate_spans=[],
        example_output_mode="occurrence",
        compact_candidate_index=True,
    )
    static_input_tokens = _chat_template_count(tokenizer, empty_prompt) + _token_count(
        tokenizer,
        json.dumps(
            build_ner_compact_candidate_index_response_format(
                sorted(DOMAIN_ENTITY_TYPES), max_entities=MAX_ENTITIES
            ),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    # A small conservative allowance covers separator/BPE merges when entries
    # are concatenated. Every emitted chunk is re-tokenized exactly below.
    static_input_tokens += 32
    def entry_cost(candidate: Mapping[str, Any]) -> int:
        # Candidate IDs and offsets are ASCII and bounded. A fixed upper bound
        # avoids thousands of per-entry tokenizer calls; final chunks are
        # always re-tokenized with the complete prompt below.
        _ = candidate
        return ENTRY_COST_UPPER_BOUND

    def measure(candidate_chunk: Sequence[Mapping[str, Any]], *, exact: bool = False) -> dict[str, Any]:
        prompt = build_ner_prompt(
            query_text=str(query["text"]),
            entity_types=DOMAIN_ENTITY_TYPES,
            examples=examples,
            include_relations=False,
            glossary_entries=glossary,
            rag_passages=rag,
            output_instruction="Return JSON only. Do not include explanations or markdown.",
            output_mode="candidate_index",
            reference_instruction=(
                "Reference passages are evidence only. Copy entities only from the final query text, "
                "never from a reference passage."
            ),
            candidate_spans=candidate_chunk,
            example_output_mode="occurrence",
            compact_candidate_index=True,
        )
        response_format = build_ner_compact_candidate_index_response_format(
            sorted(DOMAIN_ENTITY_TYPES), max_entities=MAX_ENTITIES
        )
        schema_text = json.dumps(response_format, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        raw_prompt_tokens = _token_count(tokenizer, prompt)
        chat_template_tokens = _chat_template_count(tokenizer, prompt) if exact else raw_prompt_tokens + chat_template_overhead
        schema_tokens = _token_count(tokenizer, schema_text)
        input_tokens = chat_template_tokens + schema_tokens
        return {
            "prompt": prompt,
            "response_format": response_format,
            "raw_prompt_tokens": raw_prompt_tokens,
            "prompt_tokens": chat_template_tokens,
            "chat_template_tokens": chat_template_tokens,
            "response_schema_tokens": schema_tokens,
            "request_input_tokens": input_tokens,
            "reserved_total_tokens": input_tokens + MAX_GENERATION_TOKENS + SAFETY_RESERVE_TOKENS,
        }

    start = 0
    while start < len(candidates):
        used = static_input_tokens
        end = start
        while end < len(candidates) and used + entry_cost(candidates[end]) <= MAX_INPUT_TOKENS:
            used += entry_cost(candidates[end])
            end += 1
        if end == start:
            measured = measure(candidates[start : start + 1], exact=True)
            raise ValueError(
                f"single candidate cannot fit complete request for {system}/{query['id']}: "
                f"{measured['request_input_tokens']} > {MAX_INPUT_TOKENS}"
            )
        candidate_chunk = candidates[start:end]
        exact = measure(candidate_chunk, exact=True)
        while exact["request_input_tokens"] > MAX_INPUT_TOKENS and len(candidate_chunk) > 1:
            end = start + max(1, (end - start) // 2)
            candidate_chunk = candidates[start:end]
            exact = measure(candidate_chunk, exact=True)
        if exact["request_input_tokens"] > MAX_INPUT_TOKENS:
            raise ValueError(
                f"single candidate cannot fit complete request for {system}/{query['id']}: "
                f"{exact['request_input_tokens']} > {MAX_INPUT_TOKENS}"
            )
        chunks.append({"candidates": [dict(item) for item in candidate_chunk], **exact})
        start = end

    config_hash = canonical_sha256({"gate": GATE, "system": system, "row_index": row_index})
    rows: list[dict[str, Any]] = []
    for chunk_index, chunk in enumerate(chunks):
        envelope = build_request_envelope(
            prompt=chunk["prompt"],
            model="/root/autodl-tmp/models/qwen2.5-7b",
            generation={
                "temperature": 0.0,
                "top_p": 1.0,
                "max_tokens": MAX_GENERATION_TOKENS,
                "seed": 42,
                "response_format": chunk["response_format"],
            },
            run_id=f"candidate_lattice_{system}_{query['id']}_chunk{chunk_index}",
            config_hash=config_hash,
        )
        rows.append(
            {
                "system": system,
                "query_id": str(query["id"]),
                "row_index": row_index,
                "chunk_index": chunk_index,
                "chunk_count": len(chunks),
                "candidate_count": len(chunk["candidates"]),
                "candidate_ids_sha256": canonical_sha256([item["id"] for item in chunk["candidates"]]),
                "prompt_hash": prompt_hash(chunk["prompt"]),
                "request_hash": request_hash(envelope),
                "prompt_tokens": chunk["prompt_tokens"],
                "response_schema_tokens": chunk["response_schema_tokens"],
                "request_input_tokens": chunk["request_input_tokens"],
                "raw_prompt_tokens": chunk["raw_prompt_tokens"],
                "chat_template_overhead_probe": chat_template_overhead,
                "max_generation_tokens": MAX_GENERATION_TOKENS,
                "safety_reserve_tokens": SAFETY_RESERVE_TOKENS,
                "reserved_total_tokens": chunk["reserved_total_tokens"],
                "within_context": chunk["reserved_total_tokens"] <= MAX_CONTEXT_TOKENS,
            }
        )
    return rows, {
        "chunk_count": len(rows),
        "max_request_input_tokens": max((row["request_input_tokens"] for row in rows), default=0),
        "max_reserved_total_tokens": max((row["reserved_total_tokens"] for row in rows), default=0),
        "candidate_count_total": len(candidates),
    }


def run_preflight(
    *,
    query_path: Path,
    support_path: Path,
    corpus_path: Path,
    glossary_path: Path,
    tokenizer_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output_dir}")
    rows = load_dev_rows(query_path)
    support_rows = load_records(support_path, label="support", validate_entities=True)
    corpus_rows = load_records(corpus_path, label="corpus")
    glossary_rows = load_records(glossary_path, label="glossary")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path, local_files_only=True, use_fast=True)
    pilot_rows = rows[:PILOT_ROWS]
    pilot_reports, pilot_summary = audit_lattice_coverage(pilot_rows, tokenizer)
    all_reports, all_summary = audit_lattice_coverage(rows, tokenizer)

    request_rows: list[dict[str, Any]] = []
    request_summary: dict[str, Any] = {}
    for system in SYSTEMS:
        system_rows: list[dict[str, Any]] = []
        system_details: list[dict[str, Any]] = []
        for row_index, query in enumerate(rows):
            lattice_report = all_reports[row_index]
            examples, glossary, rag, rag_mode = _system_components(
                system,
                query=query,
                support_rows=support_rows,
                corpus_rows=corpus_rows,
                glossary_rows=glossary_rows,
            )
            built_rows, details = build_budgeted_request_chunks(
                tokenizer=tokenizer,
                query=query,
                system=system,
                candidates=lattice_report["candidates"],
                examples=examples,
                glossary=glossary,
                rag=rag,
                row_index=row_index,
            )
            for item in built_rows:
                item["evidence_block_mode"] = rag_mode
                item["example_count"] = len(examples)
                item["glossary_count"] = len(glossary)
                item["rag_passage_count"] = len(rag)
            system_rows.extend(built_rows)
            system_details.append(
                {
                    "query_id": str(query["id"]),
                    "lattice_candidate_count": len(lattice_report["candidates"]),
                    "gold_entities": lattice_report["gold_entities"],
                    "covered_gold_entities": lattice_report["covered_gold_entities"],
                    **details,
                }
            )
        request_rows.extend(system_rows)
        request_summary[system] = {
            "rows": len(system_rows),
            "query_count": len(system_details),
            "max_request_input_tokens": max((row["request_input_tokens"] for row in system_rows), default=0),
            "max_reserved_total_tokens": max((row["reserved_total_tokens"] for row in system_rows), default=0),
            "all_within_context": all(bool(row["within_context"]) for row in system_rows),
            "query_details": system_details,
        }

    coverage_passed = (
        pilot_summary["coverage"] == 1.0
        and all_summary["coverage"] == 1.0
        and pilot_summary["invalid_candidate_spans"] == 0
        and all_summary["invalid_candidate_spans"] == 0
    )
    budget_passed = all(bool(summary["all_within_context"]) for summary in request_summary.values())
    report = {
        "gate": GATE,
        "protocol": PROTOCOL,
        "model_calls_allowed": False,
        "gpu_required": False,
        "query_path": str(query_path.resolve()),
        "query_sha256": sha256_file(query_path),
        "support_path": str(support_path.resolve()),
        "corpus_path": str(corpus_path.resolve()),
        "glossary_path": str(glossary_path.resolve()),
        "tokenizer_path": str(tokenizer_path.resolve()),
        "pilot_rows": PILOT_ROWS,
        "expected_dev_rows": EXPECTED_DEV_ROWS,
        "systems": list(SYSTEMS),
        "lattice": {
            "window_chars": LATTICE_WINDOW_CHARS,
            "overlap_chars": LATTICE_OVERLAP_CHARS,
            "max_span_chars": LATTICE_MAX_SPAN_CHARS,
            "max_token_width": LATTICE_MAX_TOKEN_WIDTH,
            "suffix_context_chars": LATTICE_SUFFIX_CONTEXT_CHARS,
            "ascii_radius_chars": LATTICE_ASCII_RADIUS_CHARS,
            "max_candidates_per_window": LATTICE_MAX_CANDIDATES_PER_WINDOW,
        },
        "budget": {
            "max_context_tokens": MAX_CONTEXT_TOKENS,
            "max_generation_tokens": MAX_GENERATION_TOKENS,
            "safety_reserve_tokens": SAFETY_RESERVE_TOKENS,
            "max_input_tokens": MAX_INPUT_TOKENS,
            "entry_cost_upper_bound": ENTRY_COST_UPPER_BOUND,
            "counts_prompt_plus_response_schema": True,
        },
        "pilot_coverage": pilot_summary,
        "all_dev_coverage": all_summary,
        "request_summary": request_summary,
        "checks": {
            "pilot_coverage_complete": coverage_passed and pilot_summary["coverage"] == 1.0,
            "all_dev_coverage_complete": coverage_passed and all_summary["coverage"] == 1.0,
            "candidate_span_integrity": coverage_passed,
            "complete_request_budget": budget_passed,
            "no_model_or_gpu": True,
            "frozen_test_not_read": True,
        },
        "preflight_checks_passed": coverage_passed and budget_passed,
        "pilot_ready": False,
        "decision": "candidate_lattice_budget_preflight_passed" if coverage_passed and budget_passed else "candidate_lattice_budget_preflight_blocked",
        "fail_fast": [
            "refuse an existing output directory",
            "accept only explicit non-test domain_dev.jsonl queries",
            "reject test-like query paths and IDs",
            "reject invalid candidate slices",
            "require complete candidate coverage on the 20-row pilot prefix and all 50 dev rows",
            f"require prompt plus response-schema input <= {MAX_INPUT_TOKENS} tokens",
            "reserve 2048 generation tokens plus 256 safety tokens within the 8192 context",
            "do not initialize a model, vLLM, dense retrieval model, or GPU",
        ],
    }
    output_dir.mkdir(parents=True)
    (output_dir / "preflight_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "request_audit.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in request_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-path", type=Path, required=True)
    parser.add_argument("--support-path", type=Path, required=True)
    parser.add_argument("--corpus-path", type=Path, required=True)
    parser.add_argument("--glossary-path", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(json.dumps(run_preflight(**vars(args)), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
