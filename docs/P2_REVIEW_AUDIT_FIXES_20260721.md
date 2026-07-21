# P2 Review Audit Fixes - 2026-07-21

Source audit: `docs/问题建议1.md`

Scope: 250-row P2 v2 review sheet,
`backups/P2/p2_review_sheet_llm_250_v2_cache_reparse.csv`.

Implemented fixes:

- Added `configs/p2_schema_draft_v3.yaml`.
- Widened `USES` to allow `EQUIPMENT` or `MODULE` heads with
  `EQUIPMENT`, `MODULE`, or `TECH_SCHEME` tails when explicitly supported.
- Widened `HAS_METRIC` to allow `EQUIPMENT` or `MODULE` heads with
  `METRIC` or `TECH_SCHEME` tails for capability or parameter concepts.
- Kept `PART_OF` as part-to-whole, with `EQUIPMENT`/`MODULE` on both sides,
  and strengthened direction wording.
- Added `configs/p2_llm_prompt_v6.yaml` for future GPU runs with stricter
  entity-boundary rules.
- Added annotation-guide rules for numeric weapon components, deployment modes,
  organizations, `EQUIPMENT` versus `MODULE`, and `PART_OF` direction.
- Added cache-only reparse support using an optional `parse_schema` so old
  cached model outputs can be interpreted under a newer schema without changing
  request hashes or spending GPU time.
- Marked final parse failures in the review sheet as `LLM_FAILED`, while
  keeping annotator and adjudication fields blank.

Deferred:

- No fuzzy span matching is implemented for now. The remaining span-location
  failures should be manually annotated from blank text.
- No new LLM prompt run is launched in this refinement pass.
