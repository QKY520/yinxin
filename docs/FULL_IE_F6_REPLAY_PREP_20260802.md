# FULL-IE F6 Replay Preparation

Date: 2026-08-02
Gate: `FULL_IE_F6_REPLAY_PREP_APPROVED`
Status: `PARTIAL_BLOCKED_MEMORY`

## Outcome

F6 is not complete. The leakage-safe domain RAG replay is complete and
hash-verified, but the CLUENER replay is `0/1343` because the AutoDL no-card
container has a hard 2 GiB cgroup memory limit. The frozen CPU FP32 embedding
and reranker weight files require at least 4,544,321,872 bytes before runtime
overhead, so the declared insufficient-memory stop condition fired.

No approximate retriever, FP16 fallback, lexical substitute, paid GPU, or
hardware change was used. No final model cell, prompt, prediction, or metric
was produced. Full-matrix accounting remains `0/60`.

## Bounded Scope

The gate authorized only no-card RAG replay preparation:

- domain: reuse the three hash-locked P5 D K=5 seed42/43/44 per-query RAG
  selections only if all three are exactly identical;
- CLUENER: run the frozen BGE-M3 normalized-vector, FAISS inner-product top-20,
  bge-reranker-v2-m3 top-3 retrieval contract on the 1,343-row labeled official
  dev split, without evaluation;
- reject source self-hits and fixed 8-gram containment at or above `0.80`;
- serialize query hashes and selected evidence only, never query text, gold,
  entities, relations, predictions, prompts, or raw model output; and
- make zero Qwen/vLLM/API calls and execute no Stage N, Stage R, verifier,
  aggregation, paper, or GitHub work.

The versioned input SHA256 is
`56b02bbc6861f49da3fb79cfdc5f4cb7798e0aca81422079eda6fadeab8426c6`.
It locks the F5 manifest SHA256
`592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e`
and all query, corpus, model-manifest, and P5 replay resources.

## Domain Replay

All three P5 D source files have 170 rows and matched each other exactly for
every query's three passage IDs and display strings. The output contains 170
ordered query rows and 510 selected passages.

| Audit | Result |
| --- | ---: |
| Query rows | `170` |
| Selected passages | `510` |
| Seed disagreements | `0` |
| Source self-hits | `0` |
| Prohibited serialized fields | `0` |
| 8-gram hits at or above `0.80` | `0` |
| Maximum 8-gram containment | `0.529148` |
| Mean 8-gram containment | `0.003612` |

The replay SHA256 is
`d2605817ed53e3ae8a7efd2adfb68641adebc9eaa7ed740a4141cec2ec63b91d`.
Its row schema is limited to `id`, `query_text_sha256`, `rag_passage_ids`,
`rag_passages`, and `selected_passages`; selected-passage objects contain only
`id` and `display`.

This is a prepared shared dependency, not a completed experiment cell. It does
not alter or complete any of the 12 reusable P5 NER-only Stage N cells.

## CLUENER Stop Condition

The first CLUENER attempt started in the sole `f6_cluener_replay` screen. It
validated the locked files, wrote checkpoint metadata, and then exited during
retriever initialization with a zero-byte log and zero replay rows. No Python
exception was available from that attempt, and cgroup `oom_kill` remained zero;
the report therefore does not claim an observed kernel OOM kill.

The capacity mismatch is independently decisive:

| Resource | Bytes |
| --- | ---: |
| cgroup `memory.max` | `2,147,483,648` |
| BGE-M3 discovered weights | `2,273,250,020` |
| Reranker discovered weights | `2,271,071,852` |
| Frozen dual-model lower bound | `4,544,321,872` |
| Lower-bound headroom | `-2,396,838,224` |

The implementation now performs this lower-bound check before loading either
model and writes `cluener_memory_preflight.json`. The second invocation failed
explicitly before model loading with the same values. Its preflight SHA256 is
`06592b8833d5b733a668f7e6e1d224051f3d6bbf9c31e30dfc96ed1fcd768890`.

The first attempt read official CLUENER dev only to establish locked query
IDs/text hashes for replay preparation. It serialized no label, prompt,
prediction, or metric. CLUENER remains `0/1343`, and this provides no public
benchmark or generalization evidence.

## Validation

- AutoDL preflight and closeout both showed `No devices were found`,
  `/dev/nvidia0` absent, no screen, and no model/runner process.
- All P0 model files passed the full `65/65` SHA256 manifest check. This took
  `356.2` seconds and included BGE-M3, reranker, Qwen2.5-7B, and 14B-AWQ.
- Initial implementation tests passed: F6 `6/6`, affected regressions `67/67`,
  and full tracked suite `191/191`.
- After adding the memory lower-bound preflight, F6 tests passed `7/7` and the
  full tracked suite passed `192/192`.
- Tests ran only in the isolated AutoDL workspace built from tracked HEAD plus
  the five explicitly listed F6 files. No untracked P6/M1/M2 file was deployed,
  read, executed, modified, or committed.
- Source locks passed `12/12`; all nine resource/source-replay locks passed;
  the domain prepare lock passed `5/5`.
- The final partial manifest passed `24/24` remotely and locally. Local
  PowerShell also reloaded the UTF-8 JSON and confirmed 170 unique rows, three
  passages per row, and zero prohibited fields.

Preserved operational failures:

- the first CLUENER initialization exit, its zero-byte log, and zero-row
  checkpoint are retained;
- four Windows/SSH quoting attempts failed before their intended state change
  and were replaced by explicit absolute-path commands;
- one archive attempt received a transient SSH connection refusal before any
  remote command ran, then succeeded after connectivity returned; and
- one local `ConvertFrom-Json` check used the Windows default code page and
  failed on UTF-8 Chinese text; the byte hashes were already correct, and the
  explicit UTF-8 rerun passed without modifying the artifact.

## Backup And Hashes

Remote extracted backup:
`/root/autodl-tmp/backup/full_ie/f6_replay_prep_20260802/`.

Local extracted backup:
`backups/full_ie/f6_replay_prep_20260802/`.

| Artifact | SHA256 |
| --- | --- |
| `F6_PARTIAL_ARTIFACT_SHA256.txt` | `b5db900a87cb5791a8327825b5014da82b60a7b831ee0f903514f424468a4f66` |
| `f6_prepare_report.json` | `a3dba4e8a9782423b1fc944066781dde2ce690907550cda0358e74f8bf044b2d` |
| `domain_rag_replay.json` | `d2605817ed53e3ae8a7efd2adfb68641adebc9eaa7ed740a4141cec2ec63b91d` |
| `cluener_memory_preflight.json` | `06592b8833d5b733a668f7e6e1d224051f3d6bbf9c31e30dfc96ed1fcd768890` |
| partial archive | `0ad69881c15f423cf0d6dc620427ce73614bbf53209625acd395cf1a731bf28f` |

The archive is 140,462 bytes and contains 35 tar entries. Its extracted
manifest verifies 24 implementation/config/artifact/log files; the manifest
itself is covered by the archive hash.

## Cost, Evidence, And Next Gate

Paid GPU cost is `0 CNY`. Qwen/vLLM/API calls are `0`. F6 is
`PARTIAL_BLOCKED_MEMORY`, not `DONE`; the gate is consumed at the declared stop
condition. F7, F8, F9, final evaluation, aggregation, paper propagation, and
GitHub synchronization remain unauthorized.

Recovery requires a separate bounded human gate and materially more than the
4.54 GB lower bound; at least 8 GiB container memory is a practical minimum.
If AutoDL cannot raise no-card memory, the recommended recovery is a short paid
4090 boot solely to unlock sufficient container RAM, while retaining CPU FP32
retrieval and making no Qwen/vLLM calls. That route requires a versioned guard,
fresh live price, preflight, and explicit
`FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED`; it is not authorized by this
report.
