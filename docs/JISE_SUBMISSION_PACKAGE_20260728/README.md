# JISE Submission Package (Markdown Staging Version)

Date: 2026-07-28

Target: *Journal of Information Science and Engineering* (JISE)

Source manuscript: `docs/JISE_ENGLISH_MANUSCRIPT_DRAFT_V1_20260728.md` at commit `fea7c43`

## Package Status

This directory is a GPU-free, UTF-8 Markdown staging package. It contains the
paper text and copy-ready submission materials, but it is **not yet safe to
submit**. Every `[[...]]` placeholder must be resolved by the authors. JISE's
submission system requires a PDF in the journal format; no PDF, DOCX, or LaTeX
file was produced under the present authorization.

The package preserves the current evidence boundary:

- frozen split: support 30, development 50, and test 170;
- completed final experiment scope: domain NER only, A/B/C/D, K = 5, seeds
  42/43/44, totaling 12 run units;
- C and D are near-tied in F1; C is marginally higher in recall/F1, whereas D
  has higher precision and 55.0 fewer false-positive entities on average;
- fresh two-human calibration: 20 previously unused non-test passages,
  175/220 entities, 158 exact span-plus-type matches, micro-F1 0.800000;
- the original threshold of at least 0.80 was met exactly, the later 0.85 target
  was not met, this is not frozen-test formal IAA, and TECH_SCHEME F1 is
  0.153846;
- no positive claim is made about relation extraction, CoVe/self-verification,
  public-benchmark generalization, K scans, statistical significance, or a
  complete ablation matrix.

## Files

1. `01_JISE_MANUSCRIPT_SUBMISSION_MARKDOWN.md` — JISE-oriented manuscript text
   with author/declaration placeholders and an explicit AI-tools disclosure.
2. `02_COVER_LETTER_DRAFT.md` — evidence-bounded cover-letter draft.
3. `03_SUBMISSION_METADATA_AND_AUTHOR_FORM.md` — copy-ready title, abstract,
   keywords, author-order fields, and submission-system entries.
4. `04_DECLARATIONS_AND_AI_DISCLOSURE.md` — approved AI wording plus selectable
   funding, conflict, data, code, ethics, and author-contribution statements.
5. `05_EDITOR_SELECTION.md` — two primary Associate Editor choices, alternates,
   fit rationale, and mandatory conflict checks.
6. `06_PRE_SUBMISSION_CHECKLIST.md` — official JISE requirements, unresolved
   author-only gates, and final package checks.
7. `07_EDITORIAL_OFFICE_QUERY_DRAFT.md` — author-sendable request to clarify
   length, fees, and the disclosed AI-assisted workflow.

## Official Requirements Used

The following official pages were checked on 2026-07-28:

- submission and AI policy:
  <https://jise.iis.sinica.edu.tw/pages/authors/index.html>;
- online submission instructions:
  <https://jise.iis.sinica.edu.tw/pages/authors/submission.html>;
- manuscript files, template, length, copyright, and PDF requirement:
  <https://jise.iis.sinica.edu.tw/pages/authors/manuscripts.html>;
- title, abstract, keywords, references, figures, tables, equations, and program
  formatting:
  <https://jise.iis.sinica.edu.tw/pages/authors/preparation.html>;
- current Associate Editor list:
  <https://journal.iis.sinica.edu.tw/jise_aelist.html>.

The website contains a material length ambiguity. The submission-policy page
says papers may be up to 12 JISE Word-template pages and charges USD 100 per
page beyond that limit. The manuscript page says regular manuscripts should be
within 25 pages, short papers within 15 pages, and again states that pages over
12 incur USD 100 each after acceptance. The conservative package target is
therefore no more than 12 formatted pages, but the authors must obtain written
confirmation of the operative length and all fees before submission.

## Human Completion Order

1. Confirm JISE's current institution-recognized JCR year, category, rank, and
   quartile for ISSN 1016-2364.
2. Fill and verify all author names, affiliations, postal addresses, emails,
   ORCIDs, contribution roles, corresponding-author details, and author order.
3. Select the final funding, conflict-of-interest, data/code-availability, and
   ethics statements in file 04.
4. Check conflicts for the two proposed Associate Editors and replace either
   choice with an alternate if necessary.
5. Ask JISE to confirm current regular-paper length, page charges, any other
   publication charges, and the acceptability of the fully disclosed
   human-reviewed AI-assisted annotation-proposal workflow.
6. Under a separately approved formatting gate, transfer the final text into
   the current JISE template, confirm a formatted length of at most 12 pages if
   possible, generate the required PDF, and perform a visual proofread.
7. Complete every checkbox in file 06 before uploading anything.

This package was produced in the present OpenAI Codex writing session. No
project inference model, external LLM/API, secondary reviewer agent,
frozen-test access, local Python, GPU, or vLLM was invoked.
