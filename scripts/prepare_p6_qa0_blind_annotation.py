#!/usr/bin/env python3
"""Prepare blank, blinded P6-QA0 NER annotation sheets.

Run this script only on AutoDL in GPU-free mode. It reads the frozen P2 test
text and coordinator metadata, but it never copies prior entities, relations,
predictions, prompts, titles, source URLs, or original IDs into annotator CSVs.
The frozen inputs are read-only and must match the locked P2 hash.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import random
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


EXPECTED_TEST_SHA256 = "42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0"
EXPECTED_TEST_ROWS = 170
ANNOTATOR_A_SEED = 2026072501
ANNOTATOR_B_SEED = 2026072502
CSV_FIELDS = ("blind_id", "text", "entities_json", "notes")
KNOWN_PRIOR_LABEL_SOURCES = {
    "adjudicated_double_annotation",
    "annotator_a_single_annotation",
}
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


@dataclass(frozen=True)
class PreparationConfig:
    test_jsonl: Path
    source_map_jsonl: Path
    frozen_marker: Path
    output_dir: Path
    annotator_a_seed: int = ANNOTATOR_A_SEED
    annotator_b_seed: int = ANNOTATOR_B_SEED


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare blank A/B NER sheets for the bounded P6-QA0 gate."
    )
    parser.add_argument(
        "--test-jsonl",
        default="/root/autodl-tmp/data/domain_test.jsonl",
    )
    parser.add_argument(
        "--source-map-jsonl",
        default="/root/autodl-tmp/data/domain_gold_source_map.jsonl",
    )
    parser.add_argument(
        "--frozen-marker",
        default="/root/autodl-tmp/data/FROZEN",
    )
    parser.add_argument(
        "--output-dir",
        default=(
            "/root/autodl-tmp/backup/p6/"
            "p6_qa0_blind_annotation_20260725"
        ),
    )
    parser.add_argument("--annotator-a-seed", type=int, default=ANNOTATOR_A_SEED)
    parser.add_argument("--annotator-b-seed", type=int, default=ANNOTATOR_B_SEED)
    return parser.parse_args()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


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


def validate_frozen_marker(path: Path, expected_rows: int) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"frozen marker not found: {path}")
    marker = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(marker, dict):
        raise ValueError("frozen marker must be a JSON object")
    if marker.get("phase") != "P2" or marker.get("test_size") != expected_rows:
        raise ValueError("frozen marker phase/test_size does not match P2 test")
    return marker


def validate_test_records(
    path: Path,
    expected_sha256: str,
    expected_rows: int,
) -> list[dict[str, str]]:
    actual_sha256 = sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "frozen test SHA256 mismatch: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    raw_rows = read_jsonl(path)
    if len(raw_rows) != expected_rows:
        raise ValueError(f"expected {expected_rows} test rows, got {len(raw_rows)}")

    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(raw_rows, start=1):
        original_id = row.get("id")
        text = row.get("text")
        if not isinstance(original_id, str) or not original_id:
            raise ValueError(f"missing string id in test row {index}")
        if original_id in seen_ids:
            raise ValueError(f"duplicate test id: {original_id}")
        if not isinstance(text, str) or not text:
            raise ValueError(f"missing text for test id {original_id}")
        if text.startswith(FORMULA_PREFIXES):
            raise ValueError(f"spreadsheet formula-prefix risk for test id {original_id}")
        seen_ids.add(original_id)
        rows.append({"original_id": original_id, "text": text})
    return rows


def load_test_source_metadata(
    path: Path,
    test_records: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    raw_rows = read_jsonl(path)
    test_metadata: dict[str, dict[str, str]] = {}
    for index, row in enumerate(raw_rows, start=1):
        if row.get("split") != "test":
            continue
        original_id = row.get("id")
        if not isinstance(original_id, str) or not original_id:
            raise ValueError(f"missing source-map id in row {index}")
        if original_id in test_metadata:
            raise ValueError(f"duplicate test source-map id: {original_id}")
        source_type = row.get("source_type")
        label_source = row.get("label_source")
        source_text_sha256 = row.get("text_sha256")
        if not isinstance(source_type, str) or not source_type:
            raise ValueError(f"missing source_type for {original_id}")
        if label_source not in KNOWN_PRIOR_LABEL_SOURCES:
            raise ValueError(f"unexpected prior label_source for {original_id}")
        if not isinstance(source_text_sha256, str) or len(source_text_sha256) != 64:
            raise ValueError(f"invalid text_sha256 for {original_id}")
        test_metadata[original_id] = {
            "source_type": source_type,
            "prior_label_source": label_source,
            "text_sha256": source_text_sha256,
        }

    test_ids = {row["original_id"] for row in test_records}
    metadata_ids = set(test_metadata)
    if metadata_ids != test_ids:
        missing = sorted(test_ids - metadata_ids)
        extra = sorted(metadata_ids - test_ids)
        raise ValueError(
            f"test/source-map ID mismatch: missing={missing[:5]}, extra={extra[:5]}"
        )
    for row in test_records:
        original_id = row["original_id"]
        actual_text_hash = text_sha256(row["text"])
        if test_metadata[original_id]["text_sha256"] != actual_text_hash:
            raise ValueError(f"source-map text hash mismatch for {original_id}")
    return test_metadata


def shuffled_rows(
    records: list[dict[str, str]],
    seed: int,
    annotator: str,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    rows: list[dict[str, str]] = []
    blind_ids: dict[str, str] = {}
    for position, record in enumerate(shuffled, start=1):
        blind_id = f"P6QA0-{annotator}-{position:04d}"
        blind_ids[record["original_id"]] = blind_id
        rows.append(
            {
                "blind_id": blind_id,
                "text": record["text"],
                "entities_json": "",
                "notes": "",
            }
        )
    return rows, blind_ids


def csv_payload(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_FIELDS,
        quoting=csv.QUOTE_ALL,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8-sig")


def jsonl_payload(rows: list[dict[str, str]]) -> bytes:
    lines = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return (("\n".join(lines)) + "\n").encode("utf-8")


def write_bytes_atomic(path: Path, payload: bytes) -> None:
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


def output_metadata(path: Path, rows: int, role: str, encoding: str) -> dict[str, Any]:
    return {
        "path": str(path),
        "role": role,
        "rows": rows,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "encoding": encoding,
    }


def prepare_annotation_package(
    config: PreparationConfig,
    *,
    expected_test_sha256: str = EXPECTED_TEST_SHA256,
    expected_test_rows: int = EXPECTED_TEST_ROWS,
) -> dict[str, Any]:
    if config.annotator_a_seed == config.annotator_b_seed:
        raise ValueError("annotator A/B seeds must be distinct")
    if config.output_dir.exists():
        raise FileExistsError(
            f"output directory already exists; refusing to overwrite: {config.output_dir}"
        )

    data_root = config.test_jsonl.resolve().parent
    output_resolved = config.output_dir.resolve()
    if output_resolved == data_root or data_root in output_resolved.parents:
        raise ValueError("output directory must not be inside the frozen data directory")

    validate_frozen_marker(config.frozen_marker, expected_test_rows)
    test_records = validate_test_records(
        config.test_jsonl,
        expected_test_sha256,
        expected_test_rows,
    )
    source_metadata = load_test_source_metadata(config.source_map_jsonl, test_records)

    a_rows, a_blind_ids = shuffled_rows(
        test_records,
        config.annotator_a_seed,
        "A",
    )
    b_rows, b_blind_ids = shuffled_rows(
        test_records,
        config.annotator_b_seed,
        "B",
    )
    a_order = [row["text"] for row in a_rows]
    b_order = [row["text"] for row in b_rows]
    if a_order == b_order:
        raise ValueError("annotator A/B shuffles unexpectedly produced the same order")

    coordinator_rows: list[dict[str, str]] = []
    for record in test_records:
        original_id = record["original_id"]
        metadata = source_metadata[original_id]
        coordinator_rows.append(
            {
                "original_id": original_id,
                "annotator_a_blind_id": a_blind_ids[original_id],
                "annotator_b_blind_id": b_blind_ids[original_id],
                "text_sha256": metadata["text_sha256"],
                "source_type": metadata["source_type"],
                "prior_label_source": metadata["prior_label_source"],
            }
        )

    output_parent = config.output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    staging_dir = output_parent / f".{config.output_dir.name}.tmp-{uuid4().hex}"
    staging_dir.mkdir(mode=0o700)
    try:
        a_path = staging_dir / "annotator_a_blind.csv"
        b_path = staging_dir / "annotator_b_blind.csv"
        map_path = staging_dir / "blind_id_map.jsonl"
        write_bytes_atomic(a_path, csv_payload(a_rows))
        write_bytes_atomic(b_path, csv_payload(b_rows))
        write_bytes_atomic(map_path, jsonl_payload(coordinator_rows))

        final_a_path = config.output_dir / a_path.name
        final_b_path = config.output_dir / b_path.name
        final_map_path = config.output_dir / map_path.name
        manifest = {
            "phase": "P6-QA0",
            "gate": "P6_QA0_BLANK_DOUBLE_ANNOTATION_PREP_APPROVED",
            "status": "prepared_not_annotated",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scope": {
                "task": "NER",
                "records": expected_test_rows,
                "relations_in_scope": False,
                "model_calls": False,
                "frozen_data_modified": False,
            },
            "inputs": {
                "frozen_test": {
                    "path": str(config.test_jsonl),
                    "rows": len(test_records),
                    "sha256": sha256_file(config.test_jsonl),
                },
                "source_map": {
                    "path": str(config.source_map_jsonl),
                    "rows_total": len(read_jsonl(config.source_map_jsonl)),
                    "rows_test": len(source_metadata),
                    "sha256": sha256_file(config.source_map_jsonl),
                },
                "frozen_marker": {
                    "path": str(config.frozen_marker),
                    "sha256": sha256_file(config.frozen_marker),
                },
            },
            "blind_generation": {
                "annotator_a_seed": config.annotator_a_seed,
                "annotator_b_seed": config.annotator_b_seed,
                "blind_ids_distinct_across_annotators": set(a_blind_ids.values()).isdisjoint(
                    b_blind_ids.values()
                ),
                "orders_differ": a_order != b_order,
            },
            "annotator_csv_field_allowlist": list(CSV_FIELDS),
            "forbidden_annotator_content": [
                "original IDs",
                "prior entities or relations",
                "model predictions or machine suggestions",
                "prompts",
                "titles",
                "source metadata",
                "coordinator mapping",
                "the other annotator's labels",
            ],
            "safeguards": {
                "exact_frozen_test_sha256_required": expected_test_sha256,
                "frozen_marker_required": True,
                "test_source_map_text_hashes_matched": True,
                "annotation_fields_blank": True,
                "csv_quote_all": True,
                "csv_formula_prefix_check": True,
                "output_outside_frozen_data_root": True,
                "existing_output_overwrite_refused": True,
                "coordinator_map_not_for_annotators": True,
            },
            "outputs": {
                "annotator_a": output_metadata(
                    a_path, len(a_rows), "annotator_only", "UTF-8 BOM CSV"
                )
                | {"path": str(final_a_path)},
                "annotator_b": output_metadata(
                    b_path, len(b_rows), "annotator_only", "UTF-8 BOM CSV"
                )
                | {"path": str(final_b_path)},
                "coordinator_map": output_metadata(
                    map_path, len(coordinator_rows), "coordinator_only", "UTF-8 JSONL"
                )
                | {"path": str(final_map_path)},
            },
        }
        manifest_path = staging_dir / "manifest.json"
        manifest_payload = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        write_bytes_atomic(manifest_path, manifest_payload)

        os.chmod(a_path, 0o600)
        os.chmod(b_path, 0o600)
        os.chmod(map_path, 0o600)
        os.chmod(manifest_path, 0o600)
        os.replace(staging_dir, config.output_dir)
        os.chmod(config.output_dir, 0o700)
        return manifest
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise


def main() -> int:
    args = parse_args()
    config = PreparationConfig(
        test_jsonl=Path(args.test_jsonl),
        source_map_jsonl=Path(args.source_map_jsonl),
        frozen_marker=Path(args.frozen_marker),
        output_dir=Path(args.output_dir),
        annotator_a_seed=args.annotator_a_seed,
        annotator_b_seed=args.annotator_b_seed,
    )
    manifest = prepare_annotation_package(config)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "output_dir": str(config.output_dir),
                "records": manifest["scope"]["records"],
                "frozen_test_sha256": manifest["inputs"]["frozen_test"]["sha256"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
