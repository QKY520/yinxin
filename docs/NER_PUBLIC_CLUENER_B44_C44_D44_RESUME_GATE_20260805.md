# CLUENER Public-NER Seed44 Resume Gate

Date: 2026-08-05

Human gate: `NER_PUBLIC_CLUENER_B44_C44_D44_RESUME_APPROVED`

Status: `CONSUMED_CLOSEOUT_DONE`

## Purpose And Checkpoint

The human explicitly requested continuation after the first paid window was
paused and later reported a new RTX 4090 price of `2.8 CNY/hour`. This bounded
recovery gate extends only the unfinished tail of
`NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`; it does not reopen any other cell
or claim workflow.

Nine of the twelve public-NER cells are complete and passed the sequential
row-count, output-hash, and parse-failure checks: all A/B/C/D seed42 and seed43
cells, plus A seed44. The exact resume checkpoint is:

- `cluener:B:k5:s44`: incomplete, with 285 retained SHA256 cache entries and
  no per-query or summary output;
- `cluener:C:k5:s44`: not started;
- `cluener:D:k5:s44`: not started.

The interrupted B seed44 log is preserved and must be versioned before the
runner recreates the canonical log path. No completed output may be overwritten.

## Locked Execution Contract

- Execution manifest:
  `/root/autodl-tmp/full_ie/npub_cluener_abcd_k5_20260805/execution_manifest.json`.
- Manifest SHA256:
  `cee31bd5a1285dedbd07d8eac92593f8603e2504247717d1f3d4ee805e3363f3`.
- The same Qwen2.5-7B-Instruct, vLLM, prompt, parser, generation, support,
  glossary, and F6 replay contracts remain fixed.
- The same 1,343 labeled official CLUENER dev rows are required for every cell.
- Existing cache entries may be reused only by exact request hash.
- The 13-entry `PREINFERENCE_SHA256.txt` check passed again at
  `2026-08-05T19:50:32+08:00`.
- The resumed sequence starts at `cluener:B:k5:s44` and may continue only to
  C seed44 and D seed44.

## Time And Cost Lock

- Live price reported by the human: `2.8 CNY/hour`.
- Successful resume preflight: `2026-08-05T19:50:32+08:00`.
- Target paid window: 90 minutes, through `2026-08-05T21:20:32+08:00`, about
  `4.2 CNY`.
- Hard stop: 120 minutes, at `2026-08-05T21:50:32+08:00`, at most about
  `5.6 CNY` for this resume window.
- Platform billing is authoritative. At the hard stop, issue no new request;
  preserve and back up any partial cache and outputs.

## Stop And Closeout Rules

Stop before the next cell if a completed cell has parse-failure rate `>=5%`,
if any lock/path check changes, or if vLLM/runner health fails. Preserve every
negative result. If all three cells finish, run the existing finalizer over all
12 cells, stop vLLM, verify zero model/runner processes and released GPU memory,
create and hash-verify the remote backup, and mirror lightweight artifacts to
`D:\yinsir`.

Until all 12 cells pass final closeout, official matrix accounting remains
`4/60`; the runtime checkpoint may be reported separately as `9/12` public
cells complete. A successful closeout changes accounting to `16/60`.

This gate does not authorize result-to-claim interpretation, paper or LaTeX
editing, E/E-prime, K scans, RE, domain reruns, IE051, any other F8/F9 cell,
submission, GitHub synchronization, or hardware release. After closeout, stop
for `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED`.

## Execution Resolution

B/C/D seed44 completed under the unchanged locks, and the final 12-cell v2
validation passed. The human resumed the no-card closeout on 2026-08-06; clean
tracked tests, complete remote backup, local lightweight mirroring, cost
recording, and machine checks passed. This gate is consumed and no cell may be
rerun. See `docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_CLOSEOUT_20260806.md`.
