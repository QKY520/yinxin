"""Converters for the four fixed P1 public datasets."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from equipment_ie.schema import SchemaError, iter_jsonl


class ConversionError(ValueError):
    """Raised when a source annotation cannot be converted without guessing."""


@dataclass
class ConversionAudit:
    """Mutable counters populated while a converter is consumed."""

    counters: Counter[str] = field(default_factory=Counter)
    issues: list[dict[str, Any]] = field(default_factory=list)

    def bump(self, key: str, amount: int = 1) -> None:
        self.counters[key] += amount

    def issue(self, code: str, **details: Any) -> None:
        self.counters[f"issues:{code}"] += 1
        self.issues.append({"code": code, **details})

    def to_dict(self) -> dict[str, Any]:
        return {
            "counters": dict(sorted(self.counters.items())),
            "issues": self.issues,
        }


class _RecordBuilder:
    def __init__(self, record_id: str, text: str) -> None:
        self.record_id = record_id
        self.text = text
        self.entities: list[dict[str, Any]] = []
        self.relations: list[dict[str, Any]] = []
        self._entity_indices: dict[tuple[int, int, str], int] = {}
        self._relation_keys: set[tuple[int, int, str]] = set()

    def entity(self, start: int, end: int, entity_type: str) -> int:
        key = (start, end, entity_type)
        if key not in self._entity_indices:
            self._entity_indices[key] = len(self.entities)
            self.entities.append(
                {
                    "start": start,
                    "end": end,
                    "type": entity_type,
                    "span": self.text[start:end],
                }
            )
        return self._entity_indices[key]

    def relation(self, head: int, tail: int, relation_type: str) -> None:
        key = (head, tail, relation_type)
        if key not in self._relation_keys:
            self._relation_keys.add(key)
            self.relations.append({"head": head, "tail": tail, "type": relation_type})

    def build(self) -> dict[str, Any]:
        return {
            "id": self.record_id,
            "text": self.text,
            "entities": self.entities,
            "relations": self.relations,
        }


def _load_json_object(line: str, source: Path, line_number: int) -> dict[str, Any]:
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ConversionError(f"{source}:{line_number}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ConversionError(f"{source}:{line_number}: expected a JSON object")
    return value


def convert_cluener(
    path: Path | str,
    split: str,
    *,
    labeled: bool,
    audit: ConversionAudit,
) -> Iterator[dict[str, Any]]:
    """Convert CLUENER inclusive character spans to exclusive spans."""

    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            raw = _load_json_object(line, source, row_index + 1)
            text = raw.get("text")
            if not isinstance(text, str):
                raise ConversionError(f"{source}:{row_index + 1}: missing string text")
            source_id = raw.get("id", row_index)
            builder = _RecordBuilder(f"cluener-{split}-{source_id}", text)
            labels = raw.get("label")
            if labeled and not isinstance(labels, dict):
                raise ConversionError(f"{source}:{row_index + 1}: labeled row lacks label")
            if not labeled and labels is not None:
                raise ConversionError(
                    f"{source}:{row_index + 1}: unlabeled split unexpectedly has labels"
                )
            for entity_type, surfaces in (labels or {}).items():
                if not isinstance(entity_type, str) or not isinstance(surfaces, dict):
                    raise ConversionError(f"{source}:{row_index + 1}: malformed labels")
                for expected_span, inclusive_spans in surfaces.items():
                    for inclusive_span in inclusive_spans:
                        if not isinstance(inclusive_span, list) or len(inclusive_span) != 2:
                            raise ConversionError(
                                f"{source}:{row_index + 1}: malformed CLUENER span"
                            )
                        start, inclusive_end = inclusive_span
                        end = inclusive_end + 1
                        if text[start:end] != expected_span:
                            raise ConversionError(
                                f"{source}:{row_index + 1}: CLUENER span mismatch "
                                f"for {expected_span!r} at [{start}, {end})"
                            )
                        builder.entity(start, end, entity_type)
            audit.bump("records")
            audit.bump("entities", len(builder.entities))
            yield builder.build()


def _fewnerd_label_names(parquet_file: Any) -> list[str]:
    metadata = parquet_file.schema_arrow.metadata or {}
    encoded = metadata.get(b"huggingface")
    if encoded is None:
        raise ConversionError("Few-NERD parquet lacks Hugging Face schema metadata")
    try:
        features = json.loads(encoded)["info"]["features"]
        names = features["fine_ner_tags"]["feature"]["names"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ConversionError("Few-NERD fine-label metadata is malformed") from exc
    if not isinstance(names, list) or not names or names[0] != "O":
        raise ConversionError("Few-NERD fine-label metadata has an unexpected layout")
    return [str(name) for name in names]


def fewnerd_row_to_record(
    tokens: Sequence[str],
    fine_tags: Sequence[int],
    label_names: Sequence[str],
    record_id: str,
) -> dict[str, Any]:
    """Convert one token-classification row into character spans."""

    if len(tokens) != len(fine_tags):
        raise ConversionError(f"{record_id}: token and label lengths differ")
    if any(not isinstance(token, str) or not token for token in tokens):
        raise ConversionError(f"{record_id}: tokens must be non-empty strings")

    text = " ".join(tokens)
    token_offsets: list[tuple[int, int]] = []
    cursor = 0
    for index, token in enumerate(tokens):
        if index:
            cursor += 1
        start = cursor
        cursor += len(token)
        token_offsets.append((start, cursor))

    builder = _RecordBuilder(record_id, text)
    run_start: int | None = None
    run_end: int | None = None
    run_label: str | None = None
    for token_index, raw_tag in enumerate(fine_tags):
        if not isinstance(raw_tag, int) or isinstance(raw_tag, bool):
            raise ConversionError(f"{record_id}: label ids must be integers")
        if not 0 <= raw_tag < len(label_names):
            raise ConversionError(f"{record_id}: label id {raw_tag} is out of range")
        label = label_names[raw_tag]
        if label == "O":
            if run_label is not None:
                builder.entity(run_start, run_end, run_label)  # type: ignore[arg-type]
                run_start = run_end = None
                run_label = None
            continue
        token_start, token_end = token_offsets[token_index]
        if label != run_label:
            if run_label is not None:
                builder.entity(run_start, run_end, run_label)  # type: ignore[arg-type]
            run_start, run_end, run_label = token_start, token_end, label
        else:
            run_end = token_end
    if run_label is not None:
        builder.entity(run_start, run_end, run_label)  # type: ignore[arg-type]
    return builder.build()


def convert_fewnerd(
    path: Path | str, split: str, *, audit: ConversionAudit
) -> Iterator[dict[str, Any]]:
    """Stream a Few-NERD SUP parquet split without loading it all into memory."""

    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ConversionError("pyarrow is required to convert Few-NERD") from exc

    source = Path(path)
    parquet = pq.ParquetFile(source)
    label_names = _fewnerd_label_names(parquet)
    row_index = 0
    for batch in parquet.iter_batches(
        batch_size=2048, columns=["id", "tokens", "fine_ner_tags"]
    ):
        columns = batch.to_pydict()
        for source_id, tokens, fine_tags in zip(
            columns["id"], columns["tokens"], columns["fine_ner_tags"], strict=True
        ):
            record = fewnerd_row_to_record(
                tokens,
                fine_tags,
                label_names,
                f"fewnerd-{split}-{source_id if source_id is not None else row_index}",
            )
            audit.bump("records")
            audit.bump("entities", len(record["entities"]))
            row_index += 1
            yield record


def _find_occurrences(text: str, surface: str) -> list[tuple[int, int]]:
    if not surface:
        return []
    positions: list[tuple[int, int]] = []
    cursor = 0
    while True:
        start = text.find(surface, cursor)
        if start < 0:
            return positions
        positions.append((start, start + len(surface)))
        cursor = start + 1


def _mention_distance(left: tuple[int, int], right: tuple[int, int]) -> int:
    if left[1] <= right[0]:
        return right[0] - left[1]
    if right[1] <= left[0]:
        return left[0] - right[1]
    return 0


def _choose_mention_pair(
    subjects: Sequence[tuple[int, int]], objects: Sequence[tuple[int, int]]
) -> tuple[tuple[int, int], tuple[int, int]]:
    return min(
        ((subject, obj) for subject in subjects for obj in objects),
        key=lambda pair: (
            _mention_distance(pair[0], pair[1]),
            abs(pair[0][0] - pair[1][0]),
            pair[0][0],
            pair[1][0],
        ),
    )


def duie_row_to_record(
    raw: Mapping[str, Any], record_id: str, *, audit: ConversionAudit
) -> dict[str, Any]:
    """Convert one DuIE row using a documented nearest-exact-mention rule."""

    text = raw.get("text")
    spo_list = raw.get("spo_list")
    if not isinstance(text, str) or not isinstance(spo_list, list):
        raise ConversionError(f"{record_id}: DuIE row lacks text or spo_list")
    builder = _RecordBuilder(record_id, text)
    for spo_index, spo in enumerate(spo_list):
        if not isinstance(spo, dict):
            raise ConversionError(f"{record_id}: SPO {spo_index} is not an object")
        subject = spo.get("subject")
        subject_type = spo.get("subject_type")
        predicate = spo.get("predicate")
        objects = spo.get("object")
        object_types = spo.get("object_type")
        source_object_count = len(objects) if isinstance(objects, dict) else 1
        audit.bump("source_object_values", source_object_count)
        if not all(
            isinstance(value, str) and value
            for value in (subject, subject_type, predicate)
        ):
            audit.bump("rejected_object_values", source_object_count)
            audit.issue(
                "malformed_subject_metadata",
                record_id=record_id,
                spo_index=spo_index,
                subject=subject,
                subject_type=subject_type,
                predicate=predicate,
            )
            continue
        if not isinstance(objects, dict):
            audit.bump("rejected_object_values")
            audit.issue(
                "malformed_object_container",
                record_id=record_id,
                spo_index=spo_index,
                predicate=predicate,
            )
            continue
        if isinstance(object_types, str):
            object_types = {"@value": object_types}
        if not isinstance(object_types, dict):
            audit.bump("rejected_object_values", len(objects))
            audit.issue(
                "malformed_object_type_container",
                record_id=record_id,
                spo_index=spo_index,
                predicate=predicate,
            )
            continue

        subject_positions = _find_occurrences(text, subject)
        if not subject_positions:
            audit.bump("rejected_object_values", len(objects))
            audit.issue(
                "subject_absent_from_text",
                record_id=record_id,
                spo_index=spo_index,
                predicate=predicate,
                subject=subject,
            )
            continue
        if len(subject_positions) > 1:
            audit.bump("ambiguous_subject_surfaces")
        for object_key, object_surface in objects.items():
            if (
                not isinstance(object_key, str)
                or not isinstance(object_surface, str)
                or not object_surface
            ):
                audit.bump("rejected_object_values")
                audit.issue(
                    "malformed_object_value",
                    record_id=record_id,
                    spo_index=spo_index,
                    predicate=predicate,
                    object_key=object_key,
                    object_surface=object_surface,
                )
                continue
            object_type = object_types.get(object_key)
            if not isinstance(object_type, str) or not object_type:
                audit.bump("rejected_object_values")
                audit.issue(
                    "missing_object_type",
                    record_id=record_id,
                    spo_index=spo_index,
                    predicate=predicate,
                    object_key=object_key,
                )
                continue
            object_positions = _find_occurrences(text, object_surface)
            if not object_positions:
                audit.bump("rejected_object_values")
                audit.issue(
                    "object_absent_from_text",
                    record_id=record_id,
                    spo_index=spo_index,
                    predicate=predicate,
                    object_key=object_key,
                    object_surface=object_surface,
                )
                continue
            if len(object_positions) > 1:
                audit.bump("ambiguous_object_surfaces")
            subject_span, object_span = _choose_mention_pair(
                subject_positions, object_positions
            )
            head = builder.entity(subject_span[0], subject_span[1], subject_type)
            tail = builder.entity(object_span[0], object_span[1], object_type)
            relation_type = predicate if object_key == "@value" else f"{predicate}:{object_key}"
            builder.relation(head, tail, relation_type)
            audit.bump("normalized_object_values")
    return builder.build()


def convert_duie(
    path: Path | str,
    split: str,
    *,
    labeled: bool,
    audit: ConversionAudit,
) -> Iterator[dict[str, Any]]:
    """Convert one DuIE JSONL split."""

    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            raw = _load_json_object(line, source, row_index + 1)
            if not labeled:
                if "spo_list" in raw:
                    raise ConversionError(
                        f"{source}:{row_index + 1}: unlabeled split unexpectedly has spo_list"
                    )
                raw = {"text": raw.get("text"), "spo_list": []}
            record = duie_row_to_record(
                raw, f"duie-{split}-{row_index}", audit=audit
            )
            audit.bump("records")
            audit.bump("entities", len(record["entities"]))
            audit.bump("relations", len(record["relations"]))
            yield record


def _annotated_span(
    text: str, mention: Mapping[str, Any], record_id: str, context: str
) -> tuple[int, int]:
    surface = mention.get("text")
    offset = mention.get("offset")
    if (
        not isinstance(surface, str)
        or not surface
        or not isinstance(offset, list)
        or len(offset) != 2
        or any(not isinstance(value, int) or isinstance(value, bool) for value in offset)
    ):
        raise ConversionError(f"{record_id}: malformed {context} mention")
    start, end = offset
    if not 0 <= start < end <= len(text) or text[start:end] != surface:
        raise ConversionError(
            f"{record_id}: {context} {surface!r} mismatches [{start}, {end})"
        )
    return start, end


def cmnee_row_to_record(
    raw: Mapping[str, Any], split: str, *, audit: ConversionAudit
) -> dict[str, Any]:
    """Represent CMNEE triggers, arguments, and coreference in the unified schema."""

    source_id = raw.get("id")
    text = raw.get("text")
    events = raw.get("event_list")
    coref_groups = raw.get("coref_arguments", [])
    record_id = f"cmnee-{split}-{source_id}"
    if not isinstance(source_id, (str, int)) or not isinstance(text, str):
        raise ConversionError(f"{record_id}: CMNEE row lacks id or text")
    if not isinstance(events, list) or not isinstance(coref_groups, list):
        raise ConversionError(f"{record_id}: CMNEE annotations must be lists")
    builder = _RecordBuilder(record_id, text)
    for event_index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ConversionError(f"{record_id}: event {event_index} is malformed")
        event_type = event.get("event_type")
        trigger = event.get("trigger")
        arguments = event.get("arguments")
        if not isinstance(event_type, str) or not event_type:
            raise ConversionError(f"{record_id}: event {event_index} lacks event_type")
        if not isinstance(trigger, dict) or not isinstance(arguments, list):
            raise ConversionError(f"{record_id}: event {event_index} lacks annotations")
        trigger_start, trigger_end = _annotated_span(
            text, trigger, record_id, f"event {event_index} trigger"
        )
        head = builder.entity(
            trigger_start, trigger_end, f"EVENT_TRIGGER:{event_type}"
        )
        audit.bump("events")
        for argument_index, argument in enumerate(arguments):
            if not isinstance(argument, dict):
                raise ConversionError(
                    f"{record_id}: event {event_index} argument {argument_index} is malformed"
                )
            role = argument.get("role")
            if not isinstance(role, str) or not role:
                raise ConversionError(
                    f"{record_id}: event {event_index} argument {argument_index} lacks role"
                )
            start, end = _annotated_span(
                text,
                argument,
                record_id,
                f"event {event_index} argument {argument_index}",
            )
            tail = builder.entity(start, end, f"EVENT_ARGUMENT:{role}")
            builder.relation(head, tail, f"HAS_ARGUMENT:{role}")
            audit.bump("event_arguments")

    for group_index, group in enumerate(coref_groups):
        if not isinstance(group, list):
            raise ConversionError(f"{record_id}: coref group {group_index} is malformed")
        mentions: list[int] = []
        for mention_index, mention in enumerate(group):
            if not isinstance(mention, dict):
                raise ConversionError(
                    f"{record_id}: coref group {group_index} mention {mention_index} is malformed"
                )
            start, end = _annotated_span(
                text,
                mention,
                record_id,
                f"coref group {group_index} mention {mention_index}",
            )
            mentions.append(builder.entity(start, end, "COREF_MENTION"))
        if mentions:
            for other in mentions[1:]:
                builder.relation(mentions[0], other, "COREF")
            audit.bump("coref_groups")
    return builder.build()


def convert_cmnee(
    path: Path | str, split: str, *, audit: ConversionAudit
) -> Iterator[dict[str, Any]]:
    """Convert one CMNEE JSON-array split."""

    source = Path(path)
    try:
        rows = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConversionError(f"{source}: invalid JSON: {exc}") from exc
    if not isinstance(rows, list):
        raise ConversionError(f"{source}: expected a top-level JSON array")
    for raw in rows:
        if not isinstance(raw, dict):
            raise ConversionError(f"{source}: each row must be an object")
        record = cmnee_row_to_record(raw, split, audit=audit)
        audit.bump("records")
        audit.bump("entities", len(record["entities"]))
        audit.bump("relations", len(record["relations"]))
        yield record


@dataclass(frozen=True)
class SupportSelection:
    selected_ids: frozenset[str]
    selected_by_type: dict[str, tuple[str, ...]]
    candidate_counts: dict[str, int]

    def report(self) -> dict[str, Any]:
        return {
            "selected_record_count": len(self.selected_ids),
            "candidate_counts": self.candidate_counts,
            "sampled_ids_by_type": {
                label: list(ids) for label, ids in self.selected_by_type.items()
            },
        }


def choose_support_ids(path: Path | str, *, k: int, seed: int) -> SupportSelection:
    """Reservoir-sample exactly k source records per entity type."""

    if k <= 0:
        raise ValueError("k must be positive")
    try:
        import numpy as np
    except ImportError as exc:
        raise ConversionError("numpy is required for deterministic support sampling") from exc

    rng = np.random.default_rng(seed)
    reservoirs: dict[str, list[str]] = {}
    candidate_counts: Counter[str] = Counter()
    for record in iter_jsonl(path):
        labels = sorted({entity["type"] for entity in record["entities"]})
        for label in labels:
            candidate_counts[label] += 1
            reservoir = reservoirs.setdefault(label, [])
            if len(reservoir) < k:
                reservoir.append(record["id"])
            else:
                replacement = int(rng.integers(0, candidate_counts[label]))
                if replacement < k:
                    reservoir[replacement] = record["id"]
    if not reservoirs:
        raise SchemaError(f"{path}: no entity labels are available for support sampling")
    insufficient = {
        label: count for label, count in candidate_counts.items() if count < k
    }
    if insufficient:
        raise SchemaError(f"{path}: fewer than k={k} candidates: {insufficient}")
    selected_by_type = {
        label: tuple(ids) for label, ids in sorted(reservoirs.items())
    }
    selected_ids = frozenset(
        record_id for ids in selected_by_type.values() for record_id in ids
    )
    return SupportSelection(
        selected_ids=selected_ids,
        selected_by_type=selected_by_type,
        candidate_counts=dict(sorted(candidate_counts.items())),
    )


@dataclass(frozen=True)
class RecordPartition:
    """A deterministic two-way partition of one JSONL file."""

    pool_ids: frozenset[str]
    tune_ids: frozenset[str]
    seed: int
    tune_fraction: float


def partition_record_ids(
    path: Path | str, *, tune_fraction: float, seed: int
) -> RecordPartition:
    """Split record ids with NumPy default_rng while preserving all records."""

    if not 0.0 < tune_fraction < 1.0:
        raise ValueError("tune_fraction must be between zero and one")
    try:
        import numpy as np
    except ImportError as exc:
        raise ConversionError("numpy is required for deterministic partitioning") from exc

    record_ids = [record["id"] for record in iter_jsonl(path)]
    if len(record_ids) < 2:
        raise SchemaError(f"{path}: at least two records are required for partitioning")
    tune_count = max(1, min(len(record_ids) - 1, round(len(record_ids) * tune_fraction)))
    rng = np.random.default_rng(seed)
    tune_indices = set(int(index) for index in rng.choice(len(record_ids), tune_count, replace=False))
    tune_ids = frozenset(
        record_id for index, record_id in enumerate(record_ids) if index in tune_indices
    )
    pool_ids = frozenset(record_ids).difference(tune_ids)
    if pool_ids.intersection(tune_ids) or len(pool_ids) + len(tune_ids) != len(record_ids):
        raise AssertionError("partition is not a disjoint cover of the source ids")
    return RecordPartition(
        pool_ids=pool_ids,
        tune_ids=tune_ids,
        seed=seed,
        tune_fraction=tune_fraction,
    )


def iter_selected_records(
    path: Path | str, selected_ids: frozenset[str]
) -> Iterator[dict[str, Any]]:
    """Yield selected records in their original source order."""

    found: set[str] = set()
    for record in iter_jsonl(path):
        if record["id"] in selected_ids:
            found.add(record["id"])
            yield record
    missing = selected_ids.difference(found)
    if missing:
        raise SchemaError(f"{path}: selected support ids disappeared: {sorted(missing)}")
