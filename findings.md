# Findings

## 2026-08-06 - Focused CLUENER Public-NER Result-To-Claim

- Gate: `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED`; verdict `partial`,
  confidence `high`. This was an existing-evidence review only: no Python,
  model/API, GPU, experiment, result recomputation, or manuscript edit ran.
- Public evidence: complete CLUENER labeled official dev (`1,343` rows),
  A/B/C/D, K=5, seeds42/43/44. Mean F1 is
  `0.428519/0.513964/0.517521/0.513424`; the unfavorable A seed44 result is
  retained.
- Clean public contrasts: `B-A` F1 `+0.085445`; `C-B` F1 `+0.003557` with a
  small recall gain; `D-C` F1 `-0.004097`, precision `+0.009832`, recall
  `-0.016059`, and FP `-95`. These directions match the frozen equipment-
  domain contrasts.
- Supported wording: the NER mechanisms show directionally consistent,
  descriptive behavior on the frozen equipment-domain test and one focused
  CLUENER evaluation. RAG reproduces a near-tied-F1, higher-precision,
  lower-FP operating point on the additional benchmark.
- Claim boundary: one public dataset, labeled-dev-as-final, no public paired
  uncertainty, and near-deterministic B/C/D seeds do not establish broad
  public-benchmark or cross-domain generalization. The public glossary is a
  support-derived schema-specific lexicon, not the equipment glossary.
- Still unsupported: significance, SOTA, supervised-baseline superiority,
  positive RE/public RE, RAG-for-RE, CoVe, `HAS_METRIC`, K robustness,
  formal frozen-test IAA, complete F8/F9, full matrix, and full IE.
- Route remains frozen: NER is the main contribution; RE is an exploratory
  negative result/limitation. Accounting stays `16/60`; the other 44 cells are
  `CLOSED`, and missing evidence is a limitation rather than an execution
  backlog.
- Independent review used the same documented fallback as RTC01 because the
  skill-specified `gpt-5.4` was unavailable: read-only `gpt-5.6-sol`, `xhigh`.
- Full report:
  `docs/RESULT_TO_CLAIM_NER_PUBLIC_CLUENER_ABCD_K5_20260806.md`.
- The next possible action recorded at the time was the separately approved
  paper-only `NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED` gate for
  the complete `docs/JISE_OVERLEAF_LATEX_20260729/` project. That gate was later
  consumed in commits `8189f71` and `8f1f3e1`; this findings log remains a
  historical evidence record and its claims were not changed.

## 2026-08-04 - Focused CLUENER Public-NER Route Amendment

- Gate: `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`; status
  `AUTHORIZED_AWAITING_HUMAN_GPU`. No experiment has started and current
  evidence/accounting remains `4/60`.
- Exact scope: complete labeled official CLUENER dev (`1,343` rows), A/B/C/D
  only, K=5, seeds42/43/44, NER only, reusing frozen F3/F5 support/glossary
  resources and the F6 1,343-row/4,029-passage RAG replay.
- Purpose: test whether the supported NER-side mechanism chain transfers to a
  public Chinese NER protocol. Authorization is not evidence; public transfer
  remains unsupported until all 12 cells pass closeout and result-to-claim.
- Cost lock: about 5 pure-inference GPU hours, target paid window 8 hours, hard
  stop 10 hours. At the last `2.8 CNY/hour` price, expected spend is about
  17-22 CNY with an approximately 28 CNY ceiling. The human must boot the
  RTX 4090 24 GB and report the live price before preflight/model calls.
- Successful verified closeout would move accounting to `16/60`. IE051,
  E/E-prime, K scans, RE/Stage R, domain reruns, and the other 44 incomplete
  cells remain `CLOSED`; the full matrix does not reopen.
- Post-run interpretation requires a separate
  `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` gate. Paper edits, submission, and
  GitHub synchronization are excluded from the experiment gate.
- The active future manuscript is the complete
  `docs/JISE_OVERLEAF_LATEX_20260729/` project. `main.tex` is the Overleaf entry
  point; `frontmatter.tex` and `sections/*.tex` contain the paper. Historical
  Markdown drafts are reference artifacts, not the refinement target.
- Exact contract:
  `docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_GATE_20260804.md`.

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
- At this route-freeze decision point, no experiment was the next step and
  paper propagation required a separate gate. The later focused public-NER
  amendment is recorded in the newer entry above.

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
