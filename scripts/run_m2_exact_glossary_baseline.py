#!/usr/bin/env python3
"""Run the approved deterministic exact-glossary baseline on domain dev.

This runner never contacts a model. It validates locked input hashes, refuses
frozen-test paths and visible GPUs, then writes exact span-plus-type results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import entity_micro_counts  # noqa: E402
from equipment_ie.schema import (  # noqa: E402
    iter_jsonl,
    sha256_file,
    validate_record,
    write_jsonl_atomic,
)


M2_GATE = "M2_BASELINE_PREP_APPROVED"


@dataclass(frozen=True)
class GlossarySurface:
    surface: str
    entity_type: str
    priority: int
    entry_index: int
    canonical_term: str
    source_kind: str


@dataclass(frozen=True)
class MatchCandidate:
    start: int
    end: int
    surface: str
    entity_type: str
    priority: int
    entry_index: int
    canonical_term: str
    source_kind: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the deterministic exact glossary/alias baseline."
    )
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
        raise ValueError(f"{path}: expected a YAML object")
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


def write_rows_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(
                    json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                )
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def require_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA256 mismatch: expected {expected}, got {actual}")
    return actual


def validate_execution_scope(config: Mapping[str, Any]) -> None:
    execution = config.get("execution")
    if not isinstance(execution, Mapping):
        raise ValueError("execution must be an object")
    if execution.get("authorized") is not True:
        raise RuntimeError("M2 baseline config is not authorized")
    if execution.get("human_gate") != M2_GATE:
        raise RuntimeError(f"human_gate must be {M2_GATE}")
    if execution.get("model_calls_allowed") is not False:
        raise RuntimeError("model_calls_allowed must be false")
    if execution.get("gpu_required") is not False:
        raise RuntimeError("gpu_required must be false")
    if gpu_visible():
        raise RuntimeError("GPU is visible; M2 exact-glossary baseline requires no-card mode")

    data = config.get("data")
    if not isinstance(data, Mapping) or data.get("dataset") != "domain_dev50":
        raise ValueError("M2 exact-glossary baseline is locked to domain_dev50")
    query_path = str(data.get("query_path", ""))
    forbidden = data.get("forbidden_path_fragments", ["domain_test"])
    if not isinstance(forbidden, Sequence) or isinstance(forbidden, str):
        raise ValueError("data.forbidden_path_fragments must be a list")
    if any(str(fragment) and str(fragment) in query_path for fragment in forbidden):
        raise RuntimeError("refusing a query path containing a frozen-test fragment")


def _as_priority(value: Any, *, entry_index: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"glossary entry {entry_index}: priority must be an integer") from exc


def compile_glossary_surfaces(
    records: Sequence[Mapping[str, Any]],
    *,
    allowed_types: Sequence[str],
    min_surface_chars: int,
    include_terms: bool,
    include_aliases: bool,
) -> list[GlossarySurface]:
    if min_surface_chars <= 0:
        raise ValueError("min_surface_chars must be positive")
    allowed = set(allowed_types)
    if not allowed:
        raise ValueError("allowed_types must not be empty")

    candidates: list[GlossarySurface] = []
    for entry_index, record in enumerate(records):
        term = record.get("term")
        entity_type = record.get("type")
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"glossary entry {entry_index}: term must be non-empty")
        if entity_type not in allowed:
            raise ValueError(
                f"glossary entry {entry_index}: unsupported type {entity_type!r}"
            )
        priority = _as_priority(record.get("priority", 0), entry_index=entry_index)
        raw_surfaces: list[tuple[str, str]] = []
        if include_terms:
            raw_surfaces.append((term, "term"))
        aliases = record.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        if not isinstance(aliases, list):
            raise ValueError(f"glossary entry {entry_index}: aliases must be a list")
        if include_aliases:
            for alias in aliases:
                if not isinstance(alias, str) or not alias.strip():
                    raise ValueError(
                        f"glossary entry {entry_index}: aliases must be non-empty strings"
                    )
                raw_surfaces.append((alias, "alias"))
        for surface, source_kind in raw_surfaces:
            if len(surface) < min_surface_chars:
                continue
            candidates.append(
                GlossarySurface(
                    surface=surface,
                    entity_type=str(entity_type),
                    priority=priority,
                    entry_index=entry_index,
                    canonical_term=term,
                    source_kind=source_kind,
                )
            )

    types_by_surface: dict[str, set[str]] = {}
    for candidate in candidates:
        types_by_surface.setdefault(candidate.surface, set()).add(candidate.entity_type)
    conflicts = {
        surface: sorted(types)
        for surface, types in types_by_surface.items()
        if len(types) > 1
    }
    if conflicts:
        raise ValueError(f"glossary surfaces have conflicting types: {conflicts}")

    deduplicated: dict[tuple[str, str], GlossarySurface] = {}
    for candidate in candidates:
        key = (candidate.surface, candidate.entity_type)
        previous = deduplicated.get(key)
        rank = (
            -candidate.priority,
            0 if candidate.source_kind == "term" else 1,
            candidate.entry_index,
            candidate.canonical_term,
        )
        if previous is None:
            deduplicated[key] = candidate
            continue
        previous_rank = (
            -previous.priority,
            0 if previous.source_kind == "term" else 1,
            previous.entry_index,
            previous.canonical_term,
        )
        if rank < previous_rank:
            deduplicated[key] = candidate
    if not deduplicated:
        raise ValueError("glossary produced no eligible surfaces")
    return sorted(
        deduplicated.values(),
        key=lambda item: (
            -len(item.surface),
            -item.priority,
            item.surface,
            item.entity_type,
            item.entry_index,
        ),
    )


def exact_glossary_match(
    text: str,
    surfaces: Sequence[GlossarySurface],
    *,
    type_order: Sequence[str],
) -> dict[str, Any]:
    type_rank = {entity_type: index for index, entity_type in enumerate(type_order)}
    candidates: dict[tuple[int, int, str], MatchCandidate] = {}
    for item in surfaces:
        cursor = 0
        while True:
            start = text.find(item.surface, cursor)
            if start < 0:
                break
            end = start + len(item.surface)
            key = (start, end, item.entity_type)
            candidates.setdefault(
                key,
                MatchCandidate(
                    start=start,
                    end=end,
                    surface=item.surface,
                    entity_type=item.entity_type,
                    priority=item.priority,
                    entry_index=item.entry_index,
                    canonical_term=item.canonical_term,
                    source_kind=item.source_kind,
                ),
            )
            cursor = start + 1

    ranked = sorted(
        candidates.values(),
        key=lambda item: (
            -(item.end - item.start),
            -item.priority,
            item.start,
            item.surface,
            type_rank.get(item.entity_type, len(type_rank)),
            item.entry_index,
        ),
    )
    occupied = [False] * len(text)
    selected: list[MatchCandidate] = []
    for candidate in ranked:
        if any(occupied[candidate.start : candidate.end]):
            continue
        occupied[candidate.start : candidate.end] = [True] * (
            candidate.end - candidate.start
        )
        selected.append(candidate)
    selected.sort(
        key=lambda item: (
            item.start,
            item.end,
            type_rank.get(item.entity_type, len(type_rank)),
            item.surface,
        )
    )
    return {
        "entities": [
            {
                "start": item.start,
                "end": item.end,
                "type": item.entity_type,
                "span": item.surface,
            }
            for item in selected
        ],
        "candidate_matches": len(candidates),
        "overlap_dropped": len(candidates) - len(selected),
        "matched_surfaces": [
            {
                "surface": item.surface,
                "type": item.entity_type,
                "canonical_term": item.canonical_term,
                "source_kind": item.source_kind,
                "priority": item.priority,
            }
            for item in selected
        ],
    }


def entity_keys(record: Mapping[str, Any], entity_type: str | None = None) -> set[tuple[int, int, str]]:
    return {
        (int(entity["start"]), int(entity["end"]), str(entity["type"]))
        for entity in record["entities"]
        if entity_type is None or entity["type"] == entity_type
    }


def metric_report(tp: int, fp: int, fn: int, passages: int) -> dict[str, float | int]:
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
        "fdr": fp / (tp + fp) if tp + fp else 0.0,
        "fp_per_passage": fp / passages if passages else 0.0,
    }


def evaluate_records(
    gold_records: Sequence[Mapping[str, Any]],
    predictions: Sequence[Mapping[str, Any]],
    *,
    entity_types: Sequence[str],
) -> dict[str, Any]:
    pred_by_id = {str(record["id"]): record for record in predictions}
    if len(pred_by_id) != len(predictions):
        raise ValueError("prediction IDs must be unique")
    if set(pred_by_id) != {str(record["id"]) for record in gold_records}:
        raise ValueError("gold and prediction IDs must match exactly")

    overall = entity_micro_counts(gold_records, predictions).report()
    overall_report = metric_report(
        int(overall["tp"]), int(overall["fp"]), int(overall["fn"]), len(gold_records)
    )
    per_type: dict[str, dict[str, float | int]] = {}
    for entity_type in entity_types:
        tp = fp = fn = 0
        for gold in gold_records:
            pred = pred_by_id[str(gold["id"])]
            gold_set = entity_keys(gold, entity_type)
            pred_set = entity_keys(pred, entity_type)
            tp += len(gold_set & pred_set)
            fp += len(pred_set - gold_set)
            fn += len(gold_set - pred_set)
        per_type[entity_type] = metric_report(tp, fp, fn, len(gold_records))

    zero_gold_ids = [
        str(record["id"]) for record in gold_records if not record["entities"]
    ]
    zero_gold_predicted = sum(
        len(pred_by_id[record_id]["entities"]) for record_id in zero_gold_ids
    )
    return {
        "entity_micro": overall_report,
        "per_type": per_type,
        "zero_gold": {
            "passages": len(zero_gold_ids),
            "predicted_entities": zero_gold_predicted,
            "passages_with_predictions": sum(
                bool(pred_by_id[record_id]["entities"]) for record_id in zero_gold_ids
            ),
            "mean_predicted_entities": (
                zero_gold_predicted / len(zero_gold_ids) if zero_gold_ids else 0.0
            ),
        },
    }


def ensure_new_outputs(outputs: Mapping[str, Any]) -> dict[str, Path]:
    required = ("predictions", "per_query", "summary", "manifest")
    paths: dict[str, Path] = {}
    for name in required:
        value = outputs.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"outputs.{name} must be a non-empty path")
        path = Path(value)
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {path}")
        paths[name] = path
    return paths


def analyze(config: Mapping[str, Any], config_path: Path) -> dict[str, Any]:
    validate_execution_scope(config)
    output_paths = ensure_new_outputs(config["outputs"])
    started = time.monotonic()

    data_config = config["data"]
    query_path = Path(str(data_config["query_path"]))
    query_sha256 = require_hash(
        query_path, str(data_config["expected_sha256"]), "domain_dev"
    )
    gold_records = list(iter_jsonl(query_path))
    if len(gold_records) != int(data_config["expected_records"]):
        raise ValueError("domain_dev record count mismatch")

    glossary_config = config["glossary"]
    glossary_path = Path(str(glossary_config["path"]))
    glossary_sha256 = require_hash(
        glossary_path, str(glossary_config["expected_sha256"]), "glossary"
    )
    glossary_records = list(iter_jsonl(glossary_path, validate=False))
    if len(glossary_records) != int(glossary_config["expected_records"]):
        raise ValueError("glossary record count mismatch")

    entity_types = list(config["schema"]["entity_types"])
    matching = config["matching"]
    if matching.get("case_sensitive") is not True:
        raise ValueError("exact baseline requires case_sensitive=true")
    if matching.get("occurrence_policy") != "all":
        raise ValueError("exact baseline requires occurrence_policy=all")
    if matching.get("overlap_policy") != "longest_first_nonoverlap":
        raise ValueError("unexpected overlap policy")
    type_order = list(matching["type_order"])
    if type_order != entity_types:
        raise ValueError("matching.type_order must equal schema entity type order")
    surfaces = compile_glossary_surfaces(
        glossary_records,
        allowed_types=entity_types,
        min_surface_chars=int(matching["min_surface_chars"]),
        include_terms=bool(matching["include_terms"]),
        include_aliases=bool(matching["include_aliases"]),
    )

    predictions: list[dict[str, Any]] = []
    per_query: list[dict[str, Any]] = []
    total_candidates = total_overlap_dropped = 0
    for gold in gold_records:
        match = exact_glossary_match(
            str(gold["text"]), surfaces, type_order=type_order
        )
        prediction = {
            "id": gold["id"],
            "text": gold["text"],
            "entities": match["entities"],
            "relations": [],
        }
        validate_record(prediction)
        predictions.append(prediction)
        gold_set = entity_keys(gold)
        pred_set = entity_keys(prediction)
        per_query.append(
            {
                "id": gold["id"],
                "text_sha256": text_sha256(str(gold["text"])),
                "gold_entities": len(gold_set),
                "predicted_entities": len(pred_set),
                "tp": len(gold_set & pred_set),
                "fp": len(pred_set - gold_set),
                "fn": len(gold_set - pred_set),
                "candidate_matches": match["candidate_matches"],
                "overlap_dropped": match["overlap_dropped"],
                "matched_surfaces": match["matched_surfaces"],
                "prediction": prediction,
            }
        )
        total_candidates += int(match["candidate_matches"])
        total_overlap_dropped += int(match["overlap_dropped"])

    metrics = evaluate_records(
        gold_records, predictions, entity_types=entity_types
    )
    write_jsonl_atomic(output_paths["predictions"], predictions)
    write_rows_atomic(output_paths["per_query"], per_query)
    summary = {
        "phase": "M2",
        "stage": "exact_glossary_domain_dev",
        "status": "complete",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "script_sha256": sha256_file(Path(__file__)),
        "dataset": data_config["dataset"],
        "query_records": len(gold_records),
        "query_sha256": query_sha256,
        "glossary_records": len(glossary_records),
        "glossary_surfaces": len(surfaces),
        "glossary_sha256": glossary_sha256,
        "candidate_matches": total_candidates,
        "overlap_dropped": total_overlap_dropped,
        "selected_predictions": sum(len(row["entities"]) for row in predictions),
        "metrics": metrics,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "safeguards": {
            "human_gate": M2_GATE,
            "gpu_visible": False,
            "model_calls": 0,
            "api_calls": 0,
            "vllm_calls": 0,
            "frozen_test_read": False,
            "labels_modified": False,
            "predictions_modified": False,
            "latex_modified": False,
        },
    }
    write_json_atomic(output_paths["summary"], summary)
    manifest = {
        "phase": "M2",
        "status": "complete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "config": {
                "path": str(config_path),
                "bytes": config_path.stat().st_size,
                "sha256": sha256_file(config_path),
            },
            "script": {
                "path": str(Path(__file__)),
                "bytes": Path(__file__).stat().st_size,
                "sha256": sha256_file(Path(__file__)),
            },
            "domain_dev": {
                "path": str(query_path),
                "bytes": query_path.stat().st_size,
                "sha256": query_sha256,
                "records": len(gold_records),
            },
            "glossary": {
                "path": str(glossary_path),
                "bytes": glossary_path.stat().st_size,
                "sha256": glossary_sha256,
                "records": len(glossary_records),
                "surfaces": len(surfaces),
            },
        },
        "outputs": {
            name: {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for name, path in output_paths.items()
            if name != "manifest"
        },
        "safeguards": summary["safeguards"],
    }
    write_json_atomic(output_paths["manifest"], manifest)
    return summary


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    summary = analyze(load_yaml(config_path), config_path)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
