# P3 Domain Dev50 E Verification V2 Dry-run - 2026-07-23

## Trigger

Human audit verdict was recorded in
`docs/P3_DOMAIN_DEV50_E_VERIFICATION_VERDICT_20260723.md`.

Audit result:

- `wrong_drop`: 18/20
- `correct_drop`: 1/20
- `unclear`: 1/20
- overkill rate: 90%

Root cause: the verifier treated RAG evidence as the primary judge. When the
RAG passages did not mention the candidate entity, it often answered `no` even
when the source text and gold label supported the entity.

## V2 Prompt Fix

Implemented in `scripts/run_p3_verification.py`.

Main changes:

- Source text is explicitly primary.
- RAG evidence is explicitly secondary context.
- Entity type definitions are injected into every verifier prompt.
- The verifier is told to answer `no` only when the entity is clearly absent
  from the source text or clearly violates the type definition.
- If uncertain, answer `yes` to avoid over-deletion.

Prepared configs:

- `configs/p3_domain_dev50_e_verification_k5_sanity_v2_dryrun.yaml`
- `configs/p3_domain_dev50_e_verification_k5_sanity_v2.yaml`

The non-dry-run v2 config remains unauthorized:

- `execution.authorized: false`
- `execution.human_gate: null`
- `execution.model_calls_allowed: false`

## GPU-free Verification

Remote tests:

- `python -m unittest tests.test_verification`
- Result: 6 tests OK

Remote v2 dry-run:

- query rows: 50
- atomic entity units: 332
- max prompt chars: 1722
- model calls: 0
- API called: false
- model weights loaded: false
- GPU device present: false

Artifacts:

- `/root/project/logs/p3_domain_dev50_e_verification_v2_k5_sanity_dryrun_manifest.json`
- `/root/project/logs/p3_domain_dev50_e_verification_v2_k5_sanity_dryrun_prompts.jsonl`

## Gate

Stop here. The next paid step, if approved, should be one bounded E v2 verifier
sanity on `domain_dev50` only. Do not run E-prime, P5, more seeds, or
`domain_test` before E v2 is checked.
