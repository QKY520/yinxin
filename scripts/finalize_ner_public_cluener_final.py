#!/usr/bin/env python3
"""Validate and summarize the authorized CLUENER public-NER cells."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (  # noqa: E402
    build_ner_prompt,
    parse_extraction_output,
    prompt_hash,
)
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record  # noqa: E402


GATE = "NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED"
PHASE = "NER_PUBLIC_CLUENER_FINAL"
SCHEMA_VERSION = "ner-public-cluener-abcd-k5-final-v1"
REPLAY_SHA256 = "36a529b9cd8cd0a78d2438376885263d5b9d63cb4967a0e88ad50eedbdffb455"
VARIANTS = "ABCD"
SEEDS = (42, 43, 44)
CELL_ORDER = tuple(
    f"cluener:{variant}:k5:s{seed}" for seed in SEEDS for variant in VARIANTS
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-manifest", required=True)
    parser.add_argument("--f6-replay", required=True)
    parser.add_argument("--output-report", required=True)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [dict(row) for row in iter_jsonl(path, validate=False)]


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def write_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def entity_key(entity: Mapping[str, Any]) -> tuple[int, int, str]:
    return int(entity["start"]), int(entity["end"]), str(entity["type"])


def count_entities(
    gold_records: Iterable[Mapping[str, Any]],
    prediction_records: Iterable[Mapping[str, Any]],
    *,
    entity_type: str | None = None,
) -> dict[str, Any]:
    tp = fp = fn = 0
    for gold, prediction in zip(gold_records, prediction_records, strict=True):
        gold_keys = {
            entity_key(entity)
            for entity in gold["entities"]
            if entity_type is None or entity["type"] == entity_type
        }
        pred_keys = {
            entity_key(entity)
            for entity in prediction["entities"]
            if entity_type is None or entity["type"] == entity_type
        }
        tp += len(gold_keys & pred_keys)
        fp += len(pred_keys - gold_keys)
        fn += len(gold_keys - pred_keys)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predicted_entities": tp + fp,
        "gold_entities": tp + fn,
        "entity_false_discovery_rate": fp / (tp + fp) if tp + fp else 0.0,
    }


def assert_close(observed: float, expected: float, label: str) -> None:
    if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"{label}: {observed} != {expected}")


def cache_path(cache_dir: Path, request_hash: str) -> Path:
    return cache_dir / request_hash[:2] / f"{request_hash}.json"


def validate_cache_and_prompt(
    *,
    row: Mapping[str, Any],
    query: Mapping[str, Any],
    config: Mapping[str, Any],
    config_sha256: str,
    support_by_id: Mapping[str, Mapping[str, Any]],
    cache_dir: Path,
) -> dict[str, Any]:
    attempts = row.get("attempts")
    if not isinstance(attempts, list) or len(attempts) not in (1, 2):
        raise ValueError(f"{row.get('id')}: attempts must contain one or two rows")
    example_ids = row.get("example_ids")
    if not isinstance(example_ids, list) or len(example_ids) != 5:
        raise ValueError(f"{row.get('id')}: expected exactly five example IDs")
    if len(set(example_ids)) != 5 or any(value not in support_by_id for value in example_ids):
        raise ValueError(f"{row.get('id')}: invalid support example IDs")
    examples = [support_by_id[value] for value in example_ids]
    expected_prompt = build_ner_prompt(
        query_text=str(query["text"]),
        entity_types=config["schema"]["entity_types"],
        examples=examples,
        glossary_entries=list(row.get("glossary_terms", [])),
        rag_passages=list(row.get("rag_passages", [])),
        include_relations=False,
        output_instruction=config["prompt"]["output_instruction"],
    )
    if prompt_hash(expected_prompt) != row.get("prompt_hash"):
        raise ValueError(f"{row.get('id')}: prompt hash is not reproducible")

    cache_hits = 0
    for index, attempt in enumerate(attempts):
        request_hash = attempt.get("request_hash")
        if not isinstance(request_hash, str) or len(request_hash) != 64:
            raise ValueError(f"{row.get('id')}: invalid request hash")
        path = cache_path(cache_dir, request_hash)
        cache = load_json(path)
        if cache.get("request_hash") != request_hash:
            raise ValueError(f"{row.get('id')}: cache request hash mismatch")
        if cache.get("raw_output_hash") != attempt.get("raw_output_hash"):
            raise ValueError(f"{row.get('id')}: cache raw-output hash mismatch")
        request = cache.get("request", {})
        if request.get("config_hash") != config_sha256:
            raise ValueError(f"{row.get('id')}: cache config hash mismatch")
        if request.get("run_id") != config.get("run_id"):
            raise ValueError(f"{row.get('id')}: cache run ID mismatch")
        payload = request.get("payload", {})
        if (
            payload.get("model") != config["model"]["name"]
            or payload.get("seed") != config["generation"]["seed"]
            or payload.get("temperature") != config["generation"]["temperature"]
            or payload.get("top_p") != config["generation"]["top_p"]
            or payload.get("max_tokens") != config["generation"]["max_tokens"]
        ):
            raise ValueError(f"{row.get('id')}: cached generation settings changed")
        messages = payload.get("messages")
        if not isinstance(messages, list) or len(messages) != 1:
            raise ValueError(f"{row.get('id')}: cached message envelope changed")
        if index == 0 and messages[0].get("content") != expected_prompt:
            raise ValueError(f"{row.get('id')}: complete base prompt is not reproducible")
        if bool(attempt.get("cache_hit")):
            cache_hits += 1

    final_cache = load_json(cache_path(cache_dir, str(attempts[-1]["request_hash"])))
    raw_content = final_cache.get("content")
    if not isinstance(raw_content, str):
        raise ValueError(f"{row.get('id')}: cached raw content is missing")
    flags: list[dict[str, Any]] = []
    try:
        reparsed = parse_extraction_output(
            raw_content,
            record_id=str(query["id"]),
            text=str(query["text"]),
            entity_types=set(config["schema"]["entity_types"]),
            drop_invalid_entities=True,
            sanitization_flags=flags,
        )
        reparse_failed = False
    except Exception:
        reparsed = {"id": query["id"], "text": query["text"], "entities": [], "relations": []}
        reparse_failed = True
    if reparse_failed != bool(row.get("parse_failure")):
        raise ValueError(f"{row.get('id')}: parse-failure flag is not reproducible")
    if reparsed != row.get("pred_raw"):
        raise ValueError(f"{row.get('id')}: parsed prediction is not reproducible")
    recorded_flags = row.get("sanitization_flags")
    if not isinstance(recorded_flags, list):
        raise ValueError(f"{row.get('id')}: sanitizer event list is missing")
    if not reparse_failed:
        if len(attempts) == 1 and flags != recorded_flags:
            raise ValueError(f"{row.get('id')}: sanitizer events are not reproducible")
        if len(attempts) == 2 and flags and recorded_flags[-len(flags) :] != flags:
            raise ValueError(f"{row.get('id')}: final retry sanitizer events differ")
    return {"cache_hits": cache_hits, "requests": len(attempts)}


def validate_cell(
    *,
    entry: Mapping[str, Any],
    query_records: list[dict[str, Any]],
    query_ids: list[str],
    replay_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cell_id = str(entry["cell_id"])
    config_path = Path(str(entry["execution_config_path"]))
    per_query_path = Path(str(entry["per_query_path"]))
    summary_path = Path(str(entry["summary_path"]))
    cache_dir = Path(str(entry["cache_dir"]))
    config = load_yaml(config_path)
    if sha256_file(config_path) != entry.get("execution_config_sha256"):
        raise ValueError(f"{cell_id}: execution config hash changed")
    if (
        config.get("execution", {}).get("human_gate") != GATE
        or config.get("execution", {}).get("phase") != PHASE
        or config.get("data", {}).get("dataset") != "cluener"
        or config.get("schema", {}).get("task") != "ner"
    ):
        raise ValueError(f"{cell_id}: execution scope changed")

    support_records = load_jsonl(Path(config["data"]["support_path"]))
    support_by_id = {str(row["id"]): row for row in support_records}
    if len(support_by_id) != 30:
        raise ValueError(f"{cell_id}: support bank must contain 30 unique rows")
    rows = load_jsonl(per_query_path)
    if len(rows) != 1343 or [row.get("id") for row in rows] != query_ids:
        raise ValueError(f"{cell_id}: incomplete or misordered query coverage")
    summary = load_json(summary_path)
    if summary.get("query_records") != 1343:
        raise ValueError(f"{cell_id}: summary row count changed")
    if summary.get("per_query_sha256") != sha256_file(per_query_path):
        raise ValueError(f"{cell_id}: per-query SHA256 mismatch")

    variant = str(entry["config"])
    seed = int(entry["seed"])
    allowed_types = set(config["schema"]["entity_types"])
    predictions: list[dict[str, Any]] = []
    retry_count = request_count = cache_hits = sanitizer_events = 0
    latencies: list[float] = []
    for row, query in zip(rows, query_records, strict=True):
        if (
            row.get("dataset") != "cluener"
            or row.get("config") != variant
            or row.get("k") != 5
            or row.get("seed") != seed
            or row.get("gold") != query
            or row.get("pred_verified") is not None
        ):
            raise ValueError(f"{cell_id}/{row.get('id')}: row metadata changed")
        validate_record(row["gold"])
        validate_record(row["pred_raw"])
        if row["pred_raw"].get("relations"):
            raise ValueError(f"{cell_id}/{row.get('id')}: NER prediction contains relations")
        if any(entity.get("type") not in allowed_types for entity in row["pred_raw"]["entities"]):
            raise ValueError(f"{cell_id}/{row.get('id')}: unsupported entity type")
        if variant in "AB" and (row.get("glossary_terms") or row.get("rag_passage_ids")):
            raise ValueError(f"{cell_id}/{row.get('id')}: unexpected glossary or RAG evidence")
        if variant == "C" and row.get("rag_passage_ids"):
            raise ValueError(f"{cell_id}/{row.get('id')}: C unexpectedly contains RAG evidence")
        if variant == "D":
            replay = replay_by_id[str(row["id"])]
            expected_ids = [passage["id"] for passage in replay["selected_passages"]]
            expected_passages = [passage["display"] for passage in replay["selected_passages"]]
            if row.get("rag_passage_ids") != expected_ids or row.get("rag_passages") != expected_passages:
                raise ValueError(f"{cell_id}/{row.get('id')}: D differs from frozen F6 replay")

        cache_report = validate_cache_and_prompt(
            row=row,
            query=query,
            config=config,
            config_sha256=str(entry["execution_config_sha256"]),
            support_by_id=support_by_id,
            cache_dir=cache_dir,
        )
        request_count += cache_report["requests"]
        cache_hits += cache_report["cache_hits"]
        retry_count += max(0, cache_report["requests"] - 1)
        sanitizer_events += len(row.get("sanitization_flags", []))
        latency = float(row.get("llm_latency_ms", -1))
        if latency < 0:
            raise ValueError(f"{cell_id}/{row.get('id')}: invalid latency")
        latencies.append(latency)
        predictions.append(row["pred_raw"])

    parse_failures = sum(bool(row.get("parse_failure")) for row in rows)
    parse_failure_rate = parse_failures / len(rows)
    if parse_failure_rate >= 0.05:
        raise ValueError(f"{cell_id}: parse-failure stop threshold reached")
    micro = count_entities(query_records, predictions)
    runner_micro = summary.get("entity_micro", {})
    for key in ("precision", "recall", "f1"):
        assert_close(float(runner_micro[key]), float(micro[key]), f"{cell_id}/{key}")
    for key in ("tp", "fp", "fn"):
        if int(runner_micro[key]) != int(micro[key]):
            raise ValueError(f"{cell_id}/{key}: runner metric mismatch")
    if summary.get("parse_failures") != parse_failures:
        raise ValueError(f"{cell_id}: parse-failure count mismatch")
    assert_close(
        float(summary.get("parse_failure_rate")), parse_failure_rate, f"{cell_id}/parse_failure_rate"
    )
    per_type = {
        entity_type: count_entities(query_records, predictions, entity_type=entity_type)
        for entity_type in sorted(allowed_types)
    }
    metric = {
        "cell_id": cell_id,
        "config": variant,
        "seed": seed,
        "rows": len(rows),
        "per_query_sha256": sha256_file(per_query_path),
        "summary_sha256": sha256_file(summary_path),
        "micro": micro,
        "per_type": per_type,
        "parse_failures": parse_failures,
        "parse_failure_rate": parse_failure_rate,
        "retry_count": retry_count,
        "request_count": request_count,
        "cache_hits": cache_hits,
        "sanitizer_events": sanitizer_events,
        "latency_ms": {
            "sum": sum(latencies),
            "mean": statistics.fmean(latencies),
            "median": statistics.median(latencies),
            "max": max(latencies),
        },
    }
    return metric, rows


def aggregate(cell_metrics: list[Mapping[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for metric in cell_metrics:
        grouped[str(metric["config"])].append(metric)
    result: dict[str, Any] = {}
    for variant in VARIANTS:
        metrics = sorted(grouped[variant], key=lambda value: int(value["seed"]))
        if [metric["seed"] for metric in metrics] != list(SEEDS):
            raise ValueError(f"{variant}: missing three-seed metrics")
        values: dict[str, Any] = {"seeds": list(SEEDS)}
        for key in ("precision", "recall", "f1", "entity_false_discovery_rate"):
            samples = [float(metric["micro"][key]) for metric in metrics]
            values[key] = {
                "values": samples,
                "mean": statistics.fmean(samples),
                "sample_std": statistics.stdev(samples),
            }
        for key in ("tp", "fp", "fn", "predicted_entities", "gold_entities"):
            samples = [int(metric["micro"][key]) for metric in metrics]
            values[key] = {
                "values": samples,
                "mean": statistics.fmean(samples),
                "sample_std": statistics.stdev(samples),
            }
        result[variant] = values
    return result


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.execution_manifest).resolve()
    replay_path = Path(args.f6_replay).resolve()
    output_path = Path(args.output_report).resolve()
    manifest = load_json(manifest_path)
    if (
        manifest.get("schema_version") != SCHEMA_VERSION
        or manifest.get("approved_gate") != GATE
        or manifest.get("phase") != PHASE
        or manifest.get("status") != "AUTHORIZED_PREINFERENCE"
    ):
        raise ValueError("execution manifest scope or status changed")
    cells = manifest.get("cells")
    if not isinstance(cells, list) or [cell.get("cell_id") for cell in cells] != list(CELL_ORDER):
        raise ValueError("execution manifest does not contain the exact ordered 12 cells")

    first_config = load_yaml(Path(str(cells[0]["execution_config_path"])))
    query_records = load_jsonl(Path(first_config["data"]["query_path"]))
    query_ids = [str(record["id"]) for record in query_records]
    if len(query_ids) != 1343 or len(set(query_ids)) != 1343:
        raise ValueError("CLUENER dev IDs must contain 1343 unique rows")
    for record in query_records:
        validate_record(record)

    if sha256_file(replay_path) != REPLAY_SHA256:
        raise ValueError("F6 replay SHA256 changed")
    replay = load_json(replay_path)
    replay_rows = replay.get("rows")
    if not isinstance(replay_rows, list):
        raise ValueError("F6 replay rows missing")
    replay_by_id = {str(row["id"]): row for row in replay_rows}
    if list(replay_by_id) != query_ids:
        raise ValueError("F6 replay ID order differs from CLUENER dev")

    metrics: list[dict[str, Any]] = []
    rows_by_cell: dict[str, list[dict[str, Any]]] = {}
    for entry in cells:
        metric, rows = validate_cell(
            entry=entry,
            query_records=query_records,
            query_ids=query_ids,
            replay_by_id=replay_by_id,
        )
        metrics.append(metric)
        rows_by_cell[str(entry["cell_id"])] = rows

    for seed in SEEDS:
        b_rows = rows_by_cell[f"cluener:B:k5:s{seed}"]
        c_rows = rows_by_cell[f"cluener:C:k5:s{seed}"]
        d_rows = rows_by_cell[f"cluener:D:k5:s{seed}"]
        for b_row, c_row, d_row in zip(b_rows, c_rows, d_rows, strict=True):
            if b_row["example_ids"] != c_row["example_ids"] or c_row["example_ids"] != d_row["example_ids"]:
                raise ValueError(f"seed {seed}/{b_row['id']}: B/C/D examples are not identical")
            if c_row["glossary_terms"] != d_row["glossary_terms"]:
                raise ValueError(f"seed {seed}/{b_row['id']}: C/D glossary matches differ")

    report = {
        "schema_version": "ner-public-cluener-abcd-k5-final-closeout-v1",
        "status": "PASS",
        "approved_gate": GATE,
        "execution_manifest_path": str(manifest_path),
        "execution_manifest_sha256": sha256_file(manifest_path),
        "scope": manifest["scope"],
        "cells_validated": len(metrics),
        "rows_per_cell": 1343,
        "all_ids_aligned": True,
        "unsupported_entity_types": 0,
        "relation_predictions": 0,
        "f6_replay_rows": 1343,
        "f6_replay_passages": 4029,
        "cell_metrics": metrics,
        "three_seed_aggregate": aggregate(metrics),
        "matrix_before": "4/60",
        "matrix_after": "16/60",
        "claim_interpretation_performed": False,
        "paper_edits_performed": False,
    }
    write_exclusive(output_path, report)
    print(
        json.dumps(
            {
                "status": "PASS",
                "cells": len(metrics),
                "report": str(output_path),
                "report_sha256": sha256_file(output_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
