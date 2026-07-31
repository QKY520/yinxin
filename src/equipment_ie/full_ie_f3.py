"""GPU-free F3 resource preparation for the staged full-IE experiment.

This module deliberately contains no model client. It creates only non-test
development/tuning resources, locked future-run configs, and hash manifests.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .domain_data import ngram_containment, normalized_ngrams, text_sha256
from .full_ie import DEFAULT_RELATION_TYPES, validate_approved_relation_matrix
from .schema import iter_jsonl, sha256_file, validate_record


F3_GATE = "FULL_IE_F3_CONFIG_PREP_APPROVED"
DOMAIN_F4_GATE = "FULL_IE_DOMAIN_DEV_SANITY_APPROVED"
CLUENER_F4_GATE = "FULL_IE_CLUENER_TUNE_SANITY_APPROVED"
SEED = 42
K = 5
CLUENER_SUPPORT_SIZE = 30
CLUENER_TUNE_SIZE = 50
NGRAM_SIZE = 8
CONTAINMENT_THRESHOLD = 0.80
FIXED_OUTPUT_INSTRUCTION = "只返回JSON,不要任何解释,不要markdown代码块"
FIXED_RETRY_SUFFIX = "只返回合法JSON"
FIXED_VERIFIER_OUTPUT = "只回答yes或no"

CLUENER_ENTITY_TYPES = {
    "address": "地址、地点或具体位置。",
    "book": "图书、作品或出版物名称。",
    "company": "公司、企业或商业组织名称。",
    "game": "游戏名称。",
    "government": "政府机构或行政机关名称。",
    "movie": "电影、影视作品名称。",
    "name": "人名。",
    "organization": "组织、机构或团体名称。",
    "position": "职位、职务或身份称谓。",
    "scene": "景点、景区或场景名称。",
}

FORBIDDEN_CONFIG_TOKENS = (
    "domain_test",
    "cluener_dev",
    "cluener_test",
    "test_unlabeled",
)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


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


def _write_jsonl_atomic(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    count = 0
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(
                    json.dumps(
                        dict(row),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                count += 1
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return count


def _write_yaml_atomic(path: Path, value: Any) -> None:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required for F3 config preparation") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(
                value,
                handle,
                allow_unicode=True,
                sort_keys=False,
                width=1000,
            )
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required for F3 config validation") from exc
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def _load_records(path: Path) -> list[dict[str, Any]]:
    rows = [dict(record) for record in iter_jsonl(path)]
    if not rows:
        raise ValueError(f"{path}: no records")
    seen: set[str] = set()
    for record in rows:
        record_id = str(record["id"])
        if record_id in seen:
            raise ValueError(f"{path}: duplicate id {record_id}")
        seen.add(record_id)
    return rows


def _load_text_blocklist(path: Path) -> list[dict[str, str]]:
    """Load only IDs/text from a gold-bearing final-evaluation file."""

    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(iter_jsonl(path, validate=False), start=1):
        record_id = raw.get("id")
        text = raw.get("text")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError(f"{path}:{line_number}: blocklist ID must be non-empty")
        if not isinstance(text, str) or not text:
            raise ValueError(f"{path}:{line_number}: blocklist text must be non-empty")
        if record_id in seen:
            raise ValueError(f"{path}: duplicate blocklist id {record_id}")
        seen.add(record_id)
        rows.append({"id": record_id, "text": text})
    if not rows:
        raise ValueError(f"{path}: empty text blocklist")
    return rows


def _type_counts(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for record in records:
        for entity in record.get("entities", []):
            counts[str(entity["type"])] += 1
    return dict(sorted(counts.items()))


def _record_types(record: Mapping[str, Any]) -> frozenset[str]:
    return frozenset(str(entity["type"]) for entity in record.get("entities", []))


def _stable_rank(record_id: str, *, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{record_id}".encode("utf-8")).hexdigest()


def select_coverage_records(
    records: Sequence[Mapping[str, Any]],
    *,
    size: int,
    seed: int,
    required_types: Sequence[str],
) -> list[dict[str, Any]]:
    """Select a deterministic fixed-size set while covering every required type."""

    if size <= 0 or size > len(records):
        raise ValueError("selection size must be positive and no larger than the pool")
    required = set(required_types)
    available = set().union(*(_record_types(record) for record in records))
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"source pool lacks required entity types: {missing}")

    ranked = sorted(
        (dict(record) for record in records),
        key=lambda row: (_stable_rank(str(row["id"]), seed=seed), str(row["id"])),
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    uncovered = set(required)
    while uncovered:
        candidates = [
            row
            for row in ranked
            if str(row["id"]) not in selected_ids and (_record_types(row) & uncovered)
        ]
        if not candidates:
            raise ValueError(f"cannot cover entity types {sorted(uncovered)}")
        chosen = min(
            candidates,
            key=lambda row: (
                -len(_record_types(row) & uncovered),
                _stable_rank(str(row["id"]), seed=seed),
                str(row["id"]),
            ),
        )
        selected.append(chosen)
        selected_ids.add(str(chosen["id"]))
        uncovered -= _record_types(chosen)

    for record in ranked:
        if len(selected) >= size:
            break
        if str(record["id"]) not in selected_ids:
            selected.append(record)
            selected_ids.add(str(record["id"]))
    if len(selected) != size:
        raise AssertionError(f"selected {len(selected)} records instead of {size}")
    return selected


def build_support_glossary(
    support_records: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive exact support-only glossary rows and omit type-conflicting surfaces."""

    surface_types: dict[str, set[str]] = defaultdict(set)
    counts: Counter[tuple[str, str]] = Counter()
    for record in support_records:
        for entity in record.get("entities", []):
            span = str(entity["span"]).strip()
            entity_type = str(entity["type"])
            if not span:
                continue
            surface_types[span].add(entity_type)
            counts[(span, entity_type)] += 1

    conflicts = {
        surface: sorted(types)
        for surface, types in sorted(surface_types.items())
        if len(types) > 1
    }
    rows = [
        {
            "term": span,
            "type": entity_type,
            "source": "cluener_support_bank30_seed42",
            "priority": count,
            "support_occurrences": count,
        }
        for (span, entity_type), count in counts.items()
        if span not in conflicts
    ]
    rows.sort(key=lambda row: (-int(row["priority"]), -len(str(row["term"])), str(row["term"]), str(row["type"])))
    if not rows:
        raise ValueError("support bank produced an empty unambiguous glossary")
    return rows, {
        "entries": len(rows),
        "unique_support_surfaces": len(surface_types),
        "conflicting_surfaces_omitted": len(conflicts),
        "conflicts": conflicts,
        "type_counts": dict(sorted(Counter(str(row["type"]) for row in rows).items())),
    }


def _build_ngram_index(
    blocked_records: Sequence[tuple[str, str, str]],
    *,
    ngram_size: int,
) -> tuple[list[tuple[str, str, frozenset[str]]], dict[str, set[int]]]:
    prepared: list[tuple[str, str, frozenset[str]]] = []
    inverted: dict[str, set[int]] = defaultdict(set)
    for source, record_id, text in blocked_records:
        grams = normalized_ngrams(text, ngram_size)
        index = len(prepared)
        prepared.append((source, record_id, grams))
        for gram in grams:
            inverted[gram].add(index)
    return prepared, inverted


def build_labels_stripped_rag_corpus(
    train_pool: Sequence[Mapping[str, Any]],
    *,
    support_records: Sequence[Mapping[str, Any]],
    tune_records: Sequence[Mapping[str, Any]],
    evaluation_blocklist_records: Sequence[Mapping[str, Any]],
    ngram_size: int = NGRAM_SIZE,
    containment_threshold: float = CONTAINMENT_THRESHOLD,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Strip labels and reject train rows overlapping support/tune/final-dev text."""

    blocked_records: list[tuple[str, str, str]] = []
    blocked_ids: dict[str, set[str]] = {}
    for source, records in (
        ("support", support_records),
        ("tune", tune_records),
        ("cluener_dev_blocklist", evaluation_blocklist_records),
    ):
        ids = {str(record["id"]) for record in records}
        blocked_ids[source] = ids
        blocked_records.extend(
            (source, str(record["id"]), str(record["text"])) for record in records
        )

    prepared, inverted = _build_ngram_index(
        blocked_records,
        ngram_size=ngram_size,
    )
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    for record in train_pool:
        record_id = str(record["id"])
        text = str(record["text"])
        exact_source = next(
            (source for source, ids in blocked_ids.items() if record_id in ids),
            None,
        )
        if exact_source is not None:
            reason = f"exact_id_{exact_source}"
            reason_counts[reason] += 1
            removed.append(
                {
                    "removed_id": record_id,
                    "matched_id": record_id,
                    "matched_source": exact_source,
                    "containment": 1.0,
                    "reason": reason,
                }
            )
            continue

        grams = normalized_ngrams(text, ngram_size)
        candidate_indices: set[int] = set()
        for gram in grams:
            candidate_indices.update(inverted.get(gram, ()))
        best_match: tuple[float, str, str] | None = None
        for index in sorted(candidate_indices):
            source, blocked_id, blocked_grams = prepared[index]
            score = ngram_containment(grams, blocked_grams)
            if score < containment_threshold:
                continue
            candidate = (score, source, blocked_id)
            if best_match is None or candidate > best_match:
                best_match = candidate
        if best_match is not None:
            score, source, blocked_id = best_match
            reason = f"8gram_overlap_{source}"
            reason_counts[reason] += 1
            removed.append(
                {
                    "removed_id": record_id,
                    "matched_id": blocked_id,
                    "matched_source": source,
                    "containment": round(score, 6),
                    "reason": reason,
                }
            )
            continue

        kept.append(
            {
                "id": record_id,
                "text": text,
                "title": record_id,
                "source_type": "cluener_train_pool_labels_stripped",
                "content_sha256": text_sha256(text),
            }
        )

    if not kept:
        raise ValueError("deduplication removed the complete CLUENER RAG corpus")
    return kept, {
        "protocol": "fixed_8gram_containment_against_support_tune_and_cluener_dev_text",
        "ngram_size": ngram_size,
        "containment_threshold": containment_threshold,
        "train_pool_records": len(train_pool),
        "blocked_records": {
            "support": len(support_records),
            "tune": len(tune_records),
            "cluener_dev_text_only": len(evaluation_blocklist_records),
        },
        "rag_corpus_records": len(kept),
        "removed_count": len(removed),
        "removed_by_reason": dict(sorted(reason_counts.items())),
        "removed": removed,
        "labels_stripped": True,
    }


def _flatten_definitions(raw: Mapping[str, Any]) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for name, value in raw.items():
        if isinstance(value, Mapping):
            value = value.get("definition")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"entity type {name} lacks a definition")
        definitions[str(name)] = value.strip()
    if not definitions:
        raise ValueError("entity definitions are empty")
    return definitions


def load_domain_schema(path: Path) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    schema = _load_yaml(path)
    entity_types = _flatten_definitions(schema.get("entity_types", {}))
    relation_types = validate_approved_relation_matrix(schema.get("relation_types", {}))
    return entity_types, relation_types


def _future_execution(*, dataset: str) -> dict[str, Any]:
    if dataset == "domain":
        gate = DOMAIN_F4_GATE
        phase = "FULL_IE_DOMAIN_DEV_SANITY"
    elif dataset == "cluener":
        gate = CLUENER_F4_GATE
        phase = "FULL_IE_CLUENER_TUNE_SANITY"
    else:
        raise ValueError(f"unsupported dataset {dataset}")
    return {
        "phase": phase,
        "authorized": False,
        "human_gate": gate,
        "approval_record": (
            f"Prepared under {F3_GATE}; future paid execution is not authorized."
        ),
        "model_calls_allowed": False,
        "gpu_required": True,
        "explicit_exclusions": [
            "domain_test",
            "cluener_dev_final_evaluation",
            "cluener_test_unlabeled",
            "paper_edits",
            "github_sync",
        ],
    }


def _model_config() -> dict[str, Any]:
    return {
        "name": "/root/autodl-tmp/models/qwen2.5-7b",
        "base_url": "http://127.0.0.1:8000",
        "timeout_seconds": 300,
        "api_key": "EMPTY",
    }


def _generation_config(*, verifier: bool = False) -> dict[str, Any]:
    return {
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 8 if verifier else 768,
        "seed": SEED,
    }


def _embedding_config() -> dict[str, Any]:
    return {
        "model_path": "/root/autodl-tmp/models/bge-m3",
        "device": "cpu",
        "use_fp16": False,
        "batch_size": 8,
        "max_length": 512,
    }


def _resource_lock(resources: Mapping[str, Path]) -> dict[str, Any]:
    return {
        name: {"path": str(path), "sha256": sha256_file(path)}
        for name, path in sorted(resources.items())
    }


def _stage_n_config(
    *,
    dataset: str,
    variant: str,
    query_path: Path,
    support_path: Path,
    entity_types: Mapping[str, str],
    glossary_path: Path | None,
    rag_corpus_path: Path | None,
    domain_rag_corpus_path: Path | None,
    b_output_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    slug = variant.lower()
    resources: dict[str, Path] = {
        "query": query_path,
        "support": support_path,
    }
    config: dict[str, Any] = {
        "run_id": f"full-ie-f4-{dataset}-dev-{slug}-stage-n-k5-seed42",
        "config_name": variant,
        "prepared_under_gate": F3_GATE,
        "execution": _future_execution(dataset=dataset),
        "data": {
            "dataset": dataset,
            "support_path": str(support_path),
            "query_path": str(query_path),
        },
        "schema": {
            "task": "ner",
            "entity_types": dict(entity_types),
            "relation_types": {},
        },
        "examples": {
            "mode": "fixed_random" if variant == "A" else "knn_retrieval",
            "k": K,
            "seed": SEED,
        },
        "prompt": {
            "output_instruction": FIXED_OUTPUT_INSTRUCTION,
            "retry_suffix": FIXED_RETRY_SUFFIX,
            "retry_mode": "parser_error_aware",
        },
        "parsing": {
            "drop_invalid_entities": True,
            "mode": "proposal_stage_sanitize",
            "note": "Locked for F4 dev/tune sanity; final semantics require F5 freeze.",
        },
        "model": _model_config(),
        "generation": _generation_config(),
        "cache": {"dir": f"/root/project/cache/full_ie/f4/{dataset}"},
        "outputs": {
            "per_query": str(output_root / f"{slug}_stage_n_per_query.jsonl"),
            "summary": str(output_root / f"{slug}_stage_n_summary.json"),
        },
    }
    if variant == "B":
        config["embedding"] = _embedding_config()
    elif variant in {"C", "D"}:
        config["examples"] = {
            "mode": "knn_replay",
            "k": K,
            "seed": SEED,
            "source_per_query_path": str(b_output_path),
            "source_note": "Replay B example_ids so C-B and D-C remain clean comparisons.",
        }
        if glossary_path is None:
            raise ValueError(f"{dataset} {variant} requires a glossary")
        resources["glossary"] = glossary_path
        config["glossary"] = {
            "path": str(glossary_path),
            "max_entries": 20,
            "match_mode": "substring",
            "source_note": (
                "Frozen domain glossary" if dataset == "domain" else "Support-bank-only CLUENER glossary"
            ),
        }
    if variant == "D":
        corpus_path = domain_rag_corpus_path if dataset == "domain" else rag_corpus_path
        if corpus_path is None:
            raise ValueError(f"{dataset} D requires a RAG corpus")
        resources["rag_corpus"] = corpus_path
        config["rag"] = {
            "enabled": True,
            "mode": "bge_faiss_rerank",
            "corpus_path": str(corpus_path),
            "chunk_chars": 260,
            "overlap_chars": 40,
            "retrieve_top_k": 20,
            "top_k": 3,
            "max_passage_chars": 300,
            "embedding": _embedding_config(),
            "reranker": {
                "model_path": "/root/autodl-tmp/models/bge-reranker",
                "device": "cpu",
                "use_fp16": False,
            },
        }
        if dataset == "domain":
            config["rag"]["exclude_source_ids_path"] = str(query_path)
    config["resource_lock"] = _resource_lock(resources)
    return config


def _stage_r_config(
    *,
    variant: str,
    stage_n_path: Path,
    support_path: Path,
    entity_types: Mapping[str, str],
    relation_types: Mapping[str, Mapping[str, Any]],
    output_root: Path,
) -> dict[str, Any]:
    slug = variant.lower()
    return {
        "run_id": f"full-ie-f4-domain-dev-{slug}-stage-r-k5-seed42",
        "config_name": variant,
        "prepared_under_gate": F3_GATE,
        "execution": _future_execution(dataset="domain"),
        "data": {"dataset": "domain"},
        "replay": {"reuse_stage_n_metadata": True},
        "input": {
            "stage_n_per_query_path": str(stage_n_path),
            "support_path": str(support_path),
            "expected_rows": 50,
        },
        "schema": {
            "entity_types": dict(entity_types),
            "relation_types": copy.deepcopy(dict(relation_types)),
        },
        "prompt": {
            "output_instruction": FIXED_OUTPUT_INSTRUCTION,
            "retry_suffix": FIXED_RETRY_SUFFIX,
            "version": "stage_r_same_sentence_v1",
        },
        "parsing": {
            "drop_invalid_relations": False,
            "direction_is_exact": True,
            "duplicate_policy": "deduplicate_exact",
        },
        "model": _model_config(),
        "generation": _generation_config(),
        "cache": {"dir": "/root/project/cache/full_ie/f4/domain_stage_r"},
        "outputs": {
            "per_query": str(output_root / f"{slug}_stage_r_per_query.jsonl"),
            "summary": str(output_root / f"{slug}_stage_r_summary.json"),
        },
        "resource_lock": _resource_lock({"support": support_path}),
    }


def _verification_config(
    *,
    dataset: str,
    variant: str,
    source_path: Path,
    entity_types: Mapping[str, str],
    relation_types: Mapping[str, Mapping[str, Any]],
    output_root: Path,
) -> dict[str, Any]:
    source_variant = "D" if variant == "E" else "C"
    slug = "e" if variant == "E" else "eprime"
    evidence_mode = (
        "source_text_only"
        if variant == "E-prime"
        else (
            "reuse_stage_r_rag_passages"
            if dataset == "domain"
            else "reuse_source_rag_passages"
        )
    )
    evidence: dict[str, Any] = {"mode": evidence_mode}
    if variant == "E":
        evidence["max_passages"] = 3
    return {
        "run_id": f"full-ie-f4-{dataset}-dev-{slug}-verification-k5-seed42",
        "config_name": variant,
        "source_config": source_variant,
        "prepared_under_gate": F3_GATE,
        "execution": _future_execution(dataset=dataset),
        "data": {"dataset": dataset},
        "input": {
            "per_query_path": str(source_path),
            "expected_rows": 50,
        },
        "schema": {
            "entity_types": dict(entity_types),
            "relation_types": (
                copy.deepcopy(dict(relation_types)) if dataset == "domain" else {}
            ),
        },
        "evidence": evidence,
        "prompt": {
            "version": "full_ie_atomic_source_first_v1",
            "output_instruction": FIXED_VERIFIER_OUTPUT,
            "decision_policy": "Drop only valid no; keep invalid output.",
        },
        "model": _model_config(),
        "generation": _generation_config(verifier=True),
        "cache": {"dir": f"/root/project/cache/full_ie/f4/{dataset}_verification"},
        "outputs": {
            "per_query": str(output_root / f"{slug}_verified_per_query.jsonl"),
            "summary": str(output_root / f"{slug}_verified_summary.json"),
        },
    }


def build_f3_configs(
    *,
    config_root: Path,
    domain_support: Path,
    domain_dev: Path,
    domain_glossary: Path,
    domain_rag_corpus: Path,
    cluener_support: Path,
    cluener_tune_subset: Path,
    cluener_glossary: Path,
    cluener_rag_corpus: Path,
    domain_entity_types: Mapping[str, str],
    relation_types: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Path], dict[str, Any]]:
    domain_output = Path("/root/project/results/full_ie/f4/domain_dev")
    cluener_output = Path("/root/project/results/full_ie/f4/cluener_tune50")
    configs: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}

    for dataset, query_path, support_path, glossary_path, rag_path, entity_types, output_root in (
        (
            "domain",
            domain_dev,
            domain_support,
            domain_glossary,
            None,
            domain_entity_types,
            domain_output,
        ),
        (
            "cluener",
            cluener_tune_subset,
            cluener_support,
            cluener_glossary,
            cluener_rag_corpus,
            CLUENER_ENTITY_TYPES,
            cluener_output,
        ),
    ):
        b_output = output_root / "b_stage_n_per_query.jsonl"
        for variant in ("A", "B", "C", "D"):
            key = f"{dataset}_{variant.lower()}_stage_n"
            configs[key] = _stage_n_config(
                dataset=dataset,
                variant=variant,
                query_path=query_path,
                support_path=support_path,
                entity_types=entity_types,
                glossary_path=glossary_path,
                rag_corpus_path=rag_path,
                domain_rag_corpus_path=domain_rag_corpus,
                b_output_path=b_output,
                output_root=output_root,
            )

    for variant in ("A", "B", "C", "D"):
        key = f"domain_{variant.lower()}_stage_r"
        configs[key] = _stage_r_config(
            variant=variant,
            stage_n_path=domain_output / f"{variant.lower()}_stage_n_per_query.jsonl",
            support_path=domain_support,
            entity_types=domain_entity_types,
            relation_types=relation_types,
            output_root=domain_output,
        )

    configs["domain_e_verify"] = _verification_config(
        dataset="domain",
        variant="E",
        source_path=domain_output / "d_stage_r_per_query.jsonl",
        entity_types=domain_entity_types,
        relation_types=relation_types,
        output_root=domain_output,
    )
    configs["domain_eprime_verify"] = _verification_config(
        dataset="domain",
        variant="E-prime",
        source_path=domain_output / "c_stage_r_per_query.jsonl",
        entity_types=domain_entity_types,
        relation_types=relation_types,
        output_root=domain_output,
    )
    configs["cluener_e_verify"] = _verification_config(
        dataset="cluener",
        variant="E",
        source_path=cluener_output / "d_stage_n_per_query.jsonl",
        entity_types=CLUENER_ENTITY_TYPES,
        relation_types={},
        output_root=cluener_output,
    )
    configs["cluener_eprime_verify"] = _verification_config(
        dataset="cluener",
        variant="E-prime",
        source_path=cluener_output / "c_stage_n_per_query.jsonl",
        entity_types=CLUENER_ENTITY_TYPES,
        relation_types={},
        output_root=cluener_output,
    )

    for key, config in sorted(configs.items()):
        path = config_root / f"{key}.yaml"
        _write_yaml_atomic(path, config)
        paths[key] = path

    cells: list[dict[str, Any]] = []
    for dataset in ("domain", "cluener"):
        for variant in ("A", "B", "C", "D", "E", "E-prime"):
            if variant in {"A", "B", "C", "D"}:
                steps = [
                    {
                        "runner": "scripts/run_p3_extraction.py",
                        "config_key": f"{dataset}_{variant.lower()}_stage_n",
                    }
                ]
                if dataset == "domain":
                    steps.append(
                        {
                            "runner": "scripts/run_stage_r.py",
                            "config_key": f"domain_{variant.lower()}_stage_r",
                        }
                    )
            else:
                suffix = "e" if variant == "E" else "eprime"
                steps = [
                    {
                        "runner": "scripts/run_full_ie_verification.py",
                        "config_key": f"{dataset}_{suffix}_verify",
                    }
                ]
            cells.append(
                {
                    "cell_id": f"F4-{dataset}-{variant}",
                    "dataset": dataset,
                    "variant": variant,
                    "k": K,
                    "seed": SEED,
                    "status": "PREPARED_NOT_AUTHORIZED",
                    "steps": steps,
                }
            )
    run_matrix = {
        "phase": "F3",
        "prepared_under_gate": F3_GATE,
        "status": "PREPARED_NOT_AUTHORIZED",
        "reported_dev_tune_cells": len(cells),
        "runner_configs": len(configs),
        "cells": cells,
    }
    matrix_path = config_root / "run_matrix.yaml"
    _write_yaml_atomic(matrix_path, run_matrix)
    paths["run_matrix"] = matrix_path
    return paths, run_matrix


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key)
            yield from _walk_strings(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from _walk_strings(child)


def validate_prepared_configs(config_paths: Mapping[str, Path]) -> dict[str, Any]:
    output_paths: set[str] = set()
    runner_configs = 0
    for key, path in sorted(config_paths.items()):
        config = _load_yaml(path)
        if key == "run_matrix":
            cells = config.get("cells")
            if not isinstance(cells, list) or len(cells) != 12:
                raise ValueError("F3 run matrix must contain exactly 12 dev/tune cells")
            expected = {
                (dataset, variant)
                for dataset in ("domain", "cluener")
                for variant in ("A", "B", "C", "D", "E", "E-prime")
            }
            actual = {(row.get("dataset"), row.get("variant")) for row in cells}
            if actual != expected:
                raise ValueError("F3 run matrix has missing or unexpected cells")
            continue
        runner_configs += 1
        execution = config.get("execution", {})
        if execution.get("authorized") is not False:
            raise ValueError(f"{path}: F3 config must remain unauthorized")
        if execution.get("model_calls_allowed") is not False:
            raise ValueError(f"{path}: F3 config must forbid model calls")
        if config.get("prepared_under_gate") != F3_GATE:
            raise ValueError(f"{path}: wrong preparation gate")
        scan_config = copy.deepcopy(config)
        scan_config.get("execution", {}).pop("explicit_exclusions", None)
        flattened = "\n".join(_walk_strings(scan_config)).lower()
        found = [token for token in FORBIDDEN_CONFIG_TOKENS if token in flattened]
        if found:
            raise ValueError(f"{path}: forbidden final-evaluation token(s) {found}")
        for item in config.get("resource_lock", {}).values():
            resource_path = Path(str(item["path"]))
            if not resource_path.is_file():
                raise ValueError(f"{path}: missing locked resource {resource_path}")
            if sha256_file(resource_path) != item.get("sha256"):
                raise ValueError(f"{path}: resource hash mismatch for {resource_path}")
        for output in config.get("outputs", {}).values():
            output = str(output)
            if output in output_paths:
                raise ValueError(f"duplicate F4 output path {output}")
            output_paths.add(output)

        dataset = config.get("data", {}).get("dataset")
        relation_types = config.get("schema", {}).get("relation_types")
        if key.endswith("_stage_r"):
            validate_approved_relation_matrix(relation_types)
        elif dataset == "cluener" and relation_types:
            raise ValueError(f"{path}: CLUENER config must have no relation schema")

    if runner_configs != 16:
        raise ValueError(f"F3 must contain 16 executable stage configs, found {runner_configs}")
    return {
        "runner_configs": runner_configs,
        "reported_cells": 12,
        "unique_output_paths": len(output_paths),
        "all_configs_unauthorized": True,
        "model_calls_allowed": False,
        "forbidden_final_paths_absent": True,
    }


def _file_entry(path: Path, *, role: str, records: int | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "path": str(path),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if records is not None:
        entry["records"] = records
    return entry


def _copy_artifacts(
    *,
    artifact_root: Path,
    files: Mapping[str, Path],
) -> dict[str, dict[str, Any]]:
    copied: dict[str, dict[str, Any]] = {}
    for name, source in sorted(files.items()):
        if name.startswith("config_") or name == "run_matrix":
            relative = Path("configs") / source.name
        else:
            relative = Path("resources") / source.name
        destination = artifact_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        source_hash = sha256_file(source)
        destination_hash = sha256_file(destination)
        if source_hash != destination_hash:
            raise AssertionError(f"artifact copy hash mismatch for {source}")
        copied[name] = {
            "source_path": str(source),
            "artifact_path": str(destination),
            "sha256": source_hash,
            "bytes": destination.stat().st_size,
        }
    return copied


def prepare_f3_package(
    *,
    human_gate: str,
    domain_support_path: Path,
    domain_dev_path: Path,
    domain_glossary_path: Path,
    domain_rag_corpus_path: Path,
    domain_schema_path: Path,
    cluener_train_pool_path: Path,
    cluener_tune_path: Path,
    cluener_dev_blocklist_path: Path,
    resource_root: Path,
    config_root: Path,
    artifact_root: Path,
) -> dict[str, Any]:
    if human_gate != F3_GATE:
        raise RuntimeError(f"F3 preparation requires human gate {F3_GATE}")
    if os.name == "nt":
        raise RuntimeError("F3 project Python must run on AutoDL Linux, never Windows")
    if gpu_visible():
        raise RuntimeError("F3 preparation requires AutoDL no-card mode")
    all_input_paths = (
        domain_support_path,
        domain_dev_path,
        domain_glossary_path,
        domain_rag_corpus_path,
        domain_schema_path,
        cluener_train_pool_path,
        cluener_tune_path,
        cluener_dev_blocklist_path,
    )
    for path in all_input_paths:
        if not path.is_file():
            raise ValueError(f"missing F3 input {path}")
        lowered = str(path).lower()
        if "domain_test" in lowered or "cluener_test" in lowered:
            raise ValueError(f"F3 input path is forbidden: {path}")

    domain_support = _load_records(domain_support_path)
    domain_dev = _load_records(domain_dev_path)
    if len(domain_support) != 30 or len(domain_dev) != 50:
        raise ValueError("F3 domain inputs must be frozen support30/dev50")
    domain_entity_types, relation_types = load_domain_schema(domain_schema_path)
    if set(_type_counts(domain_support)) - set(domain_entity_types):
        raise ValueError("domain support contains an entity type absent from the schema")

    train_pool = _load_records(cluener_train_pool_path)
    tune_records = _load_records(cluener_tune_path)
    evaluation_blocklist = _load_text_blocklist(cluener_dev_blocklist_path)
    required_types = tuple(CLUENER_ENTITY_TYPES)
    support_records = select_coverage_records(
        train_pool,
        size=CLUENER_SUPPORT_SIZE,
        seed=SEED,
        required_types=required_types,
    )
    tune_subset = select_coverage_records(
        tune_records,
        size=CLUENER_TUNE_SIZE,
        seed=SEED,
        required_types=required_types,
    )
    support_ids = {str(record["id"]) for record in support_records}
    tune_ids = {str(record["id"]) for record in tune_records}
    dev_ids = {str(record["id"]) for record in evaluation_blocklist}
    if support_ids & tune_ids or support_ids & dev_ids or tune_ids & dev_ids:
        raise ValueError("CLUENER pool/tune/dev ids are not disjoint")

    glossary_rows, glossary_report = build_support_glossary(support_records)
    rag_rows, dedup_report = build_labels_stripped_rag_corpus(
        train_pool,
        support_records=support_records,
        tune_records=tune_records,
        evaluation_blocklist_records=evaluation_blocklist,
    )

    resource_root.mkdir(parents=True, exist_ok=True)
    support_output = resource_root / "cluener_support_bank30_seed42.jsonl"
    tune_output = resource_root / "cluener_tune_subset50_seed42.jsonl"
    glossary_output = resource_root / "cluener_support_glossary_seed42.jsonl"
    rag_output = resource_root / "cluener_rag_corpus_labels_stripped.jsonl"
    dedup_output = resource_root / "cluener_rag_dedup_report.json"
    _write_jsonl_atomic(support_output, support_records)
    _write_jsonl_atomic(tune_output, tune_subset)
    _write_jsonl_atomic(glossary_output, glossary_rows)
    _write_jsonl_atomic(rag_output, rag_rows)
    _write_json_atomic(dedup_output, dedup_report)

    config_paths, run_matrix = build_f3_configs(
        config_root=config_root,
        domain_support=domain_support_path,
        domain_dev=domain_dev_path,
        domain_glossary=domain_glossary_path,
        domain_rag_corpus=domain_rag_corpus_path,
        cluener_support=support_output,
        cluener_tune_subset=tune_output,
        cluener_glossary=glossary_output,
        cluener_rag_corpus=rag_output,
        domain_entity_types=domain_entity_types,
        relation_types=relation_types,
    )
    config_validation = validate_prepared_configs(config_paths)

    primary_files: dict[str, Path] = {
        "cluener_support": support_output,
        "cluener_tune_subset": tune_output,
        "cluener_glossary": glossary_output,
        "cluener_rag_corpus": rag_output,
        "cluener_dedup_report": dedup_output,
    }
    primary_files.update(
        {
            ("run_matrix" if key == "run_matrix" else f"config_{key}"): path
            for key, path in config_paths.items()
        }
    )
    artifact_root.mkdir(parents=True, exist_ok=True)
    copies = _copy_artifacts(artifact_root=artifact_root, files=primary_files)

    manifest_path = artifact_root / "f3_manifest.json"
    manifest = {
        "phase": "F3",
        "gate": F3_GATE,
        "status": "PREPARED_NOT_AUTHORIZED",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety": {
            "gpu_device_present": False,
            "model_calls": 0,
            "api_called": False,
            "vllm_started": False,
            "domain_test_read": False,
            "real_prompt_artifacts_generated": False,
            "paper_edited": False,
            "github_synced": False,
            "cluener_dev_use": "text-only deduplication blocklist; no prompt or metric",
        },
        "inputs": {
            "domain_support": _file_entry(domain_support_path, role="domain_support", records=30),
            "domain_dev": _file_entry(domain_dev_path, role="domain_dev", records=50),
            "domain_glossary": _file_entry(domain_glossary_path, role="frozen_domain_glossary"),
            "domain_rag_corpus": _file_entry(domain_rag_corpus_path, role="deduplicated_domain_rag"),
            "domain_schema": _file_entry(domain_schema_path, role="approved_domain_schema_v3"),
            "cluener_train_pool": _file_entry(
                cluener_train_pool_path,
                role="support_and_rag_source",
                records=len(train_pool),
            ),
            "cluener_tune": _file_entry(
                cluener_tune_path,
                role="tuning_only",
                records=len(tune_records),
            ),
            "cluener_dev_blocklist": _file_entry(
                cluener_dev_blocklist_path,
                role="text_only_dedup_blocklist",
                records=len(evaluation_blocklist),
            ),
        },
        "resources": {
            "support_bank": {
                **_file_entry(support_output, role="fixed_support_bank", records=len(support_records)),
                "seed": SEED,
                "entity_type_counts": _type_counts(support_records),
                "all_types_covered": set(_type_counts(support_records)) == set(required_types),
            },
            "tune_subset": {
                **_file_entry(tune_output, role="fixed_paid_sanity_subset", records=len(tune_subset)),
                "seed": SEED,
                "entity_type_counts": _type_counts(tune_subset),
                "all_types_covered": set(_type_counts(tune_subset)) == set(required_types),
            },
            "glossary": {
                **_file_entry(glossary_output, role="support_only_exact_glossary", records=len(glossary_rows)),
                **glossary_report,
            },
            "rag_corpus": {
                **_file_entry(rag_output, role="labels_stripped_deduplicated_rag", records=len(rag_rows)),
                "labels_stripped": True,
            },
            "dedup_report": {
                **_file_entry(dedup_output, role="fixed_8gram_dedup_report"),
                "removed_count": dedup_report["removed_count"],
                "removed_by_reason": dedup_report["removed_by_reason"],
            },
        },
        "configs": {
            "runner_config_count": 16,
            "reported_dev_tune_cells": 12,
            "run_matrix_sha256": sha256_file(config_paths["run_matrix"]),
            "validation": config_validation,
            "files": {
                key: _file_entry(path, role="f4_locked_future_config")
                for key, path in sorted(config_paths.items())
            },
            "run_matrix_canonical_sha256": canonical_sha256(run_matrix),
        },
        "artifact_copies": copies,
    }
    _write_json_atomic(manifest_path, manifest)
    report_path = artifact_root / "f3_report.json"
    report = {
        "status": "ok",
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "support_records": len(support_records),
        "tune_subset_records": len(tune_subset),
        "rag_records": len(rag_rows),
        "rag_removed": dedup_report["removed_count"],
        "glossary_entries": len(glossary_rows),
        "runner_configs": 16,
        "reported_dev_tune_cells": 12,
        "model_calls": 0,
        "paid_gpu_cost_cny": 0,
    }
    _write_json_atomic(report_path, report)
    return report


def validate_f3_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("phase") != "F3" or manifest.get("gate") != F3_GATE:
        raise ValueError("not an F3 config-preparation manifest")
    if manifest.get("status") != "PREPARED_NOT_AUTHORIZED":
        raise ValueError("F3 manifest must remain PREPARED_NOT_AUTHORIZED")
    safety = manifest.get("safety", {})
    required_false = (
        "gpu_device_present",
        "api_called",
        "vllm_started",
        "domain_test_read",
        "real_prompt_artifacts_generated",
        "paper_edited",
        "github_synced",
    )
    for key in required_false:
        if safety.get(key) is not False:
            raise ValueError(f"F3 safety field {key} must be false")
    if safety.get("model_calls") != 0:
        raise ValueError("F3 model_calls must be zero")

    checked_files = 0
    for section in (manifest.get("inputs", {}), manifest.get("resources", {})):
        for name, item in section.items():
            file_path = Path(str(item["path"]))
            if not file_path.is_file():
                raise ValueError(f"missing manifest file {name}: {file_path}")
            if sha256_file(file_path) != item.get("sha256"):
                raise ValueError(f"manifest hash mismatch for {name}")
            checked_files += 1

    resource_items = manifest.get("resources", {})
    support_path = Path(str(resource_items["support_bank"]["path"]))
    tune_subset_path = Path(str(resource_items["tune_subset"]["path"]))
    glossary_path = Path(str(resource_items["glossary"]["path"]))
    rag_path = Path(str(resource_items["rag_corpus"]["path"]))
    support_rows = _load_records(support_path)
    tune_rows = _load_records(tune_subset_path)
    if len(support_rows) != CLUENER_SUPPORT_SIZE:
        raise ValueError("F3 support bank record count mismatch")
    if len(tune_rows) != CLUENER_TUNE_SIZE:
        raise ValueError("F3 tune subset record count mismatch")
    expected_types = set(CLUENER_ENTITY_TYPES)
    if set(_type_counts(support_rows)) != expected_types:
        raise ValueError("F3 support bank does not cover all CLUENER entity types")
    if set(_type_counts(tune_rows)) != expected_types:
        raise ValueError("F3 tune subset does not cover all CLUENER entity types")
    support_ids = {str(row["id"]) for row in support_rows}
    tune_ids = {str(row["id"]) for row in tune_rows}
    if support_ids & tune_ids:
        raise ValueError("F3 support bank and tune subset overlap")

    glossary_rows = [
        dict(row) for row in iter_jsonl(glossary_path, validate=False)
    ]
    support_surfaces = {
        str(entity["span"])
        for row in support_rows
        for entity in row["entities"]
    }
    if not glossary_rows or any(
        not isinstance(row.get("term"), str)
        or not isinstance(row.get("type"), str)
        or row["term"] not in support_surfaces
        for row in glossary_rows
    ):
        raise ValueError("F3 glossary contains a term absent from support bank")
    rag_rows = [dict(row) for row in iter_jsonl(rag_path, validate=False)]
    rag_ids: set[str] = set()
    for row in rag_rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or not record_id or record_id in rag_ids:
            raise ValueError("F3 RAG corpus has invalid or duplicate IDs")
        rag_ids.add(record_id)
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError("F3 RAG corpus contains an empty text")
        if "entities" in row or "relations" in row:
            raise ValueError("F3 RAG corpus is not labels-stripped")
    if rag_rows and rag_ids & (support_ids | tune_ids):
        raise ValueError("F3 RAG corpus contains support/tune IDs")
    if resource_items["rag_corpus"].get("labels_stripped") is not True:
        raise ValueError("F3 RAG resource must be marked labels_stripped")

    raw_config_files = manifest.get("configs", {}).get("files", {})
    config_paths: dict[str, Path] = {}
    for key, item in raw_config_files.items():
        config_path = Path(str(item["path"]))
        if not config_path.is_file():
            raise ValueError(f"missing F3 config {key}: {config_path}")
        if sha256_file(config_path) != item.get("sha256"):
            raise ValueError(f"F3 config hash mismatch for {key}")
        config_paths[key] = config_path
        checked_files += 1
    config_validation = validate_prepared_configs(config_paths)

    for name, item in manifest.get("artifact_copies", {}).items():
        source = Path(str(item["source_path"]))
        copied = Path(str(item["artifact_path"]))
        if not source.is_file() or not copied.is_file():
            raise ValueError(f"missing F3 artifact copy {name}")
        expected = item.get("sha256")
        if sha256_file(source) != expected or sha256_file(copied) != expected:
            raise ValueError(f"F3 artifact copy mismatch for {name}")
        checked_files += 2

    return {
        "status": "ok",
        "manifest_path": str(path),
        "manifest_sha256": sha256_file(path),
        "checked_files": checked_files,
        "config_validation": config_validation,
        "model_calls": 0,
        "gpu_required": False,
    }
