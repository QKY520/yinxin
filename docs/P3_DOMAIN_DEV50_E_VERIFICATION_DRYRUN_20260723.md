# P3 E/E-prime Verification GPU-free Prep - 2026-07-23

## Scope

This step only prepared self-verification prompts for E and E-prime.

No verifier model was called. No vLLM call was made. No `domain_test` or P5
artifact was touched. The AutoDL instance still reported a visible GPU because
the human had opened paid mode earlier, but the verification dry-run made
`0` model/API calls.

## Motivation

The D(RAG) audit accepted D as a positive result:

- D vs C: F1 improved from `0.5097` to `0.5415`;
- FP decreased from `190` to `159`;
- audit conclusion: D is `acceptable positive`;
- next approved step: prepare E/E-prime verification configs in GPU-free mode.

## Implemented

- Added `scripts/run_p3_verification.py`.
- Added `tests/test_verification.py`.
- Added E dry-run config:
  `configs/p3_domain_dev50_e_verification_k5_sanity_dryrun.yaml`.
- Added E-prime dry-run config:
  `configs/p3_domain_dev50_eprime_verification_k5_sanity_dryrun.yaml`.

Current dry-run prepares entity-level yes/no verification prompts only.

## E Config

E verifies D raw predictions:

- input:
  `/root/project/results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl`
- source extraction: D = kNN + glossary + RAG
- evidence mode: `use_extraction_rag_passages`
- evidence passages per prompt: up to 3
- atomic units: 332 entity prompts
- max prompt chars: 1392
- model calls: 0
- API called: false
- dry-run prompts SHA256:
  `6aefc6b394f53acedceaea33a3bd0e7f91f698a325f1538a464478df8bf28d2b`
- manifest SHA256:
  `f9c8796ecf9c311028d1826e11ba9f8c37cd6a1334500494907fe71efaf8cbce`

## E-prime Config

E-prime verifies C raw predictions:

- input:
  `/root/project/results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl`
- source extraction: C = kNN + glossary, no RAG
- evidence mode: `source_text_only`
- external evidence passages: 0
- atomic units: 360 entity prompts
- max prompt chars: 436
- model calls: 0
- API called: false
- dry-run prompts SHA256:
  `10051aa260a8b55ae711a9f99fccae22306065d2f50d60f3657115d22ee29339`
- manifest SHA256:
  `5cbd244f7ce0aa6f5458917628880347301773f8475d5ad0c52a77387c63daa5`

## Verification

Remote command:

```bash
python -m unittest tests.test_verification
```

Result: 2 tests OK.

Remote dry-runs:

```bash
python scripts/run_p3_verification.py \
  --config configs/p3_domain_dev50_e_verification_k5_sanity_dryrun.yaml \
  --dry-run

python scripts/run_p3_verification.py \
  --config configs/p3_domain_dev50_eprime_verification_k5_sanity_dryrun.yaml \
  --dry-run
```

Both dry-runs completed successfully.

## Current Limitations

- Only entity verification prompt generation is implemented.
- Verifier execution and dropping logic are not implemented yet.
- Invalid verifier output policy is recorded in config but not executed.
- Relation verification is intentionally deferred; NER is the main evidence
  line.

## Next Gate

Stop here.

Before any paid verifier run, the next bounded step should be to implement
verifier execution and raw/verified output assembly, still on dev only, then
ask for explicit paid-GPU approval.

The human should switch the AutoDL instance back to no-card mode or shut it down
to stop billing.
