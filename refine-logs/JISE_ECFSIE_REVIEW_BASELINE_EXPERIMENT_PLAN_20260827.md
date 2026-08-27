# Reviewer Baseline Experiment Plan — 2026-08-27

Gate: `JISE_ECFSIE_REVIEW_BASELINE_EXPERIMENTS_APPROVED`

## Scope

This is a new reviewer-response experiment package. Existing A/B/C/D outputs,
frozen domain labels, CLUENER labeled-dev evaluation, and all prior claims stay
unchanged. The package evaluates NER only and does not reopen RE, CoVe, or the
closed 60-cell route.

## Claim Map

| Claim/question | Evidence block |
| --- | --- |
| Does the controlled Qwen pipeline add value beyond no evidence? | zero-shot, A, D |
| Are glossary and retrieval effects independently observable? | glossary-only, BM25-only, RAG-only |
| Is the comparison credible against a conventional low-resource model? | support-only BERT-CRF |
| Does the operating point depend on K? | A/D at K=1,5,10 |

## Fixed Protocol

- Domain: 30 support, 50 tune/dev, 170 frozen test rows.
- CLUENER: 30 support, `cluener_tune.jsonl` for tuning, 1,343 labeled official
  dev rows as the final evaluation block.
- All model variants use seeds 42/43/44 and entity-level micro P/R/F1.
- Test paths are read-only and never used for checkpoint, prompt, or threshold
  selection. A final evaluation is performed only after configuration locking.
- New outputs use a separate dated root and refuse overwrite.

## Blocks

### B1 — Reviewer baselines (MUST-RUN)

Qwen zero-shot, glossary-only, BM25-only, RAG-only, and support-only
BERT-base-Chinese + CRF on both evaluation blocks at K=5. Report all rows,
including negative or unstable outcomes. BM25-only uses top-3 sparse retrieval;
RAG-only uses the existing dense retrieval/reranker path without glossary or
demonstrations.

### B2 — K sensitivity (MUST-RUN IF B1 PASSES)

A and D at K=1 and K=10 on both blocks and all three seeds. K=5 reuses the
locked rows. No K-specific tuning is allowed.

### B3 — Statistical analysis (MUST-RUN AFTER RESULTS)

Lock the comparison families before reading new test metrics. Use passage-cluster
paired bootstrap and approximate randomization, with Holm correction. Do not use
ordinary three-seed t-tests or treat passage-by-seed observations as independent.

## Expected New Units

54 units: 24 K=5 Qwen baselines, 24 A/D K-scan units, and 6 BERT-CRF units.

## Stop Rules

- Any test-derived tuning request is rejected.
- Any missing/invalid per-query output is preserved and blocks aggregation.
- Existing result files are never overwritten.
- Paid GPU work requires a separate bounded execution step after M1 sanity.
