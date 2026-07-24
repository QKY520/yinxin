# P5 Domain-Test A/B/C/D Replication - 2026-07-24

## Scope

Human approved the bounded paid GPU gate:

```text
P5_DOMAIN_REPLICATION_APPROVED
```

Approved scope:

- dataset: `domain_test`
- K: 5
- configs: A/B/C/D only
- seeds: 43 and 44
- no E/E-prime
- no CLUENER
- no K=1/K=10
- no prompt, glossary, RAG, verifier, threshold, or model tuning
- D uses the fixed P5 D RAG replay manifest from the seed-42 pilot

This run completes the three-seed domain-test A/B/C/D evidence block by combining
the earlier seed-42 pilot with the newly run seeds 43 and 44.

## Execution

Remote:

- code commit: `a4df60d`
- vLLM tmux session: `p5rep_vllm`
- runner tmux session: `p5rep_runs`
- vLLM model: `/root/autodl-tmp/models/qwen2.5-7b`
- port: `8000`
- GPU: NVIDIA GeForce RTX 4090 24GB
- pre-flight GPU memory before vLLM: `0 MiB / 24564 MiB`
- vLLM loaded memory: about `22167 MiB / 24564 MiB`
- all eight approved cells exited with code 0
- vLLM was stopped after completion
- post-stop GPU memory: `0 MiB / 24564 MiB`

Execution order:

1. B seed 43
2. C seed 43
3. D seed 43
4. A seed 43
5. B seed 44
6. C seed 44
7. D seed 44
8. A seed 44

The runner wrote a done marker at `logs/p5_domain_replication_20260724.done`.
The initial marker filename had a trailing CR character due to Windows line
endings in the launch script; it was renamed to the normalized path above. This
was execution metadata cleanup only and did not alter any result file.

## Result Validation

Remote validation checked every expected summary and per-query file for seeds
42/43/44:

- 12 summary files present
- 12 per-query JSONL files present
- every per-query file has 170 rows
- every per-query SHA256 matches its summary
- every summary reports 0 parse failures
- 8 newly approved seed43/44 exit files contain code 0

## Raw Rows

| Config | Seed | Precision | Recall | F1 | TP | FP | FN | Parse failures | Elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 42 | 0.475166 | 0.601677 | 0.530990 | 574 | 634 | 380 | 0 | 450.578s |
| A | 43 | 0.464286 | 0.626834 | 0.533452 | 598 | 690 | 356 | 0 | 454.822s |
| A | 44 | 0.512748 | 0.569182 | 0.539493 | 543 | 516 | 411 | 0 | 379.468s |
| B | 42 | 0.505608 | 0.614256 | 0.554662 | 586 | 573 | 368 | 0 | 627.969s |
| B | 43 | 0.505608 | 0.614256 | 0.554662 | 586 | 573 | 368 | 0 | 628.388s |
| B | 44 | 0.506014 | 0.617400 | 0.556185 | 589 | 575 | 365 | 0 | 632.771s |
| C | 42 | 0.511706 | 0.641509 | 0.569302 | 612 | 584 | 342 | 0 | 437.815s |
| C | 43 | 0.511706 | 0.641509 | 0.569302 | 612 | 584 | 342 | 0 | 442.055s |
| C | 44 | 0.510888 | 0.639413 | 0.567970 | 610 | 584 | 344 | 0 | 442.112s |
| D | 42 | 0.525135 | 0.613208 | 0.565764 | 585 | 529 | 369 | 0 | 6237.211s |
| D | 43 | 0.525135 | 0.613208 | 0.565764 | 585 | 529 | 369 | 0 | 435.785s |
| D | 44 | 0.525135 | 0.613208 | 0.565764 | 585 | 529 | 369 | 0 | 434.571s |

## Three-Seed Aggregates

Sample standard deviation is reported.

| Config | Precision mean +/- std | Recall mean +/- std | F1 mean +/- std | FP mean +/- std | Total elapsed |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 0.484066 +/- 0.025428 | 0.599231 +/- 0.028904 | 0.534645 +/- 0.004375 | 613.3 +/- 88.8 | 1284.9s |
| B | 0.505743 +/- 0.000234 | 0.615304 +/- 0.001816 | 0.555169 +/- 0.000880 | 573.7 +/- 1.2 | 1889.1s |
| C | 0.511433 +/- 0.000472 | 0.640811 +/- 0.001210 | 0.568858 +/- 0.000769 | 584.0 +/- 0.0 | 1322.0s |
| D | 0.525135 +/- 0.000000 | 0.613208 +/- 0.000000 | 0.565764 +/- 0.000000 | 529.0 +/- 0.0 | 7107.6s |

## Clean Deltas

| Comparison | Isolated factor | Delta Precision | Delta Recall | Delta F1 | Delta FP |
| --- | --- | ---: | ---: | ---: | ---: |
| B - A | kNN examples | +0.021677 | +0.016073 | +0.020524 | -39.7 |
| C - B | glossary injection | +0.005690 | +0.025507 | +0.013689 | +10.3 |
| D - C | RAG evidence | +0.013702 | -0.027603 | -0.003094 | -55.0 |
| C - A | kNN + glossary | +0.027367 | +0.041580 | +0.034213 | -29.3 |
| D - A | kNN + glossary + RAG | +0.041069 | +0.013976 | +0.031119 | -84.3 |

## Findings

1. C is the marginally best three-seed F1 cell on `domain_test`:
   `0.568858 +/- 0.000769`. It improves over B by +0.013689 F1, mainly through
   recall.

2. D has the best precision and lowest false positives:
   precision `0.525135`, FP mean `529.0`. Relative to C, D removes 55 FP on
   average but loses enough recall to trail C by 0.003094 F1. This is a
   near-tie on F1, not evidence that C is substantially better than D.

3. kNN is a robust positive step on `domain_test`.
   B improves over A by +0.020524 F1 and reduces FP by about 39.7 on average.

4. Glossary is F1/recall-positive but not hallucination-reducing.
   C improves F1 over B but increases FP by about 10.3.

5. RAG is a precision and FP-reduction module in this evidence block. The
   honest paper-facing statement is: C and D are near-tied on F1, with C
   marginally ahead on recall and D clearly ahead on precision and FP reduction.
   This is paper-useful because D cuts 55 FP relative to C while keeping F1
   nearly unchanged.

6. D seed43/44 used the fixed replay manifest and therefore avoided the
   seed-42 CPU reranker overhead. Seed42 D took 6237.211s; replayed D seeds took
   about 435s each. This confirms the earlier runtime diagnosis.

7. These A/B/C/D configs remain NER-only. The zero-relation behavior from the
   pilot should still be treated as configuration/runner scope, not as evidence
   that the method fails at relation extraction.

## Backup

Remote light artifact bundle:

```text
/tmp/p5_replication_light_20260724.tar.gz
```

Local verified copy:

```text
D:\yinsir\backups\P5\p5_domain_replication_20260724.tar.gz
```

SHA256:

```text
e53e7e4371f6b7d3d5d21921e2adf9149ecf0b89b6db0029f99961bfd7233b14
```

The bundle contains 54 lightweight files: P5 configs, seed42/43/44 summaries,
seed42/43/44 per-query files, seed43/44 run logs and exit files, the normalized
done marker, and the fixed D replay manifest.

## Cost

Observed paid work window for this replication:

- vLLM session created: 2026-07-24 18:16:34 CST
- runner start: 2026-07-24 18:19:15 CST
- runner done: 2026-07-24 19:24:14 CST
- post-stop GPU memory check: 2026-07-24 19:27:50 CST

Using the last reported 4090 price of 2.7 CNY/hour, the observed vLLM window is
about 1.19 hours, or about 3.2 CNY. AutoDL platform billing remains the
authoritative cost record.

## Next Gate

Human review accepted the core interpretation: C is marginally best on F1, D is
the precision/FP-reduction row, and C versus D should be described as a near-tie
rather than as a substantial F1 win for C.

Stop here before any further paid gate. Reasonable GPU-free next steps:

1. write a paper-facing interpretation of the domain A/B/C/D three-seed block;
2. decide whether to add a relation-enabled dev-first diagnostic;
3. decide whether to prepare CLUENER-compatible P5 configs.

Do not run E/E-prime, CLUENER, K=1/K=10, or any further paid GPU work without a
new bounded gate.
