#!/usr/bin/env python3
"""Run or dry-run P3 few-shot extraction configs.

Dry-run mode is GPU-free and does not contact vLLM. Non-dry execution requires
an explicitly authorized config.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (
    build_error_retry_prompt,
    build_ner_prompt,
    build_ner_occurrence_response_format,
    build_ner_occurrence_ner_only_response_format,
    build_ner_char_bio_response_format,
    build_ner_anchored_span_index_response_format,
    build_ner_span_index_response_format,
    build_ner_candidate_index_response_format,
    generate_candidate_spans,
    build_request_envelope,
    entity_micro_counts,
    parse_extraction_output,
    prompt_hash,
    select_fixed_random_examples,
    select_glossary_entries,
)
from equipment_ie.llm_labeling import chat_with_cache, request_hash
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record


P3_EXECUTION_GATES = frozenset(
    {
        "P3_GPU_SANITY_APPROVED",
        "P3_DOMAIN_SANITY_APPROVED",
        "P3_D_SANITY_APPROVED",
    }
)

P5_EXECUTION_GATES = frozenset(
    {
        "P5_DOMAIN_PILOT_APPROVED",
        "P5_DOMAIN_REPLICATION_APPROVED",
    }
)

M2_EXECUTION_GATE = "M2_DOMAIN_DEV_Z_APPROVED"
M2_EXECUTION_PHASE = "M2_DOMAIN_DEV_Z_EXECUTION"

REVIEWER_PILOT_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_PILOT_APPROVED"
REVIEWER_PILOT_PHASE = "REVIEWER_BASELINE_B1_PILOT"
REVIEWER_DIAGNOSTIC_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_PARSE_DIAGNOSTIC_APPROVED"
REVIEWER_DIAGNOSTIC_PHASE = "REVIEWER_BASELINE_B1_PARSE_DIAGNOSTIC"
REVIEWER_STABILITY_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_PARSE_STABILITY_20_APPROVED"
REVIEWER_STABILITY_PHASE = "REVIEWER_BASELINE_B1_PARSE_STABILITY_20"
SPAN_INDEX_DIAGNOSTIC_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_SPAN_INDEX_DIAGNOSTIC_APPROVED"
SPAN_INDEX_DIAGNOSTIC_PHASE = "REVIEWER_BASELINE_B1_SPAN_INDEX_DIAGNOSTIC"
NER_ENVELOPE_SMOKE_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_NER_ENVELOPE_SMOKE_TEST_APPROVED"
NER_ENVELOPE_SMOKE_PHASE = "REVIEWER_BASELINE_B1_NER_ENVELOPE_SMOKE_TEST"
DOMAIN_SCHEMA_SMOKE_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_DOMAIN_SCHEMA_COMPATIBILITY_SMOKE_APPROVED"
DOMAIN_SCHEMA_SMOKE_PHASE = "REVIEWER_BASELINE_B1_DOMAIN_SCHEMA_COMPATIBILITY_SMOKE"
OUTPUT_BUDGET_REPAIR_SMOKE_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_OUTPUT_BUDGET_REPAIR_SMOKE_APPROVED"
OUTPUT_BUDGET_REPAIR_SMOKE_PHASE = "REVIEWER_BASELINE_B1_OUTPUT_BUDGET_REPAIR_SMOKE"
OUTPUT_SCHEMA_BOUNDED_SMOKE_15_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_OUTPUT_SCHEMA_BOUNDED_SMOKE_15_APPROVED"
OUTPUT_SCHEMA_BOUNDED_SMOKE_15_PHASE = "REVIEWER_BASELINE_B1_OUTPUT_SCHEMA_BOUNDED_SMOKE_15"
FORMAL_B1_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_FORMAL_APPROVED"
FORMAL_B1_PHASE = "REVIEWER_BASELINE_B1_FORMAL"
QWEN_PARSER_CORRECTION_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_QWEN_PARSER_CORRECTION_APPROVED"
)
QWEN_PARSER_CORRECTION_PHASE = (
    "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_QWEN_PARSER_CORRECTION"
)
QWEN_PROMPT_REPAIR_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_QWEN_PROMPT_REPAIR_APPROVED"
)
QWEN_PROMPT_REPAIR_PHASE = (
    "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_QWEN_PROMPT_REPAIR"
)
OCCURRENCE_REPAIR_PILOT_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_REPAIR_PILOT_APPROVED"
)
OCCURRENCE_REPAIR_PILOT_PHASE = (
    "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_REPAIR_PILOT"
)
CANDIDATE_INDEX_PILOT_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_CANDIDATE_INDEX_PILOT_APPROVED"
)
CANDIDATE_INDEX_PILOT_PHASE = (
    "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_CANDIDATE_INDEX_PILOT"
)
ANCHORED_SPAN_INDEX_CORRECTION_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_ANCHORED_SPAN_INDEX_CORRECTION_APPROVED"
)
ANCHORED_SPAN_INDEX_CORRECTION_PHASE = (
    "REVIEWER_BASELINE_MAIN_ANCHORED_SPAN_INDEX_CORRECTION"
)
CHAR_BIO_QWEN_PILOT_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_BIO_QWEN_PILOT_APPROVED"
)
CHAR_BIO_QWEN_PILOT_PHASE = "REVIEWER_BASELINE_MAIN_UNIFIED_BIO_QWEN_PILOT"
CHAR_BIO_QWEN_REPAIR_PILOT_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_BIO_QWEN_REPAIR_PILOT_APPROVED"
)
CHAR_BIO_QWEN_REPAIR_PILOT_PHASE = (
    "REVIEWER_BASELINE_MAIN_UNIFIED_BIO_QWEN_REPAIR_PILOT"
)
B1_V2_PILOT_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_V2_PROTOCOL_CORRECTION_PILOT_APPROVED"
B1_V2_PILOT_PHASE = "REVIEWER_BASELINE_B1_V2_PROTOCOL_CORRECTION_PILOT"
B1_V2_FORMAL_GATE = "JISE_ECFSIE_REVIEW_BASELINE_B1_V2_PROTOCOL_CORRECTION_FORMAL_APPROVED"
B1_V2_FORMAL_PHASE = "REVIEWER_BASELINE_B1_V2_PROTOCOL_CORRECTION_FORMAL"
QWEN_OCCURRENCE_SANITIZED_PILOT_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_QWEN_OCCURRENCE_SANITIZED_DEV_PILOT_APPROVED"
)
QWEN_OCCURRENCE_SANITIZED_PILOT_PHASE = (
    "REVIEWER_BASELINE_QWEN_OCCURRENCE_SANITIZED_DEV_PILOT"
)
QWEN_NEUTRAL_ENVELOPE_FORMAL_GATE = (
    "JISE_ECFSIE_REVIEW_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_EXECUTION_APPROVED"
)
QWEN_NEUTRAL_ENVELOPE_FORMAL_PHASE = (
    "REVIEWER_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_EXECUTION"
)
GLOSSARY_ONLY_DEV_PILOT_GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_DEV_PILOT_APPROVED"
GLOSSARY_ONLY_DEV_PILOT_PHASE = "REVIEWER_GLOSSARY_ONLY_DEV_PILOT"
GLOSSARY_ONLY_FORMAL_GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_FORMAL_EXECUTION_APPROVED"
GLOSSARY_ONLY_FORMAL_PHASE = "REVIEWER_GLOSSARY_ONLY_FORMAL_EXECUTION"

NER_PUBLIC_EXECUTION_GATE = "NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED"
NER_PUBLIC_EXECUTION_PHASE = "NER_PUBLIC_CLUENER_FINAL"

FULL_IE_EXECUTION_GATES = {
    "FULL_IE_DOMAIN_DEV_SANITY_APPROVED": "FULL_IE_DOMAIN_DEV_SANITY",
    "FULL_IE_CLUENER_TUNE_SANITY_APPROVED": "FULL_IE_CLUENER_TUNE_SANITY",
    NER_PUBLIC_EXECUTION_GATE: NER_PUBLIC_EXECUTION_PHASE,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required for config loading") from exc
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return len(rows)


def refuse_existing_outputs(outputs: dict[str, Any], keys: tuple[str, ...]) -> None:
    """Refuse any run that would replace an existing artifact."""

    paths = [Path(str(outputs[key])) for key in keys]
    if len(set(paths)) != len(paths):
        raise FileExistsError("output paths must be distinct")
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite existing outputs: {existing}")


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def validate_execution_gate(execution: dict[str, Any]) -> None:
    if execution.get("authorized") is not True:
        raise RuntimeError("config execution.authorized must be true for model calls")
    if execution.get("model_calls_allowed") is not True:
        raise RuntimeError("config execution.model_calls_allowed must be true for model calls")

    human_gate = execution.get("human_gate")
    phase = str(execution.get("phase", ""))
    if human_gate in P3_EXECUTION_GATES:
        return
    if human_gate in P5_EXECUTION_GATES:
        if not phase.startswith("P5"):
            raise RuntimeError("P5 human gate requires execution.phase to start with P5")
        return
    if human_gate == M2_EXECUTION_GATE:
        if phase != M2_EXECUTION_PHASE:
            raise RuntimeError(
                f"{M2_EXECUTION_GATE} requires execution.phase={M2_EXECUTION_PHASE}"
            )
        return

    if human_gate == REVIEWER_PILOT_GATE:
        if phase != REVIEWER_PILOT_PHASE:
            raise RuntimeError(
                f"{REVIEWER_PILOT_GATE} requires execution.phase={REVIEWER_PILOT_PHASE}"
            )
        return

    if human_gate == REVIEWER_DIAGNOSTIC_GATE:
        if phase != REVIEWER_DIAGNOSTIC_PHASE:
            raise RuntimeError(
                f"{REVIEWER_DIAGNOSTIC_GATE} requires execution.phase={REVIEWER_DIAGNOSTIC_PHASE}"
            )
        return

    if human_gate == REVIEWER_STABILITY_GATE:
        if phase != REVIEWER_STABILITY_PHASE:
            raise RuntimeError(
                f"{REVIEWER_STABILITY_GATE} requires execution.phase={REVIEWER_STABILITY_PHASE}"
            )
        return

    if human_gate == SPAN_INDEX_DIAGNOSTIC_GATE:
        if phase != SPAN_INDEX_DIAGNOSTIC_PHASE:
            raise RuntimeError(
                f"{SPAN_INDEX_DIAGNOSTIC_GATE} requires execution.phase={SPAN_INDEX_DIAGNOSTIC_PHASE}"
            )
        return

    if human_gate == NER_ENVELOPE_SMOKE_GATE:
        if phase != NER_ENVELOPE_SMOKE_PHASE:
            raise RuntimeError(
                f"{NER_ENVELOPE_SMOKE_GATE} requires execution.phase={NER_ENVELOPE_SMOKE_PHASE}"
            )
        return

    if human_gate == DOMAIN_SCHEMA_SMOKE_GATE:
        if phase != DOMAIN_SCHEMA_SMOKE_PHASE:
            raise RuntimeError(
                f"{DOMAIN_SCHEMA_SMOKE_GATE} requires execution.phase={DOMAIN_SCHEMA_SMOKE_PHASE}"
            )
        return

    if human_gate == OUTPUT_BUDGET_REPAIR_SMOKE_GATE:
        if phase != OUTPUT_BUDGET_REPAIR_SMOKE_PHASE:
            raise RuntimeError(
                f"{OUTPUT_BUDGET_REPAIR_SMOKE_GATE} requires execution.phase={OUTPUT_BUDGET_REPAIR_SMOKE_PHASE}"
            )
        return

    if human_gate == OUTPUT_SCHEMA_BOUNDED_SMOKE_15_GATE:
        if phase != OUTPUT_SCHEMA_BOUNDED_SMOKE_15_PHASE:
            raise RuntimeError(
                f"{OUTPUT_SCHEMA_BOUNDED_SMOKE_15_GATE} requires execution.phase={OUTPUT_SCHEMA_BOUNDED_SMOKE_15_PHASE}"
            )
        return

    if human_gate == FORMAL_B1_GATE:
        if phase != FORMAL_B1_PHASE:
            raise RuntimeError(
                f"{FORMAL_B1_GATE} requires execution.phase={FORMAL_B1_PHASE}"
            )
        return

    if human_gate == "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_FORMAL_APPROVED":
        if phase != "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_FORMAL":
            raise RuntimeError(
                f"{human_gate} requires execution.phase="
                "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_FORMAL"
            )
        return

    if human_gate == "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_PILOT_APPROVED":
        if phase != "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_PILOT":
            raise RuntimeError(
                f"{human_gate} requires execution.phase="
                "REVIEWER_BASELINE_MAIN_UNIFIED_OCCURRENCE_PILOT"
            )
        return

    if human_gate == QWEN_PARSER_CORRECTION_GATE:
        if phase != QWEN_PARSER_CORRECTION_PHASE:
            raise RuntimeError(
                f"{QWEN_PARSER_CORRECTION_GATE} requires execution.phase="
                f"{QWEN_PARSER_CORRECTION_PHASE}"
            )
        return

    if human_gate == QWEN_PROMPT_REPAIR_GATE:
        if phase != QWEN_PROMPT_REPAIR_PHASE:
            raise RuntimeError(
                f"{QWEN_PROMPT_REPAIR_GATE} requires execution.phase="
                f"{QWEN_PROMPT_REPAIR_PHASE}"
            )
        return

    if human_gate == OCCURRENCE_REPAIR_PILOT_GATE:
        if phase != OCCURRENCE_REPAIR_PILOT_PHASE:
            raise RuntimeError(
                f"{OCCURRENCE_REPAIR_PILOT_GATE} requires execution.phase="
                f"{OCCURRENCE_REPAIR_PILOT_PHASE}"
            )
        return

    if human_gate == CANDIDATE_INDEX_PILOT_GATE:
        if phase != CANDIDATE_INDEX_PILOT_PHASE:
            raise RuntimeError(
                f"{CANDIDATE_INDEX_PILOT_GATE} requires execution.phase="
                f"{CANDIDATE_INDEX_PILOT_PHASE}"
            )
        return

    if human_gate == ANCHORED_SPAN_INDEX_CORRECTION_GATE:
        if phase != ANCHORED_SPAN_INDEX_CORRECTION_PHASE:
            raise RuntimeError(
                f"{ANCHORED_SPAN_INDEX_CORRECTION_GATE} requires execution.phase="
                f"{ANCHORED_SPAN_INDEX_CORRECTION_PHASE}"
            )
        return

    if human_gate == CHAR_BIO_QWEN_PILOT_GATE:
        if phase != CHAR_BIO_QWEN_PILOT_PHASE:
            raise RuntimeError(
                f"{CHAR_BIO_QWEN_PILOT_GATE} requires execution.phase="
                f"{CHAR_BIO_QWEN_PILOT_PHASE}"
            )
        return

    if human_gate == CHAR_BIO_QWEN_REPAIR_PILOT_GATE:
        if phase != CHAR_BIO_QWEN_REPAIR_PILOT_PHASE:
            raise RuntimeError(
                f"{CHAR_BIO_QWEN_REPAIR_PILOT_GATE} requires execution.phase="
                f"{CHAR_BIO_QWEN_REPAIR_PILOT_PHASE}"
            )
        return

    if human_gate == B1_V2_PILOT_GATE:
        if phase != B1_V2_PILOT_PHASE:
            raise RuntimeError(
                f"{B1_V2_PILOT_GATE} requires execution.phase={B1_V2_PILOT_PHASE}"
            )
        return

    if human_gate == B1_V2_FORMAL_GATE:
        if phase != B1_V2_FORMAL_PHASE:
            raise RuntimeError(
                f"{B1_V2_FORMAL_GATE} requires execution.phase={B1_V2_FORMAL_PHASE}"
            )
        return

    if human_gate == QWEN_OCCURRENCE_SANITIZED_PILOT_GATE:
        if phase != QWEN_OCCURRENCE_SANITIZED_PILOT_PHASE:
            raise RuntimeError(
                f"{QWEN_OCCURRENCE_SANITIZED_PILOT_GATE} requires execution.phase="
                f"{QWEN_OCCURRENCE_SANITIZED_PILOT_PHASE}"
            )
        return

    if human_gate == QWEN_NEUTRAL_ENVELOPE_FORMAL_GATE:
        if phase != QWEN_NEUTRAL_ENVELOPE_FORMAL_PHASE:
            raise RuntimeError(
                f"{QWEN_NEUTRAL_ENVELOPE_FORMAL_GATE} requires execution.phase="
                f"{QWEN_NEUTRAL_ENVELOPE_FORMAL_PHASE}"
            )
        return

    if human_gate == GLOSSARY_ONLY_DEV_PILOT_GATE:
        if phase != GLOSSARY_ONLY_DEV_PILOT_PHASE:
            raise RuntimeError(
                f"{GLOSSARY_ONLY_DEV_PILOT_GATE} requires execution.phase="
                f"{GLOSSARY_ONLY_DEV_PILOT_PHASE}"
            )
        return

    if human_gate == GLOSSARY_ONLY_FORMAL_GATE:
        if phase != GLOSSARY_ONLY_FORMAL_PHASE:
            raise RuntimeError(
                f"{GLOSSARY_ONLY_FORMAL_GATE} requires execution.phase="
                f"{GLOSSARY_ONLY_FORMAL_PHASE}"
            )
        return

    required_phase = FULL_IE_EXECUTION_GATES.get(human_gate)
    if required_phase is not None:
        if phase != required_phase:
            raise RuntimeError(f"{human_gate} requires execution.phase={required_phase}")
        return

    allowed = sorted(
        P3_EXECUTION_GATES
        | P5_EXECUTION_GATES
        | {M2_EXECUTION_GATE}
        | {REVIEWER_PILOT_GATE}
        | {REVIEWER_DIAGNOSTIC_GATE}
        | {REVIEWER_STABILITY_GATE}
        | {SPAN_INDEX_DIAGNOSTIC_GATE}
        | {NER_ENVELOPE_SMOKE_GATE}
        | {DOMAIN_SCHEMA_SMOKE_GATE}
        | {OUTPUT_BUDGET_REPAIR_SMOKE_GATE}
        | {OUTPUT_SCHEMA_BOUNDED_SMOKE_15_GATE}
        | {FORMAL_B1_GATE}
        | {
            "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_FORMAL_APPROVED",
            "JISE_ECFSIE_REVIEW_BASELINE_MAIN_UNIFIED_OCCURRENCE_PILOT_APPROVED",
            QWEN_PARSER_CORRECTION_GATE,
            QWEN_PROMPT_REPAIR_GATE,
            OCCURRENCE_REPAIR_PILOT_GATE,
            CANDIDATE_INDEX_PILOT_GATE,
            ANCHORED_SPAN_INDEX_CORRECTION_GATE,
            CHAR_BIO_QWEN_REPAIR_PILOT_GATE,
            B1_V2_PILOT_GATE,
            B1_V2_FORMAL_GATE,
            QWEN_OCCURRENCE_SANITIZED_PILOT_GATE,
            QWEN_NEUTRAL_ENVELOPE_FORMAL_GATE,
            GLOSSARY_ONLY_DEV_PILOT_GATE,
            GLOSSARY_ONLY_FORMAL_GATE,
        }
        | set(FULL_IE_EXECUTION_GATES)
    )
    raise RuntimeError(f"non-dry extraction human_gate must be one of: {allowed}")


def load_records(path: str) -> list[dict[str, Any]]:
    return [record for record in iter_jsonl(Path(path))]


def load_glossary_records(path: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, record in enumerate(iter_jsonl(Path(path), validate=False), start=1):
        term = record.get("term")
        entity_type = record.get("type")
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"{path}:{line_number}: glossary term must be a non-empty string")
        if not isinstance(entity_type, str) or not entity_type.strip():
            raise ValueError(f"{path}:{line_number}: glossary type must be a non-empty string")
        records.append(dict(record))
    if not records:
        raise ValueError(f"{path}: glossary must contain at least one row")
    return records


def chunk_text(text: str, *, chunk_chars: int, overlap_chars: int) -> list[str]:
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= chunk_chars:
        raise ValueError("overlap_chars must be non-negative and smaller than chunk_chars")
    if len(text) <= chunk_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    step = chunk_chars - overlap_chars
    while start < len(text):
        chunk = text[start : start + chunk_chars]
        if chunk:
            chunks.append(chunk)
        if start + chunk_chars >= len(text):
            break
        start += step
    return chunks


def load_rag_passages(path: str, *, chunk_chars: int, overlap_chars: int) -> list[dict[str, Any]]:
    passages: list[dict[str, Any]] = []
    for line_number, record in enumerate(iter_jsonl(Path(path), validate=False), start=1):
        text = record.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{path}:{line_number}: RAG corpus row must contain non-empty text")
        source_id = str(record.get("id") or f"row-{line_number}")
        title = str(record.get("title") or record.get("source_id") or source_id)
        for chunk_index, chunk in enumerate(
            chunk_text(text.strip(), chunk_chars=chunk_chars, overlap_chars=overlap_chars)
        ):
            passages.append(
                {
                    "id": f"{source_id}#chunk-{chunk_index}",
                    "source_id": source_id,
                    "source_type": record.get("source_type"),
                    "title": title,
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "content_sha256": record.get("content_sha256"),
                }
            )
    if not passages:
        raise ValueError(f"{path}: RAG corpus produced no passages")
    return passages


def load_rag_excluded_source_ids(rag_config: dict[str, Any]) -> set[str]:
    paths: list[str] = []
    single_path = rag_config.get("exclude_source_ids_path")
    if single_path:
        paths.append(str(single_path))
    multiple_paths = rag_config.get("exclude_source_ids_paths", [])
    if isinstance(multiple_paths, str):
        paths.append(multiple_paths)
    elif isinstance(multiple_paths, list):
        paths.extend(str(path) for path in multiple_paths)
    elif multiple_paths:
        raise ValueError("rag.exclude_source_ids_paths must be a string or list")

    excluded: set[str] = set()
    for path in paths:
        for line_number, record in enumerate(iter_jsonl(Path(path), validate=False), start=1):
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id:
                raise ValueError(f"{path}:{line_number}: exclusion row must contain non-empty id")
            excluded.add(record_id)
    return excluded


def format_rag_passage(passage: dict[str, Any], *, max_chars: int) -> str:
    text = str(passage["text"])
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "..."
    return (
        f"{passage['title']} | {passage.get('source_type') or 'unknown'} | "
        f"{passage['id']}: {text}"
    )


def char_ngrams(text: str, *, n: int = 2) -> set[str]:
    compact = "".join(text.split())
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def lexical_rag_score(query_text: str, passage: dict[str, Any]) -> tuple[int, int, int, str]:
    passage_text = str(passage["text"])
    query_grams = char_ngrams(query_text)
    passage_grams = char_ngrams(passage_text)
    overlap = len(query_grams & passage_grams)
    exact_title = 1 if str(passage.get("title") or "") in query_text else 0
    exact_source = 1 if str(passage.get("source_id") or "") in query_text else 0
    return (overlap, exact_title, exact_source, str(passage["id"]))


def load_rag_replay_manifest(path: str, config: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{path}: RAG replay manifest must be a JSON object")
    rows = manifest.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: RAG replay manifest rows must be a non-empty list")

    # A replay file is executable evidence only when its retrieval backend and
    # leakage audit are explicit. Legacy manifests remain readable for
    # preparation/round-trip inspection, but can never enter a model call.
    executable = config.get("execution", {}).get("model_calls_allowed") is True
    if executable and manifest.get("manifest_kind") != "rag_replay":
        raise ValueError(f"{path}: replay manifest_kind must be rag_replay")
    selection_backend = manifest.get("selection_backend")
    if executable and (not isinstance(selection_backend, str) or not selection_backend):
        raise ValueError(f"{path}: selection_backend is required")
    if executable and manifest.get("usable_for_model_calls") is not True:
        raise ValueError(f"{path}: replay manifest is not usable_for_model_calls")
    retrieval_mode = str(manifest.get("retrieval_mode", ""))
    if executable and retrieval_mode == "bge_m3_reranker_top20_to_top3":
        if manifest.get("dense_artifact_ready") is not True:
            raise ValueError(f"{path}: dense replay requires dense_artifact_ready=true")
        if selection_backend != "bge_m3_faiss_reranker":
            raise ValueError(
                f"{path}: dense replay selection_backend must be bge_m3_faiss_reranker"
            )
    leakage_audit = manifest.get("leakage_audit")
    if executable and not isinstance(leakage_audit, dict):
        raise ValueError(f"{path}: leakage_audit is required")
    if executable:
        for field in ("source_id_exclusion", "exact_text_exclusion", "eight_gram_exclusion"):
            if leakage_audit.get(field) is not True:
                raise ValueError(f"{path}: leakage_audit.{field} must be true")
        if leakage_audit.get("labels_stripped") is not True and not manifest.get(
            "labels_stripped_corpus_sha256"
        ):
            raise ValueError(f"{path}: labels-stripped corpus identity is required")
        for field in ("residual_exact_text_rows", "residual_8gram_rows"):
            residual = leakage_audit.get(field)
            if residual is not None and residual:
                raise ValueError(f"{path}: leakage residuals present in {field}")
    declared_count = manifest.get("query_count")
    if declared_count is not None and int(declared_count) != len(rows):
        raise ValueError(f"{path}: query_count does not match replay rows")
    query_limit = config.get("query_limit")
    if query_limit is not None and int(query_limit) != len(rows):
        raise ValueError(f"{path}: replay rows do not match config query_limit")
    expected_identity = config.get("protocol", {}).get("condition_identity", {})
    for field in ("retrieval_mode", "retrieve_top_k", "top_k"):
        expected = expected_identity.get(field)
        actual = manifest.get(field)
        if expected is not None and actual != expected:
            raise ValueError(f"{path}: {field} mismatch: {actual!r} != {expected!r}")

    query_path = config.get("data", {}).get("query_path")
    manifest_query_sha = manifest.get("query_path_sha256")
    if query_path and manifest_query_sha:
        current_query_sha = sha256_file(str(query_path))
        if current_query_sha != manifest_query_sha:
            raise ValueError(
                f"{path}: query_path_sha256 mismatch: {current_query_sha} != {manifest_query_sha}"
            )

    replay: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path}: row {index} must be an object")
        query_id = row.get("id")
        selected = row.get("selected_passages")
        if not isinstance(query_id, str) or not query_id:
            raise ValueError(f"{path}: row {index} must contain non-empty id")
        if query_id in replay:
            raise ValueError(f"{path}: duplicate replay id {query_id}")
        if not isinstance(selected, list):
            raise ValueError(f"{path}: row {query_id} selected_passages must be a list")
        expected_top_k = expected_identity.get("top_k")
        if expected_top_k is not None and len(selected) != int(expected_top_k):
            raise ValueError(
                f"{path}: row {query_id} selected passage count {len(selected)} "
                f"does not match top_k={expected_top_k}"
            )
        passages: list[dict[str, Any]] = []
        for passage_index, passage in enumerate(selected):
            if not isinstance(passage, dict):
                raise ValueError(f"{path}: row {query_id} passage {passage_index} must be an object")
            passage_id = passage.get("id")
            display = passage.get("display")
            if not isinstance(passage_id, str) or not passage_id:
                raise ValueError(f"{path}: row {query_id} passage {passage_index} missing id")
            if not isinstance(display, str) or not display:
                raise ValueError(f"{path}: row {query_id} passage {passage_index} missing display")
            passages.append(dict(passage))
        replay[query_id] = passages

    return replay, {
        "enabled": True,
        "mode": "replay_manifest",
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(str(manifest_path)),
        "source_rag_mode": manifest.get("source_rag_mode"),
        "source_config_sha256": manifest.get("source_config_sha256"),
        "query_path_sha256": manifest.get("query_path_sha256"),
        "query_records": len(rows),
    }


def build_rag_selector(
    config: dict[str, Any],
) -> tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]:
    rag_config = config.get("rag")
    if not rag_config or rag_config.get("enabled") is not True:
        return lambda _record: [], {"enabled": False}

    mode = str(rag_config.get("mode", "lexical_preview"))
    # Preparation and dry-run configs must never initialize dense models. The
    # formal bge+reranker path is available only after an explicit execution
    # gate enables model calls.
    if mode == "bge_faiss_rerank" and config.get("execution", {}).get("model_calls_allowed") is not True:
        mode = "lexical_preview"
    if mode == "replay_manifest":
        replay_path = rag_config.get("replay_manifest_path")
        if not isinstance(replay_path, str) or not replay_path:
            raise ValueError("rag.replay_manifest_path is required for replay_manifest mode")
        replay, metadata = load_rag_replay_manifest(replay_path, config)

        def select_replay(record: dict[str, Any]) -> list[dict[str, Any]]:
            record_id = str(record["id"])
            if record_id not in replay:
                raise ValueError(f"RAG replay manifest has no row for query id {record_id}")
            return [dict(passage) for passage in replay[record_id]]

        return select_replay, metadata

    corpus_path = rag_config["corpus_path"]
    top_k = int(rag_config.get("top_k", 3))
    retrieve_top_k = int(rag_config.get("retrieve_top_k", 20))
    chunk_chars = int(rag_config.get("chunk_chars", 260))
    overlap_chars = int(rag_config.get("overlap_chars", 40))
    max_passage_chars = int(rag_config.get("max_passage_chars", 300))
    passages = load_rag_passages(
        corpus_path,
        chunk_chars=chunk_chars,
        overlap_chars=overlap_chars,
    )
    raw_chunk_count = len(passages)
    excluded_source_ids = load_rag_excluded_source_ids(rag_config)
    if excluded_source_ids:
        passages = [
            passage for passage in passages if str(passage["source_id"]) not in excluded_source_ids
        ]
    if not passages:
        raise ValueError("RAG source-id exclusion removed all passages")
    if top_k <= 0 or retrieve_top_k < top_k:
        raise ValueError("rag.top_k must be positive and rag.retrieve_top_k must be >= top_k")

    if mode == "bm25":
        try:
            from scripts.build_bm25_retrieval import BM25Index, CorpusRow
        except ImportError:
            from build_bm25_retrieval import BM25Index, CorpusRow
        index = BM25Index(
            [CorpusRow(str(passage["id"]), str(passage["text"])) for passage in passages]
        )

        def select_bm25(record: dict[str, Any]) -> list[dict[str, Any]]:
            selected = index.retrieve(str(record["text"]), top_k=top_k)
            by_id = {str(passage["id"]): passage for passage in passages}
            return [
                {
                    **by_id[str(item["id"])],
                    "bm25_score": float(item["score"]),
                    "display": format_rag_passage(by_id[str(item["id"])], max_chars=max_passage_chars),
                }
                for item in selected
            ]

        return select_bm25, {
            "enabled": True,
            "mode": mode,
            "corpus_path": corpus_path,
            "corpus_rows_sha256": sha256_file(corpus_path),
            "excluded_source_ids": len(excluded_source_ids),
            "raw_chunk_count": raw_chunk_count,
            "chunk_count": len(passages),
            "retrieve_top_k": retrieve_top_k,
            "top_k": top_k,
            "index": "BM25Index",
        }

    if mode == "lexical_preview":
        def select(record: dict[str, Any]) -> list[dict[str, Any]]:
            ranked = sorted(
                passages,
                key=lambda passage: lexical_rag_score(str(record["text"]), passage),
                reverse=True,
            )
            selected = ranked[:top_k]
            return [
                {
                    **passage,
                    "display": format_rag_passage(passage, max_chars=max_passage_chars),
                }
                for passage in selected
            ]

        return select, {
            "enabled": True,
            "mode": mode,
            "note": "GPU-free lexical preview for prompt/evidence audit only; final D uses bge_faiss_rerank.",
            "corpus_path": corpus_path,
            "corpus_rows_sha256": sha256_file(corpus_path),
            "excluded_source_ids": len(excluded_source_ids),
            "raw_chunk_count": raw_chunk_count,
            "chunk_count": len(passages),
            "chunk_chars": chunk_chars,
            "overlap_chars": overlap_chars,
            "retrieve_top_k": retrieve_top_k,
            "top_k": top_k,
        }

    if mode == "bge_faiss_rerank":
        embedding_config = rag_config.get("embedding", config.get("embedding", {}))
        reranker_config = rag_config.get("reranker", {})
        model_path = embedding_config.get("model_path", "/root/autodl-tmp/models/bge-m3")
        reranker_path = reranker_config.get("model_path", "/root/autodl-tmp/models/bge-reranker")
        batch_size = int(embedding_config.get("batch_size", 8))
        max_length = int(embedding_config.get("max_length", 512))
        device = embedding_config.get("device", "cpu")
        use_fp16 = bool(embedding_config.get("use_fp16", False))
        reranker_device = reranker_config.get("device", device)
        reranker_use_fp16 = bool(reranker_config.get("use_fp16", use_fp16))
        if device == "cpu" and reranker_device == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        try:
            import faiss
            import numpy as np
            from FlagEmbedding import BGEM3FlagModel, FlagReranker
        except ImportError as exc:
            raise RuntimeError("bge_faiss_rerank requires faiss, numpy, and FlagEmbedding") from exc

        model = BGEM3FlagModel(model_path, use_fp16=use_fp16, device=device)
        reranker = FlagReranker(reranker_path, use_fp16=reranker_use_fp16, device=reranker_device)

        def encode(texts: list[str]) -> Any:
            output = model.encode(texts, batch_size=batch_size, max_length=max_length)
            dense = output["dense_vecs"] if isinstance(output, dict) else output
            vectors = np.asarray(dense, dtype="float32")
            if vectors.ndim == 1:
                vectors = vectors.reshape(1, -1)
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError("BGE-M3 produced a zero embedding")
            return vectors / norms

        passage_vectors = encode([str(passage["text"]) for passage in passages])
        index = faiss.IndexFlatIP(passage_vectors.shape[1])
        index.add(passage_vectors)

        def select(record: dict[str, Any]) -> list[dict[str, Any]]:
            query_text = str(record["text"])
            query_vector = encode([query_text])
            _, indices = index.search(query_vector, retrieve_top_k)
            candidates = [passages[int(index_)] for index_ in indices[0] if int(index_) >= 0]
            pairs = [[query_text, str(passage["text"])] for passage in candidates]
            scores = reranker.compute_score(pairs) if pairs else []
            if isinstance(scores, float):
                scores = [scores]
            ranked = sorted(zip(candidates, scores), key=lambda item: float(item[1]), reverse=True)
            return [
                {
                    **passage,
                    "rerank_score": float(score),
                    "display": format_rag_passage(passage, max_chars=max_passage_chars),
                }
                for passage, score in ranked[:top_k]
            ]

        return select, {
            "enabled": True,
            "mode": mode,
            "corpus_path": corpus_path,
            "corpus_rows_sha256": sha256_file(corpus_path),
            "excluded_source_ids": len(excluded_source_ids),
            "raw_chunk_count": raw_chunk_count,
            "chunk_count": len(passages),
            "chunk_chars": chunk_chars,
            "overlap_chars": overlap_chars,
            "retrieve_top_k": retrieve_top_k,
            "top_k": top_k,
            "embedding_model_path": model_path,
            "embedding_device": device,
            "reranker_model_path": reranker_path,
            "reranker_device": reranker_device,
            "faiss_index": "IndexFlatIP",
        }

    raise ValueError(f"unsupported rag mode {mode!r}")


def empty_prediction(gold: dict[str, Any]) -> dict[str, Any]:
    return {"id": gold["id"], "text": gold["text"], "entities": [], "relations": []}


def elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000.0, 3)


def support_candidates(records: list[dict[str, Any]], *, k: int) -> list[dict[str, Any]]:
    candidates = [dict(record) for record in records if record.get("entities")]
    if len(candidates) < k:
        raise ValueError(f"need at least {k} support records with entities")
    return candidates


def build_knn_selector(
    *,
    config: dict[str, Any],
    support_records: list[dict[str, Any]],
) -> tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]:
    example_config = config["examples"]
    k = int(example_config["k"])
    embedding_config = config.get("embedding", {})
    model_path = embedding_config.get("model_path", "/root/autodl-tmp/models/bge-m3")
    batch_size = int(embedding_config.get("batch_size", 8))
    max_length = int(embedding_config.get("max_length", 512))
    device = embedding_config.get("device", "cpu")
    use_fp16 = bool(embedding_config.get("use_fp16", False))
    if device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    try:
        import faiss
        import numpy as np
        from FlagEmbedding import BGEM3FlagModel
    except ImportError as exc:
        raise RuntimeError("knn_retrieval requires faiss, numpy, and FlagEmbedding") from exc

    candidates = support_candidates(support_records, k=k)

    model = BGEM3FlagModel(model_path, use_fp16=use_fp16, device=device)

    def encode(texts: list[str]) -> Any:
        output = model.encode(texts, batch_size=batch_size, max_length=max_length)
        dense = output["dense_vecs"] if isinstance(output, dict) else output
        vectors = np.asarray(dense, dtype="float32")
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("BGE-M3 produced a zero embedding")
        return vectors / norms

    support_vectors = encode([str(record["text"]) for record in candidates])
    index = faiss.IndexFlatIP(support_vectors.shape[1])
    index.add(support_vectors)

    def select(record: dict[str, Any]) -> list[dict[str, Any]]:
        query_vector = encode([str(record["text"])])
        _, indices = index.search(query_vector, k)
        return [dict(candidates[int(index_)]) for index_ in indices[0] if int(index_) >= 0]

    metadata = {
        "mode": "knn_retrieval",
        "k": k,
        "support_candidates": len(candidates),
        "embedding_model_path": model_path,
        "embedding_device": device,
        "embedding_max_length": max_length,
        "faiss_index": "IndexFlatIP",
    }
    return select, metadata


def build_knn_replay_selector(
    *,
    config: dict[str, Any],
    support_records: list[dict[str, Any]],
) -> tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]:
    example_config = config["examples"]
    k = int(example_config["k"])
    source_path = example_config["source_per_query_path"]
    support_by_id = {str(record["id"]): dict(record) for record in support_records}
    example_ids_by_query: dict[str, list[str]] = {}
    for line_number, row in enumerate(iter_jsonl(Path(source_path), validate=False), start=1):
        query_id = row.get("id")
        example_ids = row.get("example_ids")
        if not isinstance(query_id, str) or not query_id:
            raise ValueError(f"{source_path}:{line_number}: replay row id must be a non-empty string")
        if not isinstance(example_ids, list) or len(example_ids) < k:
            raise ValueError(f"{source_path}:{line_number}: replay row must contain at least {k} example_ids")
        normalized_ids = [str(example_id) for example_id in example_ids[:k]]
        missing = [example_id for example_id in normalized_ids if example_id not in support_by_id]
        if missing:
            raise ValueError(f"{source_path}:{line_number}: replay example ids missing from support: {missing}")
        example_ids_by_query[query_id] = normalized_ids

    def select(record: dict[str, Any]) -> list[dict[str, Any]]:
        query_id = str(record["id"])
        example_ids = example_ids_by_query.get(query_id)
        if example_ids is None:
            raise ValueError(f"{source_path}: no replay example_ids for query {query_id}")
        return [dict(support_by_id[example_id]) for example_id in example_ids]

    metadata = {
        "mode": "knn_replay",
        "source_mode": "knn_retrieval",
        "source_per_query_path": source_path,
        "k": k,
        "seed": int(example_config["seed"]),
        "query_replay_rows": len(example_ids_by_query),
    }
    return select, metadata


def build_glossary_selector(
    config: dict[str, Any],
) -> tuple[Callable[[dict[str, Any]], list[str]], dict[str, Any]]:
    glossary_config = config.get("glossary")
    if not glossary_config:
        return lambda _record: [], {"enabled": False}
    glossary_path = glossary_config["path"]
    max_entries = int(glossary_config.get("max_entries", 20))
    records = load_glossary_records(glossary_path)

    def select(record: dict[str, Any]) -> list[str]:
        return select_glossary_entries(
            str(record["text"]),
            records,
            max_entries=max_entries,
        )

    return select, {
        "enabled": True,
        "path": glossary_path,
        "candidates": len(records),
        "max_entries": max_entries,
        "match_mode": "substring",
    }


def build_query_plan(
    *,
    config: dict[str, Any],
    config_path: Path,
    dry_run: bool,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    Callable[[dict[str, Any]], list[dict[str, Any]]],
    Callable[[dict[str, Any]], list[str]],
    Callable[[dict[str, Any]], list[dict[str, Any]]],
    str,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    query_records = load_records(config["data"]["query_path"])
    query_limit = config.get("query_limit")
    if query_limit is not None:
        if isinstance(query_limit, bool) or int(query_limit) <= 0:
            raise ValueError("query_limit must be a positive integer")
        query_records = query_records[: int(query_limit)]
    if dry_run:
        max_queries = int(config.get("dry_run", {}).get("max_queries", len(query_records)))
        query_records = query_records[:max_queries]
    example_config = config["examples"]
    select_glossary, glossary_metadata = build_glossary_selector(config)
    select_rag, rag_metadata = build_rag_selector(config)
    if example_config["mode"] == "none":
        if int(example_config.get("k", -1)) != 0:
            raise ValueError("examples.mode=none requires k=0")
        metadata = {
            "mode": "none",
            "k": 0,
            "seed": int(example_config["seed"]),
            "example_ids": [],
        }
        return (
            [],
            query_records,
            lambda _record: [],
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )

    support_path = config["data"].get("support_path")
    if not isinstance(support_path, str) or not support_path:
        raise ValueError("non-zero-shot example modes require data.support_path")
    support_records = load_records(support_path)
    if example_config["mode"] == "fixed_random":
        examples = select_fixed_random_examples(
            support_records,
            k=int(example_config["k"]),
            seed=int(example_config["seed"]),
        )
        fixed_examples = [dict(record) for record in examples]
        metadata = {
            "mode": "fixed_random",
            "k": int(example_config["k"]),
            "seed": int(example_config["seed"]),
            "example_ids": [record["id"] for record in fixed_examples],
        }
        return (
            support_records,
            query_records,
            lambda _record: fixed_examples,
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )
    if example_config["mode"] == "knn_retrieval":
        selector, metadata = build_knn_selector(config=config, support_records=support_records)
        return (
            support_records,
            query_records,
            selector,
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )
    if example_config["mode"] == "knn_replay":
        selector, metadata = build_knn_replay_selector(config=config, support_records=support_records)
        return (
            support_records,
            query_records,
            selector,
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )
    raise ValueError(f"unsupported example selection mode {example_config['mode']!r}")


def run_dry(config: dict[str, Any], config_path: Path) -> int:
    (
        _,
        query_records,
        select_examples,
        select_glossary,
        select_rag,
        config_hash,
        example_metadata,
        glossary_metadata,
        rag_metadata,
    ) = build_query_plan(
        config=config, config_path=config_path, dry_run=True
    )
    entity_types = config["schema"]["entity_types"]
    generation = config["generation"]
    output_mode = str(config.get("parsing", {}).get("output_mode", "occurrence"))
    constrained_json_schema = bool(config.get("parsing", {}).get("constrained_json_schema", False))
    max_entities = int(config.get("parsing", {}).get("max_entities", 12))
    ner_only_envelope_policy = str(
        config.get("parsing", {}).get("ner_only_envelope_policy", "strict")
    )
    prompt_rows: list[dict[str, Any]] = []
    max_prompt_chars = 0
    for record in query_records:
        candidate_spans = generate_candidate_spans(record["text"]) if output_mode == "candidate_index" else None
        examples = select_examples(record)
        glossary_entries = select_glossary(record)
        rag_passages = select_rag(record)
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=entity_types,
            examples=examples,
            glossary_entries=glossary_entries,
            rag_passages=[passage["display"] for passage in rag_passages],
            include_relations=False,
            output_instruction=config["prompt"]["output_instruction"],
            output_mode=output_mode,
            reference_instruction=config["prompt"].get("reference_instruction"),
            occurrence_contract_version=config["prompt"].get("occurrence_contract_version"),
            anchored_contract_version=config["prompt"].get("anchored_contract_version"),
            candidate_spans=candidate_spans,
        )
        max_prompt_chars = max(max_prompt_chars, len(prompt))
        request_generation = generation
        if constrained_json_schema and output_mode == "char_bio":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_char_bio_response_format(
                sorted(entity_types), len(record["text"])
            )
        elif constrained_json_schema and output_mode == "anchored_span_index":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_anchored_span_index_response_format(
                sorted(entity_types), len(record["text"]), max_entities=max_entities
            )
        elif constrained_json_schema and output_mode == "span_index":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_span_index_response_format(
                sorted(entity_types), len(record["text"]), max_entities=max_entities
            )
        elif constrained_json_schema and output_mode == "occurrence":
            request_generation = dict(generation)
            if ner_only_envelope_policy == "entities_or_entities_relations_v2":
                request_generation["response_format"] = build_ner_occurrence_ner_only_response_format(
                    sorted(entity_types), max_entities=max_entities
                )
            else:
                request_generation["response_format"] = build_ner_occurrence_response_format(
                    sorted(entity_types), max_entities=max_entities
                )
        elif constrained_json_schema and output_mode == "candidate_index":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_candidate_index_response_format(
                sorted(entity_types), [item["id"] for item in candidate_spans or []], max_entities=max_entities
            )
        envelope = build_request_envelope(
            prompt=prompt,
            model=config["model"]["name"],
            generation=request_generation,
            run_id=config["run_id"],
            config_hash=config_hash,
        )
        prompt_rows.append(
            {
                "id": record["id"],
                "prompt_hash": prompt_hash(prompt),
                "request_hash": request_hash(envelope),
                "prompt_chars": len(prompt),
                "gold_entities": len(record["entities"]),
                "example_ids": [example["id"] for example in examples],
                "glossary_terms": glossary_entries,
                "rag_passage_ids": [passage["id"] for passage in rag_passages],
                "rag_passages": [passage["display"] for passage in rag_passages],
            }
        )

    outputs = config["outputs"]
    refuse_existing_outputs(outputs, ("dry_run_prompts", "manifest"))
    write_jsonl_atomic(Path(outputs["dry_run_prompts"]), prompt_rows)
    manifest = {
        "phase": "P3",
        "stage": "extraction_dry_run",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": config_hash,
        "dataset": config["data"]["dataset"],
        "query_path": config["data"]["query_path"],
        "support_path": config["data"].get("support_path"),
        "query_records": len(query_records),
        "example_selection": example_metadata,
        "glossary_selection": glossary_metadata,
        "rag_selection": rag_metadata,
        "model_calls": 0,
        "api_called": False,
        "model_weights_loaded": False,
        "gpu_device_present": gpu_visible(),
        "max_prompt_chars": max_prompt_chars,
        "dry_run_prompts": outputs["dry_run_prompts"],
        "dry_run_prompts_sha256": sha256_file(outputs["dry_run_prompts"]),
    }
    write_json_atomic(Path(outputs["manifest"]), manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


def run_execute(config: dict[str, Any], config_path: Path) -> int:
    execution = config.get("execution", {})
    validate_execution_gate(execution)
    if not gpu_visible():
        raise RuntimeError("GPU is not visible; refusing non-dry execution")

    (
        _,
        query_records,
        select_examples,
        select_glossary,
        select_rag,
        config_hash,
        example_metadata,
        glossary_metadata,
        rag_metadata,
    ) = build_query_plan(
        config=config, config_path=config_path, dry_run=False
    )
    entity_types = set(config["schema"]["entity_types"])
    generation = config["generation"]
    outputs = config["outputs"]
    refuse_existing_outputs(outputs, ("per_query", "summary"))
    cache_dir = Path(config["cache"]["dir"])
    base_url = config["model"]["base_url"]
    api_key = config["model"].get("api_key", "EMPTY")
    timeout_seconds = int(config["model"]["timeout_seconds"])
    retry_suffix = config["prompt"].get("retry_suffix", "只返回合法JSON")
    parsing = config.get("parsing", {})
    drop_invalid_entities = bool(parsing.get("drop_invalid_entities", False))
    output_mode = str(parsing.get("output_mode", "occurrence"))
    constrained_json_schema = bool(parsing.get("constrained_json_schema", False))
    max_entities = int(parsing.get("max_entities", 12))
    ner_only_envelope_policy = str(parsing.get("ner_only_envelope_policy", "strict"))

    rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    started = time.monotonic()
    for record in query_records:
        record_started = time.monotonic()
        step_started = time.monotonic()
        examples = select_examples(record)
        example_selection_ms = elapsed_ms(step_started)
        step_started = time.monotonic()
        glossary_entries = select_glossary(record)
        glossary_selection_ms = elapsed_ms(step_started)
        step_started = time.monotonic()
        rag_passages = select_rag(record)
        rag_selection_ms = elapsed_ms(step_started)
        candidate_spans = generate_candidate_spans(record["text"]) if output_mode == "candidate_index" else None
        step_started = time.monotonic()
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=config["schema"]["entity_types"],
            examples=examples,
            glossary_entries=glossary_entries,
            rag_passages=[passage["display"] for passage in rag_passages],
            include_relations=False,
            output_instruction=config["prompt"]["output_instruction"],
            output_mode=output_mode,
            reference_instruction=config["prompt"].get("reference_instruction"),
            occurrence_contract_version=config["prompt"].get("occurrence_contract_version"),
            anchored_contract_version=config["prompt"].get("anchored_contract_version"),
            candidate_spans=candidate_spans,
        )
        prompt_build_ms = elapsed_ms(step_started)
        request_generation = generation
        if constrained_json_schema and output_mode == "char_bio":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_char_bio_response_format(
                sorted(entity_types), len(record["text"])
            )
        elif constrained_json_schema and output_mode == "anchored_span_index":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_anchored_span_index_response_format(
                sorted(entity_types), len(record["text"]), max_entities=max_entities
            )
        elif constrained_json_schema and output_mode == "span_index":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_span_index_response_format(
                sorted(entity_types), len(record["text"]), max_entities=max_entities
            )
        elif constrained_json_schema and output_mode == "occurrence":
            request_generation = dict(generation)
            if ner_only_envelope_policy == "entities_or_entities_relations_v2":
                request_generation["response_format"] = build_ner_occurrence_ner_only_response_format(
                    sorted(entity_types), max_entities=max_entities
                )
            else:
                request_generation["response_format"] = build_ner_occurrence_response_format(
                    sorted(entity_types), max_entities=max_entities
                )
        elif constrained_json_schema and output_mode == "candidate_index":
            request_generation = dict(generation)
            request_generation["response_format"] = build_ner_candidate_index_response_format(
                sorted(entity_types), [item["id"] for item in candidate_spans or []], max_entities=max_entities
            )
        attempts: list[dict[str, Any]] = []
        pred: dict[str, Any] | None = None
        parse_error: str | None = None
        raw_output_hash = ""
        total_latency = 0.0
        sanitization_flags: list[dict[str, Any]] = []
        attempt_prompt = prompt
        for attempt_number in (1, 2):
            envelope = build_request_envelope(
                prompt=attempt_prompt,
                model=config["model"]["name"],
                generation=request_generation,
                run_id=config["run_id"],
                config_hash=config_hash,
            )
            result = chat_with_cache(
                envelope=envelope,
                cache_dir=cache_dir,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                api_key=api_key,
            )
            total_latency += result.latency_ms
            raw_output_hash = result.raw_output_hash
            try:
                pred = parse_extraction_output(
                    result.content,
                    record_id=record["id"],
                    text=record["text"],
                    entity_types=entity_types,
                    drop_invalid_entities=drop_invalid_entities,
                    sanitization_flags=sanitization_flags,
                    output_mode=output_mode,
                    ner_only_envelope_policy=ner_only_envelope_policy,
                    candidate_spans=candidate_spans,
                    max_entities=max_entities,
                )
                parse_error = None
            except Exception as exc:  # preserve exact parser message in row logs
                parse_error = f"{type(exc).__name__}: {exc}"
            attempts.append(
                {
                    "attempt": attempt_number,
                    "request_hash": result.request_hash,
                    "raw_output_hash": result.raw_output_hash,
                    "cache_hit": result.cache_hit,
                    "latency_ms": round(result.latency_ms, 3),
                    "parse_error": parse_error,
                }
            )
            if pred is not None:
                break
            if attempt_number == 1 and parse_error is not None:
                attempt_prompt = build_error_retry_prompt(
                    base_prompt=prompt,
                    parse_error=parse_error,
                    output_mode=output_mode,
                    retry_suffix=retry_suffix,
                )
        if pred is None:
            pred = empty_prediction(record)
        invalid_unit_drops = sum(
            1
            for flag in sanitization_flags
            if flag.get("kind") == "ENTITY_DROPPED_INVALID_UNIT"
        )
        overlap_drops = sum(
            1
            for flag in sanitization_flags
            if flag.get("kind") == "ENTITY_DROPPED_OVERLAP"
        )
        accepted_entity_count = len(pred.get("entities", []))
        # Every entity-level drop is logged before a prediction is emitted.
        # This is an audit count, not a repair: malformed-envelope rows have
        # zero observable candidates and remain parser failures.
        raw_candidate_entity_count = (
            accepted_entity_count + invalid_unit_drops + overlap_drops
            if parse_error is None
            else None
        )
        predictions.append(pred)
        rows.append(
            {
                "id": record["id"],
                "dataset": config["data"]["dataset"],
                "config": config["config_name"],
                "k": int(config["examples"]["k"]),
                "seed": int(config["examples"]["seed"]),
                "gold": record,
                "pred_raw": pred,
                "pred_verified": None,
                "latency_ms": round(total_latency, 3),
                "llm_latency_ms": round(total_latency, 3),
                "example_selection_ms": example_selection_ms,
                "glossary_selection_ms": glossary_selection_ms,
                "rag_selection_ms": rag_selection_ms,
                "prompt_build_ms": prompt_build_ms,
                "total_record_ms": elapsed_ms(record_started),
                "parse_failure": parse_error is not None,
                "raw_llm_output_hash": raw_output_hash,
                "prompt_hash": prompt_hash(prompt),
                "example_ids": [example["id"] for example in examples],
                "glossary_terms": glossary_entries,
                "rag_passage_ids": [passage["id"] for passage in rag_passages],
                "rag_passages": [passage["display"] for passage in rag_passages],
                "attempts": attempts,
                "sanitization_flags": sanitization_flags,
                "accepted_entity_count": accepted_entity_count,
                "invalid_unit_drops": invalid_unit_drops,
                "overlap_drops": overlap_drops,
                "raw_candidate_entity_count": raw_candidate_entity_count,
            }
        )

    write_jsonl_atomic(Path(outputs["per_query"]), rows)
    counts = entity_micro_counts(query_records, predictions)
    parse_failures = sum(1 for row in rows if row["parse_failure"])
    timing_fields = [
        "example_selection_ms",
        "glossary_selection_ms",
        "rag_selection_ms",
        "prompt_build_ms",
        "llm_latency_ms",
        "total_record_ms",
    ]
    timing_totals_ms = {
        field: round(sum(float(row[field]) for row in rows), 3) for field in timing_fields
    }
    timing_means_ms = {
        field: round(timing_totals_ms[field] / len(rows), 3) if rows else 0.0
        for field in timing_fields
    }
    parse_failure_rate = parse_failures / len(rows) if rows else 0.0
    protocol = config.get("protocol", {})
    parser_failure_ceiling = protocol.get("parser_failure_ceiling")
    if parser_failure_ceiling is not None:
        parser_failure_ceiling = float(parser_failure_ceiling)
        if not 0.0 <= parser_failure_ceiling <= 1.0:
            raise ValueError("protocol.parser_failure_ceiling must be between 0 and 1")
    summary = {
        "phase": "P3",
        "stage": "extraction_execution",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_hash,
        "query_records": len(query_records),
        "example_selection": example_metadata,
        "glossary_selection": glossary_metadata,
        "rag_selection": rag_metadata,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "timing_totals_ms": timing_totals_ms,
        "timing_means_ms": timing_means_ms,
        "parse_failures": parse_failures,
        "parse_failure_rate": parse_failure_rate,
        "parser_failure_ceiling": parser_failure_ceiling,
        "parser_failure_ceiling_passed": (
            parser_failure_ceiling is None or parse_failure_rate <= parser_failure_ceiling
        ),
        "sanitized_unit_events": sum(len(row["sanitization_flags"]) for row in rows),
        "sanitization_counts": {
            "invalid_unit_drops": sum(int(row["invalid_unit_drops"]) for row in rows),
            "overlap_drops": sum(int(row["overlap_drops"]) for row in rows),
            "all_unit_events": sum(len(row["sanitization_flags"]) for row in rows),
        },
        "entity_audit_counts": {
            "accepted_entities": sum(int(row["accepted_entity_count"]) for row in rows),
            "raw_candidate_entities_observed": sum(
                int(row["raw_candidate_entity_count"] or 0) for row in rows
            ),
            "rows_with_unknown_raw_candidates": sum(
                1 for row in rows if row["raw_candidate_entity_count"] is None
            ),
        },
        "entity_micro": counts.report(),
        "per_query": outputs["per_query"],
        "per_query_sha256": sha256_file(outputs["per_query"]),
    }
    write_json_atomic(Path(outputs["summary"]), summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["parser_failure_ceiling_passed"] else 2


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    if args.dry_run:
        return run_dry(config, config_path)
    return run_execute(config, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
