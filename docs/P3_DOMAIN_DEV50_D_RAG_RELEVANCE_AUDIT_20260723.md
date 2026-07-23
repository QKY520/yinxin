# P3 Domain Dev50 D(RAG) Relevance Audit - 2026-07-23

## Purpose

Audit whether D(RAG) evidence injection is directionally useful before any paid
GPU D run.

This audit is based on the GPU-free `lexical_preview` dry-run. It checks the
RAG corpus, prompt injection, and manual relevance workflow only. It is not a
final measurement of BGE-M3 + FAISS + bge-reranker-v2-m3 quality.

Source prompts:

`logs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun_prompts.jsonl`

## Audit Questions

For each sampled query:

1. Is top-1 evidence about the same equipment/object/topic as the query?
2. Are top-2/top-3 useful context or mostly noise?
3. Does evidence contain source text that could constrain false entities?
4. Is evidence likely to reduce glossary-induced type drift, or does it add
   unrelated terms?
5. Should this query be included in the paid D sanity audit sample?

## Sample Table

| # | query id | prompt chars | top-1 evidence id | top-2 evidence id | top-3 evidence id | relevance | issue | keep for paid D audit? |
| ---: | --- | ---: | --- | --- | --- | --- | --- | --- |
| 1 | domain-candidate-0003 | 4760 | domain-candidate-0003#chunk-0 | domain-candidate-0122#chunk-0 | domain-candidate-0333#chunk-0 | same / partial / noisy |  | yes / no |
| 2 | domain-candidate-0005 | 4398 | domain-candidate-0005#chunk-0 | domain-candidate-0340#chunk-0 | domain-candidate-0289#chunk-0 | same / partial / noisy |  | yes / no |
| 3 | domain-candidate-0006 | 5155 | domain-candidate-0006#chunk-0 | domain-candidate-0006#chunk-1 | domain-candidate-0316#chunk-0 | same / partial / noisy |  | yes / no |
| 4 | domain-candidate-0011 | 4488 | domain-candidate-0011#chunk-0 | domain-candidate-0064#chunk-0 | domain-candidate-0055#chunk-0 | same / partial / noisy |  | yes / no |
| 5 | domain-candidate-0015 | 4389 | domain-candidate-0015#chunk-0 | domain-candidate-0015#chunk-1 | domain-candidate-0038#chunk-0 | same / partial / noisy |  | yes / no |
| 6 | domain-candidate-0034 | 4048 | domain-candidate-0034#chunk-0 | domain-candidate-0037#chunk-0 | domain-candidate-0015#chunk-0 | same / partial / noisy |  | yes / no |
| 7 | domain-candidate-0038 | 4402 | domain-candidate-0038#chunk-0 | domain-candidate-0038#chunk-1 | domain-candidate-0014#chunk-0 | same / partial / noisy |  | yes / no |
| 8 | domain-candidate-0050 | 4084 | domain-candidate-0050#chunk-0 | domain-candidate-0037#chunk-0 | domain-candidate-0034#chunk-0 | same / partial / noisy |  | yes / no |
| 9 | domain-candidate-0054 | 4100 | domain-candidate-0054#chunk-0 | domain-candidate-0054#chunk-1 | domain-candidate-0012#chunk-0 | same / partial / noisy |  | yes / no |
| 10 | domain-candidate-0055 | 4388 | domain-candidate-0055#chunk-0 | domain-candidate-0055#chunk-1 | domain-candidate-0062#chunk-0 | same / partial / noisy |  | yes / no |

## Decision

Fill after manual review:

```text
D(RAG) lexical preview relevance is acceptable / mixed / harmful.
Top-1 same-topic count:
Top-3 useful-context count:
Main noise pattern:
Decision for next step:
```

## Allowed Next Steps

- If acceptable: prepare final D `bge_faiss_rerank` config and request paid-GPU
  approval for one bounded D sanity run only.
- If mixed: adjust RAG preview/audit criteria or inspect more dev-only rows;
  do not use `domain_test`.
- If harmful: stop before paid D and diagnose corpus/chunking/retrieval noise.
