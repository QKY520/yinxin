#!/usr/bin/env python3
"""Validate and summarize the bounded FULL-IE F4a domain-dev sanity."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import entity_micro_counts  # noqa: E402
from equipment_ie.full_ie import (  # noqa: E402
    DEFAULT_RELATION_TYPES,
    relation_evaluation_report,
)
from equipment_ie.schema import validate_record  # noqa: E402


CONFIGS = (("E-prime", "eprime"), ("E", "e"))
AUDIT_THRESHOLD = 0.70
EXPECTED_ROWS = 50
EXPECTED_K = 5
EXPECTED_SEED = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-n-dir", required=True)
    parser.add_argument("--stage-r-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--audit-limit", type=int, default=20)
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
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: every row must be an object")
    return rows


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
                handle.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def entity_key(entity: Mapping[str, Any]) -> tuple[int, int, str]:
    return (int(entity["start"]), int(entity["end"]), str(entity["type"]))


def relation_key(record: Mapping[str, Any], relation_index: int) -> tuple[Any, ...]:
    relation = record["relations"][relation_index]
    head = record["entities"][int(relation["head"])]
    tail = record["entities"][int(relation["tail"])]
    return (
        int(head["start"]),
        int(head["end"]),
        str(head["type"]),
        str(relation["type"]),
        int(tail["start"]),
        int(tail["end"]),
        str(tail["type"]),
    )


def relation_payload(record: Mapping[str, Any], relation_index: int) -> dict[str, Any]:
    relation = record["relations"][relation_index]
    head = record["entities"][int(relation["head"])]
    tail = record["entities"][int(relation["tail"])]
    return {
        "type": relation["type"],
        "head": {
            "span": head["span"],
            "start": head["start"],
            "end": head["end"],
            "type": head["type"],
        },
        "tail": {
            "span": tail["span"],
            "start": tail["start"],
            "end": tail["end"],
            "type": tail["type"],
        },
    }


def validate_run_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    config: str,
    prediction_fields: Sequence[str],
) -> None:
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"{config}: expected {EXPECTED_ROWS} rows, found {len(rows)}")
    seen: set[str] = set()
    for row in rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"{config}: row id must be a non-empty string")
        if record_id in seen:
            raise ValueError(f"{config}: duplicate row id {record_id}")
        seen.add(record_id)
        if row.get("dataset") != "domain" or row.get("config") != config:
            raise ValueError(f"{config}/{record_id}: dataset or config mismatch")
        if row.get("k") != EXPECTED_K or row.get("seed") != EXPECTED_SEED:
            raise ValueError(f"{config}/{record_id}: expected K=5 and seed=42")
        gold = row.get("gold")
        if not isinstance(gold, Mapping):
            raise ValueError(f"{config}/{record_id}: gold must be an object")
        validate_record(gold)
        if gold["id"] != record_id:
            raise ValueError(f"{config}/{record_id}: gold id mismatch")
        for field in prediction_fields:
            prediction = row.get(field)
            if not isinstance(prediction, Mapping):
                raise ValueError(f"{config}/{record_id}: {field} must be an object")
            validate_record(prediction)
            if prediction["id"] != record_id or prediction["text"] != gold["text"]:
                raise ValueError(f"{config}/{record_id}: {field} id/text mismatch")


def recompute_reports(
    rows: Sequence[Mapping[str, Any]],
    *,
    prediction_field: str,
    include_relations: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    gold_records = [row["gold"] for row in rows]
    pred_records = [row[prediction_field] for row in rows]
    entity_report = entity_micro_counts(gold_records, pred_records).report()
    relation_report = (
        relation_evaluation_report(
            gold_records,
            pred_records,
            relation_types=tuple(DEFAULT_RELATION_TYPES),
        )
        if include_relations
        else None
    )
    return entity_report, relation_report


def assert_metric_tree_matches(
    expected: Any,
    recomputed: Any,
    *,
    label: str,
) -> None:
    if isinstance(expected, Mapping) and isinstance(recomputed, Mapping):
        if set(expected) != set(recomputed):
            raise ValueError(
                f"{label}: metric keys differ: expected={sorted(expected)}, "
                f"recomputed={sorted(recomputed)}"
            )
        for key in expected:
            assert_metric_tree_matches(
                expected[key], recomputed[key], label=f"{label}.{key}"
            )
        return
    if (
        isinstance(expected, (int, float))
        and not isinstance(expected, bool)
        and isinstance(recomputed, (int, float))
        and not isinstance(recomputed, bool)
    ):
        if not math.isclose(float(expected), float(recomputed), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"{label}: expected {expected}, recomputed {recomputed}")
        return
    if expected != recomputed:
        raise ValueError(f"{label}: expected {expected!r}, recomputed {recomputed!r}")


def assert_summary_count(summary: Mapping[str, Any], key: str, value: int, label: str) -> None:
    if summary.get(key) != value:
        raise ValueError(f"{label}.{key}: expected {summary.get(key)!r}, recomputed {value}")


def rows_by_id(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row["id"]): row for row in rows}


def relation_sanitizer_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        flags = row.get("sanitization_flags", [])
        if not isinstance(flags, list):
            raise ValueError(f"row {row.get('id')}: sanitization_flags must be a list")
        for flag in flags:
            if not isinstance(flag, Mapping):
                raise ValueError(f"row {row.get('id')}: sanitizer flag must be an object")
            kind = str(flag.get("kind", ""))
            if kind.startswith("RELATION_DROPPED_"):
                counts[kind] += 1
    return dict(sorted(counts.items()))


def build_drop_audit(rows: Sequence[Mapping[str, Any]], config: str) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for row in rows:
        pred_raw = row["pred_raw"]
        gold = row["gold"]
        gold_entities = {entity_key(entity) for entity in gold["entities"]}
        gold_relations = {
            relation_key(gold, index) for index in range(len(gold["relations"]))
        }
        explicit_relations: dict[int, Mapping[str, Any]] = {}
        seen_decisions: set[tuple[str, int]] = set()
        for decision in row.get("verifier_decisions", []):
            kind = str(decision["unit_kind"])
            index = int(decision["unit_index"])
            decision_key = (kind, index)
            if decision_key in seen_decisions:
                raise ValueError(f"row {row['id']}: duplicate verifier decision {decision_key}")
            seen_decisions.add(decision_key)
            if decision.get("decision") != "no" or decision.get("valid_answer") is not True:
                continue
            common = {
                "config": config,
                "id": row["id"],
                "text": pred_raw["text"],
                "unit_index": index,
                "request_hash": decision.get("request_hash"),
                "raw_output_hash": decision.get("raw_output_hash"),
                "evidence_mode": decision.get("evidence_mode"),
            }
            if kind == "entity":
                if not 0 <= index < len(pred_raw["entities"]):
                    raise ValueError(f"row {row['id']}: entity decision index out of range")
                entity = pred_raw["entities"][index]
                exact_gold_match = entity_key(entity) in gold_entities
                audit.append(
                    {
                        **common,
                        "unit_class": "entity",
                        "drop_mode": "verifier_no",
                        "unit": dict(entity),
                        "exact_gold_match": exact_gold_match,
                        "correct_drop": not exact_gold_match,
                    }
                )
            elif kind == "relation":
                if not 0 <= index < len(pred_raw["relations"]):
                    raise ValueError(f"row {row['id']}: relation decision index out of range")
                explicit_relations[index] = decision
            else:
                raise ValueError(f"row {row['id']}: unsupported unit kind {kind!r}")

        cascade = {int(index) for index in row.get("verifier_cascade_dropped_relation_indices", [])}
        if any(not 0 <= index < len(pred_raw["relations"]) for index in cascade):
            raise ValueError(f"row {row['id']}: cascade relation index out of range")
        for index in sorted(set(explicit_relations) | cascade):
            exact_gold_match = relation_key(pred_raw, index) in gold_relations
            decision = explicit_relations.get(index)
            if index in explicit_relations and index in cascade:
                drop_mode = "verifier_no_and_cascade"
            elif index in explicit_relations:
                drop_mode = "verifier_no"
            else:
                drop_mode = "entity_cascade"
            audit.append(
                {
                    "config": config,
                    "id": row["id"],
                    "text": pred_raw["text"],
                    "unit_class": "relation",
                    "drop_mode": drop_mode,
                    "unit_index": index,
                    "unit": relation_payload(pred_raw, index),
                    "request_hash": decision.get("request_hash") if decision else None,
                    "raw_output_hash": decision.get("raw_output_hash") if decision else None,
                    "evidence_mode": decision.get("evidence_mode") if decision else None,
                    "exact_gold_match": exact_gold_match,
                    "correct_drop": not exact_gold_match,
                }
            )
    return sorted(
        audit,
        key=lambda item: (
            str(item["config"]),
            str(item["unit_class"]),
            str(item["id"]),
            int(item["unit_index"]),
        ),
    )


def select_even_sample(items: Sequence[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    if len(items) <= limit:
        return list(items)
    if limit == 1:
        return [items[0]]
    last = len(items) - 1
    indices = [round(index * last / (limit - 1)) for index in range(limit)]
    return [items[index] for index in indices]


def audit_statistics(audit: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for config, _stem in CONFIGS:
        config_result: dict[str, Any] = {}
        for unit_class in ("entity", "relation"):
            units = [
                item
                for item in audit
                if item["config"] == config and item["unit_class"] == unit_class
            ]
            correct = sum(bool(item["correct_drop"]) for item in units)
            mode_counts = Counter(str(item["drop_mode"]) for item in units)
            config_result[unit_class] = {
                "drops": len(units),
                "correct_drops": correct,
                "wrong_drops": len(units) - correct,
                "correct_drop_rate": correct / len(units) if units else None,
                "passes_70_percent": bool(units) and correct / len(units) >= AUDIT_THRESHOLD,
                "drop_modes": dict(sorted(mode_counts.items())),
            }
        result[config] = config_result
    return result


def metric_delta(verified: Mapping[str, Any], raw: Mapping[str, Any]) -> dict[str, float]:
    return {
        name: float(verified[name]) - float(raw[name])
        for name in ("precision", "recall", "f1")
    }


def summarize(
    *,
    stage_n_dir: Path,
    stage_r_dir: Path,
    audit_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    ddev1: list[dict[str, Any]] = []
    relation_parse_failures = 0
    aggregate_sanitizer_counts: Counter[str] = Counter()
    stage_r_rows_by_stem: dict[str, list[dict[str, Any]]] = {}
    for variant in "abcd":
        config = variant.upper()
        stage_n_summary_path = stage_n_dir / f"{variant}_stage_n_summary.json"
        stage_n_per_query_path = stage_n_dir / f"{variant}_stage_n_per_query.jsonl"
        stage_r_summary_path = stage_r_dir / f"{variant}_stage_r_summary.json"
        stage_r_per_query_path = stage_r_dir / f"{variant}_stage_r_per_query.jsonl"
        stage_n = read_json(stage_n_summary_path)
        stage_r = read_json(stage_r_summary_path)
        stage_n_rows = read_jsonl(stage_n_per_query_path)
        stage_r_rows = read_jsonl(stage_r_per_query_path)
        validate_run_rows(
            stage_n_rows, config=config, prediction_fields=("pred_raw",)
        )
        validate_run_rows(
            stage_r_rows, config=config, prediction_fields=("pred_raw",)
        )
        if sha256_file(stage_n_per_query_path) != stage_n.get("per_query_sha256"):
            raise ValueError(f"{config}: Stage N per-query hash mismatch")
        if sha256_file(stage_r_per_query_path) != stage_r.get("per_query_sha256"):
            raise ValueError(f"{config}: Stage R per-query hash mismatch")
        if stage_r.get("source_stage_n_sha256") != stage_n.get("per_query_sha256"):
            raise ValueError(f"{config}: Stage R source Stage N hash mismatch")

        stage_n_by_id = rows_by_id(stage_n_rows)
        for row in stage_r_rows:
            source = stage_n_by_id[str(row["id"])]
            if row["gold"] != source["gold"]:
                raise ValueError(f"{config}/{row['id']}: Stage N/R gold mismatch")
            if row["pred_raw"]["entities"] != source["pred_raw"]["entities"]:
                raise ValueError(f"{config}/{row['id']}: Stage R changed Stage N entities")

        stage_n_entity, _ = recompute_reports(
            stage_n_rows, prediction_field="pred_raw", include_relations=False
        )
        stage_r_entity, stage_r_relation = recompute_reports(
            stage_r_rows, prediction_field="pred_raw", include_relations=True
        )
        assert_metric_tree_matches(
            stage_n["entity_micro"], stage_n_entity, label=f"{config}.stage_n.entity"
        )
        assert_metric_tree_matches(
            stage_r["entity_micro"], stage_r_entity, label=f"{config}.stage_r.entity"
        )
        assert_metric_tree_matches(
            stage_r["relation"], stage_r_relation, label=f"{config}.stage_r.relation"
        )
        assert_metric_tree_matches(
            stage_n_entity, stage_r_entity, label=f"{config}.stage_n_vs_stage_r.entity"
        )
        stage_n_parse_failures = sum(bool(row.get("parse_failure")) for row in stage_n_rows)
        stage_r_parse_failures = sum(
            bool(row.get("parse_failure_relation")) for row in stage_r_rows
        )
        assert_summary_count(stage_n, "parse_failures", stage_n_parse_failures, config)
        assert_summary_count(
            stage_r, "parse_failures_relation", stage_r_parse_failures, config
        )
        sanitizer_counts = relation_sanitizer_counts(stage_r_rows)
        aggregate_sanitizer_counts.update(sanitizer_counts)
        relation_parse_failures += stage_r_parse_failures
        stage_r_rows_by_stem[variant] = stage_r_rows
        ddev1.append(
            {
                "config": config,
                "entity_micro": stage_n_entity,
                "relation": stage_r_relation,
                "entity_parse_failures": stage_n_parse_failures,
                "relation_parse_failures": stage_r_parse_failures,
                "relation_parse_failure_rate": stage_r_parse_failures / EXPECTED_ROWS,
                "relation_parse_failure_below_5_percent": (
                    stage_r_parse_failures / EXPECTED_ROWS < 0.05
                ),
                "relation_sanitizer_events": sanitizer_counts,
                "stage_n_elapsed_seconds": stage_n["elapsed_seconds"],
                "stage_r_elapsed_seconds": stage_r["elapsed_seconds"],
                "stage_n_timing_means_ms": stage_n.get("timing_means_ms", {}),
                "stage_n_per_query_sha256": stage_n["per_query_sha256"],
                "stage_r_per_query_sha256": stage_r["per_query_sha256"],
            }
        )

    all_audit: list[dict[str, Any]] = []
    verification: dict[str, Any] = {}
    for config, stem in CONFIGS:
        summary_path = stage_r_dir / f"{stem}_verified_summary.json"
        per_query_path = stage_r_dir / f"{stem}_verified_per_query.jsonl"
        summary = read_json(summary_path)
        rows = read_jsonl(per_query_path)
        validate_run_rows(
            rows, config=config, prediction_fields=("pred_raw", "pred_verified")
        )
        if len(rows) != summary.get("rows"):
            raise ValueError(f"{config}: verified summary row count mismatch")
        if sha256_file(per_query_path) != summary.get("per_query_sha256"):
            raise ValueError(f"{config}: per-query hash mismatch")
        source_stem = "c" if config == "E-prime" else "d"
        source_rows = stage_r_rows_by_stem[source_stem]
        source_by_id = rows_by_id(source_rows)
        source_hash = sha256_file(stage_r_dir / f"{source_stem}_stage_r_per_query.jsonl")
        if summary.get("input_per_query_sha256") != source_hash:
            raise ValueError(f"{config}: source Stage R hash mismatch")
        for row in rows:
            source = source_by_id[str(row["id"])]
            if row["gold"] != source["gold"] or row["pred_raw"] != source["pred_raw"]:
                raise ValueError(f"{config}/{row['id']}: source Stage R row mismatch")

        raw_entity, raw_relation = recompute_reports(
            rows, prediction_field="pred_raw", include_relations=True
        )
        verified_entity, verified_relation = recompute_reports(
            rows, prediction_field="pred_verified", include_relations=True
        )
        assert_metric_tree_matches(
            summary["raw_entity_micro"], raw_entity, label=f"{config}.raw_entity"
        )
        assert_metric_tree_matches(
            summary["verified_entity_micro"],
            verified_entity,
            label=f"{config}.verified_entity",
        )
        assert_metric_tree_matches(
            summary["raw_relation"], raw_relation, label=f"{config}.raw_relation"
        )
        assert_metric_tree_matches(
            summary["verified_relation"],
            verified_relation,
            label=f"{config}.verified_relation",
        )
        decisions = [
            decision for row in rows for decision in row.get("verifier_decisions", [])
        ]
        atomic_units = len(decisions)
        invalid_units = sum(decision.get("valid_answer") is not True for decision in decisions)
        valid_no_entities = sum(
            decision.get("unit_kind") == "entity"
            and decision.get("decision") == "no"
            and decision.get("valid_answer") is True
            for decision in decisions
        )
        valid_no_relations = sum(
            decision.get("unit_kind") == "relation"
            and decision.get("decision") == "no"
            and decision.get("valid_answer") is True
            for decision in decisions
        )
        cascade_drops = sum(
            len(row.get("verifier_cascade_dropped_relation_indices", [])) for row in rows
        )
        for key, value in (
            ("atomic_units", atomic_units),
            ("invalid_units_kept", invalid_units),
            ("valid_no_entities", valid_no_entities),
            ("valid_no_relations", valid_no_relations),
            ("cascade_dropped_relations", cascade_drops),
        ):
            assert_summary_count(summary, key, value, config)
        audit = build_drop_audit(rows, config)
        all_audit.extend(audit)
        verification[config] = {
            "summary_path": str(summary_path),
            "per_query_sha256": summary["per_query_sha256"],
            "atomic_units": atomic_units,
            "invalid_units_kept": invalid_units,
            "valid_no_entities": valid_no_entities,
            "valid_no_relations": valid_no_relations,
            "cascade_dropped_relations": cascade_drops,
            "raw_entity_micro": raw_entity,
            "verified_entity_micro": verified_entity,
            "entity_delta": metric_delta(verified_entity, raw_entity),
            "raw_relation_micro": raw_relation["exact_relation_micro"],
            "verified_relation_micro": verified_relation["exact_relation_micro"],
            "relation_delta": metric_delta(
                verified_relation["exact_relation_micro"],
                raw_relation["exact_relation_micro"],
            ),
        }

    audit_stats = audit_statistics(all_audit)
    samples: list[dict[str, Any]] = []
    for config, _stem in CONFIGS:
        for unit_class in ("entity", "relation"):
            group = [
                item
                for item in all_audit
                if item["config"] == config and item["unit_class"] == unit_class
            ]
            samples.extend(select_even_sample(group, audit_limit))

    for config, _stem in CONFIGS:
        verification[config]["drop_audit"] = audit_stats[config]
        entity_pass = audit_stats[config]["entity"]["passes_70_percent"]
        relation_pass = audit_stats[config]["relation"]["passes_70_percent"]
        positive_delta = (
            verification[config]["entity_delta"]["f1"] > 0
            or verification[config]["relation_delta"]["f1"] > 0
        )
        verification[config]["positive_claim_gate"] = {
            "passes": entity_pass and relation_pass and positive_delta,
            "entity_drop_audit_passes": entity_pass,
            "relation_drop_audit_passes": relation_pass,
            "has_positive_f1_delta": positive_delta,
        }

    per_config_parse_gate = all(
        bool(row["relation_parse_failure_below_5_percent"]) for row in ddev1
    )
    all_relation_f1_nonzero = all(
        float(row["relation"]["exact_relation_micro"]["f1"]) > 0.0 for row in ddev1
    )
    summary = {
        "status": "completed_with_limitations",
        "phase": "FULL_IE_F4A_DOMAIN_DEV_SANITY",
        "audit_threshold": AUDIT_THRESHOLD,
        "ddev1": ddev1,
        "aggregate_relation_parse_failures": relation_parse_failures,
        "aggregate_relation_rows": EXPECTED_ROWS * 4,
        "aggregate_relation_parse_failure_rate": relation_parse_failures / (EXPECTED_ROWS * 4),
        "relation_sanitizer_events": dict(sorted(aggregate_sanitizer_counts.items())),
        "ddev1_gate": {
            "all_rows_reload": True,
            "all_relation_f1_nonzero": all_relation_f1_nonzero,
            "aggregate_relation_parse_failure_below_5_percent": (
                relation_parse_failures / (EXPECTED_ROWS * 4) < 0.05
            ),
            "every_config_relation_parse_failure_below_5_percent": per_config_parse_gate,
        },
        "verification": verification,
        "audit_all_rows": len(all_audit),
        "audit_sample_rows": len(samples),
    }
    return summary, all_audit, samples


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    summary, all_audit, samples = summarize(
        stage_n_dir=Path(args.stage_n_dir),
        stage_r_dir=Path(args.stage_r_dir),
        audit_limit=args.audit_limit,
    )
    write_json_atomic(output_dir / "full_ie_f4a_summary.json", summary)
    write_jsonl_atomic(output_dir / "verifier_drop_audit_all.jsonl", all_audit)
    write_jsonl_atomic(output_dir / "verifier_drop_audit_sample.jsonl", samples)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
