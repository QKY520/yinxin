# P3 Domain Dev50 D(RAG) Sanity - 2026-07-23

## Scope

One bounded paid-GPU P3 D(RAG) sanity run on `domain_dev50`.

This is a dev-only, seed-42, K=5 sanity result. It is not a final paper number,
not a full ablation, and does not use `domain_test`.

Human approval:

```text
2026-07-23 human confirmed paid GPU is enabled and approved one bounded P3
D(RAG) domain_dev50 K=5 seed=42 sanity run only; no domain_test/P5/full
ablation.
```

## Config

- Config: `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml`
- Dataset: `domain_dev50`
- Model: Qwen2.5-7B via vLLM
- Examples: B kNN `example_ids` replay, K=5, seed=42
- Glossary: enabled, same 73-entry `data/domain_dict.jsonl`
- RAG: BGE-M3 + FAISS top-20 + bge-reranker-v2-m3 top-3
- RAG SELF fix: excluded `/root/autodl-tmp/data/domain_dev.jsonl` IDs
- Excluded source IDs: 50
- Raw RAG chunks: 333
- Retained RAG chunks: 263
- `domain_test`: not used

## Run Window

- vLLM startup began: about `2026-07-23 15:10:30` Asia/Shanghai
- vLLM health ready: `2026-07-23 15:11:44` Asia/Shanghai
- D run command started: `2026-07-23 15:12:16` Asia/Shanghai
- D run command ended: `2026-07-23 15:34:49` Asia/Shanghai
- vLLM stopped and GPU memory returned to 0 MiB shortly after verification.

Approximate GPU service window was about 26 minutes. At 2.7 CNY/hour, the
estimated cost is about 1.17 CNY. Platform billing remains authoritative.

## Result

| Config | P | R | F1 | TP | FP | FN | Parse failures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A fixed-random | 0.4914 | 0.5570 | 0.5221 | 171 | 177 | 136 | 0/50 |
| B kNN | 0.4767 | 0.5342 | 0.5038 | 164 | 180 | 143 | 0/50 |
| C kNN + glossary | 0.4722 | 0.5537 | 0.5097 | 170 | 190 | 137 | 0/50 |
| D kNN + glossary + RAG | 0.5211 | 0.5635 | 0.5415 | 173 | 159 | 134 | 0/50 |

D vs C:

- F1: `+0.0317`
- Precision: `+0.0489`
- Recall: `+0.0098`
- TP: `+3`
- FP: `-31`
- FN: `-3`

D vs A:

- F1: `+0.0193`
- Precision: `+0.0297`
- Recall: `+0.0065`
- TP: `+2`
- FP: `-18`
- FN: `-2`

Interpretation: D is the best P3 domain-dev sanity result so far. The gain is
mainly precision-oriented, consistent with RAG evidence reducing unsupported
extra entities. This is still a dev-only sanity signal and must be preserved as
such.

## Verification

Remote result verifier:

```bash
python scripts/verify_p3_sanity_result.py \
  --per-query results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl \
  --expected-rows 50
```

Verifier output summary:

- status: `ok`
- rows: 50
- parse failures: 0
- predicted entities: 332
- max type share: 0.5060
- type counts:
  - EQUIPMENT: 168
  - MODULE: 123
  - METRIC: 24
  - TECH_SCHEME: 17

## Artifacts

Remote:

- `/root/project/results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl`
- `/root/project/results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_summary.json`
- `/root/project/logs/p3_domain_dev50_d_rag_sanity_20260723.log`
- `/root/project/logs/p3_d_vllm_20260723.log`
- `/root/autodl-tmp/backup/p3/p3_domain_dev50_d_rag_sanity_20260723.tar.gz`

Local synced copies:

- `results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl`
- `results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_summary.json`
- `logs/p3_domain_dev50_d_rag_sanity_20260723.log`
- `logs/p3_d_vllm_20260723.log`
- `backups/P3/p3_domain_dev50_d_rag_sanity_20260723.tar.gz`

Hashes:

| Artifact | SHA256 |
| --- | --- |
| per-query JSONL | `34e4b5fb737057aede9ebef6143d50c3ea248ed441e0567f6da7660587609185` |
| summary JSON | `8d4ada69e5fd70f1d872be710b9935e8e4e986e5c985e46505dc0a5e1c361f86` |
| run log | `03d0a59448cf3e5c6398a48ea955563a148773ed276f7c47ad24b7b879c64712` |
| vLLM log | `e68ce59801b165776d488f50dc2eee081abf7c6f82be5d141e6bbd3788fd3722` |
| backup tar.gz | `f449d67638ac71bd43f0ffd7fe1dc93149ac1d52b431faf358ea540c34e3f843` |

## Next Gate

Stop here.

Recommended next step is human audit of D per-query differences against C:

- inspect rows where FP dropped sharply;
- inspect rows where D may have lost correct entities;
- confirm RAG evidence did not introduce new systematic type drift;
- then decide whether to prepare E/E-prime verification work or run a second
  dev sanity seed.

Do not enter P5 or use `domain_test` without explicit approval.
