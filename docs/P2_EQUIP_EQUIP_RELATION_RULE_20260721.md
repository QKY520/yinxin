# P2 EQUIPMENT-to-EQUIPMENT Relation Rule

Date: 2026-07-21
Phase: P2 annotation agreement and adjudication

## Rule

For `EQUIPMENT -> EQUIPMENT` relations, distinguish carrying/mounting from
composition:

- `USES`: use when the source sentence uses carrying or deployment wording,
  including `搭载`, `部署`, `挂载`, `装备`, `配装`, `携带`, `装载`, or `加装`.
- `PART_OF`: use only when the source sentence uses composition wording,
  including `组成`, `包括`, `包含`, `构成`, `是...的一部分`, `归属`, `隶属`, `下辖`,
  or `由...组成`.
- If neither side is explicit, do not infer a relation from domain common
  sense. Flag the row for adjudication when the relation matters.

## Reason

The user identified a systematic failure mode: the LLM tends to convert
`missile mounted on aircraft` into `missile PART_OF aircraft`. That is a
composition-vs-carrying confusion. The user-reported audit found that about 51%
of 147 `EQUIPMENT -> EQUIPMENT PART_OF` labels are affected, so this is not a
minor cleanup issue.

## Operational Impact

- Agreement F1 can still be computed, but it is not enough for freezing.
- Before P2 split/freeze, the adjudication sheet must correct rows where
  `EQUIPMENT -> EQUIPMENT PART_OF` is paired with carrying/deployment wording.
- The generated `data/annotation/adjudication_sheet.csv` must include both
  A/B disagreements and these trigger-audit rows.
- Future LLM proposal prompts and schema definitions must preserve this rule.

## Output Files

The GPU-free agreement script writes:

- `logs/p2_annotation_agreement_report.json`
- `data/annotation/adjudication_sheet.csv`

The report records counts of `EQUIPMENT -> EQUIPMENT PART_OF`, likely
`USES`-vs-`PART_OF` confusion, validation errors, and whether the annotation
agreement threshold passed.
