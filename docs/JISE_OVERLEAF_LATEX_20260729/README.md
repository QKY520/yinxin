# JISE Overleaf LaTeX Package

Date: 2026-07-29

This directory converts the evidence-locked JISE Markdown manuscript into a
modular LaTeX project for Overleaf. It uses the official JISE style and BibTeX
style downloaded from the journal website:

- official page: <https://jise.iis.sinica.edu.tw/pages/authors/manuscripts.html>;
- official archive: <https://jise.iis.sinica.edu.tw/FILE/JISE%20LaTex%20Template.zip>;
- archive SHA256: `567D7CE8527E84A60E7B9A65EF5750B4B50B152E7094D9D23E1E17CBFADC5C63`;
- bundled `JISE.sty` SHA256: `DE66C30B9FDBBF440BDE7DFA76FAD90C032618074892A31289347DEAD715D487`;
- bundled `JISEbib.bst` SHA256: `218EB343E0827A12236622DD8779FC9973A4C4E543CA03CAC47F3281177CD6FD`.

The two official style files are copied without modification. The manuscript
content comes from
`../JISE_SUBMISSION_PACKAGE_20260728/01_JISE_MANUSCRIPT_SUBMISSION_MARKDOWN.md`.

## Project Files

- `main.tex`: compile this file in Overleaf.
- `frontmatter.tex`: author, affiliation, email, and running-head fields.
- `sections/*.tex`: manuscript sections.
- `references.bib`: the 17 source-checked references used by the manuscript.
- `JISE.sty` and `JISEbib.bst`: official JISE template files.
- `latexmkrc`: local/Overleaf PDFLaTeX build settings.
- `OVERLEAF_GUIDE_ZH.md`: step-by-step Chinese instructions.

## Important Status

This is a formatting and proofing package, not a submitted record. Bold
`[AUTHOR INPUT: ...]` markers are deliberate blockers. Authors must resolve
identity, acknowledgments, funding, conflicts, data/code availability, ethics,
and CRediT roles before submission. The corresponding-author plus sign in
`frontmatter.tex` must also be placed on the correct author.

The current project contains no author biographies or portrait photos because
the repository has no verified biographical details. Add them only after the
live JISE instructions confirm that they are required for the current
submission stage.

Use PDFLaTeX, not XeLaTeX or LuaLaTeX. JISE's sample template uses PDFLaTeX and
BibTeX. The source is English-only and does not require CJK font configuration.

## Verification Status

Static verification on 2026-07-29 confirmed that all 11 section files are
included, all 17 citation keys have exactly one bibliography entry, no
bibliography entry is unused, all `\label`/`\ref` pairs resolve at source
level, and all locked P5/P6 numbers remain present. `git diff --check` also
passed. A local PDF was not compiled because Windows and WSL have no TeX
installation, the AutoDL SSH endpoint was unavailable, and a temporary
Tectonic binary download timed out. The first real compile must therefore be
performed in Overleaf as described in `OVERLEAF_GUIDE_ZH.md`; send the compile
log back for any template-specific repair.

## Evidence Boundary

Conversion does not add experimental evidence. The manuscript remains limited
to domain NER, configurations A/B/C/D, K=5, and seeds 42/43/44. It does not
claim positive relation extraction, CoVe/self-verification, public-benchmark
generalization, K-scan robustness, statistical significance, or a complete
ablation matrix. The non-test human calibration F1 of 0.8000 is not formal
frozen-test IAA, and TECH_SCHEME F1 remains 0.153846.
