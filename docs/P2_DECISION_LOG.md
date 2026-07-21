# P2 Decision Log

## 2026-07-16 - Step 5 entry authorized

The human explicitly authorized entry into Step 5 / P2 with this scope:

- Back up the existing P2 candidate artifacts in GPU-free mode.
- Submit the entity/relation schema, annotation guide, and ten examples for
  human approval.
- Do not prelabel real candidates, begin human annotation, or start the 14B
  model or any paid GPU work before approval.

Execution result:

- The candidate-stage private archive was created, copied locally, and
  hash-verified as recorded in `docs/P2_CANDIDATE_BACKUP_MANIFEST.md`.
- `configs/p2_schema_draft.yaml`, `docs/P2_ANNOTATION_GUIDE_DRAFT.md`, and
  `docs/p2_schema_examples_draft.jsonl` were prepared for Pause A.
- The examples are synthetic and do not label the collected candidate corpus.
- Current gate: `P2_PAUSE_A`, pending human schema approval.

The authorization does not extend to distant-supervision prelabeling, LLM
annotation, manual annotation, dataset splitting/freezing, or paid GPU use.

## 2026-07-16 - Pause A schema approved

The human approved all five decisions in `p2-schema-draft-v1`:

1. The four entity definitions and context-dependent EQUIPMENT/MODULE role.
2. The complete METRIC span policy.
3. The relation type matrix, including `USES` with a MODULE tail.
4. No overlapping entities, cross-sentence relations, or pronoun-coreference
   relations in v1.
5. Blank independent annotation for the 100-passage agreement sample.

The human authorized only GPU-free distant-supervision prelabeling and creation
of an unstarted review sheet. The authorization explicitly excludes the 14B
model, paid GPU work, and human annotation. After the artifacts are generated,
the project must stop for a separate 14B assistance and budget decision.

Execution result:

- Exact longest-first matching completed for all 400 candidates in GPU-free
  mode at commit `269cc53`.
- 15 candidates matched 23 proposed EQUIPMENT entities; no relations were
  inferred. Coverage was 3.75%, and the negative result was preserved.
- JSONL and CSV review sheets were generated with LLM disagreement uncomputed
  and every human annotation field untouched.
- Independent verification, 27 tests, private backup, local synchronization,
  and hash checks passed. Details are in
  `docs/P2_DISTANT_SUPERVISION_REPORT.md`.
- Current gate: stop before 14B assisted refinement and paid GPU use.

## 2026-07-16 - GPU-free 14B preparation resumed

After the distant-supervision step was paused and reported, the human asked the
agent to continue. The agent explicitly scoped the continuation to GPU-free
implementation, tests, token dry-runs, and a deployment/cost proposal. This did
not authorize model inference, paid GPU mode, or human annotation.

The sanity and full configurations are therefore committed with
`execution.authorized: false`. Changing that field or launching vLLM requires a
new explicit human approval and a live-price check.

Execution result:

- Independent 14B labeling, parsing, caching, DS/LLM union, disagreement, and
  review-sheet code was implemented without deploying the model.
- The approved schema was restored as an immutable artifact with SHA256
  `a3b2e8dc...102ac56`; versioned prompt wording was separated into
  `configs/p2_llm_prompt_v1.yaml` with SHA256 `d1a2569a...f7c739`.
- Active v2 tokenizer-only dry-runs completed for the fixed 10-record sanity set
  and all 400 candidates. Maximum contexts were 3,471 and 3,491 tokens out of
  8,192, respectively.
- Both manifests record no GPU, no API call, no model-weight load, no paid GPU,
  and no execution authorization. The P2 LLM cache and actual-output set remain
  empty.
- Four v2 manifests/logs were copied to the local private backup directory and
  matched their remote SHA256 values. Earlier v1 dry-runs are preserved but
  marked superseded because they reference the pre-correction schema hash.
- Full details and the bounded next-step proposal are recorded in
  `docs/P2_LLM_DEPLOYMENT_REPORT.md`.

Current gate: GPU-free 14B implementation and dry-run preparation are complete.
Stop before vLLM startup, inference, paid GPU mode, human annotation, splitting,
or freezing. The next possible step requires explicit approval for only the
10-record sanity run plus its budget; it does not imply approval of the
400-record full run.

## 2026-07-20 - Fixed 10-record 14B sanity approved

The human reported the live RTX 4090 price as 2.7 CNY/hour and approved only
the fixed 10-record Qwen2.5-14B-AWQ P2 sanity run.

Approved scope:

- Authorize only `configs/p2_llm_label_sanity.yaml` for actual execution.
- GPU-hour cap: 0.25 hours, cost cap: 0.675 CNY at the reported live price.
- Launch vLLM only for the sanity run, then verify, back up, report measured
  time/cost, and stop.

Explicit exclusions:

- The 400-record full pass remains unauthorized.
- Human annotation remains unauthorized.
- Dataset splitting/freezing remains unauthorized.
- P3/P4/P5 experiments remain unauthorized until the P2 gates are completed.

## 2026-07-20 - Sanity timeout guard adjusted

The first sanity execution attempt reached the old 120-second client timeout
before publishing final outputs. The atomic output guard left the final JSONL,
CSV, and report paths empty; partial successful calls remained only in the
prompt-hash cache.

Operational adjustment:

- Increase only `configs/p2_llm_label_sanity.yaml` server
  `request_timeout_seconds` from 120 to 300.
- Do not change prompt wording, schema, selected records, generation settings,
  model path, output paths, or any full-run authorization.
- Reuse cached successful requests and retry the fixed 10-record sanity only.

Execution result:

- The retry published v2 sanity outputs, but the success gate failed with
  4 parse failures out of 10 records.
- Failure modes were preserved in
  `/root/autodl-tmp/backup/p2/p2_llm_label_sanity_v2_report.json`: extra JSON
  characters, missing `occurrence`, and schema-invalid relation directions.
- The 400-record full pass remained unauthorized and was not launched.

Follow-up fix:

- Add `configs/p2_llm_prompt_v2.yaml` with explicit single-object JSON,
  exact entity-key, occurrence, and relation-type-matrix constraints.
- Update only the active sanity configuration to
  `p2-llm-label-sanity-v3` and v3 output paths, preserving the failed v2
  artifacts as a negative sanity result.
- Keep the config-level retry suffix synchronized with prompt v2 so the
  runner's prompt-consistency guard passes before any request is sent.
- Do not relax relation validation, change selected records, or authorize the
  full run.

Execution result:

- v3 sanity executed the same fixed 10 selected records and published v3
  outputs, but the success gate still failed with 4 parse failures out of 10.
- vLLM was stopped after the cap was consumed; GPU memory returned to 0 MiB.
- The measured service window was approximately 09:49:22 to 10:20:00
  Asia/Shanghai. At 2.7 CNY/hour, the estimated GPU cost is about 1.38 CNY.
- Remote backup:
  `/root/autodl-tmp/backup/p2/p2_14b_sanity_attempts_20260720.tar.gz`,
  SHA256 `72a74abd319f23fb5197cd8741622d44bf7a64717aee22f7542001b293cac528`.
- Local backup:
  `D:\yinsir\backups\P2\p2_14b_sanity_attempts_20260720.tar.gz`, same SHA256.

Current gate:

- Stop before any additional sanity retry or paid GPU use.
- The full 400-record pass, human annotation, splitting/freezing, and P3/P4/P5
  remain unauthorized.
- A prepared parser fix at commit `dee5e26` can recover extra trailing JSON
  braces while preserving schema validation, but a new v4 sanity retry requires
  explicit human approval and budget.

## 2026-07-20 - GPU-free v4 retry prepared

The human asked the agent to continue and questioned whether the experiment can
be completed reliably. The agent did not restart vLLM or make further paid GPU
calls. Instead, it prepared the next bounded retry in GPU-free mode.

Analysis from cached v3 outputs:

- The parser fix recovers three v3 failures caused by a valid JSON object
  followed by an extra closing brace.
- The remaining observed failure is a schema-invalid relation direction on
  `domain-candidate-0099`.

Prepared changes:

- `configs/p2_llm_prompt_v3.yaml` adds stricter relation constraints, including
  explicit rules that two EQUIPMENT entities must not receive `PART_OF`, and
  that firing, testing, deployment, integration, or capability statements are
  not composition relations.
- `configs/p2_llm_label_sanity.yaml` now points to
  `p2-llm-label-sanity-v4` output paths and prompt v3.
- `execution.authorized` remains `false` and `approval_record` is `null`.

Current gate: v4 is prepared only. Do not launch vLLM or execute the v4 sanity
retry until the human approves a new bounded retry budget.

## 2026-07-20 - Fixed 10-record v4 sanity retry approved

The human approved continuation after being asked to approve only the v4 fixed
10-record sanity retry. The approved retry scope is:

- Execute only `p2-llm-label-sanity-v4`.
- GPU-hour cap: 0.15 hours, cost cap: 0.405 CNY at 2.7 CNY/hour.
- Stop after verification and backup.

The 400-record full pass, human annotation, splitting/freezing, and P3/P4/P5
remain unauthorized.

Execution result:

- v4 executed the same fixed 10 selected records and published v4 outputs.
- The JSON-format failures from v3 were removed, but the success gate still
  failed with 3 parse failures out of 10: two relation type-matrix violations
  and one overlapping-entity violation.
- vLLM was stopped immediately after the run; GPU memory returned to 0 MiB.
- Remote backup:
  `/root/autodl-tmp/backup/p2/p2_14b_sanity_v4_attempt_20260720.tar.gz`,
  SHA256 `5953d1d8047ac28fcfe514611b1ea528053dd1ae47cfa9ba12c06919c51ea51c`.
- Local backup:
  `D:\yinsir\backups\P2\p2_14b_sanity_v4_attempt_20260720.tar.gz`, same SHA256.

Current gate: stop before any additional sanity retry or paid GPU use. The full
400-record pass remains unauthorized.

## 2026-07-20 - Paper route and continuation policy locked

The human clarified the final publication objective:

- Target: SCI Q4.
- Timeline target: within one month.
- Budget target: 400 CNY unless separately approved.
- Topic must remain equipment-domain information extraction.
- The original route is retained: equipment-domain small annotated dataset,
  reproducible experiment workflow, RAG/rule/schema/verification mechanisms to
  reduce hallucination, and ablation evidence.
- Chinese draft first, then English SCI manuscript.
- NER is the main evidence line; RE is auxiliary.
- Human annotators/reviewers and external commercial LLM APIs may be used as
  auxiliary support, with provenance recorded.

Operational policy after this decision:

- The paper strategy is locked, but this does not retroactively authorize the
  400-record full pass, human annotation, splitting/freezing, P3/P4/P5, or
  optional QLoRA.
- The next recommended experimental action is a bounded v5-style fixed
  10-record sanity/diagnostic retry that specifically addresses the v4
  relation type-matrix and overlapping-entity failures.
- After that retry, stop, back up, hash-verify, report time/cost, and request
  the next gate decision.

## 2026-07-20 - Fixed 10-record v5 sanity retry prepared

The project is now prepared for a bounded v5 retry only, with the updated
paper strategy locked and the previous v4 failure modes explicitly targeted.

Prepared scope:

- Execute only `p2-llm-label-sanity-v5`.
- Keep the fixed 10-record sanity selection unchanged.
- Use the new `p2-llm-label-v4` prompt file, which tightens overlap rejection
  and explicitly rejects invalid PART_OF configurations.
- GPU-hour cap: 0.25 hours.
- Cost cap: 0.675 CNY at the user-reported 2.7 CNY/hour live 4090 price.

Explicit exclusions remain unchanged:

- The 400-record full pass is not yet authorized.
- Human annotation is not yet authorized.
- Dataset splitting/freezing is not yet authorized.
- P3/P4/P5 are not yet authorized.

## 2026-07-20 - Fixed 10-record v5 sanity executed and preserved

The v5 sanity run was executed on the fixed 10-record set after the human
approved the bounded retry.

Execution result:

- v5 improved over v4 but still failed the success gate with 1 invalid output
  out of 10.
- The remaining failure was `domain-candidate-0039`, caused by nested entity
  overlap between `滚筒` and `滚筒外壳`.
- Relation type-matrix failures observed in v4 were fixed by v5.
- vLLM was stopped after v5; GPU memory returned to 0 MiB.
- Remote/local backup:
  `p2_14b_sanity_v5_attempt_20260720.tar.gz`, SHA256
  `b7d93dba8910a43ffe8ab8edc191ad295bb4cbde78e85991eb7bd85f23b4cf65`.

Current gate after v5: stop before the 400-record full pass, human annotation,
splitting/freezing, or P3/P4/P5. A further retry should not spend more 14B
tokens on prompt wording if a deterministic review-proposal-only overlap
resolver can address the remaining failure while preserving a structured flag.

## 2026-07-20 - Fixed 10-record v6 sanity passed

After the user restored the balance and supplied a new AutoDL endpoint, the
local SSH alias `autodl-paper` was updated outside Git. The new instance was
checked before execution:

- RTX 4090 visible and initially idle.
- No existing screen session.
- `/root/project` existed and pulled commit `dfa7bd1`.
- `/root/autodl-tmp/data`, `/root/autodl-tmp/models`, and
  `/root/autodl-tmp/backup/p2` existed.
- Remote unit tests passed: `python -m unittest tests.test_llm_labeling`
  reported 16 tests OK.

Implementation change:

- `parse_model_label_output` remains strict by default and still rejects
  overlapping entities for evaluation.
- P2 LLM review-sheet proposal generation now explicitly enables a
  deterministic overlap resolver:
  keep the longest non-overlapping entity proposal, log
  `LLM_OVERLAP_RESOLVED`, and drop/log any relation that references a removed
  entity.
- A unit test covers the real `滚筒` versus `滚筒外壳` failure shape.

Execution result:

- Run ID: `p2-llm-label-sanity-v6`.
- Commit: `dfa7bd1e22cc02a4e583ef34fe368d5368b72961`.
- Fixed records: 10.
- Parse/validation failures: 0.
- Success gate: passed.
- Request attempts: 12, all cache hits.
- LLM proposals: 52 entities and 20 relations.
- Logged flags:
  `ENTITY_ONLY_DISTANT=5`, `ENTITY_ONLY_LLM=50`,
  `ENTITY_OVERLAP_CONFLICT=1`, `LLM_OVERLAP_RESOLVED=1`,
  `LLM_RELATION_DROPPED_AFTER_OVERLAP_RESOLUTION=1`.
- vLLM was stopped after execution; `nvidia-smi` returned to 0 MiB used.
- v6 service window was approximately 19:46-19:52 Asia/Shanghai; at
  2.7 CNY/hour this is about 0.27 CNY. AutoDL billing remains the authoritative
  cost record.

Artifacts:

- Remote report:
  `/root/autodl-tmp/backup/p2/p2_llm_label_sanity_v6_report.json`.
- Local verification copies:
  `D:\yinsir\backups\P2\v6_verify\`.
- Valid remote/local backup:
  `p2_14b_sanity_v6_success_20260720_r2.tar.gz`, 45,314 bytes, SHA256
  `16cc70ea99cd88a337a102683cd166461f520ca9761c0e9a2f0dff560acfaead`.
- The first `p2_14b_sanity_v6_success_20260720.tar.gz` attempt was a 45-byte
  failed tar caused by an incorrect working directory and must not be treated
  as a valid backup.

Current gate:

- Stop before the 400-record P2 LLM proposal pass.
- Stop before human annotation, split/freeze, P3/P4/P5, or optional P7.
- The next decision should be either:
  1. approve a bounded 400-record P2 LLM proposal pass,
  2. manually audit the 10-row v6 review sheet first, or
  3. keep the work GPU-free and prepare annotation operations.

## 2026-07-20 - Prepared full-v6 config in GPU-free mode

After the instance was confirmed to be in GPU-free mode, a full-pass
configuration was prepared for the next possible P2 LLM proposal run:

- Added `configs/p2_llm_label_full_v6.yaml`.
- The config mirrors the successful sanity v6 prompt path:
  `p2-llm-label-v4`, retry suffix, request timeout, and conservative
  `max_concurrency=2`.
- The run remains unauthorized:
  `execution.authorized=false`, `approval_record=null`,
  `human_annotation_allowed=false`, and `split_or_freeze_allowed=false`.
- Output paths use the `_full_v6` suffix so old dry-runs and failed attempts are
  not overwritten.

This change only prepares a reproducible dry-run/execution config. It does not
authorize or launch the 400-record paid GPU pass.

GPU-free dry-run result:

- Command:
  `python scripts/run_p2_llm_labeling.py --config configs/p2_llm_label_full_v6.yaml --dry-run`.
- Remote commit: `25d83d8fbdcaf02882b7c135b819d192f6a1bd3c`.
- API/model calls: none; `api_called=false`, `model_weights_loaded=false`,
  `gpu_device_present=false`.
- Selected records: 400 total, with source counts Baidu Baike 7, patent 84,
  CMNEE 309.
- Distant-supervision coverage in selected records: 15 matched, 385 unmatched.
- Prompt/token budget:
  initial input tokens min/mean/max = 1678 / 1770.7775 / 1848;
  maximum context tokens = 3946 of 8192;
  worst-case request count = 800 including one retry for every record.
- Remote and local dry-run manifest SHA256:
  `78f0e94bbc6b188ba34d480dbc619bc407c9461249fc2e6e96fd4b0918cc6bce`.
- Remote and local dry-run log SHA256:
  `0212b2be4ca7b8a063578ba634c4d27297a9b1bfb7e859e70cb90479780f1c59`.

The full-v6 pass is technically preflighted but remains blocked on explicit
human approval, live GPU price confirmation, and a CNY/GPU-hour cap.

## 2026-07-21 - Human approved bounded 250-record P2 LLM proposal pass

The human reviewed the v6 sanity issues in `docs/错误清单.md` and approved a
bounded 250-record LLM proposal pass rather than the full 400 records.

Fixes prepared before launch:

- Added `p2-schema-draft-v2`, allowing `EQUIPMENT -> EQUIPMENT` `PART_OF` only
  for explicit component/system cases.
- Added `p2-llm-label-v5`, clarifying `USES` direction, complex nested
  component attachment, and damaged-text behavior.
- Added `docs/p2_schema_examples_draft_v2.jsonl` with compact examples for
  equipment-to-equipment `PART_OF`, nested component structure, and a negative
  control/scheduling case.
- Added quality filtering for proposal selection: skip patent `source_split:
  test` candidates and reject obvious long digit-noise spans.
- Added `configs/p2_llm_label_250_v1.yaml` with `_250_v1` output paths.

Approval scope:

- Records authorized: 250.
- Live 4090 price recorded by the human: 2.7 CNY/hour.
- GPU-hour cap: 3.0 hours.
- Cost cap: 8.1 CNY.
- Full 400-record pass remains unauthorized.
- Human annotation, split/freeze, P3/P4/P5 remain unauthorized.

Checkpoint/resume policy:

- Every request is cached under `/root/project/cache/p2_llm_label` by full
  request hash.
- If the job is paused or interrupted, rerunning the same config resumes from
  cached requests and only calls the model for missing hashes.
- Existing output paths are protected by `overwrite: false`; partial final
  outputs are written atomically only after the run completes.

GPU-free dry-run after final authorization:

- Remote/local commit: `5f59bbaae2af0d4888f8628ad84bfb26dc056cfd`.
- Config SHA256:
  `fd0dca453fd69018b597a00956aae6c500dcb91ca6f6492fa36a06222f7c88d8`.
- API/model calls: none; `api_called=false`, `model_weights_loaded=false`,
  `gpu_device_present=false`.
- Selected records: 250.
- Source counts: Baidu Baike 7, patent 66, CMNEE 177.
- Selection excludes damaged `patent` `source_split: test` candidates; the
  audited bad row `domain-candidate-0028` is not selected.
- Maximum context tokens: 3956 of 8192.
- Worst-case request count: 500 including one retry for every selected record.
- Remote/local dry-run manifest SHA256:
  `c1c72ddd7e93dbd4bfb6f3ee33629e172a6ed56af9954487ebd48c5c9b712e84`.
- Remote/local dry-run log SHA256:
  `9df2d4ac3de6a2af9164b1b3a06a032eb806b011fd9ca95a0142dc30fca7019d`.

## 2026-07-21 - 250-record v1 failed gate; cache-only v2 reparse passed

The first bounded 250-record run completed but failed the configured quality
gate:

- Run ID: `p2-llm-label-250-v1`.
- Commit: `61688ce058267e279cfd1d1b0aed1599761b21c7`.
- Records: 250.
- Parse failures: 35/250.
- Parse failure rate: 14.0%, above the 5% gate.
- Main cause: invalid LLM relations caused whole-record rejection, especially
  `USES`, `HAS_METRIC`, and `PART_OF` type-matrix violations.

Human instruction after restart: clear erroneous experiment data and keep only
an explanation of what was wrong. The project therefore keeps a non-row-level
error record in `docs/P2_250_ERROR_RECORD.md`; failed v1 row-level artifacts
are removed from active experiment storage.

Corrective action:

- Commit: `30b783ea003d9a55e6dff28fffb7e1a2d7a99bce`.
- Added a P2 proposal-only parser mode that drops invalid relations while
  keeping entity parsing strict and final evaluation parsing strict by default.
- Added `--execute-from-cache` so cached outputs can be re-parsed in GPU-free
  mode without additional LLM calls.
- New run ID: `p2-llm-label-250-v2-cache-reparse`.
- New model calls: 0.
- Cache hits: 263.
- Records: 250.
- Parse failures: 7/250.
- Parse failure rate: 2.8%.
- Invalid relations dropped and logged: 125.
- Success gate: passed.

Current gate remains P2. Human annotation, split/freeze, P3/P4/P5, and the
400-record full pass remain unauthorized.
