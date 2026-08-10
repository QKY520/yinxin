# EC-FSIE Manuscript Compression Closeout

Date: 2026-08-10

## 1. Gate And Scope

The human approved the bounded paper-only gate
`JISE_ECFSIE_MANUSCRIPT_COMPRESSION_APPROVED` to reduce the active JISE
manuscript from the verified 19-page V6 baseline toward a 13--14-page main PDF.
The pass was limited to:

- `docs/JISE_OVERLEAF_LATEX_20260729/sections/00_abstract.tex` through
  `sections/09_conclusion.tex`;
- one new standalone supplement,
  `docs/JISE_OVERLEAF_LATEX_20260729/supplementary_tables.tex`;
- this closeout and `HANDOFF.md`.

No experiment, model call, Python execution, AutoDL action, data edit, result
recomputation, author metadata, submission action, or GitHub synchronization
was authorized or performed. Existing untracked files and protected historical
deletions were not read, staged, or changed.

## 2. Source Outcome

The compressed manuscript source is commit `fc8512a` (`docs: compress EC-FSIE
manuscript and split supplement`). Relative to the final V6 body source at
`1c48d1d`:

- the ten main section files decreased from 48,843 to 24,114 bytes, a 50.6%
  source-size reduction;
- main-text tables decreased from ten to three;
- the retained main floats are the architecture figure, the A/B/C/D
  configuration table, one combined domain/CLUENER results table, and the
  compact false-positive category table;
- six detailed tables moved to the standalone supplement: entity definitions,
  CLUENER class counts, per-type human calibration, qualitative FP cases, the
  exact Stage-R audit, and bounded development diagnostics;
- the abstract is contribution-first, the Introduction has four contributions,
  Discussion emphasizes the C-versus-D deployment choice, limitations are
  consolidated, and the Conclusion no longer repeats project accounting.

The central paper statement is unchanged: EC-FSIE controls demonstrations,
schema terminology, and retrieved evidence for reproducible low-label Chinese
equipment NER, exposing a recall-oriented glossary operating point and a
precision-oriented RAG operating point.

## 3. Evidence And Claim Preservation

All 47 checked evidence literals remain present in either the main manuscript
or the supplement. They include the complete domain and CLUENER A/B/C/D
precision/recall/F1/FP values, calibration values, F7 exact RE values, F4a/F4b
diagnostics, and `16/60` accounting. All 27 cited keys remain used and resolve
to the existing 27 bibliography entries.

The compression adds no claim of statistical significance, SOTA, supervised
baseline superiority, broad public or cross-domain generalization, positive
RE, RAG-for-RE, CoVe gain, K robustness, frozen-test formal IAA, complete IE,
or hallucination elimination. Negative RE and verifier evidence is retained in
the exploratory boundary text and supplement rather than repeated throughout
the main narrative.

## 4. Static Verification

Non-Python checks report:

- zero unmatched braces or LaTeX environments across the 15 relevant TeX
  files;
- four unique main-manuscript labels, five resolving references, and zero
  missing or duplicate labels;
- 27 unique citation keys, all present in `references.bib`;
- 12 `main.tex` inputs, all present;
- internally consistent row widths for all three main and six supplementary
  tables;
- no TODO, FIXME, XXX, `[VERIFY]`, placeholder, negative-spacing, or manual
  page-enlargement marker in the edited body or supplement;
- no trailing whitespace and a clean `git diff --check`;
- zero changes to `main.tex`, `frontmatter.tex`, `sections/10_disclosures.tex`,
  `references.bib`, the architecture figure, `JISE.sty`, or `JISEbib.bst`.

The Windows control workspace has no `latexmk`, `pdflatex`, or `bibtex` command.
No local compilation is claimed.

## 5. Remaining Risk And Exact Next Gate

The 13--14-page target is an informed pagination estimate, not a verified page
count. LaTeX float placement, references, disclosures, and the JISE style can
shift the result. The standalone supplement also requires an independent
compile check. The last verified PDF remains the 19-page V6 artifact associated
with `1c48d1d`.

No gate is live after this closeout. The next exact gate should be:

`JISE_ECFSIE_COMPRESSION_OVERLEAF_AUDIT_APPROVED`

Under that gate, the human should compile `main.tex` from `fc8512a` and compile
`supplementary_tables.tex` separately in Overleaf, then return the main PDF,
supplement PDF, and main output ZIP/log. The next agent should verify actual
page count, all pages visually, float placement, clipping, overfull boxes,
LaTeX/BibTeX errors, citations, references, rerun requests, metadata, and font
embedding. Any further source edit requires a new, precisely bounded gate.
