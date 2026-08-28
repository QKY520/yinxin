# Reviewer Baseline B1 Parse Diagnostic Closeout

Date: 2026-08-28  
Gate: `JISE_ECFSIE_REVIEW_BASELINE_B1_PARSE_DIAGNOSTIC_APPROVED`  
Phase: `REVIEWER_BASELINE_B1_PARSE_DIAGNOSTIC`

## Scope

This bounded diagnostic tested the extraction-output contract after enabling
the OpenAI-compatible JSON response format. It used four variants
(`zero_shot`, `glossary_only`, `bm25_only`, `rag_only`), seed 42, and five
fresh rows selected from the previously prepared non-test `domain_dev10`
pilot subset. The diagnostic did not read frozen test data or any formal
evaluation split. It did not alter the strict parser: invalid spans, types,
occurrences, overlaps, and malformed structures remain failures.

## Code change

`src/equipment_ie/extraction.py` now accepts an optional
`generation.response_format` mapping and passes it through to the
OpenAI-compatible request payload. The default request is unchanged. A
regression test covers the JSON-mode payload. The new gate and phase were added
to `scripts/run_p3_extraction.py`; the gate still requires authorization,
model calls, and the exact diagnostic phase.

## Results

| Variant | F1 | P | R | TP/FP/FN | Parse failures | Time (s) |
|---|---:|---:|---:|---:|---:|---:|
| BM25-only | 0.658537 | 0.710526 | 0.613636 | 27/11/17 | 1/5 (20%) | 21.102 |
| glossary-only | 0.621622 | 0.766667 | 0.522727 | 23/7/21 | 1/5 (20%) | 13.306 |
| RAG-only | 0.711111 | 0.695652 | 0.727273 | 32/14/12 | 1/5 (20%) | 67.755 |
| zero-shot | 0.675000 | 0.750000 | 0.613636 | 27/9/17 | 1/5 (20%) | 14.042 |

All four units exited with code 0 and produced reloadable summaries and
five-line per-query logs. Relative to the earlier pilot's 40--50% domain
failure range, JSON mode reduced failures to 20% per unit. This is an
engineering diagnostic, not evidence for a paper claim; the sample is only 20
non-test rows in total and was not used for manuscript metrics.

## Gate decision

The chain is materially improved but the observed rate is exactly 20%, not
below 20%. Therefore this diagnostic does **not** automatically authorize the
complete B1 matrix. A full B1 run should require a separate exact gate and an
explicit decision on whether a 20% residual parser-failure rate is acceptable.
The residual failure must remain visible in final logs and must not be silently
dropped or converted into a quality claim.

## Artifacts and cleanup

Local mirror: `results/reviewer_baselines_20260828_parse_diagnostic/`.
It contains 4 configs, 8 result files, the diagnostic log, and a local hash
manifest (14 files total, 128,408 bytes at closeout). The remote diagnostic log
SHA256 is:

`a016d38a1b4076d7c34826b6bae57ad68639b2a77aea4b4c5417d4e41902a242`

The single vLLM and runner were stopped after completion. GPU state was
`0 MiB / 24564 MiB`. No paper source, `HANDOFF.md`, frozen data, formal
evaluation result, or existing A/B/C/D result was modified.
