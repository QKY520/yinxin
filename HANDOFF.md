# HANDOFF.md - New Conversation Handoff

Date: 2026-08-09
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
7. `docs/FULL_IE_F7_DOMAIN_BATCH1_CLOSEOUT_20260804.md` - F7 evidence, audit,
   cost, backup, and machine-state closeout.
8. `docs/RESULT_TO_CLAIM_F7_NER_FALLBACK_ROUTE_FREEZE_20260804.md` - latest
   result-to-claim verdict and human route decision.
9. `docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_GATE_20260804.md` - consumed
   public-NER execution scope, dependencies, time/cost stop, validation,
   backup, and exclusions.
10. `docs/NER_PUBLIC_CLUENER_B44_C44_D44_RESUME_GATE_20260805.md` - consumed
    seed44 resume checkpoint, time/cost stop, and recovery exclusions.
11. `docs/NER_PUBLIC_CLUENER_ABCD_K5_POSTVALIDATION_CHECKPOINT_20260805.md` -
    human pause after 12-cell v2 validation and before backup/closeout.
12. `docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_CLOSEOUT_20260806.md` - completed
    public-NER metrics, tests, backup, local mirror, cost, and machine state.
13. `docs/RESULT_TO_CLAIM_NER_PUBLIC_CLUENER_ABCD_K5_20260806.md` - focused
    public-NER verdict, bounded portability wording, and anti-claims.
14. `docs/NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_CLOSEOUT_20260807.md` -
    consumed LaTeX gate, manuscript commits, static audit, unresolved human
    inputs, and the next paper-only decision.

If older docs conflict with this file on status chronology, this file is newer.
Hard rules in `AGENTS.md` and `AGENT_PLAYBOOK.md` still apply.

## 0. Authoritative Snapshot For A New Session

**What we are doing**: the experiment route, evidence-to-paper propagation,
four Overleaf compile audits, consolidated post-audit EC-FSIE refinement, a
verified Related Work/citation-coverage pass, the bounded Overleaf-v3 source
corrections, the v4 pagination pass, and the final v5 Method-widow microfix are
finished locally. The project preserves an SCI-Q4-oriented Evidence-Controlled
Few-Shot Information Extraction (`EC-FSIE`) manuscript whose main contribution
is low-label Chinese equipment-domain NER. The one-sentence v5 source is newer
than the audited v4 PDF and now awaits one clean human Overleaf recompilation;
no experiment or paper-edit gate is live after this closeout.

**What is complete**:

- P0-P6, full-IE F1-F6, F7 Domain Batch 1, the focused 12-cell CLUENER block,
  both result-to-claim reviews, validation, backups, and machine closeout are
  complete. vLLM and all runners are stopped; the instance was last verified
  in no-card mode.
- Literal matrix accounting is `16/60`: 4 domain Stage N+R cells and 12
  CLUENER NER cells are complete; 8 domain cells retain Stage N only and 36
  cells are absent. All 44 incomplete identities are intentionally `CLOSED`,
  not an active backlog or failed experiments.
- The exact `NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED` gate was
  granted and consumed. Commit `8189f71` propagated verified evidence and
  limitations into the complete LaTeX project. Commit `8f1f3e1` consistently
  framed the method as the EC-FSIE framework without changing results.
- The exact `JISE_ECFSIE_LATEX_FINAL_REFINEMENT_APPROVED` gate is also consumed.
  It strengthened the title, abstract, contribution logic, framework
  formalization, controlled-evaluation narrative, negative RE boundary, and
  limitations across the authorized active LaTeX sources. CLUENER is described
  only as a limited descriptive directional replication, and RAG only as an
  observed precision/false-positive operating-point shift under near-tied F1.
- A non-Python source audit covered all 13 `.tex` files and one `.bib`: TeX
  environments and braces passed, all 8 labels and 10 references resolve, all
  27 citation uses resolve to 17 unique BibTeX keys, all 11 section files are
  referenced, and the numeric-literal sequence in every edited manuscript file
  matches its pre-refinement `HEAD` version.
- The human granted `JISE_ECFSIE_METADATA_COMPILE_PDF_AUDIT_APPROVED` and then
  deferred author/declaration metadata. The supplied Overleaf artifacts compiled
  successfully to 17 pages with zero LaTeX errors, undefined citations,
  undefined references, BibTeX warnings, or rerun requests. The audited PDF
  SHA256 is `A19BCB8C68D6721C4E75D6A9F36FD9A94A37975BC10CA72F58204A56DF318E0D`;
  the output ZIP SHA256 is
  `CD9A090270688BE4A9F0D00D4BAFC0B2AAB7C0DC784D9803A6160F09CED3C88A`.
- The post-audit refinement shortens the title and abstract, updates keywords,
  adds a grayscale TikZ EC-FSIE architecture figure, adds three locked C-only
  qualitative cases and a claim--evidence map, strengthens the Related Work gap,
  repairs BibTeX capitalization/name parsing, removes the Table 4 header
  overflow source, and consolidates Discussion/Limitations/Conclusion. It adds
  no experiment, recomputation, citation, or human metadata.
- Commit `210f5fa` contains that post-audit source refinement. The human then
  returned `JISE_OVERLEAF_LATEX_20260729__2_.pdf` and its Overleaf output ZIP.
  The second compile produced 18 uniform A4 pages with zero LaTeX errors,
  undefined citations/references, BibTeX warnings, or rerun requests; ChkTeX
  and qpdf both returned zero. The PDF SHA256 is
  `A09C4700F9D9C49BC6C218075CEBB84484AF6EF1A0F0C8D417CC1B3D86BF7B0E` and
  the ZIP SHA256 is
  `11311C3519B0EC92218022B5D9BE4FE0CE7083C00A608E36C1DC27D2166356C2`.
  Visual audit found one real `18.6267 pt` architecture-node overflow, a
  disclosure sentence that no longer accurately accounts for Codex-assisted
  TikZ drafting, one contribution-list orphan, and three undesirable page-edge
  word/compound splits. The previous Table 4 overflow and abstract spill are
  fixed; all new tables render within the page.
- The current static audit covers 14 `.tex` files and one `.bib`: environments,
  braces, and all inputs pass; 11 unique labels and 14 references resolve; all
  37 citation occurrences resolve to 27 unique BibTeX keys; no section is
  orphaned; and all 23 numeric tokens in the v5-edited Method file remain
  exactly unchanged from `HEAD`.
- The exact paper-only gate
  `JISE_ECFSIE_VERIFIED_RELATED_WORK_CITATION_PROPAGATION_APPROVED` was granted
  and consumed on 2026-08-09. The authorized pass modifies only Related Work,
  `references.bib`, and this handoff. It adds ten cross-verified peer-reviewed
  references covering prompt retrieval, modern generative/generalist IE/NER,
  RAG reliability, and direct Chinese military/equipment NER. It also upgrades
  GPT-NER from its 2023 preprint record to the Findings of NAACL 2025 version.
  The current closure has 37 citation occurrences resolving to 27 unique
  BibTeX keys, with zero missing, duplicate, or uncited keys and balanced BibTeX
  braces. No experiment, metric, result table, dataset claim, or human metadata
  changed.
- The human accepted the exact bounded gate
  `JISE_ECFSIE_OVERLEAF_V3_SOURCE_CORRECTIONS_APPROVED`; it is consumed by the
  current closeout. Only `main.tex`, the TikZ architecture source, five section
  files (four containing the identified pagination phrases plus the disclosure
  section), and this handoff were authorized. The architecture model label is
  explicitly wrapped inside its node; the contribution page receives one additional
  baseline; three vulnerable words/compounds are protected from undesirable
  page-edge splitting; and the disclosure now accurately records Codex-assisted
  TikZ drafting without implying that manuscript-preparation AI produced or
  altered experimental outputs. Native pdfTeX metadata now supplies the verified
  title, subject, and keywords while leaving author metadata unset. Static audit
  reports 26/26 environments, 11 unique labels, 14 resolving references, 37
  citation occurrences resolving to 27 BibTeX keys, no numeric-literal changes
  in any corrected file, and no changes to the frozen Related Work or
  bibliography from the preceding citation commit.
- The human supplied `JISE_OVERLEAF_LATEX_20260729__3_.pdf` and its Overleaf
  output ZIP. The third compile produced 19 uniform A4 pages with zero LaTeX
  errors, undefined citations/references, BibTeX warnings, or overfull boxes.
  All 19 pages were visually audited: PDF title/subject/keywords, the wrapped
  architecture node, disclosure, tables, and all 27 references render correctly,
  with no clipping, blank pages, or missing content. The PDF SHA256 is
  `DACE96E40038DAC0FCFA9B588967F44E75FF3398BC944ABA8DD77B8B2BF88AC5` and
  the ZIP SHA256 is
  `C824453B9DBFD7D72BDEB0DE273F07F73C974E050ED69651702AFD27AFA0A8BE`.
  Nine underfull hbox and four underfull vbox warnings caused no visible defect.
  The audit identified only three pagination blemishes: a one-line Method widow,
  `numer-/ically` across the Results page boundary, and an isolated `gain.` at
  the top of the second Conclusion page.
- The exact `JISE_ECFSIE_OVERLEAF_V4_PAGINATION_MICROFIX_APPROVED` gate was
  granted and is consumed by this closeout. It changes only
  `sections/04_method.tex`, `sections/06_results.tex`, and
  `sections/09_conclusion.tex`, plus this handoff. Three semantically equivalent
  sentence shortenings target the audited page breaks without changing any
  experiment number, table, citation, negative result, limitation, or claim
  boundary. Non-Python static checks pass with zero environment mismatches,
  duplicate labels, missing references, missing BibTeX keys, missing inputs,
  orphan sections, brace-count failures, or verification markers. Local LaTeX
  compilation remains unavailable and is not claimed.
- The human supplied `JISE_OVERLEAF_LATEX_20260729__4_.pdf` and its Overleaf
  output ZIP. The fourth compile again produced 19 uniform A4 pages with zero
  LaTeX errors, undefined citations/references, BibTeX warnings, rerun requests,
  or overfull boxes; ChkTeX and qpdf both returned zero. The PDF SHA256 is
  `54249AF7C31853CBB29D28AAD30F47F2DC7946E6BC61BBE164E1C430B366DFF0` and
  the ZIP SHA256 is
  `C55B5CFEA49076A9EF8F30C9815F5D356E3ABBB2BF84D630EA9503310FEBD1BF`.
  All 19 pages were visually audited. The Results `numer-/ically` split and the
  isolated Conclusion `gain.` were fixed, while the Method sentence still
  crossed pages after `it is not a`, leaving `post-hoc filter.` alone at the top
  of page 9. Nine underfull hbox and four underfull vbox warnings caused no
  clipping or other visible defect. Metadata remained correct with no Author
  entry; pdfTeX listed all used Type1 PFB fonts, but local `pdffonts` was absent.
- The exact `JISE_ECFSIE_OVERLEAF_V5_METHOD_WIDOW_MICROFIX_APPROVED` gate was
  granted and is consumed by this closeout. It changes only
  `sections/04_method.tex` and this handoff. The shorter positive formulation
  `RAG evidence constrains extraction during generation.` preserves the
  evidence-control timing while removing the negative post-hoc wording and the
  source of the audited page-top fragment. No experiment number, table, citation,
  result, negative finding, limitation, or claim boundary changes. Non-Python
  static checks pass; actual V5 pagination still requires Overleaf compilation.

**Current paper state**: the sole active manuscript is
`docs/JISE_OVERLEAF_LATEX_20260729/`. `main.tex` is the Overleaf entry point;
`frontmatter.tex`, `sections/*.tex`, the bibliography, and the TikZ source under
`figures/` carry the content. Historical Markdown drafts are reference artifacts
only. The v4 source compiled successfully and was visually audited in the
19-page `__4_` PDF; the one-sentence Method widow microfix is newer and has not
yet been compiled. This Windows control workspace still lacks `latexmk`,
`pdflatex`, and `bibtex`. Author/order/affiliation/corresponding-author,
acknowledgments, funding, conflicts, data/code availability, ethics, and CRediT
fields still require human-confirmed values. The paper is not submitted.

**Supported claims**: in frozen low-label Chinese equipment-domain NER, kNN
demonstration selection and the domain lexicon improve observed F1/recall;
RAG preserves near-tied F1 while increasing precision and reducing entity-level
FP. On all 1,343 labeled official CLUENER dev rows, the same clean comparison
directions provide limited descriptive replication on one additional Chinese
NER benchmark.

**Auxiliary value**: F7 shows that the locked Stage N + Stage R pipeline can
produce reproducible, per-row auditable final cells. This is reproducibility
evidence, not positive RE evidence.

**Relation to the proposal (附件四)**: the current public Chinese equipment and
military-technology text experiment can be used as a text-modality,
domain-knowledge-enhanced, few-shot NER/RAG pilot for the proposal's equipment
information-extraction direction. It is not a complete proposal validation: the
data are not the full network-equipment R&D corpus, image/table and cross-modal
alignment are absent, and the positive evidence is mainly NER while RE is weak.
The defensible bridge wording is that this work supplies a text-semantic basis
for later relation extraction, cross-modal semantic association, and retrieval
services on network-equipment R&D data.

**Unsupported claims**: statistical significance, SOTA, broad public/cross-
domain generalization, positive RE, public RE, RAG-for-RE, CoVe, usable
`HAS_METRIC`, K robustness, frozen-test formal IAA, high-quality relation
annotation, a complete 60-cell matrix, complete F8/F9, or complete end-to-end
IE success.

**Next plan**: no GPU is needed. The human should upload the current active
project to Overleaf, keep `main.tex` as the root, compile an `__5_` PDF, and
return the PDF plus output ZIP/log. The next read-only gate should be
`JISE_ECFSIE_OVERLEAF_V5_COMPILE_PDF_FINAL_CONFIRMATION_APPROVED`; it should
confirm that page 9 no longer begins with the Method fragment, then repeat the
error, warning, reference, metadata, font, and full visual checks. Human author
and declaration metadata may remain deferred. Any further source edit,
submission, external upload beyond this human Overleaf action, or GitHub
synchronization requires separate authorization.

**Lessons and red lines**: result-to-claim controls prose; framework positioning
may be strengthened but missing evidence cannot become a result. `CLOSED` is a
human route decision, not failure. CLUENER gives one-benchmark directional
replication, not broad generalization. RAG's supported effect is a precision/FP
operating-point trade-off, not an F1 gain or elimination of hallucination.
Never run project Python locally, never use frozen test to tune, never erase
negative/failure history, never touch the untracked P6/M1/M2/old-plan files,
and never reset, clean, submit, or synchronize GitHub without authorization.

Everything below is detailed chronology. Any future-tense statement below
about waiting for the CLUENER LaTeX propagation gate is superseded by this
2026-08-09 snapshot and the versioned closeout.

Historical route and execution chronology (from 2026-07-30): the human wanted
to expand the project into
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
F7 Domain Batch 1 was first prepared locally as a four-cell Stage R-only
proposal: `domain:A/B/C/D:k5:s42`. Its contract SHA256 is
`0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973`.
The human subsequently granted the exact
`FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` gate. AutoDL no-card preparation and
preflight produced a versioned authorized execution package, deterministic
compatibility views for all `680` frozen Stage N rows, and a locked execution
manifest with SHA256
`893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1`.
Remote F7 preparation tests passed `4/4`, affected tests passed `21/21`, and
the then-complete suite passed `199/199`. On 2026-08-04 the human attached the
approved RTX 4090 and reported `2.8 CNY/hour`. A/B/C/D then ran serially and all
four 170-row Stage R outputs independently passed metric, hash, prompt/cache,
and structural audits. A versioned no-model v2 finalizer repair preserved a v1
string-versus-Path failure; the final complete suite passed `200/200`. F7 is
now `DONE`, contributes `4/60` complete cells, and consumed its gate. vLLM was
stopped and the instance is back in no-card mode. The later route-freeze gate
superseded the planned continuation described in this historical chronology.

## A. Historical Detailed Snapshot Through The Public-NER RTC

**Historical task at that breakpoint**: wait for the separately approved
paper-only `NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED` gate. That
gate was later granted and consumed in commits `8189f71` and `8f1f3e1`. The
scientific line remains low-label Chinese equipment-domain NER plus a bounded
one-benchmark CLUENER replication. RE is an exploratory negative result/
limitation; the remaining 44 incomplete matrix identities are closed.

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
cell. F7 Domain Batch 1 is now complete for four Stage R-only seed42 cells.
All `680` rows, `647` model requests, prompt/cache/raw artifacts, and exact
metrics were independently audited. The versioned v1 finalization failure is
preserved, the no-model v2 repair passed the complete remote suite at
`200/200`, and the verified matrix count is now `4/60`.

**Current evidence**: the three-seed A/B/C/D NER F1 fallback remains
`0.534645/0.555169/0.568858/0.565764`. C/D are an F1 near-tie; D has higher
precision and 55 fewer FP. F7 adds final single-seed exact RE F1
`0.040541/0.056972/0.057971/0.045381` for A/B/C/D. `B-A` is weakly positive,
`C-B` is effectively tied, and `D-C` is negative. D reduces the absolute
relation FP count versus C but also loses TP and has lower RE precision; all
four configurations have zero `HAS_METRIC` TP. This does not support a positive
RE contribution, positive RAG-for-RE claim, three-seed RE aggregate, CoVe,
broad public/cross-domain generalization, K robustness, or full-matrix claim.
Human entity
calibration `0.8000` is not frozen-test formal IAA; `TECH_SCHEME` F1 is only
`0.153846`. The post-feedback relation file-concordance F1 `0.417391` is also
not formal IAA and exposes weak `PART_OF` agreement (`0.246154`). F4a remains
dev-only: E-prime improves dev NER/RE F1 while E lowers both. F4b remains
tune-only: E-prime is negative and E's slight gain misses the deletion-audit
threshold. Broad public/cross-domain generalization and positive CoVe remain
unsupported.
The focused CLUENER block has 12/12 completed, v2-validated, backed-up, and
locally mirrored cells. Its separate RTC is `partial`, confidence `high`:
`B-A` F1 is `+0.085445`; `C-B` F1 is `+0.003557`; `D-C` F1 is `-0.004097`
with precision `+0.009832` and FP `-95`. This is limited descriptive
portability to one additional Chinese NER benchmark, not broad generalization.

**Paper consequence at that breakpoint**: F7 supports the paper's reproducibility and
limitation discussion by proving that the frozen two-stage IE pipeline produces
auditable final cells and by supplying honest failure analysis. It does not
improve the headline result: exact RE remains
weak, D does not beat C, and `HAS_METRIC` has no TP. Keep the three-seed NER
result as the primary contribution and treat RE as an exploratory negative
result/limitation. CLUENER was later added only as a focused external-benchmark
replication, with labeled-dev-as-final, schema-specific resource, small C-B
delta, no public paired uncertainty, and no broad-generalization caveats intact.
The manuscript target is the complete
`docs/JISE_OVERLEAF_LATEX_20260729/` project, not a Markdown draft and not only
its `main.tex` entry file. That propagation is now complete; no further
manuscript edit is currently authorized.

**Current breakpoint**: F1, F2, F3, F4a DDEV1/DDEV2, F4b CDEV1/CDEV2, F5,
F6, and F7 Domain Batch 1 are complete. IE021, the initial F6 no-card memory
stop, F4a strict v0 A failure, and F7 v1 finalization failure remain preserved.
F7 completed four A/B/C/D K=5 seed42 cells, changing accounting to `4/60`:
four complete domain cells, eight remaining Stage N-only domain cells, and 48
wholly absent cells. The batch has `10/680 = 1.470588%` relation parse failures,
zero unsupported types/type-matrix violations, and 1,840 retained invalid-unit
sanitizer events. The paid observation envelope was about 2,463 seconds, or
approximately `1.916 CNY` at `2.8 CNY/hour`; platform billing is authoritative.
The 713-file remote backup and 17 directly mirrored lightweight results passed
hash verification. Current SSH is no-card: `No devices found`, 2 GiB cgroup,
about 59 GB free, no model/F7 process, and only the preserved dead F6 screen.
The public-NER block is `12/12` closed. The v2 report SHA256 is
`7a1f1f110e9fea8f6a92398f5e3e25bd109b7e04cb7664664a7d99572bb62824`;
the clean tracked suite passed `205/205`; the complete remote backup manifest
contains `18,239/18,239` verified entries with SHA256
`db75f2f27a8063c0660f7a773456dc8d7db6bfa57a733e14f1f3ff0e8125294e`;
and the 63-file local mirror archive SHA256 is
`daf54146a8c876b08d482ab86f3e72c52d505367bd7f5e30cf24c1f5aad3c996`.
The instance is in no-card mode with a 2 GiB cgroup and no model or runner
process. The focused public-NER RTC itself changed no result or manuscript
file. The later paper-only gate changed only approved LaTeX sources and is
closed in commits `8189f71` and `8f1f3e1`.

**Next step at this historical breakpoint**: stop and wait for
`NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED`. That gate was later
consumed. The current next plan is the paper-only metadata, compilation, PDF,
and venue-format audit described in the authoritative snapshot; it remains
separate from experiments, DOCX, submission, and GitHub synchronization.

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
  accounting remained `0/60`; F7 later received its own bounded gate, while
  F8/F9 and paper work still require new gates.
- Full recovery report:
  `docs/FULL_IE_F6_CLUENER_REPLAY_RECOVERY_20260803.md`.

### F7 Domain Final Batch 1 Closeout

Completed on 2026-08-04 under the consumed
`FULL_IE_DOMAIN_FINAL_BATCH_APPROVED` gate.

- Exact scope stayed `domain:A/B/C/D:k5:s42`, Stage R only over four locked
  170-row P5 Stage N sources. Stage N, E/E-prime, other seeds, and K scans were
  not run.
- The batch contract SHA256 remains
  `0369400022ba15319b54f72def1ad0feb65ec63d0a297eacc6f28f04d2cb9973`;
  the execution manifest SHA256 remains
  `893d79bcba8e5394208de28a0770cd2b9909c4d0361b0dc9015c726355e611b1`.
- A/B/C/D NER F1 is `0.530990/0.554662/0.569302/0.565764`; exact RE F1 is
  `0.040541/0.056972/0.057971/0.045381`. Relation TP/FP/FN is
  `15/298/412`, `19/221/408`, `20/243/407`, and `14/176/413`.
- `B-A` gives a weak RE signal, `C-B` is effectively tied, and `D-C` is
  negative. D has fewer absolute relation FP than C but lower precision after
  losing TP. All four cells have zero `HAS_METRIC` TP.
- The 680-row audit has 647 model requests, 52 deterministic skips, 19 retries,
  `10/680 = 1.470588%` relation parse failures, zero unsupported types or
  type-matrix violations, and 1,840 preserved invalid-unit sanitizer events.
- The first batch-finalization attempt failed after all cells completed with
  `AttributeError: 'str' object has no attribute 'open'`. The failure log SHA256
  is `4c9760f09324bbcac63e1b5cbb5477300d33db9bcd43125b7b5f187ac33ca4b6`.
  Locked v1 files/results were not changed. The versioned v2 Path conversion
  repair made zero model calls; focused F7 tests passed `5/5` and the complete
  remote suite passed `200/200`.
- The final batch report SHA256 is
  `6862964e4fae61cff46f284fe3b42378a97cee637e44c173570b8851ee898934`.
  It is `COMPLETE`, preserves negative results, and sets accounting to `4/60`.
- Observable paid time was about 2,463 seconds, approximately `1.916 CNY` at
  `2.8 CNY/hour`; the platform bill is authoritative. vLLM was stopped.
- The 713-file remote backup passed `713/713`; archive SHA256 is
  `0de4bc5b5cd4fe50015dcffe76c288961be05d234a4f16c7492c23916779159c`.
  The archive, manifest, and 17 hash-matched lightweight result files are under
  `D:\yinsir\backups\FULL_IE\f7_domain_batch1_20260804\`.
- Final AutoDL state is no-card (`No devices found`), 2 GiB cgroup, about 59 GB
  free, no model/F7 process, and only the preserved dead F6 screen.
- Reports: `docs/FULL_IE_F7_DOMAIN_BATCH1_PREPARATION_20260803.md`,
  `docs/FULL_IE_F7_DOMAIN_BATCH1_EXECUTION_CHECKPOINT_20260803.md`, and
  `docs/FULL_IE_F7_DOMAIN_BATCH1_CLOSEOUT_20260804.md`.
- The four cells are single-seed evidence. No aggregate/significance, positive
  full-IE, positive RE, or RAG-for-RE claim is authorized.

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

The full experiment route is frozen. The exact public-NER exception is
consumed and closed: 12 labeled-dev CLUENER A/B/C/D, K=5, seeds42/43/44 NER
cells passed validation, backup, and mirroring. Literal accounting is `16/60`;
the other 44 identities are not an active backlog. No GPU or experiment gate is
live. The focused public RTC is consumed at `partial`, confidence `high`, and
supports only limited descriptive portability to one additional Chinese NER
benchmark. The later paper-only LaTeX propagation gate is also consumed in
commits `8189f71` and `8f1f3e1`. The paper remains SCI-Q4-oriented and
NER-primary, with RE reported only as an exploratory negative result/limitation.
No further manuscript body change is authorized without a new exact gate.

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

Historical accounting at the IE022 closeout (superseded by F7 and the route
freeze below):

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

Active manuscript and historical paper artifacts:

- `docs/JISE_OVERLEAF_LATEX_20260729/` (official-template LaTeX/Overleaf
  project and the sole active manuscript; `main.tex` is the Overleaf entry
  point, while `frontmatter.tex` and `sections/*.tex` contain the paper; the
  human-reported clean-looking compile predates the current evidence/framework
  commits, and the current version still lacks local compile-log/PDF proof);

- `docs/JISE_OVERLEAF_LATEX_20260729.zip` (historical upload-ready archive;
  regenerate only under a later exact paper/packaging gate);

- `docs/JISE_SUBMISSION_PACKAGE_20260728/` (historical JISE Markdown staging
  package; reference only, not the active manuscript branch);

- docs/JISE_ENGLISH_MANUSCRIPT_DRAFT_V1_20260728.md (JISE-oriented English
  historical Markdown draft; reference only);

- `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`
  (historical Markdown draft; reference only).

The human selected JISE and completed the bounded English-Markdown, Markdown
submission-package, and LaTeX conversion gates. The LaTeX project is now the
active manuscript; the Markdown packages remain provenance/reference only and
must not be treated as the paper refinement target.
Before any eventual submission, the author still needs
an institution-level JCR check for the exact journal title/ISSN, including JCR
year, category, rank, quartile, and the institution's quartile rule, plus the
author/declaration and journal-policy confirmations recorded in the package.
The approved LaTeX/template-conversion gate is now consumed. The current work
does not authorize DOCX conversion, actual journal submission, implementation,
or any new experiment. Do not edit the manuscript to describe full IE until
verified results exist. Overleaf compilation and visual proofing are permitted
within the prior gate, but uploading the resulting PDF to JISE is not.

All generated `.docx` files were deleted on 2026-07-25 at the user's request
because of rendering/encoding problems. Future manuscript writing defaults to
the complete UTF-8 LaTeX project above, not Markdown or DOCX.

The F7 Domain Batch 1 model-call gate was consumed by the completed
`domain:A/B/C/D:k5:s42` Stage R batch. Its locked execution package and four
final cells are retained, and the versioned v1 finalization failure plus v2
no-model repair are disclosed. The exact 12-cell CLUENER public-NER amendment
is also consumed, closed, and followed by a completed bounded RTC. No model-call
gate is open. Returned-file correction, reannotation, frozen-data correction,
full aggregation, baseline runs, K scans, E/E-prime, RE, domain reruns, and all
other experiments remain closed. IE051 is historical `CLOSED`, was not
executed, and must not be described as failed or blocked. The
fresh entity annotation/validation, M1, M2, full-IE F1, F2, F3, F4a, F4b, F5,
F6 initial/recovery, and F7 Batch 1 gates are consumed. The later exact LaTeX
propagation gate was also consumed; the approved manuscript changes are in
`8189f71` and `8f1f3e1`, and no further manuscript edit is authorized.

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
> demonstrations and glossary injection show observed entity-extraction
> F1/recall improvements, while RAG evidence preserves near-tied F1 and improves
> precision / reduces false-positive entity predictions.

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

F7 adds auxiliary engineering evidence: four locked Stage N+R final cells are
reproducible and auditable down to prompt/cache/raw/per-query records, hashes,
parser events, failure repair, and verified backup. It does not add a positive
RE contribution. Exact RE F1 is only
`0.040541/0.056972/0.057971/0.045381`, D is below C, and every cell has zero
`HAS_METRIC` TP.

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
- RAG-for-RE improvement;
- CoVe/self-verification improvement;
- a usable `HAS_METRIC` relation extractor;
- public benchmark generalization;
- K=1/K=10 robustness;
- full A..E-prime ablation matrix;
- complete information extraction;
- supervised-SOTA-style claims;
- any claim that C significantly beats D.

Historical full-IE target, **closed and not a current claim or backlog**:

- reproducible two-stage domain NER+RE with exact directed relation metrics;
- complete A/B/C/D/E/E-prime K=5 comparisons and pre-specified A/E K scans;
- relation-aware CoVe evaluated as a potentially positive or negative ablation;
- public NER portability on the complete labeled CLUENER dev split; and
- paired uncertainty and result-to-claim analysis over the complete inventory.

The human stopped this extension at `4/60`. The missing evidence remains a
limitation, not an instruction to complete rows. The current `partial` verdict
and narrow NER wording control every paper-facing statement.

Paper positioning:

- Main demonstrated contribution: low-label Chinese equipment-domain NER.
- RE position: exploratory negative result/limitation, with F7 retained as
  reproducibility and audit evidence only.
- Contribution style: applied/reproducible engineering pipeline plus small
  equipment-domain dataset and honest ablation evidence.
- Target: one-month SCI-Q4-oriented manuscript route, Chinese draft first and
  then English SCI manuscript.

## 4. Current Paper And Review Artifacts

Use these as the paper-facing evidence base:

- `docs/RESULT_TO_CLAIM_F7_NER_FALLBACK_ROUTE_FREEZE_20260804.md` (latest
  claim hierarchy and route decision)
- `docs/FULL_IE_F7_DOMAIN_BATCH1_CLOSEOUT_20260804.md` (F7 evidence and audit
  provenance)
- `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_PLAN_20260730.md` (planning only;
  historical full-IE scope and gates, not paper evidence)
- `refine-logs/FULL_IE_MINIMUM_EXPERIMENT_TRACKER_20260730.md` (live cell
  inventory, route-closed status, and accounting; not experimental evidence)

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
  CoVe, broad public/cross-domain generalization, or the entire A..E-prime
  matrix passed.
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
- F7 Domain Batch 1 closeout commit:
  `f03c1b8 full-ie: close F7 domain batch 1`.
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
- F7 uses another isolated workspace at
  `/root/autodl-tmp/full_ie/f7_domain_batch1_20260803/workspace`; compatibility
  views are under the sibling `inputs_v1` directory. It does not overwrite the
  dirty `/root/project` worktree.
- Current SSH succeeds in no-card mode: `No devices found`, cgroup
  `memory.max=2147483648`, about 59 GB free on `/root/autodl-tmp`, no active
  model/F7 process, and only the preserved historical dead screen. F7 paid
  inference is complete and vLLM is stopped.
- The complete F7 backup is under
  `/root/autodl-tmp/backup/full_ie/f7_domain_batch1_20260804/`; its 713-file
  manifest and archive were verified and mirrored locally under
  `D:\yinsir\backups\FULL_IE\f7_domain_batch1_20260804\`.
- The complete F4b backup remains under
  `/root/autodl-tmp/backup/full_ie/f4b_cluener_tune_20260802/`.

Useful no-Python status command:

```bash
ssh autodl-paper 'cd /root/project && git rev-parse --short HEAD && git status --short && (nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader 2>/dev/null || echo GPU_FREE_OR_NVIDIA_SMI_UNAVAILABLE)'
```

## 7. Current Stop And Next Paper Gate

The human route decision is complete under the consumed
`FULL_IE_STOP_AND_NER_FALLBACK_RTC_APPROVED` gate. The result-to-claim verdict
remains `partial` with high confidence after the focused public evidence review.
The original completion route stopped at `4/60`; the consumed public-NER
exception raises literal accounting to `16/60` without reopening the other 44
identities. The paper route remains NER as the main contribution, with RE only
as an exploratory negative result/limitation.

### Current state: focused public-NER closeout and RTC complete

F1-F6 and F7 Domain Batch 1 remain complete and preserved. IE021, the initial
F6 no-card resource stop, the F4a strict-v0 failure, and the F7 v1 finalizer
failure remain part of the audit trail. Exact RE is weak
(`0.040541/0.056972/0.057971/0.045381`), D is below C, and all four final cells
have zero `HAS_METRIC` TP. The relation file-concordance F1 is `0.417391`, with
`PART_OF=0.246154`; neither is formal IAA. F4a/F4b remain dev/tune sanity only.

The focused public block is complete for A/B/C/D K=5 seeds42/43/44 over all
1,343 labeled official CLUENER dev rows. Validation, clean tracked tests,
complete backup, local mirror, and cost closeout passed. The exact record is
`docs/NER_PUBLIC_CLUENER_ABCD_K5_FINAL_CLOSEOUT_20260806.md`.

The separate `NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED` gate is consumed with
verdict `partial`, confidence `high`. CLUENER `B-A` F1 is `+0.085445`, `C-B`
is `+0.003557`, and `D-C` is `-0.004097` with precision `+0.009832` and FP
`-95`. This supports limited descriptive portability to one additional Chinese
NER benchmark and reproduces the RAG precision/FP operating point. It does not
support broad public/cross-domain generalization, significance, SOTA, K
robustness, RE, CoVe, or complete IE. The exact record is
`docs/RESULT_TO_CLAIM_NER_PUBLIC_CLUENER_ABCD_K5_20260806.md`.

AutoDL is in no-card mode with no vLLM/Qwen/runner process. No paid GPU or
experiment gate is live. Do not start a model or issue any new request.

### Closed experiment route and sole exception

- IE051 is retained as a historical proposal with status `CLOSED`. Its eight
  Stage R cells were never attempted; the closure is an intentional human
  route choice, not a failed run, blocked run, or negative empirical result.
- E/E-prime, K scans, RE/Stage R, domain reruns, and all remaining matrix cells
  are also `CLOSED` and must not be prepared, executed, or aggregated.
- The sole 12-cell CLUENER A/B/C/D K=5 seed42/43/44 NER exception is consumed
  and `DONE`. It did not reopen F8 as a whole.
- The 8 Stage N-only cells and 36 absent cells stay visible in literal matrix
  accounting. These 44 incomplete identities are limitations and historical
  protocol records, not an active backlog.
- Any further reopening requires an explicit human route change plus a new
  exact bounded execution gate. A historical token or tracker row provides no
  authority.

### Post-run claim and paper sequence

The 12-cell closeout, RTC, exact LaTeX propagation gate, bounded EC-FSIE
final-refinement gate, first Overleaf PDF audit, and post-audit source refinement
are complete. The
active target was and remains the complete
`docs/JISE_OVERLEAF_LATEX_20260729/` project: `main.tex` is the entry point,
while `frontmatter.tex` and `sections/*.tex` contain the manuscript. Commits
`8189f71` and `8f1f3e1` record the authorized propagation and framework
positioning; the later refinements unify the same EC-FSIE terminology and claim
boundary without changing locked results. The metadata/compile gate was granted;
metadata was deferred, the first PDF was audited, and the refined source now
requires a second human-run Overleaf compilation. That recompilation does not
authorize new experiments, result recomputation, DOCX generation, submission,
or GitHub synchronization.

The original pre-F7 `125-295 CNY` estimate remains historical planning context,
not a current remaining-cost estimate. The focused public block's three vLLM
log envelopes total 16,124.062 seconds (4.478906 hours), approximately
`12.541 CNY` at `2.8 CNY/hour`. This excludes card-on overhead outside the log
envelopes; the live platform bill controls. No remaining GPU work is authorized.

### Full-matrix accounting

- original contract: 60 reported cells = 30 domain + 30 CLUENER;
- complete: four domain A/B/C/D K=5 seed42 cells with Stage N plus Stage R and
  12 CLUENER A/B/C/D K=5 three-seed NER cells (`16/60` total);
- partial: eight domain A/B/C/D K=5 seed43/44 cells with Stage N only;
- wholly absent: 36 reported cells; total incomplete cells are `44/60`, and all
  remain route-closed;
- historical completion would have required Stage R for 26 of 30 domain cells,
  with new Stage N for 18 of them; that is no longer an active work plan;
- F4b adds six tune-sanity rows only, not reported cells;
- F5 freezes all 60 report identities and validates the 12 reuse artifacts, but
  adds no Stage R, verifier, CLUENER-final, or complete-cell result;
- F6 prepares the shared 170-row domain and 1,343-row CLUENER replay
  dependencies but no Stage N/R, verifier, CLUENER-final, or complete-cell
  result;
- F7 Batch 1 contributes four independently validated complete cells and moves
  literal accounting to `4/60`; it does not create three-seed aggregates;
- NPUB01 contributes 12 independently validated CLUENER NER cells and moves
  literal accounting to `16/60`; RTC02 interprets it only as limited,
  descriptive one-benchmark portability;
- CLUENER official unlabeled test is never offline gold. The complete 1,343-row
  labeled-dev protocol is the only authorized public final evaluation;
- E v1/v2 remain preserved negative/mixed historical NER dev evidence. F4a now
  adds relation-aware dev runs: E-prime is locally positive and E is negative.
  F4b CLUENER tune reverses that pattern: E-prime lowers F1, while E is only
  slightly positive and misses the deletion-audit threshold. None is a final
  matrix cell.

Complete-cell accounting is `16/60`, leaving eight Stage N-only cells and 36
wholly absent cells. The other 44 incomplete identities stay closed.

The JISE author/JCR/fee/AI-policy/template blockers remain valid. The immediate
next human action is to provide verified author/affiliation/disclosure inputs;
after that, approve a new exact paper-only metadata/compile gate. No GPU is
needed. Actual journal submission remains unauthorized.

## 8. Lessons Worth Remembering

- A human gate and a running resource are separate facts. F4b started only
  after both its bounded approval and a clean RTX 4090 preflight existed; its
  later no-card state means the run is stopped, not still authorized.
- Prepared F3 configs are hash-locked provenance. For an approved run, create a
  dated execution copy with the gate record and output paths; do not overwrite
  the prepared originals merely to flip `authorized/model_calls_allowed`.
- The human stopped the full-IE extension at `4/60` and selected the NER-primary
  route. RE remains an exploratory negative result/limitation, not a headline
  contribution.
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
- The uncompleted 60-cell protocol remains visible for honest accounting, but
  the human closed it as an execution route. Its missing rows cannot be treated
  as completed evidence, failed experiments, or a pending requirement.
- The 12 frozen A/B/C/D K=5 outputs remain hash-locked. Four seed42 cells have
  final Stage R and count as `4/60`; the eight seed43/44 Stage N-only files are
  preserved historical partial cells, not authority or a recommendation to run
  IE051.
- F7 shows that a complete, audited final cell is not automatically a positive
  result. A/B/C/D exact RE F1 remains weak, D does not beat C, and every cell has
  zero `HAS_METRIC` TP. Matrix progress and contribution support are separate
  facts.
- Post-inference bookkeeping can fail after valid model outputs. Preserve the
  failed finalizer log and locked outputs, make the smallest versioned no-model
  repair, regression-test it, and never overwrite the original execution lock.
- Paid cost must use the observable GPU envelope, not only summed runner time.
  F7 used 1,198.505 runner seconds inside an approximately 2,463-second paid
  envelope; startup, validation, repair, shutdown, and backup overhead matter.
- AutoDL no-card mode may have tight memory limits. Avoid loading BGE-M3 unless
  needed; prefer cached/replay artifacts when they preserve comparisons.
- DOCX output caused encoding/rendering trouble in this workflow. Use the
  complete `docs/JISE_OVERLEAF_LATEX_20260729/` project as the working
  manuscript; `main.tex` is only its Overleaf entry point. Keep Markdown drafts
  as historical references.
- The historical Chinese/English drafts, JISE Markdown package, and active
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
- Full-matrix completion is closed by explicit human decision. The focused
  12-cell public-NER exception, its RTC, and exact LaTeX propagation are all
  consumed. The later `JISE_ECFSIE_LATEX_FINAL_REFINEMENT_APPROVED` gate is also
  consumed. The next useful gate is
  `JISE_ECFSIE_METADATA_COMPILE_PDF_AUDIT_APPROVED` gate was subsequently
  granted; metadata was deferred, the first PDF audit passed compilation, and
  post-audit source refinements now await Overleaf recompilation. No GPU or
  submission authority is implied.
