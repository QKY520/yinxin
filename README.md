# Few-shot Equipment-Domain Chinese NER

This repository contains a reproducible applied-paper project for low-label
Chinese equipment-domain named entity recognition. The completed paper-facing
evidence compares fixed-random and kNN demonstrations, domain-glossary
injection, and retrieval-augmented generation with a local open-source LLM.
Relation extraction and self-verification remain parts of the broader original
design, not supported contributions of the current manuscript.

## Execution Authority

- `AGENT_PLAYBOOK.md`: authoritative phase-by-phase execution contract.
- `实验实施指导文档_综合版.md`: human-facing research and implementation guide.
- `AGENTS.md`: durable repository instructions for Codex.
- `HANDOFF.md`: latest operational status, claim boundary, and next gate.
- `docs/PROJECT_ROUTE_AND_SCI_Q4_PLAN.md`: locked SCI-Q4 paper route.
- `docs/P2_DECISION_LOG.md`: historical P2 gate and decision record.

## Current Status

As of 2026-07-27, P0/P1/P2 are complete, the domain data is frozen as
support/dev/test = 30/50/170, and P3/P4 domain-dev sanity is complete. The
closed paper-facing P5 evidence contains only domain-test NER configurations
A/B/C/D at K=5 over seeds 42/43/44. Fresh two-human non-test calibration
reached exact span+type micro-F1 0.8000; this is not frozen-test formal IAA,
and TECH_SCHEME F1 is 0.153846.

The current editable manuscript is
`docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`. The supported
claim is narrow: kNN and glossary injection improve F1/recall in the frozen
domain setting, while RAG preserves near-tied F1 and improves precision with
55 fewer false-positive entity predictions than the glossary-only row. RE,
CoVe, public-benchmark generalization, K-scan robustness, statistical
significance, and full-matrix completion are not claimed.

No new experiment, paid GPU, vLLM launch, model/API call, dry-run, or
frozen-test prompt generation is authorized without a new bounded human gate.

## Layout

- `configs/`: one YAML configuration per experimental run.
- `src/equipment_ie/`: reusable data, retrieval, extraction, and evaluation code.
- `scripts/`: phase entry points and operational utilities.
- `tests/`: unit and integration tests.
- `data/`: local metadata only; corpora are stored and backed up separately.
- `results/`: paper-facing tables, summaries, and plots.
- `docs/`: the current manuscript plus historical evidence and audit records;
  filenames containing older phase/version labels may be required for
  reproducibility and are not interchangeable manuscript versions.

GPU inference and model storage belong on AutoDL. This Windows repository is
the durable source for code and lightweight artifacts; Git is the code sync and
backup channel.
