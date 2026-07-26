#!/usr/bin/env python3
"""Prepare a text-only, non-test calibration package for P6-QA1R.

Run only on AutoDL in GPU-free mode. The script locks the existing domain-dev
file, uses text-only heuristics to cover known ambiguity families, and exports
blank independently shuffled A/B sheets. Existing dev entities and relations
are never copied to annotator artifacts or used as calibration answers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


EXPECTED_DEV_SHA256 = "ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b"
EXPECTED_DEV_ROWS = 50
CALIBRATION_ROWS = 24
PER_BUCKET_TARGET = 6
SELECTION_SEED = 2026072601
ANNOTATOR_A_SEED = 2026072602
ANNOTATOR_B_SEED = 2026072603
CSV_FIELDS = ("blind_id", "text", "entities_json", "notes", "uncertainty_code")
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
BUCKET_ORDER = ("METRIC", "TECH_SCHEME", "EQUIPMENT_MODULE", "REPEATED_MENTION")
METRIC_PATTERN = re.compile(
    r"(?:\d|公里|千米|毫米|厘米|米|千克|公斤|克|赫兹|吉赫|兆赫|"
    r"射程|航程|速度|频率|误差|精度|口径|重量|质量|温度|时间|高度|深度)"
)
TECH_PATTERN = re.compile(
    r"(?:技术|方案|算法|方法|体制|机制|流程|模式|导航|制导|探测|跟踪|控制|通信)"
)
EQUIPMENT_MODULE_PATTERN = re.compile(
    r"(?:系统|模块|单元|组件|部件|装置|平台|载荷|天线|传感器|发动机|引信|雷达|声呐)"
)
REPEAT_TERMS = (
    "系统",
    "模块",
    "单元",
    "装置",
    "平台",
    "雷达",
    "天线",
    "传感器",
    "导航",
    "制导",
    "通信",
    "飞行器",
)


@dataclass(frozen=True)
class CalibrationConfig:
    dev_jsonl: Path
    output_dir: Path
    selection_seed: int = SELECTION_SEED
    annotator_a_seed: int = ANNOTATOR_A_SEED
    annotator_b_seed: int = ANNOTATOR_B_SEED


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare blank non-test P6-QA1R calibration sheets."
    )
    parser.add_argument(
        "--dev-jsonl", default="/root/autodl-tmp/data/domain_dev.jsonl"
    )
    parser.add_argument(
        "--output-dir",
        default="/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726",
    )
    parser.add_argument("--selection-seed", type=int, default=SELECTION_SEED)
    parser.add_argument("--annotator-a-seed", type=int, default=ANNOTATOR_A_SEED)
    parser.add_argument("--annotator-b-seed", type=int, default=ANNOTATOR_B_SEED)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_dev_texts(
    path: Path,
    *,
    expected_sha256: str = EXPECTED_DEV_SHA256,
    expected_rows: int = EXPECTED_DEV_ROWS,
) -> list[dict[str, str]]:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ValueError(f"domain-dev SHA256 mismatch: expected {expected_sha256}, got {actual}")
    records: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank JSONL line at {path}:{line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"non-object dev row at {path}:{line_number}")
            original_id = row.get("id")
            text = row.get("text")
            if not isinstance(original_id, str) or not original_id:
                raise ValueError(f"missing dev id at row {line_number}")
            if not isinstance(text, str) or not text:
                raise ValueError(f"missing dev text for {original_id}")
            if text.startswith(FORMULA_PREFIXES):
                raise ValueError(f"spreadsheet formula-prefix risk for {original_id}")
            records.append({"original_id": original_id, "text": text})
    if len(records) != expected_rows:
        raise ValueError(f"expected {expected_rows} dev rows, got {len(records)}")
    ids = [record["original_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate domain-dev IDs")
    return records


def text_buckets(text: str) -> set[str]:
    buckets: set[str] = set()
    if METRIC_PATTERN.search(text):
        buckets.add("METRIC")
    if TECH_PATTERN.search(text):
        buckets.add("TECH_SCHEME")
    if EQUIPMENT_MODULE_PATTERN.search(text):
        buckets.add("EQUIPMENT_MODULE")
    if any(text.count(term) >= 2 for term in REPEAT_TERMS):
        buckets.add("REPEATED_MENTION")
    return buckets


def stable_key(record: dict[str, str], seed: int, bucket: str) -> str:
    payload = f"{seed}:{bucket}:{record['original_id']}:{text_sha256(record['text'])}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def select_calibration_records(
    records: list[dict[str, str]],
    *,
    total: int = CALIBRATION_ROWS,
    per_bucket: int = PER_BUCKET_TARGET,
    seed: int = SELECTION_SEED,
) -> list[dict[str, str]]:
    if total <= 0 or total > len(records):
        raise ValueError("calibration total must be within available record count")
    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()

    for bucket in BUCKET_ORDER:
        candidates = [record for record in records if bucket in text_buckets(record["text"])]
        candidates.sort(key=lambda record: stable_key(record, seed, bucket))
        added = 0
        for record in candidates:
            if record["original_id"] in selected_ids:
                continue
            selected.append(record | {"selection_bucket": bucket})
            selected_ids.add(record["original_id"])
            added += 1
            if added >= per_bucket or len(selected) >= total:
                break
        if len(selected) >= total:
            break

    if len(selected) < total:
        remaining = [record for record in records if record["original_id"] not in selected_ids]
        remaining.sort(key=lambda record: stable_key(record, seed, "FILL"))
        for record in remaining[: total - len(selected)]:
            selected.append(record | {"selection_bucket": "FILL"})
            selected_ids.add(record["original_id"])

    if len(selected) != total or len(selected_ids) != total:
        raise ValueError("failed to select the requested unique calibration rows")
    return selected


def make_annotator_rows(
    records: list[dict[str, str]], seed: int, annotator: str
) -> tuple[list[dict[str, str]], dict[str, str]]:
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    rows: list[dict[str, str]] = []
    blind_ids: dict[str, str] = {}
    for position, record in enumerate(shuffled, start=1):
        blind_id = f"P6CAL-{annotator}-{position:03d}"
        blind_ids[record["original_id"]] = blind_id
        rows.append(
            {
                "blind_id": blind_id,
                "text": record["text"],
                "entities_json": "",
                "notes": "",
                "uncertainty_code": "",
            }
        )
    return rows, blind_ids


def csv_payload(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_ALL, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def jsonl_payload(rows: list[dict[str, str]]) -> bytes:
    return (
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in rows
        )
        + "\n"
    ).encode("utf-8")


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


def metadata(path: Path, role: str, rows: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if rows is not None:
        result["rows"] = rows
    return result


def prepare_calibration(
    config: CalibrationConfig,
    *,
    expected_dev_sha256: str = EXPECTED_DEV_SHA256,
    expected_dev_rows: int = EXPECTED_DEV_ROWS,
    calibration_rows: int = CALIBRATION_ROWS,
) -> dict[str, Any]:
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {config.output_dir}")
    if config.annotator_a_seed == config.annotator_b_seed:
        raise ValueError("annotator A/B seeds must differ")
    data_root = config.dev_jsonl.resolve().parent
    output_resolved = config.output_dir.resolve()
    if output_resolved == data_root or data_root in output_resolved.parents:
        raise ValueError("calibration output must be outside the data directory")

    records = read_dev_texts(
        config.dev_jsonl,
        expected_sha256=expected_dev_sha256,
        expected_rows=expected_dev_rows,
    )
    selected = select_calibration_records(
        records,
        total=calibration_rows,
        per_bucket=min(PER_BUCKET_TARGET, calibration_rows),
        seed=config.selection_seed,
    )
    a_rows, a_ids = make_annotator_rows(selected, config.annotator_a_seed, "A")
    b_rows, b_ids = make_annotator_rows(selected, config.annotator_b_seed, "B")
    if [row["text"] for row in a_rows] == [row["text"] for row in b_rows]:
        raise ValueError("A/B calibration orders unexpectedly match")

    map_rows = [
        {
            "original_id": record["original_id"],
            "annotator_a_blind_id": a_ids[record["original_id"]],
            "annotator_b_blind_id": b_ids[record["original_id"]],
            "text_sha256": text_sha256(record["text"]),
            "selection_bucket": record["selection_bucket"],
        }
        for record in selected
    ]

    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = config.output_dir.parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        a_path = staging / "annotator_a_calibration.csv"
        b_path = staging / "annotator_b_calibration.csv"
        map_path = staging / "coordinator_map.jsonl"
        write_atomic(a_path, csv_payload(a_rows))
        write_atomic(b_path, csv_payload(b_rows))
        write_atomic(map_path, jsonl_payload(map_rows))
        final = {
            "annotator_a": config.output_dir / a_path.name,
            "annotator_b": config.output_dir / b_path.name,
            "coordinator_map": config.output_dir / map_path.name,
        }
        bucket_counts: dict[str, int] = {}
        for record in selected:
            bucket = record["selection_bucket"]
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        manifest = {
            "phase": "P6-QA1R-CALIBRATION-PREP",
            "status": "prepared_not_annotated",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scope": {
                "source_split": "domain_dev",
                "records": len(selected),
                "task": "NER",
                "test_read": False,
                "predictions_read": False,
                "model_calls": False,
                "existing_dev_labels_exported": False,
                "formal_iaa": False,
            },
            "input": {
                "path": str(config.dev_jsonl),
                "rows": len(records),
                "sha256": sha256_file(config.dev_jsonl),
            },
            "selection": {
                "method": "text_only_heuristic_buckets_then_sha256_fill",
                "selection_seed": config.selection_seed,
                "bucket_counts": dict(sorted(bucket_counts.items())),
            },
            "blind_generation": {
                "annotator_a_seed": config.annotator_a_seed,
                "annotator_b_seed": config.annotator_b_seed,
                "orders_differ": True,
            },
            "annotator_csv_fields": list(CSV_FIELDS),
            "forbidden_annotator_content": [
                "original IDs",
                "existing dev entities or relations",
                "old test gold",
                "model predictions or suggestions",
                "the other annotator's labels",
                "coordinator mapping",
            ],
            "outputs": {
                "annotator_a": metadata(a_path, "annotator_a_only", len(a_rows))
                | {"path": str(final["annotator_a"])},
                "annotator_b": metadata(b_path, "annotator_b_only", len(b_rows))
                | {"path": str(final["annotator_b"])},
                "coordinator_map": metadata(map_path, "coordinator_only", len(map_rows))
                | {"path": str(final["coordinator_map"])},
            },
            "next_gate": (
                "Two real humans independently annotate these calibration sheets, "
                "then jointly resolve guideline ambiguities; this is not formal test IAA."
            ),
        }
        manifest_path = staging / "manifest.json"
        write_atomic(
            manifest_path,
            (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
        for path in (a_path, b_path, map_path, manifest_path):
            os.chmod(path, 0o600)
        os.replace(staging, config.output_dir)
        os.chmod(config.output_dir, 0o700)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    config = CalibrationConfig(
        dev_jsonl=Path(args.dev_jsonl),
        output_dir=Path(args.output_dir),
        selection_seed=args.selection_seed,
        annotator_a_seed=args.annotator_a_seed,
        annotator_b_seed=args.annotator_b_seed,
    )
    manifest = prepare_calibration(config)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "records": manifest["scope"]["records"],
                "bucket_counts": manifest["selection"]["bucket_counts"],
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
