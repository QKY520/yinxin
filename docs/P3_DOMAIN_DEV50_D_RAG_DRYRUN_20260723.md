# P3 Domain Dev50 D(RAG) GPU-free Prep Report - 2026-07-23

## Scope

This step only prepared D(RAG) in AutoDL GPU-free mode.

No paid GPU, no vLLM call, no model inference, no `domain_test`, no P5/full
ablation was used.

## Implemented

- Added RAG selector support in `scripts/run_p3_extraction.py`.
- Prompt injection now records `rag_passages` after glossary and before
  examples, matching the fixed prompt block order.
- Dry-run manifests and execution summaries now include `rag_selection`.
- Per-query rows now include `rag_passage_ids` and `rag_passages`.
- Added unit tests for RAG prompt order and dry-run RAG metadata.
- Added dry-run config:
  `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun.yaml`.
- Added final D config template:
  `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml`.
- Added `rag.exclude_source_ids_path` support to prevent dev SELF leakage.

## Important Boundary

The current dry-run uses `rag.mode: lexical_preview` only to validate evidence
injection, logging, dev-id exclusion, and relevance-audit workflow in GPU-free
mode.

This is not the final D method. Final D execution must use the fixed project
path: BGE-M3 embeddings, FAISS inner-product top-20, and
bge-reranker-v2-m3 top-3, after a separate paid-GPU gate.

## Dry-run Command

Remote AutoDL GPU-free command:

```bash
cd /root/project
. /root/autodl-tmp/venvs/equipment-ie/bin/activate
python scripts/run_p3_extraction.py \
  --config configs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun.yaml \
  --dry-run
```

## Dry-run Result

- dataset: `domain_dev50`
- query records: 50
- support path: `/root/autodl-tmp/data/domain_support.jsonl`
- query path: `/root/autodl-tmp/data/domain_dev.jsonl`
- RAG corpus: `/root/autodl-tmp/data/domain_rag_corpus.jsonl`
- RAG corpus SHA256: `92658eeab6952eba6b160f15b43ec37e98fb37830becc449ca62376e9979368a`
- RAG corpus chunks before exclusion: 333
- excluded source IDs: 50 from `/root/autodl-tmp/data/domain_dev.jsonl`
- RAG corpus chunks after exclusion: 263
- chunk chars: 260
- overlap chars: 40
- retrieve top-k: 20
- injected top-k: 3
- example mode: `knn_replay`
- replay rows: 50
- glossary candidates: 73
- model calls: 0
- API called: false
- model weights loaded: false
- GPU device present: false
- max prompt chars: 5496

Outputs:

- prompts:
  `/root/project/logs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun_prompts.jsonl`
- prompts SHA256:
  `3af7c57a847c4be2d039145ff73bd66f1d81f96f8f3a14601ff68b08ab954944`
- manifest:
  `/root/project/logs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun_manifest.json`
- local manifest SHA256:
  `0b8b89bb5bb1984d81a26c7652b7eb38019b9c661bf52bdb44bfec0e513df70e`

SELF-leakage spot check after exclusion:

| query id | top-1 after exclusion |
| --- | --- |
| domain-candidate-0003 | domain-candidate-0122#chunk-0 |
| domain-candidate-0005 | domain-candidate-0340#chunk-0 |
| domain-candidate-0006 | domain-candidate-0316#chunk-0 |
| domain-candidate-0011 | domain-candidate-0064#chunk-0 |
| domain-candidate-0015 | domain-candidate-0037#chunk-0 |
| domain-candidate-0034 | domain-candidate-0037#chunk-0 |
| domain-candidate-0038 | domain-candidate-0014#chunk-0 |
| domain-candidate-0050 | domain-candidate-0037#chunk-0 |
| domain-candidate-0054 | domain-candidate-0012#chunk-0 |
| domain-candidate-0055 | domain-candidate-0062#chunk-0 |

## Verification

Remote AutoDL GPU-free unit test passed:

```bash
python -m unittest tests.test_extraction
```

Result: 13 tests OK.

## Final D Config Prepared

`configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml` is prepared with:

- `rag.mode: bge_faiss_rerank`
- BGE-M3 embedding model: `/root/autodl-tmp/models/bge-m3`
- FAISS top-20 retrieval
- bge-reranker-v2-m3 reranker: `/root/autodl-tmp/models/bge-reranker`
- top-3 evidence injection
- `exclude_source_ids_path: /root/autodl-tmp/data/domain_dev.jsonl`
- `execution.authorized: false`
- `human_gate: null`

Do not execute this config until the human explicitly approves
`P3_D_SANITY_APPROVED` and the config is updated accordingly.

## Next Gate

Human should review
`docs/P3_DOMAIN_DEV50_D_RAG_RELEVANCE_AUDIT_20260723.md`.

If relevance is acceptable, the next bounded step can be a separate request to
prepare the final `bge_faiss_rerank` D config and ask for paid-GPU approval for
one D sanity run only.
