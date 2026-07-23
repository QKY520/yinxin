# P3 Domain Dev50 E Verification V3 Dry-run - 2026-07-23

## Trigger

The human E v2 dropped-unit audit was recorded in
`docs/P3_DOMAIN_DEV50_E_V2_VERIFICATION_VERDICT_20260723.md`.

Audit result:

- `wrong_drop`: 7/13
- `correct_drop`: 5/13
- `unclear`: 1/13

Decision from audit: E v2 improved over E v1 but still overkills valid entities.
D(RAG) remains the current best domain-dev sanity result. Further paid verifier
runs are not recommended without a new rationale.

## V3 Prompt Prep

Implemented a candidate-preserving verifier prompt version in
`scripts/run_p3_verification.py`:

- `rag_primary_v1` preserves the original E v1 prompt path for reproducibility.
- `source_first_type_defined_conservative_keep_v2` preserves the E v2 prompt.
- `source_first_type_defined_candidate_preserve_v3` is the new GPU-free prep.

V3 changes:

- If the candidate span can be located in the source text and the type is not
  obviously wrong, answer `yes`.
- RAG absence cannot justify `no`.
- Military formation/group entities such as strike groups, battle groups, and
  action groups are protected when the source describes them as equipment-domain
  targets or objects.
- Basic components, payloads, and carried weapons such as shell parts, engines,
  antennas, sensors, and torpedoes are protected when source-located.
- Locations, countries, military organizations, and institutions mislabeled as
  `EQUIPMENT` still receive `no`.

Prepared configs:

- `configs/p3_domain_dev50_e_verification_k5_sanity_v3_dryrun.yaml`
- `configs/p3_domain_dev50_e_verification_k5_sanity_v3.yaml`

The non-dry-run v3 config remains unauthorized:

- `execution.authorized: false`
- `execution.model_calls_allowed: false`
- `execution.human_gate: null`

## GPU-free Verification

Remote tests:

- `python -m unittest tests.test_verification`
- Result: 7 tests OK

Remote v3 dry-run:

- query rows: 50
- atomic entity units: 332
- max prompt chars: 1921
- model calls: 0
- API called: false
- model weights loaded: false
- GPU device present: false
- prompt version:
  `source_first_type_defined_candidate_preserve_v3`

Artifacts:

- `/root/project/logs/p3_domain_dev50_e_verification_v3_k5_sanity_dryrun_manifest.json`
- `/root/project/logs/p3_domain_dev50_e_verification_v3_k5_sanity_dryrun_prompts.jsonl`

## Gate

Stop here. Do not run paid E v3, E-prime, P5, more seeds, or `domain_test`
unless the human explicitly overrides the current recommendation.

Current recommendation: preserve D(RAG) as the positive result and treat
verification as a negative/mixed branch for now.
