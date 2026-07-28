# JISE Pre-Submission Checklist

Status legend: `[x]` verified in the Markdown package; `[ ]` requires author or
future formatting action.

## A. Journal and Cost Gate

- [ ] Institution-level JCR record confirms the exact journal/ISSN, JCR year,
  category, rank, quartile, query date, and the institution's quartile rule.
- [ ] JISE editorial office confirms the current regular-paper length limit.
- [ ] JISE confirms the current page-charge rule and whether any APC, colour,
  open-access, or other publication charge applies.
- [ ] Authors accept the expected review time; the JISE policy says many review
  results arrive in approximately six months.
- [ ] JISE confirms that the fully disclosed, human-reviewed AI-assisted
  annotation-proposal workflow and experimental model outputs comply with its
  AI policy.

Official length ambiguity to resolve: the policy page says papers may be up to
12 JISE Word-template pages and charges USD 100 for each page beyond that
limit. The manuscript page says regular manuscripts should be within 25 pages,
short papers within 15 pages, and pages beyond 12 incur USD 100 each after
acceptance. Use no more than 12 formatted pages as the conservative target.

## B. Authors and Submission-System Metadata

- [ ] Every author's full name, affiliation, postal address, email, and ORCID
  (if any) is complete and consistently spelled.
- [ ] All authors approved the exact author order.
- [ ] The corresponding author and contact details are confirmed.
- [ ] All authors approved the manuscript, cover letter, originality statement,
  funding statement, conflict declaration, and submission to JISE.
- [ ] Author emails are entered in final order; JISE's system changes author
  order when the emails are moved.
- [ ] Article type is confirmed against the live system.
- [ ] Two Associate Editors are selected from the live list after conflict
  review.
- [ ] Suggested or opposed reviewers are entered only if the live system asks;
  none are invented from the reference list.

## C. Manuscript Content and Evidence

- [x] Title is specific and indexable.
- [x] Abstract contains purpose, method, results, and conclusion.
- [x] Six keywords satisfy JISE's 5-10 keyword requirement.
- [x] References use square-bracket citations and one numbered sequence in
  first-citation order.
- [x] All 17 references retain their verified publication type; preprints and
  the DuIE data resource are not misrepresented as peer-reviewed papers.
- [x] Frozen split is consistently 30/50/170.
- [x] Final experiment scope is consistently A/B/C/D, K = 5, seeds 42/43/44,
  12 run units, 170 records per run unit, and zero parse failures.
- [x] All precision, recall, F1, and FP values match the locked P5 evidence.
- [x] C/D wording is an F1 near-tie; no statistical-superiority claim appears.
- [x] D's mean FP reduction relative to C is 55.0, with seed-42 accounting of
  181 C-only FP avoided and 126 D-only FP introduced.
- [x] Calibration is consistently described as fresh two-human non-test
  agreement: 20 passages, 175/220 entities, 158 exact matches, F1 0.800000.
- [x] The original 0.80 threshold was met exactly; the later 0.85 target was
  not met; frozen-test formal IAA is unavailable; TECH_SCHEME F1 is 0.153846.
- [x] No positive claim is made about RE, CoVe, public generalization, K scans,
  statistical significance, or a complete matrix.
- [ ] Authors confirm whether the stable source/version/licence metadata for
  QAonMilitaryKG, FAISS, and bge-reranker-v2-m3 should be added before final
  formatting.

## D. AI Policy and Declarations

- [x] The manuscript explicitly discloses Qwen2.5-7B-Instruct as the evaluated
  extractor.
- [x] It discloses Qwen2.5-14B-Instruct-AWQ as a historical candidate-
  suggestion tool whose outputs were not accepted as gold without human review.
- [x] It discloses OpenAI Codex (GPT-5-based) for English conversion, language
  editing, organization, and claim-evidence checks.
- [x] It states that authors retain responsibility and that no generative AI
  produced human-calibration annotations, altered frozen labels/results, or
  generated manuscript figures/images.
- [ ] The matching AI-use statement is entered in the submission system.
- [ ] Funding, conflicts, data availability, code availability, ethics, author
  contributions, and acknowledgements are selected and verified in file 04.

## E. JISE Formatting and Files — Separate Future Gate

- [ ] Transfer the final text into the current official JISE Word or LaTeX
  template under separately approved authorization.
- [ ] Ensure the manuscript begins with title, author names, affiliations, and
  addresses.
- [ ] Confirm all five tables are clear, numbered, captioned, and cited in text.
- [x] There are no manuscript figures/images at the Markdown stage; therefore
  no AI-generated images or 300-dpi figure files are present.
- [ ] If figures are later added, verify at least 300 dpi and source/licence.
- [x] No equations, MathType objects, appendices, or program-listing frames are
  currently required.
- [ ] Generate the PDF required by JISE's auto-submission system.
- [ ] Visually proofread every PDF page for tables, symbols, references,
  page count, fonts, line breaks, and hidden placeholders.
- [ ] Aim for no more than 12 formatted pages unless JISE supplies different
  written instructions and the authors approve the resulting charge risk.
- [ ] Confirm the uploaded file contains no internal staging notes, local paths,
  comments, revision marks, or `[[...]]` placeholders.

## F. Final Upload and Post-Acceptance Items

- [ ] Run a final duplicate-submission/originality confirmation with all authors.
- [ ] Save a timestamped copy of the exact uploaded PDF and all system entries.
- [ ] Do not change a manuscript under review or after acceptance outside the
  journal's permitted revision workflow; JISE explicitly warns against this.
- [ ] If accepted, upload the completed copyright form and review the page-charge
  agreement before final-version upload.

## Automated/Static Checks to Repeat After Any Edit

- [ ] Search for unresolved placeholders: `rg -n '\[\[[^]]+\]\]' docs/JISE_SUBMISSION_PACKAGE_20260728`.
- [ ] Search for forbidden overclaims: `significant`, `state of the art`,
  `formal test IAA`, `relation extraction improvement`, and `CoVe improvement`.
- [ ] Recheck every locked numeric literal and all five table totals.
- [ ] Run `git diff --check` and record the final commit.
