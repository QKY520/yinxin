# P3 Domain Dev50 C Glossary Dry-Run Report - 2026-07-23

## Scope

- Phase: P3 domain-dev sanity preparation.
- Config: C = B kNN examples + domain glossary injection.
- Dataset: `domain_dev50` only.
- Execution mode: GPU-free dry-run only.
- Exclusions: no model calls, no vLLM, no paid GPU, no `domain_test`, no P4, no P5, no full ablation grid.

## Implementation

- Added query-matched glossary selection in `src/equipment_ie/extraction.py`.
- Added glossary loading and per-query `glossary_terms` logging in `scripts/run_p3_extraction.py`.
- Added seed glossary `data/domain_dict.jsonl`.
- Added C configs:
  - `configs/p3_domain_dev50_c_glossary_k5_sanity_sanitize_dryrun.yaml`
  - `configs/p3_domain_dev50_c_glossary_k5_sanity_sanitize.yaml`
- Added runner-level tests for glossary prompt order, substring matching, and kNN replay.

## kNN Replay Decision

The current GPU-free AutoDL instance has a cgroup memory limit of
`2147483648` bytes. Loading BGE-M3 on CPU for the C dry-run was killed by the
system before any prompt file could be written.

To keep C-B as a clean glossary-only comparison while avoiding the 2 GB no-card
memory limit, C uses `examples.mode: knn_replay` and replays the exact
`example_ids` recorded by the completed B run:

`/root/project/results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_per_query.jsonl`

This preserves the B kNN demonstration choices and avoids recomputing
embeddings during C preparation and C execution.

## GPU-Free Verification

Remote tests:

```text
python -m unittest tests.test_extraction tests.test_schema tests.test_llm_labeling tests.test_public_data tests.test_domain_data
57 tests OK
```

C dry-run:

```text
python scripts/run_p3_extraction.py \
  --config configs/p3_domain_dev50_c_glossary_k5_sanity_sanitize_dryrun.yaml \
  --dry-run
```

Result:

- query records: 50
- model calls: 0
- API called: false
- model weights loaded: false
- GPU device present: false
- max prompt chars: 4517
- kNN replay rows: 50
- glossary candidates: 73
- glossary max entries per query: 20
- glossary-covered rows: 45/50 = 90.0%
- glossary terms per row: min 0, max 7, average 2.78

Hashes:

- dry-run config: `7f6dd113dc6291578df00aab6c81583d18766419c8a078ea890cc6a3db1535b0`
- domain glossary: `01b857822894bb09268cbb7fb14ad0988630137bb7efae0b9d90f7d75a2f3ef6`
- dry-run manifest: `77d245f0c9e24b08ed73f097b1c089dd61a45ac0470ec92c0b0077a0dd0478f3`
- dry-run prompts: `b76bba01447c19f49e85f7df4a42695e96ec37ff5f32597a7771ddf6e0c034d8`

## Next Gate

Next approved step should be one bounded paid-GPU run only:

`P3 C domain_dev50 K=5 seed=42 sanity with proposal-stage sanitization`

Before running, edit the execution config to set `authorized=true`,
`human_gate=P3_DOMAIN_SANITY_APPROVED`, and `model_calls_allowed=true` after
explicit human approval. Do not enter P4/P5 or evaluate `domain_test`.
