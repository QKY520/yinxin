# P2 v6 Review Sheet Manual Audit

Date: 2026-07-20

This is a lightweight quality audit for the 10-record `p2-llm-label-sanity-v6`
review sheet. It is not formal annotation and must not be treated as the
two-annotator agreement sample.

## Files

- CSV for spreadsheet review:
  `D:\yinsir\backups\P2\v6_verify\p2_review_sheet_llm_sanity_v6.csv`
- JSONL source copy:
  `D:\yinsir\backups\P2\v6_verify\p2_review_sheet_llm_sanity_v6.jsonl`
- Run report:
  `D:\yinsir\backups\P2\v6_verify\p2_llm_label_sanity_v6_report.json`

If Excel shows mojibake, import the CSV as UTF-8 with BOM, or inspect the JSONL
through a UTF-8 editor. The file content itself was verified as normal UTF-8 on
the AutoDL Linux host.

## What To Check

For each of the 10 rows, read `text_display` and inspect:

- `llm_entities_json`: whether suggested entity spans are useful and not
  obviously over-broad or missed.
- `llm_relations_json`: whether relations are explicitly supported by the same
  local text.
- `union_entities_json` and `union_relations_json`: whether the combined
  distant-supervision plus LLM proposal is acceptable as a human review aid.
- `disagreement_flags_json`: whether disagreements point to reasonable review
  work rather than systematic prompt failure.

Use the approved schema in `docs/P2_ANNOTATION_GUIDE_DRAFT.md`:
`EQUIPMENT`, `MODULE`, `TECH_SCHEME`, `METRIC`; relations `USES`,
`HAS_METRIC`, `PART_OF`.

## Do Not Do During This Audit

- Do not start formal annotation.
- Do not create support/dev/test splits.
- Do not create `data/FROZEN`.
- Do not edit prompt, schema, thresholds, glossary, or RAG settings based on
  future test information.
- Do not overwrite the machine proposal fields.

## Decision To Report Back

Report one of these outcomes:

- `approve_full_v6`: the 10-row proposal quality is good enough to run the
  400-record P2 LLM proposal pass, subject to GPU price and cost cap approval.
- `revise_before_full`: there are systematic problems; include 2-3 concrete
  examples by `review_id`.
- `stop_gpu_work`: do not spend more GPU now.

The 400-record full-v6 pass remains blocked until the human explicitly approves
paid GPU use, live price confirmation, and a CNY/GPU-hour cap.
