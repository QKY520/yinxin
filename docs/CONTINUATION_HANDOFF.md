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
- P2 14B sanity v2/v3/v4: executed and preserved as negative/failed sanity
  attempts.
- Latest v4 result: 10 fixed records, 3 invalid outputs.
  - JSON trailing-format failures were fixed.
  - Remaining failures are relation type-matrix violations and overlapping
    entity violations.
- vLLM was stopped after v4; GPU memory returned to 0 MiB.
- Latest known remote/local v4 backup:
  `p2_14b_sanity_v4_attempt_20260720.tar.gz`
  with SHA256
  `5953d1d8047ac28fcfe514611b1ea528053dd1ae47cfa9ba12c06919c51ea51c`.

## Recommended next action

Do not jump to the 400-record pass.

The next safe experimental step is a bounded v5-style 10-record sanity retry:

1. Diagnose the 3 v4 invalid outputs from raw logs.
2. Tighten prompt/schema post-processing only for:
   - relation type matrix;
   - overlap rejection;
   - no unsupported relation directions.
3. Keep the same fixed 10 sanity records.
4. Run only the 10-record sanity retry on 4090.
5. Success gate: 0 parse/validation failures out of 10.
6. Stop, back up, hash-verify, report time/cost.

Only after sanity passes should a separate decision be made about the 400-record
P2 full pass.

## Paper strategy

Use `docs/PROJECT_ROUTE_AND_SCI_Q4_PLAN.md` as the paper-facing route lock.

The manuscript should emphasize:

1. dataset quality and annotation reproducibility;
2. engineering simplicity and reproducible pipeline;
3. hallucination reduction as the core measurable benefit;
4. clean ablations, not cherry-picked single runs.

