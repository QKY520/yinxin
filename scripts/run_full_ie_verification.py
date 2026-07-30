#!/usr/bin/env python3
"""Run future gated entity-and-relation atomic verification for E/E-prime.

This runner intentionally has no dry-run mode. It rejects the F1 implementation
gate and every other non-model gate before opening a per-query artifact.
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
    apply_atomic_verifier_decisions,
    build_full_ie_entity_verification_prompt,
    build_relation_verification_prompt,
    parse_atomic_verifier_answer,
    relation_evaluation_report,
    validate_approved_relation_matrix,
)
from equipment_ie.llm_labeling import chat_with_cache  # noqa: E402
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record  # noqa: E402


VERIFICATION_GATE_PHASES = {
    "FULL_IE_DOMAIN_DEV_SANITY_APPROVED": "FULL_IE_DOMAIN_DEV_SANITY",
    "FULL_IE_DOMAIN_FINAL_BATCH_APPROVED": "FULL_IE_DOMAIN_FINAL_BATCH",
}
SOURCE_CONFIG = {"E": "D", "E-prime": "C"}
FIXED_OUTPUT_INSTRUCTION = "只回答yes或no"


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
        raise RuntimeError("full-IE verification execution.authorized must be true")
    if execution.get("model_calls_allowed") is not True:
        raise RuntimeError("full-IE verification execution.model_calls_allowed must be true")
    human_gate = execution.get("human_gate")
    required_phase = VERIFICATION_GATE_PHASES.get(human_gate)
    if required_phase is None:
        raise RuntimeError(
            "full-IE verification human_gate must be one of "
            f"{sorted(VERIFICATION_GATE_PHASES)}"
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
            raise ValueError("full-IE row id must be a non-empty string")
        if record_id in seen:
            raise ValueError(f"duplicate full-IE row id {record_id}")
        seen.add(record_id)
        pred_raw = row.get("pred_raw")
        if not isinstance(pred_raw, dict):
            raise ValueError(f"row {record_id}: pred_raw must be an object")
        validate_record(pred_raw)
        if pred_raw["id"] != record_id:
            raise ValueError(f"row {record_id}: pred_raw id mismatch")
    return rows


def normalize_entity_definitions(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or not value:
        raise ValueError("schema.entity_types must be a non-empty object")
    definitions: dict[str, str] = {}
    for entity_type, raw_definition in value.items():
        if isinstance(raw_definition, dict):
            raw_definition = raw_definition.get("definition")
        if (
            not isinstance(entity_type, str)
            or not entity_type
            or not isinstance(raw_definition, str)
            or not raw_definition.strip()
        ):
            raise ValueError("each entity type requires a non-empty definition")
        definitions[entity_type] = raw_definition.strip()
    return definitions


def select_evidence(
    row: dict[str, Any],
    *,
    config_name: str,
    evidence_config: dict[str, Any],
) -> list[str]:
    mode = evidence_config.get("mode")
    if config_name == "E-prime":
        if mode != "source_text_only":
            raise ValueError("E-prime requires evidence.mode=source_text_only")
        return []
    if mode != "reuse_stage_r_rag_passages":
        raise ValueError("E requires evidence.mode=reuse_stage_r_rag_passages")
    raw_passages = row.get("rag_passages", [])
    if not isinstance(raw_passages, list) or any(
        not isinstance(passage, str) for passage in raw_passages
    ):
        raise ValueError(f"row {row.get('id')}: rag_passages must be a string list")
    max_passages = int(evidence_config.get("max_passages", 3))
    if max_passages != 3:
        raise ValueError("E requires evidence.max_passages=3")
    return list(raw_passages[:max_passages])


def _run_verifier_unit(
    *,
    row_id: str,
    unit_kind: str,
    unit_index: int,
    prompt: str,
    evidence_mode: str,
    evidence_count: int,
    prompt_version: str,
    model: dict[str, Any],
    generation: dict[str, Any],
    run_id: str,
    config_hash: str,
    cache_dir: Path,
) -> dict[str, Any]:
    envelope = build_request_envelope(
        prompt=prompt,
        model=model["name"],
        generation=generation,
        run_id=run_id,
        config_hash=config_hash,
    )
    result = chat_with_cache(
        envelope=envelope,
        cache_dir=cache_dir,
        base_url=model["base_url"],
        timeout_seconds=int(model["timeout_seconds"]),
        api_key=model.get("api_key", "EMPTY"),
    )
    decision = parse_atomic_verifier_answer(result.content)
    return {
        "unit_id": f"{row_id}::{unit_kind}::{unit_index}",
        "unit_kind": unit_kind,
        "unit_index": unit_index,
        f"{unit_kind}_index": unit_index,
        "decision": decision,
        "valid_answer": decision in {"yes", "no"},
        "raw_output_hash": result.raw_output_hash,
        "request_hash": result.request_hash,
        "cache_hit": result.cache_hit,
        "latency_ms": round(result.latency_ms, 3),
        "prompt_hash": prompt_hash(prompt),
        "evidence_mode": evidence_mode,
        "evidence_count": evidence_count,
        "prompt_version": prompt_version,
    }


def run_execute(config: dict[str, Any], config_path: Path) -> int:
    # This gate is deliberately checked before any per-query artifact is opened.
    validate_execution_gate(config.get("execution", {}))
    if not gpu_visible():
        raise RuntimeError("GPU is not visible; refusing full-IE verifier model execution")

    config_name = config.get("config_name")
    source_config = SOURCE_CONFIG.get(config_name)
    if source_config is None:
        raise ValueError("config_name must be E or E-prime")
    if config.get("source_config") != source_config:
        raise ValueError(f"{config_name} must verify source_config={source_config}")
    if config.get("data", {}).get("dataset") != "domain":
        raise ValueError("relation-aware verification is defined only for domain")

    input_config = config["input"]
    rows = load_per_query_rows(
        input_config["per_query_path"],
        expected_rows=input_config.get("expected_rows"),
    )
    schema = config["schema"]
    entity_definitions = normalize_entity_definitions(schema["entity_types"])
    relation_types = validate_approved_relation_matrix(schema["relation_types"])
    evidence_config = config["evidence"]
    prompt_config = config["prompt"]
    output_instruction = prompt_config.get("output_instruction", FIXED_OUTPUT_INSTRUCTION)
    if output_instruction != FIXED_OUTPUT_INSTRUCTION:
        raise ValueError("verifier output instruction differs from the fixed contract")
    prompt_version = prompt_config.get("version", "full_ie_atomic_source_first_v1")
    model = config["model"]
    generation = config["generation"]
    config_hash = sha256_file(config_path)
    cache_dir = Path(config["cache"]["dir"])

    output_rows: list[dict[str, Any]] = []
    gold_records: list[dict[str, Any]] = []
    raw_records: list[dict[str, Any]] = []
    verified_records: list[dict[str, Any]] = []
    total_units = 0
    invalid_units = 0
    valid_no_entities = 0
    valid_no_relations = 0
    cascade_dropped_relations = 0
    started = time.monotonic()
    for row in rows:
        if row.get("dataset") != "domain" or row.get("config") != source_config:
            raise ValueError(f"row {row.get('id')}: dataset/source config mismatch")
        gold = row.get("gold")
        if not isinstance(gold, dict):
            raise ValueError(f"row {row.get('id')}: gold must be an object")
        validate_record(gold)
        pred_raw = row["pred_raw"]
        evidence = select_evidence(
            row,
            config_name=str(config_name),
            evidence_config=evidence_config,
        )
        decisions: list[dict[str, Any]] = []
        for entity_index, entity in enumerate(pred_raw["entities"]):
            definition = entity_definitions.get(entity["type"])
            if definition is None:
                raise ValueError(
                    f"row {row['id']}: unsupported predicted entity type {entity['type']!r}"
                )
            prompt = build_full_ie_entity_verification_prompt(
                text=pred_raw["text"],
                entity=entity,
                entity_type_definition=definition,
                evidence_passages=evidence,
                output_instruction=output_instruction,
            )
            decisions.append(
                _run_verifier_unit(
                    row_id=row["id"],
                    unit_kind="entity",
                    unit_index=entity_index,
                    prompt=prompt,
                    evidence_mode=evidence_config["mode"],
                    evidence_count=len(evidence),
                    prompt_version=prompt_version,
                    model=model,
                    generation=generation,
                    run_id=config["run_id"],
                    config_hash=config_hash,
                    cache_dir=cache_dir,
                )
            )
        for relation_index, _relation in enumerate(pred_raw["relations"]):
            prompt = build_relation_verification_prompt(
                record=pred_raw,
                relation_index=relation_index,
                relation_types=relation_types,
                evidence_passages=evidence,
                output_instruction=output_instruction,
            )
            decisions.append(
                _run_verifier_unit(
                    row_id=row["id"],
                    unit_kind="relation",
                    unit_index=relation_index,
                    prompt=prompt,
                    evidence_mode=evidence_config["mode"],
                    evidence_count=len(evidence),
                    prompt_version=prompt_version,
                    model=model,
                    generation=generation,
                    run_id=config["run_id"],
                    config_hash=config_hash,
                    cache_dir=cache_dir,
                )
            )

        application = apply_atomic_verifier_decisions(pred_raw, decisions=decisions)
        total_units += len(decisions)
        invalid_units += application.invalid_decisions
        valid_no_entities += len(application.dropped_entity_indices)
        valid_no_relations += len(application.dropped_relation_indices)
        cascade_dropped_relations += len(application.cascade_dropped_relation_indices)
        verifier_latency = sum(float(decision["latency_ms"]) for decision in decisions)
        output_row = dict(row)
        output_row.update(
            {
                "config": config_name,
                "source_config": source_config,
                "pred_verified": application.record,
                "verifier_decisions": decisions,
                "verifier_prompt_hashes": [
                    decision["prompt_hash"] for decision in decisions
                ],
                "latency_verifier_ms": round(verifier_latency, 3),
                "verifier_cascade_dropped_relation_indices": list(
                    application.cascade_dropped_relation_indices
                ),
            }
        )
        output_rows.append(output_row)
        gold_records.append(gold)
        raw_records.append(pred_raw)
        verified_records.append(application.record)

    outputs = config["outputs"]
    write_jsonl_atomic(Path(outputs["per_query"]), output_rows)
    summary = {
        "phase": "FULL_IE",
        "stage": "atomic_entity_relation_verification",
        "run_id": config["run_id"],
        "config": config_name,
        "source_config": source_config,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_hash,
        "input_per_query_path": input_config["per_query_path"],
        "input_per_query_sha256": sha256_file(input_config["per_query_path"]),
        "rows": len(output_rows),
        "atomic_units": total_units,
        "invalid_units_kept": invalid_units,
        "valid_no_entities": valid_no_entities,
        "valid_no_relations": valid_no_relations,
        "cascade_dropped_relations": cascade_dropped_relations,
        "raw_entity_micro": entity_micro_counts(gold_records, raw_records).report(),
        "verified_entity_micro": entity_micro_counts(
            gold_records, verified_records
        ).report(),
        "raw_relation": relation_evaluation_report(
            gold_records,
            raw_records,
            relation_types=tuple(relation_types),
        ),
        "verified_relation": relation_evaluation_report(
            gold_records,
            verified_records,
            relation_types=tuple(relation_types),
        ),
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
