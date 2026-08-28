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
- `docs/JISE_ECFSIE_COMPRESSION_OVERLEAF_FINAL_TECHNICAL_CLOSEOUT_20260811.md`:
  final paper/source hashes, audits, pause state, and review restart protocol.
- `docs/PROJECT_ROUTE_AND_SCI_Q4_PLAN.md`: locked SCI-Q4 paper route.
- `docs/P2_DECISION_LOG.md`: historical P2 gate and decision record.

## Current Status

As of 2026-08-28, P0--P6, full-IE F1--F6, F7 Domain Batch 1, the focused
12-cell CLUENER block, both result-to-claim reviews, validation, backup, and
machine closeout are complete. Literal accounting is `16/60`; the other 44
identities are route-closed. Fresh two-human non-test calibration reached exact
span+type micro-F1 0.8000; this is not frozen-test formal IAA, and TECH_SCHEME
F1 is 0.153846.

The sole active manuscript is the LaTeX project at
`docs/JISE_OVERLEAF_LATEX_20260729/`. Its compressed main has passed a 12-page
Overleaf technical and visual audit, and its independent supplement has passed
a two-page audit. The human accepts the 12-page main. The supported claim is
narrow: kNN and glossary injection improve observed F1/recall in the frozen
domain setting, while RAG preserves near-tied F1 and improves precision with 55
fewer mean false-positive entity predictions than the glossary-only row.
CLUENER supplies one limited directional replication. RE, CoVe, broad public/
cross-domain generalization, K robustness, significance, SOTA, and full-matrix
completion are not claimed.

No gate is live. The project is paused until the human returns with reviewer
feedback. Do not launch an experiment, paid GPU, vLLM, model/API call, dry-run,
frozen-test prompt generation, paper edit, submission action, or GitHub sync
without a new exact bounded human gate. Human metadata remains unresolved and
must never be invented.

The latest reviewer-baseline diagnostic used 20 fresh non-test `domain_dev`
rows with an opt-in span-index output protocol. BM25-only completed with 19/20
parse failures (`95%`), caused by valid NER JSON omitting the unused top-level
`relations` list. The run was stopped, the other variants were not completed,
and the failure evidence is preserved. A NER-only envelope repair is only a
proposal; it requires a new exact gate before code changes or model calls.

On 2026-08-28 the human explicitly authorized GitHub synchronization for this
bounded handoff. Only the related documentation/code commits are eligible for
push; unrelated dirty files, data, paper sources, and attachments remain
excluded.

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
