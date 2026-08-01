# Minimum Full-IE Extension Tracker

**Date**: 2026-08-01

**Status semantics**:

- `PLANNED`: no execution authority.
- `PREPARED`: artifacts exist but the next gate is closed.
- `RUNNING`: allowed only under the exact recorded human gate.
- `DONE`: outputs are complete, hash-verified, and audited.
- `BLOCKED`: a declared stop condition fired.

Nothing in this tracker authorizes Python, data processing, prompt generation,
model/API calls, vLLM, GPU use, `domain_test` access, or any paper edit.

The `FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED`,
`FULL_IE_F3_CONFIG_PREP_APPROVED`, and
`FULL_IE_DOMAIN_DEV_SANITY_APPROVED` gates were explicitly granted and are
consumed. The blocked IE021 first attempt remains preserved. Under IE022,
human-revised A/B files were locked as `revised_v2`; a shared sentence-boundary
defect that treated semicolons as sentence terminators was diagnosed and covered
by a regression test. Final revalidation has zero structural errors and 20/20
valid pairs. Exact-directed file concordance is TP=24, FP=47, FN=20, precision
`0.338028`, recall `0.545455`, F1 `0.417391`; `PART_OF` F1 is only `0.246154`.
The user attested that both files are human-produced, but this post-feedback
result is not frozen-test formal IAA and does not establish high relation
agreement. F2 is disclosed and complete under its pre-specified structural
criterion. F3 configuration/resource preparation is complete and hash-audited.
F4a DDEV1/DDEV2 are also complete with limitations: exact RE remains very weak,
D has a `6%` relation parse-failure rate, E-prime is locally positive, and E is
negative. No CLUENER, final-evaluation, F5/F6, paper, or GitHub gate is open.

## Protocol and Implementation

| Run ID | Milestone | Purpose | Scope | Cells | Priority | Status | Gate / notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| IE000 | F0 | Confirm two-stage IE design | Plan only | 0 | MUST | DONE | Full-IE target and literal inventory confirmed |
| IE010 | F1 | Implement Stage R relation-only runner | Synthetic fixtures and legacy metadata only | 0 | MUST | DONE | Fixed prompt order, replay contract, deterministic skips, and future model gate |
| IE011 | F1 | Implement exact directed triple metrics | Synthetic fixtures | 0 | MUST | DONE | End-to-end exact key, type/FDR/coverage/conditional/zero-relation diagnostics |
| IE012 | F1 | Extend E/E-prime to relation atoms | Synthetic fixtures | 0 | MUST | DONE | Invalid output keeps atoms; entity drops cascade; legacy NER behavior preserved |
| IE013 | F1 | Implement aggregation and 60-cell manifest validation | Synthetic fixtures | 0 | MUST | DONE | Literal 30+30 inventory, hashes/statuses/arithmetic, three-seed mean/sample-SD |
| IE020 | F2 | Prepare non-test relation-calibration sheets | Existing fresh 20-text calibration set | 0 | MUST | DONE | A/B own locked entities only; 20+20 blank relation rows isolated and hash-audited |
| IE021 | F2 | Validate relation calibration | Exact directed endpoint/type triples | 0 | MUST | BLOCKED | 90 structural errors; 7/20 valid pairs; partial F1 0.454545 is not reportable; provenance unverified |
| IE022 | F2 | Revalidate human-revised relation calibration | Versioned `revised_v2` exact directed triples | 0 | MUST | DONE | 0 structural errors; 20/20 pairs; F1 0.417391; PART_OF F1 0.246154; not formal IAA |
| IE030 | F3 | Freeze domain dev configs | A-E-prime, K=5, seed42 | 6 | DONE | 16 runner configs + 12-cell matrix; all unauthorized and hash-locked |
| IE031 | F3 | Build CLUENER support bank and glossary | train_pool only | 0 | DONE | 30-record all-type bank; 61 support-only glossary entries |
| IE032 | F3 | Build/dedup CLUENER RAG corpus | labels-stripped train_pool | 0 | DONE | 9,584 rows; 89 removed by fixed 8-gram/0.80 blocklist |
| IE033 | F3 | Freeze CLUENER tune configs | A-E-prime, K=5, seed42 | 6 | DONE | 50-record all-type tune subset; no prompt artifacts |

### F3 Closeout (2026-07-31)

- Gate: `FULL_IE_F3_CONFIG_PREP_APPROVED`; AutoDL remained no-card (`No devices
  found`, `/dev/nvidia0` absent), with no vLLM/Qwen/extraction/verifier process.
- Resource package: support bank `30`, tune subset `50`, support-only glossary
  `61`, labels-stripped CLUENER RAG `9,584`; fixed 8-gram containment threshold
  `0.80` removed `89` rows (`30` exact support IDs, `34` tune overlaps, `24`
  CLUENER-dev text overlaps, `1` support overlap).
- Config package: `16` executable future runner YAMLs plus one `12`-cell run
  matrix (domain and CLUENER A/B/C/D/E/E-prime, K=5, seed42). Every config has
  `authorized=false` and `model_calls_allowed=false`; no final-evaluation path
  appears in the YAMLs and no prompt/per-query file was generated.
- The CLUENER official dev file was used only as a text-only deduplication
  blocklist; no labels, metrics, prompts, or tuning decisions were derived from
  it. `domain_test` was not read.
- Verification: F3 synthetic tests `5/5`, affected runner tests `9/9`, full
  AutoDL test suite `173/173`, independent F3 manifest validation `74` files.
- Report and manifest are under
  `backups/FULL_IE/f3_config_prep_20260731/`; report SHA256 is recorded in
  `docs/FULL_IE_CONFIG_PREP_20260731.md`.
- Cost: `0 CNY`. F3 creates no empirical result and does not change the `0/60`
  full-IE evidence count.

## Dev and Tune Gates

| Run ID | Milestone | Purpose | Dataset / split | Cells | Priority | Status | Gate / notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| DDEV1 | F4 | Relation-enabled A-D sanity | domain_dev50, K=5, seed42 | 4 | MUST | DONE | A-D exact RE F1 `0.056680/0.040404/0.039024/0.010989`; D parse failure `6%` |
| DDEV2 | F4 | Entity+relation verification sanity | domain_dev50 E/E-prime, K=5, seed42 | 2 | MUST | DONE | E-prime NER/RE F1 positive; E NER/RE F1 negative; full deletion audit retained |
| CDEV1 | F4 | Public NER A-D sanity | fixed CLUENER tune subset, K=5, seed42 | 4 | MUST | PLANNED | Later separate `FULL_IE_CLUENER_TUNE_SANITY_APPROVED` |
| CDEV2 | F4 | Public verifier E/E-prime sanity | fixed CLUENER tune subset, K=5, seed42 | 2 | MUST | PLANNED | Same CLUENER gate; entity atoms only |
| FREEZE | F5 | Lock final protocol | Prompts/configs/resources/metrics/seeds | 0 | MUST | PLANNED | Required before any final evaluation access |

### F4a Closeout (2026-08-01)

- Gate: `FULL_IE_DOMAIN_DEV_SANITY_APPROVED`; bounded to `domain_dev50`, K=5,
  seed42 DDEV1/DDEV2, and now consumed.
- Preserved v0 failure: strict A Stage R rejected `38/50` relation responses.
  The sole allowed dev revision changed only `drop_invalid_relations` to `true`;
  prompt, schema, model outputs, exact direction, and duplicate policy did not
  change. No second revision is allowed.
- DDEV1 NER F1 A/B/C/D: `0.527273/0.506135/0.523169/0.501548`. Exact RE F1:
  `0.056680/0.040404/0.039024/0.010989`. Aggregate RE parse failures are
  `7/200 = 3.5%`, but D is `3/50 = 6%` and fails the per-config `<5%` gate.
- The relation sanitizer removed `577` invalid atoms. No A-D configuration has
  a `HAS_METRIC` true positive. D is below C on both NER and RE F1, while its
  RAG path adds about `8.19 s/query` during Stage N.
- E-prime improves NER F1 `0.523169 -> 0.540816` and exact RE F1
  `0.039024 -> 0.051613`. Correct-drop rates are `65/81 = 80.25%` for entities
  and `50/50 = 100%` for unique relation drops; its local positive gate passes.
- E changes NER F1 `0.501548 -> 0.495479` and exact RE F1
  `0.010989 -> 0.000000`. Its drop audits pass (`68/93 = 73.12%` entities,
  `26/27 = 96.30%` relations), but the F1 gate fails; this is a mixed/negative
  result.
- Validation: targeted tests `5/5`, full AutoDL suite `178/178`; 1,403 backup
  files verified. Summary SHA256 is
  `c5e9df2c6a0c8d083670c64e604b2b881b23c33f3ac183a7d365433628d1309d`.
- Safety: `domain_test` was not read; CLUENER was not run; no paper or GitHub
  action occurred. Final mode was no-card with no vLLM/model/runner process.
- Cost: observable vLLM windows are about `46m23s`, approximately `2.1 CNY` at
  `2.7 CNY/hour`, but this is not the platform bill. The longer paid-mode
  envelope means actual cost may be higher; AutoDL billing is authoritative.
- These six dev sanity rows are not final reported cells. Matrix accounting
  remains `0/60`. Full report:
  `docs/FULL_IE_DOMAIN_DEV_SANITY_20260801.md`.
- Next planned gate: `FULL_IE_CLUENER_TUNE_SANITY_APPROVED` for CDEV1/CDEV2
  only. It is closed until explicitly granted.

## Domain Final Matrix: 30 Reported Cells

| Run ID | Milestone | System / variant | K | Seeds | Reported cells | Stage work | Status |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK5-A | F7 | A fixed-random | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | PLANNED |
| DK5-B | F7 | B kNN | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | PLANNED |
| DK5-C | F7 | C kNN + glossary | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | PLANNED |
| DK5-D | F7 | D C + RAG | 5 | 42/43/44 | 3 | Reuse Stage N/RAG evidence; add Stage R | PLANNED |
| DK5-E | F7 | E D + verification | 5 | 42/43/44 | 3 | Verify combined D Stage N+R output | PLANNED |
| DK5-EP | F7 | E-prime C + verification | 5 | 42/43/44 | 3 | Verify combined C Stage N+R output | PLANNED |
| DK1-A | F7 | A fixed-random | 1 | 42/43/44 | 3 | New Stage N + Stage R | PLANNED |
| DK1-E | F7 | E D + verification | 1 | 42/43/44 | 3 | New D Stage N + Stage R + verifier | PLANNED |
| DK10-A | F7 | A fixed-random | 10 | 42/43/44 | 3 | New Stage N + Stage R | PLANNED |
| DK10-E | F7 | E D + verification | 10 | 42/43/44 | 3 | New D Stage N + Stage R + verifier | PLANNED |
| **Domain total** |  |  |  |  | **30** | All rows report NER and exact RE |  |

## CLUENER Final Matrix: 30 Reported Cells

All rows use the complete labeled official dev split. C/D/E/E-prime use the
frozen support-derived glossary and labels-stripped, deduplicated train-pool
RAG corpus. There is no RE metric.

| Run ID | Milestone | System / variant | K | Seeds | Reported cells | Status |
| --- | --- | --- | ---: | --- | ---: | --- |
| CK5-A | F8 | A fixed-random | 5 | 42/43/44 | 3 | PLANNED |
| CK5-B | F8 | B kNN | 5 | 42/43/44 | 3 | PLANNED |
| CK5-C | F8 | C kNN + support glossary | 5 | 42/43/44 | 3 | PLANNED |
| CK5-D | F8 | D C + train-text RAG | 5 | 42/43/44 | 3 | PLANNED |
| CK5-E | F8 | E D + verification | 5 | 42/43/44 | 3 | PLANNED |
| CK5-EP | F8 | E-prime C + verification | 5 | 42/43/44 | 3 | PLANNED |
| CK1-A | F8 | A fixed-random | 1 | 42/43/44 | 3 | PLANNED |
| CK1-E | F8 | E D + verification | 1 | 42/43/44 | 3 | PLANNED |
| CK10-A | F8 | A fixed-random | 10 | 42/43/44 | 3 | PLANNED |
| CK10-E | F8 | E D + verification | 10 | 42/43/44 | 3 | PLANNED |
| **CLUENER total** |  |  |  |  | **30** |  |

## Aggregation and Paper Gate

| Run ID | Milestone | Purpose | Scope | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AGG1 | F9 | Validate all final cells | 60 reported cells | MUST | PLANNED | No missing rows; hashes and counts match |
| AGG2 | F9 | Aggregate mean/SD | Three seeds per cell | MUST | PLANNED | Preserve deterministic/near-deterministic behavior |
| AGG3 | F9 | Paired uncertainty | Pre-specified contrasts, 10k bootstrap | MUST | PLANNED | Holm adjustment if p-values are reported |
| AGG4 | F9 | Result-to-claim decision | NER, RE, CoVe, K, public NER | MUST | PLANNED | Positive claims depend on observed evidence |
| PAPER1 | F9 | Propagate verified evidence | Markdown/LaTeX only after separate approval | MUST | BLOCKED | No paper edit under this plan |

## Accounting Check

```text
Domain final cells   = 18 K=5 + 12 K-scan = 30
CLUENER final cells  = 18 K=5 + 12 K-scan = 30
Complete matrix      = 30 + 30 = 60
Existing full cells  = 0
Existing NER stages  = 12 (reusable only after adding Stage R)
Missing report cells = 48
```

## F1 Closeout

- AutoDL mode: GPU-free/no-card; `nvidia-smi -L` returned `No devices found`,
  `/dev/nvidia0` was absent, and no vLLM/Qwen/extraction/verifier process ran.
- Verification: 28 new full-IE synthetic tests and 38 focused legacy
  extraction/verification/schema tests passed (`66/66`).
- Safety audit: no `domain_test`, support/dev/test prompt artifact, model/API,
  vLLM, GPU, manuscript, frozen data, or GitHub synchronization was used.
- Sync audit: approved code/tests have identical local/remote SHA256 values;
  old NER core and regression-test SHA256 values remain unchanged.
- Cost: `0 CNY` paid GPU; platform paid resources were not used.
- Evidence accounting is unchanged: RE and relation-aware E/E-prime are
  implemented but not model-run or evaluated; complete full-IE cells remain
  `0/60` and the existing `12/60` are Stage N only.

## F2 Preparation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_PREP_APPROVED` was bounded to IE020 and
  is consumed. It did not authorize annotation or returned-file validation.
- Inputs: locked A/B fresh human entity CSV files and the coordinator map were
  verified against fixed SHA256 values; 20 texts aligned exactly.
- Outputs: A/B each have 20 independently ordered rows containing only their
  own locked entities, an index guide, and blank relation fields. Delivery
  directories exclude the other role and coordinator map.
- Verification: 6 preparation/audit synthetic tests and all 158 repository
  tests passed remotely; the real package audit passed with 40/40 relation rows
  blank and locked entity cells preserved.
- Backup: remote and local 10-file packages match SHA256; root manifest is
  `5d2c55c60e24a1cdec12335f567ab5457dd8ee24e1d111ed1692694a48a840a4`.
- Safety/cost: AutoDL was GPU-free; no `domain_test`, prompt, model/API, vLLM,
  paper, or GitHub action occurred. Paid GPU cost was `0 CNY`.
- Evidence accounting remains `0/60`; preparation is not relation evidence.
  The later annotation and validation gates do not change this accounting.

## F2 Validation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED` was bounded to
  returned-file validation and is consumed.
- Input integrity: A/B each contain 20 rows; all four read-only fields, row
  orders, entity hashes/counts, blind IDs, text hashes, and coordinator mapping
  are preserved.
- Stop condition: 90 hard errors comprise 70 cross-sentence relations, 18
  relation type/direction matrix violations, and 2 invalid `METRIC_SCOPE`
  uncertainty codes. IE021 is `BLOCKED`.
- Incomplete diagnostic: only 7 paired rows were structurally valid (TP=10,
  FP=15, FN=9, precision `0.400000`, recall `0.526316`, F1 `0.454545`). It is
  not a complete calibration score and must not enter paper evidence.
- Provenance: file validation cannot establish two independent humans or
  absence of AI/scripts. The newly untracked user file
  `p6_relation_annotate.py` was not read, executed, modified, or committed.
- Verification: 6/6 new synthetic tests and 164/164 repository tests passed on
  AutoDL no-card mode.
- Safety/cost: no `domain_test`, prompt, model/API, vLLM, GPU, paper, or GitHub
  action occurred; paid GPU cost was `0 CNY`.
- Evidence accounting remained `0/60` at IE021 closeout. That gate authorized
  no correction, reannotation, F3/F4, or paper action.

## F2 Revalidation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED` was bounded to
  version-locking and validating the human-revised non-test A/B files; it is
  consumed.
- Negative-result preservation: the IE021 input/report and the first revised
  revalidation output were retained. Nothing was deleted, overwritten, or
  filtered to manufacture a pass.
- Input lock: A revised SHA256 `579a1a36...a63fe3`; B revised SHA256
  `4acc4b05...24861f`; original blank sheets and coordinator map remained
  unchanged.
- Implementation diagnosis: the shared sentence helper incorrectly treated
  `；;` as sentence-final punctuation. This rejected four identical A/B
  relations inside one semicolon-delimited Chinese equipment list. The helper
  now uses true sentence-final punctuation/newlines; full-stop cross-sentence
  rejection remains covered.
- Final structure: zero hard errors and 20/20 complete valid pairs. A has 44
  relations, B has 71, 9/20 rows match exactly, and 11/20 contain disclosed
  disagreements.
- Exact-directed concordance: overall TP=24, FP=47, FN=20, P `0.338028`, R
  `0.545455`, F1 `0.417391`; `USES` F1 `0.650000`, `HAS_METRIC` F1 `0.600000`,
  and `PART_OF` F1 `0.246154`.
- Provenance/claim boundary: the user attested both files are human-produced.
  Because these are post-feedback revisions, the result remains file
  concordance rather than a new blind first-pass or frozen-test formal IAA.
  The low score weakens, rather than supports, a relation-quality claim.
- Verification: Stage R core tests `14/14`, relation-validator tests `7/7`, and
  the final AutoDL no-card repository suite `166/166` passed. Real
  `domain_test` was not read; similarly named test paths were temporary
  synthetic fixtures only.
- Successful artifact report SHA256 is
  `9fc15cf720f470b5f37366eb70fb1657eb42d52527e7859ebf44ee52ebb6bef8`;
  see `docs/FULL_IE_RELATION_CALIBRATION_REVALIDATION_20260731.md`.
- Safety/cost: no prompt, model/API, vLLM, GPU, paper, P6 user-script, or
  GitHub action occurred; paid GPU cost was `0 CNY`.
- Evidence accounting remained `0/60` at IE022 closeout. F3 and F4a later
  received their own bounded approvals and are recorded as complete above;
  F4b and all final-evaluation gates remain closed.
