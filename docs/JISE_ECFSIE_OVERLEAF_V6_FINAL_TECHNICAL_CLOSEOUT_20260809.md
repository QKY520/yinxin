# JISE EC-FSIE Overleaf V6 Final Technical Closeout

Date: 2026-08-09

Workspace: `D:\yinsir`

Status: **MANUSCRIPT BODY TECHNICALLY SEALED; HUMAN METADATA PENDING**

## 1. What Task We Are Doing

The project studies reproducible few-shot Chinese equipment-domain information
extraction. The final paper route is deliberately narrower than the original
full-IE plan: named entity recognition (NER) is the main supported contribution,
while relation extraction (RE) is retained only as an exploratory negative
result and limitation.

The active manuscript presents the method as the Evidence-Controlled Few-Shot
Information Extraction (`EC-FSIE`) framework. It emphasizes bounded evidence
channels, reproducible execution, low-label applicability, kNN demonstrations,
schema-specific lexicons, and reranked RAG evidence. The active paper is the
complete LaTeX project under `docs/JISE_OVERLEAF_LATEX_20260729/`; historical
Markdown drafts are reference artifacts only.

This closeout records the end of the paper-body refinement and Overleaf
compilation/visual-audit sequence. It does not authorize submission, metadata
invention, a new experiment, GitHub synchronization, or any change to locked
results.

## 2. Authoritative Final Artifacts

- Active LaTeX project: `docs/JISE_OVERLEAF_LATEX_20260729/`
- Overleaf entry point: `docs/JISE_OVERLEAF_LATEX_20260729/main.tex`
- Final source commit: `1c48d1d docs: merge EC-FSIE Method paragraph for pagination`
- Audited V6 PDF: `docs/JISE_OVERLEAF_LATEX_20260729__6_.pdf`
- V6 PDF size: `173669` bytes
- V6 PDF SHA256:
  `5364210C67F89EB1B347E981AB26B6A62F12D0BD3994924AFD60F8D64DD9BCBC`
- Audited V6 Overleaf output ZIP:
  `docs/JISE_OVERLEAF_LATEX_20260729__6_-output.zip`
- V6 output ZIP size: `240660` bytes
- V6 output ZIP SHA256:
  `04E3A6861CF0BCC7EC9233DEAA43B927A2874808CCA21C217B299BB9BF39B637`

The PDF is retained as a local human-supplied artifact and is not part of the
tracked manuscript-source commit. The output ZIP is ignored by Git. Do not add
either artifact to a commit unless the human explicitly changes that policy.

## 3. What Is Complete

### 3.1 Experiment and evidence route

- P0-P6, full-IE F1-F6, F7 Domain Final Batch 1, the focused 12-cell CLUENER
  block, both result-to-claim reviews, validation, backups, and machine closeout
  are complete.
- Literal matrix accounting is `16/60`: four domain Stage-N+Stage-R cells and
  twelve CLUENER NER cells are complete. The other 44 identities are
  intentionally route-closed, not an active backlog and not failed experiments.
- AutoDL was last verified in no-card mode with vLLM, Qwen, and all runners
  stopped. No GPU or experiment gate is live.

### 3.2 Paper refinement route

- Verified domain and CLUENER evidence was propagated into the complete LaTeX
  project.
- The title, abstract, introduction, Related Work, framework definition,
  experimental setup, results, discussion, limitations, conclusion, disclosure,
  bibliography, architecture figure, qualitative cases, and claim--evidence map
  were refined without changing locked experimental results.
- EC-FSIE terminology and the result-to-claim boundary are consistent across the
  manuscript.
- Six human-run Overleaf PDF/log rounds were audited. Early rounds found and
  repaired metadata gaps, an architecture-node overflow, a disclosure mismatch,
  contribution/page-edge layout defects, and three pagination artifacts.
- V4 fixed the Results `numer-/ically` split and the isolated Conclusion `gain.`.
  V5 showed that shortening a tail sentence could merely move a hyphenated
  fragment (`gen-/eration.`) to the next page. V6 merged the evidence-control
  statement into the preceding retrieval sentence and removed the page-top
  fragment structurally.

## 4. Final V6 Compilation And PDF Audit

The exact read-only gate
`JISE_ECFSIE_OVERLEAF_V6_COMPILE_PDF_FINAL_CONFIRMATION_APPROVED` is consumed.

| Check | V6 result |
| --- | --- |
| Total pages | 19 |
| Page geometry | 19 identical A4 MediaBoxes (`595.276 x 841.89` pt) |
| LaTeX errors | 0 |
| Undefined citations | 0 |
| Undefined references | 0 |
| BibTeX warnings | 0 |
| Rerun requests | 0 |
| Overfull hbox/vbox | 0 / 0 |
| Underfull hbox/vbox | 9 / 4; no visible defect |
| ChkTeX | exit 0; no errors or warnings printed |
| qpdf post-processing | exit 0 |
| Labels | 11 |
| Citation occurrences | 37 |
| Unique cited/BibTeX keys | 27 / 27 |
| Encryption | none |

PDF metadata is correct for Title, Subject, and Keywords. The PDF Author entry
is intentionally unset because the human deferred author information. The
pdfTeX log lists all used Times, Courier, Symbol, and Computer Modern Type1
`.pfb` files as written into the PDF. This is strong embedding evidence, but the
Windows control workspace lacks `pdffonts`, so independent font enumeration has
not been claimed.

All 19 pages were rendered and visually inspected. The final page flow is:

- page 8 ends cleanly with `Embedding and reranking use the locked CPU path.`;
- page 9 begins directly with the complete `For CLUENER...` paragraph;
- the Results `numer-/ically`, Conclusion `gain.`, Method `post-hoc filter.`,
  and Method `eration.` fragments are absent;
- the architecture figure, all tables, disclosure text, and all 27 references
  render without clipping, overflow, blank pages, or missing content;
- Conclusion spans pages 15--16 and References occupy pages 17--19.

Verdict: **the manuscript body passes compilation and visual audit and is
technically sealed.** It is not yet submission-ready because human-owned fields
remain visible placeholders.

## 5. Current Claim Boundary

### Supported claims

- In frozen low-label Chinese equipment-domain NER, kNN demonstration selection
  and the domain lexicon improve observed F1/recall.
- RAG preserves near-tied F1 while increasing precision and reducing
  entity-level false-positive predictions; its supported value is a
  precision-oriented operating-point shift, not an F1 gain.
- The 1,343-row labeled official CLUENER development block provides limited,
  descriptive directional replication on one additional Chinese NER benchmark.
- Frozen resources, hashes, trace artifacts, replay identifiers, and bounded
  evidence channels support reproducibility of the evaluated pipeline.

### Unsupported or prohibited claims

Do not claim statistical significance, SOTA, superiority to supervised
baselines, broad public or cross-domain generalization, positive RE,
RAG-for-RE, CoVe gains, usable `HAS_METRIC`, K robustness, frozen-test formal
IAA, high-quality relation annotation, a complete 60-cell matrix, complete
F8/F9, or complete end-to-end IE success. Do not describe CLUENER as more than
one additional Chinese NER benchmark, and do not describe entity-level FP
reduction as hallucination elimination or a general factuality result.

## 6. What Remains Unresolved

The human explicitly deferred these fields; no agent may invent them:

- author names and order;
- short author list/running author header;
- affiliations and addresses;
- corresponding author and email;
- non-AI acknowledgments, or a verified decision that none are needed;
- funding statement;
- conflict-of-interest statement;
- data-availability statement and any stable repository/DOI;
- code-availability statement and any archived release;
- institution-specific ethics determination;
- verified CRediT roles.

The template's volume, issue, year, DOI, and other publisher-owned header fields
also require target-journal instructions; they must not be guessed. Submission
portal metadata, cover letter, current JISE author guidelines, fee/APC status,
and current AI-disclosure policy still require human/venue confirmation.

## 7. Current Stop And Next Plan

No gate is live after this closeout. Stop here.

When the human is ready, the next bounded paper-only step should be human
metadata insertion. A suggested exact gate is
`JISE_ECFSIE_HUMAN_METADATA_FINALIZATION_APPROVED`, with a precise writable-file
list such as `frontmatter.tex`, `sections/10_disclosures.tex`, `main.tex` only if
PDF Author metadata must be set, `HANDOFF.md`, and this closeout or a new dated
metadata closeout. The human must supply or approve every value before editing.

After metadata insertion:

1. the human recompiles the complete project in Overleaf with `main.tex` as root;
2. the PDF and output ZIP/log are retained locally;
3. a new read-only audit rechecks compilation, first-page layout, headers,
   pagination, metadata, fonts, disclosures, references, and all placeholders;
4. submission, cover-letter finalization, external upload, and GitHub sync each
   remain separately gated actions.

No new experiment, GPU use, result recomputation, paper-body refinement, or
claim expansion is recommended or authorized.

## 8. Experience Worth Preserving

- Static LaTeX checks and a successful compile are necessary but do not prove
  visual quality. Inspect the actual human-returned PDF and log together.
- A tiny wording change can shift a page break without eliminating the defect.
  V4 and V5 demonstrated that shortening a tail sentence may leave a different
  fragment. Merging the idea into the preceding sentence removed an entire
  rendered line and was the robust repair.
- Do not use layout commands or global penalties before trying a semantically
  equivalent local rewrite; template-level layout changes can have wider effects.
- Keep result numbers, tables, negative evidence, limitations, and citation keys
  invariant during paper-only refinement. V6 changed no numeric token.
- Human metadata can reflow the first page and downstream pagination. A PDF that
  is technically sealed before metadata still requires one final visual audit
  after metadata is inserted.
- Never fabricate author, affiliation, funding, conflict, ethics, repository,
  DOI, acknowledgment, or CRediT information.
- Preserve failed compilation/finalization history and negative experiments;
  honest boundary reporting is part of EC-FSIE's reproducibility contribution.
- The main positive paper story is NER. RE remains an exploratory negative
  boundary, and CLUENER remains a limited one-benchmark directional replication.
- Windows remains a control/documentation workspace. Never run project Python
  locally, and never restart experiments merely to polish the manuscript.

## 9. Repository And Safety Boundary

The authoritative manuscript-body source commit is `1c48d1d`; a later
documentation-only handoff commit may advance repository HEAD without changing
that source. The local branch is ahead of `origin/main`; do not push, pull,
fetch, or otherwise synchronize unless the human explicitly asks. Preserve the
pre-existing deleted historical JISE Markdown-package files and all user-owned
untracked P6, M1/M2, old-plan, script, and attachment artifacts. Do not read,
restore, stage, commit, clean, reset, or delete them as part of a paper-metadata
step.

No GPU cost was incurred by the V1--V6 paper refinement and PDF-audit sequence.
