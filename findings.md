# Findings

## Result-to-Claim Gate - 2026-07-25

- claim_supported: partial
- scope: frozen self-built `domain_test`, NER-only, K=5, seeds 42/43/44, configs A/B/C/D.
- supported: kNN improves NER F1 over fixed random examples; glossary further improves recall/F1; RAG is F1-neutral to slightly negative versus glossary but improves precision and reduces false-positive entities. The combined A-to-D path improves F1 and lowers FP on the domain test set.
- not supported: broad IE claims, relation extraction claims, public benchmark generalization, K-sensitivity claims, and self-verification/CoVe benefit claims.
- main evidence: A F1 0.534645 +/- 0.004375, B 0.555169 +/- 0.000880, C 0.568858 +/- 0.000769, D 0.565764 +/- 0.000000. Clean deltas: B-A +0.020524 F1 and about -39.7 FP; C-B +0.013689 F1 and about +10.3 FP; D-C -0.003094 F1 and about -55.0 FP; D-A +0.031119 F1 and about -84.3 FP.
- claim revision: In a frozen low-label Chinese equipment-domain NER benchmark, kNN demonstrations and glossary injection improve entity extraction F1, while adding RAG evidence yields a near-tie in F1 but improves precision and reduces unsupported false-positive entity predictions. Verification and relation extraction are not claimed from the current P5 evidence.
- missing evidence: CLUENER/public NER benchmark results, E/E-prime verifier rows if verification is to be claimed, K=1/K=10 sensitivity, relation-enabled dev/test evidence if RE is to be discussed, hallucination-rate summaries beyond FP counts, and statistical/resampling checks if significance language is desired.
- next route: use GPU-free paper-facing analysis first; only request paid GPU for a bounded CLUENER/domain supplement or verifier override after a separate human gate.
- confidence: high for the partial/narrow verdict; medium for any paper-level claim until supplementary evidence is added.
- review status: local conservative verdict pending external reviewer-agent review; no secondary reviewer provider was available in this session.
