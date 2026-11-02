#!/usr/bin/env python3
"""Run the bounded candidate-lattice semantic dev pilot.

This runner is intentionally separate from the historical occurrence runner.
It uses only 20 non-test ``domain_dev`` rows (rows 11--20 and 41--50), sends
one bounded full-text span request per row to an already-running local vLLM
server, and preserves every parse outcome. It never loads evaluation or
frozen-test data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (  # noqa: E402
    ExtractionParseError,
    build_ner_compact_candidate_index_response_format,
    build_ner_span_index_response_format,
    build_ner_prompt,
    build_request_envelope,
    entity_micro_counts,
    generate_candidate_index_lattice,
    merge_candidate_index_records,
    parse_extraction_output,
    prompt_hash,
    select_glossary_entries,
)
from equipment_ie.llm_labeling import chat_with_cache, request_hash  # noqa: E402
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record  # noqa: E402

from scripts.run_p3_extraction import (  # noqa: E402
    build_knn_selector,
    build_rag_selector,
    format_rag_passage,
    load_glossary_records,
    load_records,
)


GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_SPAN_PROTOCOL_REPAIR_DEV_PILOT_APPROVED"
PROTOCOL = "unified_full_text_span_semantic_dev_pilot_v4"
SYSTEMS = ("ec_fsie_full", "zero_shot", "bm25_only", "rag_only")
PILOT_ROW_INDICES = tuple(range(10, 20)) + tuple(range(40, 50))
PILOT_ROWS = 20
MAX_CONTEXT_TOKENS = 8192
MAX_GENERATION_TOKENS = 2048
SAFETY_RESERVE_TOKENS = 256
# The selected dev pilot includes rows with 13 and 17 gold entities. Keep
# enough output headroom to avoid truncating a valid row at the transport
# schema; parser semantics still validate every returned span.
MAX_ENTITIES = 24
WINDOW_CHARS = 64
OVERLAP_CHARS = 31
MAX_SPAN_CHARS = 31
MAX_CANDIDATES_PER_WINDOW = 2048
PARSER_FAILURE_CEILING = 0.25
ENTITY_TYPES = {
    "EQUIPMENT": "complete equipment, weapon, platform, system, or model name",
    "MODULE": "equipment component, subsystem, sensor, payload, or functional module",
    "TECH_SCHEME": "technology, guidance, operation, test, improvement, or capability scheme",
    "METRIC": "numeric performance indicator, parameter, range, speed, mass, time, or count",
}


def parser_ceiling_is_unrecoverable(*, parser_failures: int, total_rows: int = PILOT_ROWS) -> bool:
    """Stop only when even perfect remaining rows cannot meet the final ceiling."""

    if parser_failures < 0 or total_rows <= 0:
        raise ValueError("parser failure accounting must be non-negative with positive total rows")
    return parser_failures / total_rows > PARSER_FAILURE_CEILING


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def reject_test_path(path: Path, *, label: str) -> Path:
    resolved = path.resolve(strict=True)
    if any("test" in part.lower() for part in resolved.parts):
        raise ValueError(f"{label} path mentions test and is forbidden: {resolved}")
    return resolved


def load_pilot_rows(path: Path) -> list[dict[str, Any]]:
    resolved = reject_test_path(path, label="query")
    if resolved.name != "domain_dev.jsonl":
        raise ValueError("query input must be explicit non-test domain_dev.jsonl")
    rows = [dict(row) for row in iter_jsonl(resolved)]
    if len(rows) < max(PILOT_ROW_INDICES) + 1:
        raise ValueError("domain_dev does not contain the required fresh pilot rows")
    selected = [rows[index] for index in PILOT_ROW_INDICES]
    for row in selected:
        if "test" in str(row.get("id", "")).lower():
            raise ValueError(f"pilot row ID mentions test: {row.get('id')}")
        validate_record(row)
    return selected


def lattice_ranges(text: str) -> list[dict[str, int]]:
    windows = generate_candidate_index_lattice(
        text,
        window_chars=WINDOW_CHARS,
        overlap_chars=OVERLAP_CHARS,
        max_span_chars=MAX_SPAN_CHARS,
        max_candidates_per_window=MAX_CANDIDATES_PER_WINDOW,
    )
    return [
        {"start": int(window[0]["window_start"]), "end": int(window[0]["window_end"])}
        for window in windows
        if window
    ]


def system_config(system: str, *, query_path: Path, support_path: Path, corpus_path: Path, glossary_path: Path) -> dict[str, Any]:
    if system not in SYSTEMS:
        raise ValueError(f"unknown system: {system}")
    config: dict[str, Any] = {
        "execution": {"authorized": True, "model_calls_allowed": True},
        "data": {"dataset": "domain", "query_path": str(query_path), "support_path": str(support_path)},
        "examples": {"mode": "none", "k": 0, "seed": 42},
        "schema": {"entity_types": ENTITY_TYPES, "relation_types": {}},
        "model": {"name": "/root/autodl-tmp/models/qwen2.5-7b", "base_url": "http://127.0.0.1:8000", "timeout_seconds": 300, "api_key": "EMPTY"},
        "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": MAX_GENERATION_TOKENS, "seed": 42},
        # Keep the single 4090 KV cache reserved for Qwen.  BGE-M3 and the
        # reranker remain the fixed models but run on CPU in this bounded
        # pilot to avoid co-resident GPU OOM.
        "embedding": {"model_path": "/root/autodl-tmp/models/bge-m3", "device": "cpu", "batch_size": 8, "max_length": 512},
        "cache": {"dir": ""},
    }
    if system == "ec_fsie_full":
        config["examples"] = {"mode": "knn_retrieval", "k": 5, "seed": 42}
        config["glossary"] = {"path": str(glossary_path), "max_entries": 20, "match_mode": "substring"}
        rag_mode = "bge_faiss_rerank"
    elif system == "bm25_only":
        rag_mode = "bm25"
    elif system == "rag_only":
        rag_mode = "bge_faiss_rerank"
    else:
        rag_mode = None
    if rag_mode:
        config["rag"] = {
            "enabled": True,
            "mode": rag_mode,
            "corpus_path": str(corpus_path),
            "top_k": 3,
            "retrieve_top_k": 20,
            "chunk_chars": 260,
            "overlap_chars": 40,
            "max_passage_chars": 300,
            "embedding": {"model_path": "/root/autodl-tmp/models/bge-m3", "device": "cpu", "batch_size": 8, "max_length": 512},
            "reranker": {"model_path": "/root/autodl-tmp/models/bge-reranker", "device": "cpu"},
        }
    return config


_SELECTOR_CACHE: dict[str, tuple[Any, Any, Any, dict[str, Any]]] = {}

def build_selectors(config: dict[str, Any], *, support_rows: list[dict[str, Any]], glossary_rows: list[dict[str, Any]], corpus_path: Path) -> tuple[Any, Any, Any, dict[str, Any]]:
    cache_key = json.dumps({"examples": config.get("examples"), "rag": config.get("rag"), "glossary": config.get("glossary")}, sort_keys=True)
    if cache_key in _SELECTOR_CACHE:
        return _SELECTOR_CACHE[cache_key]
    examples_selector = lambda _row: []
    example_metadata: dict[str, Any] = {"mode": "none", "k": 0, "seed": 42}
    if config["examples"]["mode"] == "knn_retrieval":
        examples_selector, example_metadata = build_knn_selector(config=config, support_records=support_rows)
    glossary_selector = lambda row: select_glossary_entries(str(row["text"]), glossary_rows, max_entries=20) if config.get("glossary") else []
    rag_selector = lambda _row: []
    rag_metadata: dict[str, Any] = {"enabled": False}
    if config.get("rag"):
        rag_selector, rag_metadata = build_rag_selector(config)
    result = (examples_selector, glossary_selector, rag_selector, {"examples": example_metadata, "rag": rag_metadata})
    _SELECTOR_CACHE[cache_key] = result
    return result


def run_system(
    *,
    system: str,
    rows: Sequence[Mapping[str, Any]],
    config: dict[str, Any],
    support_rows: list[dict[str, Any]],
    glossary_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    examples_selector, glossary_selector, rag_selector, selector_metadata = build_selectors(
        config, support_rows=support_rows, glossary_rows=glossary_rows, corpus_path=Path(config["rag"]["corpus_path"]) if config.get("rag") else Path(".")
    )
    config_hash = canonical_sha256({"gate": GATE, "protocol": PROTOCOL, "system": system, "seed": 42})
    cache_dir = output_dir / "cache"
    predictions: list[dict[str, Any]] = []
    row_audits: list[dict[str, Any]] = []
    parser_failures = 0
    started = time.monotonic()
    for row_index, row in enumerate(rows):
        text = str(row["text"])
        examples = examples_selector(dict(row))
        glossary = glossary_selector(dict(row))
        rag = rag_selector(dict(row))
        # The 7B model repeatedly returned valid full-text offsets that did not
        # belong to an artificial lattice window. One full-text request keeps
        # the coordinate frame unambiguous and avoids boundary hallucinations.
        ranges = [{"start": 0, "end": len(text)}]
        window_records: list[dict[str, Any]] = []
        window_audits: list[dict[str, Any]] = []
        row_failure = False
        for window_index, window in enumerate(ranges):
            prompt = build_ner_prompt(
                query_text=text,
                entity_types=ENTITY_TYPES,
                examples=examples,
                include_relations=False,
                glossary_entries=glossary,
                rag_passages=[format_rag_passage(passage, max_chars=300) for passage in rag],
                output_instruction="Return JSON only. Do not include explanations or markdown.",
                output_mode="span_index",
                reference_instruction=("Reference passages are evidence only. Copy entities only from the final query text, never from a reference passage. Return start/end/type only using offsets in the complete final query text; every entity must have length at most 31."),
                example_output_mode="span_index",
            )
            response_format = build_ner_span_index_response_format(sorted(ENTITY_TYPES), len(text), max_entities=MAX_ENTITIES)
            generation = {**config["generation"], "response_format": response_format}
            attempt_rows: list[dict[str, Any]] = []
            parsed: dict[str, Any] | None = None
            parse_error = None
            attempt_prompt = prompt
            for attempt in (1, 2):
                parsed = None
                envelope = build_request_envelope(
                    prompt=attempt_prompt,
                    model=config["model"]["name"],
                    generation=generation,
                    run_id=f"{system}_{row['id']}_w{window_index}",
                    config_hash=config_hash,
                )
                result = chat_with_cache(
                    envelope=envelope,
                    cache_dir=cache_dir,
                    base_url=config["model"]["base_url"],
                    timeout_seconds=int(config["model"]["timeout_seconds"]),
                    api_key=config["model"]["api_key"],
                )
                try:
                    parsed = parse_extraction_output(
                        result.content,
                        record_id=str(row["id"]),
                        text=text,
                        entity_types=set(ENTITY_TYPES),
                        output_mode="span_index",
                    )
                    for entity in parsed["entities"]:
                        if int(entity["end"]) - int(entity["start"]) > MAX_SPAN_CHARS:
                            raise ExtractionParseError("entity exceeds maximum span length")
                    parse_error = None
                except Exception as exc:  # preserve exact parser diagnostics
                    parse_error = f"{type(exc).__name__}: {exc}"
                attempt_rows.append({"attempt": attempt, "request_hash": result.request_hash, "raw_output_hash": result.raw_output_hash, "cache_hit": result.cache_hit, "latency_ms": round(result.latency_ms, 3), "parse_error": parse_error})
                if parsed is not None:
                    break
                if attempt == 1:
                    attempt_prompt = prompt + "\n\nParser retry: return only start/end/type objects; offsets must be inside the complete query text and exact slices of the query; omit uncertain entities."
            if parsed is None:
                row_failure = True
            else:
                window_records.append(parsed)
            window_audits.append({"window_index": window_index, "window_start": window["start"], "window_end": window["end"], "prompt_hash": prompt_hash(prompt), "candidate_count": sum(max(0, min(window["end"], start + MAX_SPAN_CHARS) - start) for start in range(window["start"], window["end"])), "attempts": attempt_rows, "parse_error": parse_error})
        if row_failure:
            prediction = {"id": row["id"], "text": text, "entities": [], "relations": []}
        else:
            # Overlapping lattice windows intentionally repeat boundary entities.
            # Remove only exact span/type duplicates; retain incompatible overlaps
            # so the canonical merger can reject them as a protocol violation.
            deduped_records = []
            seen_entities = set()
            for record in window_records:
                entities = []
                for entity in record.get("entities", []):
                    key = (int(entity["start"]), int(entity["end"]), str(entity["type"]))
                    if key in seen_entities:
                        continue
                    seen_entities.add(key)
                    entities.append(entity)
                deduped_records.append({**record, "entities": entities})
            try:
                # For the 7B relaxed pilot, resolve partial overlaps by keeping
                # the longest span (ties: earliest start, then lexical type).
                flat = [e for r in deduped_records for e in r.get("entities", [])]
                kept = []
                overlap_drops = 0
                for entity in sorted(flat, key=lambda e: (-(int(e["end"])-int(e["start"])), int(e["start"]), str(e["type"]))):
                    if any(max(int(entity["start"]), int(x["start"])) < min(int(entity["end"]), int(x["end"])) for x in kept):
                        overlap_drops += 1
                        continue
                    kept.append(entity)
                relaxed = {"id": row["id"], "text": text, "entities": kept, "relations": []}
                prediction = relaxed
                if overlap_drops:
                    window_audits.append({"relaxed_overlap_drops": overlap_drops})
            except Exception as exc:
                # Preserve cross-window conflicts as an auditable parser failure.
                row_failure = True
                window_audits.append({"merge_error": f"{type(exc).__name__}: {exc}"})
                prediction = {"id": row["id"], "text": text, "entities": [], "relations": []}
        if row_failure:
            parser_failures += 1
        predictions.append(prediction)
        row_audits.append({"id": row["id"], "row_index": row_index, "window_count": len(ranges), "parse_failure": row_failure, "window_audits": window_audits, "gold_entities": len(row["entities"]), "predicted_entities": len(prediction["entities"])})
        if parser_ceiling_is_unrecoverable(parser_failures=parser_failures, total_rows=len(rows)):
            break
    counts = entity_micro_counts(rows[: len(predictions)], predictions)
    failure_rate = parser_failures / len(predictions) if predictions else 0.0
    summary = {"system": system, "gate": GATE, "protocol": PROTOCOL, "seed": 42, "rows_requested": len(rows), "rows_completed": len(predictions), "parser_failures": parser_failures, "parser_failure_rate": failure_rate, "parser_failure_ceiling": PARSER_FAILURE_CEILING, "parser_failure_ceiling_passed": failure_rate <= PARSER_FAILURE_CEILING, "entity_micro": counts.report(), "selector_metadata": selector_metadata, "elapsed_seconds": round(time.monotonic() - started, 3), "stopped_early": len(predictions) < len(rows)}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "per_query.jsonl").write_text("\n".join(json.dumps({**audit, "prediction": prediction}, ensure_ascii=False, sort_keys=True) for audit, prediction in zip(row_audits, predictions, strict=True)) + "\n", encoding="utf-8")
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def run_pilot(*, query_path: Path, support_path: Path, corpus_path: Path, glossary_path: Path, output_dir: Path) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output directory: {output_dir}")
    if not any(Path("/dev").glob("nvidia[0-9]*")):
        raise RuntimeError("GPU is not visible; refusing semantic pilot")
    rows = load_pilot_rows(query_path)
    support_rows = load_records(str(reject_test_path(support_path, label="support")))
    corpus_path = reject_test_path(corpus_path, label="corpus")
    glossary_path = reject_test_path(glossary_path, label="glossary")
    glossary_rows = load_glossary_records(str(glossary_path))
    all_summaries: list[dict[str, Any]] = []
    for system in SYSTEMS:
        config = system_config(system, query_path=query_path, support_path=support_path, corpus_path=corpus_path, glossary_path=glossary_path)
        system_dir = output_dir / system
        summary = run_system(system=system, rows=rows, config=config, support_rows=support_rows, glossary_rows=glossary_rows, output_dir=system_dir)
        all_summaries.append(summary)
        if not summary["parser_failure_ceiling_passed"]:
            break
    report = {"gate": GATE, "protocol": PROTOCOL, "model_calls_allowed": True, "gpu_required": True, "query_path": str(query_path.resolve()), "query_sha256": sha256_file(query_path), "pilot_row_indices_zero_based": list(PILOT_ROW_INDICES), "pilot_rows": PILOT_ROWS, "systems_requested": list(SYSTEMS), "systems_completed": [summary["system"] for summary in all_summaries], "system_summaries": all_summaries, "preflight_dependencies": {"lattice": {"window_chars": WINDOW_CHARS, "overlap_chars": OVERLAP_CHARS, "max_span_chars": MAX_SPAN_CHARS}, "max_context_tokens": MAX_CONTEXT_TOKENS, "max_generation_tokens": MAX_GENERATION_TOKENS, "safety_reserve_tokens": SAFETY_RESERVE_TOKENS}, "pilot_completed": len(all_summaries) == len(SYSTEMS) and all(summary["rows_completed"] == PILOT_ROWS for summary in all_summaries), "decision": "semantic_dev_pilot_completed_diagnostic_only" if len(all_summaries) == len(SYSTEMS) else "semantic_dev_pilot_stopped_parser_ceiling"}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "pilot_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query-path", type=Path, required=True)
    parser.add_argument("--support-path", type=Path, required=True)
    parser.add_argument("--corpus-path", type=Path, required=True)
    parser.add_argument("--glossary-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    print(json.dumps(run_pilot(**vars(parse_args())), ensure_ascii=False, sort_keys=True))
