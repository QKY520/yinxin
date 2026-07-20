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
