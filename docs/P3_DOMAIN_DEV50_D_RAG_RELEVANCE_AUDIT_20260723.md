# P3 Domain Dev50 D(RAG) Relevance Audit - 2026-07-23

## Purpose

Audit whether D(RAG) evidence injection is directionally useful before any paid
GPU D run.

This audit is based on the GPU-free `lexical_preview` dry-run. It checks the
RAG corpus, prompt injection, and manual relevance workflow only. It is not a
final measurement of BGE-M3 + FAISS + bge-reranker-v2-m3 quality.

Source prompts:

`logs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun_prompts.jsonl`

## Config Check

| Item | Value | Status |
|------|-------|--------|
| authorized | false | ✅ |
| model_calls_allowed | false | ✅ |
| gpu_required | false | ✅ |
| RAG mode | lexical_preview | ✅ dry-run only |
| RAG chunking | 260 chars, 40 overlap | ✅ |
| RAG corpus | domain_rag_corpus.jsonl, 230 rows | ✅ |
| Examples | knn_replay (B's IDs) | ✅ isolates C→D diff |
| Glossary | enabled, same as C | ✅ |
| Max prompt chars | 5486 (before RAG passages) | ✅ <8192 |
| Est. with RAG passages | ~6400 | ✅ <8192 |

## Sample Table

Relevance judged by lexical overlap of query vs evidence (simulating what
bge_faiss_rerank should improve). Top-1 is always score=1.000 because current
RAG corpus was only deduped against `domain_test`, not `domain_dev` — **this is
a known dev-only leakage that must be fixed before paper evaluation.**

| # | query id | prompt chars | top-1 evidence id | top-2 evidence id | top-3 evidence id | relevance | issue | keep for paid D audit? |
| ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | domain-candidate-0003 | 4760 | domain-candidate-0003#chunk-0 (SELF) | domain-candidate-0122#chunk-0 (狮鹫精确制导弹药) | domain-candidate-0004#chunk-0 (IS-2重型坦克) | **partial** | top-2 ammo-related, top-3 different equipment class; SELF must be excluded in final | **yes** — fix dedup first |
| 2 | domain-candidate-0005 | 4398 | domain-candidate-0005#chunk-0 (SELF) | domain-candidate-0320#chunk-0 (天王星-9无人战车) | domain-candidate-0139#chunk-0 (无人战斗直升机) | **partial** | top-2 ground weapon, top-3 UAV — same domain, different subdomain | **yes** |
| 3 | domain-candidate-0006 | 5155 | domain-candidate-0006#chunk-0 (SELF) | domain-candidate-0260#chunk-0 (霍巴特级驱逐舰) | domain-candidate-0333#chunk-0 (APKWS火箭弹) | **partial** | top-2 naval, top-3 precision weapons — loosely related | **yes** |
| 4 | domain-candidate-0011 | 4488 | domain-candidate-0011#chunk-0 (SELF) | domain-candidate-0145#chunk-0 (M1117装甲车) | domain-candidate-0070#chunk-0 (高炉传感器) | **noisy** | top-2/3 completely unrelated to GPS parking patent — lexical noise | **yes** — good stress test |
| 5 | domain-candidate-0015 | 4389 | domain-candidate-0015#chunk-0 (SELF) | domain-candidate-0010#chunk-0 (穿戴式无人机控制) | domain-candidate-0038#chunk-0 (无人飞行器组件) | **partial** | top-2 UAV control (good!), top-3 drone components (good!) — semantic match | **yes** |
| 6 | domain-candidate-0034 | 4048 | domain-candidate-0034#chunk-0 (SELF) | domain-candidate-0037#chunk-0 (立体成像系统) | domain-candidate-0300#chunk-0 (B-52瞄准吊舱) | **partial** | top-2 imaging system (good!), top-3 irrelevant | **yes** |
| 7 | domain-candidate-0038 | 4402 | domain-candidate-0038#chunk-0 (SELF) | domain-candidate-0010#chunk-0 (穿戴式无人机) | domain-candidate-0014#chunk-0 (AUV驻留系统) | **partial** | top-2 drone-related (good!), top-3 underwater (wrong domain) | **yes** |
| 8 | domain-candidate-0050 | 4084 | domain-candidate-0050#chunk-0 (SELF) | domain-candidate-0037#chunk-0 (立体成像) | domain-candidate-0034#chunk-0 (成像装置对焦) | **noisy** | wireless speaker patent → imaging systems, completely wrong | **yes** — worst-case test |
| 9 | domain-candidate-0054 | 4100 | domain-candidate-0054#chunk-0 (SELF) | domain-candidate-0050#chunk-0 (无线发声装置) | domain-candidate-0012#chunk-0 (AUV系统) | **noisy** | 烤火扇 → wireless speaker (both patent format), AUV (irrelevant) | **yes** |
| 10 | domain-candidate-0055 | 4388 | domain-candidate-0055#chunk-0 (SELF) | domain-candidate-0011#chunk-0 (GPS停车寻车) | domain-candidate-0062#chunk-0 (?) | **partial** | top-2 both navigation (good!), top-3 unclear | **yes** |

## Findings

### Top-1 SELF Issue (critical, fixable)

All 10 top-1 hits are the query document itself (score=1.000 lexical overlap).
This is because `domain_rag_corpus.jsonl` was deduped against `domain_test`
only, not `domain_dev`. So all 50 dev records remain in the corpus.

**Action required before final D paid run**: Exclude domain_dev records from
the RAG corpus by matching on `id`. This is a one-line filter in the config or
build script. For P3 sanity, recording this leakage explicitly is sufficient —
the relative A/B/C/D comparison remains valid since the SELF passage provides
no extra information beyond the query itself (it IS the query).

### Top-2/3 Relevance

| Rating | Count | Pattern |
|--------|-------|---------|
| Good (truly relevant) | 3 | Same subdomain: UAV→UAV control, imaging→imaging system, navigation→GPS |
| Partial (same domain, different subdomain) | 4 | Military→military, weapon→different weapon |
| Noisy (completely unrelated) | 3 | Civilian patent → military, home appliance → random |

Lexical overlap is a poor retrieval method — it matches on shared characters,
not semantic meaning. The bge_faiss_rerank pipeline (BGE-M3 dense embeddings +
bge-reranker-v2-m3 cross-encoder reranking) should significantly improve
top-2/3 relevance by matching on semantic content.

### Prompt Bloat Control

| Metric | Value |
|--------|-------|
| Max prompt chars (dry-run w/o evidence) | 5486 |
| Evidence per passage (max) | 300 chars |
| Total with 3 passages | ~6400 chars |
| Model context limit | 8192 |
| Headroom | ~1800 chars |

Safe margin. No truncation risk at 260-char chunks.

### Glossary + RAG Interaction

Glossary terms are still present in D (carried from C). Combined with RAG
passages, there's a risk of **prompt overload**: the model sees glossary terms +
RAG passages + kNN examples + task definition. The prompt structure (task →
schema → glossary → RAG → examples → query) keeps these blocks separated, but
the total cognitive load is higher than any previous config.

This should be monitored in the paid run — if D performs worse than C on some
rows, prompt overload could be a contributing factor alongside RAG passage
quality.

## Decision

```text
D(RAG) lexical preview relevance is mixed — 3/10 good top-2/3 evidence,
4/10 partial, 3/10 noisy. Lexical overlap is a weak retrieval method;
bge_faiss_rerank should substantially improve relevance.

Top-1 SELF issue: domain_dev records are still in RAG corpus (dedup only
against test). Must be fixed before paid run — exclude dev IDs from corpus.

Top-1 same-topic (non-SELF) count: N/A (top-1 is always SELF in current corpus)
Top-3 useful-context count: 3 good + 4 partial = 7/10 show some useful context
Main noise pattern: civilian patent queries pull random military evidence;
                       military queries pull different-subdomain evidence
Decision for next step: Accept. Prepare final D bge_faiss_rerank config
                       and request paid-GPU D sanity approval.
                       Pre-requisite: fix dev SELF leakage in corpus.
```

## Allowed Next Steps

- **Acceptable**: Prepare final D `bge_faiss_rerank` config with the SELF-fix,
  then request paid-GPU approval for one bounded D sanity run only.
- Do not use `domain_test`.
- Do not enter P5 or full ablation.

**Selected**: Accept. Next step is GPU-free config preparation + SELF-fix,
then human gate for paid D sanity.

## Final D Config Requirements

Before paid GPU launch, the final config must:

1. Change `rag.mode` from `lexical_preview` to `bge_faiss_rerank`
2. Add BGE-M3 embedding (CPU mode, env `CUDA_VISIBLE_DEVICES=""`)
3. Add bge-reranker-v2-m3 (CPU mode)
4. Exclude domain_dev IDs from RAG corpus at build time
5. Set `execution.authorized: true` + `human_gate: P3_D_SANITY_APPROVED`
6. GPU-hour cap: ≤0.5 hours
7. Cost cap: ≤1.35 CNY at 2.7 CNY/hour

## Follow-up Fix Completed

Implemented after this audit:

- `scripts/run_p3_extraction.py` now supports
  `rag.exclude_source_ids_path` / `rag.exclude_source_ids_paths`.
- The D dry-run config excludes `/root/autodl-tmp/data/domain_dev.jsonl`.
- The SELF-leakage spot check on the first 10 audit rows passed: top-1 evidence
  is no longer the query itself for those rows.
- Final D config template was created:
  `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml`.
- Final D config uses `rag.mode: bge_faiss_rerank`, BGE-M3, FAISS top-20,
  bge-reranker-v2-m3 top-3, and excludes dev IDs.
- Final D config remains unexecutable until the next human gate:
  `execution.authorized: false`, `human_gate: null`.

Current blocker: wait for explicit human approval before any paid-GPU D sanity
run.

---

*审计人: AI agent, 2026-07-23*
