# FULL-IE F6 CLUENER Replay Recovery

Date: 2026-08-03
Gate: `FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED`
Status: `DONE`

## Outcome

The blocked CLUENER part of F6 replay preparation is complete. The frozen
CPU-FP32 BGE-M3 plus bge-reranker-v2-m3 retrieval path produced and
independently validated all `1,343` labeled official CLUENER dev replay rows.
Each row contains exactly three labels-stripped evidence passages. Together
with the previously completed 170-row domain replay, the F6 replay dependency
is now complete.

This recovery did not run a final model cell. It made zero Qwen, vLLM, API,
Stage N, Stage R, verifier, metric, aggregation, or paper calls. Full-matrix
accounting therefore remains `0/60`.

## Bounded Recovery Contract

- Human gate: `FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED`.
- Human-reported RTX 4090 price: `2.8 CNY/hour`.
- GPU purpose: unlock the 120 GiB container-memory tier only.
- Retrieval device and precision: CPU FP32 with `CUDA_VISIBLE_DEVICES` empty.
- Dataset/split: the frozen 1,343-row labeled official CLUENER dev query set,
  used only to prepare retrieval replay; no evaluation was performed.
- Frozen base config SHA256:
  `56b02bbc6861f49da3fb79cfdc5f4cb7798e0aca81422079eda6fadeab8426c6`.
- Recovery guard SHA256:
  `a13100c46755f2b353fb87c014a7d1604c4764e9aa8c64832e6ef031d6659b34`.
- Forbidden throughout: GPU retrieval, FP16, fallback retrieval, Qwen/vLLM,
  final metrics, `domain_test`, Stage N/R, aggregation, paper edits, and GitHub
  synchronization.

The versioned guard is
`configs/full_ie_f6_cluener_recovery_20260803/recovery_guard.json`. It does not
modify the hash-locked F6 base config.

## Execution And Recovery

The first guarded invocation stopped before retrieval because the initial
runner rejected any visible GPU, even though the approved contract required a
visible paid card solely for container memory. That failure is retained in
`recovery.log`. The runner was corrected so that it masks CUDA from the legacy
CPU runner and still fails if GPU execution is enabled.

The corrected first window started at `08:54:02 CST`, rebuilt the frozen
embedding index, and checkpointed `479/1343` rows before the user-requested
pause at `09:46:57 CST`. The checkpoint snapshot is retained under
`snapshots/paused_479/`; its seven-file manifest passes `7/7`, and the JSONL
SHA256 at the pause is
`cee61dcb2ce8e68c3cf741cf11fb30ea633ecfd264e97e043aad8aef6cb502cd`.

After the card was restarted, the resume window began at `14:22:11 CST`.
It revalidated every source lock, rebuilt only the in-memory retrieval index,
accepted the existing 479 rows, and appended rows 480 through 1,343. It
finished at `14:44:31 CST` with status `DONE`. No existing row was overwritten
or filtered.

## Independent Validation

The independent validator returned `VALID` and recomputed the replay audit:

| Audit | Result |
| --- | ---: |
| Query rows | `1343` |
| Unique query IDs | `1343` |
| Selected passages | `4029` |
| Rows with other than three passages | `0` |
| Source self-hits | `0` |
| Prohibited serialized fields | `0` |
| 8-gram hits at or above `0.80` | `0` |
| Maximum 8-gram containment | `0.785714` |
| Mean 8-gram containment | `0.017302` |
| Qwen/vLLM/API/model calls | `0` |

The final replay and per-row JSONL SHA256 values are:

- `cluener_rag_replay.json`:
  `36a529b9cd8cd0a78d2438376885263d5b9d63cb4967a0e88ad50eedbdffb455`;
- `cluener_rag_replay_rows.jsonl`:
  `ba592a229ee96f32538a4b2a44b82b3149a8b02a9db0130c7380c32efc80c262`;
- `f6_recovery_report.json`:
  `17b0e086c944ef6c285721de4d793a74681ce0d73be2bb210addf02e22358e62`;
- `f6_recovery_validation_report.json`:
  `5e9b55487c11c61c60015888456356b747783c77f8501de650b8e35ac9434de1`.

Remote tests ran on AutoDL only. The repository-standard
`python -m unittest discover -s tests -v` passed `195/195`. At the user's
request, `pytest 9.1.1` was installed in the remote venv; `pytest -q tests`
passed `195` tests plus `8` subtests. A root-level pytest discovery attempt is
documented here: it incorrectly collected a historical test snapshot under
`refine-logs` and failed import during collection. No source test failed, and
no historical artifact was modified or removed.

## Backup And Hashes

Remote extracted backup:
`/root/autodl-tmp/backup/full_ie/f6_cluener_recovery_20260803/`.

Local extracted backup:
`backups/full_ie/f6_cluener_recovery_20260803/`.

The recovery backup contains the final artifacts, paused checkpoint, failed
and successful logs, guard/config/source locks, validation output, and both
test logs. Its recursive manifest passes `38/38` remotely and locally.

| Artifact | SHA256 |
| --- | --- |
| `RECOVERY_BACKUP_SHA256.txt` | `e098c138c201fdc1e0804183da5eb97e1d6e8208fb2abd5b20d27adcb18f2947` |
| `f6_cluener_recovery_20260803.tar.gz` | `add0145f8597d4cc09e5988aefc4ef53fe5e7c1fe93e91c3022b88ab4204f2e4` |

The archive is `1,826,926` bytes and contains 52 tar entries. Local PowerShell
independently reloaded the UTF-8 rows and confirmed `1,343` rows, `1,343`
unique IDs, three passages per row, `DONE`, and `VALID`; no local project
Python was run.

## Cost And Closeout

The first observable corrected runner window lasted `3,174.640` seconds,
approximately `2.469164 CNY`. The resume report records `1,340.081` seconds,
approximately `1.042285 CNY`. Combined observable runner time is `4,514.721`
seconds (`1.254089` hours), approximately `3.511449 CNY` at `2.8 CNY/hour`.
This excludes paid-card idle time before, between, and after the runners;
AutoDL platform billing is authoritative.

Final machine inspection found RTX 4090 memory at `0 MiB`, no compute app, no
Qwen/vLLM/recovery runner, and no active screen. One preserved historical dead
screen socket remains and is not a running process. The human must now shut
down the paid 4090 instance.

F6 is complete as replay preparation only. It adds no final metric and no
paper-facing evidence. F7 domain final execution, F8 CLUENER final execution,
F9 aggregation/result-to-claim, paper edits, and GitHub sync all require new
explicit gates.
