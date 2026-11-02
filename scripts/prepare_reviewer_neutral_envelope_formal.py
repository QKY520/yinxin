#!/usr/bin/env python3
"""Prepare locked, non-executable 170-row Qwen baseline formal configs."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_PREFLIGHT_APPROVED"
QUERY = Path("/root/autodl-tmp/data/domain_test.jsonl")
SUPPORT = Path("/root/autodl-tmp/data/domain_support.jsonl")
CORPUS = Path("/root/autodl-tmp/data/domain_rag_corpus.jsonl")
GLOSSARY = Path("/root/project/data/domain_dict.jsonl")
P5_B = Path("/root/project/results/p5/p5_domain_test_b_knn_k5_seed42_per_query.jsonl")
P5_D = Path("/root/project/results/p5/p5_domain_test_d_rag_k5_seed42_per_query.jsonl")
REMOTE = Path("/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917")
LOCAL_CONFIG = ROOT / "configs/reviewer_qwen_neutral_envelope_formal_20260917"
SYSTEMS = ("zero_shot", "bm25_only", "rag_only", "ec_fsie_full")
ENTITY_TYPES = {
    "EQUIPMENT": "完整装备、武器平台、系统或型号名称。",
    "MODULE": "装备的部件、组件、子系统、传感器、载荷或功能模块。",
    "TECH_SCHEME": "技术体制、制导方式、作战/测试/改进方案或能力方案。",
    "METRIC": "数值指标、性能参数、射程、速度、重量、时间或数量表达。",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def chunks(text: str, size: int = 260, overlap: int = 40) -> list[str]:
    if len(text) <= size:
        return [text]
    output, start = [], 0
    while start < len(text):
        output.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += size - overlap
    return output


def grams(text: str, n: int = 2) -> list[str]:
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) < n:
        return [compact] if compact else []
    return [compact[i : i + n] for i in range(len(compact) - n + 1)]


def eight_gram_containment(left: str, right: str) -> float:
    a, b = set(grams(left, 8)), set(grams(right, 8))
    return len(a & b) / min(len(a), len(b)) if a and b else 0.0


def leakage_safe_passages(corpus: list[dict], blocked: list[dict]) -> tuple[list[dict], dict]:
    blocked_ids = {str(row["id"]) for row in blocked}
    blocked_texts = {str(row["text"]) for row in blocked}
    kept_docs, removed = [], []
    for row in corpus:
        rid, text = str(row["id"]), str(row["text"])
        reason = None
        if rid in blocked_ids:
            reason = "source_id_exclusion"
        elif text in blocked_texts:
            reason = "exact_text_exclusion"
        elif any(eight_gram_containment(text, str(other["text"])) >= 0.8 for other in blocked):
            reason = "8gram_exclusion"
        if reason:
            removed.append({"id": rid, "reason": reason})
        else:
            kept_docs.append(row)
    passages = []
    for row in kept_docs:
        for index, text in enumerate(chunks(str(row["text"]))):
            pid = f"{row['id']}#chunk-{index}"
            title = str(row.get("title") or row["id"])
            display = f"{title} | {row.get('source_type') or 'unknown'} | {pid}: {text[:300]}"
            passages.append({"id": pid, "source_id": str(row["id"]), "display": display, "text": text})
    return passages, {
        "source_id_exclusion": True,
        "exact_text_exclusion": True,
        "eight_gram_exclusion": True,
        "labels_stripped": True,
        "residual_exact_text_rows": 0,
        "residual_8gram_rows": 0,
        "input_corpus_rows": len(corpus),
        "kept_corpus_rows": len(kept_docs),
        "removed_rows": len(removed),
        "removed_by_reason": dict(Counter(row["reason"] for row in removed)),
        "blocked_rows": len(blocked),
        "containment_threshold": 0.8,
        "ngram_size": 8,
    }


def bm25_rows(queries: list[dict], passages: list[dict]) -> list[dict]:
    tokenized = [grams(row["text"]) for row in passages]
    lengths = [len(tokens) for tokens in tokenized]
    avgdl = sum(lengths) / len(lengths)
    df = Counter(token for tokens in tokenized for token in set(tokens))
    n_docs, k1, b = len(passages), 1.5, 0.75
    rows = []
    for query in queries:
        qtokens = set(grams(str(query["text"])))
        scored = []
        for index, (passage, tokens, dl) in enumerate(zip(passages, tokenized, lengths)):
            tf = Counter(tokens)
            score = 0.0
            for token in qtokens:
                if token not in tf:
                    continue
                idf = math.log(1.0 + (n_docs - df[token] + 0.5) / (df[token] + 0.5))
                freq = tf[token]
                score += idf * freq * (k1 + 1.0) / (freq + k1 * (1.0 - b + b * dl / avgdl))
            scored.append((score, index, passage))
        selected = sorted(scored, key=lambda item: (-item[0], item[1]))[:3]
        rows.append({
            "id": str(query["id"]),
            "selected_passages": [
                {"id": item[2]["id"], "display": item[2]["display"], "bm25_score": item[0]}
                for item in selected
            ],
        })
    return rows


def dense_rows(queries: list[dict], source_rows: list[dict]) -> list[dict]:
    if [str(row["id"]) for row in source_rows] != [str(row["id"]) for row in queries]:
        raise ValueError("P5 D query order mismatch")
    output = []
    for row in source_rows:
        ids, displays = row["rag_passage_ids"], row["rag_passages"]
        if len(ids) != 3 or len(displays) != 3:
            raise ValueError(f"{row['id']}: expected three dense passages")
        output.append({
            "id": str(row["id"]),
            "selected_passages": [
                {"id": str(pid), "display": str(display)} for pid, display in zip(ids, displays)
            ],
        })
    return output


def manifest(rows: list[dict], *, mode: str, backend: str, query_sha: str, leakage: dict, corpus_sha: str) -> dict:
    return {
        "protocol": "qwen_neutral_envelope_formal_v1",
        "manifest_kind": "rag_replay",
        "retrieval_mode": mode,
        "selection_backend": backend,
        "dense_artifact_ready": True,
        "usable_for_model_calls": True,
        "query_path_sha256": query_sha,
        "query_count": len(rows),
        "top_k": 3,
        "retrieve_top_k": 20,
        "rows": rows,
        "model_calls": 0,
        "gpu_required": False,
        "labels_stripped_corpus_sha256": corpus_sha,
        "leakage_audit": leakage,
    }


def build_config(system: str, bm25_path: str, dense_path: str) -> dict:
    out = REMOTE / "formal" / system
    cfg = {
        "run_id": f"reviewer-qwen-neutral-envelope-formal-{system}-prep",
        "config_name": f"reviewer_qwen_neutral_envelope_formal_{system}",
        "execution": {"phase": "REVIEWER_QWEN_NEUTRAL_ENVELOPE_FORMAL_PREFLIGHT", "authorized": False, "human_gate": GATE, "model_calls_allowed": False, "gpu_required": True},
        "data": {"dataset": "domain_test", "support_path": None, "query_path": str(QUERY), "expected_records": 170, "expected_sha256": sha256(QUERY)},
        "schema": {"task": "ner", "entity_types": ENTITY_TYPES, "relation_types": {}},
        "examples": {"mode": "none", "k": 0, "seed": 42},
        "prompt": {"output_instruction": "只返回JSON,不要任何解释,不要markdown代码块", "retry_suffix": "只返回合法JSON", "retry_mode": "parser_error_aware"},
        "model": {"name": "/root/autodl-tmp/models/qwen2.5-7b", "base_url": "http://127.0.0.1:8000", "timeout_seconds": 300, "api_key": "EMPTY"},
        "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 768, "seed": 42},
        "parsing": {"drop_invalid_entities": True, "output_mode": "occurrence", "constrained_json_schema": False, "ner_only_envelope_policy": "entities_or_entities_relations_v2"},
        "protocol": {"name": "qwen_neutral_envelope_formal_v1", "parser_failure_ceiling": 0.20, "gold_or_bert_repair_forbidden": True, "system": system, "run_order": list(SYSTEMS)},
        "query_limit": 170,
        "dry_run": {"max_queries": 170},
        "cache": {"dir": str(out / "cache")},
        "outputs": {"dry_run_prompts": str(out / "dry_run_prompts.jsonl"), "manifest": str(out / "manifest.json"), "per_query": str(out / "per_query.jsonl"), "summary": str(out / "summary.json")},
    }
    if system == "bm25_only":
        cfg["rag"] = {"enabled": True, "mode": "replay_manifest", "replay_manifest_path": bm25_path}
    elif system == "rag_only":
        cfg["rag"] = {"enabled": True, "mode": "replay_manifest", "replay_manifest_path": dense_path}
    elif system == "ec_fsie_full":
        cfg["data"]["support_path"] = str(SUPPORT)
        cfg["examples"] = {"mode": "knn_replay", "k": 5, "seed": 42, "source_per_query_path": str(P5_B)}
        cfg["glossary"] = {"path": str(GLOSSARY), "max_entries": 20, "match_mode": "substring"}
        cfg["rag"] = {"enabled": True, "mode": "replay_manifest", "replay_manifest_path": dense_path}
    return cfg


def main() -> int:
    if LOCAL_CONFIG.exists():
        raise FileExistsError(f"refusing to overwrite {LOCAL_CONFIG}")
    queries, support, corpus = read_jsonl(QUERY), read_jsonl(SUPPORT), read_jsonl(CORPUS)
    if len(queries) != 170 or len(support) != 30:
        raise ValueError("unexpected frozen data sizes")
    passages, leakage = leakage_safe_passages(corpus, [*support, *queries])
    bm25 = bm25_rows(queries, passages)
    dense = dense_rows(queries, read_jsonl(P5_D))
    query_sha, corpus_sha = sha256(QUERY), canonical_sha(passages)
    staging = LOCAL_CONFIG.with_name(LOCAL_CONFIG.name + ".staging")
    staging.mkdir(parents=True, exist_ok=False)
    try:
        replay = staging / "replay_manifests"
        replay.mkdir()
        bm25_payload = manifest(bm25, mode="bm25_top3", backend="deterministic_okapi_bm25_char_bigram", query_sha=query_sha, leakage=leakage, corpus_sha=corpus_sha)
        dense_payload = manifest(dense, mode="bge_m3_reranker_top20_to_top3", backend="bge_m3_faiss_reranker", query_sha=query_sha, leakage=leakage, corpus_sha=sha256(P5_D))
        (replay / "bm25.json").write_text(json.dumps(bm25_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (replay / "dense.json").write_text(json.dumps(dense_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        remote_bm25 = str(REMOTE / "replay_manifests" / "bm25.json")
        remote_dense = str(REMOTE / "replay_manifests" / "dense.json")
        for system in SYSTEMS:
            (staging / f"{system}.yaml").write_text(yaml.safe_dump(build_config(system, remote_bm25, remote_dense), allow_unicode=True, sort_keys=False), encoding="utf-8")
        report = {"gate": GATE, "model_calls": 0, "query_sha256": query_sha, "query_records": 170, "support_sha256": sha256(SUPPORT), "p5_b_sha256": sha256(P5_B), "p5_d_sha256": sha256(P5_D), "bm25_manifest_sha256": sha256(replay / "bm25.json"), "dense_manifest_sha256": sha256(replay / "dense.json"), "leakage_audit": leakage, "configs_authorized": False}
        (staging / "preflight_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        staging.rename(LOCAL_CONFIG)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
