# CLUENER Public-NER A/B/C/D K=5 Final Closeout

Date: 2026-08-06

Gate chain:

- `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`
- `NER_PUBLIC_CLUENER_B44_C44_D44_RESUME_APPROVED`

Status: `DONE_RTC_COMPLETE`

## Scope Closed

All twelve authorized NER cells are complete: CLUENER labeled official dev,
all 1,343 rows, configurations A/B/C/D, K=5, and seeds 42/43/44. The official
unlabeled CLUENER test split was not used. No E/E-prime, K scan, relation
extraction, domain rerun, IE051, or other F8/F9 cell was executed.

Every cell contains 1,343 ordered per-query rows. Final validation found zero
unsupported entity types and zero relation predictions. The locked F3/F5/F6
support, glossary, and replay contracts remained unchanged. The execution
manifest SHA256 is
`cee31bd5a1285dedbd07d8eac92593f8603e2504247717d1f3d4ee805e3363f3`.

## Mechanical Results

The following table is a direct mechanical aggregation from the versioned v2
validation report. Values are three-seed mean and sample standard deviation;
no result-to-claim interpretation is performed here.

| Config | Seed F1 values (42/43/44) | Precision | Recall | F1 | FP count | Entity FDR |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | 0.439063 / 0.460048 / 0.386446 | 0.448636 +/- 0.036890 | 0.413086 +/- 0.056862 | 0.428519 +/- 0.037917 | 1569.0 +/- 306.8 | 0.551364 +/- 0.036890 |
| B | 0.515364 / 0.511791 / 0.514735 | 0.528488 +/- 0.001929 | 0.500217 +/- 0.002118 | 0.513964 +/- 0.001907 | 1371.0 +/- 7.2 | 0.471512 +/- 0.001929 |
| C | 0.518161 / 0.516925 / 0.517478 | 0.530932 +/- 0.001140 | 0.504774 +/- 0.001316 | 0.517521 +/- 0.000619 | 1370.0 +/- 8.7 | 0.469068 +/- 0.001140 |
| D | 0.511699 / 0.514286 / 0.514286 | 0.540764 +/- 0.002162 | 0.488715 +/- 0.000940 | 0.513424 +/- 0.001493 | 1275.0 +/- 8.7 | 0.459236 +/- 0.002162 |

The low A seed44 row is retained without selection or rerun. Across all 16,116
query-cell rows, the audit records 18,136 request attempts, 2,020 retries,
1,367 exact-hash cache hits, 5,159 sanitizer events, and 138 parse failures
(`0.856292%`). Every cell is below the locked 5% stop threshold.

## Finalizer And Tests

The original finalizer v1 failure is preserved:

```text
ValueError: cluener-dev-143: sanitizer events are not reproducible
```

The runner held `duplicate_key` as tuple `(9, 12, "scene")`; JSON persistence
stored the same value as list `[9, 12, "scene"]`. This was a finalizer audit
comparison defect, not a prediction or metric defect. The v1 script and all
results remain unchanged.

The versioned no-model repair and focused test hashes are:

- `scripts/finalize_ner_public_cluener_final_v2.py`:
  `5e25f34800e24fb897694119c40b369bc9148ba5de5dd43b4e9771151ebb8b9c`;
- `tests/test_finalize_ner_public_cluener_final_v2.py`:
  `362772972d79b83a3d6b8d0376416446b60ab24a0600d56b5243ba56e8df3c95`.

Validation results:

- focused v2 tests: `3/3 PASS`;
- frozen execution-workspace suite: `26/26 PASS`;
- finalizer v2: `PASS`, 12 cells and 1,343 rows per cell;
- final validation report SHA256:
  `7a1f1f110e9fea8f6a92398f5e3e25bd109b7e04cb7664664a7d99572bb62824`;
- clean current-HEAD tracked snapshot plus v2/test: `205/205 PASS`.

The first clean-suite invocation used an invalid `unittest -t` layout and
failed before test discovery because `tests/` is not an importable package. Its
log is preserved with SHA256
`3e3d0c90f98efcadf5a17718d0b682c055a05a69d03252e7e67182163d670b99`.
The corrected isolated-working-directory log has SHA256
`c3651f86d3a721fe3d7ca89e2ac019db668d949b33763f803c5e0bc85d3673c8`.

## Backup And Mirror

Complete remote backup:

- path:
  `/root/autodl-tmp/backup/full_ie/npub_cluener_abcd_k5_final_20260806/`;
- payload files: `18,239`;
- payload bytes: `193,722,743`;
- `SHA256SUMS` entries verified: `18,239/18,239`;
- `SHA256SUMS` SHA256:
  `db75f2f27a8063c0660f7a773456dc8d7db6bfa57a733e14f1f3ff0e8125294e`;
- source-to-backup `diff -qr`: no differences.

The full remote payload includes caches, raw model outputs, complete prompts,
results, configs, validation reports, workspaces, and all runtime logs.

Lightweight local mirror:

- path:
  `D:\yinsir\backups\full_ie\npub_cluener_abcd_k5_final_20260806\`;
- extracted files: `63`;
- archive bytes: `6,531,166`;
- archive SHA256:
  `daf54146a8c876b08d482ab86f3e72c52d505367bd7f5e30cf24c1f5aad3c996`;
- the locally copied full-backup `SHA256SUMS` hash matches the remote value.

The lightweight mirror includes all 12 per-query and summary files, configs,
the execution and pre-inference manifests, validation reports, sequence events,
interruption/pause logs, and non-vLLM cell logs. Large vLLM logs and request
caches remain in the complete verified remote backup.

## Cost And Machine State

The live RTX 4090 price was `2.8 CNY/hour`. The three preserved vLLM log
envelopes are:

| Window | Start | End | Seconds | Cost at 2.8 CNY/hour |
| --- | --- | --- | ---: | ---: |
| Initial | 2026-08-05 09:17:28 | 2026-08-05 11:09:41 | 6,733.514 | 5.237 CNY |
| Resume r2 | 2026-08-05 16:17:03 | 2026-08-05 17:52:32 | 5,728.696 | 4.456 CNY |
| Resume r3 | 2026-08-05 19:57:47 | 2026-08-05 20:58:49 | 3,661.852 | 2.848 CNY |
| **Total observable vLLM envelope** |  |  | **16,124.062** | **12.541 CNY** |

This is a reproducible log-envelope estimate, not the platform invoice. Card-
on overhead outside vLLM log birth/last-write times may be billed; the AutoDL
platform bill is authoritative.

The human returned the instance to no-card mode. Final checks show `No devices
were found`, cgroup memory `2,147,483,648` bytes, and no vLLM, Qwen, extraction
runner, sequence controller, or finalizer process.

## Accounting And Next Gate

Successful closeout changes literal accounting from `4/60` to `16/60`:

- 4 complete domain Stage N+R cells;
- 12 complete CLUENER NER cells;
- 8 domain Stage N-only cells;
- 36 wholly absent cells;
- 44 incomplete identities remain route-closed.

This mechanical closeout did not itself support a public-transfer claim. The
later `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` review is recorded below.
Positive RE, RAG-for-RE, CoVe, `HAS_METRIC`, K robustness, and complete-IE
claims remain unsupported. No paper, LaTeX, DOCX, submission, or GitHub sync
operation was performed.

## Post-Closeout Result-to-Claim Resolution

The bounded public-NER RTC completed on 2026-08-06 with verdict `partial` and
confidence `high`. It made no model call, result change, or manuscript edit.

- CLUENER `B-A` mean F1 is `+0.085445`.
- CLUENER `C-B` mean F1 is `+0.003557`, a small directionally positive
  lexicon result.
- CLUENER `D-C` mean F1 is `-0.004097`, while precision is `+0.009832` and
  FP is `-95`, reproducing the equipment-domain RAG precision/FP operating-
  point pattern.
- These results support limited, descriptive portability to this one
  additional Chinese NER benchmark. They do not support broad public-
  benchmark/cross-domain generalization, significance, SOTA, K robustness,
  public RE, CoVe, or complete IE.

The overall paper route remains NER-primary, with RE as an exploratory
negative result/limitation. Accounting remains `16/60`, and the other 44
identities remain route-closed. The versioned verdict is
`docs/RESULT_TO_CLAIM_NER_PUBLIC_CLUENER_ABCD_K5_20260806.md`.

The next possible action is the separately approved paper-only
`NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED` gate for exact files in
the complete `docs/JISE_OVERLEAF_LATEX_20260729/` project. This closeout and
RTC do not themselves authorize that edit.
