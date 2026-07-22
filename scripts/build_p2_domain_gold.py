#!/usr/bin/env python3
"""Build and freeze the P2 self-built equipment-domain gold dataset.

Run on AutoDL in GPU-free mode. This script consumes completed adjudication and
annotation CSVs, creates unified JSONL gold records, deterministic splits, and
the fixed 8-gram test-deduplication log for the future RAG corpus.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.domain_data import ngram_containment, normalized_ngrams, text_sha256
from equipment_ie.schema import SchemaError, sha256_file, validate_record, write_jsonl_atomic


ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}
RELATION_MATRIX = {
    "USES": {
        "head": {"EQUIPMENT", "MODULE"},
        "tail": {"EQUIPMENT", "MODULE", "TECH_SCHEME"},
    },
    "HAS_METRIC": {
        "head": {"EQUIPMENT", "MODULE"},
        "tail": {"METRIC", "TECH_SCHEME"},
    },
    "PART_OF": {
        "head": {"EQUIPMENT", "MODULE"},
        "tail": {"EQUIPMENT", "MODULE"},
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotator-a", default="data/annotation/annotator_a_250.csv")
    parser.add_argument("--adjudication", default="data/annotation/adjudication_sheet.csv")
    parser.add_argument("--candidates", default="/root/autodl-tmp/data/domain_candidates.jsonl")
    parser.add_argument("--data-root", default="/root/autodl-tmp/data")
    parser.add_argument("--project-data-root", default="data")
    parser.add_argument("--log-root", default="logs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--support-size", type=int, default=30)
    parser.add_argument("--dev-size", type=int, default=50)
    parser.add_argument("--ngram-size", type=int, default=8)
    parser.add_argument("--containment-threshold", type=float, default=0.80)
    parser.add_argument("--repair-log", default="")
    parser.add_argument("--audit-only", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def write_objects_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    count = 0
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                count += 1
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return count


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def parse_json_array(row: dict[str, str], field: str) -> list[dict[str, Any]]:
    raw = row.get(field, "")
    if not raw.strip():
        raise ValueError(f"{row.get('review_id')}: missing {field}")
    value = json.loads(raw)
    if not isinstance(value, list):
        raise ValueError(f"{row.get('review_id')}: {field} must be an array")
    return value


def text_from_row(row: dict[str, str]) -> str:
    raw = row.get("text_json", "")
    if raw.strip():
        value = json.loads(raw)
        if not isinstance(value, str):
            raise ValueError(f"{row.get('review_id')}: text_json must be a string")
        return value
    return row["text_display"]


def normalize_record(
    row: dict[str, str],
    *,
    entity_field: str,
    relation_field: str,
    label_source: str,
    allow_repair: bool,
    repair_events: list[dict[str, Any]],
) -> dict[str, Any]:
    record_id = row["review_id"]
    text = text_from_row(row)
    raw_entities = parse_json_array(row, entity_field)
    raw_relations = parse_json_array(row, relation_field)

    entities: list[dict[str, Any]] = []
    for index, entity in enumerate(raw_entities):
        if not isinstance(entity, dict):
            raise ValueError(f"{record_id}: entity {index} must be an object")
        normalized = {
            "start": int(entity["start"]),
            "end": int(entity["end"]),
            "type": str(entity["type"]),
            "span": str(entity["span"]),
        }
        if normalized["type"] not in ENTITY_TYPES:
            raise ValueError(f"{record_id}: invalid entity type {normalized['type']}")
        entities.append(normalized)

    active_indices, duplicate_to_keep, nested_dropped = repair_entity_structure(
        record_id,
        entities,
        label_source=label_source,
        allow_repair=allow_repair,
        repair_events=repair_events,
    )

    order = sorted(
        active_indices,
        key=lambda i: (entities[i]["start"], entities[i]["end"], entities[i]["type"], entities[i]["span"]),
    )
    remap = {old: new for new, old in enumerate(order)}
    sorted_entities = [entities[old] for old in order]

    for i in range(len(sorted_entities)):
        a = sorted_entities[i]
        for j in range(i + 1, len(sorted_entities)):
            b = sorted_entities[j]
            if a["start"] < b["end"] and b["start"] < a["end"]:
                raise ValueError(f"{record_id}: overlapping entities {i}/{j}")

    relations: list[dict[str, Any]] = []
    seen_relations: set[tuple[int, int, str]] = set()
    for index, relation in enumerate(raw_relations):
        if not isinstance(relation, dict):
            raise ValueError(f"{record_id}: relation {index} must be an object")
        rel_type = str(relation["type"])
        if rel_type not in RELATION_MATRIX:
            raise ValueError(f"{record_id}: invalid relation type {rel_type}")
        raw_head = int(relation["head"])
        raw_tail = int(relation["tail"])
        if raw_head not in range(len(entities)) or raw_tail not in range(len(entities)):
            raise ValueError(f"{record_id}: relation {index} references a missing raw entity")
        if raw_head in nested_dropped or raw_tail in nested_dropped:
            repair_events.append(
                {
                    "record_id": record_id,
                    "label_source": label_source,
                    "kind": "RELATION_DROPPED_REMOVED_ENTITY",
                    "relation_raw_index": index,
                    "relation": relation,
                    "removed_entity_raw_indices": sorted(
                        [value for value in (raw_head, raw_tail) if value in nested_dropped]
                    ),
                    "reason": "relation endpoint was a nested-overlap entity removed from single annotator data",
                }
            )
            continue
        raw_head = duplicate_to_keep.get(raw_head, raw_head)
        raw_tail = duplicate_to_keep.get(raw_tail, raw_tail)
        head = remap[raw_head]
        tail = remap[raw_tail]
        head_type = sorted_entities[head]["type"]
        tail_type = sorted_entities[tail]["type"]
        matrix = RELATION_MATRIX[rel_type]
        if head_type not in matrix["head"] or tail_type not in matrix["tail"]:
            raise ValueError(
                f"{record_id}: relation {index} matrix violation {head_type}->{tail_type} {rel_type}"
            )
        key = (head, tail, rel_type)
        if key in seen_relations:
            repair_events.append(
                {
                    "record_id": record_id,
                    "label_source": label_source,
                    "kind": "RELATION_DUPLICATE_DROPPED",
                    "relation_raw_index": index,
                    "relation": relation,
                    "reason": "relation became duplicate after entity sorting or duplicate-entity remap",
                }
            )
            continue
        seen_relations.add(key)
        relations.append({"head": head, "tail": tail, "type": rel_type})

    record = {"id": record_id, "text": text, "entities": sorted_entities, "relations": relations}
    validate_record(record)
    return record


def repair_entity_structure(
    record_id: str,
    entities: list[dict[str, Any]],
    *,
    label_source: str,
    allow_repair: bool,
    repair_events: list[dict[str, Any]],
) -> tuple[set[int], dict[int, int], set[int]]:
    active_indices = set(range(len(entities)))
    duplicate_to_keep: dict[int, int] = {}
    nested_dropped: set[int] = set()
    seen_entities: dict[tuple[int, int, str, str], int] = {}

    for index, entity in enumerate(entities):
        key = (entity["start"], entity["end"], entity["type"], entity["span"])
        if key not in seen_entities:
            seen_entities[key] = index
            continue
        if not allow_repair:
            raise ValueError(f"{record_id}: duplicate entity {index}")
        keep = seen_entities[key]
        active_indices.remove(index)
        duplicate_to_keep[index] = keep
        repair_events.append(
            {
                "record_id": record_id,
                "label_source": label_source,
                "kind": "ENTITY_DUPLICATE_DROPPED",
                "kept_raw_index": keep,
                "dropped_raw_index": index,
                "kept_entity": entities[keep],
                "dropped_entity": entity,
                "reason": "exact duplicate in single annotator data",
            }
        )

    while True:
        ordered = sorted(
            active_indices,
            key=lambda i: (entities[i]["start"], entities[i]["end"], entities[i]["type"], entities[i]["span"]),
        )
        repaired = False
        for left_pos, left_index in enumerate(ordered):
            left = entities[left_index]
            for right_index in ordered[left_pos + 1 :]:
                right = entities[right_index]
                if not (left["start"] < right["end"] and right["start"] < left["end"]):
                    continue
                left_len = left["end"] - left["start"]
                right_len = right["end"] - right["start"]
                left_contains_right = left["start"] <= right["start"] and right["end"] <= left["end"]
                right_contains_left = right["start"] <= left["start"] and left["end"] <= right["end"]
                if not allow_repair or not (left_contains_right or right_contains_left) or left_len == right_len:
                    raise ValueError(f"{record_id}: overlapping entities {left_pos}/{ordered.index(right_index)}")
                if left_contains_right and left_len > right_len:
                    keep_index, drop_index = left_index, right_index
                elif right_contains_left and right_len > left_len:
                    keep_index, drop_index = right_index, left_index
                else:
                    raise ValueError(f"{record_id}: overlapping entities {left_pos}/{ordered.index(right_index)}")
                active_indices.remove(drop_index)
                nested_dropped.add(drop_index)
                repair_events.append(
                    {
                        "record_id": record_id,
                        "label_source": label_source,
                        "kind": "ENTITY_NESTED_OVERLAP_DROPPED",
                        "kept_raw_index": keep_index,
                        "dropped_raw_index": drop_index,
                        "kept_entity": entities[keep_index],
                        "dropped_entity": entities[drop_index],
                        "reason": "shorter entity strictly contained in longer single-annotator entity",
                    }
                )
                repaired = True
                break
            if repaired:
                break
        if not repaired:
            break

    return active_indices, duplicate_to_keep, nested_dropped


def split_records(
    records: list[dict[str, Any]],
    *,
    seed: int,
    support_size: int,
    dev_size: int,
) -> dict[str, list[dict[str, Any]]]:
    if len(records) < support_size + dev_size + 100:
        raise ValueError("not enough records for support/dev/test>=100")
    shuffled = list(records)
    random.Random(seed).shuffle(shuffled)
    support = sorted(shuffled[:support_size], key=lambda row: row["id"])
    dev = sorted(shuffled[support_size : support_size + dev_size], key=lambda row: row["id"])
    test = sorted(shuffled[support_size + dev_size :], key=lambda row: row["id"])
    if len(test) < 100:
        raise ValueError("domain test split must contain at least 100 records")
    return {"support": support, "dev": dev, "test": test}


def build_rag_corpus_and_dedup(
    candidates: list[dict[str, Any]],
    test_records: list[dict[str, Any]],
    *,
    ngram_size: int,
    containment_threshold: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    test_grams = {
        record["id"]: normalized_ngrams(record["text"], ngram_size)
        for record in test_records
    }
    rag_rows: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    for candidate in candidates:
        text = str(candidate["text"])
        grams = normalized_ngrams(text, ngram_size)
        matched_id = None
        matched_score = 0.0
        for test_id, test_ngram_set in test_grams.items():
            score = ngram_containment(grams, test_ngram_set)
            if score >= containment_threshold:
                matched_id = test_id
                matched_score = score
                break
        if matched_id is not None:
            removed.append(
                {
                    "removed_id": candidate["id"],
                    "matched_test_id": matched_id,
                    "containment": round(matched_score, 6),
                    "reason": "test_overlap_8gram_containment",
                }
            )
            continue
        rag_rows.append(
            {
                "id": candidate["id"],
                "text": text,
                "source_type": candidate.get("source_type", ""),
                "source_id": candidate.get("source_id", ""),
                "source_url": candidate.get("source_url", ""),
                "source_license": candidate.get("source_license", ""),
                "title": candidate.get("title", ""),
                "content_sha256": text_sha256(text),
            }
        )
    return rag_rows, removed


def count_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts = Counter(record.get("source_type", "unknown") for record in records)
    entity_counts: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()
    for record in records:
        for entity in record["entities"]:
            entity_counts[entity["type"]] += 1
        for relation in record["relations"]:
            relation_counts[relation["type"]] += 1
    return {
        "records": len(records),
        "entities": sum(entity_counts.values()),
        "relations": sum(relation_counts.values()),
        "source_counts": dict(sorted(source_counts.items())),
        "entity_type_counts": dict(sorted(entity_counts.items())),
        "relation_type_counts": dict(sorted(relation_counts.items())),
    }


def repair_summary(repair_events: list[dict[str, Any]]) -> dict[str, Any]:
    event_counts = Counter(str(event["kind"]) for event in repair_events)
    affected_records = sorted({str(event["record_id"]) for event in repair_events})
    return {
        "total_events": len(repair_events),
        "affected_records": len(affected_records),
        "affected_record_ids": affected_records,
        "event_counts": dict(sorted(event_counts.items())),
    }


def write_repair_log(path: Path, repair_events: list[dict[str, Any]]) -> dict[str, Any]:
    log = {
        "phase": "P2",
        "stage": "domain_gold_structure_repair",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "adjudicated_rows": "strict_no_repair",
            "single_annotator_rows": [
                "drop exact duplicate entities",
                "drop shorter entity only when strictly nested in a longer entity",
                "drop relations whose endpoint was removed by nested-overlap repair",
                "remap relations only for exact duplicate entity removal",
            ],
            "non_nested_or_equal_length_overlaps": "fail_build",
        },
        "summary": repair_summary(repair_events),
        "events": repair_events,
    }
    write_json_atomic(path, log)
    return log


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root)
    project_data_root = Path(args.project_data_root)
    log_root = Path(args.log_root)
    repair_log_path = Path(args.repair_log) if args.repair_log else log_root / "p2_domain_gold_repair_log.json"
    annotator_a_path = Path(args.annotator_a)
    adjudication_path = Path(args.adjudication)
    candidates_path = Path(args.candidates)

    a_rows = read_csv(annotator_a_path)
    adjudication_rows = read_csv(adjudication_path)
    adjudication_by_id = {row["review_id"]: row for row in adjudication_rows}
    if len(adjudication_by_id) != len(adjudication_rows):
        raise ValueError("duplicate review_id in adjudication sheet")

    source_map: list[dict[str, Any]] = []
    gold_records: list[dict[str, Any]] = []
    repair_events: list[dict[str, Any]] = []
    used_adjudicated = 0
    used_annotator_a = 0
    for row in a_rows:
        review_id = row["review_id"]
        if review_id in adjudication_by_id:
            gold = normalize_record(
                adjudication_by_id[review_id],
                entity_field="adjudicated_entities_json",
                relation_field="adjudicated_relations_json",
                label_source="adjudicated_double_annotation",
                allow_repair=False,
                repair_events=repair_events,
            )
            label_source = "adjudicated_double_annotation"
            used_adjudicated += 1
        else:
            gold = normalize_record(
                row,
                entity_field="annotator_a_entities_json",
                relation_field="annotator_a_relations_json",
                label_source="annotator_a_single_annotation",
                allow_repair=True,
                repair_events=repair_events,
            )
            label_source = "annotator_a_single_annotation"
            used_annotator_a += 1
        gold_records.append(gold)
        source_map.append(
            {
                "id": review_id,
                "label_source": label_source,
                "source_type": row.get("source_type", ""),
                "source_id": row.get("source_id", ""),
                "source_url": row.get("source_url", ""),
                "source_license": row.get("source_license", ""),
                "title": row.get("title_display", ""),
                "text_sha256": text_sha256(gold["text"]),
            }
        )

    if len(gold_records) != 250:
        raise ValueError(f"expected 250 gold records, got {len(gold_records)}")

    repair_log = write_repair_log(repair_log_path, repair_events)
    if args.audit_only:
        audit = {
            "stage": "domain_gold_structure_audit",
            "gold_records": len(gold_records),
            "label_sources": {
                "adjudicated_double_annotation": used_adjudicated,
                "annotator_a_single_annotation": used_annotator_a,
            },
            "repair_log": str(repair_log_path),
            "repair_summary": repair_log["summary"],
        }
        print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
        return 0

    splits = split_records(
        gold_records,
        seed=args.seed,
        support_size=args.support_size,
        dev_size=args.dev_size,
    )
    split_by_id = {
        record["id"]: split_name
        for split_name, rows in splits.items()
        for record in rows
    }
    for item in source_map:
        item["split"] = split_by_id[item["id"]]

    candidates = read_jsonl(candidates_path)
    rag_rows, removed = build_rag_corpus_and_dedup(
        candidates,
        splits["test"],
        ngram_size=args.ngram_size,
        containment_threshold=args.containment_threshold,
    )

    outputs = {
        "gold": data_root / "domain_gold_250.jsonl",
        "support": data_root / "domain_support.jsonl",
        "dev": data_root / "domain_dev.jsonl",
        "test": data_root / "domain_test.jsonl",
        "source_map": data_root / "domain_gold_source_map.jsonl",
        "rag_corpus": data_root / "domain_rag_corpus.jsonl",
        "frozen": data_root / "FROZEN",
        "project_frozen": project_data_root / "FROZEN",
        "dedup": log_root / "dedup.json",
        "repair_log": repair_log_path,
        "manifest": log_root / "p2_domain_gold_manifest.json",
    }

    write_jsonl_atomic(outputs["gold"], sorted(gold_records, key=lambda row: row["id"]))
    for split_name, records in splits.items():
        write_jsonl_atomic(outputs[split_name], records)
    write_objects_jsonl_atomic(outputs["source_map"], source_map)
    write_objects_jsonl_atomic(outputs["rag_corpus"], rag_rows)

    dedup_log = {
        "protocol": "fixed_8gram_containment_against_domain_test",
        "ngram_size": args.ngram_size,
        "containment_threshold": args.containment_threshold,
        "test_records": len(splits["test"]),
        "candidate_records": len(candidates),
        "rag_corpus_records": len(rag_rows),
        "removed_count": len(removed),
        "removed": removed,
    }
    write_json_atomic(outputs["dedup"], dedup_log)

    frozen_payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "phase": "P2",
        "seed": args.seed,
        "support_size": args.support_size,
        "dev_size": args.dev_size,
        "test_size": len(splits["test"]),
        "rule": "No prompt, threshold, schema, glossary, or RAG setting may be tuned using domain_test.jsonl after this marker.",
    }
    frozen_text = json.dumps(frozen_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    write_text_atomic(outputs["frozen"], frozen_text)
    write_text_atomic(outputs["project_frozen"], frozen_text)

    manifest_path = outputs["manifest"]
    generated_outputs = {
        name: path for name, path in outputs.items() if name != "manifest"
    }
    file_hashes = {
        name: {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        for name, path in generated_outputs.items()
    }
    manifest = {
        "phase": "P2",
        "stage": "domain_gold_split_freeze",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "label_sources": {
            "adjudicated_double_annotation": used_adjudicated,
            "annotator_a_single_annotation": used_annotator_a,
        },
        "inputs": {
            "annotator_a": {
                "path": str(annotator_a_path),
                "sha256": sha256_file(annotator_a_path),
                "rows": len(a_rows),
            },
            "adjudication": {
                "path": str(adjudication_path),
                "sha256": sha256_file(adjudication_path),
                "rows": len(adjudication_rows),
            },
            "candidates": {
                "path": str(candidates_path),
                "sha256": sha256_file(candidates_path),
                "rows": len(candidates),
            },
        },
        "counts": {
            "gold": count_records(gold_records),
            "support": count_records(splits["support"]),
            "dev": count_records(splits["dev"]),
            "test": count_records(splits["test"]),
        },
        "dedup": {
            "removed_count": len(removed),
            "rag_corpus_records": len(rag_rows),
            "log_path": str(outputs["dedup"]),
            "log_sha256": sha256_file(outputs["dedup"]),
        },
        "repairs": {
            "log_path": str(outputs["repair_log"]),
            "log_sha256": sha256_file(outputs["repair_log"]),
            **repair_log["summary"],
        },
        "files": file_hashes,
        "gate": {
            "support_dev_test_exist": True,
            "test_size_at_least_100": len(splits["test"]) >= 100,
            "frozen_marker_present": True,
            "dedup_log_present": True,
        },
    }
    write_json_atomic(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SchemaError as exc:
        raise SystemExit(f"schema validation failed: {exc}") from exc
