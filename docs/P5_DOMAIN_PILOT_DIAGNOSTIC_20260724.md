# P5 Domain-Test Pilot GPU-Free Diagnostic - 2026-07-24

## Scope

This diagnostic was done after the paid P5 domain-test pilot had completed and
after the human switched AutoDL back to GPU-free/no-card mode. It used only
existing result artifacts under `/root/project/results/p5` and their synced
local copies under `D:\yinsir\results\p5`.

No Python was run locally. No vLLM server, paid GPU work, dry-run, prompt
generation, or model call was started. The remote status check returned
`No devices were found`, confirming GPU-free/no-device mode at the time of this
analysis.

The pilot is a single-seed decision run only:

- dataset: `domain_test`
- K: 5
- seed: 42
- configs: A/B/C/D
- gate used for the paid run: `P5_DOMAIN_PILOT_APPROVED`

These numbers are not final paper mean +/- std results.

## Raw Result Table

| Config | Main change | Precision | Recall | F1 | TP | FP | FN | FP / predicted | Elapsed | LLM latency sum | Parse failures |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | fixed-random examples | 0.4752 | 0.6017 | 0.5310 | 574 | 634 | 380 | 0.5248 | 450.578s | 449.487s | 0 |
| B | kNN examples | 0.5056 | 0.6143 | 0.5547 | 586 | 573 | 368 | 0.4944 | 627.969s | 421.310s | 0 |
| C | kNN + glossary | 0.5117 | 0.6415 | 0.5693 | 612 | 584 | 342 | 0.4883 | 437.815s | 437.097s | 0 |
| D | kNN + glossary + RAG | 0.5251 | 0.6132 | 0.5658 | 585 | 529 | 369 | 0.4749 | 6237.211s | 436.549s | 0 |

All four files contain 170 per-query rows. Average gold entities per record are
5.612. The 11 zero-gold rows still receive non-empty predictions in every
config, but D has the lowest zero-gold average prediction count:

| Config | Avg predicted entities | Zero-gold avg predicted entities |
| --- | ---: | ---: |
| A | 7.106 | 7.455 |
| B | 6.818 | 6.091 |
| C | 7.035 | 6.818 |
| D | 6.553 | 5.909 |

## Clean Deltas

| Comparison | Interpretation | Delta P | Delta R | Delta F1 | Delta TP | Delta FP | Delta FN |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B - A | kNN example selection | +0.0304 | +0.0126 | +0.0237 | +12 | -61 | -12 |
| C - B | glossary injection | +0.0061 | +0.0273 | +0.0146 | +26 | +11 | -26 |
| D - C | RAG evidence | +0.0134 | -0.0283 | -0.0035 | -27 | -55 | +27 |
| C - A | kNN + glossary combined | +0.0365 | +0.0398 | +0.0383 | +38 | -50 | -38 |
| D - A | kNN + glossary + RAG combined | +0.0500 | +0.0115 | +0.0348 | +11 | -105 | -11 |

## Type-Level Pattern

| Config | Type | Precision | Recall | F1 | TP | FP | FN |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | EQUIPMENT | 0.4942 | 0.5812 | 0.5342 | 297 | 304 | 214 |
| B | EQUIPMENT | 0.5280 | 0.6086 | 0.5655 | 311 | 278 | 200 |
| C | EQUIPMENT | 0.5365 | 0.6614 | 0.5925 | 338 | 292 | 173 |
| D | EQUIPMENT | 0.5470 | 0.6262 | 0.5839 | 320 | 265 | 191 |
| A | MODULE | 0.4784 | 0.7370 | 0.5802 | 255 | 278 | 91 |
| B | MODULE | 0.5608 | 0.7197 | 0.6304 | 249 | 195 | 97 |
| C | MODULE | 0.5704 | 0.7139 | 0.6341 | 247 | 186 | 99 |
| D | MODULE | 0.6010 | 0.7139 | 0.6526 | 247 | 164 | 99 |
| A | METRIC | 0.2222 | 0.3333 | 0.2667 | 10 | 35 | 20 |
| B | METRIC | 0.1587 | 0.3333 | 0.2151 | 10 | 53 | 20 |
| C | METRIC | 0.1944 | 0.4667 | 0.2745 | 14 | 58 | 16 |
| D | METRIC | 0.1642 | 0.3667 | 0.2268 | 11 | 56 | 19 |
| A | TECH_SCHEME | 0.4138 | 0.1791 | 0.2500 | 12 | 17 | 55 |
| B | TECH_SCHEME | 0.2540 | 0.2388 | 0.2462 | 16 | 47 | 51 |
| C | TECH_SCHEME | 0.2131 | 0.1940 | 0.2031 | 13 | 48 | 54 |
| D | TECH_SCHEME | 0.1373 | 0.1045 | 0.1186 | 7 | 44 | 60 |

## Per-Record Movement

| Comparison | Changed records | Improved | Worsened | Same | Neutral changed |
| --- | ---: | ---: | ---: | ---: | ---: |
| B - A | 130 | 72 | 55 | 40 | 3 |
| C - B | 87 | 46 | 41 | 83 | 0 |
| D - C | 92 | 42 | 49 | 78 | 1 |

The direction is mixed at the record level. kNN has the clearest single-seed
win. Glossary is still positive overall, but its gains and regressions are
closely balanced. RAG changes many rows and is precision-oriented rather than
F1-oriented in this pilot.

## Relation Extraction Side Result

The four A/B/C/D pilot rows predicted zero relation triples:

| Config | Relation TP | Relation FP | Relation FN | Relation F1 |
| --- | ---: | ---: | ---: | ---: |
| A | 0 | 0 | 427 | 0.0000 |
| B | 0 | 0 | 427 | 0.0000 |
| C | 0 | 0 | 427 | 0.0000 |
| D | 0 | 0 | 427 | 0.0000 |

This means the pilot currently supports only the NER evidence line. RE should
remain auxiliary and should not be used as a positive claim unless a separate,
explicitly approved diagnostic or config correction shows why relation output is
absent and then produces reproducible relation predictions without test tuning.

## Findings

1. kNN example selection is the cleanest positive module in this pilot.
   It improves F1 by +0.0237 over fixed-random and reduces false positives by
   61. This supports keeping B as the first ablation improvement over A.

2. Glossary injection gives the best single-seed F1.
   C improves over B by +0.0146 F1 and raises recall by +0.0273. It also adds
   11 false positives, so the glossary effect should be described as recall/F1
   oriented, not as a hallucination reducer.

3. RAG reduces false positives but does not improve F1 over C on seed 42.
   D reduces FP by 55 and lowers the entity-level false-discovery-style rate
   from 0.4883 to 0.4749, but it also loses 27 TP and drops F1 by 0.0035. The
   fair pilot statement is: RAG improved precision and reduced FP, but its
   recall loss made F1 slightly worse than C in this seed.

4. RAG's runtime is the main engineering risk.
   D elapsed time is 6237.211s versus 437.815s for C, while the summed LLM
   request latency is nearly identical. The extra time is therefore dominated
   by CPU RAG/reranker work, not by vLLM generation. Any larger P5 plan that
   includes D should budget for this overhead or explicitly decide to run fewer
   RAG cells.

5. Type-level evidence is uneven.
   D improves MODULE F1 and precision, but harms EQUIPMENT recall, METRIC F1,
   and especially TECH_SCHEME F1. C is stronger for EQUIPMENT and METRIC. This
   suggests the RAG passages may make the model more conservative or shift
   attention toward component-like spans.

6. RE is currently a blocker for auxiliary relation claims.
   All four configs predicted zero relations while gold relation count is 427.
   The paper route should continue to treat NER as the main evidence line. RE
   should be reported only as a limitation or fixed in a separate human-approved
   GPU-free/code-level diagnostic before any paid relation-focused run.

## Recommended Next Gate

Do not run more paid work yet. The next best step is a bounded GPU-free/code
audit of relation-output suppression and RAG runtime, without touching
`domain_test` prompts or model outputs. If the human wants more paid evidence
after that audit, the lowest-risk paid gate is:

```text
Approve paid GPU P5 domain replication: run only A/B/C/D on domain_test,
K=5, seeds 43 and 44, with no prompt/glossary/RAG/verifier tuning and no
E/E-prime.
```

Do not authorize E/E-prime by default. P3 verification evidence was
negative/mixed, and the current pilot already has a precision-oriented D row
without verifier.
