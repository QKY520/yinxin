# HANDOFF.md - New Conversation Handoff

Date: 2026-07-23
Workspace: `D:\yinsir`

This file is written for a new Codex/agent session with no prior chat context.
Before doing project work, read these files completely:

1. `AGENT_PLAYBOOK.md` - authoritative machine execution contract.
2. `实验实施指导文档_综合版.md` - human-facing rationale and operational guide.
3. `AGENTS.md` - durable repository and safety rules.
4. This `HANDOFF.md` - latest operational state.

If old "current gate" text in the control docs conflicts with the chronology
below, treat that text as stale status and ask the human before acting. The hard
rules in the control docs still apply.

## 1. What We Are Doing

We are building a practical SCI-Q4-oriented applied/engineering paper project:

- Topic: Chinese equipment-domain few-shot information extraction.
- Main task: NER with entity types `EQUIPMENT`, `MODULE`, `TECH_SCHEME`,
  `METRIC`.
- Auxiliary task: relation extraction with `USES`, `HAS_METRIC`, `PART_OF`.
- Method line: local open-source LLM extraction with fixed-random versus kNN
  examples, glossary/schema constraints, later RAG evidence, and later atomic
  self-verification.
- Paper claim: not supervised SOTA. The claim is that retrieval and
  verification can reduce entity-level false-discovery-style hallucination while
  preserving or improving extraction F1 in a low-label equipment domain.
- Manuscript route: Chinese technical draft first, then English SCI manuscript.
- Budget target: about 400 CNY unless separately approved.

The current experimental phase is **P3 domain-dev sanity**, not P4/P5. The
current dataset for tuning/sanity is `domain_dev50`. Do not touch
`domain_test` for tuning.

## 2. Non-Negotiable Rules

- Never run project Python locally on Windows.
- Windows `D:\yinsir` is only for editing, Git, SSH/SCP, documentation, and
  lightweight artifact checks.
- All Python, tests, data processing, inference, evaluation, and aggregation
  must run on AutoDL through SSH.
- Use SSH alias `autodl-paper`; never record real host, port, passwords, keys,
  tokens, or cookies in tracked files.
- Use AutoDL GPU-free mode for coding, downloads, preprocessing, tests,
  dry-runs, and aggregation.
- Use paid GPU only for model inference/training and only after explicit human
  approval for the current bounded step.
- After every GPU phase: stop vLLM, verify GPU memory returns to 0 MiB, back
  up, sync lightweight artifacts to `D:\yinsir`, report approximate cost, and
  remind the human to shut down or switch to no-card mode.
- Preserve negative and mixed results. Do not delete, overwrite, or hide failed
  rows/runs.
- Commit and push after meaningful code/config/documentation changes.
- Do not enter P4/P5 or run full ablations until the human explicitly approves.
- After `domain_test.jsonl` is frozen, no prompt, schema, glossary, threshold,
  RAG, or verification tuning may be informed by test results.

## 3. Repo And Machine State

Local:

- Workspace: `D:\yinsir`
- Branch: `main`
- Git remote: `https://github.com/QKY520/yinxin.git`
- Previous checkpoint before this handoff rewrite:
  `c71ffb807d08e4f76bc5c8131811493485117aff`
  (`Add P3 C glossary audit template`).
- For the actual latest commit, run `git rev-parse HEAD`; this file itself is
  expected to be committed after editing.

Remote:

- SSH alias: `autodl-paper`
- Remote code: `/root/project`
- Remote data/model/backup root: `/root/autodl-tmp`
- Project venv: `/root/autodl-tmp/venvs/equipment-ie`
- Last known GPU price reported by human: 2.7 CNY/hour.
- Real host/port may change and must live only in local SSH config.

## 4. Completed Work

### P0 - Environment

Completed.

- AutoDL environment was set up.
- Project venv imports and `pip check` passed previously.
- Fixed model directories were downloaded and structurally checked:
  Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct-AWQ, BGE-M3, and
  bge-reranker-v2-m3.
- P0 backup was created and hash-verified.
- Human confirmed the P0 image was saved.

### P1 - Public Data

Completed.

- CLUENER, Few-NERD SUP, DuIE 2.0, and CMNEE were downloaded and normalized.
- 12 official split JSONL files were generated.
- K=1/5/10 support files were generated with seed 42.
- Loader/span checks passed.
- Known limitation: public CLUENER and DuIE test files have no gold labels and
  must never be evaluated as all-negative gold.
- P1 backup was created and verified.

### P2 - Domain Dataset

Completed and frozen.

- 400 public-text equipment-domain candidates collected:
  Baidu Baike 7, patent 84, CMNEE 309.
- `p2-schema-draft-v1` plus 10 synthetic examples approved by the human.
- QAonMilitaryKG exact-match distant supervision run in GPU-free mode:
  15/400 records matched, 23 EQUIPMENT suggestions, 0 relations.
- Qwen2.5-14B-AWQ LLM proposal path and human annotation/adjudication completed
  for the approved 250-record route.
- Final adjudication validation:
  - rows: 100 double-annotated adjudicated rows;
  - entities: 607;
  - relations: 259;
  - `USES=102`, `PART_OF=147`, `HAS_METRIC=10`;
  - errors: 0;
  - warnings: 0.
- Gold build audited all 250 source rows in AutoDL GPU-free mode.
- One structural repair was made and logged:
  - affected row: `domain-candidate-0123`;
  - dropped nested entity `攻击艇` `[93,96)` `EQUIPMENT`;
  - kept containing entity `快速攻击艇打击武器项目` `[91,102)`
    `TECH_SCHEME`;
  - dropped one relation pointing to the removed entity;
  - repair log SHA256:
    `4861bdfe2320b64d36bafff84d4887c684eea37d2f6dcd63cdad06525d841de8`.
- Remote GPU-free verification passed:
  - `python -m unittest tests.test_build_p2_domain_gold` => OK;
  - `python -m unittest tests.test_schema tests.test_domain_data` => OK;
  - `python scripts/verify_p2_domain_gold_freeze.py` => `status=ok`.
- Frozen outputs:
  - `/root/autodl-tmp/data/domain_gold_250.jsonl` - 250 rows;
  - `/root/autodl-tmp/data/domain_support.jsonl` - 30 rows;
  - `/root/autodl-tmp/data/domain_dev.jsonl` - 50 rows;
  - `/root/autodl-tmp/data/domain_test.jsonl` - 170 rows;
  - `/root/autodl-tmp/data/domain_rag_corpus.jsonl` - 230 rows;
  - `/root/autodl-tmp/data/FROZEN`;
  - `/root/project/logs/dedup.json`;
  - `/root/project/logs/p2_domain_gold_manifest.json`;
  - `/root/project/logs/p2_domain_gold_repair_log.json`.
- Key hashes:
  - `domain_gold_250.jsonl`:
    `fb183c733d328124c35e527872eb9cb4ea839fdf7bea1059c2313e3ea207acdc`;
  - `domain_support.jsonl`:
    `9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a`;
  - `domain_dev.jsonl`:
    `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`;
  - `domain_test.jsonl`:
    `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`;
  - `dedup.json`:
    `ebc0a79dbe5167f0e7daa0523242f99889e0280383981470de09ff9154c54768`;
  - `p2_domain_gold_manifest.json`:
    `6c7d9c1f3e361c2747e1a3b8181fcd9aeca324ebab915586096e686687d49a4a`.
- P2 gold backup:
  - remote:
    `/root/autodl-tmp/backup/p2/p2_domain_gold_freeze_20260722.tar.gz`;
  - local:
    `D:\yinsir\backups\P2\p2_domain_gold_freeze_20260722.tar.gz`;
  - SHA256:
    `a3711e2af4179d8398d8d497827ff703b1cfa4a8b0c05ea4de47837b9329ec3f`.

## 5. P3 Progress So Far

P3 is currently running only bounded `domain_dev` sanity checks with Qwen2.5-7B
via vLLM. These are proposal-stage sanity runs, not final full ablations.

### P3 Code Base

Implemented:

- `src/equipment_ie/extraction.py`
- `scripts/run_p3_extraction.py`
- `scripts/verify_p3_sanity_result.py`
- P3 configs under `configs/`
- extraction tests under `tests/test_extraction.py`

Important pipeline behavior:

- strict JSON parsing is still required;
- proposal-stage sanitizer may drop invalid proposed entity units with explicit
  flags instead of failing a whole record;
- per-query JSONL rows record prompt/output hashes and `example_ids`;
- `embedding.device: cpu` enforces `CUDA_VISIBLE_DEVICES=""` before importing
  FlagEmbedding, so BGE-M3 does not compete with vLLM for GPU memory.

### P3 A - Fixed Random Baseline

Completed on `domain_dev50`.

- Config: `configs/p3_domain_dev50_a_k5_sanity_sanitize.yaml`
- Dataset: `domain_dev50`
- Model: Qwen2.5-7B via vLLM
- Examples: fixed-random K=5 seed 42
- No glossary, no RAG, no verification
- Parse failures: 0/50
- Entity micro P/R/F1:
  - P: `0.49137931034482757`
  - R: `0.5570032573289903`
  - F1: `0.5221374045801527`
- TP/FP/FN: 171 / 177 / 136
- Sanitized unit events: 49
- Predicted entities: 348
- Max type share: 0.5229885057471264
- Backup:
  - remote:
    `/root/autodl-tmp/backup/p3/p3_domain_dev50_sanity_sanitize_20260722.tar.gz`;
  - local:
    `D:\yinsir\backups\P3\p3_domain_dev50_sanity_sanitize_20260722.tar.gz`;
  - SHA256:
    `3b26fbd36e0614e1dbc440cbab47c9eb05c750b6e135dc9595c0860a3f91bfac`.
- Report: `docs/P3_DOMAIN_DEV50_SANITY_20260722.md`
- Human audit: `docs/P3_DOMAIN_DEV50_SANITIZE_AUDIT_20260722.md`
  - 49 sanitizer flags had 0 sanitizer misdrops.
  - Four regrettable drops were model occurrence mistakes, not sanitizer bugs.
  - A was accepted as a baseline sanity result.

### P3 B - kNN Examples

Completed on `domain_dev50` and preserved as a negative result.

- Config: `configs/p3_domain_dev50_b_knn_k5_sanity_sanitize.yaml`
- Examples: BGE-M3 + FAISS kNN K=5 over support only
- No glossary, no RAG, no verification
- Parse failures: 0/50
- Entity micro P/R/F1:
  - P: `0.47674418604651164`
  - R: `0.5342019543973942`
  - F1: `0.5038402457757296`
- TP/FP/FN: 164 / 180 / 143
- Sanitized unit events: 32
- Predicted entities: 344
- Max type share: 0.5
- Comparison to A: B is lower by about `0.0183` F1.
- Backup:
  - remote:
    `/root/autodl-tmp/backup/p3/p3_domain_dev50_b_knn_sanity_sanitize_20260722.tar.gz`;
  - local:
    `D:\yinsir\backups\P3\p3_domain_dev50_b_knn_sanity_sanitize_20260722.tar.gz`;
  - SHA256:
    `53ac62255488fb9ca9269d9c789141dffec1d5729b2e6a75c99c519f0d3348db`.
- Report: `docs/P3_DOMAIN_DEV50_B_KNN_SANITY_20260722.md`
- Human audit: `docs/P3_DOMAIN_DEV50_B_KNN_AUDIT_20260722.md`
  - kNN was judged unreliable with only 30 support rows.
  - Main root causes: subdomain mismatch, type distribution distortion, and
    too-small support pool.
  - B should be retained as a negative result, not rerun away.

### P3 C - kNN Replay + Glossary

Completed on `domain_dev50` and preserved as a mixed result.

- Glossary file: `data/domain_dict.jsonl`
- Glossary size: 73 entries
- Glossary SHA256:
  `01b857822894bb09268cbb7fb14ad0988630137bb7efae0b9d90f7d75a2f3ef6`
- C uses `examples.mode: knn_replay`, not live BGE-M3 kNN, because the current
  GPU-free AutoDL cgroup memory limit was 2 GiB and BGE-M3 CPU dry-run was
  killed. Replaying B's exact `example_ids` isolates C-B as a glossary-only
  comparison.
- Dry-run report:
  `docs/P3_DOMAIN_DEV50_C_GLOSSARY_DRYRUN_20260723.md`
- Execution config:
  `configs/p3_domain_dev50_c_glossary_k5_sanity_sanitize.yaml`
- Dataset: `domain_dev50`
- Model: Qwen2.5-7B via vLLM
- Examples: B `example_ids` replay, K=5 seed 42
- Glossary: enabled, substring matching, max 20 entries
- No RAG, no verification
- Parse failures: 0/50
- Entity micro P/R/F1:
  - P: `0.4722222222222222`
  - R: `0.5537459283387622`
  - F1: `0.5097451274362819`
- TP/FP/FN: 170 / 190 / 137
- Sanitized unit events: 27
- Sanitization flags:
  - `ENTITY_DROPPED_INVALID_UNIT`: 20
  - `ENTITY_DROPPED_OVERLAP`: 7
- Predicted entities: 360
- Type counts:
  - EQUIPMENT: 179
  - MODULE: 133
  - METRIC: 31
  - TECH_SCHEME: 17
- Max type share: 0.49722222222222223
- Comparison:
  - A F1: `0.5221374045801527`
  - B F1: `0.5038402457757296`
  - C F1: `0.5097451274362819`
  - C improves over B by about `+0.0059` F1.
  - C remains below A by about `-0.0124` F1.
- Verification command on remote passed:
  `python scripts/verify_p3_sanity_result.py --per-query results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl --expected-rows 50`
- vLLM was stopped and GPU memory returned to 0 MiB / 24564 MiB.
- Backup:
  - remote:
    `/root/autodl-tmp/backup/p3/p3_domain_dev50_c_glossary_sanity_sanitize_20260723.tar.gz`;
  - local:
    `D:\yinsir\backups\P3\p3_domain_dev50_c_glossary_sanity_sanitize_20260723.tar.gz`;
  - SHA256:
    `84febe390bf5690b80e06049dd48c9d92de5e478c7e5a914dab333a707531e58`.
- Report: `docs/P3_DOMAIN_DEV50_C_GLOSSARY_SANITY_20260723.md`
- Audit template created and pushed:
  `docs/P3_DOMAIN_DEV50_C_GLOSSARY_AUDIT_20260723.md`

### P3 D - RAG GPU-free Prep

Completed in GPU-free mode only.

- Human completed the C glossary audit and accepted C as an
  `acceptable mixed result`.
- D prep scope: no paid GPU, no vLLM call, no model inference, no
  `domain_test`, no P5/full ablation.
- Added RAG selector support in `scripts/run_p3_extraction.py`.
- Prompt/logging now supports `rag_passages` and `rag_passage_ids`.
- RAG selector now supports `rag.exclude_source_ids_path` /
  `rag.exclude_source_ids_paths` to prevent dev/test SELF leakage.
- Added D dry-run config:
  `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun.yaml`.
- Added final D config template:
  `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml`.
- Dry-run mode used `rag.mode: lexical_preview` only to validate prompt
  injection, dev-id exclusion, and relevance-audit workflow under GPU-free
  constraints.
- Final D config uses the fixed method path `bge_faiss_rerank`: BGE-M3
  embeddings, FAISS top-20, and bge-reranker-v2-m3 top-3. It is not authorized
  for execution yet.
- Remote GPU-free test passed:
  `python -m unittest tests.test_extraction` => 13 tests OK.
- Remote D dry-run passed:
  `python scripts/run_p3_extraction.py --config configs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun.yaml --dry-run`
- Dry-run summary:
  - query rows: 50;
  - raw RAG corpus chunks: 333;
  - excluded dev source IDs: 50;
  - retained RAG chunks after exclusion: 263;
  - injected top-k: 3;
  - model calls: 0;
  - API called: false;
  - GPU device present: false;
  - max prompt chars: 5496.
- First 10 relevance-audit rows were spot-checked after the SELF fix; top-1 is
  no longer the query itself in those rows.
- Report:
  `docs/P3_DOMAIN_DEV50_D_RAG_DRYRUN_20260723.md`
- Relevance audit template:
  `docs/P3_DOMAIN_DEV50_D_RAG_RELEVANCE_AUDIT_20260723.md`

### P3 D - RAG Paid Sanity

Completed as one bounded paid-GPU sanity run on `domain_dev50`.

- Human confirmed paid GPU was enabled and approved one bounded P3 D(RAG)
  domain-dev sanity only.
- Config: `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml`
- Model: Qwen2.5-7B via vLLM.
- RAG path: BGE-M3 + FAISS top-20 + bge-reranker-v2-m3 top-3.
- Dev SELF leakage fix active: excluded 50 `domain_dev` source IDs from RAG.
- RAG retained chunks: 263 from 333 raw chunks.
- Run window:
  - vLLM health ready: `2026-07-23 15:11:44` Asia/Shanghai;
  - extraction started: `2026-07-23 15:12:16` Asia/Shanghai;
  - extraction ended: `2026-07-23 15:34:49` Asia/Shanghai.
- vLLM was stopped and GPU memory returned to 0 MiB.
- Approximate GPU service window: about 26 minutes.
- Estimated cost at 2.7 CNY/hour: about 1.17 CNY; platform billing is
  authoritative.
- Metrics:
  - P: `0.5210843373493976`;
  - R: `0.5635179153094463`;
  - F1: `0.5414710485133021`;
  - TP/FP/FN: 173 / 159 / 134;
  - parse failures: 0/50;
  - predicted entities: 332;
  - max type share: 0.5060.
- Comparison:
  - D vs C: F1 `+0.0317`, FP `-31`;
  - D vs A: F1 `+0.0193`, FP `-18`.
- Verification passed:
  `python scripts/verify_p3_sanity_result.py --per-query results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl --expected-rows 50`
- Backup:
  - remote:
    `/root/autodl-tmp/backup/p3/p3_domain_dev50_d_rag_sanity_20260723.tar.gz`;
  - local:
    `D:\yinsir\backups\P3\p3_domain_dev50_d_rag_sanity_20260723.tar.gz`;
  - SHA256:
    `f449d67638ac71bd43f0ffd7fe1dc93149ac1d52b431faf358ea540c34e3f843`.
- Report:
  `docs/P3_DOMAIN_DEV50_D_RAG_SANITY_20260723.md`

### P3 D - RAG Audit

Completed by the human/agent in
`docs/P3_DOMAIN_DEV50_D_RAG_AUDIT_20260723.md`.

- Conclusion: D is `acceptable positive`.
- Audit sample: 20 rows.
- GOOD / OK / POOR: 8 / 7 / 5.
- D clearly better than C: 8 rows.
- D clearly worse than C: 5 rows.
- D roughly tied with C: 7 rows.
- D deleted C's wrong entities in 13/20 audited rows.
- D wrongly dropped C's correct entities in 3/20 audited rows.
- D added wrong entities in 5/20 audited rows.
- RAG evidence was clearly relevant in 3/20, partially relevant in 8/20, and
  noisy in 9/20.
- Interpretation: D's FP reduction is a real positive signal, but RAG evidence
  noise remains. This supports preparing E/E-prime verification.

### P3 E/E-prime Verification GPU-free Prep

Completed in prompt-generation dry-run mode and execution-prep mode.

- Added `scripts/run_p3_verification.py`.
- Added `tests/test_verification.py`.
- Added E config:
  `configs/p3_domain_dev50_e_verification_k5_sanity_dryrun.yaml`.
- Added E-prime config:
  `configs/p3_domain_dev50_eprime_verification_k5_sanity_dryrun.yaml`.
- E verifies D raw predictions using D's RAG passages:
  - input rows: 50;
  - atomic entity units: 332;
  - max prompt chars: 1392;
  - model calls: 0.
- E-prime verifies C raw predictions with source text only:
  - input rows: 50;
  - atomic entity units: 360;
  - max prompt chars: 436;
  - model calls: 0.
- Remote dry-run tests passed initially:
  `python -m unittest tests.test_verification` => 2 tests OK.
- Report:
  `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DRYRUN_20260723.md`.

### P3 E/E-prime Verification Execution Prep

Completed in GPU-free mode only.

- Implemented guarded verifier execution in `scripts/run_p3_verification.py`.
- Added atomic answer parsing:
  - valid `yes` / `no` are accepted;
  - longer or ambiguous verifier outputs are treated as `invalid`.
- Implemented `pred_verified` assembly:
  - drop only entity units receiving a valid `no`;
  - keep valid `yes` and invalid verifier outputs for audit.
- Added execution safety checks:
  - `execution.authorized` must be `true`;
  - `execution.human_gate` must equal `P3_VERIFICATION_SANITY_APPROVED`;
  - GPU device must be visible.
- Added guarded paid-sanity config templates, both intentionally unauthorized:
  - `configs/p3_domain_dev50_e_verification_k5_sanity.yaml`;
  - `configs/p3_domain_dev50_eprime_verification_k5_sanity.yaml`.
- Remote GPU-free tests passed:
  `python -m unittest tests.test_verification` => 4 tests OK.
- Unauthorized execution check passed:
  - command tried to run E config without `--dry-run`;
  - it refused with
    `config execution.authorized must be true for verifier model calls`;
  - exit status was nonzero.
- Formal config dry-runs passed:
  - E: 50 rows, 332 atomic entity units, max prompt 1392 chars,
    `api_called=false`;
  - E-prime: 50 rows, 360 atomic entity units, max prompt 436 chars,
    `api_called=false`.
- AutoDL remained in `GPU_FREE_MODE`.
- Report:
  `docs/P3_DOMAIN_DEV50_E_VERIFICATION_EXEC_PREP_20260723.md`.

### P3 E - RAG + Verification Paid Sanity

Completed as one bounded paid-GPU sanity run on `domain_dev50`.

- Human enabled paid GPU mode and approved continuing the current bounded step.
- Only E was run; E-prime, P5, more seeds, and `domain_test` were not run.
- Approved config:
  `configs/p3_domain_dev50_e_verification_k5_sanity_approved_20260723.yaml`.
- Model: Qwen2.5-7B via vLLM.
- Verifier input: D RAG raw predictions.
- Evidence: D query-level RAG passages.
- Atomic verifier units: 332 entity units.
- Verifier decisions:
  - yes: 162;
  - no: 170;
  - invalid: 0.
- Raw/D metrics:
  - P: `0.5210843373493976`;
  - R: `0.5635179153094463`;
  - F1: `0.5414710485133021`;
  - TP/FP/FN: 173 / 159 / 134;
  - hallucination rate: `0.4789156626506024`.
- E verified metrics:
  - P: `0.6172839506172839`;
  - R: `0.3257328990228013`;
  - F1: `0.4264392324093816`;
  - TP/FP/FN: 100 / 62 / 207;
  - hallucination rate: `0.38271604938271603`.
- Dropped diagnostics:
  - dropped units: 170;
  - dropped exact gold matches: 73;
  - dropped exact-gold-match rate: `0.4294117647058823`.
- Interpretation: E is a negative sanity result with the current verifier
  wording. It raises precision and lowers FP/hallucination rate, but overkills
  recall and drops too many gold entities. Preserve the result; do not rerun it
  away.
- vLLM was stopped after execution and GPU memory returned to 0 MiB / 24564 MiB.
- Approximate model-active window was about 3 minutes, about 0.14 CNY at 2.7
  CNY/hour. Platform billing is authoritative.
- Backup:
  - remote:
    `/root/autodl-tmp/backup/p3/p3_domain_dev50_e_verification_sanity_20260723.tar.gz`;
  - local:
    `D:\yinsir\backups\P3\p3_domain_dev50_e_verification_sanity_20260723.tar.gz`;
  - SHA256:
    `8fccbaa14bb95d4de3da45beb638367ecd6baa5bb0490a2fa31b4a62411c6320`.
- Report:
  `docs/P3_DOMAIN_DEV50_E_VERIFICATION_SANITY_20260723.md`.
- Dropped-unit audit sheet:
  `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DROPPED_AUDIT_20260723.md`.

## 6. Current Status And Blocker

Current status:

- P2 domain gold split/freeze is complete.
- P3 domain-dev sanity has completed A, B, C, D, and one E verifier sanity on
  `domain_dev50`.
- D is the current strongest single sanity result.
- B is a valid negative result.
- C is an accepted mixed result: slight recovery over B but still below A.
- D(RAG) GPU-free prep has completed using lexical preview only.
- D relevance audit has completed. The main finding was dev SELF leakage in the
  initial preview; this has been fixed by excluding `domain_dev` IDs.
- Final D `bge_faiss_rerank` sanity run completed and is the strongest P3
  domain-dev sanity result so far.
- D audit accepted D as a positive result.
- E/E-prime verification GPU-free prompt prep has completed.
- E paid verifier sanity completed and is negative/overkill with the current
  verifier wording.
- All P3 sanity runs so far are dev-only, seed 42, K=5, and should not be
  reported as final paper numbers.
- `domain_test` has not been used for tuning and must remain untouched.

Current blocker:

- Stop for human audit and verifier prompt revision before any further paid
  verifier run.
- Do not run E-prime with the current verifier wording because E already showed
  overkill.
- Do not run P5, more seeds, `domain_test`, or full ablations until the human
  explicitly approves the next bounded gate.

## 7. Immediate Next Plan

Ask the human for one bounded decision:

1. Audit the 20 sampled dropped E entities in
   `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DROPPED_AUDIT_20260723.md`.
2. Or approve GPU-free verifier prompt revision based on the E overkill result.
3. Or stop verification work and preserve D as the current positive result.

Do not jump directly to P5.

## 8. Files A New Session Should Inspect First

Control:

- `AGENT_PLAYBOOK.md`
- `实验实施指导文档_综合版.md`
- `AGENTS.md`
- `HANDOFF.md`

Current P3 reports:

- `docs/P3_DOMAIN_DEV50_SANITY_20260722.md`
- `docs/P3_DOMAIN_DEV50_SANITIZE_AUDIT_20260722.md`
- `docs/P3_DOMAIN_DEV50_B_KNN_SANITY_20260722.md`
- `docs/P3_DOMAIN_DEV50_B_KNN_AUDIT_20260722.md`
- `docs/P3_DOMAIN_DEV50_C_GLOSSARY_DRYRUN_20260723.md`
- `docs/P3_DOMAIN_DEV50_C_GLOSSARY_SANITY_20260723.md`
- `docs/P3_DOMAIN_DEV50_C_GLOSSARY_AUDIT_20260723.md`
- `docs/P3_DOMAIN_DEV50_D_RAG_DRYRUN_20260723.md`
- `docs/P3_DOMAIN_DEV50_D_RAG_RELEVANCE_AUDIT_20260723.md`
- `docs/P3_DOMAIN_DEV50_D_RAG_SANITY_20260723.md`
- `docs/P3_DOMAIN_DEV50_D_RAG_AUDIT_20260723.md`
- `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DRYRUN_20260723.md`

Current P3 configs:

- `configs/p3_domain_dev50_a_k5_sanity_sanitize.yaml`
- `configs/p3_domain_dev50_b_knn_k5_sanity_sanitize.yaml`
- `configs/p3_domain_dev50_c_glossary_k5_sanity_sanitize.yaml`
- `configs/p3_domain_dev50_c_glossary_k5_sanity_sanitize_dryrun.yaml`
- `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize_dryrun.yaml`
- `configs/p3_domain_dev50_d_rag_k5_sanity_sanitize.yaml`
- `configs/p3_domain_dev50_e_verification_k5_sanity_dryrun.yaml`
- `configs/p3_domain_dev50_eprime_verification_k5_sanity_dryrun.yaml`

Current P3 outputs:

- `results/p3/p3_domain_dev50_a_k5_sanity_sanitize_summary.json`
- `results/p3/p3_domain_dev50_a_k5_sanity_sanitize_per_query.jsonl`
- `results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_summary.json`
- `results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_per_query.jsonl`
- `results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_summary.json`
- `results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl`

Glossary:

- `data/domain_dict.jsonl`

## 9. Useful Remote Commands

Remote status, no Python:

```bash
ssh autodl-paper 'cd /root/project; git rev-parse HEAD; git status --short; test -e /dev/nvidia0 && echo GPU_VISIBLE || echo GPU_FREE_MODE'
```

Remote tests, only in AutoDL GPU-free mode:

```bash
ssh autodl-paper 'cd /root/project; . /root/autodl-tmp/venvs/equipment-ie/bin/activate; python -m unittest tests.test_extraction tests.test_schema tests.test_llm_labeling tests.test_public_data tests.test_domain_data'
```

Verify a P3 sanity result, only on AutoDL:

```bash
ssh autodl-paper 'cd /root/project; . /root/autodl-tmp/venvs/equipment-ie/bin/activate; python scripts/verify_p3_sanity_result.py --per-query results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl --expected-rows 50'
```

Never run these Python commands locally on Windows.

## 10. Lessons Worth Remembering

- The user wants the equipment-domain paper route only. Avoid irrelevant sample
  domains or toy examples.
- P3 sanity should be domain-first now. CLUENER sanity existed historically but
  should not distract the current work.
- The proposal-stage sanitizer is acceptable so far because human audits found
  no sanitizer-caused misdrops on A; still keep auditing flags whenever a new
  module changes output behavior.
- kNN with only 30 support rows is weak. It can pull semantically broad but
  format/subdomain-mismatched examples, so B being worse than A is plausible
  and should be preserved.
- Glossary C used kNN replay deliberately. This is good experimental hygiene:
  C-B isolates glossary effects instead of mixing glossary with a new retrieval
  sample.
- GPU-free AutoDL may have only a 2 GiB memory cgroup. Avoid loading BGE-M3 in
  that mode unless necessary; use replay/cached artifacts when this preserves
  the comparison.
- Stale vLLM processes can leave the HTTP port alive while GPU memory is 0 MiB.
  Before launching a paid run, check both process/port and `nvidia-smi`.
- FlagEmbedding may try CUDA unless CPU mode is enforced before import. Keep
  `embedding.device: cpu` and the `CUDA_VISIBLE_DEVICES=""` protection.
- Negative or mixed results are useful for the paper if they are well
  diagnosed. Do not rerun them away.
- Every new glossary/RAG/prompt/verification change needs a report or decision
  log plus Git commit.
- Stop at gates. The next correct action is determined by the human's C audit,
  not by available GPU time.
