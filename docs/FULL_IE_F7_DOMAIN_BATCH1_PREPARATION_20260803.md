# FULL-IE F7 Domain Final Batch 1 Preparation

Date: 2026-08-03

Status: `PREPARED_AWAITING_GATE`

Required execution gate: `FULL_IE_DOMAIN_FINAL_BATCH_APPROVED`

## Outcome

The first F7 paid batch is now bounded as a four-cell Stage R-only proposal.
No execution authorization has been granted, no execution config has been
enabled, and no `domain_test` prompt, model call, vLLM process, Python command,
or final result was produced during this preparation step. Matrix accounting
remains `0/60`.

The proposal is recorded at
`configs/full_ie_f7_domain_batch1_20260803/batch_contract.json`. Its SHA256 is
`0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973`.
The contract keeps every authorization flag false until the exact human gate
is granted.

## Exact Scope

| Cell | Existing Stage N rows | Stage N SHA256 | Frozen config-contract SHA256 |
| --- | ---: | --- | --- |
| `domain:A:k5:s42` | 170 | `343f192e...99e8ab` | `bb92697b...ee66498` |
| `domain:B:k5:s42` | 170 | `cbf5b907...9f75e` | `77364a57...202649` |
| `domain:C:k5:s42` | 170 | `a0c1dd65...c17a4` | `1d686305...52a3c4` |
| `domain:D:k5:s42` | 170 | `ebaa68c9...a1ed0` | `248e5981...080f0e2` |

Only Stage R may run. The four existing P5 Stage N files are reused by exact
hash, for 680 total per-query inputs. Stage N is not rerun. E/E-prime and all
other cells remain outside the batch. If all four outputs pass independent
row/hash/metric validation, the literal complete-cell count will move from
`0/60` to `4/60`; a failed or corrupt cell is not counted.

The frozen Stage R contract remains unchanged:

- Qwen2.5-7B-Instruct FP16 through vLLM;
- prompt `stage_r_same_sentence_v1`;
- parser `r1_drop_invalid_relation_units`;
- one parser-aware retry;
- temperature `0.0`, top-p `1.0`, max tokens `768`, seed `42`;
- exact replay of each Stage N row's demonstration, glossary, and RAG metadata;
- exact directed `USES`, `HAS_METRIC`, and `PART_OF` evaluation.

The controlling F5 hashes are unchanged:

- freeze manifest:
  `592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e`;
- canonical contract:
  `e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae`;
- cell inventory:
  `dec872aa139289e3cc0bcfe32d75f93dfb45e1f7431af8bda6f791e52aa5cc09`.

## Runtime And Cost Bound

The four F4a A-D Stage R dev runs processed 200 rows in a combined
`485.761 s`. A simple 680/200 scaling gives `1651.5874 s`, or about
`27.5 min`, of runner time for this batch. This is only a planning estimate:
test entity counts, retries, vLLM startup, validation, backup, and paid-mode
idle time can increase the total envelope.

The proposed hard stop is the earlier of:

- `2.0` paid GPU hours; or
- `5.6 CNY` at the last reported `2.8 CNY/hour`.

The live hourly price must be reported again before execution. If it is not
`2.8 CNY/hour`, the CNY cap must be recomputed and explicitly accepted. The
AutoDL bill remains authoritative.

## Preflight And Stop Rules

Before a model call, the agent must verify the exact gate, RTX 4090 model,
free memory below 500 MiB used, absence of conflicting vLLM/Qwen/runner/screen
processes, every frozen hash and 170-row source lock, and absence of all output
targets. Dated execution copies may be created only after that preflight; F5
files are never modified in place.

The batch stops immediately on a hash/row mismatch, output collision, scope
escape, runner corruption, process conflict, 10% relation parse failures in a
completed cell, or the approved time/cost cap. A stopped or negative row is
preserved. Frozen-test outcomes cannot trigger prompt, parser, threshold,
schema, glossary, retrieval, or verifier changes.

After each cell, the per-query file must reload with 170 unique IDs and its
summary must recompute. After the batch, all prompts, cache entries, raw
outputs, rows, summaries, configs, logs, and manifests must be backed up and
hash-verified remotely and locally. vLLM must be stopped and GPU memory/process
release verified before reporting cost and asking the human to shut down.

## Explicit Exclusions

This proposal does not authorize Stage N reruns, E/E-prime, K=1/K=10,
seeds 43/44, CLUENER, F8/F9, cross-cell aggregation, manuscript changes, or
GitHub synchronization. It also does not claim that RE will improve or that a
completed cell supports a positive relation-extraction contribution.

## Machine State

At `2026-08-03T15:41:24+08:00`, SSH to `autodl-paper` returned
`Connection refused`. The instance was therefore unreachable and no paid or
model action occurred in this preparation step.
