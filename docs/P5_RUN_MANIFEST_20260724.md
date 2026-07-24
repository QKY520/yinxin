# P5 Run Manifest - 2026-07-24

## Scope

This manifest covers the next bounded P5 step only: domain-test pilot config
drafts for A/B/C/D at K=5, seed 42. It is part of GPU-free M0 preparation. It
does not authorize paid GPU execution, vLLM startup, model calls, E/E-prime, or
any verifier experiment.

## Prepared Draft Configs

| Run order | Config | Purpose | Depends on |
| --- | --- | --- | --- |
| 1 | `configs/p5_domain_test_a_k5_seed42_draft.yaml` | A baseline: fixed random examples, no glossary, no RAG | none |
| 2 | `configs/p5_domain_test_b_knn_k5_seed42_draft.yaml` | B: kNN examples only | none |
| 3 | `configs/p5_domain_test_c_glossary_k5_seed42_draft.yaml` | C: B replay plus glossary | B per-query output |
| 4 | `configs/p5_domain_test_d_rag_k5_seed42_draft.yaml` | D: C plus RAG | B per-query output |

All four configs remain `execution.authorized: false` and
`model_calls_allowed: false`. They are not runnable for paid execution until a
new human gate updates approval status. Runner support for
`P5_DOMAIN_PILOT_APPROVED` has already been patched and tested.

## Frozen Design Choices

- Dataset: `domain_test`.
- Support pool: `/root/autodl-tmp/data/domain_support.jsonl`.
- Query file: `/root/autodl-tmp/data/domain_test.jsonl`.
- K: 5.
- Seed: 42.
- Model: `/root/autodl-tmp/models/qwen2.5-7b`.
- Cache: `/root/project/cache/p5_extraction`.
- Output root: `/root/project/results/p5`.
- RAG corpus: `/root/autodl-tmp/data/domain_rag_corpus.jsonl`.
- RAG leakage guard: D excludes IDs from `/root/autodl-tmp/data/domain_test.jsonl`.
- Verification: excluded.
- E/E-prime: excluded.

## Important Non-Execution Rule

Do not dry-run these domain-test configs before the paid P5 gate. The extraction
dry-run path reads query records and writes prompts. For the frozen test split,
that is unnecessary before approval and could create avoidable leakage risk.
Allowed GPU-free checks are limited to YAML parsing, path spelling review,
field consistency review, Git sync, and remote repository status checks.

## Required Human Approval For Next Step

The next paid gate, if approved, should be stated explicitly as:

```text
Approve paid GPU P5 domain pilot: run A/B/C/D on domain_test, K=5, seed=42,
using the frozen draft configs after changing only execution authorization
metadata. No prompt/glossary/RAG/verifier tuning is authorized.
```

Without that exact kind of approval, the agent must stop after this manifest.

## Agent Actions After Future Approval

After a future paid approval, the agent should:

1. Check remote status and pull the latest commit on AutoDL.
2. Verify paid GPU mode with `nvidia-smi`.
3. Start vLLM for Qwen2.5-7B only.
4. Update or copy the four draft configs to approved configs with unchanged
   experimental parameters and explicit approval metadata.
5. Run B before C/D, because C and D replay B's example IDs.
6. Run A, B, C, D once each; do not change configs after seeing results.
7. Stop vLLM, verify GPU memory returns to 0 MiB, back up, sync lightweight
   outputs, report cost, and wait.

## Known Implementation Check

The current extraction runner was built during P3 and enforces P3 human-gate
names for non-dry execution. The runner has now been patched to accept the
P5-specific approval gate `P5_DOMAIN_PILOT_APPROVED` as well. That patch must
not alter prompt semantics, retrieval logic, parsing semantics, or metric
computation.

## Review Checklist

- [ ] A/B/C/D differ only by the intended ablation switches.
- [ ] C and D replay B for the same dataset/K/seed.
- [ ] D excludes `domain_test` IDs from RAG retrieval.
- [ ] No verifier config is included.
- [ ] No dry-run or prompt generation has been performed on `domain_test`.
- [ ] Paid GPU execution is still blocked by `authorized: false`.
