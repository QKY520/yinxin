# HANDOFF.md - New Conversation Handoff

Date: 2026-08-03
Workspace: `D:\yinsir`

This file is the latest operational state for a new Codex/agent session with no
chat history. Read these files before doing any project work:

1. `AGENT_PLAYBOOK.md` - authoritative machine execution contract.
2. `实验实施指导文档_综合版.md` - human-facing rationale and operational guide.
3. `AGENTS.md` - durable repository, safety, and collaboration rules.
4. This `HANDOFF.md` - live status and next step.
5. `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_PLAN_20260730.md` - approved
   full-IE route, phase design, and gate boundaries.
6. `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_TRACKER_20260730.md` - live
   cell inventory, gate state, and completion accounting.

If older docs conflict with this file on status chronology, this file is newer.
Hard rules in `AGENTS.md` and `AGENT_PLAYBOOK.md` still apply.

Operational status note (2026-08-03): this file and
`refine-logs/FULL_IE_MINIMUM_EXPERIMENT_TRACKER_20260730.md` carry the latest
chronology through completed F6 replay recovery and the prepared F7 Domain
Batch 1 proposal. `AGENT_PLAYBOOK.md`,
`AGENTS.md`, and `实验实施指导文档_综合版.md` still control their durable
execution, safety, and claim rules, but any dated current-gate snapshot in
those files predates this recovery closeout. The accepted `0.8000` calibration
decision, blocked IE021 attempt, completed IE022/F3/F4a/F4b/F5 work, negative
verification evidence, and `0/60` matrix accounting remain unchanged.

Latest route decision (2026-07-30): the human wants to expand the project into
the originally intended complete equipment-domain IE paper rather than submit
the current narrow NER manuscript as though it were full IE. The current
NER/JISE manuscript and submission package remain a valid fallback, but they
must not be updated with planned IE claims or invented results. A minimum
defensible two-stage extension plan and tracker now exist at
`refine-logs/FULL_IE_MINIMUM_EXPERIMENT_PLAN_20260730.md` and
`refine-logs/FULL_IE_MINIMUM_EXPERIMENT_TRACKER_20260730.md`. Planning is
complete. The bounded `FULL_IE_IMPLEMENTATION_APPROVED` gate was subsequently
granted and consumed using synthetic fixtures on AutoDL no-card mode. It added
implementation and tests only: no model/API call, vLLM startup, GPU use,
`domain_test` access, real-data prompt generation, or manuscript propagation
occurred, and that gate authorized no later phase. The separate bounded
`FULL_IE_RELATION_CALIBRATION_PREP_APPROVED` gate was then granted and consumed.
The later annotation and validation gates were also opened. The returned A/B
files preserved the locked columns, but IE021 validation found 90 structural
errors and remains a preserved `BLOCKED` first attempt. The user then attested
that both files were human-produced and supplied human-revised returns under
`FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED`. IE022 final revalidation
passed with zero structural errors and 20/20 valid pairs after correcting a
shared implementation defect that treated semicolons as sentence terminators.
The complete exact-directed file-concordance F1 is only `0.417391`, so this
completes/discloses F2 but does not support a high-quality relation-label claim.
The separately approved `FULL_IE_F3_CONFIG_PREP_APPROVED` gate is now also
consumed: no-card resources, hashes, and future F4 configs are prepared, with
no model calls or prompt artifacts. The later bounded
`FULL_IE_DOMAIN_DEV_SANITY_APPROVED` gate is also consumed. DDEV1/DDEV2 ran on
`domain_dev50` only and closed with limitations: all A-D exact RE F1 values are
below `0.057`, E-prime has a local positive NER/RE dev signal, E is negative,
and D's relation parse-failure rate is `6%`. On 2026-08-01 the human then
explicitly granted `FULL_IE_CLUENER_TUNE_SANITY_APPROVED` for F4b CDEV1/CDEV2
only. On 2026-08-02 the human booted an RTX 4090 24 GB and reported
`2.8 CNY/hour`. F4b then completed exactly the authorized 50-record K=5 seed42
scope, preserved all prompt/cache/raw/per-query artifacts, passed CDEV1
structural checks, and exposed negative/mixed verifier evidence. The user then
explicitly granted `FULL_IE_F5_PROTOCOL_FREEZE_APPROVED`. F5 completed in
no-card mode: the 60 final config IDs, resources, source files, metrics, seeds,
reuse dependencies, and output paths are hash-locked with all model calls and
execution disabled. The later bounded `FULL_IE_F6_REPLAY_PREP_APPROVED` gate
was also granted and consumed. Its domain replay completed for all 170 queries,
but the initial CLUENER attempt stopped at `0/1343`: the no-card cgroup was
limited to 2 GiB, below the frozen dual-model weight lower bound of
4,544,321,872 bytes. That blocked result remains preserved. The human then
granted `FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED`, booted an RTX 4090 at
`2.8 CNY/hour`, and approved CPU FP32 retrieval with the card used only to
unlock 120 GiB container memory. The recovery resumed from a verified
`479/1343` checkpoint and completed/validated all `1343` CLUENER rows with zero
GPU model execution. F6 replay preparation is now complete. On 2026-08-03,
F7 Domain Batch 1 was prepared locally as a four-cell Stage R-only proposal:
`domain:A/B/C/D:k5:s42`. Its contract SHA256 is
`0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973`.
All authorization/model/GPU/final-evaluation flags remain false, and the
required `FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` gate has not been granted. At
`2026-08-03T15:41:24+08:00`, SSH returned `Connection refused`; the instance
was unreachable and this preparation incurred `0 CNY`. No final-evaluation,
F7 execution, F8/F9, paper, or GitHub gate is open.

## 0. Executive Snapshot For A New Session

**Task**: extend the existing low-label Chinese equipment-domain NER project
into the minimum defensible full IE paper: domain NER+RE, E/E-prime and CoVe,
K=1/5/10 sensitivity, a gold-bearing CLUENER NER protocol, the literal 60-cell
matrix, paired aggregation, and result-to-claim. The completed narrow JISE NER
package is a fallback, not the target claim.

**Completed**: P0/P1/P2 and the frozen 30/50/170 domain split; P3/P4 dev sanity;
12 frozen P5 domain-test NER Stage N cells (A/B/C/D, K=5, seeds 42/43/44); fresh
two-human non-test entity calibration F1 `0.8000`; narrow Chinese/English/JISE
paper packages; M1 paired audit; M2 G/Z dev baselines; and a design-only
two-stage full-IE plan plus tracker. The bounded F1 implementation gate is also
complete: Stage R foundations, exact directed relation metrics, relation-aware
E/E-prime logic, manifest validation, and synthetic tests are implemented.
IE020 preparation is complete. IE021 validation infrastructure and tests are
also complete; its failed first return is preserved. IE022 versioned
revalidation is complete: the human-revised A/B files pass structural checks
on all 20 paired non-test texts, and all disagreements and the low complete F1
`0.417391` are disclosed. F3 configuration/resource preparation is complete:
16 future runner configs, a 12-cell dev/tune matrix, a 30-record support bank,
a 50-record tune subset, and a 9,584-row labels-stripped CLUENER RAG corpus
were hash-verified on AutoDL no-card mode. F4a domain-dev sanity is complete:
A-D Stage R and E/E-prime relation-aware verification ran at K=5 seed42, were
independently recomputed from per-query rows, and were backed up and hash-
verified before the instance returned to no-card mode. F4b CLUENER tune sanity
is also complete: A/B/C/D and entity-only E/E-prime ran on the deterministic
50-record tune subset at K=5 seed42, were independently audited, and were
backed up locally/remotely with all 489 manifest entries verified. F5 protocol
freeze is complete: one immutable 60-cell inventory now locks 60 unique config
IDs, 120 output paths, 13 resources, 34 source files, 12 reusable P5 Stage N
artifacts, the original deletion-only verifier, and all future gate boundaries.
It ran zero model calls and completes no final cell. F6 replay preparation then
completed the domain three-seed consensus dependency (`170` rows and `510`
passages) with zero self-hits, prohibited fields, or fixed-threshold overlaps.
The initial no-card CLUENER attempt stopped at `0/1343` on the 2 GiB cgroup and
remains preserved as a blocked row. The separately approved CPU-FP32 recovery
used a paid 4090 only to unlock 120 GiB container memory, resumed from a
verified 479-row checkpoint, and completed all `1343` CLUENER rows and `4029`
passages. Independent validation found zero self-hit, prohibited field, or
fixed-threshold overlap. F6 ran zero model/API calls and completes no final
cell. F7 Domain Batch 1 is now only a hash-locked proposal for four Stage
R-only seed42 cells; it has not been authorized or executed.

**Current evidence**: A/B/C/D NER F1 is `0.534645`, `0.555169`, `0.568858`, and
`0.565764`. C/D are an F1 near-tie; D has higher precision and 55 fewer FP.
This does not support model RE, positive CoVe, public generalization, K
robustness, or full-matrix claims. Human entity calibration `0.8000` is not
frozen-test formal IAA; `TECH_SCHEME` F1 is only `0.153846`. The post-feedback
relation file-concordance F1 `0.417391` is also not formal IAA and specifically
exposes weak `PART_OF` agreement (`0.246154`). F4a adds dev-only diagnostics,
not final evidence: A/B/C/D exact RE F1 is `0.056680/0.040404/0.039024/0.010989`;
E-prime improves dev NER/RE F1, while E lowers both. F4b adds tune-only public
diagnostics: A/B/C/D NER F1 is
`0.524444/0.563107/0.571429/0.638889`; E-prime lowers F1
`0.571429 -> 0.546512`, while E raises it only
`0.638889 -> 0.644444`. Both CLUENER deletion audits miss the `70%` positive
verification threshold, so public generalization and positive CoVe remain
unsupported.

**Current breakpoint**: F1, F2, F3, F4a DDEV1/DDEV2, F4b CDEV1/CDEV2, F5
protocol freeze, and F6 replay preparation/recovery are complete. IE021 remains
the preserved failed first relation-calibration attempt, and the initial F6
no-card memory stop also remains preserved. F4a
preserves its strict v0 A Stage R failure (`38/50` relation parse failures) and
consumed the sole allowed dev revision by changing only
`drop_invalid_relations` to `true`. Final r1 has `7/200 = 3.5%` aggregate parse
failures, but D is `3/50 = 6%` and misses the strict per-config gate. E-prime is
locally positive on dev; E is mixed/negative. These are sanity rows, so the
matrix remains `0/60`: 12 domain cells still have reusable NER-only Stage N
outputs, 48 report cells are absent, and all 30 final domain cells still need
Stage R results. The consumed F5 and F6 gates create no final matrix cell and
grant no later-phase authority. F7 Domain Batch 1 is
`PREPARED_AWAITING_GATE`: four A/B/C/D K=5 seed42 Stage R cells are scoped, but
all execution flags remain false and they do not count. The latest SSH check
returned `Connection refused`; the preceding F6 closeout had verified `0 MiB`
and no model/runner process.

**Next step**: the human must explicitly grant
`FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` for only
`domain:A/B/C/D:k5:s42`, Stage R only, with the proposed `2.0` paid-hour /
`5.6 CNY` cap at the last reported `2.8 CNY/hour`. After the gate, the human
boots the RTX 4090 and reports the live price; the agent then performs frozen-
hash, output-collision, GPU-memory, and conflict-process preflight before any
model call. Official CLUENER final evaluation, other domain cells, Stage N
reruns, E/E-prime, F8/F9, aggregation, paper edits, and GitHub synchronization
remain unauthorized.

**Red lines**: never run project Python locally on Windows; never tune from
frozen test; preserve every negative row; never call E-prime failed; never
rewrite the `0.8000` provenance; do not modify/delete/execute/commit untracked
root-level P6 user scripts, including `p6_relation_annotate.py`; do not
clean/reset the dirty remote worktree; use only SSH
alias `autodl-paper`; and after every future paid phase stop vLLM, verify GPU
release, back up, sync lightweight artifacts, report cost, and remind the human
to switch off paid hardware.

### F3 Full-IE Config And Resource Preparation

Complete on 2026-07-31 under `FULL_IE_F3_CONFIG_PREP_APPROVED` in AutoDL
GPU-free/no-card mode. This is preparation, not an empirical experiment.

- Prepared `16` future runner configs and one literal `12`-cell F4 dev/tune
  matrix covering domain and CLUENER A/B/C/D/E/E-prime at K=5 seed42. Every
  config remains `authorized=false` and `model_calls_allowed=false`.
- Prepared one deterministic all-type CLUENER support bank (`30` records), one
  all-type tune subset (`50`), and a support-only exact glossary (`61` entries).
- Built a labels-stripped CLUENER train-pool RAG corpus with `9,584` records.
  Fixed 8-gram containment at threshold `0.80` removed `89`: 30 exact support
  IDs, 34 tune overlaps, 24 CLUENER-dev text overlaps, and 1 support overlap.
- CLUENER official dev was used only as a text-only deduplication blocklist; no
  prompt, metric, or tuning result was generated from it. `domain_test` was not
  read. No prompt/per-query artifact exists in the F3 package.
- Validation: F3 tests `5/5`, affected runner tests `9/9`, full suite `173/173`;
  independent manifest validation checked `74` files. Manifest SHA256:
  `6302052aca1602d73bb96b53b1d702bebabc548f0e9fa694a7d317b0f2e7aa44`.
- Remote resources/configs/backups are under
  `/root/autodl-tmp/data/full_ie/f3_config_prep_20260731/`,
  `/root/project/configs/full_ie_f3_20260731/`, and
  `/root/autodl-tmp/backup/full_ie/f3_config_prep_20260731/`. Lightweight
  configs and the backup package were mirrored locally under
  `configs/full_ie_f3_20260731/` and
  `backups/FULL_IE/f3_config_prep_20260731/`.
- No model/API/vLLM/GPU/paper/GitHub action occurred. Cost impact: `0 CNY`.
  Evidence accounting remains `0/60`.

### F4a Full-IE Domain Dev Sanity

Complete on 2026-08-01 under `FULL_IE_DOMAIN_DEV_SANITY_APPROVED`. This is a
dev-only empirical sanity, not a final matrix batch.

- DDEV1 A/B/C/D NER F1 is `0.527273/0.506135/0.523169/0.501548`; exact directed
  RE F1 is `0.056680/0.040404/0.039024/0.010989`.
- The strict v0 A attempt with `38/50` relation parse failures is preserved.
  The only allowed dev revision changed `drop_invalid_relations` from `false`
  to `true`, retaining prompt/schema/model output and exact metric rules.
- Final aggregate RE parse failures are `7/200 = 3.5%`; D alone is `6%`, so the
  every-config `<5%` gate did not pass. The sanitizer removed `577` invalid
  relation atoms, and every A-D configuration has zero `HAS_METRIC` TP.
- E-prime improves NER F1 `0.523169 -> 0.540816` and RE F1
  `0.039024 -> 0.051613`; its entity/relation correct-drop rates are
  `80.25%/100%`, so its local positive gate passes.
- E lowers NER F1 `0.501548 -> 0.495479` and RE F1
  `0.010989 -> 0.000000`. Its drop audit passes (`73.12%/96.30%`), but its F1
  gate fails, making it a mixed/negative dev result.
- D's RAG selection adds about `8.19 s/query` and D is below C on both NER and
  RE F1. F4a therefore supplies no positive D-over-C RAG relation signal.
- Independent summarization verifies hashes, 50-row alignment, Stage N entity
  preservation, exact metrics, verifier drops/cascades, and sanitizer events.
  Targeted tests passed `5/5`; the full AutoDL suite passed `178/178`.
- The 1,403-file remote/local backup manifest is fully verified. Summary SHA256:
  `c5e9df2c6a0c8d083670c64e604b2b881b23c33f3ac183a7d365433628d1309d`.
  Full report: `docs/FULL_IE_DOMAIN_DEV_SANITY_20260801.md`.
- No `domain_test` or CLUENER run, paper edit, or GitHub sync occurred. Final
  mode was no-card with no vLLM/model/runner process. Observable vLLM activity
  was about `46m23s` (`~2.1 CNY` at `2.7 CNY/hour`), but the paid-mode envelope
  was longer and the AutoDL platform bill is authoritative.
- Matrix accounting remains `0/60`.

### F4b CLUENER Tune Sanity Closeout

Complete on 2026-08-02 under the now-consumed
`FULL_IE_CLUENER_TUNE_SANITY_APPROVED` gate.

- Scope stayed exact: CDEV1 A/B/C/D NER and CDEV2 entity-only E-prime over C
  plus E over D, all on the deterministic 50-record `cluener_tune` subset at
  K=5 seed42.
- Preflight found an RTX 4090 with `24,564 MiB`, `0 MiB` used, and no
  conflicting vLLM/Qwen/runner/screen process. Human-reported price was
  `2.8 CNY/hour`.
- Six dated execution configs are under
  `configs/full_ie_f4b_cluener_tune_20260802/`. The historical F3 configs were
  not changed. Frozen query/support/glossary/RAG hashes all match their locks.
- CDEV1 P/R/F1 and FP: A `0.495798/0.556604/0.524444`, FP `60`; B
  `0.580000/0.547170/0.563107`, FP `42`; C
  `0.576923/0.566038/0.571429`, FP `44`; D
  `0.627273/0.650943/0.638889`, FP `41`. Parse failures and unsupported types
  are zero for all four rows.
- E-prime changes F1 `0.571429 -> 0.546512`; its correct-drop rate is
  `25/38 = 65.79%`. E changes F1 `0.638889 -> 0.644444`; its correct-drop rate
  is `25/36 = 69.44%`. Both miss the `70%` positive-claim threshold. All 74
  deletions and the negative/mixed outcomes are preserved.
- The audit maps 219 extraction and 214 verifier requests exactly to 433 cache
  files with complete prompts, raw content, full responses, and hashes. Focused
  tests passed `5/5`; the tracked regression set plus F4b tests passed
  `177/177` remotely.
- Remote/local backups verify all `489/489` manifest entries. Summary SHA256:
  `80997aef4e53d5494f5902932ef477d7cbdfb36b59ba13d7959568074bd5c8f1`;
  manifest SHA256:
  `6d9f03466a7a46b41d2925e834d627d52481690ddf06548ddc129a659849f7de`;
  archive SHA256:
  `75622decfd91bd460e782da4d4694fa6bcba8187e22ec7e0a16cf62cf4d5dd4a`.
- Observable vLLM time was `3,527 s` (`0.979722 h`), about `2.74 CNY` at
  `2.8 CNY/hour`; platform billing is authoritative. vLLM stopped, GPU memory
  returned to zero, and final closeout found AutoDL in no-card mode with no
  model/runner/screen process.
- Official CLUENER dev/test, `domain_test`, K=1/K=10, seeds 43/44, F5/F6,
  final-matrix, manuscript, and GitHub actions did not occur.
- Full report: `docs/FULL_IE_CLUENER_TUNE_SANITY_20260802.md`. F4b creates no
  final cell, so accounting remains `0/60`. At F4b closeout no later gate was
  open; F5 later received its own bounded approval and is recorded below.

### F5 Full-IE Protocol Freeze Closeout

Complete on 2026-08-02 under the now-consumed
`FULL_IE_F5_PROTOCOL_FREEZE_APPROVED` gate.

- F5 froze 60 unique final config IDs and 120 unique output paths: 30 domain
  NER+RE cells and 30 CLUENER NER cells.
- The dependency graph contains 48 Stage N nodes (`12` P5 reuse locks and `36`
  planned), 24 domain Stage R nodes, and 24 E/E-prime verifier nodes. Every node
  remains unauthorized with `model_calls_allowed=false`.
- All `2,040` reused P5 rows passed semantic validation against frozen
  `domain_test`: exact IDs/gold, prompt/raw hashes, five demonstrations,
  fixed-random A sets, B/C/D replay, and exactly three D RAG passages per row.
  A bounded legacy-name map validates historical metadata without changing old
  rows or canonical F5 cell IDs.
- The original deletion-only verifier is retained with type gating disabled.
  F4b E `69.44%` and E-prime `65.79%` remain negative/mixed evidence and do not
  support a positive CoVe claim.
- Focused F3/manifest/freeze tests passed `21/21`; the corrected full tracked
  AutoDL suite passed `185/185`. One earlier invocation from outside the
  workspace produced a disclosed import error before the clean rerun.
- Freeze manifest SHA256:
  `592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e`;
  canonical SHA256:
  `e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae`.
- Remote/local technical backups pass `12/12`. Manifest SHA256:
  `381dcbbac20ddfdb7eb1862583c7cf1650de5d72e144e48e49e15a3d85d0956b`;
  archive SHA256:
  `b2a2afe2ab767b9c1f981ac0b1f74df483fbb4f43d6f22d7ec2a0e8922e29e93`.
- AutoDL remained no-card with no vLLM/model/runner/screen process. Model calls
  and paid GPU cost are both zero. During F5, no F6, final evaluation,
  aggregation, paper, or GitHub operation occurred.
- Full report: `docs/FULL_IE_F5_PROTOCOL_FREEZE_20260802.md`. Matrix accounting
  remained `0/60`. At F5 closeout F6 required a separate bounded approval; that
  later gate and its partial outcome are recorded below.

### F6 Replay Preparation And Recovery Closeout

The initial 2026-08-02 `FULL_IE_F6_REPLAY_PREP_APPROVED` gate was consumed at
the preserved `PARTIAL_BLOCKED_MEMORY` stop. The separate 2026-08-03
`FULL_IE_F6_CLUENER_REPLAY_RECOVERY_APPROVED` gate is now also consumed, and F6
replay preparation is complete.

- The hash-locked P5 D K=5 seed42/43/44 sources agree exactly. Domain replay
  contains `170` ordered query rows and `510` selected passages, with zero seed
  disagreement, source self-hit, prohibited serialized field, or fixed
  8-gram/`0.80` threshold hit. Maximum containment is `0.529148`; mean is
  `0.003612`.
- Initial CLUENER replay was `0/1343`. The first screen exited during model
  initialization with a zero-byte log and no replay row. The preserved evidence
  does not establish a kernel OOM kill.
- A versioned hard preflight now checks the cgroup before loading either model.
  It records `memory.max=2,147,483,648` bytes against a frozen BGE-M3 plus
  reranker weight lower bound of `4,544,321,872` bytes, a deficit of
  `2,396,838,224` bytes.
- No FP16, approximate retrieval, lexical fallback, hardware switch, Qwen,
  vLLM, API, Stage N/R, metric, prompt, prediction, aggregation, or paper work
  occurred. Paid GPU cost is `0 CNY`.
- Final F6 tests passed `7/7`; the full tracked AutoDL suite passed `192/192`;
  the P0 model manifest passed `65/65`. The partial backup manifest passes
  `24/24` remotely and locally.
- Remote/local extracted backups are under
  `/root/autodl-tmp/backup/full_ie/f6_replay_prep_20260802/` and
  `backups/full_ie/f6_replay_prep_20260802/`. Manifest SHA256 is
  `b5db900a87cb5791a8327825b5014da82b60a7b831ee0f903514f424468a4f66`;
  archive SHA256 is
  `0ad69881c15f423cf0d6dc620427ce73614bbf53209625acd395cf1a731bf28f`.
- That initial closeout was no-card with no model/runner/screen process. Full
  initial report: `docs/FULL_IE_F6_REPLAY_PREP_20260802.md`.
- Recovery used an RTX 4090 at the human-reported `2.8 CNY/hour` only to unlock
  a `128,849,018,880`-byte cgroup. CPU FP32 retrieval remained locked and
  `CUDA_VISIBLE_DEVICES` remained empty; no Qwen/vLLM/API/model call occurred.
- The first corrected recovery window checkpointed `479/1343` rows before a
  user-requested pause. Its seven files passed `7/7` SHA256 verification. The
  resumed window accepted those rows and finished `1343/1343` without
  overwriting or filtering the checkpoint.
- Final CLUENER replay has `1343` unique IDs and `4029` selected passages,
  exactly three per row. Source self-hits, prohibited fields, and fixed
  8-gram/`0.80` threshold hits are all zero; maximum containment is `0.785714`
  and mean is `0.017302`. Independent validation status is `VALID`.
- Remote `unittest` passed `195/195`; after the user-authorized remote install
  of pytest 9.1.1, `pytest -q tests` passed `195` tests plus `8` subtests. The
  root pytest discovery failure caused by a historical `refine-logs` test
  snapshot is documented and did not modify that artifact.
- Remote/local recovery backup manifests pass `38/38`. Manifest SHA256 is
  `e098c138c201fdc1e0804183da5eb97e1d6e8208fb2abd5b20d27adcb18f2947`;
  archive SHA256 is
  `add0145f8597d4cc09e5988aefc4ef53fe5e7c1fe93e91c3022b88ab4204f2e4`.
- Two observable recovery runner windows total `4,514.721` seconds, about
  `3.511449 CNY` at `2.8 CNY/hour`; platform billing is authoritative. Final
  inspection found `0 MiB` GPU memory and no compute app, Qwen/vLLM/recovery
  runner, or active screen. The paid card remains on pending human shutdown.
- F6 is `DONE` for replay preparation but creates no final cell. Matrix
  accounting remains `0/60`; F7-F9 and paper work require new gates.
- Full recovery report:
  `docs/FULL_IE_F6_CLUENER_REPLAY_RECOVERY_20260803.md`.

### F7 Domain Final Batch 1 Preparation

Prepared locally on 2026-08-03; execution is not authorized.

- Exact scope: `domain:A:k5:s42`, `domain:B:k5:s42`,
  `domain:C:k5:s42`, and `domain:D:k5:s42`.
- Work: Stage R only over four hash-locked P5 Stage N sources, 170 rows each;
  no Stage N rerun and no E/E-prime verification.
- Contract:
  `configs/full_ie_f7_domain_batch1_20260803/batch_contract.json`; SHA256
  `0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973`.
- Frozen F5 manifest/canonical/inventory hashes and all four source/config
  hashes are embedded in the proposal. F5 files were not edited.
- Authorization remains false for final evaluation, model calls, GPU use, and
  execution-config generation. The exact required gate is
  `FULL_IE_DOMAIN_FINAL_BATCH_APPROVED`.
- F4a timing gives a linear runner estimate of `1651.5874 s` (`27.5 min`) for
  680 rows. Proposed hard stop is `2.0` paid hours or `5.6 CNY` at the last
  reported `2.8 CNY/hour`, whichever is first. Live price and cap must be
  confirmed before execution.
- Conditional accounting is `4/60` only after all four outputs pass row,
  hash, and metric recomputation. Current accounting remains `0/60`.
- SSH returned `Connection refused` at preparation time. No Python,
  `domain_test` prompt, vLLM/model/GPU, paper, or GitHub action occurred; cost
  impact is `0 CNY`.
- Full preparation report:
  `docs/FULL_IE_F7_DOMAIN_BATCH1_PREPARATION_20260803.md`.

Latest paper-preparation note (2026-07-28): after the approved GPU-free
target-journal screening and reference-authenticity audit, the human selected
Journal of Information Science and Engineering (JISE) as the intended primary
target and explicitly approved a bounded English Markdown conversion. A
JISE-oriented English working draft now exists at
docs/JISE_ENGLISH_MANUSCRIPT_DRAFT_V1_20260728.md. It retains the locked
A/B/C/D evidence, the fresh non-test calibration disclosure, and all claim
boundaries. JISE selection does not prove its current JCR quartile or fees;
author-side institution-level JCR and journal-policy confirmation remain
required before submission.

Latest submission-package note (2026-07-28): the human subsequently approved a
GPU-free JISE submission package. Eight UTF-8 Markdown staging files now exist
under `docs/JISE_SUBMISSION_PACKAGE_20260728/`: a JISE-oriented submission
manuscript, cover letter, submission metadata/author form, declarations and AI
disclosure, Associate Editor selection, pre-submission checklist, editorial-
office query draft, and package README. The package is not a PDF, DOCX, LaTeX
source, or submitted record. It deliberately leaves author identity, funding,
conflict, data/code availability, ethics, JCR, and fee fields unresolved for
human confirmation. JISE's official pages contain a page-limit ambiguity (a
12-page template/charge boundary versus a separate regular-manuscript limit of
25 pages); the package adopts no more than 12 formatted pages only as a
conservative cost target and requires written clarification before
formatting/submission.

Latest LaTeX/Overleaf note (2026-07-29): the human explicitly approved JISE
LaTeX conversion and Overleaf upload/compile guidance, while withholding actual
submission. A modular Overleaf project now exists under
`docs/JISE_OVERLEAF_LATEX_20260729/`, with an upload-ready archive at
`docs/JISE_OVERLEAF_LATEX_20260729.zip`. It uses the official `JISE.sty` and
`JISEbib.bst` downloaded from the JISE website, retains all author-only
placeholders, and preserves the locked evidence boundary. Static checks passed
for all 11 included section files, 17 cited/17 defined bibliography entries,
labels/references, five tables, required result literals, and archive layout.
No local PDF was compiled because Windows/WSL had no TeX installation, AutoDL
SSH was unavailable, and a temporary no-install Tectonic download timed out.
The human later imported the package into Overleaf and reported that Recompile
produced the English article with no apparent error indicator. The full log and
PDF visual audit have not been archived locally; the compile is not an actual
journal submission.

Latest experiment-refinement note (2026-07-29): the human opened and completed
a bounded M1 gate for read-only statistical aggregation on AutoDL in GPU-free
mode. Existing frozen-v1 test gold, A/B/C/D predictions, summaries, and logs
were read without changing any data, prediction, prompt, or config. A paired
10,000-replicate passage-cluster bootstrap found that B-A and C-B have positive
observed F1 deltas but 95% intervals crossing zero. D-C F1 remains near-tied
(`-0.003094`, CI `[-0.026037, 0.019494]`), while its FP delta is `-55.0`
with CI `[-98.667, -12.0]`. D-A precision and FP intervals also exclude zero.
Sanitizer association, seed agreement, stratified metrics, balanced C/D
transitions, and online-versus-replay runtime were audited. No model/API/vLLM
call, GPU, new experiment, or LaTeX edit occurred. The M1 gate is consumed;
further baseline, K-scan, holdout, model, or LaTeX work needs a new explicit
gate.

Latest M2 note (2026-07-30): after the no-card G/protocol-freeze step, the
human separately approved one bounded paid-card Qwen2.5-7B schema-only Z run
on `domain_dev50`. Z used K=0 with no support, glossary, RAG, verification,
dry-run, prompt/config tuning, or `domain_test` access. All 50 rows completed:
TP=137, FP=206, FN=170, precision `0.399417`, recall `0.446254`, F1
`0.421538`, FDR `0.600583`, and zero final parse failures. Thirteen initial
parse failures were repaired by the fixed retry ladder, producing 63 requests
with 63 HTTP 200 responses. The remote 74-file audit package was copied to
`refine-logs/m2_domain_dev_z_schema_only_20260729/`; local file count, byte
sizes, and SHA256 values all matched the manifest. vLLM was stopped, and the
2026-07-30 closeout found no GPU and no related process. The observed vLLM log
window was about 5 minutes 9 seconds, approximately 0.23 CNY at 2.7 CNY/hour;
platform billing is authoritative. No LaTeX or frozen artifact was changed.
B001 and B003 are complete; B002/B004 remain unauthorized.

## 1. What We Are Doing Now

We are transitioning from a submission-ready narrow NER fallback to a planned
SCI-Q4-oriented **full information extraction (NER+RE) extension**. The target
is the original 60-cell A/B/C/D/E/E-prime matrix across the domain set and a
gold-bearing CLUENER NER protocol, with K sensitivity and honest CoVe rows.
Current evidence is still NER-only, so the paper must retain its narrow claims
until the new experiments are complete and audited.

Completed preceding planning step (2026-07-30): **minimum defensible full-IE
extension design**. The proposed implementation is two-stage: Stage N preserves
the frozen NER extractor and reuses the 12 existing A/B/C/D K=5 three-seed NER
outputs by hash; Stage R receives the source text plus Stage N predicted
entities and predicts only directed `USES`, `HAS_METRIC`, and `PART_OF`
relations. Domain reporting uses end-to-end exact directed relation-triple
micro P/R/F1. E verifies D entity and relation atoms; E-prime verifies C atoms;
deleting an entity also deletes its incident relations. This plan is recorded
in the two `FULL_IE_MINIMUM_*_20260730.md` files. It is a plan, not execution
authority.

Completed latest step (2026-07-30): **bounded no-card F1 implementation**.
The approved implementation uses fixed relation-only prompt/resource contracts,
an approved directed relation matrix, exact end-to-end triple metrics,
relation-aware deletion-only verification, entity-to-relation cascade removal,
and literal 30-domain plus 30-CLUENER manifest validation. The approved files
are:

- `src/equipment_ie/full_ie.py`;
- `src/equipment_ie/full_ie_manifest.py`;
- `scripts/run_stage_r.py`;
- `scripts/run_full_ie_verification.py`;
- `scripts/validate_full_ie_manifest.py`;
- `tests/test_full_ie.py`;
- `tests/test_full_ie_manifest.py`; and
- `tests/test_full_ie_runners.py`.

On AutoDL no-card mode, 28 new synthetic full-IE tests and 38 focused legacy
extraction/verification/schema tests passed (`66/66`). Invalid triples,
direction errors, duplicates, invalid verifier output, entity-drop cascades,
runner gate enforcement, and legacy NER compatibility are covered. No frozen
data, real-data prompt, model/API/vLLM, GPU, or paper artifact was used. This is
implemented infrastructure, not RE, CoVe, public-generalization, or matrix
evidence. Paid-GPU cost was `0 CNY`.

Completed latest step (2026-07-30): **bounded no-card F2 relation-calibration
preparation (IE020)**. The gate used only the fixed fresh 20-text non-test human
entity submissions: A SHA256 `6906142d...5f8877`, B SHA256
`40428a8e...b732e`, and coordinator map SHA256 `6a902ab6...64e18`. Each
annotator's delivery has 20 rows in that annotator's existing blind order, only
that annotator's locked entity JSON plus an index guide, and three blank
relation fields. A/B delivery directories are physically isolated from each
other and from the coordinator-only map.

The preparation/audit suite passed `6/6`; the full remote repository suite
passed `158/158`. The real-package read-only audit passed with 20 aligned texts,
40/40 blank relation rows, different A/B orders, exact locked-entity-cell
preservation, isolated inventories, and zero forbidden filename hits. Remote
and local 10-file copies match SHA256. The root package manifest is
`5d2c55c60e24a1cdec12335f567ab5457dd8ee24e1d111ed1692694a48a840a4`;
see `docs/FULL_IE_RELATION_CALIBRATION_PREPARATION_20260730.md`. No annotation,
returned-file scoring, `domain_test`, prompt, model/API/vLLM, GPU, paper, or
GitHub action occurred. Cost was `0 CNY`; evidence remains `0/60` full-IE cells.

Completed latest step (2026-07-31): **bounded no-card IE021 relation-
calibration validation**. A/B returned files have SHA256
`444f4642...83726a` and `5489aa81...46066`; their four locked columns, row
orders, 20-text alignment, and entity hashes/counts are intact. Validation
found 90 hard errors: 70 cross-sentence relations, 18 relation type/direction
matrix violations, and 2 invalid `METRIC_SCOPE` codes. Only 7/20 paired rows
were structurally scoreable (TP=10, FP=15, FN=9, precision `0.400000`, recall
`0.526316`, F1 `0.454545`), so this partial diagnostic is not a valid complete
calibration result or paper evidence. IE021 is `BLOCKED`.

The validator cannot prove independent two-human provenance or absence of
AI/scripts. A newly untracked user file `p6_relation_annotate.py` appeared and
was not read, executed, modified, or committed. Six new synthetic tests and all
164 repository tests passed on AutoDL no-card mode. No `domain_test`, prompt,
model/API/vLLM, GPU, paper, or GitHub action occurred; cost was `0 CNY`. See
`docs/FULL_IE_RELATION_CALIBRATION_VALIDATION_20260731.md`.

Completed latest step (2026-07-31): **bounded no-card IE022 relation-
calibration revalidation**. The user attested that both A/B submissions were
produced by humans and supplied human-revised files, locked as `revised_v2` at
SHA256 `579a1a36...a63fe3` and `4acc4b05...24861f`. All four read-only columns,
row orders, 20-text alignment, entity hashes/counts, original blank sheets, and
coordinator map remained unchanged. Because the files were revised after
structural feedback, this is not a new blind first-pass or frozen-test formal
IAA.

The first revised revalidation reported eight cross-sentence errors, all on
`domain-candidate-0050`. A/B had identical relations and both treated a
semicolon-delimited equipment list as one sentence. Inspection found a shared
F1 implementation defect: `same_sentence()` treated `；;` as sentence-final
punctuation even though the locked guideline only excludes genuinely
cross-sentence relations. The core helper was corrected to retain semicolons as
intra-sentence punctuation; full stops, question/exclamation marks, and
newlines remain boundaries. A new Stage R regression test covers the case. The
failed intermediate output and the original IE021 failure are both preserved.

Final IE022 revalidation passed with zero structural errors and 20/20 valid
pairs. Exact-directed file concordance is TP=24, FP=47, FN=20, precision
`0.338028`, recall `0.545455`, F1 `0.417391`; 9/20 texts match exactly and 11
disagree. Per-type F1 is `USES=0.650000`, `HAS_METRIC=0.600000`, and
`PART_OF=0.246154`. A has 44 relations and B has 71. This satisfies the
pre-specified F2 structural/disclosure criterion but is low agreement and
weakens any relation-quality claim. It is not a model RE result.

Stage R core tests passed `14/14`, validator tests passed `7/7`, and the final
AutoDL repository suite passed `166/166`. AutoDL remained no-card with no model
process; no real `domain_test`, real prompt, model/API/vLLM, GPU, paper, P6
user-script, or GitHub action occurred. Cost was `0 CNY`. The successful report
SHA256 is `9fc15cf720f470b5f37366eb70fb1657eb42d52527e7859ebf44ee52ebb6bef8`;
see `docs/FULL_IE_RELATION_CALIBRATION_REVALIDATION_20260731.md`.

Completion accounting for a new session:

- the literal matrix contains 60 reported cells: 30 domain and 30 CLUENER;
- 12 cells currently have valid NER Stage N only, so 48 reported cells are
  absent and none of the 30 domain cells has a valid Stage R result;
- adding only domain K=5 E/E-prime would complete that narrow six-row NER block
  at 18/18, but the overall matrix would still be only 18/60, with 42 reported
  cells absent and domain RE still incomplete;
- domain gold contains 74 support, 133 dev, and 427 test relations;
- CLUENER official test has no offline gold; the planned final public
  evaluation is the complete labeled official dev split (1,343 rows), with a
  frozen train-derived support/glossary/RAG protocol.

Historical verifier evidence must be understood precisely. Before F4a, E v1
and E v2 ran only as NER verification sanity on `domain_dev50`, K=5, seed 42.
E v1 was a clear method failure: F1 fell from D's `0.5415` to `0.4264`, and
18/20 audited drops were wrong. E v2 repaired the catastrophic over-deletion
but remained a mixed/negative result: F1 `0.5367` versus D `0.5415`, with 7/13
wrong drops, 5/13 correct drops, and 1/13 unclear. At that historical point,
E-prime had been prepared but never executed with model calls, and E v3 was
prompt/dry-run preparation only. F4a later ran the distinct relation-aware
dev-first protocol: E-prime improved NER/RE F1 from `0.523169/0.039024` to
`0.540816/0.051613`, while E lowered them from `0.501548/0.010989` to
`0.495479/0.000000`. These are dev sanity results, not final matrix evidence;
they do not convert E v1/v2/v3 into successful runs or support a general CoVe
claim.

Completed latest step (2026-07-30): **M2 dev baseline audit and closeout**. G
is a very weak exact-glossary lower bound on `domain_dev50` (F1 `0.014706`,
233 FP, FDR `0.983122`). The separately gated schema-only Z run completed all
50 dev passages at F1 `0.421538`, with 206 FP, FDR `0.600583`, and zero final
parse failures. Z remained K=0 with no support, glossary, RAG, verification,
dry-run, tuning, or `domain_test`. The remote audit package is locally copied
and independently hash-verified. B001 and B003 are `DONE`; no frozen-test
baseline cell is complete or authorized.

Completed latest step (2026-07-29): **M1 paired evidence and integrity audit**.
All 12 existing A/B/C/D K=5 seed cells were recomputed from hash-verified
artifacts. Passage-level bootstrap uncertainty, per-type/source/length/density
diagnostics, balanced C/D transitions, proposal-sanitizer association, seed
agreement, and runtime were reported in
`docs/M1_PAIRED_EVIDENCE_AUDIT_20260729.md`. The strongest added evidence is
D-C FP `-55.0` with 95% CI `[-98.667, -12.0]`, plus D-A precision
`+0.041068` with CI `[0.006710, 0.075562]`. B-A and C-B F1 remain positive
observed trends whose intervals cross zero. M1 used AutoDL GPU-free Python
only, changed no frozen or run artifact, and did not edit LaTeX.

Completed latest step (2026-07-29): **GPU-free JISE LaTeX/Overleaf conversion**.
The evidence-locked English manuscript has been transferred into the official
JISE LaTeX structure, split into modular source files, connected to 17
source-checked BibTeX entries, and packaged for Overleaf upload. The source
still displays deliberate `[AUTHOR INPUT: ...]` blockers. The human imported
the package into Overleaf and reported a clean-looking Recompile, but the full
compile log and PDF visual audit are not archived locally. No actual submission
was performed.

Completed preceding step (2026-07-28): **GPU-free JISE Markdown submission-
package preparation**. The package contains the submission-text branch, cover
letter, author/system metadata, declarations and AI disclosure, editor choices,
pre-submission checklist, and an editorial-office query draft. It remains a
staging package with explicit author-only blockers.

Completed preceding step (2026-07-28): **GPU-free screening of three target
journals and reference-authenticity verification**. The verified candidates
are Journal of Information Science and Engineering, KSII Transactions on
Internet and Information Systems, and Computer Science and Information Systems.
Official pages support their SCIE/SCI status, scope, public JIF, fee, and format
facts recorded in `docs/TARGET_JOURNAL_AND_REFERENCE_AUDIT_20260728.md`.
Public pages do not establish the current JCR quartile, so no journal is yet
locked as Q4. The paper's former reference-candidate list was replaced with 17
numbered entries; peer-reviewed papers, preprints, and the DuIE data resource
are explicitly distinguished. No experiment, local Python, GPU, project model,
external API, or secondary agent was used.

Completed current step (2026-07-27): **GPU-free manuscript refinement and
pre-submission claim/evidence alignment in Markdown**. The approved pass audited
the title, abstract, contributions, dataset, method, experimental scope,
results, discussion, limitations, and conclusion of the current Chinese draft.
It incorporated the fresh two-human non-test calibration, restored the full
precision/recall/F1/FP values for all A/B/C/D rows, and made the unsupported
claim boundary explicit throughout the paper. The immediate quality-control
and first manuscript-refinement step is closed for the current paper route.

On 2026-07-27, after validation of the fresh two-human non-test calibration,
the human explicitly accepted the original project minimum `>=0.80`, accepted
the observed exact span+type micro-F1 of `0.8000` as passing, and instructed
the project to close the experiment/QA issue and proceed to paper refinement.

This decision must be recorded precisely:

- `P6-QA1R` is a **human-accepted pass under the original `>=0.80` policy** for
  entering manuscript refinement;
- the automatic validator still says `blocked` only because locked guideline
  v4 also introduced a more conservative target of `>=0.85`;
- the valid result is **fresh two-human non-test calibration agreement**, not
  frozen-test formal IAA;
- the `0.8000` overall score has no margin, and `TECH_SCHEME` remains a serious
  class-specific limitation (`F1=0.153846`).

The original scoped P5 phase remains closed, while the separate evidence-
strengthening track has now completed M1 plus the dev-only M2 G and Z baselines.
The original full experimental plan is still not complete. Only the bounded P5
`domain_test` A/B/C/D, K=5, seeds 42/43/44 block exists for model-backed test
evidence. Do not translate "ready to refine the paper" or the dev-only G/Z
results into "the full P5 matrix passed."

Current editable paper drafts:

- `docs/JISE_OVERLEAF_LATEX_20260729/` (official-template LaTeX/Overleaf
  project; the human reported a clean-looking first compile, while author
  placeholders and local compile-log/PDF proof remain pending);

- `docs/JISE_OVERLEAF_LATEX_20260729.zip` (upload-ready Overleaf archive);

- `docs/JISE_SUBMISSION_PACKAGE_20260728/` (current JISE Markdown staging
  package; use its file 01 as the submission-text branch after resolving all
  author placeholders);

- docs/JISE_ENGLISH_MANUSCRIPT_DRAFT_V1_20260728.md (JISE-oriented English
  Markdown working draft);

- `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`

The human selected JISE and completed the bounded English-Markdown and Markdown
submission-package gates. That package is now the narrow NER fallback while the
full-IE extension is pursued. Before any eventual submission, the author still needs
an institution-level JCR check for the exact journal title/ISSN, including JCR
year, category, rank, quartile, and the institution's quartile rule, plus the
author/declaration and journal-policy confirmations recorded in the package.
The approved LaTeX/template-conversion gate is now consumed. The current work
does not authorize DOCX conversion, actual journal submission, implementation,
or any new experiment. Do not edit the manuscript to describe full IE until
verified results exist. Overleaf compilation and visual proofing are permitted
within the prior gate, but uploading the resulting PDF to JISE is not.

All generated `.docx` files were deleted on 2026-07-25 at the user's request
because of rendering/encoding problems. Future writing defaults to UTF-8
Markdown unless the user explicitly asks otherwise.

No further Python/model-call/paid-experiment gate is currently open. F4b, F5,
and F6 replay preparation/recovery are complete and their bounded gates are
consumed. F7 Domain Batch 1 is only `PREPARED_AWAITING_GATE`; its four
authorization flags are false. The latest SSH check returned
`Connection refused`, so the instance is unreachable. Frozen-test prompt/model
generation, official CLUENER evaluation, returned-file correction,
reannotation, frozen-data correction, aggregation, baseline runs, K scan,
extra seeds, F7 execution, F8/F9, and other experiments remain unauthorized.
The fresh entity annotation/validation, M1, M2, full-IE F1, F2, F3, F4a, F4b,
F5, F6 initial replay, and F6 recovery gates are consumed.
LaTeX was deliberately not changed; any result propagation into a manuscript
requires a later, separate approval after result-to-claim.

## 2. What Is Already Completed

### P0 - Environment

Complete.

- AutoDL environment was set up.
- Project venv and required imports passed previously.
- Four fixed model directories were downloaded and structurally checked:
  Qwen2.5-7B-Instruct, Qwen2.5-14B-Instruct-AWQ, BGE-M3, and
  bge-reranker-v2-m3.
- P0 backup was created and hash-verified.
- The human confirmed the P0 image was saved.

### P1 - Public Data

Complete.

- CLUENER, Few-NERD SUP, DuIE 2.0, and CMNEE were downloaded and normalized.
- 12 official split JSONL files were generated.
- K=1/5/10 public support files were generated with seed 42.
- Loader/span checks passed.
- Important limitation: public CLUENER and DuIE test files have no gold labels.
  They must never be evaluated as all-negative gold.

### P2 - Self-Built Domain Data

Complete and frozen as version `v1` for the current experiment. Its quality
evidence now includes a valid fresh two-human calibration on 20 previously
unused non-test passages, but the frozen test itself was not independently
double-annotated and has no formal test IAA.

- 400 public equipment-domain candidates were collected:
  Baidu Baike 7, patent 84, CMNEE 309.
- Schema `p2-schema-draft-v1` and 10 synthetic examples were approved.
- QAonMilitaryKG distant supervision had low coverage:
  15/400 records, 23 EQUIPMENT suggestions, 0 relations.
- Qwen2.5-14B-AWQ proposal workflow, machine/rule-assisted review, nominal
  adjudication, and freeze were completed for the approved 250-record route.
- Final frozen split:
  - `domain_support.jsonl`: 30 rows;
  - `domain_dev.jsonl`: 50 rows;
  - `domain_test.jsonl`: 170 rows;
  - `domain_rag_corpus.jsonl`: 230 rows;
  - `data/FROZEN` and `logs/dedup.json` exist in the remote artifact set.
- Important hashes:
  - `domain_gold_250.jsonl`:
    `fb183c733d328124c35e527872eb9cb4ea839fdf7bea1059c2313e3ea207acdc`;
  - `domain_support.jsonl`:
    `9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a`;
  - `domain_dev.jsonl`:
    `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`;
  - `domain_test.jsonl`:
    `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`.
- Local P2 gold backup:
  `backups/P2/p2_domain_gold_freeze_20260722.tar.gz`;
  SHA256 `a3711e2af4179d8398d8d497827ff703b1cfa4a8b0c05ea4de47837b9329ec3f`.
- Quality caveat: the old `0.9909` agreement came from machine/rule-generated
  pseudo A/B files and is not valid human IAA. Within the 170-row test source
  map, 61 rows are tagged `adjudicated_double_annotation` and 109 are tagged
  `annotator_a_single_annotation`; those names describe the old build path and
  do not prove independent human annotation.

### P3/P4 - Domain-Dev Sanity

Complete enough for the current paper route.

All model-run cells below are `domain_dev50`, K=5, seed 42, Qwen2.5-7B via
vLLM.

| Config | Main change | Precision | Recall | F1 | TP/FP/FN | Verdict |
| --- | --- | ---: | ---: | ---: | --- | --- |
| A | fixed random, no glossary/RAG/verif | 0.4914 | 0.5570 | 0.5221 | 171/177/136 | accepted baseline |
| B | kNN examples | 0.4767 | 0.5342 | 0.5038 | 164/180/143 | negative |
| C | B replay + glossary | 0.4722 | 0.5537 | 0.5097 | 170/190/137 | mixed |
| D | C + RAG rerank top-3 | 0.5211 | 0.5635 | 0.5415 | 173/159/134 | positive |
| E v1 | D + verifier v1 | 0.6173 | 0.3257 | 0.4264 | 100/62/207 | overkill |
| E v2 | D + verifier v2 | 0.5266 | 0.5472 | 0.5367 | 168/151/139 | mixed |

Dev interpretation: D(RAG) was the strongest positive sanity result. Verifier
variants were negative or mixed and are not recommended for more paid GPU by
default.

### P5 - Bounded Domain-Test Evidence

Complete for a narrow paper claim, not complete as the original full P5 matrix.

Completed scope:

- Dataset: `domain_test`
- K: 5
- Seeds: 42, 43, 44
- Configs:
  - A: fixed random;
  - B: kNN examples;
  - C: kNN + glossary;
  - D: kNN + glossary + RAG.
- Not run/completed: E, E-prime, CLUENER, K=1, K=10, more seeds, full public
  benchmark matrix.

All 12 completed per-query/summary files under `results/p5/` were verified:
170 rows per cell, 0 parse failures, SHA256 matched during the prior audit.

Three-seed domain-test NER results:

| Config | F1 mean +/- std | FP mean +/- std | Main reading |
| --- | ---: | ---: | --- |
| A | `0.534645 +/- 0.004375` | `613.3 +/- 88.8` | baseline |
| B | `0.555169 +/- 0.000880` | `573.7 +/- 1.2` | kNN improves F1 and lowers FP |
| C | `0.568858 +/- 0.000769` | `584.0 +/- 0.0` | best F1/recall |
| D | `0.565764 +/- 0.000000` | `529.0 +/- 0.0` | best precision and lowest FP |

Clean deltas:

- `B - A`: +0.020524 F1 and about -39.7 FP.
- `C - B`: +0.013689 F1 and about +10.3 FP.
- `D - C`: -0.003094 F1, but about -55.0 FP.
- `D - A`: +0.031119 F1 and about -84.3 FP.

Accepted wording: **C and D are near-tied on F1; C is marginally ahead on
recall/F1, while D is clearly ahead on precision and false-positive reduction.
Do not write that C significantly or substantially beats D.**

P5 paid run note:

- The replication paid vLLM window was approximately
  2026-07-24 18:16:34-19:27:50 CST.
- Estimated cost was about 3.2 CNY at 2.7 CNY/hour.
- vLLM was stopped after the run and GPU memory was verified at 0 MiB.

### M1 - Paired Evidence and Integrity Audit

Complete under the human-approved 2026-07-29 read-only aggregation gate. The
analysis was run on AutoDL in GPU-free mode and read only the already frozen
test gold, predictions, summaries, and logs.

- All 12 A/B/C/D K=5 seed cells were reloaded and recomputed: 170 passages per
  cell and zero parse failures.
- Paired passage-cluster bootstrap: 10,000 replicates, analysis seed
  `20260729`, percentile 95% intervals, aligned across configs and seeds.
- B-A F1 `+0.020524`, CI `[-0.006771, 0.047215]`; C-B F1 `+0.013689`, CI
  `[-0.013210, 0.043711]`; D-C F1 `-0.003094`, CI
  `[-0.026037, 0.019494]`. All three F1 intervals include zero.
- D-C FP `-55.0`, CI `[-98.667, -12.000]`; D-A precision `+0.041068`, CI
  `[0.006710, 0.075562]`; D-A FP `-84.333`, CI `[-141.000, -27.333]`.
- Balanced C-to-D transitions per seed: 181 FP removed, 126 introduced, 548
  TP retained, 62-64 TP lost, and 37 TP gained; 111/170 passages changed.
- D sanitizer flags occur on 52 passages per seed. Those passages account for
  36 net fewer FP, while passages without a D flag account for 19. This is an
  association only; no unsanitized counterfactual exists.
- Seed agreement: D is identical on all 170 passages across every seed pair;
  B and C are also largely deterministic. The bootstrap is therefore
  passage-sampling uncertainty conditional on fixed outputs, not broad
  stochastic-seed robustness.
- Runtime audit: D seed 42 online CPU retrieval elapsed `6237.211 s`, with
  `5800.662 s` beyond LLM time; D seeds 43/44 replayed in about 435 s.
- M1 added 0 paid-GPU CNY. No model, API, vLLM, GPU, prompt, config, label,
  prediction, or LaTeX artifact was modified.

Full report: `docs/M1_PAIRED_EVIDENCE_AUDIT_20260729.md`. Hash-verified
machine-readable outputs: `refine-logs/m1_paired_evidence_20260729/`.

### M2 - Dev Baseline Audit

Complete for B001 and B003 under two separately bounded gates on 2026-07-29,
with local closeout verification completed on 2026-07-30.

- G used the frozen 73-entry glossary (88 eligible term/alias surfaces),
  literal case-sensitive matching, all occurrences, a two-character minimum,
  no normalization/fuzzy matching, and deterministic longest-first
  non-overlap.
- The 50-record `domain_dev` SHA256 remained
  `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`;
  the glossary SHA256 remained
  `01b857822894bb09268cbb7fb14ad0988630137bb7efae0b9d90f7d75a2f3ef6`.
- G produced 237 predictions: TP=4, FP=233, FN=303, precision `0.016878`,
  recall `0.013029`, F1 `0.014706`, FDR `0.983122`, and 4.66 FP/passage.
- Only four passages had a TP and all TPs were EQUIPMENT. MODULE,
  TECH_SCHEME, and METRIC had zero TP. Both zero-gold passages had predictions.
- Z used the locked Qwen2.5-7B schema-only protocol with K=0, temperature 0,
  no support read, glossary, RAG, or verification, and the shared proposal-
  stage sanitizer. The locked protocol SHA256 is
  `2ad29153ca0d5bc377d8cd3618fb3880566a3fa190a883a975f54d91b13267a0`.
- Z produced 343 predictions: TP=137, FP=206, FN=170, precision `0.399417`,
  recall `0.446254`, F1 `0.421538`, FDR `0.600583`, and 4.12 FP/passage.
- Z per-type F1 is EQUIPMENT `0.486301`, MODULE `0.488000`, TECH_SCHEME
  `0.085106`, and METRIC `0.098361`. Both zero-gold passages had predictions,
  with 11 predictions total.
- Thirteen initial parse failures were repaired by the fixed retry ladder. All
  63 requests received HTTP 200 and the final parse-failure count was zero.
- The Z audit verified the dev hash, embedded gold, recomputed metrics, cache
  set, request/HTTP counts, protocol exclusions, and absence of a dry-run
  prompt artifact. Local closeout independently matched all 74 manifest-listed
  file sizes and SHA256 values.
- Post-run checks showed no GPU and no relevant process. No frozen test,
  label/prediction edit, prompt/config tuning, or LaTeX change occurred.

Full report: `docs/M2_BASELINE_PREPARATION_20260729.md`. Hash-verified outputs:
`refine-logs/m2_domain_dev_g_exact_glossary_20260729/` and
`refine-logs/m2_domain_dev_z_schema_only_20260729/`. The Z manifest SHA256 is
`49479141750af9b44bd03226454b0d42081c6997490676f8ceb69210f7505109`.

### P6-QA0 - Frozen-Gold Audit Preparation

Complete in AutoDL GPU-free mode. At the end of this preparation step, no human
annotation had started; the later QA2 submissions and their invalid provenance
diagnosis are recorded below.

- Added `scripts/prepare_p6_qa0_blind_annotation.py` and four focused unit
  tests. All tests passed remotely in GPU-free mode.
- The script required the exact frozen test SHA256 and P2 `FROZEN` marker,
  matched all test text hashes to the source map, and refused existing-output
  overwrite.
- Generated two independently shuffled 170-row UTF-8 BOM CSVs. Each contains
  only `blind_id,text,entities_json,notes`; both annotation fields are blank.
- Seeds: A `2026072501`, B `2026072502`; orders and blind IDs differ.
- Generated a 170-row coordinator-only blind-ID map and an atomic manifest.
- Remote package:
  `/root/autodl-tmp/backup/p6/p6_qa0_blind_annotation_20260725/`.
- Local ignored backup:
  `backups/P6/p6_qa0_blind_annotation_20260725/`.
- Output SHA256:
  - A CSV: `3a36082631b45339d8b8e6ecd724ca3bbb7f74196531339ddb4621c4a72e1171`;
  - B CSV: `39b5ee7755ee48bd1c0d762e1ecdfd8c6a4251bdf8a0e1cf82a4c7ad149ae685`;
  - coordinator map: `d39d2252400cdc17a37eef78ed3a276c1f86c804d65e03f43cef31d752e38eb1`;
  - manifest: `45fa9fd6cb7886ad7b7bc58078de4391b57e3233bd41a9960be1368a88695451`.
- Full protocol and future gates:
  `docs/P6_QA0_FROZEN_GOLD_AUDIT_PLAN_20260725.md`.
- Cost impact: 0 paid-GPU CNY; no model/vLLM/dry-run activity. Post-generation
  check still reported GPU-free/no devices.

### P6-QA2 - Submitted Annotation Validation

Complete and blocked in AutoDL GPU-free mode.

- Submitted completed hashes:
  - A: `f07a650688c9cafcf4d16f5be906a0f45a3623838994cc9af2954385eb2183b7`;
  - B: `90e8e2458de3dd1f847a730759a353efb0a493bbbe385bbaa88fecf6acccd8ef`.
- Blind IDs, 170 texts, and text hashes matched the QA0 coordinator map.
- Structural result: 19 A rows not sorted, 2 B `entities_json` fields blank,
  and 181 unresolved repeated-mention candidates (180 A, 1 B).
- Only 149/170 strict pairs entered diagnostic comparison: exact file F1
  `0.557265`, 19 exact rows, 130 disagreement rows.
- Diagnostic per-type F1: EQUIPMENT `0.645852`, MODULE `0.548673`,
  TECH_SCHEME `0.032967`; METRIC was empty in both valid subsets and is not an
  interpretable 1.0 result.
- Formal human IAA is `null`. Repository provenance files show one shared
  `ANNO` dictionary and one `process_rows` function writing both A/B completed
  sheets. Later edits cannot restore independent blank-start provenance.
- Validator and four focused tests:
  `scripts/validate_p6_qa2_annotations.py` and
  `tests/test_validate_p6_qa2_annotations.py`; tests passed remotely.
- Full report: `docs/P6_QA2_ANNOTATION_VALIDATION_20260726.md`.
- Raw coordinator-only output:
  `/root/autodl-tmp/backup/p6/p6_qa2_annotation_validation_20260726/` and
  `backups/P6/p6_qa2_annotation_validation_20260726/`.
- Validation report SHA256:
  `aa614ad12cf9b7babf0ebb0e950ec44b960cb259226027142c7a0180acef6292`.
- No old gold, predictions, prompts, models, vLLM, or paid GPU were used; no
  labels were modified. Cost impact: 0 paid-GPU CNY.

### P6-QA1R - Diagnostic Repair And Non-Test Calibration Prep

Complete in AutoDL GPU-free mode. At the end of this preparation step, human
calibration had not yet started; the subsequently submitted calibration files
and their validation are recorded in the next subsection.

- Existing provenance-invalid QA2 files were used only as diagnostic inputs.
  They remain ineligible for human IAA or adjudication.
- Entity disagreement taxonomy across 130 rows:
  - same-boundary type conflicts: 127 instances / 60 rows;
  - same-type overlapping-boundary conflicts: 40 / 28;
  - overlapping boundary-and-type conflicts: 10 / 10;
  - unmatched A/B entities: 158 / 265.
- The dominant paired confusion was `EQUIPMENT -> TECH_SCHEME` with 104
  instances. This, 180 A repeated-mention warnings, and an empty METRIC class
  drove the revised operational rules.
- Added diagnostic and calibration-prep scripts with seven focused tests; all
  tests passed remotely:
  - `scripts/analyze_p6_qa2_disagreements.py`;
  - `scripts/prepare_p6_qa1r_calibration.py`;
  - corresponding tests under `tests/`.
- Added guideline and report:
  - `docs/P6_QA1R_ANNOTATION_GUIDELINE_V3_20260726.md`;
  - `docs/P6_QA1R_DIAGNOSIS_AND_CALIBRATION_20260726.md`.
- Prepared 24 text-only domain-dev calibration rows: six each for METRIC,
  TECH_SCHEME, EQUIPMENT/MODULE, and repeated-mention risk. A/B orders differ,
  annotation fields are blank, and no old dev labels, test gold, predictions,
  or coordinator IDs were exported.
- Coordinator-only diagnosis:
  `/root/autodl-tmp/backup/p6/p6_qa1r_diagnosis_20260726/` and
  `backups/P6/p6_qa1r_diagnosis_20260726/`.
- Calibration package:
  `/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726/` and
  `backups/P6/p6_qa1r_calibration_20260726/`.
- Frozen `domain_test.jsonl` and `FROZEN` hashes remained unchanged; the final
  server check still reported no GPU devices. Cost impact: 0 paid-GPU CNY.

### P6-QA1R - Submitted Non-Test Calibration Validation

Complete and blocked in AutoDL GPU-free mode.

- Completed input hashes:
  - A: `36613af484210ea7b916e744e1785b37ee5c47ed7bf41149ef5ac19af230bb0a`;
  - B: `9017bf65c8bd5e02a529bdef73f0ff845edc46d4471a84d80bb72615fc7aa8c7`.
- A/B each contained 24 rows; blind IDs, texts, hashes, blank sheets, and the
  coordinator map aligned exactly.
- Five B rows had `ENTITIES_NOT_SORTED`; 29 B repeated-mention reviews blocked
  the gate; four duplicate uncertainty codes were warnings.
- Strict 19-row concordance: A/B entities 188/140, 100 exact matches,
  P/R/F1 `0.7143/0.5319/0.6098`, and 1/19 exact rows.
- Because all hard errors were ordering only, a secondary non-repair diagnostic
  used all 24 rows order-insensitively: A/B entities 243/197, 142 exact matches,
  P/R/F1 `0.7208/0.5844/0.6455`, and 1/24 exact rows.
- Secondary per-type F1: EQUIPMENT `0.7081`, MODULE `0.5896`, TECH_SCHEME
  `0.3200`, and METRIC `0.7879`.
- The `0.6455` diagnostic is `0.2045` below the `0.85` calibration target.
  `formal_human_iaa` remains `null`; this calibration is not formal test IAA.
- Validator and six focused tests:
  `scripts/validate_p6_qa1r_calibration.py` and
  `tests/test_validate_p6_qa1r_calibration.py`; tests passed remotely.
- Full report: `docs/P6_QA1R_CALIBRATION_VALIDATION_20260727.md`.
- Final coordinator-only output:
  `/root/autodl-tmp/backup/p6/p6_qa1r_calibration_validation_20260727_r2/`
  and `backups/P6/p6_qa1r_calibration_validation_20260727_r2/`.
- No dev gold, frozen test, predictions, prompts, model calls, vLLM, paid GPU,
  or label repair was used. Frozen hashes remained unchanged.

### P6-QA1R - Guideline Reconciliation

Complete in AutoDL GPU-free mode; guideline v4 is locked.

- Added a locked, read-only reconciliation analyzer and six focused tests:
  - `scripts/analyze_p6_qa1r_calibration_reconciliation.py`;
  - `tests/test_analyze_p6_qa1r_calibration_reconciliation.py`.
- The analysis covered all 24 calibration pairs order-insensitively without
  writing back A/B labels: 243/197 A/B entities, 142 exact matches, 1 exact row,
  23 disagreement rows, and 119 classified events.
- Rule signals: scope/include-exclude 68, same-boundary type 26, repeated mention
  14, boundary 8, and boundary-plus-type 3.
- Same-boundary type directions were `EQUIPMENT->MODULE` 15,
  `TECH_SCHEME->EQUIPMENT` 8, and `TECH_SCHEME->MODULE` 3. Directions describe
  file differences, not gold.
- Prepared and reconciled:
  - `docs/P6_QA1R_GUIDELINE_RECONCILIATION_20260727.md`;
  - `docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md`;
  - `docs/P6_QA1R_GUIDELINE_V4_LOCK_RECORD_20260727.md`.
- The human approved `P6_QA1R_GUIDELINE_V4_LOCK_APPROVED` on 2026-07-27.
  The locked guide SHA256 is
  `a15289cd0f45bc23a0ce9d981db24745b814cfb94c6b03687e60a13b81b6ca80`.
  The lock-record SHA256 is
  `870ae640ad23070ecce63ae475c52da8f93081cb6a203a33908a65071a54d500`.
  Locking changed only version/status and future-gate wording; annotation
  decision rules were not substantively rewritten.
- Lock artifacts are mirrored under
  `/root/autodl-tmp/backup/p6/p6_qa1r_guideline_v4_lock_20260727/` and
  `backups/P6/p6_qa1r_guideline_v4_lock_20260727/`.
- No calibration sheet, label, gold, prediction, prompt, or model output was
  created or changed. The server remained GPU-free; cost impact was 0 CNY.
- Prepared separate role-specific reading/operation instructions for the two
  future annotators:
  - `docs/P6_QA1R_ANNOTATOR_A_INSTRUCTIONS_V4_20260727.md`;
  - `docs/P6_QA1R_ANNOTATOR_B_INSTRUCTIONS_V4_20260727.md`.
  A/B SHA256 are respectively
  `5f0cf56819a10e76e0a2639257b8c051af213e4ee2dfe6accdbf077509e9b136`
  and
  `432acf0f19315e9eb089726126c33aabc9e7830d2fe7ea243078c4f3ea180c65`.
  These files contain no calibration text or answer and do not authorize
  calibration preparation or human annotation.
- Instruction backups are under
  `/root/autodl-tmp/backup/p6/p6_qa1r_annotator_instructions_v4_20260727/`
  and `backups/P6/p6_qa1r_annotator_instructions_v4_20260727/`.
- Final coordinator-only output:
  `/root/autodl-tmp/backup/p6/p6_qa1r_guideline_reconciliation_20260727_r2/`
  and `backups/P6/p6_qa1r_guideline_reconciliation_20260727_r2/`.
- Final summary SHA256:
  `cf0b109b80667464aeb4f0e6b4a7fa5fc8c78b5b4966a8408e1654e0778fc115`.
- The 24 rows are retired as teaching/reconciliation material. They were not
  adjudicated or rescored and cannot become a new independent calibration.
- No dev/test gold, predictions, prompts, model calls, new calibration material,
  vLLM, paid GPU, or label changes were used. Frozen hashes remained unchanged.

### P6-QA1R - Old-24 V4 Rescore Diagnostic

Complete and still invalid for fresh independent calibration.

- User-submitted A/B rescore hashes were
  `2a128744bd3b8508d65555706fc7c8a1d4692c9f761b2d57d7fedc9ccb5698d5`
  and `8c49d04b4636835942c929fa91e1c56d3e41c95ebc4ace70cd40759052209bcd`.
- Both reused the retired 24 texts. Their scripts expanded all occurrences and
  resolved overlaps before writing the CSVs, so the outputs are not valid
  evidence of a fresh, direct, mutually blind human round.
- Structure was clean, but exact file concordance was only `0.814229`: 238/268
  A/B entities, 206 exact matches, and 3/24 exact rows. Per-type F1 was
  EQUIPMENT `0.7835`, MODULE `0.8421`, TECH_SCHEME `0.4000`, and METRIC
  `0.8889`.
- This exceeds `0.80` numerically but misses the locked calibration target
  `0.85`; more importantly, `formal_human_iaa` remains `null` because the
  provenance and fresh-set requirements fail.
- Diagnostic output is under
  `/root/autodl-tmp/backup/p6/p6_qa1r_old24_v4_rescore_diagnostic_20260727_r1/`
  and `backups/P6/p6_qa1r_old24_v4_rescore_diagnostic_20260727_r1/`.

### P6-QA1R - Fresh Calibration Preparation

Complete in AutoDL GPU-free mode. At the end of this preparation step, human
annotation had not started; the later completed human files and validation are
recorded in the next subsection.

- Added `scripts/prepare_p6_qa1r_fresh_calibration.py` and four focused tests.
  Together with three old-preparer regression tests, all seven passed remotely.
- The locked old coordinator map excluded all 24 retired text hashes from the
  50-row domain-dev file. Of the 26 unused rows, 20 were selected and six were
  preserved as coordinator-only reserve.
- Selection seed `2026072701` assigned five unique texts to each text-only risk
  bucket: METRIC, TECH_SCHEME, EQUIPMENT_MODULE, and REPEATED_MENTION.
- A/B seeds `2026072702/2026072703` produced different orders and new blind-ID
  prefixes `P6FRESH-A/B`. All annotation fields are blank.
- A/B delivery directories are physically separated and contain only the role's
  blank CSV, role-specific instructions, locked v4 guideline, and delivery
  manifest. Coordinator and reserve maps are outside both delivery directories.
- A/B blank-sheet SHA256 are
  `df8b99c99b83ecbe71b38b352d584fd1e0dc67df93ba4b1a9c347c14e984c89c`
  and `b7e7df0c7331c1af379cda8e01c6287c8de2e644d82758e170ad3c26699c6ff1`.
- Coordinator-map, reserve-map, and root-manifest SHA256 are respectively
  `6a902ab6e2063b52c1d8103cf777ed25dc2def31371a3f26866f51d3d9664e18`,
  `20fe19da3911ad56d478e23c32c021f6fb3c5b340bf784d72963b6d88f228c9b`,
  and `bc404d4aeb6c2cab1c303ac063f9fdd43b950a587787cc222dcabbc4a9adba00`.
- A full reload verified blank fields, A/B/map alignment, distinct order,
  retired overlap 0, delivery separation, and the exact 24+20+6 partition.
- Remote/local package:
  `/root/autodl-tmp/backup/p6/p6_qa1r_fresh_calibration_20260727/` and
  `backups/P6/p6_qa1r_fresh_calibration_20260727/`.
- Full report: `docs/P6_QA1R_FRESH_CALIBRATION_PREPARATION_20260727.md`.
- No test, prediction, prompt, model, vLLM, paid GPU, gold change, or annotation
  activity occurred. Cost impact was 0 CNY.
- The human subsequently approved
  `P6_QA1R_FRESH_CALIBRATION_ANNOTATION_APPROVED` on 2026-07-27. Only the two
  role-separated delivery directories were distributed. Both completed files
  were subsequently returned, hash-locked, and validated under the separate
  validation gate described below.
- Annotation start/return protocol:
  `docs/P6_QA1R_FRESH_CALIBRATION_ANNOTATION_START_20260727.md`.

### P6-QA1R - Fresh Human Calibration Validation

Complete in AutoDL GPU-free mode; no labels were changed. The human has accepted
this result as passing the original project minimum and has closed this QA issue
for the current paper-writing route.

- The coordinator explicitly confirmed that the final A/B files contain two
  human annotation results. Locked completed SHA256 are
  `6906142d5894c3a4f1332bed326258b4f9c35958baa17f8e8475339b435f8877`
  and `40428a8ed642685dd7940c60e3dc08af929dcaa4e71c0b7530e89eaa7dbb732e`.
- All 20 pairs passed structure: zero hard errors, zero blocking reviews, and
  all four types covered by both annotators.
- A/B entities were 175/220 with 158 exact matches. Precision/recall/F1 were
  `0.718182/0.902857/0.800000`; 5/20 rows were exactly equal and 15 disagreed.
- Per-type F1: EQUIPMENT `0.728261`, MODULE `0.898876`, TECH_SCHEME `0.153846`,
  and METRIC `1.000000`.
- The original minimum `>=0.80` is met exactly. The conservative v4 target
  `>=0.85` is not met, so the automatic validator status is still `blocked`.
- Human result-policy decision on 2026-07-27: accept `0.8000` under the original
  minimum and proceed to manuscript refinement. This is a documented policy
  acceptance, not a change to the measured result or validator output.
- This is valid fresh human calibration agreement, not frozen-test formal IAA;
  `formal_test_iaa` remains `null`.
- Final output:
  `/root/autodl-tmp/backup/p6/p6_qa1r_fresh_calibration_validation_20260727_r2/`
  and `backups/P6/p6_qa1r_fresh_calibration_validation_20260727_r2/`.
- Full report: `docs/P6_QA1R_FRESH_CALIBRATION_VALIDATION_20260727.md`.
- No test/gold/prediction/model activity occurred; frozen hashes remained
  unchanged and cost impact was 0 CNY.

### GPU-Free Markdown Manuscript Refinement

Complete on 2026-07-27 under the human-approved paper-refinement gate.

- Edited only
  `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md` and this
  `HANDOFF.md`; the five user-owned untracked P6 helper scripts that existed at
  that time were preserved without execution or modification.
- Added the 400-candidate construction summary, 30/50/170 frozen split,
  leakage controls, and the explicit absence of full frozen-test double
  annotation/formal IAA.
- Added the fresh two-human non-test calibration protocol and complete result:
  20/20 structurally valid pairs, 175/220 entities, 158 exact matches,
  P/R/F1 `0.718182/0.902857/0.800000`, and per-type F1 values of `0.728261`,
  `0.898876`, `0.153846`, and `1.000000` for
  EQUIPMENT/MODULE/TECH_SCHEME/METRIC.
- Recorded that `0.8000` exactly meets the human-accepted original `>=0.80`
  minimum but misses the later conservative `>=0.85` target, is not
  frozen-test formal IAA, and leaves `TECH_SCHEME` as a major limitation.
- Restored six-decimal P5 precision/recall/F1 values and retained all FP means
  and standard deviations. The paper consistently describes C/D as an F1
  near-tie: C is marginally higher in recall/F1; D is higher in precision and
  has 55.0 fewer FP on average.
- Removed "significantly" as a positive result claim and explicitly excludes
  RE, CoVe, public-benchmark generalization, K-scan robustness,
  statistical significance, and full-matrix completion from current claims.
- Document-only verification checked 31 required evidence literals, all clean
  F1/FP deltas, the 181/126 qualitative FP accounting and category sum, and
  `git diff --check`. No Python, frozen-test read, SSH job, project model,
  external LLM/API, dry-run, vLLM, GPU, or new experiment was used. Paid-GPU
  cost impact: 0 CNY.

### JISE-Oriented English Markdown Conversion

Complete on 2026-07-28 under the human-approved, GPU-free English-conversion
gate.

- The human selected Journal of Information Science and Engineering (JISE) as
  the intended primary target after the three-journal screening.
- Created docs/JISE_ENGLISH_MANUSCRIPT_DRAFT_V1_20260728.md from the
  evidence-locked Chinese Markdown manuscript. It is a plain UTF-8 English
  working draft, not a JISE template, LaTeX source, DOCX file, PDF, or
  submission package.
- Preserved the frozen 30/50/170 split, all A/B/C/D K=5 seed-42/43/44 numbers,
  the C/D F1 near-tie wording, the 55.0-FP reduction, and the seed-42
  181/126 qualitative FP accounting.
- Preserved the calibration disclosure: 20 fresh non-test passages, A/B
  175/220 entities, 158 exact matches, exact micro-F1 0.8000, original
  >=0.80 threshold accepted, later >=0.85 target not met, no frozen-test
  formal IAA, and TECH_SCHEME F1 0.153846.
- Explicitly excludes positive claims about RE, CoVe, public-benchmark
  generalization, K scans, statistical significance, and full-matrix
  completion. The same 17 source-checked references are retained, with
  preprints and data resources identified honestly.
- No Python, frozen-test read, SSH job, project model, external LLM/API,
  secondary agent, dry-run, vLLM, GPU, or new experiment was used. Paid-GPU
  cost impact: 0 CNY.

### GPU-Free JISE Submission Package

Complete on 2026-07-28 under the human-approved Markdown submission-package
gate.

- Created `docs/JISE_SUBMISSION_PACKAGE_20260728/` with eight UTF-8 Markdown
  files: manuscript, cover letter, author/system metadata, declaration and AI-
  disclosure options, two-editor selection, checklist, editorial-office query,
  and README.
- Rechecked the current official JISE submission, manuscript, preparation, AI-
  policy, and Associate Editor pages. The system requires a PDF for submission;
  final publication accepts JISE Word or LaTeX files; keywords must number
  5-10; references use square brackets in first-citation order; two relevant
  Associate Editors must be selected; AI tools/models and purposes must be
  disclosed in the manuscript or acknowledgements and in the submission system.
- Recommended Associate Editors, subject to live-list and conflict recheck:
  Makoto P. Kato (information retrieval/extraction/knowledge base) and Berlin
  Chen (information retrieval/NLP/machine learning). Shou-De Lin and Chao-Lin
  Liu are documented alternates.
- Corrected the earlier simplified length note: JISE's policy page uses 12
  template pages as a limit/charge boundary, whereas its manuscript page states
  regular manuscripts should be within 25 pages (short papers within 15) and
  also charges USD 100 per accepted page above 12. The package targets no more
  than 12 formatted pages conservatively and blocks submission pending written
  confirmation of length and all charges.
- Added an explicit AI disclosure: Qwen2.5-7B-Instruct is the evaluated
  experimental extractor; Qwen2.5-14B-Instruct-AWQ historically generated
  candidate suggestions that were not accepted as gold without human review;
  OpenAI Codex (GPT-5-based) assisted with English conversion, language editing,
  organization, and claim-evidence checks. No generative AI produced the two-
  human calibration annotations, changed frozen labels/numerical results, or
  generated manuscript figures/images.
- Static checks found all locked P5/P6 literals, 17 numbered references, five
  numbered table captions, and six keywords. The abstract in the manuscript and
  metadata form matches. Recomputed text-level deltas remain B-A `0.020524`,
  C-B `0.013689`, D-C `-0.003094`, C-D FP `55.0`, and the qualitative category
  sum `181`. `git diff --check` passed after Markdown cleanup.
- All `[[...]]` placeholders are intentional blockers. No author names,
  affiliations, funding, conflicts, ethics determination, licences, or public-
  release promises were invented.
- This package was prepared in the current Codex writing session; no project
  inference model, external LLM/API, second agent, Python, frozen-test read, SSH
  job, dry-run, vLLM, paid GPU, or new experiment was invoked. Paid-GPU cost
  impact: 0 CNY.

### Repository Version Cleanup

Complete on 2026-07-27 under the human-approved old-version cleanup request.

- Removed `docs/CONTINUATION_HANDOFF.md`, a stale 2026-07-20 P2 handoff that
  conflicted with the root `HANDOFF.md`, and refreshed `README.md` to make the
  root file the sole live status entry point.
- Removed seven ignored `backups/P5` patch copies whose only purpose was to
  recover superseded DOCX/paper-draft stages. Their source commits
  `660b641`, `79a807d`, `1d0464d`, `2ae8e38`, `b606084`, `873e618`, and
  `863c701` were verified as ancestors of the current Git `HEAD`, so those old
  versions remain recoverable from Git history.
- Marked the two retained P5 paper-review audits as historical evidence whose
  DOCX targets have been deleted, and pointed both to the sole current Markdown
  manuscript.
- Preserved all experiment configs, raw/per-query results, logs, failed and
  negative runs, frozen-data audits, calibration provenance, paper evidence
  reports, phase backups, and the five user-owned untracked P6 scripts that
  existed at that time. Files named `draft`, `v1/v2/v3`, or `sanity` were not
  deleted when they form part of the reproducibility or decision trail.
- No Python, frozen-test read, SSH job, project model, external LLM/API, vLLM,
  GPU, or experiment was used. Paid-GPU cost impact: 0 CNY.

## 3. Current Claim Boundary

Result-to-claim verdict: `partial`.

Supported claim:

> In a frozen low-label Chinese equipment-domain NER setting, kNN
> demonstrations and glossary injection improve entity extraction F1, while RAG
> evidence preserves near-tied F1 and improves precision / reduces
> false-positive entity predictions.

M1 refines the strength of this claim: the observed B-A and C-B F1 increases
are positive but their paired passage-bootstrap intervals include zero. The
most defensible interval-supported result is the RAG operating-point change:
D-C reduces FP by 55.0 with CI `[-98.667, -12.000]` while F1 remains near-tied;
D-A improves precision by 0.041068 and reduces FP by 84.333 with intervals
excluding zero. Use "observed increase" or "associated with" for B/C, and do
not use "significant" for their F1 changes.

M2 adds two dev-side baselines only. G's dev F1 is `0.014706` with 233 FP and
FDR `0.983122`; Z's dev F1 is `0.421538` with 206 FP and FDR `0.600583`.
This supports describing exact frozen-glossary matching as inadequate and Z as
a substantially stronger schema-only baseline on the same dev split. It does
not add a paper-facing frozen-test baseline row, permit comparison of Z's dev
score with A/B/C/D test scores as if they shared an evaluation split, or
authorize post-hoc tuning. Z's TECH_SCHEME and METRIC F1 values are only
`0.085106` and `0.098361`, respectively, and must remain visible limitations.

This result statement is conditional on the current frozen `v1` labels. The
paper may report the fresh two-human non-test calibration agreement exactly as
performed: 20 previously unused non-test passages, exact span+type micro-F1
`0.8000`, zero structural errors, and a major `TECH_SCHEME` limitation. It must
not rename this number as frozen-test IAA, imply that all 170 frozen test rows
were independently double-annotated, claim that all entity classes have good
agreement, or describe the dataset as fully quality-controlled human gold.

Safe dataset wording is: a small frozen equipment-domain dataset with a
documented annotation workflow and an independent non-test human-calibration
audit. Avoid stronger provenance language unless a later formal test audit and
new frozen version actually exist.

Not supported by current evidence:

- relation extraction success;
- CoVe/self-verification improvement;
- public benchmark generalization;
- K=1/K=10 robustness;
- full A..E-prime ablation matrix;
- supervised-SOTA-style claims;
- any claim that C significantly beats D.

Target after the newly selected extension, **not a current claim**:

- reproducible two-stage domain NER+RE with exact directed relation metrics;
- complete A/B/C/D/E/E-prime K=5 comparisons and pre-specified A/E K scans;
- relation-aware CoVe evaluated as a potentially positive or negative ablation;
- public NER portability on the complete labeled CLUENER dev split; and
- paired uncertainty and result-to-claim analysis over the complete inventory.

Completing rows does not guarantee that RE, CoVe, RAG, glossary injection, or K
robustness will be positive. Only observed results and intervals can support a
benefit claim. Until that evidence exists, the current `partial` verdict and
narrow NER wording continue to control every paper-facing statement.

Paper positioning:

- Current demonstrated task: NER.
- Selected target task: full domain IE, with NER primary and RE formally
  evaluated as an auxiliary evidence line after dev-first validation.
- Contribution style: applied/reproducible engineering pipeline plus small
  equipment-domain dataset and honest ablation evidence.
- Target: one-month SCI-Q4-oriented manuscript route, Chinese draft first and
  then English SCI manuscript.

## 4. Current Paper And Review Artifacts

Use these as the paper-facing evidence base:

- `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_PLAN_20260730.md` (planning only;
  authoritative full-IE scope and gates, not paper evidence)
- `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_TRACKER_20260730.md` (live cell
  inventory and F1 implementation status; not experimental evidence)

- `docs/JISE_SUBMISSION_PACKAGE_20260728/`
- `docs/JISE_ENGLISH_MANUSCRIPT_DRAFT_V1_20260728.md`
- `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`
- `docs/TARGET_JOURNAL_AND_REFERENCE_AUDIT_20260728.md`
- `docs/RESULT_TO_CLAIM_P5_DOMAIN_20260725.md`
- `docs/P5_DOMAIN_PAPER_EVIDENCE_20260725.md`
- `docs/P5_PAPER_REVIEW_AUDIT_20260725.md`
- `docs/P5_PAPER_P0_REVIEW_FEEDBACK_20260725.md`
- `docs/P6_QA0_FROZEN_GOLD_AUDIT_PLAN_20260725.md`
- `docs/P6_QA2_ANNOTATION_VALIDATION_20260726.md`
- `docs/P6_QA1R_ANNOTATION_GUIDELINE_V3_20260726.md`
- `docs/P6_QA1R_DIAGNOSIS_AND_CALIBRATION_20260726.md`
- `docs/P6_QA1R_CALIBRATION_VALIDATION_20260727.md`
- `docs/P6_QA1R_GUIDELINE_RECONCILIATION_20260727.md`
- `docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md`
- `docs/P6_QA1R_GUIDELINE_V4_LOCK_RECORD_20260727.md`
- `docs/P6_QA1R_ANNOTATOR_A_INSTRUCTIONS_V4_20260727.md`
- `docs/P6_QA1R_ANNOTATOR_B_INSTRUCTIONS_V4_20260727.md`
- `docs/P6_QA1R_FRESH_CALIBRATION_PREPARATION_20260727.md`
- `docs/P6_QA1R_FRESH_CALIBRATION_ANNOTATION_START_20260727.md`
- `docs/P6_QA1R_FRESH_CALIBRATION_VALIDATION_20260727.md`
- `docs/M1_PAIRED_EVIDENCE_AUDIT_20260729.md`
- `docs/FULL_IE_RELATION_CALIBRATION_PREPARATION_20260730.md`
- `docs/FULL_IE_RELATION_CALIBRATION_VALIDATION_20260731.md`
- `docs/FULL_IE_RELATION_CALIBRATION_REVALIDATION_20260731.md`
- `docs/FULL_IE_CONFIG_PREP_20260731.md`
- `docs/FULL_IE_DOMAIN_DEV_SANITY_20260801.md`
- `docs/FULL_IE_CLUENER_TUNE_SANITY_20260802.md`
- `docs/FULL_IE_F5_PROTOCOL_FREEZE_20260802.md`
- `refine-logs/m1_paired_evidence_20260729/`
- `docs/M2_BASELINE_PREPARATION_20260729.md`
- `refine-logs/m2_domain_dev_g_exact_glossary_20260729/`
- `refine-logs/m2_domain_dev_z_schema_only_20260729/`
- `findings.md`
- `logs/p5_c_vs_d_fp_qualitative_20260725.json`
- `logs/p5_c_vs_d_fp_qualitative_20260725.csv`

P0 paper repair already completed:

- Added variance explanation: A has fixed-random example-selection noise;
  B/C/D use kNN/replay, so variance is much smaller.
- Added C-vs-D qualitative FP analysis:
  - D removes/avoids 181 C-only false positives;
  - D introduces 126 new false positives;
  - net FP reduction is 55;
  - major categories: unsupported entity 84, type/overlap 34, short alias/code
    25, boundary error 24, metric fragment 14.

## 5. Non-Negotiable Execution Rules

- Never run project Python locally on Windows.
- Windows `D:\yinsir` is only for editing, Git, SSH/SCP, documentation, and
  lightweight artifact checks.
- All Python, tests, data processing, inference, evaluation, and aggregation
  must run on AutoDL through SSH alias `autodl-paper`.
- Until a new gate is approved, current work is local documentation/Git and
  lightweight read-only inspection only. All bounded gates through F5 are
  consumed. F1/F2/F3/F5 Python and tests ran on AutoDL GPU-free/no-card mode;
  F4a/F4b paid inference was separately closed, backed up, and returned to
  no-card. Nothing ran on Windows.
- Use paid GPU only for model inference/training and only after explicit human
  approval for one bounded step.
- After every GPU phase: stop vLLM, verify GPU memory returns to 0 MiB, back up,
  sync lightweight artifacts to `D:\yinsir`, report cost, and remind the human
  to shut down or switch to no-card mode.
- Never use `domain_test` for prompt tuning, glossary tuning, RAG tuning,
  threshold changes, or verification tuning.
- Do not run Stage R or relation-aware E/E-prime on real data, or run CLUENER,
  K=1/K=10, full P5, more seeds, dry-runs, model calls, or new `domain_test`
  prompt generation without the exact next bounded gate. The consumed F1 gate
  permitted synthetic fixtures only and still authorizes no model or final-
  evaluation action.
- Do not distribute any coordinator map to annotators. The prior 24-row human
  calibration gate is consumed; do not edit or rescore those same rows as a new
  independent round.
- The relation-calibration A/B workflow is complete through IE022. Do not edit
  either locked `revised_v2` file, rescore it under a new rule, or delete the
  IE021/intermediate failures. Future relation-gold adjudication or a fresh
  calibration round requires a separate gate and version.
- Guideline v4 is locked. Do not use the lock gate to generate or start a
  fresh calibration round; that requires
  `P6_QA1R_FRESH_CALIBRATION_PREP_APPROVED`.
- Fresh A/B annotation and validation are complete. Never edit these submitted
  files and recompute them to improve `0.8000`; preserve all 15 disagreement
  rows. Do not call this calibration number frozen-test formal IAA.
- The human has accepted the original `>=0.80` threshold for this submission
  route. Do not reopen the threshold dispute or demand another calibration
  round unless the human explicitly requests it or a target journal/reviewer
  creates a new bounded requirement.
- Do not treat the current A/B completed files or their `0.5573` diagnostic as
  human IAA. Do not repair them into an adjudication input; independence was
  already lost through a shared generation script.
- Calibration uses domain-dev text only and is not formal test IAA. Existing
  domain-dev labels are not calibration answers and must not be shown to the
  two annotators.
- Never overwrite frozen `v1`. Any corrected gold must be independently
  adjudicated, versioned as `v2`, re-frozen, and assigned new hashes.
- Preserve negative and mixed results; do not rerun them away.
- The narrow experiment package is closed and retained as a fallback. The
  selected full-IE extension now has tested infrastructure but remains
  experimentally incomplete. Never write that all planned experiments, RE,
  CoVe, public generalization, or the entire A..E-prime matrix passed.
- The real AutoDL host/port/passwords live only in the user's local SSH config.
  Use only the alias `autodl-paper` in docs and commands.

## 6. Repo And Machine Notes

Local:

- Workspace: `D:\yinsir`
- Branch: `main`
- Git remote: `https://github.com/QKY520/yinxin.git`
- Git identity for this repo: `yly <714520833@qq.com>`
- F4a closeout commit:
  `72065fe full-ie: close F4a domain dev sanity`.
- F4b closeout commit:
  `6ad6070 exp: close out F4b CLUENER tune sanity`.
- The F1 closeout adds only the eight approved Stage R/manifest runner and test
  files listed in Section 1, this handoff, and the dated full-IE tracker. It
  leaves all untracked P6, M1, M2, and old-plan artifacts untouched.
- JISE Markdown submission-package commit:
  `d5ba7ca docs: prepare JISE submission package`.
- JISE-oriented English working-draft commit:
  `fea7c43 docs: add JISE English manuscript draft`.
- Latest completed guidance commit before the manuscript-refinement pass:
  `87d2e8c docs: synchronize paper-stage project guidance`.
- Local `main` remains ahead of `origin/main`, and GitHub synchronization is
  intentionally paused. The M2 closeout artifacts and Z hash-verified package
  are captured by the local closeout commit. M1 analysis code, focused tests,
  report, and output directory remain untracked for a later separately scoped
  commit. The generic untracked `refine-logs/EXPERIMENT_PLAN.md` and
  `refine-logs/EXPERIMENT_TRACKER.md` belong to the earlier evidence-
  strengthening route; do not mistake them for the live full-IE plan, delete
  them, or commit them without a separate decision. The dated
  `FULL_IE_MINIMUM_EXPERIMENT_*_20260730.md` pair is the current route plan.
  Eight user-owned annotation helper scripts remain untracked:
  `p6_annotate_complete.py`, `p6_cal_b_annotate.py`,
  `p6_cal_b_annotate_v4.py`, `p6_complete_annotate.py`, and
  `p6_fresh_b_annotate.py`, plus `p6_relation_annotate.py`,
  `p6_relation_annotate_v2.py`, and `p6_relation_annotate_v3.py`. Preserve
  them; do not read, execute, modify, delete, or commit them unless the human
  explicitly requests it.
- Earlier calibration-validation commit:
  `fcd1556 p6: validate blocked calibration round`.
- QA1R diagnosis/calibration-prep commit:
  `f8162ce p6: prepare annotation agreement recovery`.
- QA2 implementation commit:
  `6690d92 p6: record blocked annotation QA2`.
- Previous QA0 commit:
  `a39a5a2 p6: prepare blinded frozen-gold audit`.
- GitHub push attempts through 2026-07-28 failed because the local proxy
  `127.0.0.1` could not connect. On 2026-07-29 the human explicitly instructed
  the agent not to retry GitHub push, pull, or connectivity checks. Keep all
  work local and attempt GitHub synchronization only when the human explicitly
  asks to "sync".

Remote:

- SSH alias: `autodl-paper`
- Remote code: `/root/project`
- Remote data/model/backup root: `/root/autodl-tmp`
- Project venv: `/root/autodl-tmp/venvs/equipment-ie`
- Status verified again during F4a closeout on 2026-08-01: remote Git HEAD
  remains `863c701`. The eight approved implementation/test files were manually synced
  for no-card testing. Five IE020 code/test/guideline files were later manually
  synced for no-card preparation and audit; the IE021 validator and test were
  then incrementally synced. IE022 additionally synced the versioned validator
  lock/test and the shared Stage R sentence-boundary fix/test. F3/F4a approved
  code, configs, and tests were then manually synced without GitHub. The remote worktree also retains
  pre-existing manually synced modified/untracked P6 files because GitHub sync
  is unavailable. Do not clean or reset that worktree, and do not overwrite its
  divergent handoff.
- F4b additionally synced its dated execution configs, summarizer, and focused
  test without GitHub. Remote Git HEAD remains older than authoritative local
  tracked history; do not clean/reset the dirty worktree.
- F5 used a tracked-only independent workspace at
  `/root/autodl-tmp/full_ie/f5_protocol_freeze_20260802/workspace`; it did not
  overwrite `/root/project` or its existing dirty files. The verified technical
  backup is under
  `/root/autodl-tmp/backup/full_ie/f5_protocol_freeze_20260802/`.
- F6 likewise used an independent workspace at
  `/root/autodl-tmp/full_ie/f6_replay_prep_20260802/workspace` and did not
  overwrite `/root/project`. Its partial verified backup is under
  `/root/autodl-tmp/backup/full_ie/f6_replay_prep_20260802/`.
- F6 recovery used another independent workspace at
  `/root/autodl-tmp/full_ie/f6_cluener_replay_recovery_20260803/workspace` and
  did not overwrite `/root/project`. Its verified backup is under
  `/root/autodl-tmp/backup/full_ie/f6_cluener_recovery_20260803/`.
- Last verified mode at F6 recovery closeout on 2026-08-03: the paid RTX 4090
  was visible with `0 MiB` used, no compute app, vLLM, Qwen, recovery
  runner, or active screen. One historical dead screen socket is preserved.
  The paid-mode cgroup `memory.max` was `128,849,018,880` bytes.
- Current reachability check at `2026-08-03T15:41:24+08:00`: SSH returned
  `Connection refused`. The instance is therefore unreachable and no current
  GPU/process state can be queried; no new paid action was started.
- The complete F4b backup remains under
  `/root/autodl-tmp/backup/full_ie/f4b_cluener_tune_20260802/`.

Useful no-Python status command:

```bash
ssh autodl-paper 'cd /root/project && git rev-parse --short HEAD && git status --short && (nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo GPU_FREE_OR_NVIDIA_SMI_UNAVAILABLE)'
```

## 7. Recommended Next Step

The route decision is complete: pursue the minimum defensible full-IE extension
and retain the narrow JISE NER package as fallback. F1-F3, F4a domain-dev
sanity, F4b CLUENER tune sanity, F5 protocol freeze, and F6 replay preparation
are complete. IE021 and the initial F6 no-card resource stop remain preserved
blocked attempts; IE022 completes F2 under its structural/full-disclosure
criterion. F4a/F4b ran only sanity data, F5 froze identities/dependencies, and
F6 prepared the domain and CLUENER replay dependencies without model calls.
F7 Domain Batch 1 is now scoped and hash-locked, but all execution flags are
false. There are still `0/60` complete full-IE cells. A new session must not
infer F7 execution, final-evaluation, aggregation, or paper authority from the
consumed F6 gates or the prepared proposal.

### Current state: F7 Batch 1 prepared; no final execution gate

The initial A/B returns and 90-error IE021 report remain locked negative
evidence. The user attested both submissions were human-produced. Human-revised
`revised_v2` files preserve all locked columns and now pass with zero structural
errors over 20/20 texts. A semicolon sentence-boundary implementation bug was
fixed and regression-tested without relaxing the no-cross-sentence rule.

Complete exact-directed file concordance is only F1 `0.417391`, with
`PART_OF=0.246154`; this is not formal IAA or support for a high-quality
relation-label claim. It is a disclosed calibration limitation. F4a reinforces
the risk: A-D dev exact RE F1 is at most `0.056680`, and no configuration has a
`HAS_METRIC` TP. E-prime gives a local positive dev signal, but E is negative;
D is slower and below C. F4b then shows D strongest on the 50-record CLUENER
tune subset, but its E-prime row is negative and E's small positive F1 delta
does not pass the deletion-audit gate. F4b is tune-only, not public benchmark
generalization. F5 locks the literal 60-cell protocol, but all 60 cell configs
and execution nodes remain unauthorized. F6 verified the 170-row domain replay
and the recovered 1,343-row CLUENER replay; this is dependency preparation, not
evaluation evidence. The proposed first F7 batch contains only A/B/C/D K=5
seed42 Stage R over four frozen Stage N files. Its authorization remains false,
and SSH currently returns `Connection refused`. Stop until the human grants
`FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` for this exact scope and budget, then
boots the 4090 and reports the live price. Do not run official CLUENER final
evaluation, other domain cells, Stage N, E/E-prime, F8/F9, or edit the paper.

### Later sequence: planned, not authorized

1. F3: complete; domain-dev and CLUENER-tune resources/configs are prepared.
2. F4a: complete; bounded domain-dev IE sanity consumed its one allowed
   protocol revision and closed with limitations.
3. F4b: complete under the consumed `FULL_IE_CLUENER_TUNE_SANITY_APPROVED`
   gate; fixed CLUENER tune sanity is audited, backed up, and stopped.
4. F5: complete under the consumed `FULL_IE_F5_PROTOCOL_FREEZE_APPROVED` gate;
   60 identities and all dependency/resource/source locks are frozen.
5. F6: complete; domain replay has 170 rows and recovered CLUENER replay has
   1,343 rows. The initial resource stop and the resumed checkpoint are both
   preserved; no model call or final cell was produced.
6. F7: Batch 1 proposal is prepared for A/B/C/D K=5 seed42 Stage R only;
   after its separate gate, run domain final cells in bounded paid batches,
   reusing the 12 existing Stage N outputs where frozen.
7. F8: run the 30 CLUENER NER cells on complete labeled official dev.
8. F9: aggregate, perform paired uncertainty/result-to-claim, then request a
   separate manuscript-propagation gate.

The original plan estimates `125-295 CNY` of additional paid compute. F4a now
provides a first dev benchmark, but the estimate still has large uncertainty
and must be recalculated before final batches because final split sizes, cache
reuse, RAG latency, and paid-mode idle time differ from the bounded sanity.
Stop for a new budget decision before additional spend exceeds 300 CNY or the
project total approaches the existing 400 CNY target. Platform billing is
authoritative.

### Full-matrix accounting

- original contract: 60 reported cells = 30 domain + 30 CLUENER;
- existing: 12 domain A/B/C/D K=5 cells with NER Stage N only;
- absent: 48 reported cells;
- required RE work: all 30 domain cells need Stage R;
- F4b adds six tune-sanity rows only, not reported cells; final accounting is
  still `0/60`, with 12 reusable domain Stage N outputs and 48 report cells
  wholly absent;
- F5 freezes all 60 report identities and validates the 12 reuse artifacts, but
  adds no Stage R, verifier, CLUENER-final, or complete-cell result;
- F6 prepares the shared 170-row domain and 1,343-row CLUENER replay
  dependencies but no Stage N/R, verifier, CLUENER-final, or complete-cell
  result;
- the prepared F7 Batch 1 proposal covers four Stage R-only cells but remains
  unauthorized and contributes `0` complete cells;
- CLUENER official unlabeled test is never offline gold; use the locked labeled
  dev protocol only after its own tune/resource freeze;
- E v1/v2 remain preserved negative/mixed historical NER dev evidence. F4a now
  adds relation-aware dev runs: E-prime is locally positive and E is negative.
  F4b CLUENER tune reverses that pattern: E-prime lowers F1, while E is only
  slightly positive and misses the deletion-audit threshold. None is a final
  matrix cell.

The JISE author/JCR/fee/AI-policy/template blockers remain valid but are not the
immediate machine step while the full-IE extension is being pursued. Actual
journal submission remains unauthorized.

## 8. Lessons Worth Remembering

- A human gate and a running resource are separate facts. F4b started only
  after both its bounded approval and a clean RTX 4090 preflight existed; its
  later no-card state means the run is stopped, not still authorized.
- Prepared F3 configs are hash-locked provenance. For an approved run, create a
  dated execution copy with the gate record and output paths; do not overwrite
  the prepared originals merely to flip `authorized/model_calls_allowed`.
- The human has selected a full-IE extension; the narrow NER/JISE package is a
  fallback, not permission to describe the current evidence as full IE.
- A route decision or experiment plan is not an execution gate. Every no-card,
  paid-dev, final-evaluation, aggregation, and paper-propagation phase still
  needs its own bounded approval.
- The existing narrow experiment package is closed and reproducible, but it is
  not a completed full-matrix IE experiment.
- The fresh human calibration solved the immediate `>=0.80` credibility gate
  for proceeding with the paper. It did not create frozen-test formal IAA or
  erase class-specific ambiguity.
- Preserve both threshold facts: the original minimum was met exactly and the
  human accepted it; the later conservative `0.85` target was not met and the
  validator output must not be rewritten.
- Structurally frozen data is not automatically publication-grade human gold.
  The `0.9909` pseudo-IAA must never be cited as human agreement.
- True A/B annotation must start from blank text, remain mutually blind, and
  include every explicit repeated mention. An agent cannot substitute for a
  human annotator or human adjudicator when the paper claims human gold.
- A shared annotation dictionary that writes both A and B invalidates human
  independence even if one file is edited afterward. File agreement is not
  annotation provenance.
- Low agreement must be repaired through non-test calibration and clearer
  operational rules, not by editing labels to reach a threshold. The present
  diagnosis found physical-system versus TECH_SCHEME confusion, repeated
  mention omissions, and complete METRIC under-coverage as the main risks.
- The first v3 calibration round also failed: order-insensitive F1 `0.6455`,
  with TECH_SCHEME F1 `0.3200`, MODULE F1 `0.5896`, and 29 repeated-mention
  reviews. Discuss it to improve v4, then use a fresh unused calibration set;
  never relabel the same 24 rows and call the new score independent agreement.
- Reapplying v4 to those same retired 24 rows yielded clean file concordance
  `0.8142`, but it remains invalid for fresh human calibration and exposed
  TECH_SCHEME F1 `0.4000`. Familiar items plus scripts that expand mentions or
  resolve overlaps cannot establish independent-human provenance.
- The genuinely fresh 20-row human calibration reached exact micro-F1 `0.8000`
  with perfect METRIC and strong MODULE agreement, but TECH_SCHEME F1 remained
  only `0.1538`. Meeting the overall minimum does not erase this class-specific
  limitation or create formal-test IAA.
- The coordinator explicitly attested that the final fresh A/B files are human
  annotations. Use that accepted provenance; do not reopen the earlier
  script-origin dispute for these final files.
- The relation `revised_v2` files are also coordinator-attested human work and
  structurally valid, but their exact-directed concordance F1 is only
  `0.417391` (`PART_OF=0.246154`). Treat this as a disclosed relation-quality
  limitation, not formal IAA or positive RE evidence.
- Chinese semicolons delimit clauses inside an orthographic sentence and are
  common in equipment/patent enumerations. Shared Stage R sentence logic must
  not treat `；;` as a sentence terminator; true full-stop cross-sentence and
  pronoun-based links remain forbidden.
- Reconciliation found 119 events across 23/24 rows. The dominant fix is not a
  looser metric; it is an explicit inclusion/exclusion policy, object-versus-
  method decision order, evidence-based EQUIPMENT/MODULE role, alias role
  persistence, full metric/model boundaries, and per-annotator preflight.
- Old frozen `v1` must be preserved. Any correction is a new `v2` with blind
  adjudication, new hashes, and uniform re-scoring only after a later gate.
- C and D are a near-tie on F1. D's value is FP/precision reduction, not a large
  F1 gain.
- The stronger paper is the honest one: do not overclaim RE, CoVe, public
  generalization, or statistical significance.
- Glossary helps recall/F1 but can add false positives.
- The exact frozen-glossary matcher is not a competitive standalone system on
  dev: F1 `0.014706`, 233 FP, and FDR `0.983122`. Preserve this negative lower
  bound; do not tune it after the fact under the same G name.
- The locked schema-only Z baseline completed on dev at F1 `0.421538`, with
  206 FP and FDR `0.600583`. It is dev-only and must not be inserted into the
  frozen-test A/B/C/D table or compared across splits as though it were a test
  result. TECH_SCHEME and METRIC remain weak at F1 `0.085106` and `0.098361`.
- RAG is slower because CPU embedding/reranking dominated D's wall time; future
  RAG runs need replay manifests or timing hygiene if more experiments are ever
  approved.
- P5 A/B/C/D were NER-only configs (`schema.task: ner`, empty relation types);
  zero relation predictions are expected and are not evidence that RE failed as
  a tested module.
- Verification E v1 was a clear dev method failure (`0.4264` F1 versus D
  `0.5415`; 18/20 audited drops wrong). E v2 was mixed/negative (`0.5367`;
  7/13 wrong drops, 5/13 correct, 1/13 unclear), and E v3 was preparation only.
  F4a is a distinct relation-aware protocol: E-prime improved dev NER/RE F1,
  while E lowered both. Never collapse these versions into one result.
- CoVe is deletion-only in the current design: it cannot recover missed
  entities or repair boundaries/types. It improves F1 only when dropped units
  are overwhelmingly false positives. In the implemented relation-aware path,
  dropping an entity also removes incident relations, so over-deletion has a
  larger error cascade. F4a confirms both outcomes: E-prime's deletion precision
  raises dev F1, while E deletes its only relation TP and lowers dev F1.
- Completing all 60 rows proves evaluation completeness, not positive module
  gains. Negative RE, CoVe, RAG, glossary, public-transfer, or K-sensitivity
  findings must remain visible and control the final claims.
- The 12 frozen A/B/C/D K=5 outputs can reuse Stage N by hash. Stage R and exact
  directed metric infrastructure now have a real dev sanity, but no dev output
  counts as a final full-IE cell. Final Stage R still requires separately
  authorized frozen-protocol execution.
- AutoDL no-card mode may have tight memory limits. Avoid loading BGE-M3 unless
  needed; prefer cached/replay artifacts when they preserve comparisons.
- DOCX output caused encoding/rendering trouble in this workflow. Use Markdown
  as the working manuscript format.
- The current Chinese/English drafts, JISE Markdown package, and official-style
  LaTeX/Overleaf project include the accepted fresh-calibration result,
  explicit dataset-quality caveats, exact P5 values, and a consistent claim
  boundary. The human reported a clean-looking first Overleaf compile, but its
  log/PDF proof still needs local retention and visual audit. Author identity/
  declaration completion and target-specific JCR, fee, AI-policy, and final-
  format confirmation remain required before submission.
- Backups and hashes matter. Never leave the only copy of data/results on the
  AutoDL instance.
- Every new paid action needs an explicit bounded human gate, even if it seems
  technically small.
- Full-matrix completion is an optional evidence expansion, not a prerequisite
  already imposed on the current narrow SCI-Q4 manuscript route.
