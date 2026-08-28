# JISE EC-FSIE Reviewer Baseline B1 Span-Index Diagnostic Closeout

Date: 2026-08-28

Gate: `JISE_ECFSIE_REVIEW_BASELINE_B1_SPAN_INDEX_DIAGNOSTIC_APPROVED`

## Scope

- Added an opt-in `span_index` NER output protocol while preserving the existing occurrence protocol as the default.
- Used 20 fresh non-test `domain_dev` rows (rows 11--20 and 41--50); no frozen-test or formal evaluation split was read.
- Planned four diagnostic variants: BM25-only, glossary-only, RAG-only, and zero-shot.
- Required parse failure rate: at most 10% for every variant.

## Implementation and verification

- `src/equipment_ie/extraction.py` builds and strictly parses `start`/`end`/`type` entities, derives `span` from the source text, and rejects invalid offsets, types, duplicates, overlaps, and malformed JSON.
- `scripts/run_p3_extraction.py` accepts the bounded gate/phase and reads `parsing.output_mode`.
- Remote test suite passed: `28 passed`.
- The original occurrence mode and all historical results remain unchanged.

## Runtime outcome

The first alphabetically executed variant, BM25-only, completed 20 rows:

| Variant | Rows | Parse failures | Failure rate | Gate result |
| --- | ---: | ---: | ---: | --- |
| BM25-only | 20 | 19 | 95% | FAIL |

The run was stopped immediately after the first completed variant exceeded the 10% ceiling. The other three variants were not completed and no full B1 evaluation was started. A partially started glossary-only cache is preserved, but it has no completed `per_query` or summary artifact and is not a result row.

## Root cause

The model generally returned structurally valid span-index entities, for example:

```json
{"entities":[{"start":14,"end":18,"type":"MODULE"}]}
```

Because this is a NER-only task, it often omitted the unused top-level `"relations": []` field. The canonical strict parser requires exactly `entities` and `relations`, so those responses failed with `ExtractionParseError: output must contain entities and relations only`. The observed failure is therefore primarily a top-level NER envelope mismatch, not evidence that the span offsets themselves are unstable.

No failed record was removed, repaired, or relabeled after seeing its output.

## Artifacts

- Remote root: `/root/autodl-tmp/reviewer_baselines_20260828_span_index/`
- Local lightweight mirror: `results/reviewer_baselines_20260828_span_index/`
- BM25 summary SHA256: `3bfd8495b35d9d4597c1f5e96549ead77755fa375380a1cdfead2b0236696fe8`
- BM25 per-query SHA256: `a05d0456514a6b2e3ed023aa56bf7edc6944ddd08457b3e1269290a17798e4e6`
- Runner log SHA256: `d813eb79259a36be23d8c13329bcfbf04cfa0f8aa93d3f7ef74dda96d7024283`

## Machine and cost closeout

- `reviewer-b1-span-run` stopped.
- `reviewer-b1-span-vllm` stopped.
- Final GPU memory: `0 MiB / 24564 MiB`.
- Paid window was approximately eight minutes; at the last recorded 2.8 CNY/hour price, estimated cost is about 0.4 CNY. Platform billing is authoritative.

## Decision and next gate

This diagnostic gate is consumed and failed its parse-stability criterion. Do not repeat it until it happens to pass. The narrow next method decision is to define a NER-only envelope policy that deterministically supplies an empty `relations` list when the response contains only `entities`, while continuing to reject unknown top-level keys and all invalid entity units. That parser-policy change, its unit tests, and any rerun require a new exact bounded gate. No paper-facing metric or claim may be derived from this diagnostic.
