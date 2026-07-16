# P2 14B Deployment Readiness Report

Date: 2026-07-16

Status: GPU-free implementation and dry-run verification complete; stopped
before model inference, paid GPU use, and human annotation.

Code commit used by both active dry-runs:
`472711e8f1ac496e1822993fd67f096a683a2c55`

## Approved Scope And Current Gate

The continuation after deterministic distant supervision authorized only:

- implementation of the independent Qwen2.5-14B-Instruct-AWQ proposal path;
- remote tests in AutoDL GPU-free mode;
- tokenizer-only prompt and token-budget dry-runs; and
- a deployment and cost proposal for a later human decision.

It did not authorize vLLM startup, an inference API call, paid GPU mode, the
400-record full pass, human annotation, dataset splitting, or test freezing.
Both checked-in run configurations therefore remain
`execution.authorized: false` with a null `approval_record`.

The next gate is explicit, sanity-only GPU and budget approval. Approval of the
10-record sanity pass would not authorize the 400-record pass.

## Immutable Inputs

| Artifact | Version | SHA256 |
| --- | --- | --- |
| Approved schema | `p2-schema-draft-v1` | `a3b2e8dcb81a6223058e028cdadcc6aecb87a10968d8ff0454aa7e535102ac56` |
| Prompt definitions | `p2-llm-label-v1` | `d1a2569ad6a93122937c493d5b5d1b66fbb216716c4e27590c7e5a5056f7c739` |
| Ten approved synthetic examples | Pause A examples | `8e7f427fab7a0bb1586b299aeb23a6ceff43747fc2c85c213d75a6e14aaea423` |
| Candidate corpus | 400 public passages | `32622228a7e0d45b31ce7ee2c0f78bcad0a5aa4a07ad8d01212bd03d3c19ee4f` |
| Distant-supervision proposals | 400 records | `b40e9d5c34c27d22b699d758af79c88705e4e4637184458aaae04bbaa05af96b` |

Prompt wording is stored separately from the approved schema so that prompt
revision does not silently mutate the schema approval artifact. The LLM prompt
does not expose distant-supervision suggestions; disagreement is computed only
after independent LLM parsing.

## Active V2 Dry-Run Results

The dry-runs loaded only the local tokenizer to apply the exact chat template.
They verified input, schema, prompt, example, model-metadata, and P0-manifest
hashes. They did not load model weights or contact vLLM.

| Measure | Sanity v2 | Full v2 |
| --- | ---: | ---: |
| Selected records | 10 | 400 |
| Source counts (Baike / CMNEE / patent) | 4 / 3 / 3 | 7 / 309 / 84 |
| DS matched / unmatched | 3 / 7 | 15 / 385 |
| Initial input tokens, total | 13,758 | 544,311 |
| Initial input tokens, mean | 1,375.8 | 1,360.7775 |
| Initial input tokens, maximum | 1,418 | 1,438 |
| Maximum request context | 3,471 / 8,192 | 3,491 / 8,192 |
| Worst-case request count with one retry | 20 | 800 |
| Dry-run duration | 13.284 s | 19.698 s |

The maximum context includes the configured 2,048-token output allowance. Both
passes remain well below the fixed 8,192-token model context. The full-pass
figures are capacity planning only and do not authorize execution.

## Verified Artifacts

The four active v2 artifacts are preserved remotely and copied into the local
private `backups/P2` directory. Local and remote SHA256 values match.
The non-sensitive structured index is tracked as
`docs/p2_llm_dry_run_manifest.json`.

| Artifact | Remote path | Bytes | SHA256 |
| --- | --- | ---: | --- |
| Sanity manifest | `/root/autodl-tmp/backup/p2/p2_llm_label_sanity_v2_dry_run.json` | 10,116 | `1c07a6fa5c0fa91ec776bb89bc7961c64d0694e843853bc239051fa04ddd6caa` |
| Full manifest | `/root/autodl-tmp/backup/p2/p2_llm_label_full_v2_dry_run.json` | 256,692 | `b8208599be36d7f334743866686da81a421d73fe9052ac8728451feb52eb7888` |
| Sanity log | `/root/project/logs/p2_llm_label_sanity_v2.jsonl` | 378 | `66f4b025b723ea1dbd2fb12ef729b7771e192fe8b7a499a6da298fd2687f09e6` |
| Full log | `/root/project/logs/p2_llm_label_full_v2.jsonl` | 372 | `74f8df362ef2c8d72f6f58b65fa892aeabef49d289ed69f60dac988e39f9dd88` |

At the post-run audit, `/dev/nvidia0` was absent, `nvidia-smi` was disabled,
no vLLM/Qwen process or named session was present, the P2 LLM cache contained
zero files, and no actual LLM proposal, union, review-sheet, or execution-report
output existed. Each active manifest also records:

- `execution_authorized = false`;
- `gpu_device_present = false`;
- `api_called = false`;
- `model_weights_loaded = false`; and
- `paid_gpu_used = false`.

GPU inference spend remains 0 CNY.

## Superseded V1 Dry-Runs

The following dry-runs are retained for provenance but must not be used for a
deployment decision. They were generated before prompt definitions were split
from the schema artifact and reference superseded schema SHA256
`bee2197c8ea3baaba6132cb95660412addcc2817514f6f0671ca85b3de1f3259`.
They also used no GPU, API, or model weights.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `p2_llm_label_sanity_dry_run.json` | 10,022 | `47e9418c3997699cf6e3bf2c4eb9d87168b0668477d8650e92b20a975825064e` |
| `p2_llm_label_full_dry_run.json` | 256,598 | `f176f2aa6e37777b3c0c869721d7886b9fc28c631a211ea15c478d1df7a9f42d` |

They are marked superseded rather than deleted, preserving the correction
history and preventing selective loss of an invalidated artifact.

## Proposed Sanity-Only GPU Step

This proposal is not authorization. If the human later approves it:

1. The human verifies the live RTX 4090 price and explicitly approves the
   sanity budget, then switches AutoDL to paid GPU mode.
2. The agent records `nvidia-smi`, GPU model/free memory, conflicting processes,
   live price, start time, command, PID/session, config hash, and log path.
3. The agent commits a separate sanity-only approval record and authorizes only
   `p2_llm_label_sanity.yaml`.
4. The agent starts Qwen2.5-14B-Instruct-AWQ and runs exactly the fixed 10-record
   sanity selection. The 400-record configuration remains unauthorized.
5. The agent verifies all 10 rows reload, human fields remain untouched, and
   parse failures are below 5%. For 10 rows this requires zero parse failures.
6. The agent backs up and hash-verifies all lightweight outputs, reports measured
   runtime and cost, reminds the human to shut down, and stops for a separate
   full-pass decision.

The sanity cap is 0.25 GPU-hour. At the documentation estimate of 2.08 CNY/hour,
the cap would be approximately 0.52 CNY, but the live platform price must be
recorded before launch. A full-pass time and cost estimate will be derived from
the measured sanity run; no full-pass cap is approved or inferred now.
