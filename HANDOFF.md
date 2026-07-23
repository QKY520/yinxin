# HANDOFF.md - New Conversation Handoff

Date: 2026-07-23
Workspace: `D:\yinsir`

This file is written for a new Codex/agent session with no prior chat context.
Read these files before doing any project work:

1. `AGENT_PLAYBOOK.md` - authoritative machine execution contract.
2. `实验实施指导文档_综合版.md` - human-facing rationale and operational guide.
3. `AGENTS.md` - durable repository and safety rules.
4. This `HANDOFF.md` - latest operational state.

Some "current gate" text in `AGENTS.md` and `AGENT_PLAYBOOK.md` is stale
because the project advanced beyond those snapshots. Treat the chronology in
this `HANDOFF.md` as the latest status, while all hard safety, cost, remote-only
execution, leakage, and human-gate rules in the control docs still apply.

## 1. Mission

We are building a practical SCI-Q4-oriented applied/engineering paper project:

- Domain: Chinese equipment-domain technical/public texts.
- Main task: few-shot NER.
- Auxiliary task: exact relation extraction.
- Entity schema: `EQUIPMENT`, `MODULE`, `TECH_SCHEME`, `METRIC`.
- Relation schema: `USES`, `HAS_METRIC`, `PART_OF`.
- Method line: local Qwen2.5 extraction with fixed-random versus kNN examples,
  glossary injection, RAG evidence, and atomic self-verification.
- Paper claim: not supervised SOTA. The intended claim is that retrieval and
  verification-style mechanisms can reduce entity-level false-discovery-style
  hallucination while preserving or improving extraction F1 in a low-label
  equipment domain.
- Manuscript route: Chinese technical draft first, then English SCI manuscript.
- Budget target: about 400 CNY unless separately approved.

Current experimental scope is still **dev-only sanity**, not final P5. All P3
numbers below are from `domain_dev50`, seed 42, K=5. They are not final paper
numbers and must not be reported as mean +/- std.

## 2. Non-Negotiable Rules

- Never run project Python locally on Windows.
- Windows `D:\yinsir` is only for editing, Git, SSH/SCP, documentation, and
  lightweight artifact checks.
- All Python, tests, data processing, inference, evaluation, and aggregation
  must run on AutoDL through SSH alias `autodl-paper`.
- Use AutoDL GPU-free mode for coding, tests, dry-runs, preprocessing, and
  aggregation.
- Use paid GPU only for model inference/training and only after explicit human
  approval for one bounded step.
- After every GPU phase: stop vLLM, verify GPU memory returns to 0 MiB, back
  up, sync lightweight artifacts to `D:\yinsir`, report cost, and remind the
  human to shut down or switch to no-card mode.
- Never touch `domain_test` for prompt tuning, glossary tuning, RAG tuning,
  threshold changes, or verification tuning.
- Preserve negative and mixed results. Do not rerun them away.
- Commit and push after meaningful code/config/documentation changes.
- Do not run E-prime, P5/full ablations, more seeds, or any `domain_test`
  evaluation without a new explicit gate.
- The real AutoDL host/port/passwords live only in the user's local SSH config.
  Never write them into tracked files.

## 3. Repo And Machine

Local:

- Workspace: `D:\yinsir`
- Branch: `main`
- Git remote: `https://github.com/QKY520/yinxin.git`
- Git identity for this repo: `yly <714520833@qq.com>`

Remote:

- SSH alias: `autodl-paper`
- Remote code: `/root/project`
- Remote data/model/backup root: `/root/autodl-tmp`
- Project venv: `/root/autodl-tmp/venvs/equipment-ie`
- Last reported 4090 price: 2.7 CNY/hour.
- Last observed status after E v3 dry-run: GPU-free / no Nvidia device.

Useful status command:

```bash
ssh autodl-paper 'cd /root/project; git rev-parse --short HEAD; git status --short; nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo GPU_FREE_OR_NVIDIA_SMI_UNAVAILABLE'
```

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

- 400 public-text equipment-domain candidates were collected:
  Baidu Baike 7, patent 84, CMNEE 309.
- Schema `p2-schema-draft-v1` and 10 synthetic examples were approved.
- QAonMilitaryKG exact-match distant supervision had low coverage:
  15/400 records matched, 23 EQUIPMENT suggestions, 0 relations.
- Qwen2.5-14B-AWQ proposal path and human annotation/adjudication completed for
  the approved 250-record route.
- Final adjudicated 100-row double-annotation subset:
  607 entities, 259 relations, 0 errors, 0 warnings.
- One structural repair was logged for `domain-candidate-0123`.
- Frozen outputs on remote:
  - `/root/autodl-tmp/data/domain_gold_250.jsonl` - 250 rows;
  - `/root/autodl-tmp/data/domain_support.jsonl` - 30 rows;
  - `/root/autodl-tmp/data/domain_dev.jsonl` - 50 rows;
  - `/root/autodl-tmp/data/domain_test.jsonl` - 170 rows;
  - `/root/autodl-tmp/data/domain_rag_corpus.jsonl` - 230 rows;
  - `/root/autodl-tmp/data/FROZEN`;
  - `/root/project/logs/dedup.json`.
- Important hashes:
  - `domain_gold_250.jsonl`:
    `fb183c733d328124c35e527872eb9cb4ea839fdf7bea1059c2313e3ea207acdc`;
  - `domain_support.jsonl`:
    `9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a`;
  - `domain_dev.jsonl`:
    `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`;
  - `domain_test.jsonl`:
    `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`.
- P2 gold backup:
  - `D:\yinsir\backups\P2\p2_domain_gold_freeze_20260722.tar.gz`;
  - SHA256:
    `a3711e2af4179d8398d8d497827ff703b1cfa4a8b0c05ea4de47837b9329ec3f`.

## 5. P3 Domain-Dev Final Sanity Summary

P3 domain-dev sanity has now completed A, B, C, D, E v1, E v2, plus a GPU-free
E v3 dry-run. All model-run cells are `domain_dev50`, K=5, seed 42, Qwen2.5-7B
via vLLM. These are sanity results only.

| Config | Main change | Precision | Recall | F1 | TP/FP/FN | Hallucination rate | Verdict |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| A | fixed random, no glossary/RAG/verif | 0.4914 | 0.5570 | 0.5221 | 171/177/136 | 0.5086 | accepted baseline |
| B | kNN examples | 0.4767 | 0.5342 | 0.5038 | 164/180/143 | 0.5233 | negative |
| C | B replay + glossary | 0.4722 | 0.5537 | 0.5097 | 170/190/137 | 0.5278 | mixed |
| D | C + RAG rerank top-3 | 0.5211 | 0.5635 | 0.5415 | 173/159/134 | 0.4789 | positive, current best |
| E v1 | D + verifier v1 | 0.6173 | 0.3257 | 0.4264 | 100/62/207 | 0.3827 | negative, severe overkill |
| E v2 | D + source-first verifier v2 | 0.5266 | 0.5472 | 0.5367 | 168/151/139 | 0.4734 | mixed/near-tie negative |

Key comparisons:

- `B - A`: kNN is negative on this tiny 30-row support set:
  F1 `-0.0183`, FP `+3`.
- `C - B`: glossary slightly recovers recall/F1 but increases FP:
  F1 `+0.0059`, FP `+10`.
- `D - C`: RAG is the strongest positive module:
  F1 `+0.0317`, FP `-31`.
- `D - A`: D is also better than the fixed-random baseline:
  F1 `+0.0193`, FP `-18`.
- `E v1 - D`: verifier v1 reduces hallucination rate by about 9.6 percentage
  points but destroys recall and F1.
- `E v2 - D`: verifier v2 fixes most overkill but still slightly lowers F1 and
  barely reduces hallucination rate.

Current decision:

- **D(RAG) is the current best positive result.**
- Verification should be preserved as a negative/mixed branch for now.
- Do not run E-prime with the current verifier approach.
- E v3 prompt exists only as GPU-free prep and remains unauthorized for paid
  execution.

## 6. P3 Detailed Milestones And Reports

Important reports:

- A baseline:
  - `docs/P3_DOMAIN_DEV50_SANITY_20260722.md`
  - `docs/P3_DOMAIN_DEV50_SANITIZE_AUDIT_20260722.md`
- B kNN:
  - `docs/P3_DOMAIN_DEV50_B_KNN_SANITY_20260722.md`
  - `docs/P3_DOMAIN_DEV50_B_KNN_AUDIT_20260722.md`
- C glossary:
  - `docs/P3_DOMAIN_DEV50_C_GLOSSARY_DRYRUN_20260723.md`
  - `docs/P3_DOMAIN_DEV50_C_GLOSSARY_SANITY_20260723.md`
  - `docs/P3_DOMAIN_DEV50_C_GLOSSARY_AUDIT_20260723.md`
- D RAG:
  - `docs/P3_DOMAIN_DEV50_D_RAG_DRYRUN_20260723.md`
  - `docs/P3_DOMAIN_DEV50_D_RAG_RELEVANCE_AUDIT_20260723.md`
  - `docs/P3_DOMAIN_DEV50_D_RAG_SANITY_20260723.md`
  - `docs/P3_DOMAIN_DEV50_D_RAG_AUDIT_20260723.md`
- E verification:
  - `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DRYRUN_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_VERIFICATION_EXEC_PREP_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_VERIFICATION_SANITY_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_VERIFICATION_VERDICT_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_VERIFICATION_V2_DRYRUN_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_V2_VERIFICATION_SANITY_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_V2_VERIFICATION_VERDICT_20260723.md`
  - `docs/P3_DOMAIN_DEV50_E_VERIFICATION_V3_DRYRUN_20260723.md`
- Final summary:
  - `docs/P3_DOMAIN_DEV50_FINAL_SUMMARY_20260723.md`

Important P3 backups:

- A:
  `D:\yinsir\backups\P3\p3_domain_dev50_sanity_sanitize_20260722.tar.gz`
  SHA256 `3b26fbd36e0614e1dbc440cbab47c9eb05c750b6e135dc9595c0860a3f91bfac`
- B:
  `D:\yinsir\backups\P3\p3_domain_dev50_b_knn_sanity_sanitize_20260722.tar.gz`
  SHA256 `53ac62255488fb9ca9269d9c789141dffec1d5729b2e6a75c99c519f0d3348db`
- C:
  `D:\yinsir\backups\P3\p3_domain_dev50_c_glossary_sanity_sanitize_20260723.tar.gz`
  SHA256 `84febe390bf5690b80e06049dd48c9d92de5e478c7e5a914dab333a707531e58`
- D:
  `D:\yinsir\backups\P3\p3_domain_dev50_d_rag_sanity_20260723.tar.gz`
  SHA256 `f449d67638ac71bd43f0ffd7fe1dc93149ac1d52b431faf358ea540c34e3f843`
- E v1:
  `D:\yinsir\backups\P3\p3_domain_dev50_e_verification_sanity_20260723.tar.gz`
  SHA256 `74c702f9b3bcfbb2db902e9c5b2fae61223ec819358d23227938063458067a51`
- E v2:
  `D:\yinsir\backups\P3\p3_domain_dev50_e_v2_verification_sanity_20260723.tar.gz`
  SHA256 `68514392464b742586327223e476dfa9bc3e38b45905d9c33634980de92e742c`

## 7. Current Status And Blocker

Current status:

- P0, P1, and P2 are complete.
- Domain data is frozen. `domain_test` exists and has not been used for tuning.
- P3 domain-dev sanity sequence is complete enough for a decision.
- D(RAG) is the current best positive result.
- Verification E v1/E v2 is negative/mixed and should not receive more paid GPU
  time by default.
- E v3 prompt/config was prepared in GPU-free mode only and is not authorized.
- AutoDL was last observed in GPU-free/no-device mode after E v3 dry-run.

Current blocker:

- Stop for a human decision before any further paid experiment.
- Do not run E v3, E-prime, P5/full ablations, more seeds, or `domain_test`
  unless the human explicitly approves the next bounded gate.

## 8. Recommended Next Plan

Recommended next step is GPU-free decision planning:

1. Preserve D(RAG) as the current positive dev result.
2. Treat verification as a documented negative/mixed branch.
3. Prepare a reduced next-run plan that avoids more paid verifier experiments
   unless the human explicitly wants them.
4. Decide whether the next paid gate should be:
   - a small D-focused sanity on another allowed dev/public split; or
   - preparation for the full P5 grid with E kept as a negative row; or
   - another explicitly approved verifier experiment using v3 despite the
     current recommendation.

Do not jump directly to P5 without a human gate.

## 9. Lessons Worth Remembering

- The equipment-domain route is fixed. Do not drift into toy domains or generic
  NER demos.
- P3 sanity is domain-first now. CLUENER is still needed later but should not
  distract from the current domain decision.
- kNN with only 30 support rows is weak; B being worse than A is plausible and
  useful negative evidence.
- C used kNN replay deliberately so C-B isolates glossary injection. Preserve
  this hygiene.
- Glossary is a double-edged tool: it can recover domain terms but also induces
  broad type bias and false positives.
- D had an important leakage bug in early preview: top-1 retrieved the query
  itself because dev IDs were not excluded. The fix is active: exclude dev IDs
  from RAG corpus for dev sanity; later exclude test IDs for test.
- RAG relevance is noisy but still helped by structurally anchoring the model
  and reducing FP. D is positive despite imperfect evidence.
- Verification v1 failed because the verifier treated RAG evidence as primary.
  It answered `no` when RAG did not mention the entity.
- Verification v2 fixed most overkill but still did not beat D; it retained
  useful location/organization filtering but still deleted legitimate
  formation/group and component entities.
- E v3 prompt is only a GPU-free backup design; do not run it paid unless the
  human explicitly overrides the current recommendation.
- Always stop vLLM immediately after a paid run and verify GPU memory returns
  to 0 MiB.
- AutoDL GPU-free mode may have tight memory limits. Avoid loading BGE-M3 unless
  needed; use replay/cached artifacts when that preserves comparisons.
- All negative and mixed rows are paper evidence. Do not delete or hide them.
- Every prompt/config/glossary/RAG decision needs a Git commit or structured
  decision record.

