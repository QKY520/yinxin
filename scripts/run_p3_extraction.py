#!/usr/bin/env python3
"""Run or dry-run P3 few-shot extraction configs.

Dry-run mode is GPU-free and does not contact vLLM. Non-dry execution requires
an explicitly authorized config.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.extraction import (
    build_error_retry_prompt,
    build_ner_prompt,
    build_request_envelope,
    entity_micro_counts,
    parse_extraction_output,
    prompt_hash,
    select_fixed_random_examples,
    select_glossary_entries,
)
from equipment_ie.llm_labeling import chat_with_cache, request_hash
from equipment_ie.schema import iter_jsonl, sha256_file, validate_record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("pyyaml is required for config loading") from exc
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def write_json_atomic(path: Path, value: Any) -> None:
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


def write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return len(rows)


def gpu_visible() -> bool:
    return any(Path("/dev").glob("nvidia[0-9]*"))


def load_records(path: str) -> list[dict[str, Any]]:
    return [record for record in iter_jsonl(Path(path))]


def load_glossary_records(path: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, record in enumerate(iter_jsonl(Path(path), validate=False), start=1):
        term = record.get("term")
        entity_type = record.get("type")
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"{path}:{line_number}: glossary term must be a non-empty string")
        if not isinstance(entity_type, str) or not entity_type.strip():
            raise ValueError(f"{path}:{line_number}: glossary type must be a non-empty string")
        records.append(dict(record))
    if not records:
        raise ValueError(f"{path}: glossary must contain at least one row")
    return records


def chunk_text(text: str, *, chunk_chars: int, overlap_chars: int) -> list[str]:
    if chunk_chars <= 0:
        raise ValueError("chunk_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= chunk_chars:
        raise ValueError("overlap_chars must be non-negative and smaller than chunk_chars")
    if len(text) <= chunk_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    step = chunk_chars - overlap_chars
    while start < len(text):
        chunk = text[start : start + chunk_chars]
        if chunk:
            chunks.append(chunk)
        if start + chunk_chars >= len(text):
            break
        start += step
    return chunks


def load_rag_passages(path: str, *, chunk_chars: int, overlap_chars: int) -> list[dict[str, Any]]:
    passages: list[dict[str, Any]] = []
    for line_number, record in enumerate(iter_jsonl(Path(path), validate=False), start=1):
        text = record.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{path}:{line_number}: RAG corpus row must contain non-empty text")
        source_id = str(record.get("id") or f"row-{line_number}")
        title = str(record.get("title") or record.get("source_id") or source_id)
        for chunk_index, chunk in enumerate(
            chunk_text(text.strip(), chunk_chars=chunk_chars, overlap_chars=overlap_chars)
        ):
            passages.append(
                {
                    "id": f"{source_id}#chunk-{chunk_index}",
                    "source_id": source_id,
                    "source_type": record.get("source_type"),
                    "title": title,
                    "chunk_index": chunk_index,
                    "text": chunk,
                    "content_sha256": record.get("content_sha256"),
                }
            )
    if not passages:
        raise ValueError(f"{path}: RAG corpus produced no passages")
    return passages


def format_rag_passage(passage: dict[str, Any], *, max_chars: int) -> str:
    text = str(passage["text"])
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "..."
    return (
        f"{passage['title']} | {passage.get('source_type') or 'unknown'} | "
        f"{passage['id']}: {text}"
    )


def char_ngrams(text: str, *, n: int = 2) -> set[str]:
    compact = "".join(text.split())
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def lexical_rag_score(query_text: str, passage: dict[str, Any]) -> tuple[int, int, int, str]:
    passage_text = str(passage["text"])
    query_grams = char_ngrams(query_text)
    passage_grams = char_ngrams(passage_text)
    overlap = len(query_grams & passage_grams)
    exact_title = 1 if str(passage.get("title") or "") in query_text else 0
    exact_source = 1 if str(passage.get("source_id") or "") in query_text else 0
    return (overlap, exact_title, exact_source, str(passage["id"]))


def build_rag_selector(
    config: dict[str, Any],
) -> tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]:
    rag_config = config.get("rag")
    if not rag_config or rag_config.get("enabled") is not True:
        return lambda _record: [], {"enabled": False}

    corpus_path = rag_config["corpus_path"]
    top_k = int(rag_config.get("top_k", 3))
    retrieve_top_k = int(rag_config.get("retrieve_top_k", 20))
    chunk_chars = int(rag_config.get("chunk_chars", 260))
    overlap_chars = int(rag_config.get("overlap_chars", 40))
    max_passage_chars = int(rag_config.get("max_passage_chars", 300))
    mode = str(rag_config.get("mode", "lexical_preview"))
    passages = load_rag_passages(
        corpus_path,
        chunk_chars=chunk_chars,
        overlap_chars=overlap_chars,
    )
    if top_k <= 0 or retrieve_top_k < top_k:
        raise ValueError("rag.top_k must be positive and rag.retrieve_top_k must be >= top_k")

    if mode == "lexical_preview":
        def select(record: dict[str, Any]) -> list[dict[str, Any]]:
            ranked = sorted(
                passages,
                key=lambda passage: lexical_rag_score(str(record["text"]), passage),
                reverse=True,
            )
            selected = ranked[:top_k]
            return [
                {
                    **passage,
                    "display": format_rag_passage(passage, max_chars=max_passage_chars),
                }
                for passage in selected
            ]

        return select, {
            "enabled": True,
            "mode": mode,
            "note": "GPU-free lexical preview for prompt/evidence audit only; final D uses bge_faiss_rerank.",
            "corpus_path": corpus_path,
            "corpus_rows_sha256": sha256_file(corpus_path),
            "chunk_count": len(passages),
            "chunk_chars": chunk_chars,
            "overlap_chars": overlap_chars,
            "retrieve_top_k": retrieve_top_k,
            "top_k": top_k,
        }

    if mode == "bge_faiss_rerank":
        embedding_config = rag_config.get("embedding", config.get("embedding", {}))
        reranker_config = rag_config.get("reranker", {})
        model_path = embedding_config.get("model_path", "/root/autodl-tmp/models/bge-m3")
        reranker_path = reranker_config.get("model_path", "/root/autodl-tmp/models/bge-reranker")
        batch_size = int(embedding_config.get("batch_size", 8))
        max_length = int(embedding_config.get("max_length", 512))
        device = embedding_config.get("device", "cpu")
        use_fp16 = bool(embedding_config.get("use_fp16", False))
        reranker_device = reranker_config.get("device", device)
        reranker_use_fp16 = bool(reranker_config.get("use_fp16", use_fp16))
        if device == "cpu" and reranker_device == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        try:
            import faiss
            import numpy as np
            from FlagEmbedding import BGEM3FlagModel, FlagReranker
        except ImportError as exc:
            raise RuntimeError("bge_faiss_rerank requires faiss, numpy, and FlagEmbedding") from exc

        model = BGEM3FlagModel(model_path, use_fp16=use_fp16, device=device)
        reranker = FlagReranker(reranker_path, use_fp16=reranker_use_fp16, device=reranker_device)

        def encode(texts: list[str]) -> Any:
            output = model.encode(texts, batch_size=batch_size, max_length=max_length)
            dense = output["dense_vecs"] if isinstance(output, dict) else output
            vectors = np.asarray(dense, dtype="float32")
            if vectors.ndim == 1:
                vectors = vectors.reshape(1, -1)
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError("BGE-M3 produced a zero embedding")
            return vectors / norms

        passage_vectors = encode([str(passage["text"]) for passage in passages])
        index = faiss.IndexFlatIP(passage_vectors.shape[1])
        index.add(passage_vectors)

        def select(record: dict[str, Any]) -> list[dict[str, Any]]:
            query_text = str(record["text"])
            query_vector = encode([query_text])
            _, indices = index.search(query_vector, retrieve_top_k)
            candidates = [passages[int(index_)] for index_ in indices[0] if int(index_) >= 0]
            pairs = [[query_text, str(passage["text"])] for passage in candidates]
            scores = reranker.compute_score(pairs) if pairs else []
            if isinstance(scores, float):
                scores = [scores]
            ranked = sorted(zip(candidates, scores), key=lambda item: float(item[1]), reverse=True)
            return [
                {
                    **passage,
                    "rerank_score": float(score),
                    "display": format_rag_passage(passage, max_chars=max_passage_chars),
                }
                for passage, score in ranked[:top_k]
            ]

        return select, {
            "enabled": True,
            "mode": mode,
            "corpus_path": corpus_path,
            "corpus_rows_sha256": sha256_file(corpus_path),
            "chunk_count": len(passages),
            "chunk_chars": chunk_chars,
            "overlap_chars": overlap_chars,
            "retrieve_top_k": retrieve_top_k,
            "top_k": top_k,
            "embedding_model_path": model_path,
            "embedding_device": device,
            "reranker_model_path": reranker_path,
            "reranker_device": reranker_device,
            "faiss_index": "IndexFlatIP",
        }

    raise ValueError(f"unsupported rag mode {mode!r}")


def empty_prediction(gold: dict[str, Any]) -> dict[str, Any]:
    return {"id": gold["id"], "text": gold["text"], "entities": [], "relations": []}


def support_candidates(records: list[dict[str, Any]], *, k: int) -> list[dict[str, Any]]:
    candidates = [dict(record) for record in records if record.get("entities")]
    if len(candidates) < k:
        raise ValueError(f"need at least {k} support records with entities")
    return candidates


def build_knn_selector(
    *,
    config: dict[str, Any],
    support_records: list[dict[str, Any]],
) -> tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]:
    example_config = config["examples"]
    k = int(example_config["k"])
    embedding_config = config.get("embedding", {})
    model_path = embedding_config.get("model_path", "/root/autodl-tmp/models/bge-m3")
    batch_size = int(embedding_config.get("batch_size", 8))
    max_length = int(embedding_config.get("max_length", 512))
    device = embedding_config.get("device", "cpu")
    use_fp16 = bool(embedding_config.get("use_fp16", False))
    if device == "cpu":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
    try:
        import faiss
        import numpy as np
        from FlagEmbedding import BGEM3FlagModel
    except ImportError as exc:
        raise RuntimeError("knn_retrieval requires faiss, numpy, and FlagEmbedding") from exc

    candidates = support_candidates(support_records, k=k)

    model = BGEM3FlagModel(model_path, use_fp16=use_fp16, device=device)

    def encode(texts: list[str]) -> Any:
        output = model.encode(texts, batch_size=batch_size, max_length=max_length)
        dense = output["dense_vecs"] if isinstance(output, dict) else output
        vectors = np.asarray(dense, dtype="float32")
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("BGE-M3 produced a zero embedding")
        return vectors / norms

    support_vectors = encode([str(record["text"]) for record in candidates])
    index = faiss.IndexFlatIP(support_vectors.shape[1])
    index.add(support_vectors)

    def select(record: dict[str, Any]) -> list[dict[str, Any]]:
        query_vector = encode([str(record["text"])])
        _, indices = index.search(query_vector, k)
        return [dict(candidates[int(index_)]) for index_ in indices[0] if int(index_) >= 0]

    metadata = {
        "mode": "knn_retrieval",
        "k": k,
        "support_candidates": len(candidates),
        "embedding_model_path": model_path,
        "embedding_device": device,
        "embedding_max_length": max_length,
        "faiss_index": "IndexFlatIP",
    }
    return select, metadata


def build_knn_replay_selector(
    *,
    config: dict[str, Any],
    support_records: list[dict[str, Any]],
) -> tuple[Callable[[dict[str, Any]], list[dict[str, Any]]], dict[str, Any]]:
    example_config = config["examples"]
    k = int(example_config["k"])
    source_path = example_config["source_per_query_path"]
    support_by_id = {str(record["id"]): dict(record) for record in support_records}
    example_ids_by_query: dict[str, list[str]] = {}
    for line_number, row in enumerate(iter_jsonl(Path(source_path), validate=False), start=1):
        query_id = row.get("id")
        example_ids = row.get("example_ids")
        if not isinstance(query_id, str) or not query_id:
            raise ValueError(f"{source_path}:{line_number}: replay row id must be a non-empty string")
        if not isinstance(example_ids, list) or len(example_ids) < k:
            raise ValueError(f"{source_path}:{line_number}: replay row must contain at least {k} example_ids")
        normalized_ids = [str(example_id) for example_id in example_ids[:k]]
        missing = [example_id for example_id in normalized_ids if example_id not in support_by_id]
        if missing:
            raise ValueError(f"{source_path}:{line_number}: replay example ids missing from support: {missing}")
        example_ids_by_query[query_id] = normalized_ids

    def select(record: dict[str, Any]) -> list[dict[str, Any]]:
        query_id = str(record["id"])
        example_ids = example_ids_by_query.get(query_id)
        if example_ids is None:
            raise ValueError(f"{source_path}: no replay example_ids for query {query_id}")
        return [dict(support_by_id[example_id]) for example_id in example_ids]

    metadata = {
        "mode": "knn_replay",
        "source_mode": "knn_retrieval",
        "source_per_query_path": source_path,
        "k": k,
        "seed": int(example_config["seed"]),
        "query_replay_rows": len(example_ids_by_query),
    }
    return select, metadata


def build_glossary_selector(
    config: dict[str, Any],
) -> tuple[Callable[[dict[str, Any]], list[str]], dict[str, Any]]:
    glossary_config = config.get("glossary")
    if not glossary_config:
        return lambda _record: [], {"enabled": False}
    glossary_path = glossary_config["path"]
    max_entries = int(glossary_config.get("max_entries", 20))
    records = load_glossary_records(glossary_path)

    def select(record: dict[str, Any]) -> list[str]:
        return select_glossary_entries(
            str(record["text"]),
            records,
            max_entries=max_entries,
        )

    return select, {
        "enabled": True,
        "path": glossary_path,
        "candidates": len(records),
        "max_entries": max_entries,
        "match_mode": "substring",
    }


def build_query_plan(
    *,
    config: dict[str, Any],
    config_path: Path,
    dry_run: bool,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    Callable[[dict[str, Any]], list[dict[str, Any]]],
    Callable[[dict[str, Any]], list[str]],
    Callable[[dict[str, Any]], list[dict[str, Any]]],
    str,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    support_records = load_records(config["data"]["support_path"])
    query_records = load_records(config["data"]["query_path"])
    if dry_run:
        max_queries = int(config.get("dry_run", {}).get("max_queries", len(query_records)))
        query_records = query_records[:max_queries]
    example_config = config["examples"]
    select_glossary, glossary_metadata = build_glossary_selector(config)
    select_rag, rag_metadata = build_rag_selector(config)
    if example_config["mode"] == "fixed_random":
        examples = select_fixed_random_examples(
            support_records,
            k=int(example_config["k"]),
            seed=int(example_config["seed"]),
        )
        fixed_examples = [dict(record) for record in examples]
        metadata = {
            "mode": "fixed_random",
            "k": int(example_config["k"]),
            "seed": int(example_config["seed"]),
            "example_ids": [record["id"] for record in fixed_examples],
        }
        return (
            support_records,
            query_records,
            lambda _record: fixed_examples,
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )
    if example_config["mode"] == "knn_retrieval":
        selector, metadata = build_knn_selector(config=config, support_records=support_records)
        return (
            support_records,
            query_records,
            selector,
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )
    if example_config["mode"] == "knn_replay":
        selector, metadata = build_knn_replay_selector(config=config, support_records=support_records)
        return (
            support_records,
            query_records,
            selector,
            select_glossary,
            select_rag,
            sha256_file(config_path),
            metadata,
            glossary_metadata,
            rag_metadata,
        )
    raise ValueError(f"unsupported example selection mode {example_config['mode']!r}")


def run_dry(config: dict[str, Any], config_path: Path) -> int:
    (
        _,
        query_records,
        select_examples,
        select_glossary,
        select_rag,
        config_hash,
        example_metadata,
        glossary_metadata,
        rag_metadata,
    ) = build_query_plan(
        config=config, config_path=config_path, dry_run=True
    )
    entity_types = config["schema"]["entity_types"]
    generation = config["generation"]
    prompt_rows: list[dict[str, Any]] = []
    max_prompt_chars = 0
    for record in query_records:
        examples = select_examples(record)
        glossary_entries = select_glossary(record)
        rag_passages = select_rag(record)
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=entity_types,
            examples=examples,
            glossary_entries=glossary_entries,
            rag_passages=[passage["display"] for passage in rag_passages],
            include_relations=False,
            output_instruction=config["prompt"]["output_instruction"],
        )
        max_prompt_chars = max(max_prompt_chars, len(prompt))
        envelope = build_request_envelope(
            prompt=prompt,
            model=config["model"]["name"],
            generation=generation,
            run_id=config["run_id"],
            config_hash=config_hash,
        )
        prompt_rows.append(
            {
                "id": record["id"],
                "prompt_hash": prompt_hash(prompt),
                "request_hash": request_hash(envelope),
                "prompt_chars": len(prompt),
                "gold_entities": len(record["entities"]),
                "example_ids": [example["id"] for example in examples],
                "glossary_terms": glossary_entries,
                "rag_passage_ids": [passage["id"] for passage in rag_passages],
                "rag_passages": [passage["display"] for passage in rag_passages],
            }
        )

    outputs = config["outputs"]
    write_jsonl_atomic(Path(outputs["dry_run_prompts"]), prompt_rows)
    manifest = {
        "phase": "P3",
        "stage": "extraction_dry_run",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": config_hash,
        "dataset": config["data"]["dataset"],
        "query_path": config["data"]["query_path"],
        "support_path": config["data"]["support_path"],
        "query_records": len(query_records),
        "example_selection": example_metadata,
        "glossary_selection": glossary_metadata,
        "rag_selection": rag_metadata,
        "model_calls": 0,
        "api_called": False,
        "model_weights_loaded": False,
        "gpu_device_present": gpu_visible(),
        "max_prompt_chars": max_prompt_chars,
        "dry_run_prompts": outputs["dry_run_prompts"],
        "dry_run_prompts_sha256": sha256_file(outputs["dry_run_prompts"]),
    }
    write_json_atomic(Path(outputs["manifest"]), manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


def run_execute(config: dict[str, Any], config_path: Path) -> int:
    execution = config.get("execution", {})
    if execution.get("authorized") is not True:
        raise RuntimeError("config execution.authorized must be true for model calls")
    if execution.get("human_gate") not in {
        "P3_GPU_SANITY_APPROVED",
        "P3_DOMAIN_SANITY_APPROVED",
    }:
        raise RuntimeError("P3 GPU sanity human gate is not approved in config")
    if not gpu_visible():
        raise RuntimeError("GPU is not visible; refusing non-dry execution")

    (
        _,
        query_records,
        select_examples,
        select_glossary,
        select_rag,
        config_hash,
        example_metadata,
        glossary_metadata,
        rag_metadata,
    ) = build_query_plan(
        config=config, config_path=config_path, dry_run=False
    )
    entity_types = set(config["schema"]["entity_types"])
    generation = config["generation"]
    outputs = config["outputs"]
    cache_dir = Path(config["cache"]["dir"])
    base_url = config["model"]["base_url"]
    api_key = config["model"].get("api_key", "EMPTY")
    timeout_seconds = int(config["model"]["timeout_seconds"])
    retry_suffix = config["prompt"].get("retry_suffix", "只返回合法JSON")
    parsing = config.get("parsing", {})
    drop_invalid_entities = bool(parsing.get("drop_invalid_entities", False))

    rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    started = time.monotonic()
    for record in query_records:
        examples = select_examples(record)
        glossary_entries = select_glossary(record)
        rag_passages = select_rag(record)
        prompt = build_ner_prompt(
            query_text=record["text"],
            entity_types=config["schema"]["entity_types"],
            examples=examples,
            glossary_entries=glossary_entries,
            rag_passages=[passage["display"] for passage in rag_passages],
            include_relations=False,
            output_instruction=config["prompt"]["output_instruction"],
        )
        attempts: list[dict[str, Any]] = []
        pred: dict[str, Any] | None = None
        parse_error: str | None = None
        raw_output_hash = ""
        total_latency = 0.0
        sanitization_flags: list[dict[str, Any]] = []
        attempt_prompt = prompt
        for attempt_number in (1, 2):
            envelope = build_request_envelope(
                prompt=attempt_prompt,
                model=config["model"]["name"],
                generation=generation,
                run_id=config["run_id"],
                config_hash=config_hash,
            )
            result = chat_with_cache(
                envelope=envelope,
                cache_dir=cache_dir,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                api_key=api_key,
            )
            total_latency += result.latency_ms
            raw_output_hash = result.raw_output_hash
            try:
                pred = parse_extraction_output(
                    result.content,
                    record_id=record["id"],
                    text=record["text"],
                    entity_types=entity_types,
                    drop_invalid_entities=drop_invalid_entities,
                    sanitization_flags=sanitization_flags,
                )
                parse_error = None
            except Exception as exc:  # preserve exact parser message in row logs
                parse_error = f"{type(exc).__name__}: {exc}"
            attempts.append(
                {
                    "attempt": attempt_number,
                    "request_hash": result.request_hash,
                    "raw_output_hash": result.raw_output_hash,
                    "cache_hit": result.cache_hit,
                    "latency_ms": round(result.latency_ms, 3),
                    "parse_error": parse_error,
                }
            )
            if pred is not None:
                break
            if attempt_number == 1 and parse_error is not None:
                attempt_prompt = build_error_retry_prompt(
                    base_prompt=prompt,
                    parse_error=parse_error,
                    retry_suffix=retry_suffix,
                )
        if pred is None:
            pred = empty_prediction(record)
        predictions.append(pred)
        rows.append(
            {
                "id": record["id"],
                "dataset": config["data"]["dataset"],
                "config": config["config_name"],
                "k": int(config["examples"]["k"]),
                "seed": int(config["examples"]["seed"]),
                "gold": record,
                "pred_raw": pred,
                "pred_verified": None,
                "latency_ms": round(total_latency, 3),
                "parse_failure": parse_error is not None,
                "raw_llm_output_hash": raw_output_hash,
                "prompt_hash": prompt_hash(prompt),
                "example_ids": [example["id"] for example in examples],
                "glossary_terms": glossary_entries,
                "rag_passage_ids": [passage["id"] for passage in rag_passages],
                "rag_passages": [passage["display"] for passage in rag_passages],
                "attempts": attempts,
                "sanitization_flags": sanitization_flags,
            }
        )

    write_jsonl_atomic(Path(outputs["per_query"]), rows)
    counts = entity_micro_counts(query_records, predictions)
    parse_failures = sum(1 for row in rows if row["parse_failure"])
    summary = {
        "phase": "P3",
        "stage": "extraction_execution",
        "run_id": config["run_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": config_hash,
        "query_records": len(query_records),
        "example_selection": example_metadata,
        "glossary_selection": glossary_metadata,
        "rag_selection": rag_metadata,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "parse_failures": parse_failures,
        "parse_failure_rate": parse_failures / len(rows) if rows else 0.0,
        "sanitized_unit_events": sum(len(row["sanitization_flags"]) for row in rows),
        "entity_micro": counts.report(),
        "per_query": outputs["per_query"],
        "per_query_sha256": sha256_file(outputs["per_query"]),
    }
    write_json_atomic(Path(outputs["summary"]), summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    config = load_yaml(config_path)
    if args.dry_run:
        return run_dry(config, config_path)
    return run_execute(config, config_path)


if __name__ == "__main__":
    raise SystemExit(main())
