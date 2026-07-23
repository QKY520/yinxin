# P3 Domain Dev50 Final Sanity Summary - 2026-07-23

## Scope

This document summarizes the completed P3 domain-dev sanity sequence.

- Dataset: `domain_dev50`
- Split role: dev/tuning sanity only
- K: 5
- Seed: 42
- Model: Qwen2.5-7B-Instruct via vLLM
- Task summarized here: NER entity extraction
- Test usage: `domain_test` was not used
- Status: not final paper numbers; not 3-seed mean/std

## Result Table

| Config | Main change | Precision | Recall | F1 | TP/FP/FN | Hallucination rate | Verdict |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| A | fixed random, no glossary/RAG/verif | 0.4914 | 0.5570 | 0.5221 | 171/177/136 | 0.5086 | accepted baseline |
| B | kNN examples | 0.4767 | 0.5342 | 0.5038 | 164/180/143 | 0.5233 | negative |
| C | B replay + glossary | 0.4722 | 0.5537 | 0.5097 | 170/190/137 | 0.5278 | mixed |
| D | C + RAG rerank top-3 | 0.5211 | 0.5635 | 0.5415 | 173/159/134 | 0.4789 | positive, current best |
| E v1 | D + verifier v1 | 0.6173 | 0.3257 | 0.4264 | 100/62/207 | 0.3827 | negative, severe overkill |
| E v2 | D + source-first verifier v2 | 0.5266 | 0.5472 | 0.5367 | 168/151/139 | 0.4734 | mixed/near-tie negative |

Hallucination rate here means entity-level FP divided by all predicted entities.

## Main Findings

### A Baseline

A is a usable baseline. Parse failures were 0/50 and no entity type exceeded
90% of predictions. Human sanitizer audit found no sanitizer-caused misdrops.

### B kNN

B is negative. With only 30 support rows, kNN retrieved examples that were often
too broad or subdomain-mismatched. F1 dropped from A's 0.5221 to 0.5038.
Preserve this as evidence that example retrieval alone is not reliable under
the current tiny support condition.

### C Glossary

C is mixed. It recovered some entities versus B but increased FP, so F1 only
rose slightly to 0.5097 and remained below A. Human audit concluded glossary is
a double-edged tool: accurate term matches help, broad terms induce type bias
and false positives.

### D RAG

D is the strongest positive result.

- D vs C: F1 `+0.0317`, FP `190 -> 159`.
- D vs A: F1 `+0.0193`, FP `177 -> 159`.
- Human audit: 8 GOOD / 7 OK / 5 POOR.
- RAG evidence itself was often noisy, but the RAG block still made the model
  more conservative and reduced over-labeling.

D is the current best candidate for the next stage.

### E Verification

E v1 is clearly negative. It reduced hallucination rate but destroyed recall:
F1 fell from 0.5415 to 0.4264. Human audit found 18/20 dropped entities were
wrong drops. Root cause: the verifier treated RAG evidence as primary and
answered `no` when RAG did not mention the candidate entity.

E v2 fixed most of the catastrophic overkill, but still did not beat D:

- dropped units fell from 170 to 13;
- hallucination rate fell only from 0.4789 to 0.4734;
- F1 fell from 0.5415 to 0.5367;
- human audit found 7/13 wrong drops.

The remaining verifier bias is systematic: it is too harsh on military
formation/group entities and basic component/carried-weapon entities.

E v3 was prepared only as a GPU-free candidate-preserving prompt. It was not
executed with paid model calls and remains unauthorized.

## Decision

For the current domain-dev sanity stage:

1. D(RAG) is the best positive result.
2. kNN-only B is negative.
3. Glossary C is mixed.
4. Verification E v1/E v2 is negative/mixed and should not receive more paid
   GPU time by default.
5. Do not run E-prime now.
6. Do not proceed to P5/full ablations without an explicit human gate.

## Recommended Next Step

Use GPU-free planning to decide the next bounded paid gate.

Recommended default:

- preserve D as the current positive result;
- document verification as a negative/mixed branch;
- prepare the next run plan around D rather than spending more on verifier
  prompt variants.

Acceptable next gates, in order of preference:

1. Prepare a D-focused next-stage plan/config set in GPU-free mode.
2. Prepare full P5 grid configs while keeping E as a negative row, but do not
   run them yet.
3. Explicitly approve another bounded verifier experiment using v3 despite the
   current recommendation.

`domain_test` remains untouched.
