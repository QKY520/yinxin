# Cover Letter Draft

> Staging note: replace every `[[...]]` field and delete this note before use.
> The originality, author-approval, conflict, and funding statements must be
> confirmed by all authors; they are not facts established by the repository.

Date: [[SUBMISSION DATE]]

To: Editor-in-Chief
*Journal of Information Science and Engineering*

Dear Editor-in-Chief,

We submit the manuscript entitled “Retrieval-Augmented Evidence for Low-Label
Chinese Equipment-Domain NER: A Reproducible Study of Entity-Level False
Positives” for consideration as a [[REGULAR PAPER / AUTHOR TO CONFIRM]] in the
*Journal of Information Science and Engineering*.

The manuscript addresses a practical natural-language-processing and
information-extraction problem within JISE's stated areas of Artificial
Intelligence, Information Retrieval, Machine Learning, and Natural Language
Processing. It studies a reproducible local-LLM pipeline for low-label Chinese
equipment-domain named entity recognition. Four incremental configurations
compare fixed-random and k-nearest-neighbor demonstrations, query-matched
glossary injection, and reranked retrieval-augmented evidence.

The final evidence is deliberately bounded. On a frozen 170-passage test set,
we report 12 NER-only run units covering configurations A/B/C/D at K = 5 and
seeds 42, 43, and 44. The glossary-only and RAG configurations are near-tied in
F1 (0.568858 and 0.565764). The RAG configuration has higher precision and 55.0
fewer false-positive entities on average. A fresh two-human calibration on 20
previously unused non-test passages reached exact span-plus-type micro-F1 of
0.8000, exactly meeting the study's original minimum, while exposing weak
TECH_SCHEME agreement (F1 0.153846). The manuscript clearly states that this is
not frozen-test formal inter-annotator agreement and does not claim relation-
extraction or self-verification gains, public-benchmark generalization, K-scan
robustness, statistical significance, or completion of a full ablation matrix.

The paper's practical contribution is an auditable engineering baseline that
separates recall-oriented and precision-oriented modules and retains negative
trade-offs. We believe this evidence-bounded analysis is relevant to JISE
readers working on applied NLP, information retrieval, and reliable AI systems.

In accordance with JISE's submission policy, our preferred Associate Editors
are:

1. Makoto P. Kato, whose listed interests include information retrieval,
   information extraction, and knowledge bases; and
2. Berlin Chen, whose listed interests include information retrieval, natural
   language processing, machine learning, and data analytics.

[[AUTHORS MUST CONFIRM: Neither proposed editor has a disqualifying recent
collaboration, institutional relationship, supervisory relationship, personal
relationship, or other conflict with any author.]]

The manuscript discloses all AI-assisted roles. Qwen2.5-7B-Instruct is the
experimental extractor under evaluation. Qwen2.5-14B-Instruct-AWQ generated
candidate annotation suggestions in a historical review workflow; suggestions
were not accepted as gold without human review. OpenAI Codex, a GPT-5-based
agent, assisted with English conversion, language editing, organization, and
claim-evidence consistency checks. The authors remain responsible for the
paper. No generative AI produced the two-human calibration annotations,
modified the frozen labels or numerical results, or generated figures/images
for the manuscript. The relevant disclosure is included in the paper and will
also be entered in the submission system.

[[ALL AUTHORS MUST CONFIRM BEFORE RETAINING THIS PARAGRAPH: This manuscript is
original, has not been published, is not under consideration elsewhere, and is
approved for submission by every listed author. All authors have reviewed the
final author order and declarations.]]

Thank you for considering our manuscript.

Sincerely,

[[CORRESPONDING AUTHOR FULL NAME]]

[[DEPARTMENT AND INSTITUTION]]

[[FULL POSTAL ADDRESS]]

Email: [[CORRESPONDING AUTHOR EMAIL]]

ORCID: [[ORCID OR REMOVE]]

On behalf of all authors
