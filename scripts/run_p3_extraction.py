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
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (
    build_error_retry_prompt,
    build_ner_prompt,
    build_request_envelope,
    entity_micro_counts,
    parse_extraction_output,
    prompt_hash,
    select_fixed_random_examples,
)
from equipment_ie.llm_labeling import chat_with_cache, request_hash
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record


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


def load_records(path: str) -> list[dict[str, Any]]:
    return [record for record in iter_jsonl(Path(path))]


def empty_prediction(gold: dict[str, Any]) -> dict[str, Any]:
    return {"id": gold["id"], "text": gold["text"], "entities": [], "relations": []}


def build_query_plan(
    *,
    config: dict[str, Any],
    config_path: Path,
    dry_run: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    support_records = load_records(config["data"]["support_path"])
    query_records = load_records(config["data"]["query_path"])
    if dry_run:
        max_queries = int(config.get("dry_run", {}).get("max_queries", len(query_records)))
        query_records = query_records[:max_queries]
    example_config = config["examples"]
    if example_config["mode"] != "fixed_random":
        raise ValueError("only fixed_random is implemented for P3-A dry-run")
    examples = select_fixed_random_examples(
        support_records,
        k=int(example_config["k"]),
        seed=int(example_config["seed"]),
    )
    return support_records, query_records, examples, sha256_file(config_path)


def run_dry(config: dict[str, Any], config_path: Path) -> int:
    _, query_records, examples, config_hash = build_query_plan(
        config=config, config_path=config_path, dry_run=True
    )
    entity_types = config["schema"]["entity_types"]
    generation = config["generation"]
    prompt_rows: list[dict[str, Any]] = []
    max_prompt_chars = 0
    for record in query_records:
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=entity_types,
            examples=examples,
            include_relations=False,
            output_instruction=config["prompt"]["output_instruction"],
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
                "id": record["id"],
                "prompt_hash": prompt_hash(prompt),
                "request_hash": request_hash(envelope),
                "prompt_chars": len(prompt),
                "gold_entities": len(record["entities"]),
            }
        )

    outputs = config["outputs"]
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
        "support_path": config["data"]["support_path"],
        "query_records": len(query_records),
        "examples": [record["id"] for record in examples],
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
    if execution.get("authorized") is not True:
        raise RuntimeError("config execution.authorized must be true for model calls")
    if execution.get("human_gate") not in {
        "P3_GPU_SANITY_APPROVED",
        "P3_DOMAIN_SANITY_APPROVED",
    }:
        raise RuntimeError("P3 GPU sanity human gate is not approved in config")
    if not gpu_visible():
        raise RuntimeError("GPU is not visible; refusing non-dry execution")

    _, query_records, examples, config_hash = build_query_plan(
        config=config, config_path=config_path, dry_run=False
    )
    entity_types = set(config["schema"]["entity_types"])
    generation = config["generation"]
    outputs = config["outputs"]
    cache_dir = Path(config["cache"]["dir"])
    base_url = config["model"]["base_url"]
    api_key = config["model"].get("api_key", "EMPTY")
    timeout_seconds = int(config["model"]["timeout_seconds"])
    retry_suffix = config["prompt"].get("retry_suffix", "只返回合法JSON")

    rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    started = time.monotonic()
    for record in query_records:
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=config["schema"]["entity_types"],
            examples=examples,
            include_relations=False,
            output_instruction=config["prompt"]["output_instruction"],
        )
        attempts: list[dict[str, Any]] = []
        pred: dict[str, Any] | None = None
        parse_error: str | None = None
        raw_output_hash = ""
        total_latency = 0.0
        attempt_prompt = prompt
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
            total_latency += result.latency_ms
            raw_output_hash = result.raw_output_hash
            try:
                pred = parse_extraction_output(
                    result.content,
                    record_id=record["id"],
                    text=record["text"],
                    entity_types=entity_types,
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
                    retry_suffix=retry_suffix,
                )
        if pred is None:
            pred = empty_prediction(record)
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
                "parse_failure": parse_error is not None,
                "raw_llm_output_hash": raw_output_hash,
                "prompt_hash": prompt_hash(prompt),
                "attempts": attempts,
            }
        )

    write_jsonl_atomic(Path(outputs["per_query"]), rows)
    counts = entity_micro_counts(query_records, predictions)
    parse_failures = sum(1 for row in rows if row["parse_failure"])
    summary = {
        "phase": "P3",
        "stage": "extraction_execution",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_hash,
        "query_records": len(query_records),
        "examples": [record["id"] for record in examples],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "parse_failures": parse_failures,
        "parse_failure_rate": parse_failures / len(rows) if rows else 0.0,
        "entity_micro": counts.report(),
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
