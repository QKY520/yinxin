# Minimum Full-IE Extension Tracker

**Date**: 2026-07-30

**Status semantics**:

- `PLANNED`: no execution authority.
- `PREPARED`: artifacts exist but the next gate is closed.
- `RUNNING`: allowed only under the exact recorded human gate.
- `DONE`: outputs are complete, hash-verified, and audited.
- `BLOCKED`: a declared stop condition fired.

Nothing in this tracker authorizes Python, data processing, prompt generation,
model/API calls, vLLM, GPU use, `domain_test` access, or any paper edit.

Current gate: `FULL_IE_RELATION_CALIBRATION_PREP_APPROVED` was explicitly
granted and consumed on 2026-07-30. IE020 is complete using the locked fresh
20-text non-test entity submissions on AutoDL no-card mode. The A/B relation
fields remain blank and annotation has not started. Stop before annotation
unless `FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED` is granted; returned-
file validation separately requires
`FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED`.

## Protocol and Implementation

| Run ID | Milestone | Purpose | Scope | Cells | Priority | Status | Gate / notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| IE000 | F0 | Confirm two-stage IE design | Plan only | 0 | MUST | DONE | Full-IE target and literal inventory confirmed |
| IE010 | F1 | Implement Stage R relation-only runner | Synthetic fixtures and legacy metadata only | 0 | MUST | DONE | Fixed prompt order, replay contract, deterministic skips, and future model gate |
| IE011 | F1 | Implement exact directed triple metrics | Synthetic fixtures | 0 | MUST | DONE | End-to-end exact key, type/FDR/coverage/conditional/zero-relation diagnostics |
| IE012 | F1 | Extend E/E-prime to relation atoms | Synthetic fixtures | 0 | MUST | DONE | Invalid output keeps atoms; entity drops cascade; legacy NER behavior preserved |
| IE013 | F1 | Implement aggregation and 60-cell manifest validation | Synthetic fixtures | 0 | MUST | DONE | Literal 30+30 inventory, hashes/statuses/arithmetic, three-seed mean/sample-SD |
| IE020 | F2 | Prepare non-test relation-calibration sheets | Existing fresh 20-text calibration set | 0 | MUST | DONE | A/B own locked entities only; 20+20 blank relation rows isolated and hash-audited |
| IE021 | F2 | Validate relation calibration | Exact directed endpoint/type triples | 0 | MUST | PLANNED | Annotation not started; separate annotation and validation approvals; diagnostic, not frozen-test IAA |
| IE030 | F3 | Freeze domain dev configs | A-E-prime, K=5, seed42 | 6 | MUST | PLANNED | Dev paths only |
| IE031 | F3 | Build CLUENER support bank and glossary | train_pool only | 0 | MUST | PLANNED | Fixed 30-record bank; record type coverage |
| IE032 | F3 | Build/dedup CLUENER RAG corpus | labels-stripped train_pool | 0 | MUST | PLANNED | Exclude support/tune/dev overlap |
| IE033 | F3 | Freeze CLUENER tune configs | A-E-prime, K=5, seed42 | 6 | MUST | PLANNED | Tune only; no official dev/test prompt output |

## Dev and Tune Gates

| Run ID | Milestone | Purpose | Dataset / split | Cells | Priority | Status | Gate / notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| DDEV1 | F4 | Relation-enabled A-D sanity | domain_dev50, K=5, seed42 | 4 | MUST | PLANNED | Paid gate; NER+RE metrics |
| DDEV2 | F4 | Entity+relation verification sanity | domain_dev50 E/E-prime, K=5, seed42 | 2 | MUST | PLANNED | Audit up to 20 dropped units per class |
| CDEV1 | F4 | Public NER A-D sanity | fixed CLUENER tune subset, K=5, seed42 | 4 | MUST | PLANNED | No official dev/test evaluation |
| CDEV2 | F4 | Public verifier E/E-prime sanity | fixed CLUENER tune subset, K=5, seed42 | 2 | MUST | PLANNED | Entity atoms only |
| FREEZE | F5 | Lock final protocol | Prompts/configs/resources/metrics/seeds | 0 | MUST | PLANNED | Required before any final evaluation access |

## Domain Final Matrix: 30 Reported Cells

| Run ID | Milestone | System / variant | K | Seeds | Reported cells | Stage work | Status |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK5-A | F7 | A fixed-random | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | PLANNED |
| DK5-B | F7 | B kNN | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | PLANNED |
| DK5-C | F7 | C kNN + glossary | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | PLANNED |
| DK5-D | F7 | D C + RAG | 5 | 42/43/44 | 3 | Reuse Stage N/RAG evidence; add Stage R | PLANNED |
| DK5-E | F7 | E D + verification | 5 | 42/43/44 | 3 | Verify combined D Stage N+R output | PLANNED |
| DK5-EP | F7 | E-prime C + verification | 5 | 42/43/44 | 3 | Verify combined C Stage N+R output | PLANNED |
| DK1-A | F7 | A fixed-random | 1 | 42/43/44 | 3 | New Stage N + Stage R | PLANNED |
| DK1-E | F7 | E D + verification | 1 | 42/43/44 | 3 | New D Stage N + Stage R + verifier | PLANNED |
| DK10-A | F7 | A fixed-random | 10 | 42/43/44 | 3 | New Stage N + Stage R | PLANNED |
| DK10-E | F7 | E D + verification | 10 | 42/43/44 | 3 | New D Stage N + Stage R + verifier | PLANNED |
| **Domain total** |  |  |  |  | **30** | All rows report NER and exact RE |  |

## CLUENER Final Matrix: 30 Reported Cells

All rows use the complete labeled official dev split. C/D/E/E-prime use the
frozen support-derived glossary and labels-stripped, deduplicated train-pool
RAG corpus. There is no RE metric.

| Run ID | Milestone | System / variant | K | Seeds | Reported cells | Status |
| --- | --- | --- | ---: | --- | ---: | --- |
| CK5-A | F8 | A fixed-random | 5 | 42/43/44 | 3 | PLANNED |
| CK5-B | F8 | B kNN | 5 | 42/43/44 | 3 | PLANNED |
| CK5-C | F8 | C kNN + support glossary | 5 | 42/43/44 | 3 | PLANNED |
| CK5-D | F8 | D C + train-text RAG | 5 | 42/43/44 | 3 | PLANNED |
| CK5-E | F8 | E D + verification | 5 | 42/43/44 | 3 | PLANNED |
| CK5-EP | F8 | E-prime C + verification | 5 | 42/43/44 | 3 | PLANNED |
| CK1-A | F8 | A fixed-random | 1 | 42/43/44 | 3 | PLANNED |
| CK1-E | F8 | E D + verification | 1 | 42/43/44 | 3 | PLANNED |
| CK10-A | F8 | A fixed-random | 10 | 42/43/44 | 3 | PLANNED |
| CK10-E | F8 | E D + verification | 10 | 42/43/44 | 3 | PLANNED |
| **CLUENER total** |  |  |  |  | **30** |  |

## Aggregation and Paper Gate

| Run ID | Milestone | Purpose | Scope | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AGG1 | F9 | Validate all final cells | 60 reported cells | MUST | PLANNED | No missing rows; hashes and counts match |
| AGG2 | F9 | Aggregate mean/SD | Three seeds per cell | MUST | PLANNED | Preserve deterministic/near-deterministic behavior |
| AGG3 | F9 | Paired uncertainty | Pre-specified contrasts, 10k bootstrap | MUST | PLANNED | Holm adjustment if p-values are reported |
| AGG4 | F9 | Result-to-claim decision | NER, RE, CoVe, K, public NER | MUST | PLANNED | Positive claims depend on observed evidence |
| PAPER1 | F9 | Propagate verified evidence | Markdown/LaTeX only after separate approval | MUST | BLOCKED | No paper edit under this plan |

## Accounting Check

```text
Domain final cells   = 18 K=5 + 12 K-scan = 30
CLUENER final cells  = 18 K=5 + 12 K-scan = 30
Complete matrix      = 30 + 30 = 60
Existing full cells  = 0
Existing NER stages  = 12 (reusable only after adding Stage R)
Missing report cells = 48
```

## F1 Closeout

- AutoDL mode: GPU-free/no-card; `nvidia-smi -L` returned `No devices found`,
  `/dev/nvidia0` was absent, and no vLLM/Qwen/extraction/verifier process ran.
- Verification: 28 new full-IE synthetic tests and 38 focused legacy
  extraction/verification/schema tests passed (`66/66`).
- Safety audit: no `domain_test`, support/dev/test prompt artifact, model/API,
  vLLM, GPU, manuscript, frozen data, or GitHub synchronization was used.
- Sync audit: approved code/tests have identical local/remote SHA256 values;
  old NER core and regression-test SHA256 values remain unchanged.
- Cost: `0 CNY` paid GPU; platform paid resources were not used.
- Evidence accounting is unchanged: RE and relation-aware E/E-prime are
  implemented but not model-run or evaluated; complete full-IE cells remain
  `0/60` and the existing `12/60` are Stage N only.

## F2 Preparation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_PREP_APPROVED` was bounded to IE020 and
  is consumed. It did not authorize annotation or returned-file validation.
- Inputs: locked A/B fresh human entity CSV files and the coordinator map were
  verified against fixed SHA256 values; 20 texts aligned exactly.
- Outputs: A/B each have 20 independently ordered rows containing only their
  own locked entities, an index guide, and blank relation fields. Delivery
  directories exclude the other role and coordinator map.
- Verification: 6 preparation/audit synthetic tests and all 158 repository
  tests passed remotely; the real package audit passed with 40/40 relation rows
  blank and locked entity cells preserved.
- Backup: remote and local 10-file packages match SHA256; root manifest is
  `5d2c55c60e24a1cdec12335f567ab5457dd8ee24e1d111ed1692694a48a840a4`.
- Safety/cost: AutoDL was GPU-free; no `domain_test`, prompt, model/API, vLLM,
  paper, or GitHub action occurred. Paid GPU cost was `0 CNY`.
- Evidence accounting remains `0/60`; preparation is not relation evidence.
  Stop before `FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED`.
