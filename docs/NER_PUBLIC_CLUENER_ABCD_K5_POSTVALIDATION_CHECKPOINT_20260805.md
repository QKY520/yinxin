# CLUENER Public-NER Post-Validation Checkpoint

Date: 2026-08-05

Gate chain:

- `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`
- `NER_PUBLIC_CLUENER_B44_C44_D44_RESUME_APPROVED`

Status: `HUMAN_PAUSED_POSTVALIDATION_PREBACKUP`

## Completed Runtime Scope

All twelve authorized CLUENER NER cells are complete: configurations A/B/C/D,
K=5, and seeds 42/43/44 over all 1,343 labeled official CLUENER dev rows. The
last cell, `cluener:D:k5:s44`, completed at
`2026-08-05T20:58:30+08:00`. The sequence controller accepted all twelve
per-query files and summaries. Every cell remained below the locked 5% parse-
failure stop threshold.

The completed seed44 tail records the following raw checkpoint values:

| Cell | F1 | Parse failures |
| --- | ---: | ---: |
| A/s44 | 0.3864455660 | 14/1,343 |
| B/s44 | 0.5147354320 | 11/1,343 |
| C/s44 | 0.5174778391 | 10/1,343 |
| D/s44 | 0.5142857143 | 19/1,343 |

This table is a runtime checkpoint, not a result-to-claim interpretation. The
versioned final report remains the source for the complete 12-cell metrics.

## Finalizer Audit

The original finalizer v1 was executed and its failure is preserved:

```text
ValueError: cluener-dev-143: sanitizer events are not reproducible
```

This was a finalizer comparison defect, not result corruption. The runner held
`duplicate_key` as tuple `(9, 12, "scene")`; JSON serialization stored the same
value as list `[9, 12, "scene"]`. The v1 script was not modified.

The versioned no-model repair adds JSON-value normalization before comparing
sanitizer events:

- `scripts/finalize_ner_public_cluener_final_v2.py`, SHA256
  `5e25f34800e24fb897694119c40b369bc9148ba5de5dd43b4e9771151ebb8b9c`;
- `tests/test_finalize_ner_public_cluener_final_v2.py`, SHA256
  `362772972d79b83a3d6b8d0376416446b60ab24a0600d56b5243ba56e8df3c95`.

Remote validation completed before the human pause:

- focused v2 tests: `3/3 PASS`;
- frozen execution-workspace suite: `26/26 PASS`;
- v2 final validation: `PASS`, 12 cells, 1,343 rows per cell;
- report:
  `/root/autodl-tmp/full_ie/npub_cluener_abcd_k5_20260805/validation/final_validation_report_v2.json`;
- report SHA256:
  `7a1f1f110e9fea8f6a92398f5e3e25bd109b7e04cb7664664a7d99572bb62824`.

No result-to-claim interpretation or paper edit was performed.

## Machine And Cost Checkpoint

The human returned the instance to no-card mode. The post-switch audit showed
`No devices were found`, a 2 GiB cgroup memory limit, and no vLLM, extraction
runner, sequence controller, or finalizer process. The live price for the paid
resume window was `2.8 CNY/hour`; platform billing remains authoritative.

Resume preflight passed at `2026-08-05T19:50:32+08:00`, and the last model cell
completed at `20:58:30+08:00`. Final paid-window and total-block cost accounting
must be recorded during closeout from the preserved timestamps and platform
billing; this checkpoint does not invent a billed duration.

## Exact Resume Point

The human paused after v2 validation and before backup. On resumption, do not
restart vLLM and do not rerun any cell. Continue in no-card mode with only:

1. build a clean current-HEAD tracked-file test snapshot that physically
   excludes all protected untracked P6, M1/M2, and old-plan files;
2. overlay the already versioned v2 finalizer and its test, then run the full
   tracked remote test suite and record the exact count;
3. create the complete remote run backup and SHA256 manifest, then verify every
   manifest entry;
4. mirror lightweight results, validation reports, runtime events, and closeout
   records to `D:\yinsir\backups` and verify hashes;
5. update the playbook, guide, `AGENTS.md`, `HANDOFF.md`, full-IE tracker, and a
   versioned final closeout document;
6. commit only the authorized v2/test and closeout documentation changes.

Official matrix accounting remains `4/60` until the backup, mirror, and final
closeout pass. A completed closeout may change it to `16/60`. Result-to-claim,
LaTeX/paper edits, E/E-prime, K scans, RE, domain reruns, IE051, remaining F8/F9
cells, submission, and GitHub synchronization remain unauthorized. After final
closeout, stop for a separate `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` gate.

## Resume Resolution

The human explicitly continued on 2026-08-06. The clean tracked suite, complete
remote backup, local lightweight mirror, cost record, and final documentation
all passed. This checkpoint is historical and no longer the active stop. The
authoritative outcome is
`docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_CLOSEOUT_20260806.md`; do not rerun any
cell.
