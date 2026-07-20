# Few-shot Equipment Information Extraction

This repository implements a reproducible paper project for few-shot named
entity recognition and relation extraction from public equipment-domain
documents. The experimental system combines dynamic demonstration retrieval,
domain glossary injection, retrieval-augmented generation, and atomic
self-verification to measure both extraction F1 and hallucination reduction.

## Execution Authority

- `AGENT_PLAYBOOK.md`: authoritative phase-by-phase execution contract.
- `实验实施指导文档_综合版.md`: human-facing research and implementation guide.
- `AGENTS.md`: durable repository instructions for Codex.
- `docs/PROJECT_ROUTE_AND_SCI_Q4_PLAN.md`: locked paper route, contribution list, and one-month SCI Q4 framing.
- `docs/CONTINUATION_HANDOFF.md`: compact handoff for a new conversation after context compression.
- `docs/P2_DECISION_LOG.md`: gate history and latest approval state.

## Layout

- `configs/`: one YAML configuration per experimental run.
- `src/equipment_ie/`: reusable data, retrieval, extraction, and evaluation code.
- `scripts/`: phase entry points and operational utilities.
- `tests/`: unit and integration tests.
- `data/`: local metadata only; corpora are stored and backed up separately.
- `results/`: paper-facing tables, summaries, and plots.

GPU inference and model storage belong on AutoDL. This Windows repository is
the durable source for code and lightweight artifacts; Git is the code sync and
backup channel.
