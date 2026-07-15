"""Validation and JSONL I/O for the unified information-extraction schema."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any


class SchemaError(ValueError):
    """Raised when a record violates the unified data contract."""


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate one record without modifying it."""

    required = {"id", "text", "entities", "relations"}
    missing = required.difference(record)
    if missing:
        raise SchemaError(f"record is missing required keys: {sorted(missing)}")

    record_id = record["id"]
    text = record["text"]
    entities = record["entities"]
    relations = record["relations"]
    if not isinstance(record_id, str) or not record_id:
        raise SchemaError("id must be a non-empty string")
    if not isinstance(text, str):
        raise SchemaError(f"{record_id}: text must be a string")
    if not isinstance(entities, list):
        raise SchemaError(f"{record_id}: entities must be a list")
    if not isinstance(relations, list):
        raise SchemaError(f"{record_id}: relations must be a list")

    seen_entities: set[tuple[int, int, str]] = set()
    for index, entity in enumerate(entities):
        if not isinstance(entity, Mapping):
            raise SchemaError(f"{record_id}: entity {index} must be an object")
        if set(entity) != {"start", "end", "type", "span"}:
            raise SchemaError(
                f"{record_id}: entity {index} must contain start/end/type/span only"
            )
        start = entity["start"]
        end = entity["end"]
        entity_type = entity["type"]
        span = entity["span"]
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
        ):
            raise SchemaError(f"{record_id}: entity {index} offsets must be integers")
        if not 0 <= start < end <= len(text):
            raise SchemaError(
                f"{record_id}: entity {index} has invalid [{start}, {end}) offsets"
            )
        if not isinstance(entity_type, str) or not entity_type:
            raise SchemaError(f"{record_id}: entity {index} type must be non-empty")
        if not isinstance(span, str) or text[start:end] != span:
            raise SchemaError(
                f"{record_id}: entity {index} span does not equal text[start:end]"
            )
        key = (start, end, entity_type)
        if key in seen_entities:
            raise SchemaError(f"{record_id}: duplicate entity {key}")
        seen_entities.add(key)

    seen_relations: set[tuple[int, int, str]] = set()
    for index, relation in enumerate(relations):
        if not isinstance(relation, Mapping):
            raise SchemaError(f"{record_id}: relation {index} must be an object")
        if set(relation) != {"head", "tail", "type"}:
            raise SchemaError(
                f"{record_id}: relation {index} must contain head/tail/type only"
            )
        head = relation["head"]
        tail = relation["tail"]
        relation_type = relation["type"]
        if (
            not isinstance(head, int)
            or isinstance(head, bool)
            or not isinstance(tail, int)
            or isinstance(tail, bool)
        ):
            raise SchemaError(f"{record_id}: relation {index} indices must be integers")
        if not 0 <= head < len(entities) or not 0 <= tail < len(entities):
            raise SchemaError(f"{record_id}: relation {index} references a missing entity")
        if not isinstance(relation_type, str) or not relation_type:
            raise SchemaError(f"{record_id}: relation {index} type must be non-empty")
        key = (head, tail, relation_type)
        if key in seen_relations:
            raise SchemaError(f"{record_id}: duplicate relation {key}")
        seen_relations.add(key)


def iter_jsonl(path: Path | str, *, validate: bool = True) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from a UTF-8 JSONL file."""

    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise SchemaError(f"{source}:{line_number}: blank JSONL line")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SchemaError(f"{source}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise SchemaError(f"{source}:{line_number}: JSONL row must be an object")
            if validate:
                validate_record(record)
            yield record


def write_jsonl_atomic(
    path: Path | str, records: Iterable[Mapping[str, Any]]
) -> dict[str, int]:
    """Validate and atomically write records, returning basic counts."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    counts = {"records": 0, "entities": 0, "relations": 0}
    seen_ids: set[str] = set()
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                validate_record(record)
                record_id = str(record["id"])
                if record_id in seen_ids:
                    raise SchemaError(f"{destination}: duplicate record id {record_id}")
                seen_ids.add(record_id)
                handle.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                )
                counts["records"] += 1
                counts["entities"] += len(record["entities"])
                counts["relations"] += len(record["relations"])
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return counts


def validate_jsonl(path: Path | str) -> dict[str, int]:
    """Validate an entire JSONL file and return aggregate counts."""

    counts = {"records": 0, "entities": 0, "relations": 0}
    seen_ids: set[str] = set()
    for record in iter_jsonl(path):
        record_id = record["id"]
        if record_id in seen_ids:
            raise SchemaError(f"{path}: duplicate record id {record_id}")
        seen_ids.add(record_id)
        counts["records"] += 1
        counts["entities"] += len(record["entities"])
        counts["relations"] += len(record["relations"])
    return counts


def sha256_file(path: Path | str, *, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA256 digest of a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
