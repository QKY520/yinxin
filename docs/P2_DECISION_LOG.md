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
