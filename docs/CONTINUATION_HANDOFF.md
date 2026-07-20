# Continuation Handoff

Date: 2026-07-20

This document is for a fresh conversation or a new agent after context
compression. It summarizes what must be preserved and what can be done next.

## Current user goal

The user wants the whole experiment completed to a publishable SCI Q4 level
within roughly one month and within a target budget of 400 CNY. The paper should
be drafted in Chinese first, then converted to English.

The original research route is retained:

- equipment-domain small annotated dataset;
- reproducible few-shot NER/RE pipeline;
- RAG plus glossary/schema/rule constraints plus verification to reduce
  hallucination;
- ablation evidence proving module contribution.

NER is the main task. RE is auxiliary.

## Hard execution constraints

- Never run project Python locally on Windows.
- All Python, data processing, model inference, evaluation, and training run on
  AutoDL through SSH alias `autodl-paper`.
- Use GPU-free mode for coding, downloads, preprocessing, and aggregation.
- Use paid 4090 GPU only for model inference/training.
- Do not start 400-record full P2 pass, human annotation, splitting/freezing,
  P3/P4/P5, or optional QLoRA unless the relevant gate is explicitly approved.
- Preserve all failed runs and backups.
- Keep host, port, credentials, tokens, and keys out of Git.

## Current experiment state

- P0 environment: complete.
- P1 public data: complete.
- P2 deterministic distant supervision: complete but low coverage.
- P2 schema and 10 examples: approved.
- P2 14B assisted labeling implementation: complete.
- P2 14B sanity v2/v3/v4/v5: executed and preserved as negative/failed sanity
  attempts.
- Latest successful run: `p2-llm-label-sanity-v6`, commit `dfa7bd1`.
  - Fixed 10 records.
  - 0 parse/validation failures.
  - Success gate passed.
  - 52 LLM entity suggestions and 20 relation suggestions.
  - One nested-overlap case was resolved by a deterministic review-proposal-only
    rule, logged as `LLM_OVERLAP_RESOLVED=1`; one relation referencing the
    removed entity was dropped and logged.
  - The final evaluation parser remains strict by default; only P2 LLM
    proposal generation enables this resolver.
- vLLM was stopped after v6; GPU memory returned to 0 MiB.
- Latest remote/local v6 backup:
  `p2_14b_sanity_v6_success_20260720_r2.tar.gz`
  with SHA256
  `16cc70ea99cd88a337a102683cd166461f520ca9761c0e9a2f0dff560acfaead`.
  The earlier same-name v6 tar without `_r2` was a failed 45-byte backup
  attempt and must not be treated as valid.

## Recommended next action

Do not jump automatically to the 400-record pass. The next action requires a
separate human decision. Safe options are:

1. Approve the 400-record P2 LLM proposal pass with a fixed budget cap and the
   same review-sheet-only overlap resolver.
2. First manually audit the 10-row v6 review sheet to check whether the 14B
   proposals are useful enough for human annotation.
3. Stop paid GPU work and proceed with human guideline review or other
   GPU-free preparation.

## Paper strategy

Use `docs/PROJECT_ROUTE_AND_SCI_Q4_PLAN.md` as the paper-facing route lock.

The manuscript should emphasize:

1. dataset quality and annotation reproducibility;
2. engineering simplicity and reproducible pipeline;
3. hallucination reduction as the core measurable benefit;
4. clean ablations, not cherry-picked single runs.
