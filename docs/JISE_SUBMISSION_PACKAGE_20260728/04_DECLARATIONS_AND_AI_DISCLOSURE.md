# Declarations and AI-Assisted Tools Disclosure

This file separates statements supported by the project record from statements
that only the authors can confirm. Select one valid option for each unresolved
item and use identical wording in the manuscript, cover letter, and submission
system where applicable.

## 1. AI-Assisted Tools Disclosure — Evidence-Locked Wording

Recommended manuscript text:

> Qwen2.5-7B-Instruct was the experimental named entity recognition extractor
> evaluated in this study. Qwen2.5-14B-Instruct-AWQ was used in the historical
> dataset-review workflow to generate candidate annotation suggestions; no
> machine suggestion was accepted as gold without human review. OpenAI Codex, a
> GPT-5-based agent, assisted with Chinese-to-English conversion, language
> editing, organization, and claim-evidence consistency checks. The authors
> reviewed and take responsibility for all text, citations, data, analyses, and
> conclusions. No generative AI produced the two-human calibration annotations,
> modified the frozen reference labels or numerical results, or generated any
> figure/image in the manuscript. Qwen2.5-7B-Instruct predictions are primary
> experimental outputs because the study directly evaluates an AI extraction
> system.

This wording should not be shortened to “AI was used only for polishing.” The
Qwen2.5-7B extractor and the historical Qwen2.5-14B suggestion role are
scientifically relevant and must remain disclosed. It must also not imply that
the fresh calibration is formal frozen-test IAA.

JISE additionally requires an AI-use declaration in the submission system.
Use the matching text in file 03.

## 2. AI-Generated Figures and Data

Supported statement:

> The manuscript contains no AI-generated figures or images. The two-human
> calibration annotations, frozen reference labels, and reported numerical
> results were not generated or modified by the writing assistant. The
> Qwen2.5-7B predictions are experimental outputs of the AI system under study,
> and the historical Qwen2.5-14B candidate-suggestion role is fully disclosed.

Author action: because JISE states that AI-generated images or data are
generally not accepted but lists exceptions for material directly related to AI
research, request written confirmation that the disclosed, human-reviewed
candidate-suggestion workflow and model-output evaluation satisfy the policy.

## 3. Funding — Author Must Select One

Option A, only if no external funding supported the work:

> This research received no external funding.

Option B:

> This work was supported by [[FUNDER]] under Grant [[NUMBER]].

Do not choose Option A merely because no funding information appears in the
repository.

## 4. Conflicts of Interest — Author Must Select One

Option A, only after every author confirms:

> The authors declare no conflicts of interest.

Option B:

> [[DESCRIBE THE RELEVANT FINANCIAL OR NON-FINANCIAL INTEREST AND ITS
> MANAGEMENT.]]

Editor conflicts are checked separately in file 05.

## 5. Data Availability — Author and Licence Review Required

Recommended conservative option when redistribution has not been cleared:

> The dataset was derived from multiple public sources with source-specific
> redistribution conditions. The frozen splits and annotations are retained in
> the project archive, but unrestricted redistribution has not yet been cleared.
> Reproducibility metadata, schemas, hashes, aggregate results, and legally
> redistributable artifacts will be made available at [[STABLE REPOSITORY/DOI]]
> after source-licence review.

Alternative only if a complete legal review and stable deposit are finished:

> The data and accompanying provenance metadata are available at [[STABLE
> REPOSITORY/DOI]], subject to the licences stated there.

Do not promise raw-text release or “data available on request” unless the
corresponding author is willing and legally able to fulfill that promise.

## 6. Code Availability — Author Must Select One

Recommended after the current local commits are pushed and a stable public
release is archived:

> Source code, configurations, and paper-facing evaluation artifacts are
> available at [[REPOSITORY URL AND ARCHIVED RELEASE DOI/TAG]].

Interim wording if a stable release does not exist at submission time:

> Source code and configurations are retained in the project repository. A
> stable public release is pending repository synchronization and licence review.

The current local branch is ahead of the public remote, so the first statement
must not be used until the cited release is actually reachable and complete.

## 7. Ethics and Human Annotation — Institutional Decision Required

Suggested wording if the authors' institution confirms that formal human-
subjects review was not required:

> The study used public technical texts and involved no intervention or
> collection of sensitive personal data. Two human annotators performed a
> non-test annotation-guideline calibration. [[INSTITUTION]] determined that
> [[ETHICS REVIEW WAS NOT REQUIRED / THE ACTIVITY WAS EXEMPT, WITH REFERENCE IF
> APPLICABLE]].

Do not state an exemption without institution-specific confirmation. If an
approval or consent process applied, report its identifier and exact scope.

## 8. Author Contributions — Complete with CRediT Roles

Template:

> Conceptualization, [[INITIALS]]; methodology, [[INITIALS]]; software,
> [[INITIALS]]; validation, [[INITIALS]]; investigation, [[INITIALS]]; data
> curation, [[INITIALS]]; formal analysis, [[INITIALS]]; writing—original draft,
> [[INITIALS]]; writing—review and editing, [[INITIALS]]; supervision,
> [[INITIALS]]; project administration, [[INITIALS]]; funding acquisition,
> [[INITIALS OR NOT APPLICABLE]]. All authors reviewed and approved the final
> manuscript.

Roles must reflect actual work. Do not assign the writing assistant authorship
or a CRediT role.

## 9. Acknowledgements

Add only verified non-author contributions, facilities, or support:

> [[ACKNOWLEDGEMENTS OR “None.”]]

Keep the AI disclosure even if the acknowledgements line is “None.”
