# P2 Adjudication Preparation Report

Date: 2026-07-21
Mode: AutoDL GPU-free

## Inputs

- `data/annotation/annotator_a_250.csv`
  - Rows: 250
  - SHA256: `865cac599fdcfdb868648ace96b12378427745e42ea6d470863cc5898bc93f5a`
- `data/annotation/annotator_b_100.csv`
  - Rows: 100
  - SHA256: `621faf549448066bf8ebed1063b4199f0e3f7d08087df3035ac8660f78ce6646`
- `data/annotation/agreement_sample_ids.json`
  - Agreement IDs: 100
  - SHA256: `1a15f9b31252a8b8397028346ccb20f18d37ab2e83332c5dcf68b60ce7a538ee`

## Agreement Results

Entity exact span+type micro agreement:

- Precision: `1.0000`
- Recall: `0.9821`
- F1: `0.9909`
- TP/FP/FN: `602/0/11`

Relation exact-triple agreement, diagnostic only:

- Precision: `0.9649`
- Recall: `0.9649`
- F1: `0.9649`
- TP/FP/FN: `275/10/10`

The entity agreement threshold `>= 0.80` is passed. This alone does not allow
freezing because adjudication and schema validation still have blockers.

## Validation Blockers

The current annotation files have 7 validation errors:

- `domain-candidate-0006`: overlapping entities and one invalid
  `EQUIPMENT -> TECH_SCHEME PART_OF`.
- `domain-candidate-0094`: four overlapping-entity errors.
- `domain-candidate-0182`: one overlapping-entity error.

These rows are included in the adjudication sheet.

## EQUIPMENT-to-EQUIPMENT PART_OF Audit

The new carrying-vs-composition rule was applied:

- Carrying/mounting/deployment wording such as `搭载`, `部署`, `挂载`, `装备`,
  `配装`, `携带`, `装载`, `加装` should be `USES`.
- Composition wording such as `组成`, `包括`, `包含`, `构成`, `是...的一部分`,
  `归属`, `隶属`, `下辖`, `由...组成` supports `PART_OF`.

Annotator A, all 250 rows:

- Total relations: `661`
- `EQUIPMENT -> EQUIPMENT PART_OF`: `147`
- Likely true `PART_OF`: `38`
- Likely `USES` confusion: `43`
- Mixed triggers: `3`
- No explicit composition trigger: `63`
- Rows needing adjudication from trigger audit: `46`
- Relation instances needing adjudication from trigger audit: `109`

Annotator B, 100 rows:

- Total relations: `285`
- `EQUIPMENT -> EQUIPMENT PART_OF`: `65`
- Likely true `PART_OF`: `14`
- Likely `USES` confusion: `16`
- Mixed triggers: `1`
- No explicit composition trigger: `34`
- Relation instances needing adjudication from trigger audit: `51`

## Generated Outputs

- `logs/p2_annotation_agreement_report.json`
  - SHA256: `23db71bc64a3f92d6a9f47088600714c136ce8ad53dc3652b5c4a372026d3706`
- `data/annotation/adjudication_sheet.csv`
  - Rows: `51`
  - SHA256: `601ec1e8e4951c87c679074f42495092db0a082361540898fe6a82c639773938`

Adjudication sheet reason counts:

- `A_B_DISAGREEMENT`: `1`
- `A_B_DISAGREEMENT;EQUIP_EQUIP_PART_OF_TRIGGER_AUDIT`: `1`
- `A_B_DISAGREEMENT;EQUIP_EQUIP_PART_OF_TRIGGER_AUDIT;SCHEMA_VALIDATION_ERROR`: `1`
- `A_B_DISAGREEMENT;SCHEMA_VALIDATION_ERROR`: `2`
- `EQUIP_EQUIP_PART_OF_TRIGGER_AUDIT`: `46`

## Gate Decision

Do not split or freeze yet.

The next required human action is to complete `data/annotation/adjudication_sheet.csv`:

- Fill `adjudicated_entities_json`.
- Fill `adjudicated_relations_json`.
- Fill `adjudication_notes`.
- Apply the carrying-vs-composition rule consistently.

After the adjudication sheet is complete, rerun
`scripts/evaluate_p2_annotation_agreement.py` or the next gold-build script in
GPU-free mode, then proceed to support/dev/test split and dedup/freeze only if
validation passes.
