# Minimum Full-IE Extension Tracker

**Date**: 2026-08-04

**Route decision**: `FULL_IE_STOP_AND_NER_FALLBACK_RTC_APPROVED` is consumed.
The human stopped the 60-cell completion route at the literal `4/60` evidence
state. The paper route is frozen to NER as the main contribution, with RE kept
only as an exploratory negative result/limitation.

**Focused route amendment**: `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED` is the
sole live experiment gate, status `AUTHORIZED_AWAITING_HUMAN_GPU`. It reopens
only the 12 canonical CLUENER A/B/C/D K=5 seed42/43/44 NER cells over all 1,343
labeled official dev rows. No cell has started, so current accounting remains
`4/60`. The human must boot the RTX 4090 24 GB and report the live price before
preflight or model calls. If all 12 cells pass closeout, accounting becomes
`16/60`; the other 44 incomplete identities remain `CLOSED`.

**Status semantics**:

- `PLANNED`: no execution authority.
- `PREPARED`: artifacts exist but the next gate is closed.
- `PREPARED_AWAITING_GATE`: an exact bounded execution proposal and hash exist,
  but all authorization/model-call flags remain false.
- `AUTHORIZED`: the exact human gate is open, but execution has not begun or is
  waiting for a human-only prerequisite.
- `RUNNING`: allowed only under the exact recorded human gate.
- `DONE`: outputs are complete, hash-verified, and audited.
- `BLOCKED`: a declared stop condition fired.
- `CLOSED`: intentionally not executed, or not continued, because an explicit
  human route decision removed the item from the active scope. `CLOSED` is not
  an execution failure, a blocked run, a negative empirical result, or evidence
  that an attempted experiment failed.

This tracker does not create execution authority by itself. Authority comes only
from the exact recorded human gate and remains bounded by its exclusions.

The `FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED`,
`FULL_IE_F3_CONFIG_PREP_APPROVED`, and
`FULL_IE_DOMAIN_DEV_SANITY_APPROVED` gates were explicitly granted and are
consumed. The blocked IE021 first attempt remains preserved. Under IE022,
human-revised A/B files were locked as `revised_v2`; a shared sentence-boundary
defect that treated semicolons as sentence terminators was diagnosed and covered
by a regression test. Final revalidation has zero structural errors and 20/20
valid pairs. Exact-directed file concordance is TP=24, FP=47, FN=20, precision
`0.338028`, recall `0.545455`, F1 `0.417391`; `PART_OF` F1 is only `0.246154`.
The user attested that both files are human-produced, but this post-feedback
result is not frozen-test formal IAA and does not establish high relation
agreement. F2 is disclosed and complete under its pre-specified structural
criterion. F3 configuration/resource preparation is complete and hash-audited.
F4a DDEV1/DDEV2 are also complete with limitations: exact RE remains very weak,
D has a `6%` relation parse-failure rate, E-prime is locally positive, and E is
negative. F4b CDEV1/CDEV2 is now complete under the consumed
`FULL_IE_CLUENER_TUNE_SANITY_APPROVED` gate. A-D tune NER F1 is
`0.524444/0.563107/0.571429/0.638889`; all parse/type checks pass. E-prime is
negative and E is only slightly positive on F1, while both deletion audits miss
the `70%` positive-claim threshold. F5 is now complete under the consumed
`FULL_IE_F5_PROTOCOL_FREEZE_APPROVED` gate: all 60 config IDs, 13 resources, 34
source files, 12 P5 Stage N reuse locks, metrics, prompts, seeds, and output
paths are frozen with model calls disabled. The later
`FULL_IE_F6_REPLAY_PREP_APPROVED` gate was granted and consumed at a declared
resource stop: the 170-row domain replay passed consensus/leakage validation,
but the first CLUENER attempt stopped at `0/1343` because the no-card cgroup
limit was 2 GiB versus a 4.54 GB frozen dual-model weight lower bound. That
blocked attempt remains preserved. The human subsequently granted
`FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED` and booted an RTX 4090 at
`2.8 CNY/hour` solely to unlock 120 GiB container memory. The recovery retained
CPU FP32 retrieval with CUDA masked, resumed from a verified `479/1343`
checkpoint, and completed/validated all `1343` CLUENER rows. F6 replay
preparation is now `DONE`; it completes no final model cell.

The human subsequently granted and consumed the exact
`FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` gate for F7 Domain Batch 1. Its scope was
only `domain:A/B/C/D:k5:s42`, reusing four locked 170-row P5 Stage N files and
adding Stage R only. All four outputs independently reload, recompute, and pass
hash/audit checks, so F7 is `DONE` and matrix accounting is now `4/60`. Exact
RE F1 is `0.040541/0.056972/0.057971/0.045381` for A/B/C/D; all four have zero
`HAS_METRIC` TP, and D is below C, so the batch does not support a positive RE
or RAG-for-RE claim. The locked execution manifest remains unchanged at SHA256
`893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1`.
The v1 batch-finalization failure is preserved and a versioned v2 no-model
repair completed with the full remote suite at `200/200`. vLLM was stopped;
the instance is back in no-card mode with no model/F7 process. F8-F9, paper,
and GitHub gates remain closed.

The later `FULL_IE_STOP_AND_NER_FALLBACK_RTC_APPROVED` gate is now also
consumed. Its independent result-to-claim verdict is `partial` with high
confidence. It freezes the supported paper line to the three-seed narrow NER
evidence, records F7 as reproducibility/audit evidence plus weak/negative RE,
and closed the remaining matrix route at that point. IE051 is preserved below
as a historical proposal but is now `CLOSED`: it was never executed and is not
a failed or blocked experiment. The human subsequently granted the focused
public-NER amendment recorded above. E/E-prime, K scans, RE, domain reruns, the
other 44 incomplete cells, full F8/F9 aggregation, paper work, submission, and
GitHub sync remain closed. Public transfer remains unsupported until NPUB01
completes and a separate post-run result-to-claim gate passes.

## Protocol and Implementation

| Run ID | Milestone | Purpose | Scope | Cells | Priority | Status | Gate / notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| IE000 | F0 | Confirm two-stage IE design | Plan only | 0 | MUST | DONE | Full-IE target and literal inventory confirmed |
| IE010 | F1 | Implement Stage R relation-only runner | Synthetic fixtures and legacy metadata only | 0 | MUST | DONE | Fixed prompt order, replay contract, deterministic skips, and future model gate |
| IE011 | F1 | Implement exact directed triple metrics | Synthetic fixtures | 0 | MUST | DONE | End-to-end exact key, type/FDR/coverage/conditional/zero-relation diagnostics |
| IE012 | F1 | Extend E/E-prime to relation atoms | Synthetic fixtures | 0 | MUST | DONE | Invalid output keeps atoms; entity drops cascade; legacy NER behavior preserved |
| IE013 | F1 | Implement aggregation and 60-cell manifest validation | Synthetic fixtures | 0 | MUST | DONE | Literal 30+30 inventory, hashes/statuses/arithmetic, three-seed mean/sample-SD |
| IE020 | F2 | Prepare non-test relation-calibration sheets | Existing fresh 20-text calibration set | 0 | MUST | DONE | A/B own locked entities only; 20+20 blank relation rows isolated and hash-audited |
| IE021 | F2 | Validate relation calibration | Exact directed endpoint/type triples | 0 | MUST | BLOCKED | 90 structural errors; 7/20 valid pairs; partial F1 0.454545 is not reportable; provenance unverified |
| IE022 | F2 | Revalidate human-revised relation calibration | Versioned `revised_v2` exact directed triples | 0 | MUST | DONE | 0 structural errors; 20/20 pairs; F1 0.417391; PART_OF F1 0.246154; not formal IAA |
| IE030 | F3 | Freeze domain dev configs | A-E-prime, K=5, seed42 | 6 | DONE | 16 runner configs + 12-cell matrix; all unauthorized and hash-locked |
| IE031 | F3 | Build CLUENER support bank and glossary | train_pool only | 0 | DONE | 30-record all-type bank; 61 support-only glossary entries |
| IE032 | F3 | Build/dedup CLUENER RAG corpus | labels-stripped train_pool | 0 | DONE | 9,584 rows; 89 removed by fixed 8-gram/0.80 blocklist |
| IE033 | F3 | Freeze CLUENER tune configs | A-E-prime, K=5, seed42 | 6 | DONE | 50-record all-type tune subset; no prompt artifacts |
| IE040 | F6 | Initial leakage-safe RAG replay preparation | Domain three-seed consensus plus no-card CLUENER dev text retrieval | 0 | MUST | BLOCKED | Preserved resource stop: domain 170/170 passes; CLUENER 0/1343 because 2 GiB was below the 4.54 GB weight lower bound |
| IE041 | F6 | Recover frozen CLUENER RAG replay | CPU FP32 retrieval on the 1,343-row labeled official dev split; paid card for memory only | 0 | MUST | DONE | Resumed from verified 479-row checkpoint; final 1343 rows/4029 passages; zero self-hit, prohibited fields, or >=0.80 containment hits |
| IE050 | F7 | Prepare and execute Domain Final Batch 1 | A/B/C/D, K=5, seed42; Stage R only over four locked P5 Stage N files | 4 | MUST | DONE | 680/680 rows complete; exact RE F1 0.040541/0.056972/0.057971/0.045381; 10/680 parse failures; backup verified; matrix 4/60 |
| IE051 | F7 | Historical proposal: replicate Domain A-D K=5 Stage R | A/B/C/D, K=5, seeds43/44; Stage R only over eight locked P5 Stage N files | 8 | HISTORICAL | CLOSED | Not executed; closed by the human NER-fallback route decision, not failed or blocked |
| RTC01 | Route freeze | Result-to-claim after F7 | Existing NER, F4a/F4b, F7, annotation, and 4/60 evidence only | 0 | MUST | DONE | `partial`, high confidence; NER primary, RE exploratory negative/limitation; no paper body edited |
| NPUB01 | Focused public NER | Execute complete CLUENER A-D K=5 final block | Labeled official dev 1,343; A/B/C/D; seeds42/43/44; NER only | 12 | MUST | AUTHORIZED | `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`; awaiting human 4090 boot and live price; no cell started |

### F3 Closeout (2026-07-31)

- Gate: `FULL_IE_F3_CONFIG_PREP_APPROVED`; AutoDL remained no-card (`No devices
  found`, `/dev/nvidia0` absent), with no vLLM/Qwen/extraction/verifier process.
- Resource package: support bank `30`, tune subset `50`, support-only glossary
  `61`, labels-stripped CLUENER RAG `9,584`; fixed 8-gram containment threshold
  `0.80` removed `89` rows (`30` exact support IDs, `34` tune overlaps, `24`
  CLUENER-dev text overlaps, `1` support overlap).
- Config package: `16` executable future runner YAMLs plus one `12`-cell run
  matrix (domain and CLUENER A/B/C/D/E/E-prime, K=5, seed42). Every config has
  `authorized=false` and `model_calls_allowed=false`; no final-evaluation path
  appears in the YAMLs and no prompt/per-query file was generated.
- The CLUENER official dev file was used only as a text-only deduplication
  blocklist; no labels, metrics, prompts, or tuning decisions were derived from
  it. `domain_test` was not read.
- Verification: F3 synthetic tests `5/5`, affected runner tests `9/9`, full
  AutoDL test suite `173/173`, independent F3 manifest validation `74` files.
- Report and manifest are under
  `backups/FULL_IE/f3_config_prep_20260731/`; report SHA256 is recorded in
  `docs/FULL_IE_CONFIG_PREP_20260731.md`.
- Cost: `0 CNY`. F3 creates no empirical result and does not change the `0/60`
  full-IE evidence count.

## Dev and Tune Gates

| Run ID | Milestone | Purpose | Dataset / split | Cells | Priority | Status | Gate / notes |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| DDEV1 | F4 | Relation-enabled A-D sanity | domain_dev50, K=5, seed42 | 4 | MUST | DONE | A-D exact RE F1 `0.056680/0.040404/0.039024/0.010989`; D parse failure `6%` |
| DDEV2 | F4 | Entity+relation verification sanity | domain_dev50 E/E-prime, K=5, seed42 | 2 | MUST | DONE | E-prime NER/RE F1 positive; E NER/RE F1 negative; full deletion audit retained |
| CDEV1 | F4 | Public NER A-D sanity | fixed CLUENER tune subset, K=5, seed42 | 4 | MUST | DONE | A-D F1 `0.524444/0.563107/0.571429/0.638889`; zero parse failures/unsupported types |
| CDEV2 | F4 | Public verifier E/E-prime sanity | fixed CLUENER tune subset, K=5, seed42 | 2 | MUST | DONE | E-prime F1 `0.571429 -> 0.546512`; E `0.638889 -> 0.644444`; both drop-audit gates fail |
| FREEZE | F5 | Lock final protocol | Prompts/configs/resources/metrics/seeds | 0 | MUST | DONE | 60 IDs frozen; 12 Stage N reuse locks; all execution unauthorized |

### F4a Closeout (2026-08-01)

- Gate: `FULL_IE_DOMAIN_DEV_SANITY_APPROVED`; bounded to `domain_dev50`, K=5,
  seed42 DDEV1/DDEV2, and now consumed.
- Preserved v0 failure: strict A Stage R rejected `38/50` relation responses.
  The sole allowed dev revision changed only `drop_invalid_relations` to `true`;
  prompt, schema, model outputs, exact direction, and duplicate policy did not
  change. No second revision is allowed.
- DDEV1 NER F1 A/B/C/D: `0.527273/0.506135/0.523169/0.501548`. Exact RE F1:
  `0.056680/0.040404/0.039024/0.010989`. Aggregate RE parse failures are
  `7/200 = 3.5%`, but D is `3/50 = 6%` and fails the per-config `<5%` gate.
- The relation sanitizer removed `577` invalid atoms. No A-D configuration has
  a `HAS_METRIC` true positive. D is below C on both NER and RE F1, while its
  RAG path adds about `8.19 s/query` during Stage N.
- E-prime improves NER F1 `0.523169 -> 0.540816` and exact RE F1
  `0.039024 -> 0.051613`. Correct-drop rates are `65/81 = 80.25%` for entities
  and `50/50 = 100%` for unique relation drops; its local positive gate passes.
- E changes NER F1 `0.501548 -> 0.495479` and exact RE F1
  `0.010989 -> 0.000000`. Its drop audits pass (`68/93 = 73.12%` entities,
  `26/27 = 96.30%` relations), but the F1 gate fails; this is a mixed/negative
  result.
- Validation: targeted tests `5/5`, full AutoDL suite `178/178`; 1,403 backup
  files verified. Summary SHA256 is
  `c5e9df2c6a0c8d083670c64e604b2b881b23c33f3ac183a7d365433628d1309d`.
- Safety: `domain_test` was not read; CLUENER was not run; no paper or GitHub
  action occurred. Final mode was no-card with no vLLM/model/runner process.
- Cost: observable vLLM windows are about `46m23s`, approximately `2.1 CNY` at
  `2.7 CNY/hour`, but this is not the platform bill. The longer paid-mode
  envelope means actual cost may be higher; AutoDL billing is authoritative.
- These six dev sanity rows are not final reported cells. Matrix accounting
  remains `0/60`. Full report:
  `docs/FULL_IE_DOMAIN_DEV_SANITY_20260801.md`.
- F4b CDEV1/CDEV2 subsequently completed under its separate bounded gate. No
  later phase is currently authorized.

### Historical F4b Authorization Checkpoint (2026-08-01)

- Human gate: `FULL_IE_CLUENER_TUNE_SANITY_APPROVED` was explicitly granted for
  CDEV1/CDEV2 only. It is not authority for any final-evaluation cell.
- Machine state at that checkpoint: `nvidia-smi -L` returned
  `No devices found`, `/dev/nvidia0` was absent, and no vLLM/Qwen/extraction/
  verifier process or screen session existed. No F4b model call or prompt was
  generated and new cost is `0 CNY`.
- Human-only prerequisite recorded at that checkpoint: boot the AutoDL RTX 4090
  24 GB and report the live hourly price. The agent must not rent, switch, stop,
  or release hardware.
- Planned agent action after GPU preflight: copy, never overwrite, the
  hash-locked F3 CLUENER configs into a versioned F4b execution directory;
  change only bounded
  execution authorization/output paths needed for this gate; run A/B/C/D then
  E/E-prime on the deterministic 50-record tune subset at K=5 seed42.
- Frozen resources:
  `/root/autodl-tmp/data/full_ie/f3_config_prep_20260731/` and
  `/root/project/configs/full_ie_f3_20260731/`. Query input is
  `cluener_tune_subset50_seed42.jsonl`, never official dev/test.
- Success checks: 50/50 rows reload, zero unsupported entity types, parse
  failure below `5%`, hashes/configs recorded, and E/E-prime deletion audit
  retained. Preserve negative results and do not tune from final data.
- Required closeout recorded at that checkpoint: stop vLLM, verify no model
  process, back up and hash-check outputs/cache/logs, mirror lightweight
  artifacts to `D:\yinsir`, report
  observed GPU time and platform-bill uncertainty, then ask the human to return
  to no-card mode.
- Forbidden: official CLUENER dev/test, `domain_test`, K=1/K=10, extra seeds,
  F5/F6, final matrix work, manuscript edits, and GitHub sync.

### F4b Closeout (2026-08-02)

- Gate: `FULL_IE_CLUENER_TUNE_SANITY_APPROVED`; bounded to CDEV1/CDEV2 on the
  deterministic 50-record `cluener_tune` subset at K=5 seed42, now consumed.
- Preflight: RTX 4090 with `24,564 MiB`, `0 MiB` initially used, and no
  conflicting vLLM/Qwen/runner/screen process. Human-reported price was
  `2.8 CNY/hour`.
- Versioning: copied the six hash-locked F3 CLUENER configs into
  `configs/full_ie_f4b_cluener_tune_20260802/`; F3 files remain unchanged.
  Query/support/glossary/RAG hashes are `7264b03d...d8ade5`,
  `abd6a338...9a5219`, `0ac4dc41...3ba3a9b`, and
  `f0b0cef6...ac2eb7ee`.
- CDEV1 exact entity P/R/F1 and FP: A
  `0.495798/0.556604/0.524444`, FP `60`; B
  `0.580000/0.547170/0.563107`, FP `42`; C
  `0.576923/0.566038/0.571429`, FP `44`; D
  `0.627273/0.650943/0.638889`, FP `41`. All four have zero parse failures and
  zero unsupported entity types.
- Clean comparisons: C/D replay B's exact per-query demonstrations; D has
  top-3 RAG evidence on all 50 rows and zero query self-hits. D is strongest on
  this tune subset but averages `7.609 s/query`, including `6.669 s/query` for
  CPU RAG selection.
- CDEV2: E-prime over C changes F1 `0.571429 -> 0.546512`, deleting 38 entities
  with `25/38 = 65.79%` correct drops. E over D changes F1
  `0.638889 -> 0.644444`, deleting 36 with `25/36 = 69.44%` correct drops.
  Both miss the `70%` positive-claim threshold; neither supports a positive
  verification/CoVe claim. All 74 deletion rows are retained.
- Provenance audit: 219 extraction requests and 214 verifier requests map
  exactly to 433 cache files with complete prompt, content, raw response, and
  hashes; no cache file is missing or orphaned. Focused tests passed `5/5`; the
  Git-tracked regression suite plus F4b tests passed `177/177` on AutoDL.
- Backup: remote/local `489/489` manifest entries pass. Summary SHA256 is
  `80997aef4e53d5494f5902932ef477d7cbdfb36b59ba13d7959568074bd5c8f1`;
  manifest SHA256 is
  `6d9f03466a7a46b41d2925e834d627d52481690ddf06548ddc129a659849f7de`;
  archive SHA256 is
  `75622decfd91bd460e782da4d4694fa6bcba8187e22ec7e0a16cf62cf4d5dd4a`.
- Cost/machine: vLLM ran `10:14:16-11:13:03 CST`, `3,527 s`, approximately
  `2.74 CNY` at `2.8 CNY/hour`; platform billing is authoritative. vLLM was
  stopped, GPU memory released, and final closeout found no-card mode with no
  model/runner/screen process.
- Safety: official CLUENER dev/test, `domain_test`, K=1/K=10, seeds 43/44,
  F5/F6, final matrix, manuscript, and GitHub operations did not occur.
- Evidence: F4b is tune-only and creates no final cell. Matrix accounting stays
  `0/60`. At F4b closeout no next gate was open; F5 later received its own
  bounded approval and is recorded below. Full report:
  `docs/FULL_IE_CLUENER_TUNE_SANITY_20260802.md`.

### F5 Closeout (2026-08-02)

- Gate: `FULL_IE_F5_PROTOCOL_FREEZE_APPROVED`; bounded to no-card protocol,
  hash, manifest, and remote-test work, now consumed.
- Frozen inventory: 60 unique final config IDs, 120 unique final output paths,
  48 Stage N nodes (`12` reused, `36` planned), 24 domain Stage R nodes, and 24
  E/E-prime verification nodes. All remain unauthorized with model calls
  disabled.
- Reuse audit: all `2,040` P5 Stage N rows passed semantic checks against
  frozen `domain_test`, including legacy metadata mapping, exact gold/ID
  alignment, prompt/raw hashes, five demonstrations, B/C/D replay, and three D
  RAG passages per row. Historical P5 rows were not edited.
- Verification policy: original atomic valid-`no` deletion only; invalid output
  keeps atoms; type gating remains disabled. F4b E `69.44%` and E-prime
  `65.79%` deletion precision remain negative/mixed evidence, not a positive
  CoVe claim.
- Validation: focused F3/manifest/freeze tests `21/21`; corrected full tracked
  AutoDL suite `185/185`; independent file-lock validation and local/remote
  artifact checks passed. One earlier full-suite invocation from the wrong
  working directory produced a disclosed import error before the corrected
  clean run.
- Manifest SHA256 is
  `592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e`;
  canonical SHA256 is
  `e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae`.
- Backup: 12/12 files verified remotely and locally. Backup manifest SHA256 is
  `381dcbbac20ddfdb7eb1862583c7cf1650de5d72e144e48e49e15a3d85d0956b`;
  archive SHA256 is
  `b2a2afe2ab767b9c1f981ac0b1f74df483fbb4f43d6f22d7ec2a0e8922e29e93`.
- Safety/cost: AutoDL remained no-card with no vLLM/model/runner/screen process;
  model calls `0`, paid GPU cost `0 CNY`. F6, final evaluation, aggregation,
  paper edits, and GitHub sync did not occur.
- Evidence accounting remains `0/60`; the freeze validates future identities
  and reuse dependencies but completes no final cell. Full report:
  `docs/FULL_IE_F5_PROTOCOL_FREEZE_20260802.md`.

### F6 Initial Stop And Recovery Closeout (2026-08-02 to 2026-08-03)

- Initial gate: `FULL_IE_F6_REPLAY_PREP_APPROVED`; bounded to no-card replay
  preparation with zero Qwen/vLLM/API calls, consumed at a declared memory stop
  condition. The resulting `BLOCKED` IE040 row remains preserved.
- Domain: all three hash-locked P5 D K=5 seed42/43/44 sources agree exactly on
  170 rows and 510 passages. Source self-hits, prohibited serialized fields,
  and fixed 8-gram threshold hits are all zero; maximum containment is
  `0.529148` and mean containment is `0.003612`.
- Initial CLUENER result: `0/1343`. The first screen exited during model
  initialization with a zero-byte log and no replay row. A new preflight
  established `memory.max=2,147,483,648` versus a frozen embedding+reranker
  weight lower bound of `4,544,321,872` bytes and then refused before model
  loading. No fallback precision, retriever, prompt, prediction, or metric was
  used.
- Initial validation: final F6 tests `7/7`; full tracked AutoDL suite `192/192`;
  P0 model manifest `65/65`; source locks `12/12`; final partial backup manifest
  `24/24` remotely and locally. Its manifest SHA256 is
  `b5db900a87cb5791a8327825b5014da82b60a7b831ee0f903514f424468a4f66`;
  archive SHA256 is
  `0ad69881c15f423cf0d6dc620427ce73614bbf53209625acd395cf1a731bf28f`.
- Recovery gate: `FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED`; now consumed.
  The human booted an RTX 4090 at `2.8 CNY/hour` solely to unlock a
  `128,849,018,880`-byte cgroup. The guarded runner retained CPU FP32 retrieval
  and an empty `CUDA_VISIBLE_DEVICES`; GPU execution, FP16, Qwen/vLLM, API,
  final metrics, Stage N/R, aggregation, paper, and GitHub work stayed blocked.
- Resume integrity: the first corrected window reached `479/1343` before a
  user-requested pause. Its seven-file snapshot passed `7/7`; the resumed
  window accepted those rows and appended through `1343/1343` without
  overwriting or filtering the checkpoint.
- Final CLUENER audit: `1343` unique rows, `4029` selected passages, exactly
  three per row, zero source self-hits, zero prohibited fields, and zero fixed
  8-gram/`0.80` threshold hits. Maximum containment is `0.785714`; mean is
  `0.017302`. Independent recovery status is `VALID`.
- Tests/backups: AutoDL `unittest` passed `195/195`; `pytest -q tests` passed
  `195` tests plus `8` subtests. The remote/local recursive recovery manifest
  passes `38/38`; manifest SHA256 is
  `e098c138c201fdc1e0804183da5eb97e1d6e8208fb2abd5b20d27adcb18f2947`
  and archive SHA256 is
  `add0145f8597d4cc09e5988aefc4ef53fe5e7c1fe93e91c3022b88ab4204f2e4`.
- Cost/closeout: two observable runner windows total `4,514.721` seconds,
  approximately `3.511449 CNY` at `2.8 CNY/hour`; platform billing is
  authoritative. Final inspection found `0 MiB` GPU memory, no compute app,
  Qwen/vLLM/recovery runner, or active screen.
- Overall F6 status is now `DONE` for replay preparation. No final cell is
  complete and matrix accounting remained `0/60`. F7 later received its own
  bounded gate; F8-F9 and paper work remain unauthorized. Full initial and
  recovery reports:
  `docs/FULL_IE_F6_REPLAY_PREP_20260802.md` and
  `docs/FULL_IE_F6_CLUENER_REPLAY_RECOVERY_20260803.md`.

### F7 Domain Final Batch 1 Closeout (2026-08-04)

- Completed cells: `domain:A:k5:s42`, `domain:B:k5:s42`,
  `domain:C:k5:s42`, and `domain:D:k5:s42`.
- Scope remained Stage R only over four hash-locked P5 Stage N sources: `680`
  total rows. Stage N reruns and E/E-prime were excluded.
- Batch contract SHA256 remains
  `0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973`;
  execution manifest SHA256 remains
  `893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1`.
- NER F1 for A/B/C/D is
  `0.530990/0.554662/0.569302/0.565764`; NER FP is `634/573/584/529`.
- Exact RE F1 is `0.040541/0.056972/0.057971/0.045381`, with TP/FP/FN
  `15/298/412`, `19/221/408`, `20/243/407`, and `14/176/413`.
  `B-A` is weakly positive, `C-B` is effectively tied, and `D-C` is negative.
  Every row has zero `HAS_METRIC` TP.
- The 680-row audit records 647 model requests, 52 deterministic skips, 19
  retries, `10/680 = 1.470588%` relation parse failures, zero unsupported types
  or type-matrix violations, and 1,840 preserved invalid-unit sanitizer events.
- The first batch-finalization attempt failed after inference because a string
  path was passed to a Path-only SHA helper. Its log SHA256 is
  `4c9760f09324bbcac63e1b5cbb5477300d33db9bcd43125b7b5f187ac33ca4b6`.
  Locked v1 files/results remain unchanged. A versioned v2 repair made zero
  model calls; focused F7 tests passed `5/5` and the full suite passed `200/200`.
- The final batch report is `COMPLETE`, has SHA256
  `6862964e4fae61cff46f284fe3b42378a97cee637e44c173570b8851ee898934`,
  and changes literal accounting from `0/60` to `4/60`.
- The observable paid envelope was about 2,463 seconds, approximately
  `1.916 CNY` at `2.8 CNY/hour`; platform billing is authoritative. vLLM was
  stopped and the instance returned to no-card mode with a 2 GiB cgroup and no
  model/F7 process.
- The remote 713-file payload manifest verifies `713/713`. The local archive
  SHA256 is
  `0de4bc5b5cd4fe50015dcffe76c288961be05d234a4f16c7492c23916779159c`;
  all 17 mirrored lightweight result files also match the manifest.
- Full reports: `docs/FULL_IE_F7_DOMAIN_BATCH1_PREPARATION_20260803.md`,
  `docs/FULL_IE_F7_DOMAIN_BATCH1_EXECUTION_CHECKPOINT_20260803.md`, and
  `docs/FULL_IE_F7_DOMAIN_BATCH1_CLOSEOUT_20260804.md`.
- At F7 closeout this gate was consumed and there was no open authority for
  seeds 43/44, E/E-prime, K scans, CLUENER final evaluation, F8/F9,
  aggregation, paper work, or GitHub synchronization. The later NPUB01 route
  amendment is recorded below and does not alter this historical closeout.

### Historical IE051 Domain K=5 Replication Proposal (CLOSED, Not Executed)

- Proposed cells: A/B/C/D at K=5 for seeds43 and 44, eight final domain cells
  total.
- Historical suggested approval token:
  `FULL_IE_DOMAIN_K5_REPLICATION_BATCH_APPROVED`. It was never granted and the
  proposal is no longer an active next step.
- Reuse requirement: use the eight hash-locked P5 Stage N outputs. Do not rerun
  Stage N or alter F5/F7 source, prompt, metric, parser, or output contracts.
- Scientific purpose: combine IE051 with the four completed seed42 cells to
  compute A/B/C/D three-seed exact RE mean/sample-SD. This is the minimum useful
  checkpoint before deciding whether more full-IE spending is justified.
- Historical execution requirements and exclusions remain part of the decision
  trail, but they are not an active gate specification and authorize no prep,
  GPU, model call, output, aggregation, or synchronization.
- Final status is `CLOSED` under
  `FULL_IE_STOP_AND_NER_FALLBACK_RTC_APPROVED`. The eight Stage R cells were not
  attempted. Closing them is an intentional human route choice, not an
  experimental failure or negative result.
- The formerly listed alternative was selected: stop the matrix expansion and
  freeze the NER-centered paper route. Paper edits still require their own
  separate gate.

### Focused CLUENER Public-NER Authorization (2026-08-04)

- Gate: `NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED`; status
  `AUTHORIZED_AWAITING_HUMAN_GPU`; no model call or final cell has started.
- Exact scope: all 1,343 labeled official CLUENER dev rows; A/B/C/D only;
  K=5; seeds42/43/44; NER only; 12 canonical F5 inventory identities.
- Locked reuse: frozen F3/F5 support bank and support glossary, plus the
  completed F6 1,343-row/4,029-passage RAG replay. Online retrieval is closed.
- Human prerequisite: boot the AutoDL RTX 4090 24 GB and report the live price.
  The target paid window is 8 hours and the hard stop is 10 paid-GPU hours.
- Current evidence/accounting remains `4/60`. Successful verified closeout
  would make it `16/60`; the remaining 44 incomplete identities stay closed.
- Excluded: sampled public subsets, unlabeled test, E/E-prime, K scans,
  RE/Stage R, domain reruns, IE051, paper edits, result-to-claim, submission,
  and GitHub synchronization.
- Exact execution and closeout contract:
  `docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_GATE_20260804.md`.
- After closeout, stop for a separately approved
  `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` result-to-claim step.

## Domain Final Matrix: 30 Reported Cells

| Run ID | Milestone | System / variant | K | Seeds | Reported cells | Stage work | Status |
| --- | --- | --- | ---: | --- | ---: | --- | --- |
| DK5-A | F7 | A fixed-random | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | seed42 DONE; seeds43/44 CLOSED |
| DK5-B | F7 | B kNN | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | seed42 DONE; seeds43/44 CLOSED |
| DK5-C | F7 | C kNN + glossary | 5 | 42/43/44 | 3 | Reuse Stage N; add Stage R | seed42 DONE; seeds43/44 CLOSED |
| DK5-D | F7 | D C + RAG | 5 | 42/43/44 | 3 | Reuse Stage N/RAG evidence; add Stage R | seed42 DONE; seeds43/44 CLOSED |
| DK5-E | F7 | E D + verification | 5 | 42/43/44 | 3 | Verify combined D Stage N+R output | CLOSED (not run) |
| DK5-EP | F7 | E-prime C + verification | 5 | 42/43/44 | 3 | Verify combined C Stage N+R output | CLOSED (not run) |
| DK1-A | F7 | A fixed-random | 1 | 42/43/44 | 3 | New Stage N + Stage R | CLOSED (not run) |
| DK1-E | F7 | E D + verification | 1 | 42/43/44 | 3 | New D Stage N + Stage R + verifier | CLOSED (not run) |
| DK10-A | F7 | A fixed-random | 10 | 42/43/44 | 3 | New Stage N + Stage R | CLOSED (not run) |
| DK10-E | F7 | E D + verification | 10 | 42/43/44 | 3 | New D Stage N + Stage R + verifier | CLOSED (not run) |
| **Domain total** |  |  |  |  | **30** | All rows report NER and exact RE |  |

## CLUENER Final Matrix: 30 Reported Cells

All rows use the complete labeled official dev split. C/D/E/E-prime use the
frozen support-derived glossary and labels-stripped, deduplicated train-pool
RAG corpus. There is no RE metric.

| Run ID | Milestone | System / variant | K | Seeds | Reported cells | Status |
| --- | --- | --- | ---: | --- | ---: | --- |
| CK5-A | F8 | A fixed-random | 5 | 42/43/44 | 3 | AUTHORIZED (NPUB01; not started) |
| CK5-B | F8 | B kNN | 5 | 42/43/44 | 3 | AUTHORIZED (NPUB01; not started) |
| CK5-C | F8 | C kNN + support glossary | 5 | 42/43/44 | 3 | AUTHORIZED (NPUB01; not started) |
| CK5-D | F8 | D C + train-text RAG | 5 | 42/43/44 | 3 | AUTHORIZED (NPUB01; not started) |
| CK5-E | F8 | E D + verification | 5 | 42/43/44 | 3 | CLOSED (not run) |
| CK5-EP | F8 | E-prime C + verification | 5 | 42/43/44 | 3 | CLOSED (not run) |
| CK1-A | F8 | A fixed-random | 1 | 42/43/44 | 3 | CLOSED (not run) |
| CK1-E | F8 | E D + verification | 1 | 42/43/44 | 3 | CLOSED (not run) |
| CK10-A | F8 | A fixed-random | 10 | 42/43/44 | 3 | CLOSED (not run) |
| CK10-E | F8 | E D + verification | 10 | 42/43/44 | 3 | CLOSED (not run) |
| **CLUENER total** |  |  |  |  | **30** |  |

## Aggregation and Paper Gate

| Run ID | Milestone | Purpose | Scope | Priority | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| AGG1 | F9 | Validate all final cells | 60 reported cells | HISTORICAL | CLOSED | Matrix stopped at 4/60; not run and not failed |
| AGG2 | F9 | Aggregate mean/SD | Three seeds per cell | HISTORICAL | CLOSED | Missing cells remain explicit limitations |
| AGG3 | F9 | Paired uncertainty | Pre-specified contrasts, 10k bootstrap | HISTORICAL | CLOSED | No new full-matrix inference |
| AGG4 | F9 | Full-matrix result-to-claim decision | NER, RE, CoVe, K, public NER | HISTORICAL | CLOSED | Superseded by RTC01 on existing evidence |
| RTC02 | Post-NPUB01 | Focused public-NER result-to-claim | Verified 12-cell block plus prior frozen evidence | MUST | PLANNED | Await `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` after closeout |
| PAPER1 | Paper-only | Propagate verified evidence | Complete `docs/JISE_OVERLEAF_LATEX_20260729/` project after separate exact approval | MUST | PLANNED | `main.tex` is entry only; edit `frontmatter.tex`/`sections/*.tex` as evidence requires; no paper edit before RTC02 |

## Accounting Check

```text
Domain final cells   = 18 K=5 + 12 K-scan = 30
CLUENER final cells  = 18 K=5 + 12 K-scan = 30
Complete matrix      = 30 + 30 = 60
Complete full cells  = 4
Stage N-only cells   = 8
Wholly absent cells  = 48
Authorized not run   = 12 CLUENER A/B/C/D K=5 cells (NPUB01)
Still route-closed   = 44 incomplete cells
Incomplete cells     = 56 total at current evidence state
Completed F7 B1      = 4 Stage R cells, validated and counted
NPUB01 success state = 16 complete; 8 Stage N-only; 36 wholly absent
Route target         = NER-primary paper; RE exploratory negative/limitation
60-cell completion   = CLOSED except the 12 exact NPUB01 identities
```

## F1 Closeout

- AutoDL mode: GPU-free/no-card; `nvidia-smi -L` returned `No devices found`,
  `/dev/nvidia0` was absent, and no vLLM/Qwen/extraction/verifier process ran.
- Verification: 28 new full-IE synthetic tests and 38 focused legacy
  extraction/verification/schema tests passed (`66/66`).
- Safety audit: no `domain_test`, support/dev/test prompt artifact, model/API,
  vLLM, GPU, manuscript, frozen data, or GitHub synchronization was used.
- Sync audit: approved code/tests have identical local/remote SHA256 values;
  old NER core and regression-test SHA256 values remain unchanged.
- Cost: `0 CNY` paid GPU; platform paid resources were not used.
- Evidence accounting is unchanged: RE and relation-aware E/E-prime are
  implemented but not model-run or evaluated; complete full-IE cells remain
  `0/60` and the existing `12/60` are Stage N only.

## F2 Preparation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_PREP_APPROVED` was bounded to IE020 and
  is consumed. It did not authorize annotation or returned-file validation.
- Inputs: locked A/B fresh human entity CSV files and the coordinator map were
  verified against fixed SHA256 values; 20 texts aligned exactly.
- Outputs: A/B each have 20 independently ordered rows containing only their
  own locked entities, an index guide, and blank relation fields. Delivery
  directories exclude the other role and coordinator map.
- Verification: 6 preparation/audit synthetic tests and all 158 repository
  tests passed remotely; the real package audit passed with 40/40 relation rows
  blank and locked entity cells preserved.
- Backup: remote and local 10-file packages match SHA256; root manifest is
  `5d2c55c60e24a1cdec12335f567ab5457dd8ee24e1d111ed1692694a48a840a4`.
- Safety/cost: AutoDL was GPU-free; no `domain_test`, prompt, model/API, vLLM,
  paper, or GitHub action occurred. Paid GPU cost was `0 CNY`.
- Evidence accounting remains `0/60`; preparation is not relation evidence.
  The later annotation and validation gates do not change this accounting.

## F2 Validation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED` was bounded to
  returned-file validation and is consumed.
- Input integrity: A/B each contain 20 rows; all four read-only fields, row
  orders, entity hashes/counts, blind IDs, text hashes, and coordinator mapping
  are preserved.
- Stop condition: 90 hard errors comprise 70 cross-sentence relations, 18
  relation type/direction matrix violations, and 2 invalid `METRIC_SCOPE`
  uncertainty codes. IE021 is `BLOCKED`.
- Incomplete diagnostic: only 7 paired rows were structurally valid (TP=10,
  FP=15, FN=9, precision `0.400000`, recall `0.526316`, F1 `0.454545`). It is
  not a complete calibration score and must not enter paper evidence.
- Provenance: file validation cannot establish two independent humans or
  absence of AI/scripts. The newly untracked user file
  `p6_relation_annotate.py` was not read, executed, modified, or committed.
- Verification: 6/6 new synthetic tests and 164/164 repository tests passed on
  AutoDL no-card mode.
- Safety/cost: no `domain_test`, prompt, model/API, vLLM, GPU, paper, or GitHub
  action occurred; paid GPU cost was `0 CNY`.
- Evidence accounting remained `0/60` at IE021 closeout. That gate authorized
  no correction, reannotation, F3/F4, or paper action.

## F2 Revalidation Closeout

- Gate: `FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED` was bounded to
  version-locking and validating the human-revised non-test A/B files; it is
  consumed.
- Negative-result preservation: the IE021 input/report and the first revised
  revalidation output were retained. Nothing was deleted, overwritten, or
  filtered to manufacture a pass.
- Input lock: A revised SHA256 `579a1a36...a63fe3`; B revised SHA256
  `4acc4b05...24861f`; original blank sheets and coordinator map remained
  unchanged.
- Implementation diagnosis: the shared sentence helper incorrectly treated
  `；;` as sentence-final punctuation. This rejected four identical A/B
  relations inside one semicolon-delimited Chinese equipment list. The helper
  now uses true sentence-final punctuation/newlines; full-stop cross-sentence
  rejection remains covered.
- Final structure: zero hard errors and 20/20 complete valid pairs. A has 44
  relations, B has 71, 9/20 rows match exactly, and 11/20 contain disclosed
  disagreements.
- Exact-directed concordance: overall TP=24, FP=47, FN=20, P `0.338028`, R
  `0.545455`, F1 `0.417391`; `USES` F1 `0.650000`, `HAS_METRIC` F1 `0.600000`,
  and `PART_OF` F1 `0.246154`.
- Provenance/claim boundary: the user attested both files are human-produced.
  Because these are post-feedback revisions, the result remains file
  concordance rather than a new blind first-pass or frozen-test formal IAA.
  The low score weakens, rather than supports, a relation-quality claim.
- Verification: Stage R core tests `14/14`, relation-validator tests `7/7`, and
  the final AutoDL no-card repository suite `166/166` passed. Real
  `domain_test` was not read; similarly named test paths were temporary
  synthetic fixtures only.
- Successful artifact report SHA256 is
  `9fc15cf720f470b5f37366eb70fb1657eb42d52527e7859ebf44ee52ebb6bef8`;
  see `docs/FULL_IE_RELATION_CALIBRATION_REVALIDATION_20260731.md`.
- Safety/cost: no prompt, model/API, vLLM, GPU, paper, P6 user-script, or
  GitHub action occurred; paid GPU cost was `0 CNY`.
- Evidence accounting remained `0/60` at IE022 closeout. F3, F4a, F4b, and F5
  later received their own bounded approvals and are recorded as complete
  above. All final-evaluation and later-phase gates remain closed.
