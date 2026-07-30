"""Literal 60-cell full-IE manifest inventory and aggregate validation."""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any


MANIFEST_VERSION = "full-ie-60-v1"
SEEDS = (42, 43, 44)
K5_CONFIGS = ("A", "B", "C", "D", "E", "E-prime")
KSCAN_CONFIGS = ("A", "E")
K_VALUES = (1, 5, 10)
CELL_STATUSES = frozenset({"PLANNED", "STAGE_N_DONE", "DONE", "BLOCKED"})
STAGE_STATUSES = frozenset({"PLANNED", "DONE", "BLOCKED"})
METRIC_FIELDS = ("tp", "fp", "fn", "precision", "recall", "f1")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def cell_id(dataset: str, config: str, k: int, seed: int) -> str:
    return f"{dataset}:{config}:k{k}:s{seed}"


def expected_full_ie_cells() -> list[dict[str, Any]]:
    """Return the exact ordered 30-domain plus 30-CLUENER inventory."""

    cells: list[dict[str, Any]] = []
    for dataset in ("domain", "cluener"):
        for config in K5_CONFIGS:
            for seed in SEEDS:
                cells.append(
                    {
                        "cell_id": cell_id(dataset, config, 5, seed),
                        "dataset": dataset,
                        "config": config,
                        "k": 5,
                        "seed": seed,
                    }
                )
        for k in (1, 10):
            for config in KSCAN_CONFIGS:
                for seed in SEEDS:
                    cells.append(
                        {
                            "cell_id": cell_id(dataset, config, k, seed),
                            "dataset": dataset,
                            "config": config,
                            "k": k,
                            "seed": seed,
                        }
                    )
    return cells


def build_planned_manifest() -> dict[str, Any]:
    """Build an empty manifest whose inventory can be reviewed before execution."""

    cells: list[dict[str, Any]] = []
    for expected in expected_full_ie_cells():
        dataset = expected["dataset"]
        cells.append(
            {
                **expected,
                "status": "PLANNED",
                "stage_n": {"status": "PLANNED", "artifact_sha256": None},
                "stage_r": (
                    {"status": "PLANNED", "artifact_sha256": None}
                    if dataset == "domain"
                    else None
                ),
                "metrics": None,
            }
        )
    return {"manifest_version": MANIFEST_VERSION, "cells": cells}


def _validate_stage(value: Any, *, label: str) -> str:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    status = value.get("status")
    if status not in STAGE_STATUSES:
        raise ValueError(f"{label}.status must be one of {sorted(STAGE_STATUSES)}")
    digest = value.get("artifact_sha256")
    if status == "DONE":
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ValueError(f"{label} DONE requires a lowercase SHA256")
    elif digest is not None:
        raise ValueError(f"{label} may not have an artifact hash before DONE")
    return str(status)


def _validate_metric_block(value: Any, *, label: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    missing = set(METRIC_FIELDS).difference(value)
    if missing:
        raise ValueError(f"{label} is missing metrics {sorted(missing)}")
    counts: dict[str, int] = {}
    for field in ("tp", "fp", "fn"):
        raw = value[field]
        if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
            raise ValueError(f"{label}.{field} must be a non-negative integer")
        counts[field] = raw
    expected_precision = counts["tp"] / (counts["tp"] + counts["fp"]) if counts["tp"] + counts["fp"] else 0.0
    expected_recall = counts["tp"] / (counts["tp"] + counts["fn"]) if counts["tp"] + counts["fn"] else 0.0
    expected_f1 = (
        2 * expected_precision * expected_recall / (expected_precision + expected_recall)
        if expected_precision + expected_recall
        else 0.0
    )
    for field, expected in (
        ("precision", expected_precision),
        ("recall", expected_recall),
        ("f1", expected_f1),
    ):
        raw = value[field]
        if not isinstance(raw, (int, float)) or isinstance(raw, bool) or not math.isfinite(float(raw)):
            raise ValueError(f"{label}.{field} must be finite")
        if not math.isclose(float(raw), expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"{label}.{field} does not recompute from TP/FP/FN")


def _validate_done_metrics(cell: Mapping[str, Any]) -> None:
    metrics = cell.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ValueError(f"{cell['cell_id']}: DONE requires metrics")
    _validate_metric_block(metrics.get("entity"), label=f"{cell['cell_id']}.metrics.entity")
    relation = metrics.get("relation")
    if cell["dataset"] == "domain":
        _validate_metric_block(relation, label=f"{cell['cell_id']}.metrics.relation")
    elif relation is not None:
        raise ValueError(f"{cell['cell_id']}: CLUENER must not report relation metrics")


def validate_full_ie_manifest(
    manifest: Mapping[str, Any],
    *,
    require_complete: bool = False,
) -> dict[str, Any]:
    """Validate exact inventory, stage completeness, hashes, and metric arithmetic."""

    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError(f"manifest_version must be {MANIFEST_VERSION}")
    raw_cells = manifest.get("cells")
    if not isinstance(raw_cells, list):
        raise ValueError("manifest cells must be a list")
    expected = {item["cell_id"]: item for item in expected_full_ie_cells()}
    seen: dict[str, Mapping[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    for index, raw_cell in enumerate(raw_cells):
        if not isinstance(raw_cell, Mapping):
            raise ValueError(f"cells[{index}] must be an object")
        identifier = raw_cell.get("cell_id")
        if not isinstance(identifier, str):
            raise ValueError(f"cells[{index}].cell_id must be a string")
        if identifier in seen:
            raise ValueError(f"duplicate cell {identifier}")
        expected_cell = expected.get(identifier)
        if expected_cell is None:
            raise ValueError(f"unexpected cell {identifier}")
        for field in ("dataset", "config", "k", "seed"):
            if raw_cell.get(field) != expected_cell[field]:
                raise ValueError(f"{identifier}: {field} does not match the fixed inventory")
        status = raw_cell.get("status")
        if status not in CELL_STATUSES:
            raise ValueError(f"{identifier}: invalid cell status {status!r}")
        stage_n_status = _validate_stage(raw_cell.get("stage_n"), label=f"{identifier}.stage_n")
        if raw_cell["dataset"] == "domain":
            stage_r_status = _validate_stage(raw_cell.get("stage_r"), label=f"{identifier}.stage_r")
        else:
            if raw_cell.get("stage_r") is not None:
                raise ValueError(f"{identifier}: CLUENER has no Stage R")
            stage_r_status = None

        if status == "DONE":
            if stage_n_status != "DONE" or (
                raw_cell["dataset"] == "domain" and stage_r_status != "DONE"
            ):
                raise ValueError(f"{identifier}: DONE cell has incomplete stages")
            _validate_done_metrics(raw_cell)
        elif status == "STAGE_N_DONE":
            if raw_cell["dataset"] != "domain":
                raise ValueError(f"{identifier}: CLUENER Stage N is already the complete task")
            if stage_n_status != "DONE" or stage_r_status != "PLANNED":
                raise ValueError(f"{identifier}: STAGE_N_DONE has inconsistent stage states")
            if raw_cell.get("metrics") is not None:
                raise ValueError(f"{identifier}: partial cells may not carry final metrics")
        elif status == "PLANNED":
            if stage_n_status != "PLANNED" or (
                raw_cell["dataset"] == "domain" and stage_r_status != "PLANNED"
            ):
                raise ValueError(f"{identifier}: PLANNED requires all stages PLANNED")
            if raw_cell.get("metrics") is not None:
                raise ValueError(f"{identifier}: PLANNED cell may not carry final metrics")
        elif status == "BLOCKED":
            relevant_stage_statuses = [stage_n_status]
            if stage_r_status is not None:
                relevant_stage_statuses.append(stage_r_status)
            if "BLOCKED" not in relevant_stage_statuses:
                raise ValueError(f"{identifier}: BLOCKED requires a blocked stage")
            if stage_n_status == "BLOCKED" and stage_r_status == "DONE":
                raise ValueError(f"{identifier}: Stage R cannot be DONE when Stage N is blocked")
            if raw_cell.get("metrics") is not None:
                raise ValueError(f"{identifier}: BLOCKED cell may not carry final metrics")

        seen[identifier] = raw_cell
        status_counts[str(status)] += 1

    missing = sorted(set(expected) - set(seen))
    if missing:
        raise ValueError(f"manifest is missing {len(missing)} fixed cells: {missing[:5]}")
    if len(raw_cells) != 60:
        raise ValueError(f"manifest must contain exactly 60 cells, found {len(raw_cells)}")
    if require_complete and status_counts["DONE"] != 60:
        raise ValueError(f"complete manifest requires 60 DONE cells, found {status_counts['DONE']}")
    return {
        "cells": len(raw_cells),
        "domain_cells": sum(cell["dataset"] == "domain" for cell in raw_cells),
        "cluener_cells": sum(cell["dataset"] == "cluener" for cell in raw_cells),
        "status_counts": dict(sorted(status_counts.items())),
        "complete": status_counts["DONE"] == 60,
    }


def aggregate_manifest_metrics(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Aggregate complete three-seed cell metrics with sample standard deviation."""

    validate_full_ie_manifest(manifest, require_complete=True)
    groups: dict[tuple[str, str, int], list[Mapping[str, Any]]] = {}
    for cell in manifest["cells"]:
        key = (cell["dataset"], cell["config"], int(cell["k"]))
        groups.setdefault(key, []).append(cell)

    rows: list[dict[str, Any]] = []
    for (dataset, config, k), cells in sorted(groups.items()):
        seeds = tuple(sorted(int(cell["seed"]) for cell in cells))
        if seeds != SEEDS:
            raise ValueError(f"{dataset}/{config}/k{k}: expected seeds {SEEDS}, found {seeds}")
        metric_kinds = ("entity", "relation") if dataset == "domain" else ("entity",)
        aggregates: dict[str, Any] = {}
        for kind in metric_kinds:
            aggregates[kind] = {}
            for field in METRIC_FIELDS:
                values = [float(cell["metrics"][kind][field]) for cell in cells]
                aggregates[kind][field] = {
                    "mean": statistics.fmean(values),
                    "sd": statistics.stdev(values),
                }
        rows.append(
            {
                "dataset": dataset,
                "config": config,
                "k": k,
                "seeds": list(seeds),
                "metrics": aggregates,
            }
        )
    if len(rows) != 20:
        raise ValueError(f"expected 20 three-seed aggregate rows, found {len(rows)}")
    return rows
