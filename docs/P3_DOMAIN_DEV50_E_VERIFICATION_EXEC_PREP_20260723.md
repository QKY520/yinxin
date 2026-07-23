# P3 Domain Dev50 E/E-prime Verification Execution Prep - 2026-07-23

## Scope

This was a GPU-free implementation and verification-prep step only.

- No paid GPU was used.
- No vLLM/model call was made.
- `domain_test` was not read or used.
- P5/full ablation was not started.

## Implemented

- `scripts/run_p3_verification.py` now supports guarded verifier execution.
- Verifier answers are parsed as atomic `yes` / `no`; any longer or ambiguous answer is `invalid`.
- Verified outputs drop only entity units with a valid `no`.
- `yes` and `invalid` verifier outputs are kept for audit.
- Per-query output preserves both `pred_raw` and `pred_verified`.
- Verifier decisions record unit id, span/type, decision, validity, hashes, cache hit, latency, and evidence mode.
- Execution refuses to run unless all of the following are true:
  - `execution.authorized: true`
  - `execution.human_gate: P3_VERIFICATION_SANITY_APPROVED`
  - GPU device is visible

## Prepared Configs

| Config | Source Raw Predictions | Evidence Mode | Authorized |
| --- | --- | --- | --- |
| `configs/p3_domain_dev50_e_verification_k5_sanity.yaml` | D RAG run | reuse extraction RAG passages | `false` |
| `configs/p3_domain_dev50_eprime_verification_k5_sanity.yaml` | C glossary run | source text only | `false` |

Both configs are intentionally non-executable until the human approves one bounded paid-GPU verifier sanity.

## GPU-free Verification

Remote command class:

```bash
ssh autodl-paper 'cd /root/project; . /root/autodl-tmp/venvs/equipment-ie/bin/activate; ...'
```

Results:

| Check | Result |
| --- | --- |
| `python -m unittest tests.test_verification` | 4 tests OK |
| Unauthorized execution guard | refused with `config execution.authorized must be true for verifier model calls` |
| E dry-run | 50 rows, 332 atomic entity units, max prompt 1392 chars, `api_called=false` |
| E-prime dry-run | 50 rows, 360 atomic entity units, max prompt 436 chars, `api_called=false` |
| GPU mode | `GPU_FREE_MODE` |

Dry-run artifacts on AutoDL:

- `/root/project/logs/p3_domain_dev50_e_verification_k5_sanity_prompts.jsonl`
- `/root/project/logs/p3_domain_dev50_e_verification_k5_sanity_manifest.json`
- `/root/project/logs/p3_domain_dev50_eprime_verification_k5_sanity_prompts.jsonl`
- `/root/project/logs/p3_domain_dev50_eprime_verification_k5_sanity_manifest.json`

## Next Gate

Stop here. The next bounded action needs explicit human approval:

1. Run only E paid verifier sanity on `domain_dev50`, or
2. Run only E-prime paid verifier sanity on `domain_dev50`, or
3. audit the generated verifier prompts first.

Do not start both verifier runs, P5, more seeds, or any `domain_test` work without a new explicit gate.
