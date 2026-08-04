# Focused CLUENER Public-NER Final Gate

Date: 2026-08-04

Human gate: `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`

Status: `AUTHORIZED_AWAITING_HUMAN_GPU`

## Route Amendment

The human approved one narrow amendment to the 2026-08-04 NER-primary route.
The original 60-cell completion route remains closed, except for the 12
CLUENER A/B/C/D K=5 NER cells named below. IE051, domain reruns, E/E-prime,
K scans, relation extraction, F8 completion, F9 full-matrix aggregation, paper
propagation, submission, and GitHub synchronization remain closed.

Authorization does not create evidence. Until all 12 cells finish and pass
validation, literal matrix accounting remains `4/60`, and public-benchmark
generalization remains unsupported.

The earlier paper-propagation discussion produced no manuscript edit. Paper
work is deferred until this public block is closed and a separate
result-to-claim step determines what the new results support.

## Scientific Purpose

The only purpose of this gate is to test whether the NER-side A/B/C/D mechanism
chain transfers from the frozen equipment-domain setting to a public Chinese
NER protocol. It is not a reduced full-IE matrix and cannot support RE, CoVe,
K-robustness, or complete-matrix claims.

The efficient reduction is by configuration, not by evaluation examples: all
1,343 labeled official CLUENER dev records must be evaluated. No sampled
public subset may be substituted.

## Exact Cells

Dataset and split: complete labeled official CLUENER dev, `1,343` records.
The official unlabeled CLUENER test split is excluded.

Task: NER only. K: `5`. Seeds: `42`, `43`, and `44`.

| Config | Fixed definition | Cells |
| --- | --- | ---: |
| A | fixed-random demonstrations; no glossary; no RAG | 3 |
| B | kNN demonstrations; no glossary; no RAG | 3 |
| C | B plus frozen support-derived CLUENER glossary | 3 |
| D | C plus frozen F6 top-3 RAG replay | 3 |
| **Total** |  | **12** |

Canonical cell identities are the corresponding CLUENER A/B/C/D K=5
seed42/43/44 entries in the F5 frozen inventory. Execution must use versioned
copies; the F3 and F5 originals must not be overwritten merely to change
authorization or output paths.

## Locked Dependencies

- Primary model: Qwen2.5-7B-Instruct through vLLM, using the existing fixed
  model and generation contract.
- F5 freeze manifest SHA256:
  `592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e`.
- F5 canonical manifest SHA256:
  `e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae`.
- CLUENER support bank: 30 records, SHA256
  `abd6a338bf393426f35e12a08d073c6661e59131bc52ae77ca9f96d8859a5219`.
- Support-only CLUENER glossary: 61 entries, SHA256
  `0ac4dc41ceb9c458250354fef3826c8b21a9d128c9491a6477b2171f03ba3a9b`.
- Labels-stripped CLUENER RAG corpus SHA256:
  `f0b0cef66415bff65537076d1ab16552038dcb4388ed22c133255057ac2eb7ee`.
- F6 CLUENER replay summary: 1,343 rows and 4,029 passages, SHA256
  `36a529b9cd8cd0a78d2438376885263d5b9d63cb4967a0e88ad50eedbdffb455`.
- F6 CLUENER replay rows SHA256:
  `ba592a229ee96f32538a4b2a44b82b3149a8b02a9db0130c7380c32efc80c262`.
- F6 recovery backup manifest SHA256:
  `e098c138c201fdc1e0804183da5eb97e1d6e8208fb2abd5b20d27adcb18f2947`.

Every lock must pass before a final-data prompt or model call. The scorer may
read the labeled dev gold only to compute metrics; labels must never enter a
prompt, demonstration candidate pool, glossary, or RAG evidence.

## Human And Agent Sequence

1. This documentation step records the gate and then stops.
2. The human boots the AutoDL RTX 4090 24 GB and reports the live hourly price.
3. The agent verifies GPU identity and free memory, absence of conflicting
   vLLM/Qwen/runner sessions, storage, source/resource hashes, output
   collisions, and the exact 12-cell execution manifest.
4. If the reported price differs from the last observed `2.8 CNY/hour`, the
   agent reports the revised 8-hour and 10-hour cost before any model call and
   waits for confirmation.
5. The agent starts the fixed Qwen2.5-7B vLLM service and runs only the 12 cells.
   A small prefix check, if used, must be the retained beginning of the same
   final cell; it cannot be discarded, tuned on, or rerun under changed rules.
6. The agent stops at every structural, hash, cost, or time condition below.
7. At closeout, the agent stops vLLM, verifies no model process, backs up and
   hash-verifies all artifacts, mirrors lightweight outputs to `D:\yinsir`,
   reports the platform-observed paid window and cost, and asks the human to
   return the instance to no-card mode.

## Time And Cost Lock

- Measured planning basis: F4b A/B/C plus D without online retrieval is about
  `4.49 seconds/query` across four configurations.
- Pure-inference estimate for 1,343 rows, four configs, and three seeds:
  approximately `5.0 GPU hours`.
- Target paid-GPU envelope: `8 hours`.
- Hard stop: `10 paid-GPU hours`, measured from the successful paid-card
  preflight. At the hard stop, issue no new model request; preserve and back up
  partial results and report status.
- At the last observed `2.8 CNY/hour`, the planning estimate is about
  `17-22 CNY`, with a 10-hour ceiling of about `28 CNY`. The live platform
  price and bill are authoritative.
- F6 replay must be used. Recomputing BGE-M3/reranker retrieval inside the paid
  final run is forbidden.

## Required Outputs And Validation

Each cell must retain `1,343` ordered per-query rows, complete prompts, raw
responses, cache entries, prompt/raw hashes, example IDs, glossary matches,
RAG passage IDs where applicable, latency, retry, sanitizer, and parse-failure
records. Identical requests may use the existing SHA256 cache; different seeds
or generation settings must not be treated as identical without a hash match.

Required metrics are entity-level micro precision, recall, and F1; TP/FP/FN;
entity false-discovery-style rate; per-type metrics; parse-failure rate; retry
count; and latency. Mechanical three-seed mean and sample standard deviation
for A/B/C/D are allowed as part of cell validation. Claim interpretation,
paper wording, and cross-route result-to-claim are not authorized by this gate.

Completion requires:

- 12/12 exact cells present with 1,343 unique aligned IDs each;
- full official labeled dev coverage, with no sampled replacement;
- zero unsupported entity types and no gold leakage into prompts/resources;
- every metric recomputable from per-query rows;
- fixed retry behavior, with parse failures counted as no prediction;
- all source, prompt, raw-output, cache, result, and backup hashes verified;
- negative, near-tied, failed, and partial outputs preserved without selection;
- vLLM stopped and no Qwen/runner process left after the paid phase.

If any config reaches a final parse-failure rate of `5%` or more, or a locked
hash/resource/output-path check fails, stop before the next cell. Do not revise
the prompt or protocol from final-data behavior.

## Explicit Exclusions

This gate does not authorize:

- any CLUENER example sampling in place of all 1,343 labeled dev rows;
- the official unlabeled CLUENER test split;
- E or E-prime, K=1 or K=10, relation extraction, Stage R, or verification;
- any domain Stage N/Stage R rerun, IE051, or other matrix cell;
- support-bank, glossary, RAG, prompt, parser, metric, threshold, model, or
  generation-policy changes;
- online BGE-M3/reranker retrieval during the paid final run;
- test-informed tuning, favorable-seed selection, or deletion of negative rows;
- paper/LaTeX/Markdown edits, result-to-claim interpretation, DOCX generation,
  submission, or GitHub synchronization;
- renting, switching, stopping, or releasing hardware by the agent.

## Post-Run Gate

Successful execution would move literal inventory accounting from `4/60` to
`16/60`: four existing domain cells plus 12 CLUENER NER cells. Eight domain
cells would remain Stage N-only and 36 cells wholly absent. The remaining 44
incomplete cells stay `CLOSED`; the full 60-cell route does not reopen.

After closeout, stop. A separate
`NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` gate is required to decide whether
the public results support transfer, how they change the `partial` verdict,
and what may later be propagated to the complete
`docs/JISE_OVERLEAF_LATEX_20260729/` project. `main.tex` is only the Overleaf
entry point; manuscript content lives in `frontmatter.tex` and `sections/*.tex`.
