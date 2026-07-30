#!/usr/bin/env python3
"""Run the gated relation-only Stage R over recorded Stage N entity rows.

This runner has no dry-run mode. Unauthorized execution fails before reading
any per-query or support data, and model calls additionally require a GPU.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (  # noqa: E402
    build_request_envelope,
    entity_micro_counts,
    prompt_hash,
)
from equipment_ie.full_ie import (  # noqa: E402
    build_stage_r_prompt,
    build_stage_r_retry_prompt,
    parse_stage_r_output,
    relation_evaluation_report,
    stage_r_skip_reason,
    validate_approved_relation_matrix,
)
from equipment_ie.llm_labeling import chat_with_cache  # noqa: E402
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record  # noqa: E402


STAGE_R_GATE_PHASES = {
    "FULL_IE_DOMAIN_DEV_SANITY_APPROVED": "FULL_IE_DOMAIN_DEV_SANITY",
    "FULL_IE_DOMAIN_FINAL_BATCH_APPROVED": "FULL_IE_DOMAIN_FINAL_BATCH",
}
FIXED_OUTPUT_INSTRUCTION = "只返回JSON,不要任何解释,不要markdown代码块"
FIXED_RETRY_SUFFIX = "只返回合法JSON"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
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


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def validate_execution_gate(execution: dict[str, Any]) -> None:
    if execution.get("authorized") is not True:
        raise RuntimeError("Stage R execution.authorized must be true")
    if execution.get("model_calls_allowed") is not True:
        raise RuntimeError("Stage R execution.model_calls_allowed must be true")
    human_gate = execution.get("human_gate")
    required_phase = STAGE_R_GATE_PHASES.get(human_gate)
    if required_phase is None:
        raise RuntimeError(
            f"Stage R human_gate must be one of {sorted(STAGE_R_GATE_PHASES)}"
        )
    if execution.get("phase") != required_phase:
        raise RuntimeError(f"{human_gate} requires execution.phase={required_phase}")


def load_per_query_rows(path: str, *, expected_rows: int | None) -> list[dict[str, Any]]:
    rows = [dict(row) for row in iter_jsonl(Path(path), validate=False)]
    if expected_rows is not None and len(rows) != int(expected_rows):
        raise ValueError(f"{path}: expected {expected_rows} rows, found {len(rows)}")
    seen: set[str] = set()
    for row in rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("Stage N row id must be a non-empty string")
        if record_id in seen:
            raise ValueError(f"duplicate Stage N row id {record_id}")
        seen.add(record_id)
    return rows


def load_support_by_id(path: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for record in iter_jsonl(Path(path)):
        if record["id"] in records:
            raise ValueError(f"duplicate support id {record['id']}")
        records[record["id"]] = record
    return records


def stage_n_record_from_row(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("pred_entities_stage_n", row.get("pred_raw"))
    if isinstance(value, list):
        gold = row.get("gold")
        if not isinstance(gold, dict):
            raise ValueError(f"row {row.get('id')}: gold is required with entity-list Stage N input")
        value = {
            "id": row["id"],
            "text": gold["text"],
            "entities": value,
            "relations": [],
        }
    if not isinstance(value, dict):
        raise ValueError(f"row {row.get('id')}: Stage N prediction must be an object or entity list")
    record = dict(value)
    validate_record(record)
    if record["id"] != row.get("id"):
        raise ValueError(f"row {row.get('id')}: Stage N record id mismatch")
    if record["relations"]:
        raise ValueError(f"row {row.get('id')}: Stage N record must not contain relations")
    return record


def build_stage_r_row_plan(
    *,
    row: dict[str, Any],
    support_by_id: dict[str, dict[str, Any]],
    relation_types: dict[str, dict[str, Any]],
    output_instruction: str,
) -> dict[str, Any]:
    """Resolve one replay-safe Stage R prompt plan from recorded Stage N metadata."""

    stage_n_record = stage_n_record_from_row(row)
    raw_example_ids = row.get("example_ids")
    if not isinstance(raw_example_ids, list) or any(
        not isinstance(value, str) for value in raw_example_ids
    ):
        raise ValueError(f"row {row.get('id')}: example_ids must be a string list")
    expected_k = int(row.get("k", -1))
    if len(raw_example_ids) != expected_k:
        raise ValueError(
            f"row {row.get('id')}: recorded example count {len(raw_example_ids)} != k={expected_k}"
        )
    if len(set(raw_example_ids)) != len(raw_example_ids):
        raise ValueError(f"row {row.get('id')}: example_ids must not contain duplicates")
    missing = [example_id for example_id in raw_example_ids if example_id not in support_by_id]
    if missing:
        raise ValueError(f"row {row.get('id')}: missing support examples {missing}")
    examples = [support_by_id[example_id] for example_id in raw_example_ids]
    glossary_entries = row.get("glossary_terms", [])
    rag_passages = row.get("rag_passages", [])
    if not isinstance(glossary_entries, list) or any(
        not isinstance(value, str) for value in glossary_entries
    ):
        raise ValueError(f"row {row.get('id')}: glossary_terms must be a string list")
    if not isinstance(rag_passages, list) or any(not isinstance(value, str) for value in rag_passages):
        raise ValueError(f"row {row.get('id')}: rag_passages must be a string list")
    rag_passage_ids = row.get("rag_passage_ids", [])
    if not isinstance(rag_passage_ids, list) or any(
        not isinstance(value, str) for value in rag_passage_ids
    ):
        raise ValueError(f"row {row.get('id')}: rag_passage_ids must be a string list")
    if len(rag_passage_ids) != len(rag_passages):
        raise ValueError(f"row {row.get('id')}: RAG passage ids/text counts differ")
    skip_reason = stage_r_skip_reason(stage_n_record, relation_types)
    prompt = None
    if skip_reason is None:
        prompt = build_stage_r_prompt(
            stage_n_record=stage_n_record,
            relation_types=relation_types,
            examples=examples,
            glossary_entries=glossary_entries,
            rag_passages=rag_passages,
            output_instruction=output_instruction,
        )
    return {
        "stage_n_record": stage_n_record,
        "example_ids": list(raw_example_ids),
        "examples": examples,
        "glossary_entries": list(glossary_entries),
        "rag_passages": list(rag_passages),
        "rag_passage_ids": list(rag_passage_ids),
        "skip_reason": skip_reason,
        "prompt": prompt,
    }


def validate_source_resource_contract(config_name: str, plan: dict[str, Any]) -> None:
    if config_name in {"A", "B"} and plan["glossary_entries"]:
        raise ValueError(f"{config_name} Stage R may not inject glossary entries")
    if config_name != "D" and plan["rag_passages"]:
        raise ValueError(f"{config_name} Stage R may not inject RAG passages")


def run_execute(config: dict[str, Any], config_path: Path) -> int:
    # Gate before any input path is opened. F1 implementation approval is not a model gate.
    validate_execution_gate(config.get("execution", {}))
    if not gpu_visible():
        raise RuntimeError("GPU is not visible; refusing Stage R model execution")
    if config.get("data", {}).get("dataset") != "domain":
        raise ValueError("Stage R is defined only for the domain dataset")
    config_name = config.get("config_name")
    if config_name not in {"A", "B", "C", "D"}:
        raise ValueError("Stage R source config must be one of A/B/C/D")
    if config.get("replay", {}).get("reuse_stage_n_metadata") is not True:
        raise ValueError("Stage R requires replay.reuse_stage_n_metadata=true")

    input_config = config["input"]
    rows = load_per_query_rows(
        input_config["stage_n_per_query_path"],
        expected_rows=input_config.get("expected_rows"),
    )
    support_by_id = load_support_by_id(input_config["support_path"])
    relation_types = validate_approved_relation_matrix(
        config["schema"]["relation_types"]
    )
    prompt_config = config["prompt"]
    output_instruction = prompt_config.get("output_instruction", FIXED_OUTPUT_INSTRUCTION)
    retry_suffix = prompt_config.get("retry_suffix", FIXED_RETRY_SUFFIX)
    if output_instruction != FIXED_OUTPUT_INSTRUCTION:
        raise ValueError("Stage R output instruction differs from the fixed contract")
    if retry_suffix != FIXED_RETRY_SUFFIX:
        raise ValueError("Stage R retry suffix differs from the fixed parsing ladder")
    parsing = config.get("parsing", {})
    drop_invalid_relations = bool(parsing.get("drop_invalid_relations", False))
    generation = config["generation"]
    config_hash = sha256_file(config_path)
    cache_dir = Path(config["cache"]["dir"])
    base_url = config["model"]["base_url"]
    api_key = config["model"].get("api_key", "EMPTY")
    timeout_seconds = int(config["model"]["timeout_seconds"])

    output_rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    gold_records: list[dict[str, Any]] = []
    model_requests = 0
    deterministic_skips = 0
    started = time.monotonic()
    for row in rows:
        if row.get("dataset") != "domain" or row.get("config") != config_name:
            raise ValueError(f"row {row.get('id')}: dataset/config mismatch")
        gold = row.get("gold")
        if not isinstance(gold, dict):
            raise ValueError(f"row {row.get('id')}: gold must be an object")
        validate_record(gold)
        plan = build_stage_r_row_plan(
            row=row,
            support_by_id=support_by_id,
            relation_types=relation_types,
            output_instruction=output_instruction,
        )
        validate_source_resource_contract(str(config_name), plan)
        source = plan["stage_n_record"]
        prompt = plan["prompt"]
        attempts: list[dict[str, Any]] = []
        sanitization_flags: list[dict[str, Any]] = []
        total_latency_ms = 0.0
        raw_output_hash = ""
        parse_error: str | None = None
        prediction: dict[str, Any] | None = None
        if plan["skip_reason"] is not None:
            deterministic_skips += 1
            prediction = {
                "id": source["id"],
                "text": source["text"],
                "entities": [dict(entity) for entity in source["entities"]],
                "relations": [],
            }
        else:
            attempt_prompt = str(prompt)
            for attempt_number in (1, 2):
                envelope = build_request_envelope(
                    prompt=attempt_prompt,
                    model=config["model"]["name"],
                    generation=generation,
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
                model_requests += 1
                total_latency_ms += result.latency_ms
                raw_output_hash = result.raw_output_hash
                try:
                    prediction = parse_stage_r_output(
                        result.content,
                        stage_n_record=source,
                        relation_types=relation_types,
                        drop_invalid_relations=drop_invalid_relations,
                        sanitization_flags=sanitization_flags,
                    )
                    parse_error = None
                except Exception as exc:
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
                if prediction is not None:
                    break
                if attempt_number == 1 and parse_error is not None:
                    attempt_prompt = build_stage_r_retry_prompt(
                        base_prompt=str(prompt),
                        parse_error=parse_error,
                        retry_suffix=retry_suffix,
                    )
        if prediction is None:
            prediction = {
                "id": source["id"],
                "text": source["text"],
                "entities": [dict(entity) for entity in source["entities"]],
                "relations": [],
            }
        predictions.append(prediction)
        gold_records.append(gold)
        output_rows.append(
            {
                "id": row["id"],
                "dataset": "domain",
                "config": config_name,
                "k": int(row["k"]),
                "seed": int(row["seed"]),
                "gold": gold,
                "pred_entities_stage_n": [dict(entity) for entity in source["entities"]],
                "pred_relations_stage_r": [dict(relation) for relation in prediction["relations"]],
                "pred_raw": prediction,
                "pred_verified": None,
                "ner_prompt_hash": row.get("prompt_hash"),
                "relation_prompt_hash": prompt_hash(prompt) if prompt is not None else None,
                "verifier_prompt_hashes": [],
                "raw_ner_output_hash": row.get("raw_llm_output_hash"),
                "raw_relation_output_hash": raw_output_hash or None,
                "example_ids": plan["example_ids"],
                "glossary_terms": plan["glossary_entries"],
                "rag_passage_ids": plan["rag_passage_ids"],
                "rag_passages": plan["rag_passages"],
                "parse_failure_ner": bool(row.get("parse_failure", False)),
                "parse_failure_relation": parse_error is not None,
                "relation_skip_reason": plan["skip_reason"],
                "sanitization_flags": list(row.get("sanitization_flags", []))
                + sanitization_flags,
                "verifier_decisions": [],
                "latency_ner_ms": float(row.get("latency_ms", 0.0)),
                "latency_relation_ms": round(total_latency_ms, 3),
                "latency_verifier_ms": 0.0,
                "relation_attempts": attempts,
            }
        )

    outputs = config["outputs"]
    write_jsonl_atomic(Path(outputs["per_query"]), output_rows)
    entity_report = entity_micro_counts(gold_records, predictions).report()
    relation_report = relation_evaluation_report(
        gold_records,
        predictions,
        relation_types=tuple(relation_types),
    )
    summary = {
        "phase": "FULL_IE",
        "stage": "stage_r_execution",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_hash,
        "source_stage_n_path": input_config["stage_n_per_query_path"],
        "source_stage_n_sha256": sha256_file(input_config["stage_n_per_query_path"]),
        "rows": len(output_rows),
        "model_requests": model_requests,
        "deterministic_skips": deterministic_skips,
        "parse_failures_relation": sum(row["parse_failure_relation"] for row in output_rows),
        "entity_micro": entity_report,
        "relation": relation_report,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "per_query": outputs["per_query"],
        "per_query_sha256": sha256_file(outputs["per_query"]),
    }
    write_json_atomic(Path(outputs["summary"]), summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    return run_execute(config, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
