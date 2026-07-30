# Findings

## 2026-07-30 - Full-IE Route Decision And Verifier Evidence

- The human selected a minimum defensible full-IE extension; the narrow NER/JISE
  package remains a fallback and must not be presented as completed IE.
- Planning artifacts:
  `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_PLAN_20260730.md` and
  `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_TRACKER_20260730.md`.
- Proposed architecture: preserve/reuse Stage N NER outputs, then run a
  relation-only Stage R over predicted entities. Domain RE uses end-to-end exact
  directed relation-triple micro P/R/F1. Relation-aware E verifies D; E-prime
  verifies C; dropping an entity removes its incident relations.
- Accounting: 60 reported cells total; 12 have valid NER Stage N only, 48 are
  absent, and all 30 domain cells still need Stage R. Adding only domain K=5
  E/E-prime would leave the project at 18/60 reported cells with 42 absent.
- Historical E evidence is NER dev sanity, not final test or relation-aware
  verification. E v1 was clearly negative: F1 `0.4264` versus D `0.5415`, with
  18/20 audited drops wrong. E v2 was mixed/negative: F1 `0.5367`, with 7/13
  drops wrong, 5/13 correct, and 1/13 unclear. E-prime was never executed with
  model calls; E v3 was preparation only.
- CoVe is deletion-only. It cannot recover false negatives or repair entity
  boundaries/types, and relation-aware over-deletion also removes incident
  relations. A positive claim requires a dev drop audit with at least 70%
  genuine errors among deleted units; below 50% stops the positive route.
- Current authorization: planning/documentation only. The next possible gate is
  `FULL_IE_IMPLEMENTATION_APPROVED`, limited to AutoDL no-card Stage R/metric/
  verifier implementation and synthetic tests. It does not authorize data
  prompts, `domain_test`, model/API/vLLM/GPU use, paper edits, or GitHub sync.
- Completing the matrix guarantees only evaluation completeness. Positive RE,
  CoVe, RAG, glossary, public-transfer, or K-robustness claims still depend on
  observed results and uncertainty; all negative rows must be retained.

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
