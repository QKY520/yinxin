#!/usr/bin/env python3
"""Prepare a fresh, text-only P6-QA1R calibration package.

Run only on AutoDL in GPU-free mode. The retired 24-row calibration set is
excluded by locked text hashes. Only domain-dev IDs and text are used for
selection; existing entity and relation labels are not exported or used as
answers. Annotator A/B delivery directories are separated from coordinator
maps and contain blank fields plus the locked v4 guideline and role-specific
instructions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from prepare_p6_qa1r_calibration import (
        BUCKET_ORDER,
        CSV_FIELDS,
        EXPECTED_DEV_ROWS,
        EXPECTED_DEV_SHA256,
        csv_payload,
        jsonl_payload,
        metadata,
        read_dev_texts,
        stable_key,
        text_buckets,
        text_sha256,
        write_atomic,
    )
except ModuleNotFoundError:  # imported as scripts.* from repository root
    from scripts.prepare_p6_qa1r_calibration import (
        BUCKET_ORDER,
        CSV_FIELDS,
        EXPECTED_DEV_ROWS,
        EXPECTED_DEV_SHA256,
        csv_payload,
        jsonl_payload,
        metadata,
        read_dev_texts,
        stable_key,
        text_buckets,
        text_sha256,
        write_atomic,
    )


EXPECTED_RETIRED_MAP_SHA256 = (
    "a42511bd41bef0666c703c8d4e6ca1eb623688bba0e3b872786f164fedb3b18b"
)
EXPECTED_RETIRED_ROWS = 24
EXPECTED_UNUSED_ROWS = 26
EXPECTED_GUIDELINE_SHA256 = (
    "a15289cd0f45bc23a0ce9d981db24745b814cfb94c6b03687e60a13b81b6ca80"
)
EXPECTED_A_INSTRUCTIONS_SHA256 = (
    "5f0cf56819a10e76e0a2639257b8c051af213e4ee2dfe6accdbf077509e9b136"
)
EXPECTED_B_INSTRUCTIONS_SHA256 = (
    "432acf0f19315e9eb089726126c33aabc9e7830d2fe7ea243078c4f3ea180c65"
)
CALIBRATION_ROWS = 20
PER_BUCKET_TARGET = 5
SELECTION_SEED = 2026072701
ANNOTATOR_A_SEED = 2026072702
ANNOTATOR_B_SEED = 2026072703
GUIDELINE_NAME = "P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md"
A_INSTRUCTIONS_NAME = "P6_QA1R_ANNOTATOR_A_INSTRUCTIONS_V4_20260727.md"
B_INSTRUCTIONS_NAME = "P6_QA1R_ANNOTATOR_B_INSTRUCTIONS_V4_20260727.md"
A_SHEET_NAME = "annotator_a_fresh_calibration.csv"
B_SHEET_NAME = "annotator_b_fresh_calibration.csv"
RETIRED_MAP_FIELDS = {
    "original_id",
    "annotator_a_blind_id",
    "annotator_b_blind_id",
    "text_sha256",
    "selection_bucket",
}


@dataclass(frozen=True)
class FreshCalibrationConfig:
    dev_jsonl: Path
    retired_map: Path
    guideline: Path
    annotator_a_instructions: Path
    annotator_b_instructions: Path
    output_dir: Path
    selection_seed: int = SELECTION_SEED
    annotator_a_seed: int = ANNOTATOR_A_SEED
    annotator_b_seed: int = ANNOTATOR_B_SEED


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare excluded, blank P6-QA1R fresh calibration sheets."
    )
    parser.add_argument(
        "--dev-jsonl", default="/root/autodl-tmp/data/domain_dev.jsonl"
    )
    parser.add_argument(
        "--retired-map",
        default=(
            "/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726/"
            "coordinator_map.jsonl"
        ),
    )
    parser.add_argument(
        "--guideline",
        default=f"/root/project/docs/{GUIDELINE_NAME}",
    )
    parser.add_argument(
        "--annotator-a-instructions",
        default=f"/root/project/docs/{A_INSTRUCTIONS_NAME}",
    )
    parser.add_argument(
        "--annotator-b-instructions",
        default=f"/root/project/docs/{B_INSTRUCTIONS_NAME}",
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "/root/autodl-tmp/backup/p6/"
            "p6_qa1r_fresh_calibration_20260727"
        ),
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


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{label} SHA256 mismatch: expected {expected}, got {actual}")


def read_retired_hashes(
    path: Path,
    *,
    expected_sha256: str = EXPECTED_RETIRED_MAP_SHA256,
    expected_rows: int = EXPECTED_RETIRED_ROWS,
) -> tuple[set[str], set[str]]:
    require_hash(path, expected_sha256, "retired coordinator map")
    original_ids: set[str] = set()
    hashes: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ValueError(f"blank retired-map line at {path}:{line_number}")
            row = json.loads(line)
            if not isinstance(row, dict) or set(row) != RETIRED_MAP_FIELDS:
                raise ValueError(f"retired-map field mismatch at line {line_number}")
            original_id = row["original_id"]
            digest = row["text_sha256"]
            if not isinstance(original_id, str) or not original_id:
                raise ValueError(f"invalid retired original ID at line {line_number}")
            if (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError(f"invalid retired text hash at line {line_number}")
            if original_id in original_ids or digest in hashes:
                raise ValueError("retired coordinator map contains duplicate ID or text hash")
            original_ids.add(original_id)
            hashes.add(digest)
    if len(hashes) != expected_rows:
        raise ValueError(f"expected {expected_rows} retired rows, got {len(hashes)}")
    return original_ids, hashes


def unused_records(
    records: list[dict[str, str]],
    retired_ids: set[str],
    retired_hashes: set[str],
    *,
    expected_unused_rows: int | None = EXPECTED_UNUSED_ROWS,
) -> list[dict[str, str]]:
    dev_ids = {record["original_id"] for record in records}
    dev_hashes = {text_sha256(record["text"]) for record in records}
    if len(dev_hashes) != len(records):
        raise ValueError("domain-dev contains duplicate text hashes")
    if not retired_ids <= dev_ids or not retired_hashes <= dev_hashes:
        raise ValueError("retired coordinator map is not a subset of locked domain-dev")
    remaining = [
        record
        for record in records
        if record["original_id"] not in retired_ids
        and text_sha256(record["text"]) not in retired_hashes
    ]
    if expected_unused_rows is not None and len(remaining) != expected_unused_rows:
        raise ValueError(
            f"expected {expected_unused_rows} unused domain-dev rows, got {len(remaining)}"
        )
    return remaining


def select_balanced_records(
    records: list[dict[str, str]],
    *,
    per_bucket: int = PER_BUCKET_TARGET,
    seed: int = SELECTION_SEED,
) -> list[dict[str, str]]:
    if per_bucket <= 0:
        raise ValueError("per-bucket target must be positive")
    slots = [
        (bucket, position)
        for bucket in BUCKET_ORDER
        for position in range(1, per_bucket + 1)
    ]
    candidates: dict[tuple[str, int], list[dict[str, str]]] = {}
    for slot in slots:
        bucket = slot[0]
        eligible = [record for record in records if bucket in text_buckets(record["text"])]
        eligible.sort(key=lambda record: stable_key(record, seed, bucket))
        if len(eligible) < per_bucket:
            raise ValueError(
                f"insufficient unused candidates for {bucket}: {len(eligible)}"
            )
        candidates[slot] = eligible

    slot_for_record: dict[str, tuple[str, int]] = {}
    record_for_slot: dict[tuple[str, int], dict[str, str]] = {}

    def assign(slot: tuple[str, int], seen_records: set[str]) -> bool:
        for record in candidates[slot]:
            record_id = record["original_id"]
            if record_id in seen_records:
                continue
            seen_records.add(record_id)
            previous_slot = slot_for_record.get(record_id)
            if previous_slot is None or assign(previous_slot, seen_records):
                slot_for_record[record_id] = slot
                record_for_slot[slot] = record
                return True
        return False

    ordered_slots = sorted(
        slots,
        key=lambda slot: (len(candidates[slot]), BUCKET_ORDER.index(slot[0]), slot[1]),
    )
    for slot in ordered_slots:
        if not assign(slot, set()):
            raise ValueError("unable to assign unique records to all bucket slots")

    selected = [
        record_for_slot[(bucket, position)] | {"selection_bucket": bucket}
        for bucket in BUCKET_ORDER
        for position in range(1, per_bucket + 1)
    ]
    selected_ids = {record["original_id"] for record in selected}
    if len(selected) != len(slots) or len(selected_ids) != len(slots):
        raise ValueError("balanced selection did not produce unique requested rows")
    return selected


def make_fresh_annotator_rows(
    records: list[dict[str, str]], seed: int, annotator: str
) -> tuple[list[dict[str, str]], dict[str, str]]:
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    rows: list[dict[str, str]] = []
    blind_ids: dict[str, str] = {}
    for position, record in enumerate(shuffled, start=1):
        blind_id = f"P6FRESH-{annotator}-{position:03d}"
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


def file_metadata(path: Path, role: str, rows: int | None = None) -> dict[str, Any]:
    result = metadata(path, role, rows)
    result["path"] = str(path)
    return result


def prepare_fresh_calibration(
    config: FreshCalibrationConfig,
    *,
    expected_dev_sha256: str = EXPECTED_DEV_SHA256,
    expected_dev_rows: int = EXPECTED_DEV_ROWS,
    expected_retired_map_sha256: str = EXPECTED_RETIRED_MAP_SHA256,
    expected_retired_rows: int = EXPECTED_RETIRED_ROWS,
    expected_unused_rows: int | None = EXPECTED_UNUSED_ROWS,
    expected_guideline_sha256: str = EXPECTED_GUIDELINE_SHA256,
    expected_a_instructions_sha256: str = EXPECTED_A_INSTRUCTIONS_SHA256,
    expected_b_instructions_sha256: str = EXPECTED_B_INSTRUCTIONS_SHA256,
    calibration_rows: int = CALIBRATION_ROWS,
    per_bucket: int = PER_BUCKET_TARGET,
) -> dict[str, Any]:
    if config.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {config.output_dir}")
    if config.annotator_a_seed == config.annotator_b_seed:
        raise ValueError("annotator A/B seeds must differ")
    if calibration_rows != per_bucket * len(BUCKET_ORDER):
        raise ValueError("calibration rows must equal per-bucket target times bucket count")
    data_root = config.dev_jsonl.resolve().parent
    output_resolved = config.output_dir.resolve()
    if output_resolved == data_root or data_root in output_resolved.parents:
        raise ValueError("fresh calibration output must be outside the data directory")

    require_hash(config.guideline, expected_guideline_sha256, "locked guideline")
    require_hash(
        config.annotator_a_instructions,
        expected_a_instructions_sha256,
        "annotator A instructions",
    )
    require_hash(
        config.annotator_b_instructions,
        expected_b_instructions_sha256,
        "annotator B instructions",
    )
    records = read_dev_texts(
        config.dev_jsonl,
        expected_sha256=expected_dev_sha256,
        expected_rows=expected_dev_rows,
    )
    retired_ids, retired_hashes = read_retired_hashes(
        config.retired_map,
        expected_sha256=expected_retired_map_sha256,
        expected_rows=expected_retired_rows,
    )
    unused = unused_records(
        records,
        retired_ids,
        retired_hashes,
        expected_unused_rows=expected_unused_rows,
    )
    selected = select_balanced_records(
        unused,
        per_bucket=per_bucket,
        seed=config.selection_seed,
    )
    if len(selected) != calibration_rows:
        raise ValueError("fresh selection row count mismatch")
    selected_ids = {record["original_id"] for record in selected}
    selected_hashes = {text_sha256(record["text"]) for record in selected}
    if selected_ids & retired_ids or selected_hashes & retired_hashes:
        raise ValueError("fresh selection overlaps the retired calibration set")
    reserve = sorted(
        [record for record in unused if record["original_id"] not in selected_ids],
        key=lambda record: stable_key(record, config.selection_seed, "RESERVE"),
    )

    a_rows, a_ids = make_fresh_annotator_rows(
        selected, config.annotator_a_seed, "A"
    )
    b_rows, b_ids = make_fresh_annotator_rows(
        selected, config.annotator_b_seed, "B"
    )
    if [row["text"] for row in a_rows] == [row["text"] for row in b_rows]:
        raise ValueError("A/B fresh calibration orders unexpectedly match")
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
    reserve_rows = [
        {
            "original_id": record["original_id"],
            "text_sha256": text_sha256(record["text"]),
            "text_buckets": sorted(text_buckets(record["text"])),
        }
        for record in reserve
    ]
    bucket_candidate_counts = {
        bucket: sum(bucket in text_buckets(record["text"]) for record in unused)
        for bucket in BUCKET_ORDER
    }
    bucket_counts = {
        bucket: sum(record["selection_bucket"] == bucket for record in selected)
        for bucket in BUCKET_ORDER
    }

    config.output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = config.output_dir.parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        a_delivery = staging / "annotator_a_delivery"
        b_delivery = staging / "annotator_b_delivery"
        coordinator = staging / "coordinator_only"
        for directory in (a_delivery, b_delivery, coordinator):
            directory.mkdir(mode=0o700)

        a_sheet = a_delivery / A_SHEET_NAME
        b_sheet = b_delivery / B_SHEET_NAME
        a_guide = a_delivery / GUIDELINE_NAME
        b_guide = b_delivery / GUIDELINE_NAME
        a_instructions = a_delivery / A_INSTRUCTIONS_NAME
        b_instructions = b_delivery / B_INSTRUCTIONS_NAME
        coordinator_map = coordinator / "coordinator_map.jsonl"
        reserve_map = coordinator / "reserve_map.jsonl"

        write_atomic(a_sheet, csv_payload(a_rows))
        write_atomic(b_sheet, csv_payload(b_rows))
        write_atomic(a_guide, config.guideline.read_bytes())
        write_atomic(b_guide, config.guideline.read_bytes())
        write_atomic(a_instructions, config.annotator_a_instructions.read_bytes())
        write_atomic(b_instructions, config.annotator_b_instructions.read_bytes())
        write_atomic(coordinator_map, jsonl_payload(map_rows))
        write_atomic(reserve_map, jsonl_payload(reserve_rows))

        a_delivery_manifest = {
            "role": "annotator_a_only",
            "status": "blank_not_started",
            "sheet": file_metadata(a_sheet, "annotator_a_only", len(a_rows))
            | {"path": A_SHEET_NAME},
            "guideline": file_metadata(a_guide, "shared_locked_guideline")
            | {"path": GUIDELINE_NAME},
            "instructions": file_metadata(a_instructions, "annotator_a_only")
            | {"path": A_INSTRUCTIONS_NAME},
            "forbidden": [
                "annotator B delivery",
                "coordinator map",
                "old labels or gold",
                "predictions or model suggestions",
                "automatic label-writing scripts",
            ],
        }
        b_delivery_manifest = {
            "role": "annotator_b_only",
            "status": "blank_not_started",
            "sheet": file_metadata(b_sheet, "annotator_b_only", len(b_rows))
            | {"path": B_SHEET_NAME},
            "guideline": file_metadata(b_guide, "shared_locked_guideline")
            | {"path": GUIDELINE_NAME},
            "instructions": file_metadata(b_instructions, "annotator_b_only")
            | {"path": B_INSTRUCTIONS_NAME},
            "forbidden": [
                "annotator A delivery",
                "coordinator map",
                "old labels or gold",
                "predictions or model suggestions",
                "automatic label-writing scripts",
            ],
        }
        a_delivery_manifest_path = a_delivery / "delivery_manifest.json"
        b_delivery_manifest_path = b_delivery / "delivery_manifest.json"
        write_atomic(
            a_delivery_manifest_path,
            (
                json.dumps(
                    a_delivery_manifest,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8"),
        )
        write_atomic(
            b_delivery_manifest_path,
            (
                json.dumps(
                    b_delivery_manifest,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8"),
        )

        final_a = config.output_dir / "annotator_a_delivery"
        final_b = config.output_dir / "annotator_b_delivery"
        final_coordinator = config.output_dir / "coordinator_only"
        manifest = {
            "phase": "P6-QA1R-FRESH-CALIBRATION-PREP",
            "gate": "P6_QA1R_FRESH_CALIBRATION_PREP_APPROVED",
            "status": "prepared_blank_not_started",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scope": {
                "source_split": "domain_dev",
                "source_rows": len(records),
                "retired_rows_excluded": len(retired_hashes),
                "unused_pool_rows": len(unused),
                "selected_rows": len(selected),
                "reserve_rows": len(reserve),
                "task": "NER",
                "test_read": False,
                "predictions_read": False,
                "model_calls": False,
                "existing_dev_labels_exported": False,
                "existing_dev_labels_used_for_selection": False,
                "human_annotation_started": False,
                "formal_iaa": False,
            },
            "locked_inputs": {
                "domain_dev": {
                    "path": str(config.dev_jsonl),
                    "sha256": sha256_file(config.dev_jsonl),
                },
                "retired_coordinator_map": {
                    "path": str(config.retired_map),
                    "sha256": sha256_file(config.retired_map),
                },
                "guideline": {
                    "path": str(config.guideline),
                    "sha256": sha256_file(config.guideline),
                },
                "annotator_a_instructions": {
                    "path": str(config.annotator_a_instructions),
                    "sha256": sha256_file(config.annotator_a_instructions),
                },
                "annotator_b_instructions": {
                    "path": str(config.annotator_b_instructions),
                    "sha256": sha256_file(config.annotator_b_instructions),
                },
            },
            "selection": {
                "method": "retired-hash-exclusion_then_deterministic_bucket_matching",
                "selection_seed": config.selection_seed,
                "per_bucket_target": per_bucket,
                "bucket_candidate_counts": bucket_candidate_counts,
                "selected_bucket_counts": bucket_counts,
                "retired_overlap_rows": 0,
            },
            "blind_generation": {
                "annotator_a_seed": config.annotator_a_seed,
                "annotator_b_seed": config.annotator_b_seed,
                "blind_id_prefixes": ["P6FRESH-A", "P6FRESH-B"],
                "orders_differ": True,
            },
            "annotator_csv_fields": list(CSV_FIELDS),
            "outputs": {
                "annotator_a_sheet": file_metadata(
                    a_sheet, "annotator_a_only", len(a_rows)
                )
                | {"path": str(final_a / A_SHEET_NAME)},
                "annotator_b_sheet": file_metadata(
                    b_sheet, "annotator_b_only", len(b_rows)
                )
                | {"path": str(final_b / B_SHEET_NAME)},
                "annotator_a_delivery_manifest": file_metadata(
                    a_delivery_manifest_path, "annotator_a_only"
                )
                | {"path": str(final_a / a_delivery_manifest_path.name)},
                "annotator_b_delivery_manifest": file_metadata(
                    b_delivery_manifest_path, "annotator_b_only"
                )
                | {"path": str(final_b / b_delivery_manifest_path.name)},
                "coordinator_map": file_metadata(
                    coordinator_map, "coordinator_only", len(map_rows)
                )
                | {"path": str(final_coordinator / coordinator_map.name)},
                "reserve_map": file_metadata(
                    reserve_map, "coordinator_only", len(reserve_rows)
                )
                | {"path": str(final_coordinator / reserve_map.name)},
            },
            "next_gate": "P6_QA1R_FRESH_CALIBRATION_ANNOTATION_APPROVED",
            "next_gate_scope": (
                "Two different humans receive only their own delivery directory and "
                "independently annotate all rows; no comparison occurs before both "
                "completed files are hash-locked."
            ),
        }
        manifest_path = staging / "manifest.json"
        write_atomic(
            manifest_path,
            (
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8"),
        )
        for path in staging.rglob("*"):
            os.chmod(path, 0o700 if path.is_dir() else 0o600)
        os.replace(staging, config.output_dir)
        os.chmod(config.output_dir, 0o700)
        return manifest
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    config = FreshCalibrationConfig(
        dev_jsonl=Path(args.dev_jsonl),
        retired_map=Path(args.retired_map),
        guideline=Path(args.guideline),
        annotator_a_instructions=Path(args.annotator_a_instructions),
        annotator_b_instructions=Path(args.annotator_b_instructions),
        output_dir=Path(args.output_dir),
        selection_seed=args.selection_seed,
        annotator_a_seed=args.annotator_a_seed,
        annotator_b_seed=args.annotator_b_seed,
    )
    manifest = prepare_fresh_calibration(config)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "selected_rows": manifest["scope"]["selected_rows"],
                "reserve_rows": manifest["scope"]["reserve_rows"],
                "selected_bucket_counts": manifest["selection"][
                    "selected_bucket_counts"
                ],
                "output_dir": str(config.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
