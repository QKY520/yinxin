"""No-card F6 RAG replay preparation and leakage validation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .domain_data import ngram_containment, normalized_ngrams


F6_GATE = "FULL_IE_F6_REPLAY_PREP_APPROVED"
F6_VERSION = "full-ie-f6-replay-v1"
F5_MANIFEST_SHA256 = "592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e"

EXPECTED_RETRIEVAL = {
    "embedding": "BGE-M3 normalized vectors",
    "glossary_max_entries": 20,
    "index": "FAISS inner product",
    "reranker": "bge-reranker-v2-m3",
    "rag_chunk_chars": 260,
    "rag_overlap_chars": 40,
    "retrieve_top_k": 20,
    "rerank_top_k": 3,
    "max_passage_chars": 300,
}

PROHIBITED_REPLAY_FIELDS = {
    "gold",
    "entities",
    "relations",
    "pred_raw",
    "pred_verified",
    "prompt",
    "raw_output",
    "query_text",
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def nonempty_line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def read_cgroup_memory_limit_bytes() -> int | None:
    candidates = (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    )
    for path in candidates:
        if not path.is_file():
            continue
        value = path.read_text(encoding="utf-8").strip()
        if value == "max":
            return None
        try:
            limit = int(value)
        except ValueError as exc:
            raise ValueError(f"{path}: invalid cgroup memory limit {value!r}") from exc
        if limit <= 0:
            raise ValueError(f"{path}: cgroup memory limit must be positive")
        return limit
    return None


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _model_weight_inventory(model_path: Path) -> dict[str, Any]:
    if not model_path.is_dir():
        raise ValueError(f"missing model directory {model_path}")
    weight_paths: set[Path] = set()
    for pattern in ("pytorch_model*.bin", "*.safetensors", "*.pt"):
        weight_paths.update(path for path in model_path.rglob(pattern) if path.is_file())
    if not weight_paths:
        raise ValueError(f"no model weight files found under {model_path}")
    return {
        "path": str(model_path),
        "weight_files": len(weight_paths),
        "weight_bytes": sum(path.stat().st_size for path in weight_paths),
    }


def inspect_cpu_model_memory(
    inputs: Mapping[str, Any],
    *,
    memory_limit_bytes: int | None,
) -> dict[str, Any]:
    if isinstance(memory_limit_bytes, bool) or (
        memory_limit_bytes is not None and memory_limit_bytes <= 0
    ):
        raise ValueError("memory_limit_bytes must be positive or None")
    models = _require_mapping(inputs.get("models"), label="models")
    inventories = {
        "embedding": _model_weight_inventory(Path(str(models.get("embedding_path")))),
        "reranker": _model_weight_inventory(Path(str(models.get("reranker_path")))),
    }
    minimum_weight_bytes = sum(
        int(inventory["weight_bytes"]) for inventory in inventories.values()
    )
    sufficient = memory_limit_bytes is None or memory_limit_bytes >= minimum_weight_bytes
    return {
        "device": models.get("device"),
        "use_fp16": models.get("use_fp16"),
        "cgroup_memory_limit_bytes": memory_limit_bytes,
        "minimum_model_weight_bytes": minimum_weight_bytes,
        "headroom_bytes_before_runtime": (
            None if memory_limit_bytes is None else memory_limit_bytes - minimum_weight_bytes
        ),
        "basis": "sum_of_discovered_weight_file_bytes_lower_bound",
        "models": inventories,
        "sufficient": sufficient,
    }


def _validate_lock(
    value: Any,
    *,
    label: str,
    expected_rows: int | None,
    verify_file: bool,
) -> dict[str, Any]:
    lock = _require_mapping(value, label=label)
    path_value = lock.get("path")
    digest = lock.get("sha256")
    rows = lock.get("rows")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValueError(f"{label}.path must be absolute")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError(f"{label}.sha256 must be SHA256")
    if rows != expected_rows:
        raise ValueError(f"{label}.rows must be {expected_rows!r}")
    if verify_file:
        path = Path(path_value)
        if not path.is_file():
            raise ValueError(f"{label}: missing file {path}")
        if sha256_file(path) != digest:
            raise ValueError(f"{label}: SHA256 mismatch for {path}")
        if expected_rows is not None and nonempty_line_count(path) != expected_rows:
            raise ValueError(f"{label}: row count mismatch for {path}")
    return dict(lock)


def _locked_rows(lock: Mapping[str, Any], *, label: str) -> int:
    rows = lock.get("rows")
    if isinstance(rows, bool) or not isinstance(rows, int) or rows <= 0:
        raise ValueError(f"{label}.rows must be a positive integer")
    return rows


def validate_f6_inputs(
    inputs: Mapping[str, Any],
    *,
    repo_root: Path,
    verify_files: bool = False,
) -> dict[str, Any]:
    if inputs.get("version") != F6_VERSION:
        raise ValueError(f"version must be {F6_VERSION}")
    if inputs.get("human_gate") != F6_GATE:
        raise ValueError(f"human_gate must be {F6_GATE}")
    if inputs.get("date") != "2026-08-02":
        raise ValueError("date must be 2026-08-02")

    authorization = _require_mapping(inputs.get("authorization"), label="authorization")
    expected_authorization = {
        "gpu_required": False,
        "llm_calls_allowed": False,
        "final_evaluation_allowed": False,
        "stage_execution_allowed": False,
        "aggregation_allowed": False,
        "paper_edits_allowed": False,
        "github_sync_allowed": False,
    }
    if dict(authorization) != expected_authorization:
        raise ValueError("authorization must match the bounded F6 no-card contract")

    retrieval = _require_mapping(inputs.get("retrieval"), label="retrieval")
    if dict(retrieval) != EXPECTED_RETRIEVAL:
        raise ValueError("retrieval contract differs from the F5 freeze")
    leakage = _require_mapping(inputs.get("leakage"), label="leakage")
    if leakage.get("ngram_size") != 8 or leakage.get("containment_threshold") != 0.8:
        raise ValueError("leakage audit must use fixed 8-gram containment at 0.8")
    if leakage.get("reject_source_self_hit") is not True:
        raise ValueError("source self-hits must be rejected")

    f5 = _require_mapping(inputs.get("f5_manifest"), label="f5_manifest")
    relative_path = f5.get("repo_relative_path")
    if not isinstance(relative_path, str) or Path(relative_path).is_absolute():
        raise ValueError("f5_manifest.repo_relative_path must be repo-relative")
    if f5.get("sha256") != F5_MANIFEST_SHA256:
        raise ValueError("F5 manifest SHA256 changed")
    f5_path = (repo_root / relative_path).resolve()
    if verify_files:
        if sha256_file(f5_path) != F5_MANIFEST_SHA256:
            raise ValueError("F5 manifest file does not match the frozen SHA256")
        f5_manifest = load_json(f5_path)
        frozen_retrieval = f5_manifest.get("protocol_contract", {}).get("retrieval")
        if frozen_retrieval != EXPECTED_RETRIEVAL:
            raise ValueError("F5 manifest retrieval contract changed")
        if f5_manifest.get("status") != "FROZEN_NOT_AUTHORIZED":
            raise ValueError("F5 manifest unexpectedly authorizes execution")

    resources = _require_mapping(inputs.get("resources"), label="resources")
    expected_resource_rows = {
        "domain_query": 170,
        "domain_corpus": 230,
        "cluener_query": 1343,
        "cluener_corpus": 9584,
        "model_file_manifest": 65,
        "model_manifest_metadata": 2,
    }
    if set(resources) != set(expected_resource_rows):
        raise ValueError("resource inventory must contain exactly six frozen locks")
    for name, expected_rows in expected_resource_rows.items():
        _validate_lock(
            resources[name],
            label=f"resources.{name}",
            expected_rows=expected_rows,
            verify_file=verify_files,
        )

    domain_sources = inputs.get("domain_consensus_sources")
    if not isinstance(domain_sources, list) or len(domain_sources) != 3:
        raise ValueError("domain_consensus_sources must contain three seeds")
    seeds: set[int] = set()
    for index, value in enumerate(domain_sources):
        lock = _require_mapping(value, label=f"domain_consensus_sources[{index}]")
        seed = lock.get("seed")
        if seed not in {42, 43, 44} or seed in seeds:
            raise ValueError("domain consensus seeds must be exactly 42/43/44")
        seeds.add(int(seed))
        _validate_lock(
            lock,
            label=f"domain_consensus_sources[{index}]",
            expected_rows=170,
            verify_file=verify_files,
        )

    models = _require_mapping(inputs.get("models"), label="models")
    if models.get("embedding_path") != "/root/autodl-tmp/models/bge-m3":
        raise ValueError("BGE-M3 path changed")
    if models.get("reranker_path") != "/root/autodl-tmp/models/bge-reranker":
        raise ValueError("reranker path changed")
    if models.get("device") != "cpu" or models.get("use_fp16") is not False:
        raise ValueError("F6 models must remain CPU FP32")

    source_paths = inputs.get("source_paths")
    if not isinstance(source_paths, list) or not source_paths:
        raise ValueError("source_paths must be a non-empty list")
    if len(source_paths) != len(set(source_paths)):
        raise ValueError("source_paths contains duplicates")
    if any(not isinstance(path, str) or Path(path).is_absolute() for path in source_paths):
        raise ValueError("source_paths must be repo-relative strings")
    if verify_files:
        for relative in source_paths:
            path = repo_root / relative
            if not path.is_file():
                raise ValueError(f"missing F6 source file {path}")

    return {
        "version": F6_VERSION,
        "gate": F6_GATE,
        "resources": len(resources),
        "domain_sources": len(domain_sources),
        "source_paths": len(source_paths),
        "gpu_required": False,
        "llm_calls_allowed": False,
    }


def build_source_locks(repo_root: Path, source_paths: Sequence[str]) -> list[dict[str, str]]:
    locks: list[dict[str, str]] = []
    for relative in sorted(source_paths):
        path = repo_root / relative
        if not path.is_file():
            raise ValueError(f"missing F6 source file {path}")
        locks.append({"path": relative, "sha256": sha256_file(path)})
    return locks


def _query_index(path: Path, *, expected_rows: int) -> tuple[list[str], dict[str, str]]:
    ids: list[str] = []
    texts: dict[str, str] = {}
    for row in load_jsonl(path):
        record_id = row.get("id")
        text = row.get("text")
        if not isinstance(record_id, str) or not record_id or record_id in texts:
            raise ValueError(f"{path}: query IDs must be unique non-empty strings")
        if not isinstance(text, str) or not text:
            raise ValueError(f"{path}: query text must be non-empty")
        ids.append(record_id)
        texts[record_id] = text
    if len(ids) != expected_rows:
        raise ValueError(f"{path}: expected {expected_rows} query rows")
    return ids, texts


def _validate_passage_lists(
    row: Mapping[str, Any],
    *,
    label: str,
) -> tuple[list[str], list[str]]:
    passage_ids = row.get("rag_passage_ids")
    passages = row.get("rag_passages")
    if not isinstance(passage_ids, list) or len(passage_ids) != 3:
        raise ValueError(f"{label}: expected exactly three passage IDs")
    if not isinstance(passages, list) or len(passages) != 3:
        raise ValueError(f"{label}: expected exactly three passage displays")
    if any(not isinstance(value, str) or not value for value in passage_ids):
        raise ValueError(f"{label}: passage IDs must be non-empty strings")
    if any(not isinstance(value, str) or not value for value in passages):
        raise ValueError(f"{label}: passage displays must be non-empty strings")
    if len(set(passage_ids)) != 3:
        raise ValueError(f"{label}: passage IDs must be unique")
    return list(passage_ids), list(passages)


def build_domain_consensus_manifest(
    inputs: Mapping[str, Any],
    *,
    output_path: Path,
    config_sha256: str,
) -> dict[str, Any]:
    query_lock = inputs["resources"]["domain_query"]
    query_path = Path(query_lock["path"])
    query_ids, query_texts = _query_index(
        query_path,
        expected_rows=_locked_rows(query_lock, label="resources.domain_query"),
    )

    source_maps: list[tuple[Mapping[str, Any], dict[str, dict[str, Any]]]] = []
    for lock in sorted(inputs["domain_consensus_sources"], key=lambda item: int(item["seed"])):
        rows = load_jsonl(Path(lock["path"]))
        row_map: dict[str, dict[str, Any]] = {}
        for row in rows:
            record_id = row.get("id")
            if not isinstance(record_id, str) or record_id in row_map:
                raise ValueError(f"seed {lock['seed']}: invalid or duplicate row ID")
            _validate_passage_lists(row, label=f"seed {lock['seed']} row {record_id}")
            row_map[record_id] = row
        if set(row_map) != set(query_ids):
            raise ValueError(f"seed {lock['seed']}: query ID coverage differs")
        source_maps.append((lock, row_map))

    rows: list[dict[str, Any]] = []
    reference_seed, reference = source_maps[0]
    for record_id in query_ids:
        passage_ids, passages = _validate_passage_lists(
            reference[record_id],
            label=f"seed {reference_seed['seed']} row {record_id}",
        )
        for lock, row_map in source_maps[1:]:
            candidate_ids, candidate_passages = _validate_passage_lists(
                row_map[record_id],
                label=f"seed {lock['seed']} row {record_id}",
            )
            if candidate_ids != passage_ids or candidate_passages != passages:
                raise ValueError(
                    f"domain RAG replay differs at {record_id} between seeds "
                    f"{reference_seed['seed']} and {lock['seed']}"
                )
        rows.append(
            {
                "id": record_id,
                "query_text_sha256": text_sha256(query_texts[record_id]),
                "rag_passage_ids": passage_ids,
                "rag_passages": passages,
                "selected_passages": [
                    {"id": passage_id, "display": display}
                    for passage_id, display in zip(passage_ids, passages)
                ],
            }
        )

    manifest = {
        "stage": "f6_rag_replay",
        "version": F6_VERSION,
        "human_gate": F6_GATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "domain",
        "method": "locked_p5_d_three_seed_consensus",
        "source_rag_mode": "per_query_consensus_replay",
        "config_sha256": config_sha256,
        "f5_manifest_sha256": F5_MANIFEST_SHA256,
        "query_path": str(query_path),
        "query_path_sha256": query_lock["sha256"],
        "query_records": len(query_ids),
        "source_per_query_locks": [dict(lock) for lock, _ in source_maps],
        "api_called": False,
        "llm_calls": 0,
        "gpu_device_present": gpu_visible(),
        "rows": rows,
    }
    write_json_atomic(output_path, manifest)
    return manifest


def _checkpoint_rows(
    checkpoint_path: Path,
    *,
    query_texts: Mapping[str, str],
) -> dict[str, dict[str, Any]]:
    if not checkpoint_path.exists():
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(checkpoint_path):
        record_id = row.get("id")
        if not isinstance(record_id, str) or record_id in rows or record_id not in query_texts:
            raise ValueError(f"{checkpoint_path}: invalid checkpoint ID {record_id!r}")
        if row.get("query_text_sha256") != text_sha256(query_texts[record_id]):
            raise ValueError(f"{checkpoint_path}: query hash mismatch for {record_id}")
        _validate_passage_lists(row, label=f"checkpoint row {record_id}")
        rows[record_id] = row
    return rows


def _serialized_selected_passages(selected: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    keep_fields = (
        "id",
        "source_id",
        "source_type",
        "title",
        "chunk_index",
        "content_sha256",
        "rerank_score",
        "display",
    )
    serialized: list[dict[str, Any]] = []
    for passage in selected:
        serialized.append({key: passage[key] for key in keep_fields if key in passage})
    return serialized


def build_cluener_replay_manifest(
    inputs: Mapping[str, Any],
    *,
    output_path: Path,
    checkpoint_path: Path,
    checkpoint_metadata_path: Path,
    config_sha256: str,
    selector_builder: Callable[
        [dict[str, Any]],
        tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]],
    ],
    progress_every: int = 25,
) -> dict[str, Any]:
    query_lock = inputs["resources"]["cluener_query"]
    query_path = Path(query_lock["path"])
    query_ids, query_texts = _query_index(
        query_path,
        expected_rows=_locked_rows(query_lock, label="resources.cluener_query"),
    )
    retrieval = inputs["retrieval"]
    models = inputs["models"]
    rag_config = {
        "enabled": True,
        "mode": "bge_faiss_rerank",
        "corpus_path": inputs["resources"]["cluener_corpus"]["path"],
        "chunk_chars": retrieval["rag_chunk_chars"],
        "overlap_chars": retrieval["rag_overlap_chars"],
        "retrieve_top_k": retrieval["retrieve_top_k"],
        "top_k": retrieval["rerank_top_k"],
        "max_passage_chars": retrieval["max_passage_chars"],
        "embedding": {
            "model_path": models["embedding_path"],
            "device": "cpu",
            "use_fp16": False,
            "batch_size": models["embedding_batch_size"],
            "max_length": models["max_length"],
        },
        "reranker": {
            "model_path": models["reranker_path"],
            "device": "cpu",
            "use_fp16": False,
        },
    }
    selector_config = {"data": {"query_path": str(query_path)}, "rag": rag_config}
    selector_contract_sha256 = canonical_sha256(selector_config)
    expected_checkpoint_metadata = {
        "version": F6_VERSION,
        "dataset": "cluener",
        "config_sha256": config_sha256,
        "selector_contract_sha256": selector_contract_sha256,
        "query_path_sha256": query_lock["sha256"],
        "corpus_sha256": inputs["resources"]["cluener_corpus"]["sha256"],
    }
    if checkpoint_metadata_path.exists():
        if load_json(checkpoint_metadata_path) != expected_checkpoint_metadata:
            raise ValueError("CLUENER checkpoint metadata does not match the frozen contract")
    else:
        write_json_atomic(checkpoint_metadata_path, expected_checkpoint_metadata)

    completed = _checkpoint_rows(checkpoint_path, query_texts=query_texts)
    select_rag, rag_metadata = selector_builder(selector_config)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if checkpoint_path.exists() else "w"
    with checkpoint_path.open(mode, encoding="utf-8", newline="\n") as handle:
        for index, record_id in enumerate(query_ids, start=1):
            if record_id in completed:
                continue
            started = time.monotonic()
            selected = select_rag({"id": record_id, "text": query_texts[record_id]})
            if len(selected) != 3:
                raise ValueError(f"CLUENER row {record_id}: selector returned {len(selected)} passages")
            passage_ids = [str(passage["id"]) for passage in selected]
            displays = [str(passage["display"]) for passage in selected]
            row = {
                "id": record_id,
                "query_text_sha256": text_sha256(query_texts[record_id]),
                "rag_passage_ids": passage_ids,
                "rag_passages": displays,
                "selected_passages": _serialized_selected_passages(selected),
                "selection_latency_ms": round((time.monotonic() - started) * 1000.0, 3),
            }
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            completed[record_id] = row
            if progress_every > 0 and (index % progress_every == 0 or index == len(query_ids)):
                print(
                    json.dumps(
                        {
                            "stage": "f6_cluener_replay_progress",
                            "completed": len(completed),
                            "total": len(query_ids),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

    if set(completed) != set(query_ids):
        raise ValueError("CLUENER checkpoint does not cover every query")
    rows = [completed[record_id] for record_id in query_ids]
    manifest = {
        "stage": "f6_rag_replay",
        "version": F6_VERSION,
        "human_gate": F6_GATE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": "cluener",
        "method": "bge_m3_faiss_top20_reranker_top3",
        "source_rag_mode": "bge_faiss_rerank",
        "config_sha256": config_sha256,
        "selector_contract_sha256": selector_contract_sha256,
        "f5_manifest_sha256": F5_MANIFEST_SHA256,
        "query_path": str(query_path),
        "query_path_sha256": query_lock["sha256"],
        "query_records": len(query_ids),
        "corpus_path": inputs["resources"]["cluener_corpus"]["path"],
        "corpus_sha256": inputs["resources"]["cluener_corpus"]["sha256"],
        "rag_selection": rag_metadata,
        "api_called": False,
        "llm_calls": 0,
        "gpu_device_present": gpu_visible(),
        "rows": rows,
    }
    write_json_atomic(output_path, manifest)
    return manifest


def _display_passage_text(display: str, passage_id: str) -> str:
    marker = f"{passage_id}: "
    position = display.find(marker)
    if position < 0:
        raise ValueError(f"passage display does not contain its ID marker {passage_id}")
    text = display[position + len(marker) :]
    if not text:
        raise ValueError(f"passage display has empty text for {passage_id}")
    if text.endswith("..."):
        raise ValueError(f"passage display is unexpectedly truncated for {passage_id}")
    return text


def _contains_prohibited_field(value: Any) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in PROHIBITED_REPLAY_FIELDS:
                return str(key)
            found = _contains_prohibited_field(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _contains_prohibited_field(child)
            if found is not None:
                return found
    return None


def validate_replay_manifest(
    manifest: Mapping[str, Any],
    inputs: Mapping[str, Any],
    *,
    dataset: str,
    config_sha256: str,
) -> dict[str, Any]:
    if dataset not in {"domain", "cluener"}:
        raise ValueError("dataset must be domain or cluener")
    query_lock = inputs["resources"][f"{dataset}_query"]
    expected_rows = _locked_rows(query_lock, label=f"resources.{dataset}_query")
    query_ids, query_texts = _query_index(Path(query_lock["path"]), expected_rows=expected_rows)
    if manifest.get("version") != F6_VERSION or manifest.get("human_gate") != F6_GATE:
        raise ValueError(f"{dataset}: invalid F6 version or gate")
    if manifest.get("dataset") != dataset:
        raise ValueError(f"{dataset}: manifest dataset mismatch")
    if manifest.get("config_sha256") != config_sha256:
        raise ValueError(f"{dataset}: config SHA256 mismatch")
    if manifest.get("f5_manifest_sha256") != F5_MANIFEST_SHA256:
        raise ValueError(f"{dataset}: F5 manifest SHA256 mismatch")
    if manifest.get("query_path_sha256") != query_lock["sha256"]:
        raise ValueError(f"{dataset}: query SHA256 mismatch")
    if manifest.get("query_records") != expected_rows:
        raise ValueError(f"{dataset}: query row count mismatch")
    if manifest.get("api_called") is not False or manifest.get("llm_calls") != 0:
        raise ValueError(f"{dataset}: LLM/API calls are forbidden")
    if manifest.get("gpu_device_present") is not False:
        raise ValueError(f"{dataset}: replay must be built in no-card mode")

    prohibited = _contains_prohibited_field(manifest)
    if prohibited is not None:
        raise ValueError(f"{dataset}: replay leaks prohibited field {prohibited}")
    rows = manifest.get("rows")
    if not isinstance(rows, list) or len(rows) != expected_rows:
        raise ValueError(f"{dataset}: replay row count mismatch")

    row_ids: list[str] = []
    max_containment = 0.0
    containment_total = 0.0
    selected_count = 0
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"{dataset}: row {index} must be an object")
        record_id = row.get("id")
        if not isinstance(record_id, str) or record_id not in query_texts:
            raise ValueError(f"{dataset}: row {index} has invalid ID")
        row_ids.append(record_id)
        if row.get("query_text_sha256") != text_sha256(query_texts[record_id]):
            raise ValueError(f"{dataset}: query hash mismatch for {record_id}")
        passage_ids, displays = _validate_passage_lists(row, label=f"{dataset} row {record_id}")
        selected = row.get("selected_passages")
        if not isinstance(selected, list) or len(selected) != 3:
            raise ValueError(f"{dataset}: selected_passages mismatch for {record_id}")
        selected_ids = [passage.get("id") for passage in selected if isinstance(passage, Mapping)]
        selected_displays = [
            passage.get("display") for passage in selected if isinstance(passage, Mapping)
        ]
        if selected_ids != passage_ids or selected_displays != displays:
            raise ValueError(f"{dataset}: selected passage fields diverge for {record_id}")
        if dataset == "cluener" and any(
            not isinstance(passage, Mapping)
            or isinstance(passage.get("rerank_score"), bool)
            or not isinstance(passage.get("rerank_score"), (int, float))
            or not math.isfinite(float(passage["rerank_score"]))
            for passage in selected
        ):
            raise ValueError(f"{dataset}: finite reranker score missing for {record_id}")

        query_grams = normalized_ngrams(query_texts[record_id], 8)
        for passage_id, display, passage in zip(passage_ids, displays, selected):
            source_id = str(passage.get("source_id") or passage_id.split("#chunk-", 1)[0])
            if source_id == record_id:
                raise ValueError(f"{dataset}: source self-hit {record_id} -> {passage_id}")
            passage_text = _display_passage_text(display, passage_id)
            score = ngram_containment(query_grams, normalized_ngrams(passage_text, 8))
            max_containment = max(max_containment, score)
            containment_total += score
            selected_count += 1
            if score >= float(inputs["leakage"]["containment_threshold"]):
                raise ValueError(
                    f"{dataset}: 8-gram containment {score:.6f} reaches threshold for "
                    f"{record_id} -> {passage_id}"
                )

    if row_ids != query_ids or len(set(row_ids)) != expected_rows:
        raise ValueError(f"{dataset}: replay IDs/order do not match the query file")
    return {
        "dataset": dataset,
        "rows": expected_rows,
        "selected_passages": selected_count,
        "source_self_hits": 0,
        "containment_hits_at_or_above_threshold": 0,
        "max_8gram_containment": round(max_containment, 6),
        "mean_8gram_containment": round(containment_total / selected_count, 6),
        "prohibited_fields": 0,
    }
