# P1 Public Data Validation

Generated on 2026-07-15 from `configs/p1_public_data.yaml`. The conversion was
executed on AutoDL in GPU-free mode at code commit `7191703`.

## Gate 1

- 12 official split files were normalized and reloaded successfully.
- 12 deterministic support files cover K = 1, 5, and 10 with seed 42.
- 100 entity spans per dataset (400 total) were sampled; every
  `text[start:end] == span` check passed.
- The remote and local report hashes match.

| Dataset | Split | Records | Entities | Relations | Gold |
| --- | --- | ---: | ---: | ---: | --- |
| CLUENER | train | 10,748 | 23,971 | 0 | yes |
| CLUENER | dev | 1,343 | 3,072 | 0 | yes |
| CLUENER | test | 1,345 | 0 | 0 | no |
| Few-NERD SUP | train | 131,767 | 340,387 | 0 | yes |
| Few-NERD SUP | dev | 18,824 | 48,770 | 0 | yes |
| Few-NERD SUP | test | 37,648 | 96,902 | 0 | yes |
| DuIE 2.0 | train | 171,293 | 491,450 | 322,218 | yes |
| DuIE 2.0 | dev | 20,674 | 59,761 | 39,231 | yes |
| DuIE 2.0 | test | 101,311 | 0 | 0 | no |
| CMNEE | train | 12,000 | 128,157 | 99,716 | yes |
| CMNEE | dev | 2,000 | 21,163 | 16,351 | yes |
| CMNEE | test | 3,000 | 39,264 | 31,075 | yes |

CMNEE entities include event triggers, event arguments, and coreference
mentions. Its relations encode trigger-to-argument edges and coreference edges.

## Source Audit

- Few-NERD's official SUP link was dead. The conversion uses the DFKI-SLT
  Hugging Face mirror pinned at revision `205f3e9`, whose dataset card declares
  CC BY-SA 4.0.
- CMNEE is pinned at ModelScope revision `5337fbd`; the ModelScope API declares
  Apache-2.0.
- The CLUENER archive does not bundle a license file. The project policy records
  Apache-2.0, but redistribution stays disabled until upstream evidence is
  archived.
- The official DuIE archive and its `License.pdf` are retained privately; the
  PDF hash is recorded in the YAML config.
- DuIE contains nine source annotations that cannot form legal exact spans:
  eight in train and one in dev. They were explicitly rejected and logged, not
  silently repaired. This is 9 of 362,074 source object values.
- DuIE lacks source offsets. Repeated surfaces use the fixed nearest-exact-match
  rule with deterministic start-offset tie breaking. Ambiguity counters remain
  in `conversion_report.json`.

The public CLUENER and DuIE test releases contain text but no gold labels. Their
normalized filenames end in `_test_unlabeled.jsonl`; downstream evaluation must
refuse to treat those empty annotations as all-negative gold. The fixed plan's
"full official test" requirement therefore needs a documented decision before
offline CLUENER test metrics are run.

## Backup

- Remote archive: `/root/autodl-tmp/backup/p1/p1_data_backup.tar.gz`
- Local private copy: `D:\yinsir\backups\P1\p1_data_backup.tar.gz`
- Bytes: `184027514`
- SHA256: `e472122c3abf62039d088fb0c016b69dca44db8bac4716eed188630ad440a341`
- Archive listing check: passed, 703 entries
- Detailed reports: `D:\yinsir\backups\P1\`

No dataset content is tracked by Git.
