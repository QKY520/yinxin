# P2 Annotation Completion Audit - 2026-07-21

Input files checked:

- `docs/人工标注完成.md`
- `data/annotation/annotator_a_250.csv`
- `data/annotation/annotator_b_100.csv`
- `data/annotation/agreement_sample_ids.json`

Remote validation was run in GPU-free mode on AutoDL.

## Numeric Check

Agreement sample:

- Shared IDs: 100
- Missing in A: 0
- Missing in B: 0
- Rows with `LLM_FAILED`: 7
- Source counts: Baidu Baike 5, patent 24, CMNEE 71
- JSON/span validation errors: 0

Agreement metrics, treating exact `(start, end, type)` entity matches as the
primary unit:

- Entity micro precision: 1.0000
- Entity micro recall: 0.9821
- Entity micro F1: 0.9909
- Relation exact-triple micro precision: 0.9649
- Relation exact-triple micro recall: 0.9649
- Relation exact-triple micro F1: 0.9649

The generated disagreement/adjudication sheet contains 5 rows.

## Gate Assessment

The numeric agreement is above the `0.80` threshold, but the files do **not**
qualify as completed human double annotation for P2 Gate 2.

Reason:

- `scripts/p2_annotate.py` describes the process as simulating annotator A/B.
- `scripts/p2_annotate_v2.py` generates A from the union proposal and B from
  the LLM raw proposal.
- This is machine/rule-assisted pseudo-annotation, not two humans independently
  annotating 100 passages from blank text.
- The high F1 is therefore not valid evidence of human agreement.

Allowed use:

- Treat these files as a machine-assisted draft or pre-adjudication diagnostic.
- Use the 5-row disagreement sheet to inspect common differences.
- Use the scripts and notes to understand what rule-based corrections were
  applied.

Not allowed:

- Do not treat this as gold annotation.
- Do not compute final agreement claims from this run.
- Do not split/freeze support/dev/test based on these labels.
- Do not proceed to P3/P4/P5 using these labels as the self-built domain gold
  set.

## Required Next Step

Run true human annotation for the 100 agreement passages:

1. Annotator A and annotator B must independently annotate from text according
   to `docs/P2_ANNOTATION_GUIDE_DRAFT.md`.
2. For the agreement subset, do not generate A/B labels by scripts.
3. Machine proposals may be used only as optional review hints outside the
   agreement measurement, or the paper must clearly state that agreement is not
   independent human agreement.
4. After true A/B files are filled, recompute exact span+type entity agreement
   F1 in GPU-free mode.

Current P2 Gate 2 status: **blocked on true human double annotation**.
