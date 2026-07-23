# P3 Domain Dev50 C Glossary Sanity Report - 2026-07-23

## Scope

- Phase: P3 domain-dev sanity.
- Config: C = B kNN example choices replayed + glossary injection.
- Dataset: `domain_dev50` only.
- K/seed: K=5, seed=42.
- Model: `/root/autodl-tmp/models/qwen2.5-7b` served by vLLM.
- Sanitization: proposal-stage invalid-unit dropping, same policy as A/B.
- Exclusions: no `domain_test`, no P4, no P5, no full ablation grid.

## Result

| Metric | Value |
| --- | ---: |
| Query rows | 50 |
| Parse failures | 0/50 = 0.0% |
| Entity precision | 0.4722 |
| Entity recall | 0.5537 |
| Entity F1 | 0.5097 |
| TP / FP / FN | 170 / 190 / 137 |
| Sanitized unit events | 27 |
| Predicted entities | 360 |
| Max type share | 0.4972 |

Type counts:

| Type | Count |
| --- | ---: |
| EQUIPMENT | 179 |
| MODULE | 133 |
| METRIC | 31 |
| TECH_SCHEME | 17 |

Sanitization flags:

| Flag | Count |
| --- | ---: |
| `ENTITY_DROPPED_INVALID_UNIT` | 20 |
| `ENTITY_DROPPED_OVERLAP` | 7 |

Glossary coverage:

| Item | Value |
| --- | ---: |
| Glossary candidates | 73 |
| Rows with matched terms | 45/50 = 90.0% |
| Avg terms per row | 2.78 |
| Min / max terms per row | 0 / 7 |

## Comparison

| Config | P | R | F1 | Parse failures |
| --- | ---: | ---: | ---: | ---: |
| A fixed-random | 0.4914 | 0.5570 | 0.5221 | 0/50 |
| B kNN | 0.4767 | 0.5342 | 0.5038 | 0/50 |
| C kNN + glossary | 0.4722 | 0.5537 | 0.5097 | 0/50 |

Interpretation:

- C improves over B by about +0.0059 F1, mainly by recovering recall.
- C remains below A by about -0.0124 F1.
- The glossary did not cause parse instability or type collapse.
- This is a mixed result: glossary partially mitigates B's kNN degradation but
  does not yet beat the fixed-random baseline on `domain_dev50`.

## Verification

Command:

```text
python scripts/verify_p3_sanity_result.py \
  --per-query results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl \
  --expected-rows 50
```

Verifier result:

```json
{"status":"ok","rows":50,"parse_failures":0,"pred_entities":360,"max_type_share":0.49722222222222223,"type_counts":{"EQUIPMENT":179,"METRIC":31,"MODULE":133,"TECH_SCHEME":17}}
```

Hashes:

- Config: `32b96b11a61a939da5eb6cdeb39c57f06a27bb088c2210af4c759198893c68e6`
- Glossary: `01b857822894bb09268cbb7fb14ad0988630137bb7efae0b9d90f7d75a2f3ef6`
- Summary: `d54c1744ec05e02b7583ba646f7a456e3592201fe65babf840a5e5bda68e4232`
- Per-query: `9e190c12ff48ee50e3c1c79739ca40b3ed199fb4201a920c8dfa24f6475f6a7c`
- vLLM log: `096e70f74dafeb1dbacb1b21ac6b8002e238afe85ad76730cca0ea285f251f7c`

Backup:

- Remote archive:
  `/root/autodl-tmp/backup/p3/p3_domain_dev50_c_glossary_sanity_sanitize_20260723.tar.gz`
- Local archive:
  `D:\yinsir\backups\P3\p3_domain_dev50_c_glossary_sanity_sanitize_20260723.tar.gz`
- Remote/local SHA256:
  `84febe390bf5690b80e06049dd48c9d92de5e478c7e5a914dab333a707531e58`

## Cost And Cleanup

- GPU: NVIDIA GeForce RTX 4090.
- GPU memory before vLLM: 0 MiB / 24564 MiB.
- vLLM was stopped after the run.
- GPU memory after cleanup: 0 MiB / 24564 MiB.
- Approximate agent-managed paid-GPU window: 09:17-09:23 Asia/Shanghai on
  2026-07-23.
- Estimated cost at 2.7 CNY/hour: about 0.27 CNY.
- AutoDL platform billing remains authoritative.

## Next Gate

Stop for human audit of C before any further experiment.

Suggested audit focus:

- Whether matched `glossary_terms` are relevant per query.
- Whether C reduced EQUIPMENT/MODULE boundary errors compared with B.
- Whether the 31 METRIC predictions are legitimate or glossary-induced
  over-labeling.
- Whether C's recall recovery is worth preserving before testing RAG.

Do not proceed to P4/P5 or `domain_test` without explicit approval.
