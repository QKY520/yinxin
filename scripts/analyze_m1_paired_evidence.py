#!/usr/bin/env python3
"""Run the approved M1 paired reanalysis over locked P5 artifacts.

Run only on AutoDL in GPU-free mode. The script reads the existing frozen-test
gold, predictions, summaries, source map, and execution logs for aggregation.
It never changes labels or predictions, builds prompts, imports model code,
contacts an API, or starts GPU work. Outputs contain aggregate statistics only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import random
import shutil
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from uuid import uuid4


EXPECTED_DOMAIN_TEST_SHA256 = (
    "42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0"
)
EXPECTED_SOURCE_MAP_SHA256 = (
    "9b77f3da190371a47196b0e8e1192172801e20d8f12945657da53dabb684e748"
)
EXPECTED_FROZEN_SHA256 = (
    "e12517324c90a7261fcb46df698112dac8f83c2f5c6441e39c4340ada2cee0dd"
)
EXPECTED_ROWS = 170
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 20_260_729
SEEDS = (42, 43, 44)
ENTITY_TYPES = ("EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC")
CONFIGS = ("A", "B", "C", "D")
CONFIG_NAMES = {
    "A": "fixed-random demonstrations",
    "B": "kNN demonstrations",
    "C": "kNN + glossary",
    "D": "kNN + glossary + RAG",
}
EXPECTED_CONFIG_VALUES = {
    "A": "A_fixed_random_domain_test_p5_draft",
    "B": "B_knn_domain_test_p5_draft",
    "C": "C_knn_glossary_domain_test_p5_draft",
    "D": "D_knn_glossary_rag_domain_test_p5_draft",
}
CONTRASTS = (
    ("B-A", "A", "B"),
    ("C-B", "B", "C"),
    ("D-C", "C", "D"),
    ("D-A", "A", "D"),
)
BOOTSTRAP_METRICS = (
    "precision",
    "recall",
    "f1",
    "fp",
    "fdr",
    "fp_per_passage",
)


@dataclass(frozen=True)
class RunSpec:
    config: str
    seed: int
    stem: str
    per_query_sha256: str
    log_name: str

    @property
    def per_query_name(self) -> str:
        return f"{self.stem}_per_query.jsonl"

    @property
    def summary_name(self) -> str:
        return f"{self.stem}_summary.json"


RUN_SPECS = (
    RunSpec(
        "A",
        42,
        "p5_domain_test_a_k5_seed42",
        "343f192e6c5bc2a3bd0c720af1d9241836c01dd53584a454c787a5ccfb99e8ab",
        "p5_domain_test_a_k5_seed42_run.log",
    ),
    RunSpec(
        "A",
        43,
        "p5_domain_test_a_k5_seed43",
        "358ddfac801240260ace896c13a4eced2668245b518c95466efda5e11e38c164",
        "p5_domain_test_a_k5_seed43_approved_20260724_run.log",
    ),
    RunSpec(
        "A",
        44,
        "p5_domain_test_a_k5_seed44",
        "1b46b3213aa95ef2175c80e17324530729eca0a77cb0d518c01134cf0b684310",
        "p5_domain_test_a_k5_seed44_approved_20260724_run.log",
    ),
    RunSpec(
        "B",
        42,
        "p5_domain_test_b_knn_k5_seed42",
        "cbf5b907a421c904e4c121e4e4203dd1451c6fb698032809805de4928ee9f75e",
        "p5_domain_test_b_knn_k5_seed42_run.log",
    ),
    RunSpec(
        "B",
        43,
        "p5_domain_test_b_knn_k5_seed43",
        "37de8978b361c5e279e30dbcba3a341055b018199da5213109f3cb13b32c112a",
        "p5_domain_test_b_knn_k5_seed43_approved_20260724_run.log",
    ),
    RunSpec(
        "B",
        44,
        "p5_domain_test_b_knn_k5_seed44",
        "cad10220e98518d56ed08f0b61b823a9f01f76165dc063835da9ef28c7945cbb",
        "p5_domain_test_b_knn_k5_seed44_approved_20260724_run.log",
    ),
    RunSpec(
        "C",
        42,
        "p5_domain_test_c_glossary_k5_seed42",
        "a0c1dd65193b4e6259af0aa542763e3c9940fa26949df8dc29fa7252afac17a4",
        "p5_domain_test_c_glossary_k5_seed42_run.log",
    ),
    RunSpec(
        "C",
        43,
        "p5_domain_test_c_glossary_k5_seed43",
        "2c75820dc65ac3595aaa2eb1c73b32f2dff499ac667704ce3d3ace9381752478",
        "p5_domain_test_c_glossary_k5_seed43_approved_20260724_run.log",
    ),
    RunSpec(
        "C",
        44,
        "p5_domain_test_c_glossary_k5_seed44",
        "1b8fc7b3633ddfe6ce1567596efca3cd44505670e45c7a98498d5ad7175f8ccb",
        "p5_domain_test_c_glossary_k5_seed44_approved_20260724_run.log",
    ),
    RunSpec(
        "D",
        42,
        "p5_domain_test_d_rag_k5_seed42",
        "ebaa68c940223ff8688377f63a3f9dbafefaf561382b6a3445c5cdda354a1ed0",
        "p5_domain_test_d_rag_k5_seed42_run.log",
    ),
    RunSpec(
        "D",
        43,
        "p5_domain_test_d_rag_k5_seed43",
        "90ce8bed50005bd7f93f0e8db58f8b44874f0fa67ca6c4c06063f15dbe3d83ab",
        "p5_domain_test_d_rag_k5_seed43_approved_20260724_run.log",
    ),
    RunSpec(
        "D",
        44,
        "p5_domain_test_d_rag_k5_seed44",
        "9415c935b271ebdc4f93650a88f135fa4b1883072a2e0ac06cb1be35da6d754a",
        "p5_domain_test_d_rag_k5_seed44_approved_20260724_run.log",
    ),
)


@dataclass(frozen=True)
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(self.tp + other.tp, self.fp + other.fp, self.fn + other.fn)

    def scaled(self, multiplier: int) -> "Counts":
        return Counts(self.tp * multiplier, self.fp * multiplier, self.fn * multiplier)


@dataclass
class RunData:
    spec: RunSpec
    rows_by_id: dict[str, dict[str, Any]]
    gold_sets: dict[str, frozenset[tuple[int, int, str]]]
    pred_sets: dict[str, frozenset[tuple[int, int, str]]]
    counts_by_id: dict[str, Counts]
    summary: dict[str, Any]
    log_event: dict[str, Any]
    cell_metrics: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the approved M1 evidence from locked P5 outputs."
    )
    parser.add_argument("--results-dir", default="/root/project/results/p5")
    parser.add_argument("--logs-dir", default="/root/project/logs")
    parser.add_argument(
        "--domain-test", default="/root/autodl-tmp/data/domain_test.jsonl"
    )
    parser.add_argument(
        "--source-map",
        default="/root/autodl-tmp/data/domain_gold_source_map.jsonl",
    )
    parser.add_argument("--frozen-marker", default="/root/autodl-tmp/data/FROZEN")
    parser.add_argument(
        "--output-dir",
        default="/root/autodl-tmp/backup/m1/m1_paired_evidence_20260729",
    )
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    parser.add_argument("--bootstrap-seed", type=int, default=BOOTSTRAP_SEED)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA256 mismatch: expected {expected}, got {actual}")
    return actual


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL row at {path}:{line_number}")
            rows.append(value)
    return rows


def index_unique(rows: Sequence[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id or row_id in indexed:
            raise ValueError(f"empty or duplicate id in {label}: {row_id!r}")
        indexed[row_id] = row
    return indexed


def entity_key(entity: Mapping[str, Any]) -> tuple[int, int, str]:
    start = entity.get("start")
    end = entity.get("end")
    entity_type = entity.get("type")
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
        or not isinstance(entity_type, str)
        or start < 0
        or end <= start
    ):
        raise ValueError(f"invalid exact-span entity: {dict(entity)!r}")
    return start, end, entity_type


def entity_set(record: Mapping[str, Any]) -> frozenset[tuple[int, int, str]]:
    raw_entities = record.get("entities")
    if not isinstance(raw_entities, list):
        raise ValueError("record entities must be a list")
    keys = [entity_key(entity) for entity in raw_entities if isinstance(entity, dict)]
    if len(keys) != len(raw_entities):
        raise ValueError("record contains a non-object entity")
    if len(set(keys)) != len(keys):
        raise ValueError("record contains duplicate exact-span entities")
    return frozenset(keys)


def micro_counts(
    gold: Iterable[tuple[int, int, str]],
    pred: Iterable[tuple[int, int, str]],
    entity_type: str | None = None,
) -> Counts:
    gold_set = set(gold)
    pred_set = set(pred)
    if entity_type is not None:
        gold_set = {entity for entity in gold_set if entity[2] == entity_type}
        pred_set = {entity for entity in pred_set if entity[2] == entity_type}
    return Counts(
        tp=len(gold_set & pred_set),
        fp=len(pred_set - gold_set),
        fn=len(gold_set - pred_set),
    )


def metric_report(counts: Counts, passages: int) -> dict[str, float | int]:
    predicted = counts.tp + counts.fp
    gold = counts.tp + counts.fn
    precision = counts.tp / predicted if predicted else 0.0
    recall = counts.tp / gold if gold else 0.0
    denominator = precision + recall
    f1 = 2 * precision * recall / denominator if denominator else 0.0
    return {
        "tp": counts.tp,
        "fp": counts.fp,
        "fn": counts.fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fdr": counts.fp / predicted if predicted else 0.0,
        "fp_per_passage": counts.fp / passages if passages else 0.0,
    }


def sum_counts(counts: Iterable[Counts]) -> Counts:
    total = Counts()
    for item in counts:
        total = total + item
    return total


def mean_sd(values: Sequence[float]) -> dict[str, float]:
    if not values:
        raise ValueError("mean_sd requires at least one value")
    return {
        "mean": statistics.fmean(values),
        "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def metrics_match(actual: Mapping[str, Any], expected: Mapping[str, Any]) -> bool:
    for key in ("tp", "fp", "fn"):
        if int(actual[key]) != int(expected[key]):
            return False
    for key in ("precision", "recall", "f1"):
        if not math.isclose(
            float(actual[key]), float(expected[key]), rel_tol=0.0, abs_tol=1e-12
        ):
            return False
    return True


def load_log_event(path: Path, per_query_name: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(value, dict):
                continue
            per_query = value.get("per_query")
            if isinstance(per_query, str) and Path(per_query).name == per_query_name:
                matches.append(value)
    if len(matches) != 1:
        raise ValueError(
            f"expected one execution event for {per_query_name} in {path}, got {len(matches)}"
        )
    return matches[0]


def validate_gold_sources(
    domain_rows: Sequence[dict[str, Any]], source_rows: Sequence[dict[str, Any]]
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    if len(domain_rows) != EXPECTED_ROWS:
        raise ValueError(f"domain_test rows: expected {EXPECTED_ROWS}, got {len(domain_rows)}")
    domain_by_id = index_unique(domain_rows, "domain_test")
    ids = [str(row["id"]) for row in domain_rows]
    source_by_id = index_unique(source_rows, "source map")
    test_source_ids = {
        row_id for row_id, row in source_by_id.items() if row.get("split") == "test"
    }
    if test_source_ids != set(ids):
        raise ValueError("source-map test IDs do not exactly match domain_test IDs")
    for row_id in ids:
        gold = domain_by_id[row_id]
        text = gold.get("text")
        if not isinstance(text, str):
            raise ValueError(f"domain_test text is not a string for {row_id}")
        expected_text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if source_by_id[row_id].get("text_sha256") != expected_text_hash:
            raise ValueError(f"source-map text hash mismatch for {row_id}")
        entity_set(gold)
    return ids, source_by_id


def load_run(
    spec: RunSpec,
    results_dir: Path,
    logs_dir: Path,
    ids: Sequence[str],
    domain_by_id: Mapping[str, dict[str, Any]],
) -> RunData:
    per_query_path = results_dir / spec.per_query_name
    summary_path = results_dir / spec.summary_name
    log_path = logs_dir / spec.log_name
    require_hash(per_query_path, spec.per_query_sha256, spec.per_query_name)
    summary = read_json(summary_path)
    if summary.get("per_query_sha256") != spec.per_query_sha256:
        raise ValueError(f"summary hash reference mismatch for {spec.stem}")
    if int(summary.get("query_records", -1)) != EXPECTED_ROWS:
        raise ValueError(f"summary row count mismatch for {spec.stem}")
    log_event = load_log_event(log_path, spec.per_query_name)
    if log_event.get("per_query_sha256") != spec.per_query_sha256:
        raise ValueError(f"execution-log hash reference mismatch for {spec.stem}")

    rows = read_jsonl(per_query_path)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"per-query rows mismatch for {spec.stem}: {len(rows)}")
    if [row.get("id") for row in rows] != list(ids):
        raise ValueError(f"per-query ID order mismatch for {spec.stem}")
    rows_by_id = index_unique(rows, spec.stem)
    gold_sets: dict[str, frozenset[tuple[int, int, str]]] = {}
    pred_sets: dict[str, frozenset[tuple[int, int, str]]] = {}
    counts_by_id: dict[str, Counts] = {}
    parse_failures = 0
    for row_id in ids:
        row = rows_by_id[row_id]
        if row.get("dataset") != "domain_test":
            raise ValueError(f"dataset mismatch in {spec.stem}:{row_id}")
        if row.get("config") != EXPECTED_CONFIG_VALUES[spec.config]:
            raise ValueError(f"config mismatch in {spec.stem}:{row_id}")
        if row.get("k") != 5 or row.get("seed") != spec.seed:
            raise ValueError(f"K/seed mismatch in {spec.stem}:{row_id}")
        if row.get("gold") != domain_by_id[row_id]:
            raise ValueError(f"embedded gold drift in {spec.stem}:{row_id}")
        pred = row.get("pred_raw")
        if not isinstance(pred, dict):
            raise ValueError(f"missing pred_raw in {spec.stem}:{row_id}")
        if pred.get("id") != row_id or pred.get("text") != domain_by_id[row_id].get("text"):
            raise ValueError(f"prediction identity/text mismatch in {spec.stem}:{row_id}")
        if row.get("pred_verified") is not None:
            raise ValueError(f"unexpected verified prediction in {spec.stem}:{row_id}")
        flags = row.get("sanitization_flags")
        if not isinstance(flags, list) or any(not isinstance(flag, dict) for flag in flags):
            raise ValueError(f"invalid sanitizer flags in {spec.stem}:{row_id}")
        parse_failures += int(bool(row.get("parse_failure")))
        gold_set = entity_set(domain_by_id[row_id])
        pred_set = entity_set(pred)
        gold_sets[row_id] = gold_set
        pred_sets[row_id] = pred_set
        counts_by_id[row_id] = micro_counts(gold_set, pred_set)

    counts = sum_counts(counts_by_id.values())
    cell_metrics = metric_report(counts, len(ids))
    summary_metrics = summary.get("entity_micro")
    log_metrics = log_event.get("entity_micro")
    if not isinstance(summary_metrics, dict) or not metrics_match(cell_metrics, summary_metrics):
        raise ValueError(f"recomputed metrics mismatch summary for {spec.stem}")
    if not isinstance(log_metrics, dict) or not metrics_match(cell_metrics, log_metrics):
        raise ValueError(f"recomputed metrics mismatch execution log for {spec.stem}")
    if parse_failures != int(summary.get("parse_failures", -1)) or parse_failures != 0:
        raise ValueError(f"unexpected parse failures for {spec.stem}: {parse_failures}")
    flag_count = sum(len(row["sanitization_flags"]) for row in rows)
    if flag_count != int(summary.get("sanitized_unit_events", -1)):
        raise ValueError(f"sanitizer count mismatch for {spec.stem}")
    cell_metrics = {
        "config": spec.config,
        "system": CONFIG_NAMES[spec.config],
        "seed": spec.seed,
        **cell_metrics,
        "parse_failures": parse_failures,
        "sanitizer_events": flag_count,
        "sanitizer_affected_passages": sum(
            bool(row["sanitization_flags"]) for row in rows
        ),
        "per_query_sha256": spec.per_query_sha256,
        "summary_sha256": sha256_file(summary_path),
        "execution_log_sha256": sha256_file(log_path),
    }
    return RunData(
        spec=spec,
        rows_by_id=rows_by_id,
        gold_sets=gold_sets,
        pred_sets=pred_sets,
        counts_by_id=counts_by_id,
        summary=summary,
        log_event=log_event,
        cell_metrics=cell_metrics,
    )


def weighted_counts(values: Sequence[Counts], weights: Sequence[int]) -> Counts:
    if len(values) != len(weights):
        raise ValueError("values and weights must have equal length")
    total = Counts()
    for counts, weight in zip(values, weights, strict=True):
        if weight:
            total = total + counts.scaled(weight)
    return total


def config_mean_metrics(
    counts_by_run: Mapping[tuple[str, int], Sequence[Counts]],
    config: str,
    seeds: Sequence[int],
    weights: Sequence[int],
) -> dict[str, float]:
    passages = sum(weights)
    reports = [
        metric_report(weighted_counts(counts_by_run[(config, seed)], weights), passages)
        for seed in seeds
    ]
    return {
        metric: statistics.fmean(float(report[metric]) for report in reports)
        for metric in BOOTSTRAP_METRICS
    }


def percentile(values: Sequence[float], quantile: float) -> float:
    if not values or not 0.0 <= quantile <= 1.0:
        raise ValueError("invalid percentile input")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def paired_bootstrap(
    counts_by_run: Mapping[tuple[str, int], Sequence[Counts]],
    passage_count: int,
    *,
    configs: Sequence[str] = CONFIGS,
    seeds: Sequence[int] = SEEDS,
    contrasts: Sequence[tuple[str, str, str]] = CONTRASTS,
    replicates: int = BOOTSTRAP_REPLICATES,
    random_seed: int = BOOTSTRAP_SEED,
) -> list[dict[str, Any]]:
    if passage_count <= 0 or replicates <= 0:
        raise ValueError("passage_count and replicates must be positive")
    expected_keys = {(config, seed) for config in configs for seed in seeds}
    if set(counts_by_run) != expected_keys:
        raise ValueError("bootstrap run matrix is incomplete")
    if any(len(values) != passage_count for values in counts_by_run.values()):
        raise ValueError("bootstrap count vectors have inconsistent lengths")

    full_weights = [1] * passage_count
    point = {
        config: config_mean_metrics(counts_by_run, config, seeds, full_weights)
        for config in configs
    }
    distributions: dict[tuple[str, str], list[float]] = {
        (label, metric): []
        for label, _, _ in contrasts
        for metric in BOOTSTRAP_METRICS
    }
    rng = random.Random(random_seed)
    for _ in range(replicates):
        weights = [0] * passage_count
        for _ in range(passage_count):
            weights[rng.randrange(passage_count)] += 1
        replicate_metrics = {
            config: config_mean_metrics(counts_by_run, config, seeds, weights)
            for config in configs
        }
        for label, earlier, later in contrasts:
            for metric in BOOTSTRAP_METRICS:
                distributions[(label, metric)].append(
                    replicate_metrics[later][metric] - replicate_metrics[earlier][metric]
                )

    rows: list[dict[str, Any]] = []
    for label, earlier, later in contrasts:
        for metric in BOOTSTRAP_METRICS:
            values = distributions[(label, metric)]
            lower = percentile(values, 0.025)
            upper = percentile(values, 0.975)
            rows.append(
                {
                    "contrast": label,
                    "earlier": earlier,
                    "later": later,
                    "definition": f"{later} minus {earlier}",
                    "metric": metric,
                    "point_delta": point[later][metric] - point[earlier][metric],
                    "ci95_lower": lower,
                    "ci95_upper": upper,
                    "bootstrap_probability_gt_zero": sum(value > 0 for value in values)
                    / replicates,
                    "bootstrap_probability_lt_zero": sum(value < 0 for value in values)
                    / replicates,
                    "ci_excludes_zero": lower > 0 or upper < 0,
                    "replicates": replicates,
                    "analysis_seed": random_seed,
                }
            )
    return rows


def aggregate_cell_metrics(cell_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    metric_names = ("precision", "recall", "f1", "fp", "fdr", "fp_per_passage")
    for config in CONFIGS:
        selected = [row for row in cell_rows if row["config"] == config]
        if len(selected) != len(SEEDS):
            raise ValueError(f"incomplete cell aggregate for {config}")
        output[config] = {
            "system": CONFIG_NAMES[config],
            **{
                metric: mean_sd([float(row[metric]) for row in selected])
                for metric in metric_names
            },
        }
    return output


def build_per_type_rows(
    runs: Mapping[tuple[str, int], RunData], ids: Sequence[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        for seed in SEEDS:
            run = runs[(config, seed)]
            for entity_type in ENTITY_TYPES:
                counts = sum_counts(
                    micro_counts(
                        run.gold_sets[row_id], run.pred_sets[row_id], entity_type
                    )
                    for row_id in ids
                )
                rows.append(
                    {
                        "config": config,
                        "seed": seed,
                        "entity_type": entity_type,
                        **metric_report(counts, len(ids)),
                    }
                )
    return rows


def aggregate_group_metrics(
    rows: Sequence[dict[str, Any]], group_fields: Sequence[str]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[field] for field in group_fields)].append(row)
    output: list[dict[str, Any]] = []
    for key, values in sorted(grouped.items(), key=lambda item: tuple(map(str, item[0]))):
        aggregate: dict[str, Any] = dict(zip(group_fields, key, strict=True))
        aggregate["seeds"] = len(values)
        for metric in ("precision", "recall", "f1", "fp", "fdr", "fp_per_passage"):
            stats = mean_sd([float(row[metric]) for row in values])
            aggregate[f"{metric}_mean"] = stats["mean"]
            aggregate[f"{metric}_sd"] = stats["sd"]
        output.append(aggregate)
    return output


def text_length_bin(length: int) -> str:
    if length <= 128:
        return "<=128"
    if length <= 256:
        return "129-256"
    return ">256"


def gold_count_bin(count: int) -> str:
    if count == 0:
        return "0"
    if count <= 4:
        return "1-4"
    if count <= 9:
        return "5-9"
    return ">=10"


def build_stratified_rows(
    runs: Mapping[tuple[str, int], RunData],
    ids: Sequence[str],
    source_by_id: Mapping[str, dict[str, Any]],
    domain_by_id: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    membership: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row_id in ids:
        text = str(domain_by_id[row_id]["text"])
        gold_count = len(runs[("A", 42)].gold_sets[row_id])
        levels = (
            ("source_type", str(source_by_id[row_id]["source_type"])),
            ("text_length_chars", text_length_bin(len(text))),
            ("gold_entity_count", gold_count_bin(gold_count)),
            ("zero_gold", "yes" if gold_count == 0 else "no"),
        )
        for dimension, level in levels:
            membership[(dimension, level)].append(row_id)

    rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        for seed in SEEDS:
            run = runs[(config, seed)]
            for (dimension, level), member_ids in sorted(membership.items()):
                counts = sum_counts(run.counts_by_id[row_id] for row_id in member_ids)
                rows.append(
                    {
                        "config": config,
                        "seed": seed,
                        "dimension": dimension,
                        "level": level,
                        "passages": len(member_ids),
                        "passages_with_fp": sum(
                            run.counts_by_id[row_id].fp > 0 for row_id in member_ids
                        ),
                        **metric_report(counts, len(member_ids)),
                    }
                )
    return rows


def build_changed_passage_rows(
    runs: Mapping[tuple[str, int], RunData], ids: Sequence[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, earlier, later in CONTRASTS:
        for seed in SEEDS:
            earlier_run = runs[(earlier, seed)]
            later_run = runs[(later, seed)]
            changed = improved = worsened = tied = added = removed = 0
            for row_id in ids:
                before = earlier_run.pred_sets[row_id]
                after = later_run.pred_sets[row_id]
                if before != after:
                    changed += 1
                before_error = earlier_run.counts_by_id[row_id].fp + earlier_run.counts_by_id[row_id].fn
                after_error = later_run.counts_by_id[row_id].fp + later_run.counts_by_id[row_id].fn
                if after_error < before_error:
                    improved += 1
                elif after_error > before_error:
                    worsened += 1
                else:
                    tied += 1
                added += len(after - before)
                removed += len(before - after)
            rows.append(
                {
                    "contrast": label,
                    "seed": seed,
                    "passages": len(ids),
                    "changed_predictions": changed,
                    "unchanged_predictions": len(ids) - changed,
                    "lower_fp_plus_fn": improved,
                    "higher_fp_plus_fn": worsened,
                    "equal_fp_plus_fn": tied,
                    "later_only_entities": added,
                    "earlier_only_entities": removed,
                }
            )
    return rows


def passage_transition(
    gold: frozenset[tuple[int, int, str]],
    before: frozenset[tuple[int, int, str]],
    after: frozenset[tuple[int, int, str]],
) -> Counter[str]:
    before_tp = before & gold
    after_tp = after & gold
    before_fp = before - gold
    after_fp = after - gold
    return Counter(
        {
            "tp_retained": len(before_tp & after_tp),
            "tp_lost": len(before_tp - after_tp),
            "tp_gained": len(after_tp - before_tp),
            "fp_retained": len(before_fp & after_fp),
            "fp_removed": len(before_fp - after_fp),
            "fp_introduced": len(after_fp - before_fp),
            "changed_passages": int(before != after),
        }
    )


def build_cd_transition_rows(
    runs: Mapping[tuple[str, int], RunData], ids: Sequence[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pooled: Counter[str] = Counter()
    for seed in SEEDS:
        c_run = runs[("C", seed)]
        d_run = runs[("D", seed)]
        counts: Counter[str] = Counter()
        for row_id in ids:
            counts.update(
                passage_transition(
                    c_run.gold_sets[row_id],
                    c_run.pred_sets[row_id],
                    d_run.pred_sets[row_id],
                )
            )
        counts["run_passage_observations"] = len(ids)
        counts["net_fp_reduction"] = counts["fp_removed"] - counts["fp_introduced"]
        counts["net_tp_change"] = counts["tp_gained"] - counts["tp_lost"]
        if counts["tp_retained"] + counts["tp_lost"] != int(c_run.cell_metrics["tp"]):
            raise AssertionError("C TP transition accounting mismatch")
        if counts["tp_retained"] + counts["tp_gained"] != int(d_run.cell_metrics["tp"]):
            raise AssertionError("D TP transition accounting mismatch")
        if counts["fp_retained"] + counts["fp_removed"] != int(c_run.cell_metrics["fp"]):
            raise AssertionError("C FP transition accounting mismatch")
        if counts["fp_retained"] + counts["fp_introduced"] != int(d_run.cell_metrics["fp"]):
            raise AssertionError("D FP transition accounting mismatch")
        row = {"seed": seed, **dict(counts)}
        rows.append(row)
        pooled.update(counts)
    pooled["net_fp_reduction"] = pooled["fp_removed"] - pooled["fp_introduced"]
    pooled["net_tp_change"] = pooled["tp_gained"] - pooled["tp_lost"]
    rows.append({"seed": "pooled_run_passages", **dict(pooled)})
    return rows


def sanitizer_entity_key(flag: Mapping[str, Any]) -> tuple[int, int, str] | None:
    entity = flag.get("entity")
    if isinstance(entity, dict) and {"start", "end", "type"}.issubset(entity):
        try:
            return entity_key(entity)
        except ValueError:
            return None
    duplicate_key = flag.get("duplicate_key")
    if (
        isinstance(duplicate_key, list)
        and len(duplicate_key) == 3
        and isinstance(duplicate_key[0], int)
        and isinstance(duplicate_key[1], int)
        and isinstance(duplicate_key[2], str)
    ):
        return duplicate_key[0], duplicate_key[1], duplicate_key[2]
    return None


def build_sanitizer_rows(
    runs: Mapping[tuple[str, int], RunData], ids: Sequence[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    audit_rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        for seed in SEEDS:
            run = runs[(config, seed)]
            grouped: dict[tuple[str, str], dict[str, Any]] = {}
            for row_id in ids:
                for flag in run.rows_by_id[row_id]["sanitization_flags"]:
                    kind = str(flag.get("kind") or "UNKNOWN")
                    reason = str(flag.get("reason") or "")
                    key = (kind, reason)
                    bucket = grouped.setdefault(
                        key,
                        {
                            "event_count": 0,
                            "affected_ids": set(),
                            "mappable_entity_events": 0,
                            "exact_gold_match_events": 0,
                        },
                    )
                    bucket["event_count"] += 1
                    bucket["affected_ids"].add(row_id)
                    mapped = sanitizer_entity_key(flag)
                    if mapped is not None:
                        bucket["mappable_entity_events"] += 1
                        if mapped in run.gold_sets[row_id]:
                            bucket["exact_gold_match_events"] += 1
            for (kind, reason), bucket in sorted(grouped.items()):
                audit_rows.append(
                    {
                        "config": config,
                        "seed": seed,
                        "kind": kind,
                        "reason": reason,
                        "event_count": bucket["event_count"],
                        "affected_passages": len(bucket["affected_ids"]),
                        "mappable_entity_events": bucket["mappable_entity_events"],
                        "exact_gold_match_events": bucket["exact_gold_match_events"],
                    }
                )

    association_rows: list[dict[str, Any]] = []
    for seed in SEEDS:
        c_run = runs[("C", seed)]
        d_run = runs[("D", seed)]
        buckets: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        for row_id in ids:
            c_flags = len(c_run.rows_by_id[row_id]["sanitization_flags"])
            d_flags = len(d_run.rows_by_id[row_id]["sanitization_flags"])
            levels = (
                ("d_any_flag", "yes" if d_flags else "no"),
                ("either_any_flag", "yes" if c_flags or d_flags else "no"),
                (
                    "flag_count_relation",
                    "d_more" if d_flags > c_flags else "d_less" if d_flags < c_flags else "equal",
                ),
            )
            transition = passage_transition(
                c_run.gold_sets[row_id],
                c_run.pred_sets[row_id],
                d_run.pred_sets[row_id],
            )
            for dimension, level in levels:
                bucket = buckets[(dimension, level)]
                bucket["passages"] += 1
                bucket["c_sanitizer_events"] += c_flags
                bucket["d_sanitizer_events"] += d_flags
                bucket.update(transition)
        for (dimension, level), bucket in sorted(buckets.items()):
            bucket["net_fp_reduction"] = bucket["fp_removed"] - bucket["fp_introduced"]
            bucket["net_tp_change"] = bucket["tp_gained"] - bucket["tp_lost"]
            association_rows.append(
                {"seed": seed, "dimension": dimension, "level": level, **dict(bucket)}
            )
    return audit_rows, association_rows


def build_runtime_rows(runs: Mapping[tuple[str, int], RunData]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        for seed in SEEDS:
            run = runs[(config, seed)]
            llm_seconds = sum(
                float(row.get("llm_latency_ms", row.get("latency_ms", 0.0)))
                for row in run.rows_by_id.values()
            ) / 1000.0
            elapsed_seconds = float(run.summary["elapsed_seconds"])
            timing_totals = run.summary.get("timing_totals_ms")
            total_record_seconds: float | None = None
            rag_selection_seconds: float | None = None
            if isinstance(timing_totals, dict):
                total_record_seconds = float(timing_totals.get("total_record_ms", 0.0)) / 1000.0
                rag_selection_seconds = float(timing_totals.get("rag_selection_ms", 0.0)) / 1000.0
            rag_metadata = run.summary.get("rag_selection")
            rag_mode = "disabled"
            if isinstance(rag_metadata, dict) and rag_metadata.get("enabled"):
                rag_mode = str(rag_metadata.get("mode") or "enabled_unspecified")
            cache_hits = sum(
                bool(attempt.get("cache_hit"))
                for row in run.rows_by_id.values()
                for attempt in row.get("attempts", [])
                if isinstance(attempt, dict)
            )
            rows.append(
                {
                    "config": config,
                    "seed": seed,
                    "rag_mode": rag_mode,
                    "elapsed_seconds": elapsed_seconds,
                    "llm_latency_seconds": llm_seconds,
                    "elapsed_minus_llm_seconds": elapsed_seconds - llm_seconds,
                    "total_record_seconds": total_record_seconds,
                    "rag_selection_seconds": rag_selection_seconds,
                    "cache_hits": cache_hits,
                }
            )
    return rows


def build_seed_agreement_rows(
    runs: Mapping[tuple[str, int], RunData], ids: Sequence[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for config in CONFIGS:
        for left_seed, right_seed in combinations(SEEDS, 2):
            left = runs[(config, left_seed)]
            right = runs[(config, right_seed)]
            identical_predictions = sum(
                left.pred_sets[row_id] == right.pred_sets[row_id] for row_id in ids
            )
            identical_raw_hashes = sum(
                left.rows_by_id[row_id].get("raw_llm_output_hash")
                == right.rows_by_id[row_id].get("raw_llm_output_hash")
                for row_id in ids
            )
            rows.append(
                {
                    "config": config,
                    "left_seed": left_seed,
                    "right_seed": right_seed,
                    "passages": len(ids),
                    "identical_prediction_sets": identical_predictions,
                    "different_prediction_sets": len(ids) - identical_predictions,
                    "identical_raw_output_hashes": identical_raw_hashes,
                }
            )
    return rows


def csv_payload(rows: Sequence[dict[str, Any]], fields: Sequence[str]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(fields),
        extrasaction="raise",
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def write_atomic(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp-{uuid4().hex}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def json_payload(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def output_metadata(path: Path, rows: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if rows is not None:
        result["rows"] = rows
    return result


def analyze(
    *,
    results_dir: Path,
    logs_dir: Path,
    domain_test_path: Path,
    source_map_path: Path,
    frozen_marker_path: Path,
    output_dir: Path,
    bootstrap_replicates: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_dir}")
    if bootstrap_replicates <= 0:
        raise ValueError("bootstrap_replicates must be positive")

    input_hashes = {
        "domain_test": require_hash(
            domain_test_path, EXPECTED_DOMAIN_TEST_SHA256, "domain_test"
        ),
        "source_map": require_hash(
            source_map_path, EXPECTED_SOURCE_MAP_SHA256, "domain_gold_source_map"
        ),
        "frozen_marker": require_hash(
            frozen_marker_path, EXPECTED_FROZEN_SHA256, "FROZEN marker"
        ),
    }
    domain_rows = read_jsonl(domain_test_path)
    source_rows = read_jsonl(source_map_path)
    ids, source_by_id = validate_gold_sources(domain_rows, source_rows)
    domain_by_id = index_unique(domain_rows, "domain_test")

    runs: dict[tuple[str, int], RunData] = {}
    for spec in RUN_SPECS:
        run = load_run(spec, results_dir, logs_dir, ids, domain_by_id)
        runs[(spec.config, spec.seed)] = run
    if set(runs) != {(config, seed) for config in CONFIGS for seed in SEEDS}:
        raise ValueError("A/B/C/D x seed run matrix is incomplete")

    reference_gold = runs[("A", 42)].gold_sets
    for run in runs.values():
        if run.gold_sets != reference_gold:
            raise ValueError(f"gold-set drift in {run.spec.stem}")

    cell_rows = [runs[(config, seed)].cell_metrics for config in CONFIGS for seed in SEEDS]
    config_aggregates = aggregate_cell_metrics(cell_rows)
    counts_by_run = {
        (config, seed): [runs[(config, seed)].counts_by_id[row_id] for row_id in ids]
        for config in CONFIGS
        for seed in SEEDS
    }
    bootstrap_rows = paired_bootstrap(
        counts_by_run,
        len(ids),
        replicates=bootstrap_replicates,
        random_seed=bootstrap_seed,
    )
    per_type_rows = build_per_type_rows(runs, ids)
    per_type_aggregates = aggregate_group_metrics(per_type_rows, ("config", "entity_type"))
    stratified_rows = build_stratified_rows(runs, ids, source_by_id, domain_by_id)
    changed_rows = build_changed_passage_rows(runs, ids)
    transition_rows = build_cd_transition_rows(runs, ids)
    sanitizer_rows, sanitizer_association_rows = build_sanitizer_rows(runs, ids)
    runtime_rows = build_runtime_rows(runs)
    seed_agreement_rows = build_seed_agreement_rows(runs, ids)

    created_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "phase": "M1-PAIRED-EVIDENCE-AUDIT",
        "status": "complete_aggregate_only",
        "created_at": created_at,
        "scope": {
            "frozen_test_read": True,
            "existing_predictions_read": True,
            "labels_modified": False,
            "predictions_modified": False,
            "prompt_or_config_changes": False,
            "model_calls": False,
            "gpu_used": False,
            "latex_modified": False,
            "analysis_is_post_hoc_exploratory": True,
        },
        "integrity": {
            "domain_test_rows": len(ids),
            "run_cells": len(runs),
            "input_hashes": input_hashes,
            "all_per_query_hashes_locked": True,
            "all_summary_and_log_metrics_recomputed": True,
            "all_parse_failures_zero": True,
            "gold_identical_across_runs": True,
            "source_map_complete_for_test": True,
        },
        "bootstrap_protocol": {
            "unit": "passage cluster",
            "paired_across": "all A/B/C/D cells and aligned seeds",
            "seed_aggregation": "arithmetic mean of seed-specific micro metrics",
            "interval": "95% percentile",
            "replicates": bootstrap_replicates,
            "analysis_seed": bootstrap_seed,
        },
        "config_aggregates": config_aggregates,
        "bootstrap_contrasts": bootstrap_rows,
        "per_type_aggregates": per_type_aggregates,
        "cd_transitions": transition_rows,
        "sanitizer_guardrail": (
            "Flag associations are descriptive. Sanitized outputs do not provide a valid "
            "counterfactual unsanitized score, so no RAG-versus-sanitizer causal share is claimed."
        ),
        "runtime_guardrail": (
            "Elapsed time includes the original execution path; seed-42 D used online CPU "
            "retrieval while seed-43/44 D replayed a locked manifest."
        ),
    }

    output_parent = output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = output_parent / f".{output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        payloads: list[tuple[str, bytes, int | None]] = [
            ("summary.json", json_payload(summary), None),
            (
                "cell_metrics.csv",
                csv_payload(cell_rows, tuple(cell_rows[0].keys())),
                len(cell_rows),
            ),
            (
                "bootstrap_contrasts.csv",
                csv_payload(bootstrap_rows, tuple(bootstrap_rows[0].keys())),
                len(bootstrap_rows),
            ),
            (
                "per_type_metrics.csv",
                csv_payload(per_type_rows, tuple(per_type_rows[0].keys())),
                len(per_type_rows),
            ),
            (
                "per_type_aggregates.csv",
                csv_payload(per_type_aggregates, tuple(per_type_aggregates[0].keys())),
                len(per_type_aggregates),
            ),
            (
                "stratified_metrics.csv",
                csv_payload(stratified_rows, tuple(stratified_rows[0].keys())),
                len(stratified_rows),
            ),
            (
                "changed_passages.csv",
                csv_payload(changed_rows, tuple(changed_rows[0].keys())),
                len(changed_rows),
            ),
            (
                "cd_transitions.csv",
                csv_payload(transition_rows, tuple(transition_rows[0].keys())),
                len(transition_rows),
            ),
            (
                "sanitizer_audit.csv",
                csv_payload(sanitizer_rows, tuple(sanitizer_rows[0].keys())),
                len(sanitizer_rows),
            ),
            (
                "sanitizer_cd_association.csv",
                csv_payload(
                    sanitizer_association_rows,
                    tuple(sanitizer_association_rows[0].keys()),
                ),
                len(sanitizer_association_rows),
            ),
            (
                "runtime.csv",
                csv_payload(runtime_rows, tuple(runtime_rows[0].keys())),
                len(runtime_rows),
            ),
            (
                "seed_agreement.csv",
                csv_payload(seed_agreement_rows, tuple(seed_agreement_rows[0].keys())),
                len(seed_agreement_rows),
            ),
        ]
        output_manifest: dict[str, Any] = {}
        for name, payload, row_count in payloads:
            path = staging / name
            write_atomic(path, payload)
            os.chmod(path, 0o600)
            output_manifest[name] = output_metadata(path, row_count)
        manifest = {
            "phase": summary["phase"],
            "status": summary["status"],
            "created_at": created_at,
            "inputs": {
                "domain_test": {"path": str(domain_test_path), "sha256": input_hashes["domain_test"]},
                "source_map": {"path": str(source_map_path), "sha256": input_hashes["source_map"]},
                "frozen_marker": {"path": str(frozen_marker_path), "sha256": input_hashes["frozen_marker"]},
                "runs": [
                    {
                        "config": spec.config,
                        "seed": spec.seed,
                        "per_query": str(results_dir / spec.per_query_name),
                        "per_query_sha256": spec.per_query_sha256,
                        "summary": str(results_dir / spec.summary_name),
                        "summary_sha256": runs[(spec.config, spec.seed)].cell_metrics[
                            "summary_sha256"
                        ],
                        "execution_log": str(logs_dir / spec.log_name),
                        "execution_log_sha256": runs[(spec.config, spec.seed)].cell_metrics[
                            "execution_log_sha256"
                        ],
                    }
                    for spec in RUN_SPECS
                ],
            },
            "safeguards": summary["scope"],
            "outputs": output_manifest,
        }
        manifest_path = staging / "manifest.json"
        write_atomic(manifest_path, json_payload(manifest))
        os.chmod(manifest_path, 0o600)
        os.replace(staging, output_dir)
        os.chmod(output_dir, 0o700)
        return summary
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    summary = analyze(
        results_dir=Path(args.results_dir),
        logs_dir=Path(args.logs_dir),
        domain_test_path=Path(args.domain_test),
        source_map_path=Path(args.source_map),
        frozen_marker_path=Path(args.frozen_marker),
        output_dir=Path(args.output_dir),
        bootstrap_replicates=args.bootstrap_replicates,
        bootstrap_seed=args.bootstrap_seed,
    )
    print(
        json.dumps(
            {
                "status": summary["status"],
                "run_cells": summary["integrity"]["run_cells"],
                "domain_test_rows": summary["integrity"]["domain_test_rows"],
                "bootstrap_replicates": summary["bootstrap_protocol"]["replicates"],
                "model_calls": summary["scope"]["model_calls"],
                "gpu_used": summary["scope"]["gpu_used"],
                "latex_modified": summary["scope"]["latex_modified"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
