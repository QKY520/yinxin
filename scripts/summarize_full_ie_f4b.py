#!/usr/bin/env python3
"""Validate and summarize the bounded FULL-IE F4b CLUENER tune sanity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import entity_micro_counts, prompt_hash  # noqa: E402
from equipment_ie.llm_labeling import (  # noqa: E402
    request_hash as compute_request_hash,
    sha256_text,
)
from equipment_ie.schema import validate_record  # noqa: E402


EXPECTED_ROWS = 50
EXPECTED_K = 5
EXPECTED_SEED = 42
AUDIT_THRESHOLD = 0.70
GATE = "FULL_IE_CLUENER_TUNE_SANITY_APPROVED"
PHASE = "FULL_IE_CLUENER_TUNE_SANITY"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENTITY_TYPES = (
    "address",
    "book",
    "company",
    "game",
    "government",
    "movie",
    "name",
    "organization",
    "position",
    "scene",
)
STAGE_N_CONFIGS = {
    "A": "a",
    "B": "b",
    "C": "c",
    "D": "d",
}
VERIFICATION_CONFIGS = {
    "E-prime": {
        "stem": "eprime",
        "source_config": "C",
        "source_stem": "c",
        "evidence_mode": "source_text_only",
        "evidence_count": 0,
    },
    "E": {
        "stem": "e",
        "source_config": "D",
        "source_stem": "d",
        "evidence_mode": "reuse_source_rag_passages",
        "evidence_count": 3,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--log-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--hourly-rate", type=float, required=True)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: every JSONL row must be an object")
    return rows


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required") from exc
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


def write_jsonl_atomic(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(
                    json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n"
                )
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def entity_key(entity: Mapping[str, Any]) -> tuple[int, int, str]:
    return (int(entity["start"]), int(entity["end"]), str(entity["type"]))


def rows_by_id(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row["id"]): row for row in rows}


def assert_metric_tree_matches(expected: Any, actual: Any, *, label: str) -> None:
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        if set(expected) != set(actual):
            raise ValueError(f"{label}: metric keys differ")
        for key in expected:
            assert_metric_tree_matches(
                expected[key], actual[key], label=f"{label}.{key}"
            )
        return
    if (
        isinstance(expected, (int, float))
        and not isinstance(expected, bool)
        and isinstance(actual, (int, float))
        and not isinstance(actual, bool)
    ):
        if not math.isclose(float(expected), float(actual), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"{label}: expected {expected}, recomputed {actual}")
        return
    if expected != actual:
        raise ValueError(f"{label}: expected {expected!r}, recomputed {actual!r}")


def recompute_entity_metrics(
    rows: Sequence[Mapping[str, Any]], *, prediction_field: str
) -> dict[str, Any]:
    return entity_micro_counts(
        [row["gold"] for row in rows],
        [row[prediction_field] for row in rows],
    ).report()


def per_type_metrics(
    rows: Sequence[Mapping[str, Any]], *, prediction_field: str
) -> dict[str, dict[str, Any]]:
    gold_counts: Counter[str] = Counter()
    pred_counts: Counter[str] = Counter()
    true_counts: Counter[str] = Counter()
    for row in rows:
        gold = {entity_key(entity) for entity in row["gold"]["entities"]}
        pred = {entity_key(entity) for entity in row[prediction_field]["entities"]}
        gold_counts.update(key[2] for key in gold)
        pred_counts.update(key[2] for key in pred)
        true_counts.update(key[2] for key in gold & pred)
    report: dict[str, dict[str, Any]] = {}
    for entity_type in ENTITY_TYPES:
        tp = true_counts[entity_type]
        fp = pred_counts[entity_type] - tp
        fn = gold_counts[entity_type] - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        report[entity_type] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "gold": gold_counts[entity_type],
            "predicted": pred_counts[entity_type],
        }
    return report


def nearest_rank_percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0.0 < percentile <= 1.0:
        raise ValueError("percentile must be in (0, 1]")
    ordered = sorted(float(value) for value in values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def latency_report(
    rows: Sequence[Mapping[str, Any]], fields: Sequence[str]
) -> dict[str, dict[str, float]]:
    report: dict[str, dict[str, float]] = {}
    for field in fields:
        values: list[float] = []
        for row in rows:
            value = row.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ValueError(f"row {row.get('id')}: invalid {field}")
            values.append(float(value))
        report[field] = {
            "mean": statistics.fmean(values),
            "median": statistics.median(values),
            "p95_nearest_rank": nearest_rank_percentile(values, 0.95),
            "total": sum(values),
        }
    return report


def validate_common_config(config: Mapping[str, Any], *, name: str) -> None:
    execution = config.get("execution", {})
    if execution.get("authorized") is not True:
        raise ValueError(f"{name}: execution is not authorized")
    if execution.get("model_calls_allowed") is not True:
        raise ValueError(f"{name}: model calls were not authorized")
    if execution.get("human_gate") != GATE or execution.get("phase") != PHASE:
        raise ValueError(f"{name}: gate or phase mismatch")
    if config.get("config_name") != name:
        raise ValueError(f"{name}: config_name mismatch")
    if config.get("data", {}).get("dataset") != "cluener":
        raise ValueError(f"{name}: dataset must be cluener")
    schema = config.get("schema", {})
    if set(schema.get("entity_types", {})) != set(ENTITY_TYPES):
        raise ValueError(f"{name}: entity schema differs from the ten CLUENER types")
    if schema.get("relation_types", {}) != {}:
        raise ValueError(f"{name}: CLUENER relation schema must be empty")
    generation = config.get("generation", {})
    if generation.get("seed") != EXPECTED_SEED:
        raise ValueError(f"{name}: generation seed mismatch")


def validate_resource_locks(
    config: Mapping[str, Any], verified: dict[str, str]
) -> dict[str, dict[str, str]]:
    locks = config.get("resource_lock", {})
    if not isinstance(locks, Mapping) or not locks:
        raise ValueError(f"{config.get('config_name')}: resource_lock is missing")
    report: dict[str, dict[str, str]] = {}
    for label, raw in locks.items():
        if not isinstance(raw, Mapping):
            raise ValueError(f"resource lock {label}: expected object")
        path = Path(str(raw.get("path", "")))
        expected = str(raw.get("sha256", ""))
        if not path.is_file() or not HEX64.fullmatch(expected):
            raise ValueError(f"resource lock {label}: path/hash is invalid")
        actual = verified.setdefault(str(path), sha256_file(path))
        if actual != expected:
            raise ValueError(f"resource lock {label}: SHA256 mismatch")
        report[str(label)] = {"path": str(path), "sha256": actual}
    return report


def validate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    config: str,
    prediction_fields: Sequence[str],
) -> None:
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"{config}: expected {EXPECTED_ROWS} rows, found {len(rows)}")
    seen: set[str] = set()
    allowed = set(ENTITY_TYPES)
    for row in rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"{config}: row id must be non-empty")
        if record_id in seen:
            raise ValueError(f"{config}: duplicate id {record_id}")
        seen.add(record_id)
        if row.get("dataset") != "cluener" or row.get("config") != config:
            raise ValueError(f"{config}/{record_id}: dataset/config mismatch")
        if row.get("k") != EXPECTED_K or row.get("seed") != EXPECTED_SEED:
            raise ValueError(f"{config}/{record_id}: expected K=5 seed42")
        gold = row.get("gold")
        if not isinstance(gold, Mapping):
            raise ValueError(f"{config}/{record_id}: gold must be an object")
        validate_record(gold)
        if gold["id"] != record_id or gold["relations"]:
            raise ValueError(f"{config}/{record_id}: invalid CLUENER gold")
        if any(entity["type"] not in allowed for entity in gold["entities"]):
            raise ValueError(f"{config}/{record_id}: unsupported gold type")
        for field in prediction_fields:
            prediction = row.get(field)
            if not isinstance(prediction, Mapping):
                raise ValueError(f"{config}/{record_id}: {field} must be an object")
            validate_record(prediction)
            if (
                prediction["id"] != record_id
                or prediction["text"] != gold["text"]
                or prediction["relations"]
            ):
                raise ValueError(f"{config}/{record_id}: invalid {field} record")
            unsupported = {
                entity["type"]
                for entity in prediction["entities"]
                if entity["type"] not in allowed
            }
            if unsupported:
                raise ValueError(
                    f"{config}/{record_id}: unsupported prediction types {unsupported}"
                )


def validate_cache_entry(
    *,
    cache_root: Path,
    request_digest: str,
    raw_digest: str,
    expected_prompt_digest: str | None,
    phase: str,
) -> dict[str, Any]:
    if not HEX64.fullmatch(request_digest) or not HEX64.fullmatch(raw_digest):
        raise ValueError(f"{phase}: malformed request/raw hash")
    path = cache_root / request_digest[:2] / f"{request_digest}.json"
    entry = read_json(path)
    if entry.get("request_hash") != request_digest:
        raise ValueError(f"{path}: request hash field mismatch")
    request = entry.get("request")
    if not isinstance(request, Mapping) or compute_request_hash(request) != request_digest:
        raise ValueError(f"{path}: request envelope hash mismatch")
    content = entry.get("content")
    if not isinstance(content, str) or sha256_text(content) != raw_digest:
        raise ValueError(f"{path}: raw content hash mismatch")
    if entry.get("raw_output_hash") != raw_digest:
        raise ValueError(f"{path}: raw output hash field mismatch")
    payload = request.get("payload")
    messages = payload.get("messages") if isinstance(payload, Mapping) else None
    if (
        not isinstance(messages, list)
        or len(messages) != 1
        or not isinstance(messages[0], Mapping)
        or messages[0].get("role") != "user"
        or not isinstance(messages[0].get("content"), str)
        or not messages[0]["content"]
    ):
        raise ValueError(f"{path}: prompt text is not preserved")
    prompt_digest = prompt_hash(messages[0]["content"])
    if expected_prompt_digest is not None and prompt_digest != expected_prompt_digest:
        raise ValueError(f"{path}: prompt hash mismatch")
    try:
        response_content = entry["response"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"{path}: raw response is not preserved") from exc
    if response_content != content:
        raise ValueError(f"{path}: response/content mismatch")
    return {
        "phase": phase,
        "request_hash": request_digest,
        "raw_output_hash": raw_digest,
        "prompt_hash": prompt_digest,
        "run_id": request.get("run_id"),
        "config_hash": request.get("config_hash"),
        "cache_path": str(path),
        "cache_sha256": sha256_file(path),
        "created_at": entry.get("created_at"),
        "latency_ms": entry.get("latency_ms"),
    }


def validate_cache_inventory(
    cache_root: Path,
    referenced: Mapping[str, Mapping[str, Any]],
    *,
    label: str,
) -> None:
    actual = {
        path.stem
        for path in cache_root.rglob("*.json")
        if path.is_file()
    }
    expected = set(referenced)
    if actual != expected:
        missing = sorted(expected - actual)
        orphaned = sorted(actual - expected)
        raise ValueError(
            f"{label}: cache inventory mismatch missing={missing[:3]} "
            f"orphaned={orphaned[:3]}"
        )


def metric_delta(verified: Mapping[str, Any], raw: Mapping[str, Any]) -> dict[str, float]:
    return {
        key: float(verified[key]) - float(raw[key])
        for key in ("precision", "recall", "f1")
    }


def build_entity_drop_audit(
    rows: Sequence[Mapping[str, Any]], *, config: str
) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for row in rows:
        gold = {entity_key(entity) for entity in row["gold"]["entities"]}
        raw_entities = row["pred_raw"]["entities"]
        for decision in row.get("verifier_decisions", []):
            if not (
                decision.get("valid_answer") is True
                and decision.get("decision") == "no"
            ):
                continue
            index = int(decision["unit_index"])
            entity = raw_entities[index]
            exact_gold_match = entity_key(entity) in gold
            audit.append(
                {
                    "config": config,
                    "source_config": row.get("source_config"),
                    "id": row["id"],
                    "text": row["pred_raw"]["text"],
                    "unit_index": index,
                    "entity": dict(entity),
                    "exact_gold_match": exact_gold_match,
                    "correct_drop": not exact_gold_match,
                    "decision": "no",
                    "evidence_mode": decision.get("evidence_mode"),
                    "evidence_count": decision.get("evidence_count"),
                    "prompt_hash": decision.get("prompt_hash"),
                    "request_hash": decision.get("request_hash"),
                    "raw_output_hash": decision.get("raw_output_hash"),
                }
            )
    return audit


def drop_statistics(audit: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(audit)
    correct = sum(item.get("correct_drop") is True for item in audit)
    rate = correct / total if total else None
    return {
        "dropped_entities": total,
        "correct_drops": correct,
        "incorrect_drops": total - correct,
        "correct_drop_rate": rate,
        "audit_threshold": AUDIT_THRESHOLD,
        "passes_70_percent": rate is not None and rate >= AUDIT_THRESHOLD,
    }


def validate_verified_contract(
    row: Mapping[str, Any],
    *,
    evidence_mode: str,
    evidence_count: int,
) -> None:
    raw = row["pred_raw"]
    decisions = row.get("verifier_decisions")
    if not isinstance(decisions, list) or len(decisions) != len(raw["entities"]):
        raise ValueError(f"row {row.get('id')}: expected one decision per entity")
    if [decision.get("unit_index") for decision in decisions] != list(
        range(len(raw["entities"]))
    ):
        raise ValueError(f"row {row.get('id')}: decision indices are incomplete")
    expected_entities = []
    for decision, entity in zip(decisions, raw["entities"]):
        if decision.get("unit_kind") != "entity":
            raise ValueError(f"row {row.get('id')}: non-entity verifier unit")
        valid = decision.get("valid_answer") is True
        answer = decision.get("decision")
        if valid != (answer in {"yes", "no"}):
            raise ValueError(f"row {row.get('id')}: inconsistent verifier validity")
        if decision.get("evidence_mode") != evidence_mode:
            raise ValueError(f"row {row.get('id')}: evidence mode mismatch")
        if decision.get("evidence_count") != evidence_count:
            raise ValueError(f"row {row.get('id')}: evidence count mismatch")
        if not (valid and answer == "no"):
            expected_entities.append(entity)
    expected = dict(raw)
    expected["entities"] = expected_entities
    expected["relations"] = []
    if row["pred_verified"] != expected:
        raise ValueError(f"row {row.get('id')}: verifier changed more than valid-no drops")
    if row.get("verifier_prompt_hashes") != [
        decision.get("prompt_hash") for decision in decisions
    ]:
        raise ValueError(f"row {row.get('id')}: verifier prompt hash list mismatch")
    expected_latency = round(
        sum(float(decision["latency_ms"]) for decision in decisions), 3
    )
    if not math.isclose(
        float(row.get("latency_verifier_ms", -1)),
        expected_latency,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise ValueError(f"row {row.get('id')}: verifier latency mismatch")


def validate_query_alignment(
    rows: Sequence[Mapping[str, Any]], query_rows: Sequence[Mapping[str, Any]], config: str
) -> None:
    if [row["id"] for row in rows] != [row["id"] for row in query_rows]:
        raise ValueError(f"{config}: query id order mismatch")
    for row, query in zip(rows, query_rows):
        if row["gold"] != query:
            raise ValueError(f"{config}/{row['id']}: gold differs from locked query row")


def load_run_window(log_dir: Path, hourly_rate: float) -> dict[str, Any]:
    if hourly_rate < 0:
        raise ValueError("hourly rate cannot be negative")
    start_text = (log_dir / "vllm_start_time.txt").read_text(encoding="utf-8").strip()
    stop_text = (log_dir / "vllm_stop_time.txt").read_text(encoding="utf-8").strip()
    start = datetime.fromisoformat(start_text)
    stop = datetime.fromisoformat(stop_text)
    seconds = (stop - start).total_seconds()
    if seconds < 0:
        raise ValueError("vLLM stop precedes start")
    return {
        "vllm_start": start_text,
        "vllm_stop": stop_text,
        "observable_seconds": seconds,
        "observable_hours": seconds / 3600.0,
        "hourly_rate_cny": hourly_rate,
        "estimated_cost_cny": seconds / 3600.0 * hourly_rate,
        "platform_bill_authoritative": True,
    }


def summarize(
    *,
    config_dir: Path,
    result_dir: Path,
    cache_dir: Path,
    log_dir: Path,
    hourly_rate: float,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    resource_hashes: dict[str, str] = {}
    config_hashes: dict[str, str] = {}
    config_locks: dict[str, Any] = {}
    stage_rows: dict[str, list[dict[str, Any]]] = {}
    cdev1: list[dict[str, Any]] = []
    cache_index: dict[str, dict[str, Any]] = {}
    extraction_cache = cache_dir / "extraction"
    verification_cache = cache_dir / "verification"
    query_rows: list[dict[str, Any]] | None = None
    query_path: Path | None = None

    for config_name, stem in STAGE_N_CONFIGS.items():
        config_path = config_dir / f"cluener_{stem}_stage_n.yaml"
        summary_path = result_dir / f"{stem}_stage_n_summary.json"
        per_query_path = result_dir / f"{stem}_stage_n_per_query.jsonl"
        config = read_yaml(config_path)
        validate_common_config(config, name=config_name)
        examples = config.get("examples", {})
        if examples.get("k") != EXPECTED_K or examples.get("seed") != EXPECTED_SEED:
            raise ValueError(f"{config_name}: example K/seed mismatch")
        locked_query_path = Path(str(config.get("data", {}).get("query_path", "")))
        if locked_query_path.name != "cluener_tune_subset50_seed42.jsonl":
            raise ValueError(f"{config_name}: unauthorized query path")
        if query_path is None:
            query_path = locked_query_path
            query_rows = read_jsonl(query_path)
            if len(query_rows) != EXPECTED_ROWS:
                raise ValueError("locked CLUENER tune subset must contain 50 rows")
            for query in query_rows:
                validate_record(query)
        elif locked_query_path != query_path:
            raise ValueError(f"{config_name}: query path differs across configs")

        file_config_hash = sha256_file(config_path)
        config_hashes[config_name] = file_config_hash
        config_locks[config_name] = validate_resource_locks(config, resource_hashes)
        run_summary = read_json(summary_path)
        rows = read_jsonl(per_query_path)
        validate_rows(rows, config=config_name, prediction_fields=("pred_raw",))
        assert query_rows is not None
        validate_query_alignment(rows, query_rows, config_name)
        if run_summary.get("config_sha256") != file_config_hash:
            raise ValueError(f"{config_name}: config SHA256 mismatch")
        if run_summary.get("per_query_sha256") != sha256_file(per_query_path):
            raise ValueError(f"{config_name}: per-query SHA256 mismatch")
        recomputed = recompute_entity_metrics(rows, prediction_field="pred_raw")
        assert_metric_tree_matches(
            run_summary.get("entity_micro"), recomputed, label=f"{config_name}.entity"
        )
        parse_failures = sum(bool(row.get("parse_failure")) for row in rows)
        if run_summary.get("parse_failures") != parse_failures:
            raise ValueError(f"{config_name}: parse failure count mismatch")
        sanitizer_events = sum(len(row.get("sanitization_flags", [])) for row in rows)
        if run_summary.get("sanitized_unit_events") != sanitizer_events:
            raise ValueError(f"{config_name}: sanitizer event count mismatch")

        attempt_count = 0
        retry_rows = 0
        cache_hits = 0
        for row in rows:
            attempts = row.get("attempts")
            if not isinstance(attempts, list) or not attempts:
                raise ValueError(f"{config_name}/{row['id']}: attempts missing")
            attempt_count += len(attempts)
            retry_rows += len(attempts) > 1
            cache_hits += sum(attempt.get("cache_hit") is True for attempt in attempts)
            if row.get("raw_llm_output_hash") != attempts[-1].get("raw_output_hash"):
                raise ValueError(f"{config_name}/{row['id']}: final raw hash mismatch")
            if not HEX64.fullmatch(str(row.get("prompt_hash", ""))):
                raise ValueError(f"{config_name}/{row['id']}: malformed prompt hash")
            for index, attempt in enumerate(attempts):
                request_digest = str(attempt.get("request_hash", ""))
                entry = validate_cache_entry(
                    cache_root=extraction_cache,
                    request_digest=request_digest,
                    raw_digest=str(attempt.get("raw_output_hash", "")),
                    expected_prompt_digest=(
                        str(row["prompt_hash"]) if index == 0 else None
                    ),
                    phase="extraction",
                )
                existing = cache_index.setdefault(request_digest, entry)
                if existing != entry:
                    raise ValueError(f"cache request {request_digest}: conflicting metadata")

        stage_rows[config_name] = rows
        cdev1.append(
            {
                "config": config_name,
                "rows": len(rows),
                "entity_micro": recomputed,
                "per_type": per_type_metrics(rows, prediction_field="pred_raw"),
                "parse_failures": parse_failures,
                "parse_failure_rate": parse_failures / EXPECTED_ROWS,
                "unsupported_entity_types": [],
                "sanitizer_events": sanitizer_events,
                "attempts": attempt_count,
                "retry_rows": retry_rows,
                "cache_hits": cache_hits,
                "elapsed_seconds": run_summary.get("elapsed_seconds"),
                "latency_ms": latency_report(
                    rows,
                    (
                        "llm_latency_ms",
                        "total_record_ms",
                        "example_selection_ms",
                        "glossary_selection_ms",
                        "rag_selection_ms",
                        "prompt_build_ms",
                    ),
                ),
                "config_sha256": file_config_hash,
                "per_query_sha256": run_summary["per_query_sha256"],
            }
        )

    assert query_rows is not None and query_path is not None
    b_by_id = rows_by_id(stage_rows["B"])
    for config_name in ("C", "D"):
        for row in stage_rows[config_name]:
            source = b_by_id[str(row["id"])]
            if row.get("example_ids") != source.get("example_ids"):
                raise ValueError(f"{config_name}/{row['id']}: B example replay mismatch")
    a_examples = {tuple(row.get("example_ids", [])) for row in stage_rows["A"]}
    if len(a_examples) != 1 or len(next(iter(a_examples))) != EXPECTED_K:
        raise ValueError("A: fixed-random example set is not fixed at K=5")
    for config_name in ("B", "C", "D"):
        if any(
            len(row.get("example_ids", [])) != EXPECTED_K
            or len(set(row["example_ids"])) != EXPECTED_K
            for row in stage_rows[config_name]
        ):
            raise ValueError(f"{config_name}: invalid per-query K=5 examples")
    if any(
        len(row.get("rag_passage_ids", [])) != 3
        or len(row.get("rag_passages", [])) != 3
        for row in stage_rows["D"]
    ):
        raise ValueError("D: RAG top-3 evidence is incomplete")
    rag_self_hits = sum(
        any(
            str(passage_id).split("#chunk-")[0] == row["id"]
            for passage_id in row.get("rag_passage_ids", [])
        )
        for row in stage_rows["D"]
    )
    if rag_self_hits:
        raise ValueError(f"D: found {rag_self_hits} query self-hits in RAG")
    validate_cache_inventory(extraction_cache, cache_index, label="extraction")

    drop_audit: list[dict[str, Any]] = []
    verification: dict[str, Any] = {}
    for config_name, spec in VERIFICATION_CONFIGS.items():
        stem = str(spec["stem"])
        source_config = str(spec["source_config"])
        config_path = config_dir / f"cluener_{stem}_verify.yaml"
        summary_path = result_dir / f"{stem}_verified_summary.json"
        per_query_path = result_dir / f"{stem}_verified_per_query.jsonl"
        config = read_yaml(config_path)
        validate_common_config(config, name=config_name)
        if config.get("source_config") != source_config:
            raise ValueError(f"{config_name}: source_config mismatch")
        file_config_hash = sha256_file(config_path)
        config_hashes[config_name] = file_config_hash
        run_summary = read_json(summary_path)
        rows = read_jsonl(per_query_path)
        validate_rows(
            rows,
            config=config_name,
            prediction_fields=("pred_raw", "pred_verified"),
        )
        source_rows = stage_rows[source_config]
        if [row["id"] for row in rows] != [row["id"] for row in source_rows]:
            raise ValueError(f"{config_name}: source row order mismatch")
        for row, source in zip(rows, source_rows):
            if row.get("source_config") != source_config:
                raise ValueError(f"{config_name}/{row['id']}: source label mismatch")
            if row["gold"] != source["gold"] or row["pred_raw"] != source["pred_raw"]:
                raise ValueError(f"{config_name}/{row['id']}: source row changed")
            validate_verified_contract(
                row,
                evidence_mode=str(spec["evidence_mode"]),
                evidence_count=int(spec["evidence_count"]),
            )
            for decision in row["verifier_decisions"]:
                entry = validate_cache_entry(
                    cache_root=verification_cache,
                    request_digest=str(decision.get("request_hash", "")),
                    raw_digest=str(decision.get("raw_output_hash", "")),
                    expected_prompt_digest=str(decision.get("prompt_hash", "")),
                    phase="verification",
                )
                request_digest = str(decision["request_hash"])
                existing = cache_index.setdefault(request_digest, entry)
                if existing != entry:
                    raise ValueError(f"cache request {request_digest}: conflicting metadata")

        if run_summary.get("config_sha256") != file_config_hash:
            raise ValueError(f"{config_name}: config SHA256 mismatch")
        if run_summary.get("per_query_sha256") != sha256_file(per_query_path):
            raise ValueError(f"{config_name}: per-query SHA256 mismatch")
        source_path = result_dir / f"{spec['source_stem']}_stage_n_per_query.jsonl"
        if run_summary.get("input_per_query_sha256") != sha256_file(source_path):
            raise ValueError(f"{config_name}: source SHA256 mismatch")

        raw_metrics = recompute_entity_metrics(rows, prediction_field="pred_raw")
        verified_metrics = recompute_entity_metrics(
            rows, prediction_field="pred_verified"
        )
        assert_metric_tree_matches(
            run_summary.get("raw_entity_micro"),
            raw_metrics,
            label=f"{config_name}.raw_entity",
        )
        assert_metric_tree_matches(
            run_summary.get("verified_entity_micro"),
            verified_metrics,
            label=f"{config_name}.verified_entity",
        )
        decisions = [
            decision for row in rows for decision in row["verifier_decisions"]
        ]
        atomic_units = len(decisions)
        invalid_units = sum(decision.get("valid_answer") is not True for decision in decisions)
        valid_no_entities = sum(
            decision.get("valid_answer") is True and decision.get("decision") == "no"
            for decision in decisions
        )
        if run_summary.get("atomic_units") != atomic_units:
            raise ValueError(f"{config_name}: atomic unit count mismatch")
        if run_summary.get("invalid_units_kept") != invalid_units:
            raise ValueError(f"{config_name}: invalid unit count mismatch")
        if run_summary.get("valid_no_entities") != valid_no_entities:
            raise ValueError(f"{config_name}: valid-no count mismatch")
        if run_summary.get("valid_no_relations") != 0:
            raise ValueError(f"{config_name}: CLUENER relation verifier count is nonzero")

        audit = build_entity_drop_audit(rows, config=config_name)
        if len(audit) != valid_no_entities:
            raise ValueError(f"{config_name}: deletion audit count mismatch")
        drop_audit.extend(audit)
        drop_stats = drop_statistics(audit)
        delta = metric_delta(verified_metrics, raw_metrics)
        verification[config_name] = {
            "source_config": source_config,
            "rows": len(rows),
            "atomic_entity_units": atomic_units,
            "invalid_units_kept": invalid_units,
            "valid_no_entities": valid_no_entities,
            "raw_entity_micro": raw_metrics,
            "verified_entity_micro": verified_metrics,
            "entity_delta": delta,
            "raw_per_type": per_type_metrics(rows, prediction_field="pred_raw"),
            "verified_per_type": per_type_metrics(
                rows, prediction_field="pred_verified"
            ),
            "drop_audit": drop_stats,
            "positive_claim_gate": {
                "passes": drop_stats["passes_70_percent"] and delta["f1"] > 0,
                "drop_audit_passes": drop_stats["passes_70_percent"],
                "f1_delta_positive": delta["f1"] > 0,
            },
            "cache_hits": sum(decision.get("cache_hit") is True for decision in decisions),
            "elapsed_seconds": run_summary.get("elapsed_seconds"),
            "latency_ms": latency_report(rows, ("latency_verifier_ms",)),
            "config_sha256": file_config_hash,
            "input_per_query_sha256": run_summary["input_per_query_sha256"],
            "per_query_sha256": run_summary["per_query_sha256"],
        }

    verification_references = {
        digest: metadata
        for digest, metadata in cache_index.items()
        if metadata["phase"] == "verification"
    }
    extraction_references = {
        digest: metadata
        for digest, metadata in cache_index.items()
        if metadata["phase"] == "extraction"
    }
    validate_cache_inventory(
        verification_cache, verification_references, label="verification"
    )

    all_parse_below_five = all(
        row["parse_failure_rate"] < 0.05 for row in cdev1
    )
    summary = {
        "status": "completed_with_negative_verification_evidence",
        "phase": PHASE,
        "human_gate": GATE,
        "dataset": "cluener",
        "split": "cluener_tune_subset50_seed42",
        "rows_per_config": EXPECTED_ROWS,
        "k": EXPECTED_K,
        "seed": EXPECTED_SEED,
        "config_sha256": config_hashes,
        "resource_locks": config_locks,
        "unique_resource_sha256": resource_hashes,
        "query_path": str(query_path),
        "query_sha256": sha256_file(query_path),
        "cdev1": cdev1,
        "clean_comparisons": {
            "a_fixed_random_k5": True,
            "c_and_d_replay_b_example_ids": True,
            "d_rag_top3_every_row": True,
            "d_rag_query_self_hits": rag_self_hits,
        },
        "cdev1_gate": {
            "all_50_rows_reload": True,
            "all_parse_failure_rates_below_5_percent": all_parse_below_five,
            "unsupported_entity_types": 0,
            "resource_hashes_verified": True,
            "config_and_per_query_hashes_verified": True,
            "passes": all_parse_below_five,
        },
        "cdev2": verification,
        "cache_integrity": {
            "extraction_referenced_requests": len(extraction_references),
            "extraction_cache_files": len(list(extraction_cache.rglob("*.json"))),
            "verification_referenced_requests": len(verification_references),
            "verification_cache_files": len(list(verification_cache.rglob("*.json"))),
            "all_prompts_preserved": True,
            "all_raw_outputs_preserved": True,
            "all_raw_responses_preserved": True,
            "no_missing_or_orphaned_cache_files": True,
        },
        "verifier_drop_audit_rows": len(drop_audit),
        "observable_cost": load_run_window(log_dir, hourly_rate),
        "evidence_accounting": {
            "f4b_tune_sanity_rows": 6,
            "final_matrix_cells_completed": 0,
            "final_matrix_cells_total": 60,
        },
        "claim_boundary": {
            "public_final_generalization_supported": False,
            "positive_verification_supported": False,
            "reason": (
                "F4b is tune-only; E-prime lowers F1 and both verifier deletion "
                "audits are below the 70% positive-claim threshold."
            ),
        },
    }
    return summary, drop_audit, sorted(cache_index.values(), key=lambda row: (row["phase"], row["request_hash"]))


def main() -> int:
    args = parse_args()
    summary, drop_audit, cache_index = summarize(
        config_dir=Path(args.config_dir),
        result_dir=Path(args.result_dir),
        cache_dir=Path(args.cache_dir),
        log_dir=Path(args.log_dir),
        hourly_rate=args.hourly_rate,
    )
    output_dir = Path(args.output_dir)
    write_json_atomic(output_dir / "full_ie_f4b_summary.json", summary)
    write_jsonl_atomic(
        output_dir / "verifier_entity_drop_audit_all.jsonl", drop_audit
    )
    write_jsonl_atomic(output_dir / "cache_index.jsonl", cache_index)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
