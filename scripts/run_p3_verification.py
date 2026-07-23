#!/usr/bin/env python3
"""Prepare P3 self-verification prompts from extraction per-query rows."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import build_request_envelope, prompt_hash
from equipment_ie.llm_labeling import chat_with_cache, request_hash
from equipment_ie.schema import iter_jsonl, sha256_file


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


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def parse_verifier_answer(content: str) -> str:
    normalized = content.strip().lower()
    if normalized in {"yes", "yes.", "是", "是。"}:
        return "yes"
    if normalized in {"no", "no.", "否", "否。"}:
        return "no"
    return "invalid"


def load_per_query_rows(path: str, *, expected_rows: int | None) -> list[dict[str, Any]]:
    rows = [dict(row) for row in iter_jsonl(Path(path), validate=False)]
    if expected_rows is not None and len(rows) != expected_rows:
        raise ValueError(f"{path}: expected {expected_rows} rows, found {len(rows)}")
    return rows


def build_entity_verification_prompt(
    *,
    text: str,
    entity: dict[str, Any],
    evidence_passages: list[str],
    output_instruction: str,
) -> str:
    evidence_block = "\n".join(f"- {passage}" for passage in evidence_passages) if evidence_passages else "无"
    return "\n\n".join(
        [
            "任务：判断候选实体是否被原文支持。只判断给定实体，不要新增实体。",
            f"原文：{text}",
            f"候选实体：{entity['span']}（{entity['type']}）",
            f"参考资料：\n{evidence_block}",
            "判断标准：如果该 span 在原文中存在，且类型与上下文一致，回答 yes；否则回答 no。",
            output_instruction,
        ]
    )


def select_evidence(row: dict[str, Any], evidence_config: dict[str, Any]) -> list[str]:
    mode = evidence_config.get("mode", "source_text_only")
    if mode == "source_text_only":
        return []
    if mode == "use_extraction_rag_passages":
        passages = row.get("rag_passages", [])
        if not isinstance(passages, list):
            return []
        max_passages = int(evidence_config.get("max_passages", 3))
        return [str(passage) for passage in passages[:max_passages]]
    raise ValueError(f"unsupported verification evidence mode {mode!r}")


def run_dry(config: dict[str, Any], config_path: Path) -> int:
    input_config = config["input"]
    rows = load_per_query_rows(
        input_config["per_query_path"],
        expected_rows=input_config.get("expected_rows"),
    )
    evidence_config = config.get("evidence", {"mode": "source_text_only"})
    output_instruction = config["prompt"].get("output_instruction", "只回答yes或no")
    generation = config["generation"]
    config_hash = sha256_file(config_path)

    prompt_rows: list[dict[str, Any]] = []
    max_prompt_chars = 0
    for row in rows:
        pred_raw = row.get("pred_raw")
        if not isinstance(pred_raw, dict):
            raise ValueError(f"row {row.get('id')}: pred_raw must be an object")
        entities = pred_raw.get("entities", [])
        if not isinstance(entities, list):
            raise ValueError(f"row {row.get('id')}: pred_raw.entities must be a list")
        evidence_passages = select_evidence(row, evidence_config)
        for index, entity in enumerate(entities):
            if not isinstance(entity, dict):
                raise ValueError(f"row {row.get('id')}: entity {index} must be an object")
            for key in ("span", "type", "start", "end"):
                if key not in entity:
                    raise ValueError(f"row {row.get('id')}: entity {index} missing {key}")
            prompt = build_entity_verification_prompt(
                text=str(pred_raw["text"]),
                entity=entity,
                evidence_passages=evidence_passages,
                output_instruction=output_instruction,
            )
            max_prompt_chars = max(max_prompt_chars, len(prompt))
            envelope = build_request_envelope(
                prompt=prompt,
                model=config["model"]["name"],
                generation=generation,
                run_id=config["run_id"],
                config_hash=config_hash,
            )
            prompt_rows.append(
                {
                    "id": row["id"],
                    "unit_id": f"{row['id']}::entity::{index}",
                    "unit_kind": "entity",
                    "span": entity["span"],
                    "type": entity["type"],
                    "start": entity["start"],
                    "end": entity["end"],
                    "prompt_hash": prompt_hash(prompt),
                    "request_hash": request_hash(envelope),
                    "prompt_chars": len(prompt),
                    "evidence_mode": evidence_config.get("mode", "source_text_only"),
                    "evidence_count": len(evidence_passages),
                }
            )

    outputs = config["outputs"]
    write_jsonl_atomic(Path(outputs["dry_run_prompts"]), prompt_rows)
    manifest = {
        "phase": "P3",
        "stage": "verification_dry_run",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": config_hash,
        "source_config": config["config_name"],
        "input_per_query_path": input_config["per_query_path"],
        "input_per_query_sha256": sha256_file(input_config["per_query_path"]),
        "query_rows": len(rows),
        "atomic_units": len(prompt_rows),
        "evidence": evidence_config,
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


def drop_entities_by_unit_decisions(
    pred_raw: dict[str, Any],
    *,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    drop_indices = {
        int(decision["entity_index"])
        for decision in decisions
        if decision["decision"] == "no" and decision["valid_answer"]
    }
    entities = [
        dict(entity)
        for index, entity in enumerate(pred_raw["entities"])
        if index not in drop_indices
    ]
    return {
        "id": pred_raw["id"],
        "text": pred_raw["text"],
        "entities": entities,
        "relations": [],
    }


def run_execute(config: dict[str, Any], config_path: Path) -> int:
    execution = config.get("execution", {})
    if execution.get("authorized") is not True:
        raise RuntimeError("config execution.authorized must be true for verifier model calls")
    if execution.get("model_calls_allowed") is not True:
        raise RuntimeError("config execution.model_calls_allowed must be true for verifier model calls")
    if execution.get("human_gate") != "P3_VERIFICATION_SANITY_APPROVED":
        raise RuntimeError("P3 verification human gate is not approved in config")
    if not gpu_visible():
        raise RuntimeError("GPU is not visible; refusing verifier execution")

    input_config = config["input"]
    rows = load_per_query_rows(
        input_config["per_query_path"],
        expected_rows=input_config.get("expected_rows"),
    )
    evidence_config = config.get("evidence", {"mode": "source_text_only"})
    output_instruction = config["prompt"].get("output_instruction", "只回答yes或no")
    generation = config["generation"]
    config_hash = sha256_file(config_path)
    outputs = config["outputs"]
    cache_dir = Path(config["cache"]["dir"])
    base_url = config["model"]["base_url"]
    api_key = config["model"].get("api_key", "EMPTY")
    timeout_seconds = int(config["model"]["timeout_seconds"])

    per_query_rows: list[dict[str, Any]] = []
    total_units = 0
    dropped_units = 0
    invalid_units = 0
    for row in rows:
        pred_raw = row["pred_raw"]
        evidence_passages = select_evidence(row, evidence_config)
        decisions: list[dict[str, Any]] = []
        for index, entity in enumerate(pred_raw["entities"]):
            prompt = build_entity_verification_prompt(
                text=str(pred_raw["text"]),
                entity=entity,
                evidence_passages=evidence_passages,
                output_instruction=output_instruction,
            )
            envelope = build_request_envelope(
                prompt=prompt,
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
            decision = parse_verifier_answer(result.content)
            valid_answer = decision in {"yes", "no"}
            total_units += 1
            if decision == "no":
                dropped_units += 1
            if not valid_answer:
                invalid_units += 1
            decisions.append(
                {
                    "unit_id": f"{row['id']}::entity::{index}",
                    "unit_kind": "entity",
                    "entity_index": index,
                    "span": entity["span"],
                    "type": entity["type"],
                    "decision": decision,
                    "valid_answer": valid_answer,
                    "raw_output_hash": result.raw_output_hash,
                    "request_hash": result.request_hash,
                    "cache_hit": result.cache_hit,
                    "latency_ms": round(result.latency_ms, 3),
                    "prompt_hash": prompt_hash(prompt),
                    "evidence_mode": evidence_config.get("mode", "source_text_only"),
                    "evidence_count": len(evidence_passages),
                }
            )
        pred_verified = drop_entities_by_unit_decisions(pred_raw, decisions=decisions)
        per_query_rows.append(
            {
                "id": row["id"],
                "dataset": row.get("dataset"),
                "config": config["config_name"],
                "k": row.get("k"),
                "seed": row.get("seed"),
                "gold": row.get("gold"),
                "pred_raw": pred_raw,
                "pred_verified": pred_verified,
                "verifier_decisions": decisions,
                "source_prompt_hash": row.get("prompt_hash"),
                "source_raw_llm_output_hash": row.get("raw_llm_output_hash"),
            }
        )

    write_jsonl_atomic(Path(outputs["per_query"]), per_query_rows)
    summary = {
        "phase": "P3",
        "stage": "verification_execution",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_hash,
        "source_config": config["config_name"],
        "input_per_query_path": input_config["per_query_path"],
        "input_per_query_sha256": sha256_file(input_config["per_query_path"]),
        "query_rows": len(rows),
        "atomic_units": total_units,
        "dropped_units": dropped_units,
        "invalid_units": invalid_units,
        "evidence": evidence_config,
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
    if args.dry_run:
        return run_dry(config, config_path)
    return run_execute(config, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
