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

## Important Boundary

The current dry-run uses `rag.mode: lexical_preview` only to validate evidence
injection, logging, and relevance-audit workflow in GPU-free mode.

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
- RAG corpus chunks: 333
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
- max prompt chars: 5486

Outputs:

- prompts:
  `/root/project/logs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun_prompts.jsonl`
- prompts SHA256:
  `6104c6e4d160f3406b833c798d9dd99b1312d180d3d224ce64207d5b8d0cb5ca`
- manifest:
  `/root/project/logs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun_manifest.json`
- local manifest SHA256:
  `8e2b4aae619409cb5246ff1797435a550b60b526ebb30c85d32a2350c14e773f`

## Verification

Remote AutoDL GPU-free unit test passed:

```bash
python -m unittest tests.test_extraction
```

Result: 13 tests OK.

## Next Gate

Human should review
`docs/P3_DOMAIN_DEV50_D_RAG_RELEVANCE_AUDIT_20260723.md`.

If relevance is acceptable, the next bounded step can be a separate request to
prepare the final `bge_faiss_rerank` D config and ask for paid-GPU approval for
one D sanity run only.
