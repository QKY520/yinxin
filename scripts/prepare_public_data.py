#!/usr/bin/env python3
"""Normalize and validate all P1 public datasets from a pinned YAML config."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.public_data import (  # noqa: E402
    ConversionAudit,
    choose_support_ids,
    convert_cluener,
    convert_cmnee,
    convert_duie,
    convert_fewnerd,
    iter_selected_records,
    partition_record_ids,
)
from equipment_ie.schema import (  # noqa: E402
    iter_jsonl,
    sha256_file,
    validate_jsonl,
    write_jsonl_atomic,
)


def _write_json_atomic(path: Path, value: Any) -> None:
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


def _append_log(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _load_config(path: Path) -> dict[str, Any]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("phase") != "P1":
        raise ValueError(f"{path}: expected a P1 configuration object")
    return config


def _verify_source(path: Path, expected_sha256: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ValueError(
            f"source hash mismatch for {path}: expected {expected_sha256}, got {actual}"
        )
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def _converter(
    dataset: str,
    dataset_format: str,
    source: Path,
    split: str,
    labeled: bool,
    audit: ConversionAudit,
):
    if dataset_format == "cluener":
        return convert_cluener(source, split, labeled=labeled, audit=audit)
    if dataset_format == "fewnerd":
        if not labeled:
            raise ValueError("Few-NERD SUP splits must be labeled")
        return convert_fewnerd(source, split, audit=audit)
    if dataset_format == "duie":
        return convert_duie(source, split, labeled=labeled, audit=audit)
    if dataset_format == "cmnee":
        if not labeled:
            raise ValueError("CMNEE splits must be labeled")
        return convert_cmnee(source, split, audit=audit)
    raise ValueError(f"{dataset}: unsupported source format {dataset_format}")


def _span_sanity(
    dataset_files: dict[str, list[Path]], sample_size: int, seed: int
) -> dict[str, Any]:
    import numpy as np

    report: dict[str, Any] = {"seed": seed, "sample_size_per_dataset": sample_size}
    for dataset, paths in sorted(dataset_files.items()):
        rng = np.random.default_rng(seed)
        reservoir: list[dict[str, Any]] = []
        seen = 0
        for path in paths:
            for record in iter_jsonl(path):
                for entity_index, entity in enumerate(record["entities"]):
                    if record["text"][entity["start"] : entity["end"]] != entity["span"]:
                        raise AssertionError(f"span mismatch in {path}: {record['id']}")
                    seen += 1
                    item = {
                        "file": path.name,
                        "id": record["id"],
                        "entity_index": entity_index,
                        "start": entity["start"],
                        "end": entity["end"],
                        "type": entity["type"],
                        "span": entity["span"],
                    }
                    if len(reservoir) < sample_size:
                        reservoir.append(item)
                    else:
                        replacement = int(rng.integers(0, seen))
                        if replacement < sample_size:
                            reservoir[replacement] = item
        if seen < sample_size:
            raise AssertionError(
                f"{dataset}: only {seen} entities are available for a {sample_size}-span sample"
            )
        report[dataset] = {
            "available_entities": seen,
            "checked": len(reservoir),
            "all_exact": True,
            "sample": reservoir,
        }
    return report


def _entity_type_counts(path: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in iter_jsonl(path):
        counts.update(entity["type"] for entity in record["entities"])
    return dict(sorted(counts.items()))


def prepare(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    data_root = Path(config["data_root"])
    report_root = Path(config["report_root"])
    data_root.mkdir(parents=True, exist_ok=True)
    report_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "phase": "P1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "datasets": {},
        "support": {},
    }
    labeled_outputs: dict[str, list[Path]] = {}
    train_outputs: dict[str, Path] = {}
    official_outputs: list[Path] = []
    derived_outputs: list[Path] = []

    for dataset, dataset_config in config["datasets"].items():
        dataset_report: dict[str, Any] = {
            "source": dataset_config["source"],
            "splits": {},
        }
        dataset_format = dataset_config["format"]
        for split, split_config in dataset_config["splits"].items():
            source_path = Path(split_config["input"])
            source_artifact = _verify_source(source_path, split_config["sha256"])
            output_path = data_root / split_config["output"]
            audit = ConversionAudit()
            records = _converter(
                dataset,
                dataset_format,
                source_path,
                split,
                bool(split_config["labeled"]),
                audit,
            )
            counts = write_jsonl_atomic(output_path, records)
            expected_records = split_config.get("expected_records")
            if expected_records is not None and counts["records"] != expected_records:
                raise AssertionError(
                    f"{dataset}/{split}: expected {expected_records} rows, got {counts['records']}"
                )
            reloaded_counts = validate_jsonl(output_path)
            if reloaded_counts != counts:
                raise AssertionError(f"{output_path}: write/read counts differ")
            if not split_config["labeled"] and (
                counts["entities"] or counts["relations"]
            ):
                raise AssertionError(f"{output_path}: unlabeled split contains gold labels")
            split_report = {
                "labeled": bool(split_config["labeled"]),
                "source": source_artifact,
                "output": {
                    "path": str(output_path),
                    "bytes": output_path.stat().st_size,
                    "sha256": sha256_file(output_path),
                    **counts,
                },
                "audit": audit.to_dict(),
                "round_trip": True,
            }
            dataset_report["splits"][split] = split_report
            official_outputs.append(output_path)
            if split_config["labeled"]:
                labeled_outputs.setdefault(dataset, []).append(output_path)
            if split == "train":
                train_outputs[dataset] = output_path
        report["datasets"][dataset] = dataset_report

    cluener_protocol = config["cluener_protocol"]
    cluener_source = train_outputs["cluener"]
    partition = partition_record_ids(
        cluener_source,
        tune_fraction=float(cluener_protocol["tune_fraction"]),
        seed=int(cluener_protocol["seed"]),
    )
    cluener_pool = data_root / cluener_protocol["pool_output"]
    cluener_tune = data_root / cluener_protocol["tune_output"]
    pool_counts = write_jsonl_atomic(
        cluener_pool, iter_selected_records(cluener_source, partition.pool_ids)
    )
    tune_counts = write_jsonl_atomic(
        cluener_tune, iter_selected_records(cluener_source, partition.tune_ids)
    )
    source_counts = validate_jsonl(cluener_source)
    if pool_counts["records"] + tune_counts["records"] != source_counts["records"]:
        raise AssertionError("CLUENER pool and tune partitions do not cover official train")
    pool_types = _entity_type_counts(cluener_pool)
    tune_types = _entity_type_counts(cluener_tune)
    if set(pool_types) != set(tune_types):
        raise AssertionError("CLUENER pool and tune partitions have different type coverage")
    report["cluener_protocol"] = {
        "evaluation_file": str(data_root / cluener_protocol["evaluation_output"]),
        "evaluation_role": "frozen_official_dev",
        "seed": partition.seed,
        "tune_fraction": partition.tune_fraction,
        "pool": {
            "path": str(cluener_pool),
            "sha256": sha256_file(cluener_pool),
            "bytes": cluener_pool.stat().st_size,
            "counts": pool_counts,
            "entity_type_counts": pool_types,
        },
        "tune": {
            "path": str(cluener_tune),
            "sha256": sha256_file(cluener_tune),
            "bytes": cluener_tune.stat().st_size,
            "counts": tune_counts,
            "entity_type_counts": tune_types,
        },
        "disjoint_cover": True,
    }
    train_outputs["cluener"] = cluener_pool
    derived_outputs.extend([cluener_pool, cluener_tune])

    for dataset, train_path in sorted(train_outputs.items()):
        report["support"][dataset] = {}
        for k in config["shots"]:
            selection = choose_support_ids(train_path, k=int(k), seed=int(config["seed"]))
            support_path = data_root / f"{dataset}_support_k{k}_seed{config['seed']}.jsonl"
            counts = write_jsonl_atomic(
                support_path, iter_selected_records(train_path, selection.selected_ids)
            )
            support_report = selection.report()
            support_report.update(
                {
                    "k": int(k),
                    "seed": int(config["seed"]),
                    "path": str(support_path),
                    "bytes": support_path.stat().st_size,
                    "sha256": sha256_file(support_path),
                    "counts": counts,
                }
            )
            report["support"][dataset][f"k{k}"] = support_report

    span_report = _span_sanity(
        labeled_outputs,
        int(config["span_sanity_per_dataset"]),
        int(config["seed"]),
    )
    span_report_path = report_root / "span_sanity.json"
    _write_json_atomic(span_report_path, span_report)

    report["gate1"] = {
        "official_jsonl_files": len(official_outputs),
        "all_round_trips_passed": True,
        "span_samples_checked": sum(
            value["checked"]
            for key, value in span_report.items()
            if key not in {"seed", "sample_size_per_dataset"}
        ),
        "all_sampled_spans_exact": True,
        "unlabeled_official_tests": [
            "cluener_test_unlabeled.jsonl",
            "duie_test_unlabeled.jsonl",
        ],
        "cluener_evaluation_file": cluener_protocol["evaluation_output"],
        "cluener_support_pool": cluener_protocol["pool_output"],
        "cluener_tuning_file": cluener_protocol["tune_output"],
        "cluener_protocol_disjoint": True,
    }
    report_path = report_root / "conversion_report.json"
    _write_json_atomic(report_path, report)

    manifest_paths = official_outputs + derived_outputs + [
        Path(item["path"])
        for dataset_support in report["support"].values()
        for item in dataset_support.values()
    ] + [span_report_path, report_path]
    artifact_manifest = [
        {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "source_location": str(path),
            "backup_location": "pending durable P1 backup",
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
        for path in sorted(manifest_paths)
    ]
    manifest_path = report_root / "artifact_manifest.json"
    _write_json_atomic(manifest_path, artifact_manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "p1_public_data.yaml",
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    started = time.monotonic()
    config = _load_config(config_path)
    log_path = Path(config["log_path"])
    event: dict[str, Any] = {
        "phase": "P1",
        "step": "prepare_public_data",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
    }
    try:
        report = prepare(config_path)
        event.update(
            {
                "status": "ok",
                "duration_seconds": round(time.monotonic() - started, 3),
                "gate1": report["gate1"],
            }
        )
        _append_log(log_path, event)
        print(json.dumps(report["gate1"], ensure_ascii=False, sort_keys=True))
        return 0
    except BaseException as exc:
        event.update(
            {
                "status": "error",
                "duration_seconds": round(time.monotonic() - started, 3),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        _append_log(log_path, event)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
