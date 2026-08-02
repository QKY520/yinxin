# FULL-IE F5 Protocol Freeze

Date: 2026-08-02
Gate: `FULL_IE_F5_PROTOCOL_FREEZE_APPROVED`
Status: `DONE_FROZEN_NOT_AUTHORIZED`

## Outcome

F5 is complete in AutoDL no-card mode. The final protocol now has one
hash-locked 60-cell inventory: 30 domain NER+RE cells and 30 CLUENER NER cells.
Every cell and execution node remains unauthorized, with
`model_calls_allowed=false`. F5 freezes future work; it does not authorize or
execute F6, final evaluation, aggregation, or paper propagation.

The matrix remains `0/60` complete. Twelve domain A/B/C/D K=5 cells retain
hash-verified P5 NER Stage N outputs for future reuse, but none is a complete
full-IE cell until its required Stage R result exists.

## Frozen Contract

- Report cells: `60`, comprising `30` domain and `30` CLUENER cells.
- Unique final config IDs: `60`.
- Unique final output paths: `120` (per-query plus aggregate).
- Stage N nodes: `48`, comprising `12` hash-reused P5 nodes and `36` planned
  nodes.
- Domain Stage R nodes: `24`.
- E/E-prime verification nodes: `24`.
- Locked resources: `13`; locked source/config files: `34`.
- Seeds: `42/43/44`; K values: `1/5/10` under the approved literal inventory.
- Cell status: `12` `STAGE_N_DONE`, `48` `PLANNED`, `0` complete.
- Future gates remain explicit per node; no cell can run from this manifest
  alone.

The original deletion-only atomic verifier is retained. A valid `no` deletes
an atom; invalid verifier output conservatively keeps it. Type gating is
disabled. The F4b observations remain locked negative/mixed diagnostics:
E deleted correctly `25/36 = 69.44%`, and E-prime deleted correctly
`25/38 = 65.79%`. Neither is rewritten as passing `70%`, and no positive CoVe
claim is frozen.

The sole F4a relation parser revision is also retained: invalid relation atoms
are logged and dropped under the r1 sanitizer. Exact direction, schema,
duplicate policy, prompt order, and negative results remain unchanged.

## P5 Stage N Reuse Audit

All `12 x 170 = 2,040` reused per-query rows were verified against locked
files. The audit checks:

- canonical F5 cell IDs against the historical P5 `domain_test` dataset and
  legacy config names;
- exact ID coverage and gold-record equality with frozen `domain_test`;
- valid prompt and raw-output SHA256 values;
- five unique demonstration IDs per query;
- fixed-random A behavior and three distinct A seed sets;
- exact B/C/D demonstration replay within each seed;
- glossary/RAG field shape and config-specific absence rules; and
- exactly three retained RAG passages for every reused D row.

The first enhanced prepare invocation stopped on the expected historical
metadata difference (`domain_test` plus legacy P5 config names versus canonical
F5 IDs). A bounded compatibility map was added only to the reuse validator.
Canonical final cell IDs remain unchanged. No old P5 row was edited.

## Artifacts And Hashes

The versioned package is under `configs/full_ie_f5_freeze_20260802/`.

| Artifact | SHA256 |
| --- | --- |
| `freeze_inputs.json` | `5649a8f0e797c69e2ee7d3eb8156c87de89dda853271ec97bb4bfb7be3155d37` |
| `freeze_manifest.json` | `592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e` |
| canonical manifest | `e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae` |
| `cell_inventory.csv` | `dec872aa139289e3cc0bcfe32d75f93dfb45e1f7431af8bda6f791e52aa5cc09` |
| `SOURCE_SHA256.txt` | `a654bd164250e3a866cdf6c189b04511da5b7da66dad0de67f9e13bb8d8e1031` |
| `RESOURCE_SHA256.txt` | `519d18af46d36eb5c0724ceaaed60565351d35dc5ecd7f9727ceeb9fc24f18b7` |
| `REUSED_STAGE_N_SHA256.txt` | `9c14c5af8b495d5fb957bd83c20625caf0375206eb7db3aa7658422e48bd5184` |
| `freeze_report.json` | `34c67f7081e207ce4b2e87cff034efb7d09b240cf8b1472dcb41c1ced683d627` |
| `FREEZE_ARTIFACT_SHA256.txt` | `aff71cc3917d7c3fa2ac79b0aa5033b67e575d82a9b6ac967b4672b5142bf751` |

The manifest locks absolute authoritative resource paths, including labeled
official CLUENER dev for future evaluation and frozen `domain_test`. F5 read
those files only for hashes, row counts, and P5 reuse integrity. It generated
no prompts or predictions and made no tuning decision from final labels.

## Validation

- No-card preflight: `nvidia-smi` returned `No devices were found` and
  `/dev/nvidia0` was absent.
- No Python/vLLM/Qwen/runner process or screen session was present.
- Focused F3/manifest/freeze regression tests: `21/21` passed remotely.
- Full tracked AutoDL regression suite: `185/185` passed from the workspace
  root.
- An earlier full-suite invocation from outside the workspace produced one
  import error because `scripts` was not on `sys.path`; the corrected invocation
  passed all 185 tests. The failed invocation is disclosed rather than hidden.
- Independent manifest validation with `--verify-files` passed all 60 cells,
  13 resources, 34 source locks, and 12 reuse locks.
- `FREEZE_ARTIFACT_SHA256.txt` passed `7/7` remotely and locally.

## Backup, Cost, And Safety

The technical backup contains exactly 12 F5 implementation, test, input, and
generated files. Both remote and local extracted copies pass `12/12` hashes.

- Remote backup:
  `/root/autodl-tmp/backup/full_ie/f5_protocol_freeze_20260802/`.
- Local backup: `backups/FULL_IE/f5_protocol_freeze_20260802/`.
- Backup manifest SHA256:
  `381dcbbac20ddfdb7eb1862583c7cf1650de5d72e144e48e49e15a3d85d0956b`.
- Archive SHA256:
  `b2a2afe2ab767b9c1f981ac0b1f74df483fbb4f43d6f22d7ec2a0e8922e29e93`.
- Model calls: `0`; paid GPU cost: `0 CNY`.

No vLLM/model process was started. No final cell, F6 replay, final prompt,
official CLUENER evaluation, Stage R execution, aggregation, manuscript edit,
GitHub synchronization, or user-owned P6/M1/M2 artifact operation occurred.

## Next Gate

`FULL_IE_F5_PROTOCOL_FREEZE_APPROVED` is consumed. The next planned phase is F6
no-card leakage-safe RAG replay preparation, but it is not authorized. Stop and
wait for a separate bounded F6 gate.
