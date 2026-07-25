# Findings

## 2026-07-25 - P5 Domain A/B/C/D Result-To-Claim Verdict

- Verdict: `partial`
- Confidence: high for the narrow domain-test NER verdict; medium for paper-level
  framing until supplementary evidence exists.
- Review status: secondary Codex result-to-claim reviewer completed on
  2026-07-25 and agreed with the `partial` narrow verdict.
- Supported claim: in the frozen low-label Chinese equipment-domain NER setting,
  kNN demonstrations improve over fixed-random examples, glossary injection
  improves recall/F1, and RAG evidence keeps F1 near-tied with glossary-only
  while improving precision and reducing false-positive entity predictions.
- Main evidence: A F1 `0.534645 +/- 0.004375`, B `0.555169 +/- 0.000880`,
  C `0.568858 +/- 0.000769`, D `0.565764 +/- 0.000000`. Clean deltas:
  `B-A = +0.020524` F1 and about `-39.7` FP; `C-B = +0.013689` F1 and about
  `+10.3` FP; `D-C = -0.003094` F1 and about `-55.0` FP; `D-A = +0.031119`
  F1 and about `-84.3` FP.
- Best scoped wording: "In a frozen low-label Chinese equipment-domain NER
  setting, kNN demonstrations and glossary injection improve entity extraction
  F1, while RAG evidence preserves near-tied F1 and improves precision / reduces
  false-positive entity predictions. Verification and relation extraction are
  not claimed from the current evidence."
- Not supported: broad IE claims, RE claims, public benchmark generalization,
  K=1/K=10 robustness, or self-verification/CoVe benefit.
- Missing evidence: CLUENER/public NER results, K-sensitivity, verifier rows if
  verification is to be claimed, relation-enabled dev diagnostics if RE is to be
  discussed, and formal false-discovery-style summaries beyond FP counts.
- Route: do GPU-free paper-facing aggregation and wording cleanup first. Any
  paid GPU supplement requires a new bounded human gate.
