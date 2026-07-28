# JISE Submission Metadata and Author Form

> Complete this file before template conversion. JISE's online instructions
> state that author emails are added first, author information is then updated,
> and moving the emails changes author order. The order below must therefore be
> locked and checked by every author before data entry.

## Article Metadata

- Target journal: *Journal of Information Science and Engineering* (JISE)
- ISSN: 1016-2364
- Article type: [[REGULAR PAPER / CONFIRM AVAILABLE SYSTEM OPTION]]
- Title: Retrieval-Augmented Evidence for Low-Label Chinese Equipment-Domain
  NER: A Reproducible Study of Entity-Level False Positives
- Short title: Low-Label Chinese Equipment-Domain NER
- Language: English
- Keywords (6): Chinese named entity recognition; low-label learning; equipment
  domain; retrieval-augmented generation; domain glossary; large language
  models

The six keywords satisfy JISE's requirement for 5-10 keywords or key phrases.

## Copy-Ready Abstract

Named entity recognition (NER) for Chinese equipment-domain documents is
constrained by scarce annotations and by false-positive entity predictions from
generative large language model (LLM) extractors. We construct a small frozen
dataset from public equipment-related texts, with 30 support passages, 50
development passages, and 170 test passages. Using Qwen2.5-7B-Instruct as a
local extractor, we compare four incremental NER-only configurations on the
frozen test set: fixed-random demonstrations, k-nearest-neighbor (kNN)
demonstrations, kNN demonstrations with a domain glossary, and the same
configuration augmented with reranked retrieval-augmented generation (RAG)
evidence. A fresh two-human calibration on 20 previously unused non-test
passages obtained exact span-plus-type micro-F1 of 0.8000. This score exactly
met the study's original minimum threshold, but it is not formal inter-annotator
agreement for the frozen test set; moreover, the TECH_SCHEME class obtained F1
of only 0.153846. In descriptive three-seed ablations at K = 5, kNN improved F1
by 0.020524 over the fixed-random baseline, and glossary injection added
0.013689 F1 mainly through recall. The glossary-only configuration C and the
RAG configuration D were near-tied in F1 (0.568858 versus 0.565764).
Configuration D achieved higher precision and reduced the mean false-positive
entity count from 584.0 to 529.0. The evidence therefore supports RAG as a
precision- and false-positive-oriented module in this frozen low-label
equipment-domain NER setting, rather than as the best-F1 configuration or a
general solution to hallucination.

Abstract length in the Markdown source is approximately 218 words. It includes
the purpose, methodology, results, and conclusion requested by JISE.

## Author Order and Identity

Add or remove rows as needed. Use the exact spelling that should appear in the
article and submission system.

| Order | Full name | Email | ORCID | Affiliation key | Corresponding? |
| ---: | --- | --- | --- | --- | --- |
| 1 | [[AUTHOR 1]] | [[EMAIL 1]] | [[ORCID 1 / NONE]] | [[1]] | [[YES/NO]] |
| 2 | [[AUTHOR 2 / DELETE IF UNUSED]] | [[EMAIL 2]] | [[ORCID 2 / NONE]] | [[2]] | [[YES/NO]] |
| 3 | [[AUTHOR 3 / DELETE IF UNUSED]] | [[EMAIL 3]] | [[ORCID 3 / NONE]] | [[3]] | [[YES/NO]] |

Author-order approval record:

- Author 1 approval/date: [[...]]
- Author 2 approval/date: [[...]]
- Author 3 approval/date: [[...]]

## Affiliations and Addresses

1. [[DEPARTMENT, INSTITUTION, CITY, POSTCODE, COUNTRY/REGION]]
2. [[DEPARTMENT, INSTITUTION, CITY, POSTCODE, COUNTRY/REGION]]
3. [[ADD OR DELETE AS NEEDED]]

Corresponding author:

- Full name: [[...]]
- Full postal address: [[...]]
- Email: [[...]]
- Telephone if requested by the system: [[...]]

## Submission-System AI Declaration

Copy only after all authors verify the wording:

> Qwen2.5-7B-Instruct was the experimental NER extractor evaluated in this
> study. Qwen2.5-14B-Instruct-AWQ generated candidate annotation suggestions in
> a historical review workflow; suggestions were not accepted as gold without
> human review. OpenAI Codex (GPT-5-based) assisted with Chinese-to-English
> conversion, language editing, organization, and claim-evidence consistency
> checks. The authors verified and take responsibility for all content,
> citations, data, analyses, and conclusions. No generative AI produced the
> two-human calibration annotations, modified the frozen labels or numerical
> results, or generated figures/images for this manuscript. Model predictions
> from Qwen2.5-7B-Instruct are primary experimental outputs because the paper
> directly evaluates an AI extraction system.

## Preferred Associate Editors

Primary choices, subject to final conflict review and confirmation against the
live JISE list:

1. Kato, Makoto P. — University of Tsukuba.
2. Chen, Berlin — National Taiwan Normal University.

See `05_EDITOR_SELECTION.md` for the official listed interests and alternates.

## Other System Fields Requiring Author Input

- Funding body and grant number: [[... / NONE CONFIRMED]]
- Conflict-of-interest declaration: [[... / NONE CONFIRMED]]
- Data availability selection: [[SELECT IN FILE 04]]
- Code availability selection: [[SELECT IN FILE 04]]
- Ethics approval or exemption wording: [[SELECT IN FILE 04]]
- Suggested reviewers, only if the live system requests them: [[DO NOT INVENT]]
- Opposed reviewers/editors and evidence of conflict, only if needed: [[...]]
- Covering note or special issue: [[REGULAR SUBMISSION / CONFIRM]]
- JCR check record: [[YEAR, CATEGORY, RANK, QUARTILE, QUERY DATE, INSTITUTIONAL RULE]]
- Fee confirmation record: [[EDITORIAL-OFFICE RESPONSE DATE AND TERMS]]
