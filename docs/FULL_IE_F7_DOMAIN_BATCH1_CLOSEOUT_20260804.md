# F7 Domain Final Batch 1 Closeout

Date: 2026-08-04

Gate: `FULL_IE_DOMAIN_FINAL_BATCH_APPROVED`

Final status: `DONE`

Matrix accounting: `0/60 -> 4/60`

## Scope

The consumed gate covered only four final domain cells:

- `domain:A:k5:s42`
- `domain:B:k5:s42`
- `domain:C:k5:s42`
- `domain:D:k5:s42`

Each cell reused its hash-locked 170-row P5 Stage N output and added Stage R
only. Stage N was not rerun. E/E-prime, seeds 43/44, K=1/10, CLUENER, F8/F9,
aggregation, manuscript changes, and GitHub synchronization were excluded.

The locked execution manifest was not modified:

```text
configs/full_ie_f7_domain_batch1_exec_20260803/execution_manifest.json
SHA256 893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1
```

## Paid Execution

Preflight found the approved RTX 4090 24 GB with zero used memory and no
vLLM, Qwen, runner, or active screen conflict. The human reported a live price
of `2.8 CNY/hour`. Qwen2.5-7B-Instruct was served through vLLM and the four
cells ran serially in A, B, C, D order.

| Config | NER P | NER R | NER F1 | NER FP | Exact RE P | Exact RE R | Exact RE F1 | RE TP/FP/FN | Relation parse failures | Mean relation latency (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| A | 0.475166 | 0.601677 | 0.530990 | 634 | 0.047923 | 0.035129 | 0.040541 | 15/298/412 | 4/170 | 2384.837 |
| B | 0.505608 | 0.614256 | 0.554662 | 573 | 0.079167 | 0.044496 | 0.056972 | 19/221/408 | 1/170 | 1362.214 |
| C | 0.511706 | 0.641509 | 0.569302 | 584 | 0.076046 | 0.046838 | 0.057971 | 20/243/407 | 3/170 | 1704.054 |
| D | 0.525135 | 0.613208 | 0.565764 | 529 | 0.073684 | 0.032787 | 0.045381 | 14/176/413 | 2/170 | 1572.130 |

All four final summaries have `status=COMPLETE`, `rows=170`, and
`matrix_complete_cell=true`. The batch report has `status=COMPLETE` and
`matrix_after=4/60`:

```text
/root/project/results/full_ie/final_v1/batches/f7_domain_batch1_seed42_abcd.json
SHA256 6862964e4fae61cff46f284fe3b42378a97cee637e44c173570b8851ee898934
```

## Interpretation Boundary

- `B-A` exact RE F1 is approximately `+0.016431`, a weak positive signal.
- `C-B` is approximately `+0.001000`, which is effectively tied at this
  resolution.
- `D-C` is approximately `-0.012590`; RAG did not improve exact RE in this
  batch.
- D predicted fewer relations and had 67 fewer absolute relation false
  positives than C, but it also lost 6 true positives. Its exact RE precision
  (`0.073684`) is therefore below C (`0.076046`).
- Every configuration has zero `HAS_METRIC` true positives.
- These are four single-seed final cells. They do not support a three-seed
  aggregate, significance statement, positive RAG-for-RE claim, or broad RE
  contribution.

The narrow NER fallback remains intact. This batch supplies complete-cell
provenance and weak/negative RE evidence; it does not change the existing
result-to-claim verdict to a positive full-IE verdict.

## Audit

Across 680 per-query rows, the run recorded:

- 647 model requests with 647 cache entries and prompt/request hashes;
- 52 deterministic skips and 19 retry requests;
- 10 relation parse failures, or `10/680 = 1.470588%`;
- zero unsupported entity/relation types and zero relation type-matrix
  violations;
- 1,840 `RELATION_DROPPED_INVALID_UNIT` sanitizer events, retained in the
  per-query audit rather than hidden or rewritten;
- 1,198.505 seconds of summed four-cell runner time.

Prompt text, raw model responses, complete cache records, per-query rows,
summaries, execution logs, compatibility views, and frozen dependencies are
retained in the verified backup. Negative and failed rows were not filtered.

## Finalization Repair

The first versioned `finalize-batch` attempt ran after all four cells were
complete and failed without changing model outputs:

```text
AttributeError: 'str' object has no attribute 'open'
```

The cause was passing the string `final_summary_path` directly to the
Path-only `sha256_file` helper. The locked v1 execution files and four cell
outputs were left unchanged. The failure log is preserved at:

```text
/root/autodl-tmp/full_ie/f7_domain_batch1_20260803/runtime/finalize_batch_v1_failed.log
SHA256 4c9760f09324bbcac63e1b5cbb5477300d33db9bcd43125b7b5f187ac33ca4b6
```

A versioned, no-model v2 repair wraps that value with `Path` before hashing:

| File | SHA256 |
| --- | --- |
| `scripts/finalize_full_ie_f7_batch_v2.py` | `5fa0640e6228e2d0d0bf871f0c75d8041510544d8ec00908bc93b556b0ed58c4` |
| `tests/test_full_ie_f7_batch_v2.py` | `48d776b2855833d99b3e1e6c30c7addfba01d7307bc3b811dfe807eb6330876a` |
| `configs/full_ie_f7_domain_batch1_finalize_v2_20260804/repair_manifest.json` | `591ef2d7db366ef2a76a3f334ef192e71f8cec6869a84d6e35a57142b4ad9626` |

The v2 repair made zero model calls. One initial test command omitted the
required `PYTHONPATH=src:.` and failed during import; that invocation is
disclosed rather than counted as a code failure. With the correct remote
environment, the v2 regression passed `1/1`, focused F7 tests passed `5/5`,
and the complete remote suite passed `200/200`.

## Backup, Cost, And Final Machine State

The paid observation envelope was approximately
`2026-08-04 08:35:16-09:16:19 CST` (`2,463` seconds), or approximately
`1.916 CNY` at `2.8 CNY/hour`. The AutoDL platform bill remains authoritative.
The four runner logs account for 1,198.505 seconds inside that envelope.

vLLM was stopped before closeout and no model process remained. After the
human returned the instance to no-card mode, final checks reported:

```text
GPU: No devices were found
cgroup memory.max: 2147483648
vLLM/Qwen/F7/runner processes: none
screen: one preserved historical dead F6 socket only
```

Remote verified backup:

```text
/root/autodl-tmp/backup/full_ie/f7_domain_batch1_20260804/
artifact manifest: 713/713 files verified
artifact_manifest.sha256 SHA256 46fee95aa6f5e89648cd75fa7e30d64bac19f142b770fd57433c0f23956f830f
archive bytes: 4465120
archive SHA256 0de4bc5b5cd4fe50015dcffe76c288961be05d234a4f16c7492c23916779159c
```

The archive, manifest, and lightweight result tree were mirrored to:

```text
D:\yinsir\backups\FULL_IE\f7_domain_batch1_20260804\
```

PowerShell verification matched the remote archive and manifest hashes and
checked all 17 mirrored lightweight result files with zero missing or hash
failures. No project Python ran on Windows.

## Gate Close

`FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` is consumed. F7 Batch 1 is complete and
contributes exactly four final cells. There is no open next experiment gate.
Seeds 43/44, E/E-prime, K scans, CLUENER final evaluation, F8/F9, aggregation,
paper propagation, and GitHub synchronization remain unauthorized.

The recommended next proposal is IE051: eight Stage R-only A/B/C/D K=5 cells
for seeds43/44, reusing locked P5 Stage N outputs. Its value is to produce a
three-seed RE mean/SD at minimal additional model scope, followed by an
immediate result-to-claim stop. IE051 is not approved by this report. If the
replicated RE signal remains weak, `HAS_METRIC` remains at zero TP, or D remains
non-positive versus C, the preferred paper route is the NER-centered fallback
with RE disclosed as an exploratory limitation.
