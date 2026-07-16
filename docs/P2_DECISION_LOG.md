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
