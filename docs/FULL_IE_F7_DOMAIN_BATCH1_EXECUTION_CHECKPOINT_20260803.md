# FULL-IE F7 Domain Final Batch 1 Execution Checkpoint

Date: 2026-08-03

Status: `AUTHORIZED_PREINFERENCE_PREPARED`

Approved gate: `FULL_IE_DOMAIN_FINAL_BATCH_APPROVED`

## Outcome

The human explicitly granted the exact F7 Domain Final Batch gate. The bounded
execution package is prepared and independently preflighted in AutoDL no-card
mode, but model inference has not started because no GPU is currently attached.
This checkpoint incurred `0 CNY` and leaves complete-cell accounting at
`0/60`.

The authorized scope is exactly, in serial order:

1. `domain:A:k5:s42` Stage R over the frozen P5 Stage N output;
2. `domain:B:k5:s42` Stage R over the frozen P5 Stage N output;
3. `domain:C:k5:s42` Stage R over the frozen P5 Stage N output;
4. `domain:D:k5:s42` Stage R over the frozen P5 Stage N output.

Stage N reruns, E/E-prime, other seeds, K=1/K=10, CLUENER, F8/F9,
aggregation, paper edits, and GitHub synchronization remain excluded.

## Compatibility View

The four frozen P5 Stage N files use historical row metadata
`dataset=domain_test` and long-form P5 configuration names. The frozen Stage R
runner accepts canonical `dataset=domain` and `config=A/B/C/D`. A deterministic
compatibility view therefore changes only those two metadata fields. It does
not change gold records, Stage N predictions, example IDs, glossary terms, RAG
passages, prompt hashes, raw-output hashes, parse flags, or latency metadata.

The preparation generated and validated `680` rows in total. Original Stage N
predictions changed: `false`.

| Cell | Compatibility-view SHA256 | Execution-config SHA256 |
| --- | --- | --- |
| A | `31a09a8e3d48258c335dd4f2bc1b546bf500a61354054d42934a76c7d05cca14` | `233ec98c3a0f1773c0ba4eaed2eb37bb5176aac987b5449f9df97adf0d51a402` |
| B | `eed657044481a6f10874beedf7249d1a3187916444d9a4344b654b132b914703` | `ea77055d9224ad92cd6a1b94fde9014bdf6c9ea9425406497c9f6341828b833e` |
| C | `e1b59f6cc395b7f3c43fb6ccf5a14e794abb48f289c87770c9a47dcdb33b1f94` | `c82683803d5217f519dafc72866c862044d515ce00321ca478be2cd643aff335` |
| D | `5d3219e36f7bb7e729a07b9c6e40f3ce48198563b9fe68e5ffb4b965f3c4d62b` | `dbe87c85f8f30e2941e1794e34bf1f176f7c10c47735ca34387b10d3c11e172c` |

Execution manifest:
`configs/full_ie_f7_domain_batch1_exec_20260803/execution_manifest.json`

Execution-manifest SHA256:
`893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1`

The manifest locks the preparation, finalization, and regression-test source
files. Those files and the dated execution directory must not be edited in
place. Any necessary change requires a new versioned execution package and a
new preflight.

## Verification

All project Python was run remotely through `autodl-paper`; none was run on
Windows.

- New F7 regression tests: `4/4` passed.
- F7 plus directly affected tests: `21/21` passed.
- Complete remote regression suite: `199/199` passed.
- Real-data no-card preparation: passed for all four 170-row inputs.
- Batch preflight: passed with all result and cache targets absent.
- Prompt/model requests during preparation: `0`.

The isolated execution workspace is:
`/root/autodl-tmp/full_ie/f7_domain_batch1_20260803/workspace`.
Compatibility views are under:
`/root/autodl-tmp/full_ie/f7_domain_batch1_20260803/inputs_v1`.

## Current Machine And Cost State

The resumed SSH check succeeds. AutoDL is in GPU-free/no-card mode:

- `nvidia-smi` reports `No devices found`;
- cgroup memory limit is `2 GiB`;
- `/root/autodl-tmp` has about `59 GB` free;
- no vLLM, Qwen, Stage R, preparation, or finalization process is active;
- the only screen entry is the preserved historical dead
  `2148.f6_cluener_recovery` session;
- all F7 model/cache/result targets remain absent.

No paid inference has started. F7 cost at this checkpoint is `0 CNY`.

## Paid-Run Entry Condition

The human must switch the existing instance to the approved RTX 4090 24 GB and
report the live hourly price. Before any model call, the agent must confirm:

- GPU model is RTX 4090 24 GB and memory used is below `500 MiB`;
- no vLLM/Qwen/runner or conflicting active screen exists;
- the execution manifest and all frozen source/config/view hashes match;
- every current and future output/cache target for the batch is absent;
- the paid cap remains the earlier of `2.0 hours` or `5.6 CNY` at
  `2.8 CNY/hour`, unless the human explicitly approves a recalculated cap.

Each cell must run `preflight-cell`, frozen `run_stage_r.py`, and
`finalize-cell` before the next cell begins. A completed cell must contain 170
unique rows and independently recomputed NER and exact directed RE metrics.
The batch stops and preserves artifacts on any hash mismatch, collision,
corruption, conflict, budget limit, or relation parse-failure rate of at least
`10%` in a completed cell.

Operational success means all four frozen cells complete and pass the declared
recomputation and provenance checks. It does not mean that RE scores are
guaranteed positive; negative results remain mandatory evidence and cannot be
edited, selected away, or relabeled.
