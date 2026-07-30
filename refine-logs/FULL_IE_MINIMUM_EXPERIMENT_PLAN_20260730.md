# Minimum Defensible Full-IE Extension Plan

**Problem**: Complete the originally intended low-label Chinese equipment
information-extraction evidence without discarding the 12 frozen NER-only P5
cells.

**Method thesis**: A staged local-LLM pipeline first extracts entities and then
extracts explicit directed relations among the predicted entities. Retrieval,
glossary injection, RAG, and atomic verification are evaluated through the
pre-specified A/B/C/D/E/E-prime comparison chain.

**Date**: 2026-07-30

**Status**: The human selected the full-IE extension as the target; the design
and inventory are prepared, but `FULL_IE_IMPLEMENTATION_APPROVED` has not been
granted. This file authorizes no Python execution, data processing, prompt
generation, model/API call, vLLM startup, GPU use, `domain_test` read, paper
edit, or GitHub synchronization.

## Decision Summary

The minimum defensible implementation is a **two-stage IE pipeline**, not a
new joint entity-and-relation prompt for every row:

1. Stage N keeps the frozen NER extractor and its existing output contract.
2. Stage R receives the source text plus Stage N's predicted entity list and
   predicts only relations among those entities.
3. The main RE score is end-to-end exact directed triple micro P/R/F1. Missing
   or mistyped entity endpoints therefore prevent a relation from matching.
4. E and E-prime verify both entity atoms and relation atoms. Dropping an
   entity also drops every incident relation.

This choice preserves the 12 completed domain A/B/C/D, K=5, three-seed NER
outputs. Each of those cells still requires a new Stage R output before it can
enter the full-IE table. It avoids changing the already frozen NER prompt and
avoids rerunning those 12 NER cells merely to request relations.

The destination remains the original **60 reported cells**:

| Dataset / block | Cell definition | Reported cells |
| --- | --- | ---: |
| Domain K=5 | A/B/C/D/E/E-prime x seeds 42/43/44 | 18 |
| Domain K scan | A/E x K=1/10 x seeds 42/43/44 | 12 |
| CLUENER K=5 | A/B/C/D/E/E-prime x seeds 42/43/44 | 18 |
| CLUENER K scan | A/E x K=1/10 x seeds 42/43/44 | 12 |
| **Total** |  | **60** |

Current completion accounting is therefore:

- 12 cells have a valid frozen **NER stage only**;
- 48 reported cells are absent;
- all 30 domain cells need Stage R;
- only after those conditions are met may the result package be called a
  complete 60-cell matrix.

Historical verifier status is not a missing bookkeeping detail. E v1 was a
clear negative NER dev result (F1 `0.4264` versus D `0.5415`, with 18/20
audited drops wrong). E v2 was mixed/negative (F1 `0.5367`, with 7/13 wrong
drops, 5/13 correct, and 1/13 unclear). E-prime was never executed with model
calls, and E v3 was preparation only. The relation-aware E/E-prime work in this
plan is therefore a new dev-first protocol, not a replay of a passing verifier.

## Claim Map

| Claim | Why it matters | Minimum convincing evidence | Linked blocks |
| --- | --- | --- | --- |
| C1: The staged pipeline performs end-to-end equipment-domain IE, not NER alone. | This is required before the paper can use a full-IE framing. | Frozen domain results for entity micro P/R/F1 and exact directed relation-triple micro P/R/F1, with all A through E-prime K=5 rows and A/E K sensitivity. | B1, B2, B4 |
| C2: Retrieval, glossary, RAG, and verification have measurable, isolated effects under the fixed protocol. | This is the mechanism-level contribution. | Clean B-A, C-B, D-C, E-D, E-prime-C, and E-E-prime contrasts with paired uncertainty, all negative rows retained, and no test-informed tuning. | B2, B3, B4, B6 |

### Supporting scope claim

The same NER-side A through E-prime mechanism chain is evaluated on the
gold-bearing official CLUENER dev split. CLUENER has no relation schema in this
project, so it supports only public **NER** portability, not public RE
generalization.

### Anti-claims to rule out

- Adding a relation column to existing NER outputs is sufficient evidence of
  relation extraction.
- A completed matrix guarantees positive CoVe, RAG, RE, or K-robustness gains.
- CLUENER official unlabeled test data provide offline gold metrics.
- Three near-deterministic seeds establish broad stochastic robustness.
- Relation scores are reliable without disclosing relation-gold provenance and
  relation-calibration limitations.

## Fixed Protocol Choices

### Domain data

- Support: frozen 30 records, 183 entities, 74 relations.
- Development: frozen 50 records, 307 entities, 133 relations.
- Test: frozen 170 records, 954 entities, 427 relations.
- Entity types: EQUIPMENT, MODULE, TECH_SCHEME, METRIC.
- Relation types: USES, HAS_METRIC, PART_OF with the approved v3 direction and
  type matrix.
- No prompt, threshold, schema, glossary, retrieval, parser, or verifier change
  may be informed by `domain_test`.

### Stage R relation-only prompt

The relation prompt must contain, in order:

1. task definition and explicit same-sentence-only rule;
2. entity list copied exactly from the frozen Stage N prediction;
3. relation definitions, allowed head/tail types, and direction;
4. optional glossary block;
5. optional RAG evidence block;
6. K demonstrations using the same demonstration IDs as Stage N;
7. query text; and
8. the fixed JSON-only output instruction.

The model returns only zero-based `head`, `tail`, and `type` relation objects.
It cannot add, delete, rename, or re-bound entities. If fewer than two entities
or no type-compatible same-sentence pair exists, Stage R returns an empty list
deterministically and records why no model request was needed.

For the 12 existing P5 cells, Stage R must replay each row's recorded
`example_ids`, `glossary_terms`, and `rag_passages`. It must not reselect
examples or evidence from test text.

### Exact RE metric

Each relation is canonicalized as:

```text
(head_start, head_end, head_type, relation_type,
 tail_start, tail_end, tail_type)
```

Direction is part of the key. The primary score uses predicted entity
endpoints and is therefore end-to-end. Required diagnostics are:

- exact triple micro precision, recall, and F1;
- TP/FP/FN and relation false-discovery rate;
- per-relation-type metrics and gold/predicted counts;
- gold-relation endpoint coverage by Stage N;
- conditional relation accuracy among triples whose endpoints are available;
- relations predicted on zero-relation passages;
- parse-failure rate, retry count, latency, and sanitizer/drop counts.

### Relation-aware verification

E verifies D output; E-prime verifies C output. The verifier processes entity
atoms and relation atoms separately:

- an entity prompt checks exact span and type against source text first;
- a relation prompt checks both directed endpoints and the relation definition;
- RAG evidence is secondary context for E and absent for E-prime;
- only a valid `no` drops an atom; invalid answers keep the atom and are logged;
- a dropped entity deterministically removes incident relations;
- raw and verified entities/relations remain available in every row.

Before any final evaluation, manually review up to 20 dropped dev entities and
20 dropped dev relations. At least 70% in each available unit class should be
genuine errors for a positive verification claim. Below 50% requires stopping
and one dev-only revision; a second failure closes the positive CoVe claim.
E/E-prime may still be retained as negative full-matrix rows if the human
explicitly approves that continuation.

### CLUENER gold and portable resources

The official CLUENER test split is unlabeled and remains unused. The valid
offline protocol is:

- source pool: existing `cluener_train_pool.jsonl`;
- development/tuning: existing `cluener_tune.jsonl`, with a deterministic
  fixed tune subset for paid sanity;
- final public evaluation: complete labeled `cluener_dev.jsonl` (1,343 rows);
- support bank: one frozen 30-record bank drawn from train_pool before final
  evaluation, with documented type coverage;
- glossary: exact surface/type entries derived only from that 30-record support
  bank, so C does not consume the full labeled train set;
- RAG: labels stripped from remaining train-pool text, with support/tune/dev
  IDs and fixed 8-gram overlaps removed before indexing;
- retrieval: BGE-M3 top-20, bge-reranker-v2-m3 top-3, matching the fixed
  technology contract.

This protocol makes C/D/E portable rather than injecting the equipment-domain
glossary into unrelated CLUENER labels. It must be described as a
support-derived CLUENER lexicon and an unlabeled training-text RAG corpus, not
as the equipment glossary.

## Paper Storyline

### Main paper must prove

- Domain Stage N and Stage R form a reproducible end-to-end IE pipeline.
- All six K=5 configurations have complete entity and relation metrics over
  three seeds.
- A/E K=1/5/10 results establish the observed K dependence without selecting a
  favorable K after test evaluation.
- E/E-prime results and dropped-unit audits show whether verification helps or
  harms; negative results remain in the table.
- CLUENER rows use labeled dev gold and a separate, schema-valid public
  protocol.

### Appendix can support

- Per-type entity and relation metrics.
- Endpoint-coverage and relation-error decomposition.
- Sanitizer/parser event tables and verifier decision audits.
- Full paired bootstrap intervals and multiplicity-adjusted p-values.
- Runtime split by NER, relation extraction, retrieval, and verification.

### Experiments intentionally cut

- DuIE full evaluation: its relation ontology differs and its official test is
  unlabeled; adding it is not required to complete the original 60-cell grid.
- Few-NERD and CMNEE matrices: they do not share the paper's task/schema.
- New model families, QLoRA, 14B transfer, more than three nominal seeds, and
  new retrieval hyperparameter sweeps.
- Repairing or relabeling frozen v1 after seeing model predictions.
- A supervised encoder baseline unless later requested by a reviewer.

## Experiment Blocks

### B0: GPU-Free Implementation and Synthetic Verification

- **Claim tested**: none; this establishes executable correctness.
- **Work**: implement Stage R, exact triple metrics, combined per-query rows,
  relation-aware E/E-prime, config validation, aggregation, and tests.
- **Data**: synthetic fixtures only for unit tests; support/dev metadata may be
  inspected after its own gate. No `domain_test` read and no prompt artifact.
- **Success criterion**: AutoDL GPU-free tests pass; legacy NER-only configs
  produce byte-compatible behavior; malformed/directed/duplicate relation
  cases are covered.
- **Priority**: MUST-RUN.

### B1: Relation-Gold Calibration Diagnostic

- **Claim tested**: relation labels are sufficiently interpretable to report
  model RE results responsibly.
- **Data**: the existing 20-passage fresh non-test human-calibration texts may
  be reused, but both humans must independently add directed relations without
  seeing model output, frozen gold, or each other's relations.
- **Metric**: exact endpoint span/type plus directed relation-type micro F1,
  overall and per relation type; structural errors reported separately.
- **Success criterion**: no structural errors and a fully disclosed diagnostic.
  This remains non-test calibration, not frozen-test formal IAA. A low result
  weakens the dataset claim and is never repaired by deleting disagreements.
- **Priority**: MUST-RUN for a relation-quality contribution.

### B2: Domain Dev-First IE Sanity

- **Claim tested**: the staged protocol produces valid nonzero relation output
  and preserves the clean A/B/C/D/E/E-prime comparison.
- **Dataset**: domain_dev50 only.
- **Rows**: A/B/C/D Stage N+R and E/E-prime verification, K=5, seed 42.
- **Metrics**: all required entity/relation metrics, parse rate, endpoint
  coverage, atomic verifier audit, and latency.
- **Success criterion**: 50/50 rows reload; final parse failure below 5%; exact
  relation F1 is nonzero; no unsupported relation type; no test-informed
  choice; verifier audit passes the 70% criterion for any positive claim.
- **Failure interpretation**: allow at most one dev-only protocol revision. If
  RE remains unusable, do not launch test. If verification remains negative,
  retain it only as a negative matrix row or abandon the positive CoVe claim.
- **Priority**: MUST-RUN.

### B3: CLUENER Tune Sanity and Resource Freeze

- **Claim tested**: the public NER mechanism chain is schema-valid and does not
  depend on unlabeled test gold.
- **Dataset**: deterministic subset of `cluener_tune`, never official dev/test.
- **Rows**: A/B/C/D/E/E-prime, K=5, seed 42; add A/E at K=1/10 only if the
  common runner cannot be structurally verified from K=5.
- **Success criterion**: resource hashes, dedup report, prompt/config hashes,
  0 unsupported entity types, and parse failure below 5%.
- **Priority**: MUST-RUN before the 1,343-row public evaluation.

### B4: Frozen Domain Full-IE Matrix

- **Claim tested**: C1 and C2 on the primary domain setting.
- **Dataset**: frozen domain_test170, one locked evaluation after B0-B3.
- **Rows**: all 30 domain cells in the inventory above.
- **Setup**: Stage R is added to all 30 cells; the existing 12 Stage N files
  are reused by hash. New Stage N runs are needed only for A and the D source
  of E at K=1/10. K=5 E/E-prime reuse existing C/D Stage N files.
- **Success criterion**: no missing cell; all aggregates recompute; all
  prompts/configs match the pre-test freeze; every negative result is kept.
- **Priority**: MUST-RUN.

### B5: Gold-Bearing CLUENER NER Matrix

- **Claim tested**: the NER-side mechanism chain is portable to a public
  Chinese benchmark protocol.
- **Dataset**: complete official labeled CLUENER dev split, 1,343 rows.
- **Rows**: all 30 CLUENER cells in the inventory above; no RE metric.
- **Success criterion**: no unlabeled-test use, no missing cell, complete
  three-seed aggregates, resource/dedup hashes, and honest negative rows.
- **Failure interpretation**: domain-specific benefits that fail on CLUENER
  stay domain-specific; no public-generalization claim is made for them.
- **Priority**: MUST-RUN for literal completion of the original 60-cell grid.

### B6: Pre-Specified Aggregation and Result-to-Claim

- **Claim tested**: whether observed differences support the intended wording.
- **Analysis**: three-seed mean/SD plus 10,000-replicate paired
  passage-cluster bootstrap on entity F1, relation F1, entity FP, and relation
  FP. Primary contrasts are B-A, C-B, D-C, and E-D. E-prime-C and E-E-prime
  are secondary. Report Holm-adjusted inference if p-values are used.
- **Success criterion**: all numbers recompute from per-query rows; significance
  language appears only when the pre-specified interval/test supports it.
- **Failure interpretation**: completion of a cell does not turn a negative or
  near-tied result into a positive contribution.
- **Priority**: MUST-RUN after B4/B5.

## Execution Order and Human Gates

| Milestone | Agent work | Human action | Stop/go gate | GPU/cost |
| --- | --- | --- | --- | --- |
| F0 | Approve this scope and inventory only | Confirm staged IE and literal 60-cell target | No code before approval | 0 GPU |
| F1 | Implement B0 remotely in no-card mode; run synthetic/unit tests on AutoDL | Approve `FULL_IE_IMPLEMENTATION_APPROVED` | Tests and legacy compatibility pass | 0 paid GPU |
| F2 | Prepare relation-calibration sheets and validate returned annotations | Two humans independently annotate relations | Separate calibration approval and disclosure | Human time; 0 GPU |
| F3 | Prepare dev/tune configs, hashes, and resource manifests | Approve exact dev paid gate | No test paths/prompts; configs review clean | No-card prep |
| F4 | Run B2 and B3 only | Turn on paid GPU and later shut it down | Dev/tune success criteria pass | Roughly 5-15 CNY |
| F5 | Freeze prompts, metrics, resources, seeds, and all 60 final config IDs | Approve freeze manifest | No unresolved config or output collision | 0 GPU |
| F6 | Precompute leakage-safe RAG replay artifacts in no-card mode under an explicit evaluation-prep gate | Confirm no paid GPU is active | Hash/dedup/replay verification passes | 0 paid GPU |
| F7 | Run B4 domain cells in small batches; back up and hash after each batch | Approve each bounded paid batch; shut down after each | No missing/corrupt rows; no tuning | Roughly 20-60 CNY |
| F8 | Run B5 CLUENER cells in small batches; back up and hash after each batch | Approve each bounded paid batch; shut down after each | Complete 1,343-row cells; cost cap observed | Roughly 100-220 CNY |
| F9 | Aggregate B6, run result-to-claim, then separately update manuscript | Approve paper propagation only after audit | Claims follow results | 0 paid GPU |

Cost estimates are deliberately broad because relation prompts and atomic
verification have not yet been benchmarked. At the last reported 2.7 CNY/hour,
the plan targets **125-295 CNY** of additional paid compute. Stop and obtain a
new budget decision before cumulative additional spend exceeds 300 CNY or the
project total approaches the existing 400 CNY target. Platform billing is
authoritative.

## Final Output Contract

Every domain per-query row must include at least:

```text
id, dataset, config, k, seed, gold,
pred_entities_stage_n, pred_relations_stage_r, pred_raw, pred_verified,
ner_prompt_hash, relation_prompt_hash, verifier_prompt_hashes,
raw_ner_output_hash, raw_relation_output_hash,
example_ids, glossary_terms, rag_passage_ids,
parse_failure_ner, parse_failure_relation,
sanitization_flags, verifier_decisions,
latency_ner_ms, latency_relation_ms, latency_verifier_ms
```

Required paper-facing artifacts:

- one 60-cell run manifest with config hashes and status;
- `results/main_table.csv` with one row per reported cell;
- complete mean/SD and paired-analysis summary;
- domain entity and exact relation tables;
- CLUENER labeled-dev NER table;
- A/E K-sensitivity table or figure;
- E/E-prime raw-versus-verified audit;
- relation-calibration report;
- cost log and hash-verified phase backups.

## Risks and Mitigations

- **Existing 12 cells are only partially reusable**: reuse Stage N by hash, but
  require Stage R before counting them as full IE.
- **RE quality may be low**: tune only on dev, allow one protocol revision, and
  report endpoint coverage so entity errors are separated from relation errors.
- **Verification was previously negative**: enforce the manual drop audit and
  never promise a positive CoVe result in advance.
- **Relation gold lacks formal human IAA**: complete the non-test relation
  calibration and retain the provenance limitation.
- **CLUENER modules need schema-specific resources**: use only a frozen
  support-derived glossary and labels-stripped, deduplicated train text.
- **Public runtime dominates**: precompute RAG replay in no-card mode, batch by
  config, reuse valid cache entries, and stop at cost gates.
- **Test leakage**: no test-derived prompt, threshold, glossary, verifier, or
  config changes; test failures are reported rather than repaired.
- **Positive claims cannot be guaranteed**: a completed matrix supports an
  evaluation claim, while benefit claims still depend on observed direction
  and uncertainty.

## Final Checklist

- [ ] Stage R implementation and exact triple tests pass remotely.
- [ ] Legacy NER behavior is unchanged.
- [ ] Relation calibration is completed and disclosed.
- [ ] Domain dev full-IE sanity passes.
- [ ] E/E-prime dropped entity and relation audits pass or are retained as
      explicit negative results.
- [ ] CLUENER support/glossary/RAG protocol is frozen and deduplicated.
- [ ] All 30 domain cells contain entity and relation metrics.
- [ ] All 30 CLUENER cells use complete labeled dev evaluation.
- [ ] All 60 reported cells have three-seed aggregates where specified.
- [ ] Paired uncertainty and multiple-comparison handling are reported.
- [ ] No unsupported positive claim enters the manuscript.
