# P5 M0 Draft Audit - 2026-07-24

## Scope

This audit covers the GPU-free P5 M0 artifacts only:

- `docs/P5_RUN_MANIFEST_20260724.md`
- `configs/p5_domain_test_a_k5_seed42_draft.yaml`
- `configs/p5_domain_test_b_knn_k5_seed42_draft.yaml`
- `configs/p5_domain_test_c_glossary_k5_seed42_draft.yaml`
- `configs/p5_domain_test_d_rag_k5_seed42_draft.yaml`

No paid GPU execution, vLLM startup, model call, dry-run, prompt generation, or
config modification is authorized by this audit.

## Human Verdict

The human audit passed. The audit confirmed:

1. The A/B/C/D ablation differences are clean.
2. C and D replay B for the same dataset, K, and seed.
3. D excludes `domain_test` IDs from RAG retrieval to avoid test SELF leakage.
4. All four draft configs remain blocked with `authorized: false`.

## Frozen Draft State

The draft state should be preserved:

- Keep the four config files as draft configs.
- Keep `execution.authorized: false`.
- Keep `model_calls_allowed: false`.
- Do not run domain-test dry-runs before a paid gate, because dry-run reads test
  records and writes prompts.
- Do not modify prompt, glossary, RAG, verifier, threshold, or experimental
  parameters using `domain_test`.

## Current Gate

P5 M0 is complete. The next possible experimental step remains blocked until
the human explicitly approves a bounded paid GPU gate. The expected wording for
that future gate is still:

```text
Approve paid GPU P5 domain pilot: run A/B/C/D on domain_test, K=5, seed=42,
using the frozen draft configs after changing only execution authorization
metadata. No prompt/glossary/RAG/verifier tuning is authorized.
```

Until such approval is given, stop after documentation and synchronization.
