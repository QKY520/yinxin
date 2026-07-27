# HANDOFF.md - New Conversation Handoff

Date: 2026-07-27
Workspace: `D:\yinsir`

This file is the latest operational state for a new Codex/agent session with no
chat history. Read these files before doing any project work:

1. `AGENTS.md` - durable repository, safety, and collaboration rules.
2. `AGENT_PLAYBOOK.md` - authoritative machine execution contract.
3. `实验实施指导文档_综合版.md` - human-facing rationale and operational guide.
4. This `HANDOFF.md` - live status and next step.

If older docs conflict with this file on status chronology, this file is newer.
Hard rules in `AGENTS.md` and `AGENT_PLAYBOOK.md` still apply.

## 1. What We Are Doing Now

We are preparing a practical SCI-Q4-oriented applied/engineering paper about
few-shot Chinese equipment-domain NER using a reproducible local-LLM extraction
pipeline.

Current task: **GPU-free paper writing and pre-submission preparation in
Markdown**. `P6-QA1R` non-test calibration validation remains `blocked`, and
the approved coordinator reconciliation is complete. The human locked
guideline v4 on 2026-07-27 under `P6_QA1R_GUIDELINE_V4_LOCK_APPROVED` without
changing or adjudicating submitted labels. A fresh 20-row non-test calibration
package was then prepared and verified under
`P6_QA1R_FRESH_CALIBRATION_PREP_APPROVED`. It remains completely blank; the
human then approved `P6_QA1R_FRESH_CALIBRATION_ANNOTATION_APPROVED`. The two
role-separated directories were completed by two humans, and the human
coordinator explicitly confirmed their provenance. Validation under
`P6_QA1R_FRESH_CALIBRATION_VALIDATION_APPROVED` is complete: strict fresh
human-calibration F1 is exactly `0.8000`, with no structural errors. This meets
the original minimum `>=0.80` but not the conservative v4 target `>=0.85`.
The project is stopped before the result-policy decision, formal test
re-annotation, adjudication, v2 freezing, or re-evaluation.

Current editable paper draft:

- `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`

All generated `.docx` files were deleted on 2026-07-25 at the user's request
because of rendering/encoding problems. Future writing defaults to UTF-8
Markdown unless the user explicitly asks otherwise.

No paid GPU, vLLM launch, dry-run, model call, frozen-test prompt generation,
further calibration editing/comparison, re-annotation, adjudication,
frozen-data correction, re-evaluation, or new experiment is currently
authorized. The fresh annotation and validation gates are consumed.

## 2. What Is Already Completed

### P0 - Environment

Complete.

- AutoDL environment was set up.
- Project venv and required imports passed previously.
- Four fixed model directories were downloaded and structurally checked:
  Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct-AWQ, BGE-M3, and
  bge-reranker-v2-m3.
- P0 backup was created and hash-verified.
- The human confirmed the P0 image was saved.

### P1 - Public Data

Complete.

- CLUENER, Few-NERD SUP, DuIE 2.0, and CMNEE were downloaded and normalized.
- 12 official split JSONL files were generated.
- K=1/5/10 public support files were generated with seed 42.
- Loader/span checks passed.
- Important limitation: public CLUENER and DuIE test files have no gold labels.
  They must never be evaluated as all-negative gold.

### P2 - Self-Built Domain Data

Structurally complete and frozen as version `v1`; independent human-gold quality
evidence is not complete.

- 400 public equipment-domain candidates were collected:
  Baidu Baike 7, patent 84, CMNEE 309.
- Schema `p2-schema-draft-v1` and 10 synthetic examples were approved.
- QAonMilitaryKG distant supervision had low coverage:
  15/400 records, 23 EQUIPMENT suggestions, 0 relations.
- Qwen2.5-14B-AWQ proposal workflow, machine/rule-assisted review, nominal
  adjudication, and freeze were completed for the approved 250-record route.
- Final frozen split:
  - `domain_support.jsonl`: 30 rows;
  - `domain_dev.jsonl`: 50 rows;
  - `domain_test.jsonl`: 170 rows;
  - `domain_rag_corpus.jsonl`: 230 rows;
  - `data/FROZEN` and `logs/dedup.json` exist in the remote artifact set.
- Important hashes:
  - `domain_gold_250.jsonl`:
    `fb183c733d328124c35e527872eb9cb4ea839fdf7bea1059c2313e3ea207acdc`;
  - `domain_support.jsonl`:
    `9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a`;
  - `domain_dev.jsonl`:
    `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`;
  - `domain_test.jsonl`:
    `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`.
- Local P2 gold backup:
  `backups/P2/p2_domain_gold_freeze_20260722.tar.gz`;
  SHA256 `a3711e2af4179d8398d8d497827ff703b1cfa4a8b0c05ea4de47837b9329ec3f`.
- Quality caveat: the old `0.9909` agreement came from machine/rule-generated
  pseudo A/B files and is not valid human IAA. Within the 170-row test source
  map, 61 rows are tagged `adjudicated_double_annotation` and 109 are tagged
  `annotator_a_single_annotation`; those names describe the old build path and
  do not prove independent human annotation.

### P3/P4 - Domain-Dev Sanity

Complete enough for the current paper route.

All model-run cells below are `domain_dev50`, K=5, seed 42, Qwen2.5-7B via
vLLM.

| Config | Main change | Precision | Recall | F1 | TP/FP/FN | Verdict |
| --- | --- | ---: | ---: | ---: | --- | --- |
| A | fixed random, no glossary/RAG/verif | 0.4914 | 0.5570 | 0.5221 | 171/177/136 | accepted baseline |
| B | kNN examples | 0.4767 | 0.5342 | 0.5038 | 164/180/143 | negative |
| C | B replay + glossary | 0.4722 | 0.5537 | 0.5097 | 170/190/137 | mixed |
| D | C + RAG rerank top-3 | 0.5211 | 0.5635 | 0.5415 | 173/159/134 | positive |
| E v1 | D + verifier v1 | 0.6173 | 0.3257 | 0.4264 | 100/62/207 | overkill |
| E v2 | D + verifier v2 | 0.5266 | 0.5472 | 0.5367 | 168/151/139 | mixed |

Dev interpretation: D(RAG) was the strongest positive sanity result. Verifier
variants were negative or mixed and are not recommended for more paid GPU by
default.

### P5 - Bounded Domain-Test Evidence

Complete for a narrow paper claim, not complete as the original full P5 matrix.

Completed scope:

- Dataset: `domain_test`
- K: 5
- Seeds: 42, 43, 44
- Configs:
  - A: fixed random;
  - B: kNN examples;
  - C: kNN + glossary;
  - D: kNN + glossary + RAG.
- Not run/completed: E, E-prime, CLUENER, K=1, K=10, more seeds, full public
  benchmark matrix.

All 12 completed per-query/summary files under `results/p5/` were verified:
170 rows per cell, 0 parse failures, SHA256 matched during the prior audit.

Three-seed domain-test NER results:

| Config | F1 mean +/- std | FP mean +/- std | Main reading |
| --- | ---: | ---: | --- |
| A | `0.534645 +/- 0.004375` | `613.3 +/- 88.8` | baseline |
| B | `0.555169 +/- 0.000880` | `573.7 +/- 1.2` | kNN improves F1 and lowers FP |
| C | `0.568858 +/- 0.000769` | `584.0 +/- 0.0` | best F1/recall |
| D | `0.565764 +/- 0.000000` | `529.0 +/- 0.0` | best precision and lowest FP |

Clean deltas:

- `B - A`: +0.020524 F1 and about -39.7 FP.
- `C - B`: +0.013689 F1 and about +10.3 FP.
- `D - C`: -0.003094 F1, but about -55.0 FP.
- `D - A`: +0.031119 F1 and about -84.3 FP.

Accepted wording: **C and D are near-tied on F1; C is marginally ahead on
recall/F1, while D is clearly ahead on precision and false-positive reduction.
Do not write that C significantly or substantially beats D.**

P5 paid run note:

- The replication paid vLLM window was approximately
  2026-07-24 18:16:34-19:27:50 CST.
- Estimated cost was about 3.2 CNY at 2.7 CNY/hour.
- vLLM was stopped after the run and GPU memory was verified at 0 MiB.

### P6-QA0 - Frozen-Gold Audit Preparation

Complete in AutoDL GPU-free mode; no human annotation has started.

- Added `scripts/prepare_p6_qa0_blind_annotation.py` and four focused unit
  tests. All tests passed remotely in GPU-free mode.
- The script required the exact frozen test SHA256 and P2 `FROZEN` marker,
  matched all test text hashes to the source map, and refused existing-output
  overwrite.
- Generated two independently shuffled 170-row UTF-8 BOM CSVs. Each contains
  only `blind_id,text,entities_json,notes`; both annotation fields are blank.
- Seeds: A `2026072501`, B `2026072502`; orders and blind IDs differ.
- Generated a 170-row coordinator-only blind-ID map and an atomic manifest.
- Remote package:
  `/root/autodl-tmp/backup/p6/p6_qa0_blind_annotation_20260725/`.
- Local ignored backup:
  `backups/P6/p6_qa0_blind_annotation_20260725/`.
- Output SHA256:
  - A CSV: `3a36082631b45339d8b8e6ecd724ca3bbb7f74196531339ddb4621c4a72e1171`;
  - B CSV: `39b5ee7755ee48bd1c0d762e1ecdfd8c6a4251bdf8a0e1cf82a4c7ad149ae685`;
  - coordinator map: `d39d2252400cdc17a37eef78ed3a276c1f86c804d65e03f43cef31d752e38eb1`;
  - manifest: `45fa9fd6cb7886ad7b7bc58078de4391b57e3233bd41a9960be1368a88695451`.
- Full protocol and future gates:
  `docs/P6_QA0_FROZEN_GOLD_AUDIT_PLAN_20260725.md`.
- Cost impact: 0 paid-GPU CNY; no model/vLLM/dry-run activity. Post-generation
  check still reported GPU-free/no devices.

### P6-QA2 - Submitted Annotation Validation

Complete and blocked in AutoDL GPU-free mode.

- Submitted completed hashes:
  - A: `f07a650688c9cafcf4d16f5be906a0f45a3623838994cc9af2954385eb2183b7`;
  - B: `90e8e2458de3dd1f847a730759a353efb0a493bbbe385bbaa88fecf6acccd8ef`.
- Blind IDs, 170 texts, and text hashes matched the QA0 coordinator map.
- Structural result: 19 A rows not sorted, 2 B `entities_json` fields blank,
  and 181 unresolved repeated-mention candidates (180 A, 1 B).
- Only 149/170 strict pairs entered diagnostic comparison: exact file F1
  `0.557265`, 19 exact rows, 130 disagreement rows.
- Diagnostic per-type F1: EQUIPMENT `0.645852`, MODULE `0.548673`,
  TECH_SCHEME `0.032967`; METRIC was empty in both valid subsets and is not an
  interpretable 1.0 result.
- Formal human IAA is `null`. Repository provenance files show one shared
  `ANNO` dictionary and one `process_rows` function writing both A/B completed
  sheets. Later edits cannot restore independent blank-start provenance.
- Validator and four focused tests:
  `scripts/validate_p6_qa2_annotations.py` and
  `tests/test_validate_p6_qa2_annotations.py`; tests passed remotely.
- Full report: `docs/P6_QA2_ANNOTATION_VALIDATION_20260726.md`.
- Raw coordinator-only output:
  `/root/autodl-tmp/backup/p6/p6_qa2_annotation_validation_20260726/` and
  `backups/P6/p6_qa2_annotation_validation_20260726/`.
- Validation report SHA256:
  `aa614ad12cf9b7babf0ebb0e950ec44b960cb259226027142c7a0180acef6292`.
- No old gold, predictions, prompts, models, vLLM, or paid GPU were used; no
  labels were modified. Cost impact: 0 paid-GPU CNY.

### P6-QA1R - Diagnostic Repair And Non-Test Calibration Prep

Complete in AutoDL GPU-free mode. At the end of this preparation step, human
calibration had not yet started; the subsequently submitted calibration files
and their validation are recorded in the next subsection.

- Existing provenance-invalid QA2 files were used only as diagnostic inputs.
  They remain ineligible for human IAA or adjudication.
- Entity disagreement taxonomy across 130 rows:
  - same-boundary type conflicts: 127 instances / 60 rows;
  - same-type overlapping-boundary conflicts: 40 / 28;
  - overlapping boundary-and-type conflicts: 10 / 10;
  - unmatched A/B entities: 158 / 265.
- The dominant paired confusion was `EQUIPMENT -> TECH_SCHEME` with 104
  instances. This, 180 A repeated-mention warnings, and an empty METRIC class
  drove the revised operational rules.
- Added diagnostic and calibration-prep scripts with seven focused tests; all
  tests passed remotely:
  - `scripts/analyze_p6_qa2_disagreements.py`;
  - `scripts/prepare_p6_qa1r_calibration.py`;
  - corresponding tests under `tests/`.
- Added guideline and report:
  - `docs/P6_QA1R_ANNOTATION_GUIDELINE_V3_20260726.md`;
  - `docs/P6_QA1R_DIAGNOSIS_AND_CALIBRATION_20260726.md`.
- Prepared 24 text-only domain-dev calibration rows: six each for METRIC,
  TECH_SCHEME, EQUIPMENT/MODULE, and repeated-mention risk. A/B orders differ,
  annotation fields are blank, and no old dev labels, test gold, predictions,
  or coordinator IDs were exported.
- Coordinator-only diagnosis:
  `/root/autodl-tmp/backup/p6/p6_qa1r_diagnosis_20260726/` and
  `backups/P6/p6_qa1r_diagnosis_20260726/`.
- Calibration package:
  `/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726/` and
  `backups/P6/p6_qa1r_calibration_20260726/`.
- Frozen `domain_test.jsonl` and `FROZEN` hashes remained unchanged; the final
  server check still reported no GPU devices. Cost impact: 0 paid-GPU CNY.

### P6-QA1R - Submitted Non-Test Calibration Validation

Complete and blocked in AutoDL GPU-free mode.

- Completed input hashes:
  - A: `36613af484210ea7b916e744e1785b37ee5c47ed7bf41149ef5ac19af230bb0a`;
  - B: `9017bf65c8bd5e02a529bdef73f0ff845edc46d4471a84d80bb72615fc7aa8c7`.
- A/B each contained 24 rows; blind IDs, texts, hashes, blank sheets, and the
  coordinator map aligned exactly.
- Five B rows had `ENTITIES_NOT_SORTED`; 29 B repeated-mention reviews blocked
  the gate; four duplicate uncertainty codes were warnings.
- Strict 19-row concordance: A/B entities 188/140, 100 exact matches,
  P/R/F1 `0.7143/0.5319/0.6098`, and 1/19 exact rows.
- Because all hard errors were ordering only, a secondary non-repair diagnostic
  used all 24 rows order-insensitively: A/B entities 243/197, 142 exact matches,
  P/R/F1 `0.7208/0.5844/0.6455`, and 1/24 exact rows.
- Secondary per-type F1: EQUIPMENT `0.7081`, MODULE `0.5896`, TECH_SCHEME
  `0.3200`, and METRIC `0.7879`.
- The `0.6455` diagnostic is `0.2045` below the `0.85` calibration target.
  `formal_human_iaa` remains `null`; this calibration is not formal test IAA.
- Validator and six focused tests:
  `scripts/validate_p6_qa1r_calibration.py` and
  `tests/test_validate_p6_qa1r_calibration.py`; tests passed remotely.
- Full report: `docs/P6_QA1R_CALIBRATION_VALIDATION_20260727.md`.
- Final coordinator-only output:
  `/root/autodl-tmp/backup/p6/p6_qa1r_calibration_validation_20260727_r2/`
  and `backups/P6/p6_qa1r_calibration_validation_20260727_r2/`.
- No dev gold, frozen test, predictions, prompts, model calls, vLLM, paid GPU,
  or label repair was used. Frozen hashes remained unchanged.

### P6-QA1R - Guideline Reconciliation

Complete in AutoDL GPU-free mode; guideline v4 is locked.

- Added a locked, read-only reconciliation analyzer and six focused tests:
  - `scripts/analyze_p6_qa1r_calibration_reconciliation.py`;
  - `tests/test_analyze_p6_qa1r_calibration_reconciliation.py`.
- The analysis covered all 24 calibration pairs order-insensitively without
  writing back A/B labels: 243/197 A/B entities, 142 exact matches, 1 exact row,
  23 disagreement rows, and 119 classified events.
- Rule signals: scope/include-exclude 68, same-boundary type 26, repeated mention
  14, boundary 8, and boundary-plus-type 3.
- Same-boundary type directions were `EQUIPMENT->MODULE` 15,
  `TECH_SCHEME->EQUIPMENT` 8, and `TECH_SCHEME->MODULE` 3. Directions describe
  file differences, not gold.
- Prepared and reconciled:
  - `docs/P6_QA1R_GUIDELINE_RECONCILIATION_20260727.md`;
  - `docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md`;
  - `docs/P6_QA1R_GUIDELINE_V4_LOCK_RECORD_20260727.md`.
- The human approved `P6_QA1R_GUIDELINE_V4_LOCK_APPROVED` on 2026-07-27.
  The locked guide SHA256 is
  `a15289cd0f45bc23a0ce9d981db24745b814cfb94c6b03687e60a13b81b6ca80`.
  The lock-record SHA256 is
  `870ae640ad23070ecce63ae475c52da8f93081cb6a203a33908a65071a54d500`.
  Locking changed only version/status and future-gate wording; annotation
  decision rules were not substantively rewritten.
- Lock artifacts are mirrored under
  `/root/autodl-tmp/backup/p6/p6_qa1r_guideline_v4_lock_20260727/` and
  `backups/P6/p6_qa1r_guideline_v4_lock_20260727/`.
- No calibration sheet, label, gold, prediction, prompt, or model output was
  created or changed. The server remained GPU-free; cost impact was 0 CNY.
- Prepared separate role-specific reading/operation instructions for the two
  future annotators:
  - `docs/P6_QA1R_ANNOTATOR_A_INSTRUCTIONS_V4_20260727.md`;
  - `docs/P6_QA1R_ANNOTATOR_B_INSTRUCTIONS_V4_20260727.md`.
  A/B SHA256 are respectively
  `5f0cf56819a10e76e0a2639257b8c051af213e4ee2dfe6accdbf077509e9b136`
  and
  `432acf0f19315e9eb089726126c33aabc9e7830d2fe7ea243078c4f3ea180c65`.
  These files contain no calibration text or answer and do not authorize
  calibration preparation or human annotation.
- Instruction backups are under
  `/root/autodl-tmp/backup/p6/p6_qa1r_annotator_instructions_v4_20260727/`
  and `backups/P6/p6_qa1r_annotator_instructions_v4_20260727/`.
- Final coordinator-only output:
  `/root/autodl-tmp/backup/p6/p6_qa1r_guideline_reconciliation_20260727_r2/`
  and `backups/P6/p6_qa1r_guideline_reconciliation_20260727_r2/`.
- Final summary SHA256:
  `cf0b109b80667464aeb4f0e6b4a7fa5fc8c78b5b4966a8408e1654e0778fc115`.
- The 24 rows are retired as teaching/reconciliation material. They were not
  adjudicated or rescored and cannot become a new independent calibration.
- No dev/test gold, predictions, prompts, model calls, new calibration material,
  vLLM, paid GPU, or label changes were used. Frozen hashes remained unchanged.

### P6-QA1R - Old-24 V4 Rescore Diagnostic

Complete and still invalid for fresh independent calibration.

- User-submitted A/B rescore hashes were
  `2a128744bd3b8508d65555706fc7c8a1d4692c9f761b2d57d7fedc9ccb5698d5`
  and `8c49d04b4636835942c929fa91e1c56d3e41c95ebc4ace70cd40759052209bcd`.
- Both reused the retired 24 texts. Their scripts expanded all occurrences and
  resolved overlaps before writing the CSVs, so the outputs are not valid
  evidence of a fresh, direct, mutually blind human round.
- Structure was clean, but exact file concordance was only `0.814229`: 238/268
  A/B entities, 206 exact matches, and 3/24 exact rows. Per-type F1 was
  EQUIPMENT `0.7835`, MODULE `0.8421`, TECH_SCHEME `0.4000`, and METRIC
  `0.8889`.
- This exceeds `0.80` numerically but misses the locked calibration target
  `0.85`; more importantly, `formal_human_iaa` remains `null` because the
  provenance and fresh-set requirements fail.
- Diagnostic output is under
  `/root/autodl-tmp/backup/p6/p6_qa1r_old24_v4_rescore_diagnostic_20260727_r1/`
  and `backups/P6/p6_qa1r_old24_v4_rescore_diagnostic_20260727_r1/`.

### P6-QA1R - Fresh Calibration Preparation

Complete in AutoDL GPU-free mode; human annotation has not started.

- Added `scripts/prepare_p6_qa1r_fresh_calibration.py` and four focused tests.
  Together with three old-preparer regression tests, all seven passed remotely.
- The locked old coordinator map excluded all 24 retired text hashes from the
  50-row domain-dev file. Of the 26 unused rows, 20 were selected and six were
  preserved as coordinator-only reserve.
- Selection seed `2026072701` assigned five unique texts to each text-only risk
  bucket: METRIC, TECH_SCHEME, EQUIPMENT_MODULE, and REPEATED_MENTION.
- A/B seeds `2026072702/2026072703` produced different orders and new blind-ID
  prefixes `P6FRESH-A/B`. All annotation fields are blank.
- A/B delivery directories are physically separated and contain only the role's
  blank CSV, role-specific instructions, locked v4 guideline, and delivery
  manifest. Coordinator and reserve maps are outside both delivery directories.
- A/B blank-sheet SHA256 are
  `df8b99c99b83ecbe71b38b352d584fd1e0dc67df93ba4b1a9c347c14e984c89c`
  and `b7e7df0c7331c1af379cda8e01c6287c8de2e644d82758e170ad3c26699c6ff1`.
- Coordinator-map, reserve-map, and root-manifest SHA256 are respectively
  `6a902ab6e2063b52c1d8103cf777ed25dc2def31371a3f26866f51d3d9664e18`,
  `20fe19da3911ad56d478e23c32c021f6fb3c5b340bf784d72963b6d88f228c9b`,
  and `bc404d4aeb6c2cab1c303ac063f9fdd43b950a587787cc222dcabbc4a9adba00`.
- A full reload verified blank fields, A/B/map alignment, distinct order,
  retired overlap 0, delivery separation, and the exact 24+20+6 partition.
- Remote/local package:
  `/root/autodl-tmp/backup/p6/p6_qa1r_fresh_calibration_20260727/` and
  `backups/P6/p6_qa1r_fresh_calibration_20260727/`.
- Full report: `docs/P6_QA1R_FRESH_CALIBRATION_PREPARATION_20260727.md`.
- No test, prediction, prompt, model, vLLM, paid GPU, gold change, or annotation
  activity occurred. Cost impact was 0 CNY.
- The human subsequently approved
  `P6_QA1R_FRESH_CALIBRATION_ANNOTATION_APPROVED` on 2026-07-27. Only the two
  role-separated delivery directories may be distributed; coordinator
  comparison remains unauthorized until both completed files are returned and
  hash-locked.
- Annotation start/return protocol:
  `docs/P6_QA1R_FRESH_CALIBRATION_ANNOTATION_START_20260727.md`.

### P6-QA1R - Fresh Human Calibration Validation

Complete in AutoDL GPU-free mode; no labels were changed.

- The coordinator explicitly confirmed that the final A/B files contain two
  human annotation results. Locked completed SHA256 are
  `6906142d5894c3a4f1332bed326258b4f9c35958baa17f8e8475339b435f8877`
  and `40428a8ed642685dd7940c60e3dc08af929dcaa4e71c0b7530e89eaa7dbb732e`.
- All 20 pairs passed structure: zero hard errors, zero blocking reviews, and
  all four types covered by both annotators.
- A/B entities were 175/220 with 158 exact matches. Precision/recall/F1 were
  `0.718182/0.902857/0.800000`; 5/20 rows were exactly equal and 15 disagreed.
- Per-type F1: EQUIPMENT `0.728261`, MODULE `0.898876`, TECH_SCHEME `0.153846`,
  and METRIC `1.000000`.
- The original minimum `>=0.80` is met exactly. The conservative v4 target
  `>=0.85` is not met, so the automatic validator status is still `blocked`.
- This is valid fresh human calibration agreement, not frozen-test formal IAA;
  `formal_test_iaa` remains `null`.
- Final output:
  `/root/autodl-tmp/backup/p6/p6_qa1r_fresh_calibration_validation_20260727_r2/`
  and `backups/P6/p6_qa1r_fresh_calibration_validation_20260727_r2/`.
- Full report: `docs/P6_QA1R_FRESH_CALIBRATION_VALIDATION_20260727.md`.
- No test/gold/prediction/model activity occurred; frozen hashes remained
  unchanged and cost impact was 0 CNY.

## 3. Current Claim Boundary

Result-to-claim verdict: `partial`.

Supported claim:

> In a frozen low-label Chinese equipment-domain NER setting, kNN
> demonstrations and glossary injection improve entity extraction F1, while RAG
> evidence preserves near-tied F1 and improves precision / reduces
> false-positive entity predictions.

This result statement is conditional on the current frozen `v1` labels. Until
true double annotation and blind adjudication are complete, the paper must not
claim independently human-annotated gold, valid human IAA, or a fully
quality-controlled dataset contribution.

Not supported by current evidence:

- relation extraction success;
- CoVe/self-verification improvement;
- public benchmark generalization;
- K=1/K=10 robustness;
- full A..E-prime ablation matrix;
- supervised-SOTA-style claims;
- any claim that C significantly beats D.

Paper positioning:

- Main task: NER.
- RE: auxiliary background only unless new dev-first evidence is created later.
- Contribution style: applied/reproducible engineering pipeline plus small
  equipment-domain dataset and honest ablation evidence.
- Target: one-month SCI-Q4-oriented manuscript route, Chinese draft first and
  then English SCI manuscript.

## 4. Current Paper And Review Artifacts

Use these as the paper-facing evidence base:

- `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`
- `docs/RESULT_TO_CLAIM_P5_DOMAIN_20260725.md`
- `docs/P5_DOMAIN_PAPER_EVIDENCE_20260725.md`
- `docs/P5_PAPER_REVIEW_AUDIT_20260725.md`
- `docs/P5_PAPER_P0_REVIEW_FEEDBACK_20260725.md`
- `docs/P6_QA0_FROZEN_GOLD_AUDIT_PLAN_20260725.md`
- `docs/P6_QA2_ANNOTATION_VALIDATION_20260726.md`
- `docs/P6_QA1R_ANNOTATION_GUIDELINE_V3_20260726.md`
- `docs/P6_QA1R_DIAGNOSIS_AND_CALIBRATION_20260726.md`
- `docs/P6_QA1R_CALIBRATION_VALIDATION_20260727.md`
- `docs/P6_QA1R_GUIDELINE_RECONCILIATION_20260727.md`
- `docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md`
- `docs/P6_QA1R_GUIDELINE_V4_LOCK_RECORD_20260727.md`
- `docs/P6_QA1R_ANNOTATOR_A_INSTRUCTIONS_V4_20260727.md`
- `docs/P6_QA1R_ANNOTATOR_B_INSTRUCTIONS_V4_20260727.md`
- `docs/P6_QA1R_FRESH_CALIBRATION_PREPARATION_20260727.md`
- `docs/P6_QA1R_FRESH_CALIBRATION_ANNOTATION_START_20260727.md`
- `docs/P6_QA1R_FRESH_CALIBRATION_VALIDATION_20260727.md`
- `findings.md`
- `logs/p5_c_vs_d_fp_qualitative_20260725.json`
- `logs/p5_c_vs_d_fp_qualitative_20260725.csv`

P0 paper repair already completed:

- Added variance explanation: A has fixed-random example-selection noise;
  B/C/D use kNN/replay, so variance is much smaller.
- Added C-vs-D qualitative FP analysis:
  - D removes/avoids 181 C-only false positives;
  - D introduces 126 new false positives;
  - net FP reduction is 55;
  - major categories: unsupported entity 84, type/overlap 34, short alias/code
    25, boundary error 24, metric fragment 14.

## 5. Non-Negotiable Execution Rules

- Never run project Python locally on Windows.
- Windows `D:\yinsir` is only for editing, Git, SSH/SCP, documentation, and
  lightweight artifact checks.
- All Python, tests, data processing, inference, evaluation, and aggregation
  must run on AutoDL through SSH alias `autodl-paper`.
- Use AutoDL GPU-free/no-card mode for current work.
- Use paid GPU only for model inference/training and only after explicit human
  approval for one bounded step.
- After every GPU phase: stop vLLM, verify GPU memory returns to 0 MiB, back up,
  sync lightweight artifacts to `D:\yinsir`, report cost, and remind the human
  to shut down or switch to no-card mode.
- Never use `domain_test` for prompt tuning, glossary tuning, RAG tuning,
  threshold changes, or verification tuning.
- Do not run E/E-prime, CLUENER, K=1/K=10, full P5, more seeds, dry-runs, model
  calls, or new `domain_test` prompt generation without a new explicit gate.
- Do not distribute any coordinator map to annotators. The prior 24-row human
  calibration gate is consumed; do not edit or rescore those same rows as a new
  independent round.
- Guideline v4 is locked. Do not use the lock gate to generate or start a
  fresh calibration round; that requires
  `P6_QA1R_FRESH_CALIBRATION_PREP_APPROVED`.
- Fresh A/B annotation and validation are complete. Never edit these submitted
  files and recompute them to improve `0.8000`; preserve all 15 disagreement
  rows. Do not call this calibration number frozen-test formal IAA.
- Do not treat the current A/B completed files or their `0.5573` diagnostic as
  human IAA. Do not repair them into an adjudication input; independence was
  already lost through a shared generation script.
- Calibration uses domain-dev text only and is not formal test IAA. Existing
  domain-dev labels are not calibration answers and must not be shown to the
  two annotators.
- Never overwrite frozen `v1`. Any corrected gold must be independently
  adjudicated, versioned as `v2`, re-frozen, and assigned new hashes.
- Preserve negative and mixed results; do not rerun them away.
- The real AutoDL host/port/passwords live only in the user's local SSH config.
  Use only the alias `autodl-paper` in docs and commands.

## 6. Repo And Machine Notes

Local:

- Workspace: `D:\yinsir`
- Branch: `main`
- Git remote: `https://github.com/QKY520/yinxin.git`
- Git identity for this repo: `yly <714520833@qq.com>`
- Calibration-validation commit:
  `fcd1556 p6: validate blocked calibration round`.
- QA1R diagnosis/calibration-prep commit:
  `f8162ce p6: prepare annotation agreement recovery`.
- QA2 implementation commit:
  `6690d92 p6: record blocked annotation QA2`.
- Previous QA0 commit:
  `a39a5a2 p6: prepare blinded frozen-gold audit`.
- GitHub push attempts through 2026-07-27 still failed because the local proxy
  `127.0.0.1` could not connect. AutoDL SSH is working, so QA2 code,
  documentation, tests, and lightweight artifacts were synced through the
  `autodl-paper` alias. The local commits remain unpushed until GitHub
  connectivity is restored.

Remote:

- SSH alias: `autodl-paper`
- Remote code: `/root/project`
- Remote data/model/backup root: `/root/autodl-tmp`
- Project venv: `/root/autodl-tmp/venvs/equipment-ie`
- Current Git HEAD before manual QA0 sync: `863c701`; the remote worktree has
  the final QA0 files copied from local because GitHub sync is unavailable.
- Last verified mode: GPU-free/no-card (`No devices found`). Confirm again
  before doing anything remote.

Useful no-Python status command:

```bash
ssh autodl-paper 'cd /root/project && git rev-parse --short HEAD && git status --short && (nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo GPU_FREE_OR_NVIDIA_SMI_UNAVAILABLE)'
```

## 7. Recommended Next Step

The current decision is whether to accept the original minimum `0.80` and plan
a formal test audit, or to retain the conservative v4 target `0.85` and perform
new guideline/text work. The SCI-Q4/time-oriented recommendation is to accept
the honestly reported minimum while explicitly retaining the TECH_SCHEME
limitation, then prepare only a GPU-free formal-audit plan. A bounded approval
for that route is:

```text
P6_QA1R_ACCEPT_080_MINIMUM_AND_PLAN_FORMAL_AUDIT_APPROVED
```

That gate would authorize planning only. It would not authorize reading or
changing frozen test, generating model prompts, adjudication, re-scoring,
model calls, or paid GPU.

Fresh test re-annotation, adjudication, frozen-data changes, model calls, and
re-evaluation remain later bounded steps.

In parallel, GPU-free manuscript work may continue only with conservative
wording: the current results are conditional on frozen `v1` labels, C and D are
near-tied on F1, and no human-IAA or quality-controlled-human-gold claim is
currently allowed.

## 8. Lessons Worth Remembering

- The project is now paper-first, not experiment-first.
- The experiment is basically complete only for the narrow domain NER claim; it
  is not a complete full-matrix IE paper.
- Structurally frozen data is not automatically publication-grade human gold.
  The `0.9909` pseudo-IAA must never be cited as human agreement.
- True A/B annotation must start from blank text, remain mutually blind, and
  include every explicit repeated mention. An agent cannot substitute for a
  human annotator or human adjudicator when the paper claims human gold.
- A shared annotation dictionary that writes both A and B invalidates human
  independence even if one file is edited afterward. File agreement is not
  annotation provenance.
- Low agreement must be repaired through non-test calibration and clearer
  operational rules, not by editing labels to reach a threshold. The present
  diagnosis found physical-system versus TECH_SCHEME confusion, repeated
  mention omissions, and complete METRIC under-coverage as the main risks.
- The first v3 calibration round also failed: order-insensitive F1 `0.6455`,
  with TECH_SCHEME F1 `0.3200`, MODULE F1 `0.5896`, and 29 repeated-mention
  reviews. Discuss it to improve v4, then use a fresh unused calibration set;
  never relabel the same 24 rows and call the new score independent agreement.
- Reapplying v4 to those same retired 24 rows yielded clean file concordance
  `0.8142`, but it remains invalid for fresh human calibration and exposed
  TECH_SCHEME F1 `0.4000`. Familiar items plus scripts that expand mentions or
  resolve overlaps cannot establish independent-human provenance.
- The genuinely fresh 20-row human calibration reached exact micro-F1 `0.8000`
  with perfect METRIC and strong MODULE agreement, but TECH_SCHEME F1 remained
  only `0.1538`. Meeting the overall minimum does not erase this class-specific
  limitation or create formal-test IAA.
- Reconciliation found 119 events across 23/24 rows. The dominant fix is not a
  looser metric; it is an explicit inclusion/exclusion policy, object-versus-
  method decision order, evidence-based EQUIPMENT/MODULE role, alias role
  persistence, full metric/model boundaries, and per-annotator preflight.
- Old frozen `v1` must be preserved. Any correction is a new `v2` with blind
  adjudication, new hashes, and uniform re-scoring only after a later gate.
- C and D are a near-tie on F1. D's value is FP/precision reduction, not a large
  F1 gain.
- The stronger paper is the honest one: do not overclaim RE, CoVe, public
  generalization, or statistical significance.
- Glossary helps recall/F1 but can add false positives.
- RAG is slower because CPU embedding/reranking dominated D's wall time; future
  RAG runs need replay manifests or timing hygiene if more experiments are ever
  approved.
- P5 A/B/C/D were NER-only configs (`schema.task: ner`, empty relation types);
  zero relation predictions are expected and are not evidence that RE failed as
  a tested module.
- Verification v1/v2 over-killed or failed to beat D on dev. Keep it as a
  limitation/negative result unless new evidence is produced.
- AutoDL no-card mode may have tight memory limits. Avoid loading BGE-M3 unless
  needed; prefer cached/replay artifacts when they preserve comparisons.
- DOCX output caused encoding/rendering trouble in this workflow. Use Markdown
  as the working manuscript format.
- Backups and hashes matter. Never leave the only copy of data/results on the
  AutoDL instance.
- Every new paid action needs an explicit bounded human gate, even if it seems
  technically small.
