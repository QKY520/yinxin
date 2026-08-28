# JISE EC-FSIE Reviewer Baseline B1 Pilot Closeout

Date: 2026-08-28  
Gate: `JISE_ECFSIE_REVIEW_BASELINE_B1_PILOT_APPROVED`  
Phase: `REVIEWER_BASELINE_B1_PILOT`

## Scope

This was a chain-validation pilot for the reviewer-requested baseline runner,
not a final experiment and not a paper-result update. It covered eight seed-42
units: four variants (`zero_shot`, `glossary_only`, `bm25_only`, and
`rag_only`) on ten non-test `domain_dev` rows and ten non-test `cluener_tune`
rows. No frozen test or formal evaluation split was read. BERT-CRF and K-scan
variants were outside this gate.

The configs were independently audited for evaluation/test paths. All configs
were marked `authorized: true`, used the approved gate and phase, and wrote to
the isolated pilot output directory.

## Completion

All 8/8 units exited with code 0. Every unit produced a reloadable
`summary.json` and a ten-line `per_query.jsonl`.

| Dataset | Variant | F1 | P | R | TP/FP/FN | Parse failures | Time (s) |
|---|---|---:|---:|---:|---:|---:|---:|
| domain | zero-shot | 0.578512 | 0.700000 | 0.492958 | 35/15/36 | 4/10 (40%) | 53.872 |
| domain | glossary-only | 0.556522 | 0.727273 | 0.450704 | 32/12/39 | 5/10 (50%) | 49.021 |
| domain | BM25-only | 0.477876 | 0.642857 | 0.380282 | 27/15/44 | 5/10 (50%) | 57.706 |
| domain | RAG-only | 0.548387 | 0.641509 | 0.478873 | 34/19/37 | 5/10 (50%) | 129.895 |
| CLUENER | zero-shot | 0.000000 | 0.000000 | 0.000000 | 0/0/29 | 0/10 (0%) | 2.076 |
| CLUENER | glossary-only | 0.000000 | 0.000000 | 0.000000 | 0/0/29 | 0/10 (0%) | 2.069 |
| CLUENER | BM25-only | 0.000000 | 0.000000 | 0.000000 | 0/10/29 | 5/10 (50%) | 12.549 |
| CLUENER | RAG-only | 0.000000 | 0.000000 | 0.000000 | 0/8/29 | 8/10 (80%) | 30.076 |

The CLUENER values are pilot diagnostics on ten tune rows only. They are not
public-benchmark evidence and must not be propagated to the manuscript.

## Diagnostic findings

The main failure mode is extraction-output validation, not a process crash.
Observed parser errors include:

- entity occurrence not found because the model emitted a paraphrase or a
  differently encoded span;
- overlapping entities;
- output shape outside the required `entities`/`relations` JSON object; and
- occasional malformed JSON.

The failure rate is 40--50% on domain and reaches 80% for CLUENER RAG-only.
This is too high to authorize the full reviewer baseline matrix. The pilot
therefore validates the dispatcher, isolation, logging, and cleanup path, but
does not validate baseline quality.

RAG-only also has materially higher latency because BGE-M3 embedding and the
reranker were intentionally run on CPU to avoid competing with the Qwen vLLM
process. This is an implementation-cost observation, not a quality claim.

## Artifacts and verification

Local mirror:
`results/reviewer_baselines_20260827/b1_pilot/`

It contains 8 configs, 16 output files (8 summaries and 8 per-query logs), and
the scheduler log and a local SHA256 manifest, for 26 files and 407,583 bytes.
The remote and local pilot
log SHA256 is:

`a2f72569568854c733538ada97ae462fc7239e6c79b05de6593f9d9d221cce6b`

The eight summary/per-query SHA256 values are recorded by the local artifact
hash manifest produced during closeout. Remote output count and local mirrored
output count both equal 24 under `configs/` and `outputs/`; all per-query files
contain ten rows. The remote GPU was released after the run: `0 MiB / 24564
MiB`, and the reviewer vLLM screen was stopped. Historical dead screen entries
were not touched.

## Gate decision

**Do not proceed directly to the complete B1 baseline matrix.** A new bounded
diagnostic gate is required to repair or characterize prompt/JSON/span
validation behavior on a fresh non-test subset. Any future full B1 run needs a
separate exact approval after the diagnostic passes an explicitly stated
parse-failure criterion.

No paper source, frozen data, formal evaluation result, `HANDOFF.md`, or
existing A/B/C/D result was changed in this pilot.
