# P3 Domain Dev50 E V2 Verification Sanity - 2026-07-23

## Scope

Bounded paid-GPU sanity run only.

- Config: `configs/p3_domain_dev50_e_verification_k5_sanity_v2_approved_20260723.yaml`
- Input: D RAG raw predictions on `domain_dev50`
- Model: Qwen2.5-7B via vLLM
- Verification units: entity units only
- Evidence: source-first verifier prompt, D RAG passages as secondary context
- Exclusions: no E-prime run, no P5, no more seeds, no `domain_test`

## Run Record

- Remote HEAD at launch: `62a4242`
- vLLM ready: 2026-07-23 20:41:50 Asia/Shanghai
- Verifier execution: 2026-07-23 20:42:03 to 20:42:27 Asia/Shanghai
- vLLM stopped after execution; GPU memory returned to 0 MiB / 24564 MiB.
- Approximate model-active window: about 3 minutes.
- Estimated cost at 2.7 CNY/hour: about 0.14 CNY. Platform billing is authoritative.

## Metrics

| Metric | D raw / E v2 raw | E v2 verified |
| --- | ---: | ---: |
| Precision | 0.5211 | 0.5266 |
| Recall | 0.5635 | 0.5472 |
| F1 | 0.5415 | 0.5367 |
| TP / FP / FN | 173 / 159 / 134 | 168 / 151 / 139 |
| Entity hallucination rate | 0.4789 | 0.4734 |

Verifier decisions:

| Decision | Count |
| --- | ---: |
| yes | 319 |
| no | 13 |
| invalid | 0 |

Dropped-unit diagnostics:

| Item | Value |
| --- | ---: |
| Dropped units | 13 |
| Dropped exact gold matches | 5 |
| Dropped exact-gold-match rate | 0.3846 |

Type drop counts:

| Type | Dropped |
| --- | ---: |
| EQUIPMENT | 10 |
| MODULE | 3 |

## Backup

- Remote:
  `/root/autodl-tmp/backup/p3/p3_domain_dev50_e_v2_verification_sanity_20260723.tar.gz`
- Local:
  `D:\yinsir\backups\P3\p3_domain_dev50_e_v2_verification_sanity_20260723.tar.gz`
- SHA256:
  `68514392464b742586327223e476dfa9bc3e38b45905d9c33634980de92e742c`

## Conclusion

E v2 fixed the catastrophic overkill seen in E v1: dropped units fell from 170
to 13 and invalid outputs stayed at 0.

However, E v2 is still not a positive result. It slightly reduces FP and the
entity hallucination rate, but also drops 5 gold entities and lowers F1 from
0.5415 to 0.5367. The gain in hallucination rate is only about 0.56 percentage
points, which is not enough to justify the recall loss.

Current best domain-dev sanity remains D(RAG). Preserve E v1 and E v2 as
negative/mixed verification evidence. Do not run E-prime or P5 from this
verifier wording.

## Next Gate

Recommended next decision:

1. Stop paid verifier work and keep D as the current positive result, or
2. perform GPU-free redesign of verification into a stricter candidate-only
   rule/audit stage before any more paid verifier runs.

Do not use `domain_test`.
