# P3 Domain Dev50 E Verification Sanity - 2026-07-23

## Scope

Bounded paid-GPU sanity run only.

- Config: `configs/p3_domain_dev50_e_verification_k5_sanity_approved_20260723.yaml`
- Input: D RAG raw predictions on `domain_dev50`
- Model: Qwen2.5-7B via vLLM
- Verification units: entity units only
- Evidence: D query-level RAG passages
- Exclusions: no E-prime run, no P5, no more seeds, no `domain_test`

## Run Record

- Remote HEAD at launch: `cda2952`
- Post-run summarizer HEAD: `633262e`
- vLLM ready: 2026-07-23 17:40:04 Asia/Shanghai
- Verifier execution: 2026-07-23 17:40:25 to 17:40:53 Asia/Shanghai
- vLLM stopped after execution; GPU memory returned to 0 MiB / 24564 MiB.
- Approximate model-active window: about 3 minutes.
- Estimated cost at 2.7 CNY/hour: about 0.14 CNY. Platform billing is authoritative.

## Output Artifacts

- Per-query:
  `results/p3/p3_domain_dev50_e_verification_k5_sanity_approved_20260723_per_query.jsonl`
- Execution summary:
  `results/p3/p3_domain_dev50_e_verification_k5_sanity_approved_20260723_summary.json`
- Evaluation summary:
  `results/p3/p3_domain_dev50_e_verification_k5_sanity_approved_20260723_eval_summary.json`
- Dropped-unit audit sheet:
  `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DROPPED_AUDIT_20260723.md`
- Remote/local backup:
  `backups/P3/p3_domain_dev50_e_verification_sanity_20260723.tar.gz`
- Backup SHA256:
  `8fccbaa14bb95d4de3da45beb638367ecd6baa5bb0490a2fa31b4a62411c6320`

## Metrics

| Metric | D raw / E raw | E verified |
| --- | ---: | ---: |
| Precision | 0.5211 | 0.6173 |
| Recall | 0.5635 | 0.3257 |
| F1 | 0.5415 | 0.4264 |
| TP / FP / FN | 173 / 159 / 134 | 100 / 62 / 207 |
| Entity hallucination rate | 0.4789 | 0.3827 |

Verifier decisions:

| Decision | Count |
| --- | ---: |
| yes | 162 |
| no | 170 |
| invalid | 0 |

Dropped-unit diagnostics:

| Item | Value |
| --- | ---: |
| Dropped units | 170 |
| Dropped exact gold matches | 73 |
| Dropped exact-gold-match rate | 0.4294 |

Type drop counts:

| Type | Dropped |
| --- | ---: |
| EQUIPMENT | 71 |
| MODULE | 73 |
| METRIC | 17 |
| TECH_SCHEME | 9 |

## Conclusion

E is a negative sanity result in its current wording. Verification reduced FP
and raised precision, but the recall loss is too large: 73 exact gold entities
were dropped, and F1 fell from D's 0.5415 to 0.4264.

This indicates the current verifier prompt is over-conservative rather than
paper-ready. Preserve the result as evidence, but do not run E-prime, P5, more
seeds, or `domain_test` with this verifier wording.

## Next Gate

Recommended next step: human-audit the 20 sampled dropped entities in
`docs/P3_DOMAIN_DEV50_E_VERIFICATION_DROPPED_AUDIT_20260723.md`, then revise the
verification prompt to require source-text support first and use RAG only as
secondary context. After that, run another bounded E sanity only.
