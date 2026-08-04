# Findings

## 2026-08-04 - F7 Result-To-Claim And NER Fallback Route Freeze

- Gate: `FULL_IE_STOP_AND_NER_FALLBACK_RTC_APPROVED`; verdict `partial`,
  confidence `high`.
- Supported paper line: on the frozen low-label Chinese equipment-domain NER
  test set, kNN demonstrations and glossary injection have scoped observed
  F1/recall gains, while RAG keeps F1 near-tied and improves precision/reduces
  entity false positives. B-A and C-B are not described as statistically
  significant; D-C is a precision/FP operating-point change, not an F1 gain.
- Auxiliary value: F7 proves that the locked Stage N + Stage R pipeline can
  produce reproducible, per-query auditable final cells with complete prompt,
  cache, parser, hash, failure-repair, and backup provenance.
- Negative evidence: A/B/C/D seed42 exact RE F1 is
  `0.040541/0.056972/0.057971/0.045381`; D is below C and all four cells have
  zero `HAS_METRIC` TP. F4a/F4b remain dev/tune-only and do not support final
  CoVe or public-generalization claims.
- Annotation limits remain material: fresh non-test entity calibration F1 is
  exactly `0.800000`, `TECH_SCHEME` F1 is `0.153846`, and relation file
  concordance F1 is `0.417391` (`PART_OF=0.246154`). None is frozen-test formal
  IAA.
- Matrix evidence remains literal `4/60`: four complete cells, eight Stage
  N-only partial cells, and 48 wholly absent cells.
- Human route decision: stop filling the 60-cell matrix. Do not execute IE051,
  E/E-prime, K scans, CLUENER final, F8, or F9. IE051 is retained as a
  historical proposal with status `CLOSED`, meaning not executed because the
  human selected another route; it is not a failed or blocked experiment.
- Frozen paper route: NER is the main contribution; RE is an exploratory
  negative result/limitation. Positive RE, RAG-for-RE, CoVe, `HAS_METRIC`,
  public transfer, K robustness, and complete-IE claims remain unsupported.
- Independent review: the skill-requested `gpt-5.4` reviewer was unavailable
  in the current interface, so a read-only `gpt-5.6-sol` xhigh secondary agent
  supplied the structured judgment and agreed with the `partial` route freeze.
- Full report:
  `docs/RESULT_TO_CLAIM_F7_NER_FALLBACK_ROUTE_FREEZE_20260804.md`.
- No experiment is the next step. Paper propagation requires a separate
  `NER_FALLBACK_MANUSCRIPT_PROPAGATION_APPROVED` gate.

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
