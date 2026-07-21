# P2 Adjudication Validation Report

Date: 2026-07-21
Mode: AutoDL GPU-free

## Input

- File: `data/annotation/adjudication_sheet.csv`
- Rows: `100`
- Final SHA256:
  `9d277bf918a74aa07f94f12917e5d9d9787e819b667f838fb778c6316042b1c1`

## Repair Policy

The human authorized the agent to make adjudication decisions. The applied
policy was conservative:

- `EQUIPMENT -> EQUIPMENT PART_OF` with carrying/mounting/deployment triggers
  and no composition trigger was changed to `USES`.
- `EQUIPMENT -> EQUIPMENT PART_OF` with no explicit composition trigger was
  removed.
- `EQUIPMENT -> EQUIPMENT PART_OF` with explicit composition triggers was kept.

This avoids preserving unsupported composition relations in the domain gold
data. RE remains auxiliary, so dropping uncertain relations is safer than
keeping false `PART_OF` triples.

## Fix Summary

The in-place repair changed 11 rows:

- `domain-candidate-0102`
- `domain-candidate-0111`
- `domain-candidate-0122`
- `domain-candidate-0135`
- `domain-candidate-0154`
- `domain-candidate-0168`
- `domain-candidate-0236`
- `domain-candidate-0240`
- `domain-candidate-0242`
- `domain-candidate-0253`
- `domain-candidate-0257`

Relation changes:

- `PART_OF -> USES`: `6`
- Dropped no-composition `PART_OF`: `18`
- Kept explicit-composition `PART_OF`: `16`

Repair report:

- `logs/p2_adjudication_fix_report.json`
- SHA256:
  `9285195236245feb94a9f1c715ae8ca67fea3dc5aa33bf0816bebf73423bf56a`

## Final Validation

Validation script:

- `scripts/validate_p2_adjudication.py`

Final validation result:

- Errors: `0`
- Warnings: `0`
- Filled rows: `100`
- Entities: `607`
- Relations: `259`
- `USES`: `102`
- `PART_OF`: `147`
- `HAS_METRIC`: `10`
- `EQUIPMENT -> EQUIPMENT PART_OF`: `16`
- `EQUIPMENT -> EQUIPMENT PART_OF` with composition trigger: `16`

Validation report:

- `logs/p2_adjudication_validation_report.json`
- SHA256:
  `f26160fc29dc9920dbd8d4fa71c2bf1b9771aca3f1380f09615f281fd4c1896d`

## Gate Status

The adjudication sheet is now structurally valid and passes the
carrying-vs-composition rule audit.

This does not automatically start split/freeze. The next step is to build the
domain gold records from the adjudicated 100 rows plus the accepted single
annotator rows as allowed by the P2 protocol, then run deduplication and freeze
only after explicit confirmation.
