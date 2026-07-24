# P5 Domain-Test Pilot Report - 2026-07-24

## Scope

Human approval in chat on 2026-07-24: paid GPU mode was enabled and the agent
was authorized to run exactly one bounded P5 domain-test pilot:

- dataset: `domain_test`
- configs: A/B/C/D only
- K: 5
- seed: 42
- model: Qwen2.5-7B-Instruct via vLLM
- gate: `P5_DOMAIN_PILOT_APPROVED`

Only execution metadata was changed in copied approved configs. Prompt,
glossary, RAG, verifier, parser, data paths, generation settings, and output
paths were not tuned from `domain_test`.

## Execution

- Local commit with approved configs: `d522b3e`
- Remote `/root/project` fast-forwarded to `d522b3e`
- GPU: NVIDIA GeForce RTX 4090, 24 GB
- vLLM service window: approximately 12:10-14:31 Asia/Shanghai
- Estimated GPU cost at 2.7 CNY/hour: about 6.3 CNY
- Platform billing remains authoritative.
- vLLM was stopped after the pilot; GPU memory returned to 0 MiB.

## Results

Single-seed pilot only. These are not final paper mean +/- std numbers.

| Config | Precision | Recall | F1 | TP | FP | FN | Parse failures | Elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A fixed-random | 0.4752 | 0.6017 | 0.5310 | 574 | 634 | 380 | 0 | 450.578s |
| B kNN | 0.5056 | 0.6143 | 0.5547 | 586 | 573 | 368 | 0 | 627.969s |
| C kNN + glossary | 0.5117 | 0.6415 | 0.5693 | 612 | 584 | 342 | 0 | 437.815s |
| D kNN + glossary + RAG | 0.5251 | 0.6132 | 0.5658 | 585 | 529 | 369 | 0 | 6237.211s |

Key single-seed comparisons:

- `B - A`: kNN improved F1 by +0.0237 and reduced FP by 61.
- `C - B`: glossary improved F1 by +0.0146 and recall by +0.0273, but FP rose
  by 11.
- `D - C`: RAG reduced FP by 55 and improved precision by +0.0134, but reduced
  recall enough that F1 fell by -0.0035.
- Best pilot F1: C.
- Best pilot precision / lowest FP among A-D: D.

## Artifacts

Remote:

- `/root/project/results/p5/`
- `/root/project/logs/p5_domain_test_*_run.log`
- `/root/project/logs/p5_domain_test_*_run.exit`
- `/root/project/logs/p5_vllm_20260724.log`
- `/root/autodl-tmp/backup/p5/p5_domain_pilot_20260724.tar.gz`

Local synced copies:

- `D:\yinsir\results\p5\`
- `D:\yinsir\logs\p5_domain_test_*`
- `D:\yinsir\logs\p5_vllm_20260724.log`
- `D:\yinsir\backups\P5\p5_domain_pilot_20260724.tar.gz`

Backup SHA256:

```text
61b05d4c89c26b22881ea17ce36da91a84fdb83ad0d3a49aaa84317e7357d808
```

## Next Gate

Stop here. Do not run E, E-prime, more seeds, CLUENER, full P5, dry-runs, or
any additional `domain_test` evaluation without a new explicit human gate.

Recommended human decision: whether to authorize a bounded replication step for
domain A/B/C/D on seeds 43 and 44, or to revise the P5 plan based on the pilot
finding that C gives the best F1 while D reduces false positives at substantial
runtime cost.
