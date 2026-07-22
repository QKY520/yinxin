# P2 Domain Gold Freeze Report - 2026-07-22

## Scope

This report records the P2 domain gold build, split, test freeze, deduplication,
repair log, verification, and backup.

Execution was limited to AutoDL GPU-free mode. No vLLM server, paid GPU
inference, P3, P4, or P5 work was started.

## Inputs

- Annotator A 250-row file:
  `data/annotation/annotator_a_250.csv`
- Final 100-row adjudication file:
  `data/annotation/adjudication_sheet.csv`
- Candidate corpus:
  `/root/autodl-tmp/data/domain_candidates.jsonl`

Input hashes from the build manifest:

| Input | Rows | SHA256 |
| --- | ---: | --- |
| annotator A | 250 | `865cac599fdcfdb868648ace96b12378427745e42ea6d470863cc5898bc93f5a` |
| adjudication | 100 | `9d277bf918a74aa07f94f12917e5d9d9787e819b667f838fb778c6316042b1c1` |
| candidates | 400 | `32622228a7e0d45b31ce7ee2c0f78bcad0a5aa4a07ad8d01212bd03d3c19ee4f` |

## Structural Repair

The build first ran an audit-only pass over all 250 rows. Exactly one row
required conservative repair:

- `domain-candidate-0123`

Repair policy:

- adjudicated rows are strict and are not repaired;
- single-annotator rows may drop exact duplicate entities;
- single-annotator rows may drop the shorter entity only when it is strictly
  nested in a longer entity;
- relations touching a nested-dropped entity are dropped and logged;
- non-nested overlaps or equal-length overlaps fail the build.

Applied repair:

- Dropped nested entity: `攻击艇` `[93,96)` `EQUIPMENT`.
- Kept entity: `快速攻击艇打击武器项目` `[91,102)` `TECH_SCHEME`.
- Dropped one `PART_OF` relation whose endpoint referenced the removed entity.

Repair log:

- Remote: `/root/project/logs/p2_domain_gold_repair_log.json`
- Local backup:
  `D:\yinsir\backups\P2\domain_gold_freeze_20260721\p2_domain_gold_repair_log.json`
- SHA256:
  `4861bdfe2320b64d36bafff84d4887c684eea37d2f6dcd63cdad06525d841de8`

## Split And Counts

Split seed: `42`

| File | Records | Entities | Relations | SHA256 |
| --- | ---: | ---: | ---: | --- |
| `domain_gold_250.jsonl` | 250 | 1444 | 634 | `fb183c733d328124c35e527872eb9cb4ea839fdf7bea1059c2313e3ea207acdc` |
| `domain_support.jsonl` | 30 | 183 | 74 | `9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a` |
| `domain_dev.jsonl` | 50 | 307 | 133 | `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b` |
| `domain_test.jsonl` | 170 | 954 | 427 | `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0` |

The domain test split has at least 100 records and is now frozen. After this
freeze, no prompt, threshold, schema, glossary, or RAG setting may be tuned
using `domain_test.jsonl`.

## Deduplication

Protocol:

- fixed 8-gram containment against frozen domain test text;
- containment threshold: `0.80`.

Result:

- candidate records: 400;
- test records: 170;
- removed from RAG corpus: 170;
- retained RAG corpus records: 230.

Dedup log:

- Remote: `/root/project/logs/dedup.json`
- Local backup:
  `D:\yinsir\backups\P2\domain_gold_freeze_20260721\dedup.json`
- SHA256:
  `ebc0a79dbe5167f0e7daa0523242f99889e0280383981470de09ff9154c54768`

## Verification

Remote GPU-free tests:

```text
python -m unittest tests.test_build_p2_domain_gold
python -m unittest tests.test_schema tests.test_domain_data
```

Both passed.

Independent freeze verification:

```text
python scripts/verify_p2_domain_gold_freeze.py
```

The verifier reloaded all JSONL files with the unified schema validator, checked
record counts, checked both FROZEN markers, checked dedup/repair/manifest
presence, and recomputed manifest file hashes.

Verifier result:

```json
{"status":"ok","manifest_sha256":"6c7d9c1f3e361c2747e1a3b8181fcd9aeca324ebab915586096e686687d49a4a"}
```

## Backup

Remote archive:

- `/root/autodl-tmp/backup/p2/p2_domain_gold_freeze_20260722.tar.gz`
- bytes: `272250`
- SHA256:
  `a3711e2af4179d8398d8d497827ff703b1cfa4a8b0c05ea4de47837b9329ec3f`

Local archive:

- `D:\yinsir\backups\P2\p2_domain_gold_freeze_20260722.tar.gz`
- bytes: `272250`
- SHA256:
  `a3711e2af4179d8398d8d497827ff703b1cfa4a8b0c05ea4de47837b9329ec3f`

Local expanded verification copy:

- `D:\yinsir\backups\P2\domain_gold_freeze_20260721\`

## Gate Status

P2 domain gold split/freeze artifacts are generated, schema-valid, test-frozen,
deduplicated, locally backed up, and hash-verified.

P2 Gate 2 data-file conditions are satisfied:

- `domain_support.jsonl`, `domain_dev.jsonl`, and `domain_test.jsonl` exist.
- `domain_test.jsonl` has 170 records.
- `FROZEN` exists remotely under both data and project roots.
- `dedup.json` exists.

Do not enter P3/P4/P5 until the human explicitly approves the next gate.
