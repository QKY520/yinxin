# Result-To-Claim Gate - P5 Domain A/B/C/D - 2026-07-25

## Scope

This is a GPU-free result-to-claim review after the bounded P5 domain-test
A/B/C/D runs completed.

Reviewed evidence:

- dataset: frozen `domain_test`, 170 records
- K: 5
- seeds: 42, 43, 44
- configs: A/B/C/D only
- task evidence: NER only
- no E/E-prime paid replication
- no CLUENER/public benchmark P5 result yet
- no K=1/K=10 result yet
- no relation-enabled P5 result yet

No local Python, vLLM, paid GPU work, dry-run, prompt generation, or model call
was run for this review.

## Intended Claim Before Review

The original broad paper direction was:

> A reproducible low-label equipment-domain IE pipeline combining kNN
> demonstrations, glossary/schema constraints, RAG evidence, and
> self-verification can improve extraction quality and reduce unsupported /
> hallucination-style entity predictions.

The completed P5 domain A/B/C/D evidence can only test part of that claim.

## Evidence

Three-seed aggregate numbers, sample standard deviation:

| Config | Precision mean +/- std | Recall mean +/- std | F1 mean +/- std | FP mean +/- std |
| --- | ---: | ---: | ---: | ---: |
| A | 0.484066 +/- 0.025428 | 0.599231 +/- 0.028904 | 0.534645 +/- 0.004375 | 613.3 +/- 88.8 |
| B | 0.505743 +/- 0.000234 | 0.615304 +/- 0.001816 | 0.555169 +/- 0.000880 | 573.7 +/- 1.2 |
| C | 0.511433 +/- 0.000472 | 0.640811 +/- 0.001210 | 0.568858 +/- 0.000769 | 584.0 +/- 0.0 |
| D | 0.525135 +/- 0.000000 | 0.613208 +/- 0.000000 | 0.565764 +/- 0.000000 | 529.0 +/- 0.0 |

Clean deltas:

| Comparison | Factor | Delta F1 | Delta FP |
| --- | --- | ---: | ---: |
| B - A | kNN examples | +0.020524 | -39.7 |
| C - B | glossary injection | +0.013689 | +10.3 |
| D - C | RAG evidence | -0.003094 | -55.0 |
| D - A | combined B/C/D path | +0.031119 | -84.3 |

Human review accepted the near-tie interpretation for C versus D: C is
marginally ahead on recall/F1, while D is clearly ahead on precision and FP
reduction. Do not write that C significantly beats D.

## Secondary Review Verdict

The secondary result-to-claim reviewer judged the evidence as:

- `claim_supported`: `partial`
- confidence: high for the narrow domain-test NER verdict; medium for
  paper-level framing until supplementary evidence exists.

## What The Results Support

The results support a scoped domain-test NER claim:

1. kNN examples are positive over fixed-random examples:
   `B - A = +0.020524` F1 and about `-39.7` FP.
2. Glossary injection improves recall/F1:
   `C - B = +0.013689` F1.
3. RAG evidence is a precision and false-positive reduction module:
   `D - C = -0.003094` F1 but about `-55.0` FP.
4. The combined path from A to D is positive:
   `D - A = +0.031119` F1 and about `-84.3` FP.

## What The Results Do Not Support

The current evidence does not support:

- broad information extraction claims across tasks;
- relation extraction claims;
- public benchmark generalization;
- K=1/K=10 robustness;
- self-verification or CoVe benefit;
- a claim that RAG is the best F1 module;
- a claim that C substantially outperforms D.

## Missing Evidence

The main gaps are:

1. CLUENER/public NER evidence or a documented public-benchmark protocol.
2. K-sensitivity for at least selected rows if the paper wants few-shot
   robustness claims.
3. Formal false-discovery-style summaries beyond FP counts, recomputed from
   per-query rows.
4. Relation-enabled dev-first diagnostic if RE remains in the paper.
5. Paid E/E-prime rows only if the human explicitly decides to revisit
   verification despite negative/mixed dev evidence.

## Revised Claim

Use this scoped claim for the current evidence:

> In a frozen low-label Chinese equipment-domain NER setting, kNN demonstrations
> and glossary injection improve entity extraction F1, while RAG evidence
> preserves near-tied F1 and improves precision / reduces false-positive entity
> predictions. Verification and relation extraction are not claimed from the
> current evidence.

## Route

Recommended next action:

1. Continue GPU-free paper-facing aggregation and wording cleanup.
2. Produce a compact paper table and claim-evidence map from the current domain
   A/B/C/D results.
3. Decide after that whether supplementary evidence is worth a new gate.

No further paid GPU work is authorized by this verdict.
