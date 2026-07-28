# Retrieval-Augmented Evidence for Low-Label Chinese Equipment-Domain NER: A Reproducible Study of Entity-Level False Positives

**[[AUTHOR 1 FULL NAME]]^1, [[AUTHOR 2 FULL NAME]]^2, [[ADD OR DELETE AUTHORS AS NEEDED]]**

^1 [[DEPARTMENT, INSTITUTION, CITY, POSTCODE, COUNTRY/REGION]]
^2 [[DEPARTMENT, INSTITUTION, CITY, POSTCODE, COUNTRY/REGION]]

**Corresponding author:** [[FULL NAME, POSTAL ADDRESS, EMAIL]]
**Article type:** [[REGULAR PAPER — CONFIRM IN THE LIVE SYSTEM]]

> **Staging note:** Resolve every `[[...]]` field and remove this note before journal-template conversion.

## Abstract

Named entity recognition (NER) for Chinese equipment-domain documents is constrained by scarce annotations and by false-positive entity predictions from generative large language model (LLM) extractors. We construct a small frozen dataset from public equipment-related texts, with 30 support passages, 50 development passages, and 170 test passages. Using Qwen2.5-7B-Instruct as a local extractor, we compare four incremental NER-only configurations on the frozen test set: fixed-random demonstrations, k-nearest-neighbor (kNN) demonstrations, kNN demonstrations with a domain glossary, and the same configuration augmented with reranked retrieval-augmented generation (RAG) evidence. A fresh two-human calibration on 20 previously unused non-test passages obtained exact span-plus-type micro-F1 of 0.8000. This score exactly met the study's original minimum threshold, but it is not formal inter-annotator agreement for the frozen test set; moreover, the TECH_SCHEME class obtained F1 of only 0.153846. In descriptive three-seed ablations at K = 5, kNN improved F1 by 0.020524 over the fixed-random baseline, and glossary injection added 0.013689 F1 mainly through recall. The glossary-only configuration C and the RAG configuration D were near-tied in F1 (0.568858 versus 0.565764). Configuration D achieved higher precision and reduced the mean false-positive entity count from 584.0 to 529.0. The evidence therefore supports RAG as a precision- and false-positive-oriented module in this frozen low-label equipment-domain NER setting, rather than as the best-F1 configuration or a general solution to hallucination.

**Keywords:** Chinese named entity recognition; low-label learning; equipment domain; retrieval-augmented generation; domain glossary; large language models

## 1. Introduction

Chinese equipment and military-technology documents contain equipment names, modules, technical schemes, and performance metrics that are valuable for downstream search, analysis, and knowledge-base construction. Manual annotation of these entities is expensive, particularly when a domain corpus grows beyond a small collection of passages. Few-shot NER provides a practical route to bootstrap extraction from limited labeled examples, but generative LLM extractors can also create entity-level false positives. For example, an organization may be labeled as EQUIPMENT, a descriptive phrase as MODULE, or a partial numerical expression as a complete METRIC. Such errors increase the burden of downstream review and reduce trust in a deployment.

The practical question in this setting is therefore not only how to maximize F1, but also how to reduce unsupported or boundary-unreliable entity predictions without materially degrading extraction performance. Few-shot NER studies have shown that example selection and semantic proximity affect performance under limited supervision [1-3]. Meanwhile, universal information extraction and instruction-tuned extraction systems show that structured generation can support multiple extraction tasks [4-7]. These lines of work motivate a targeted engineering question: can relevant demonstrations, query-matched terminology, and retrieved evidence provide useful and interpretable control over a local LLM extractor in a narrow equipment-domain NER setting?

This paper studies that question using a frozen Chinese equipment-domain dataset and four incremental configurations. Configuration A uses a fixed-random demonstration set; B replaces it with kNN-retrieved demonstrations; C adds a query-matched domain glossary; and D additionally injects reranked RAG evidence. The resulting comparison chain is deliberately narrow. It measures entity-level micro precision, recall, F1, and false-positive entity counts for NER only. It does not establish relation-extraction effectiveness, Chain-of-Verification (CoVe) gains, public-benchmark generalization, K sensitivity, statistical significance, or completion of the originally planned full information-extraction matrix.

The contributions are as follows.

1. We document a small frozen Chinese equipment-domain NER dataset with four entity types and an independent two-human non-test calibration audit. The audit is reported accurately as non-test calibration agreement, not as formal frozen-test inter-annotator agreement (IAA).
2. We implement a reproducible local-LLM few-shot extraction pipeline that compares fixed-random versus kNN demonstrations, query-matched glossary injection, and reranked RAG evidence.
3. We provide descriptive three-seed evidence that kNN and the glossary improve F1/recall, while RAG preserves near-tied F1 relative to the glossary configuration and improves precision with 55.0 fewer false-positive entities on average. No claim of statistical significance is made.

## 2. Related Work

Few-shot NER benchmarks and methods emphasize the importance of effective use of small support sets. Few-NERD provides a representative fine-grained benchmark for few-shot NER [1]. Structured nearest-neighbor learning [2] and decomposed meta-learning [3] improve few-shot generalization through different modeling strategies. Our work does not train a new few-shot NER model. Instead, it uses semantic nearest neighbors to choose in-context examples for a local generative extractor and compares this choice with a fixed-random baseline in a domain-specific setting.

Generative information extraction has increasingly used structured outputs and task instructions. UIE formulates universal information extraction as structure generation [4], and InstructUIE extends this perspective through multi-task instruction tuning [5]. GPT-NER [6] and OneKE [7] further illustrate schema-guided LLM extraction. InstructUIE and GPT-NER are cited here as arXiv preprints, while OneKE is a peer-reviewed WWW Companion paper. Our objective differs from building a general-purpose IE system: we test whether a small number of modular, reproducible prompt components can improve the precision-recall trade-off of low-label equipment-domain NER.

External terminology has long been used in NER through gazetteers and related knowledge resources [8]. In this study, glossary injection is not a static neural feature. The system matches terminology to the current query and inserts up to a bounded number of relevant entries into the prompt. This distinction matters because dynamic terminology can increase domain coverage and recall while also encouraging extra entity predictions.

RAG conditions generation on retrieved evidence [9], and later work has examined retrieval, reranking, and reliability-oriented extensions of the RAG pipeline [10]. Work on hallucination detection and verification, including SelfCheckGPT [11] and Chain-of-Verification [12], motivates caution about unsupported generated outputs. However, the present results do not establish a positive CoVe effect. The verified final evidence concerns RAG evidence in NER-only configurations A/B/C/D, not a completed self-verification evaluation.

Chinese NER and IE resources include CLUENER [13] and DuIE 2.0 [14]; Few-NERD provides an English few-shot reference [1]. CMNEE is a public document-level military event-extraction dataset [15], not a NER dataset. These resources differ in language, task definition, or schema from the EQUIPMENT, MODULE, TECH_SCHEME, and METRIC categories used here. The present paper is therefore positioned as an applied domain NER study, not as a public-benchmark or state-of-the-art comparison.

## 3. Dataset and Task Definition

### 3.1. Construction, Split, and Freeze

We collected 400 candidate passages from public sources: 7 encyclopedia passages, 84 patent abstracts, and 309 passages originating from military- or equipment-related public text associated with CMNEE source material [15]. A project-recorded QAonMilitaryKG seed dictionary was used only for exact string-match suggestion generation. Qwen2.5-14B-Instruct-AWQ was also used in the historical proposal workflow to generate review suggestions; neither machine suggestion nor model output was accepted as gold by itself.

After human review and structural validation, 250 passages were frozen as dataset version v1: 30 support passages, 50 development passages, and 170 test passages. The support split is the sole candidate pool for both fixed-random and kNN demonstrations. Development data was used before the final test evaluation. The frozen test set was used only to evaluate final configurations; it was not used to tune prompts, thresholds, schemas, glossary entries, or retrieval settings.

The RAG corpus consists of public encyclopedia passages, patent abstracts, and glossary entries. It was deduplicated against frozen test texts with a fixed 8-gram overlap protocol. Thus, test passages do not enter the demonstration pool or RAG corpus, and the system does not retrieve the held-out test passage itself as evidence.

Freezing the split does not mean that all 170 test passages received mutually blind independent double annotation and formal adjudication. Such a complete frozen-test annotation chain is unavailable. We therefore do not describe v1 as fully independently double-annotated human gold, and we do not report a frozen-test formal IAA value.

### 3.2. Entity Types and Metrics

**Table 1. Entity definitions used in the frozen dataset.**

| Entity type | Definition |
| --- | --- |
| EQUIPMENT | An equipment item, weapon system, platform, or model name. |
| MODULE | A component, module, subsystem, or constituent unit. |
| TECH_SCHEME | A technical scheme, system, method, or mechanism. |
| METRIC | A performance metric, parameter, or measurement expression. |

An entity prediction is counted as a true positive only when both its span boundary and type exactly match the reference annotation. We report entity-level micro precision, recall, and F1, together with the false-positive entity count. The latter is a count of incorrect predicted entities. Dividing it by all predicted entities would produce an entity-level false-discovery-style measure; it is not an open-domain factuality score and is not treated as a general hallucination metric in this paper.

### 3.3. Fresh Two-Human Non-Test Calibration

To independently assess the operability of the locked annotation guideline, two human annotators independently labeled 20 previously unused non-test passages. The passages were not part of the frozen test set. Annotators began from blank sheets, received distinct randomized orders and blind identifiers, and were compared without modifying, sorting, completing, or adjudicating either annotation file. All 20 pairs passed structural checks; there were zero structural hard errors and zero blocking review items, and both annotators used all four entity types.

Annotators A and B produced 175 and 220 entities, respectively, with 158 exact span-plus-type matches. Treating A as the reference for the directional precision/recall report gives precision 0.718182, recall 0.902857, and exact micro-F1 0.800000; exchanging the reference changes directional precision and recall but not F1. Five of 20 passages were exactly identical, while 15 retained disagreements.

**Table 2. Fresh two-human calibration on 20 previously unused non-test passages.**

| Entity type | A/B entity count | Exact matches | F1 |
| --- | ---: | ---: | ---: |
| EQUIPMENT | 75/109 | 67 | 0.728261 |
| MODULE | 84/94 | 80 | 0.898876 |
| TECH_SCHEME | 6/7 | 1 | 0.153846 |
| METRIC | 10/10 | 10 | 1.000000 |

The overall F1 of 0.8000 exactly met the study's original minimum threshold of at least 0.80 and was accepted for progression to manuscript preparation. It has no safety margin and did not reach the later, more conservative target of at least 0.85. Most importantly, TECH_SCHEME F1 is only 0.153846, based on 6 and 7 annotations from the two annotators. This reveals substantial class ambiguity between technical schemes and physical equipment or modules. The result is fresh two-human non-test calibration agreement; it is not frozen-test formal IAA and does not establish uniformly reliable agreement across all four entity types.

## 4. Method

### 4.1. Structured Few-Shot Extraction

The extractor receives one query passage and K support examples and returns a JSON entity list. Prompt blocks follow a fixed order: task definition, entity schema, optional glossary entries, optional RAG evidence, K demonstrations, and the query passage. The output instruction requires JSON only. Requests are cached by a SHA256 hash of the complete prompt and model-relevant generation settings. The parsing ladder strips code fences, attempts structured JSON parsing, retries once with a legal-JSON reminder when necessary, and records a second failure as no prediction while preserving the raw output.

### 4.2. Demonstrations, Glossary, and RAG Evidence

In fixed-random mode, one K-example set is selected from the support split according to the run seed. In kNN mode, BGE-M3 [16] encodes normalized support and query vectors, and FAISS inner-product search retrieves the K most similar support examples for each query. For configurations C and D, the retrieved example identifiers are replayed from configuration B so that B-to-C and C-to-D comparisons isolate glossary and RAG changes, respectively.

The glossary is seeded from project-recorded QAonMilitaryKG terminology and high-frequency corpus terms. Entries are matched to a query by substring or keyword, with at most 20 injected entries. The RAG corpus is segmented into approximately 200-300-character passages. BGE-M3/FAISS first retrieves the top 20 candidates, bge-reranker-v2-m3 reranks them, and the top 3 evidence passages are inserted into the prompt. RAG is used to constrain initial extraction with retrieved context, not as a post-hoc rule filter.

### 4.3. Evaluated Configurations

**Table 3. Evaluated NER-only configurations.**

| Configuration | Demonstrations | Glossary | RAG evidence | Isolated comparison |
| --- | --- | --- | --- | --- |
| A | Fixed random | No | No | Baseline |
| B | kNN | No | No | B - A: demonstration retrieval |
| C | kNN replay | Yes | No | C - B: glossary injection |
| D | kNN replay | Yes | Yes | D - C: RAG evidence |

The original engineering design also explored self-verification/CoVe variants. Their development-set results were negative or mixed, and no positive final test evidence exists. They are therefore excluded from the verified method contribution and from the final table.

## 5. Experimental Setup

All final results come from the frozen 170-passage domain test split using K = 5 and random seeds 42, 43, and 44. The primary extractor is Qwen2.5-7B-Instruct [17], deployed locally in FP16. The evaluated scope is limited to four configurations and three seeds, yielding 12 completed run units. Each unit has 170 traceable per-query records, and the observed parse-failure count is zero. Tables report the mean and sample standard deviation over the three seeds.

The final configurations are NER-only: relation types are empty and no relation-extraction metric is reported. Zero relation predictions in this configuration are not relation-extraction results. The final test package does not contain E or E-prime verifier configurations, public-benchmark evaluations, K = 1 or K = 10 scans, or additional seeds. With only three seeds and no hypothesis test, all between-configuration readings in this paper are descriptive rather than statistically significant findings.

## 6. Results and Analysis

**Table 4. Frozen domain-test NER results over seeds 42, 43, and 44 at K = 5. Values are mean ± sample standard deviation.**

| Configuration | Precision (mean ± std) | Recall (mean ± std) | F1 (mean ± std) | FP (mean ± std) |
| --- | ---: | ---: | ---: | ---: |
| A | 0.484066 ± 0.025428 | 0.599231 ± 0.028904 | 0.534645 ± 0.004375 | 613.3 ± 88.8 |
| B | 0.505743 ± 0.000234 | 0.615304 ± 0.001816 | 0.555169 ± 0.000880 | 573.7 ± 1.2 |
| C | 0.511433 ± 0.000472 | 0.640811 ± 0.001210 | 0.568858 ± 0.000769 | 584.0 ± 0.0 |
| D | 0.525135 ± 0.000000 | 0.613208 ± 0.000000 | 0.565764 ± 0.000000 | 529.0 ± 0.0 |

The random seed affects both fixed-random example selection and generation in configuration A. Configuration B uses deterministic kNN demonstration retrieval, and C/D replay B's demonstration identifiers. Therefore, the larger variance in A additionally contains fixed-random demonstration-selection noise, whereas B/C/D mainly reflect residual generation or cache-condition variation under the recorded setup.

### 6.1. kNN Demonstrations and Glossary Injection

Configuration B improves F1 by 0.020524 over A and reduces the mean false-positive count by approximately 39.7. In the present frozen dataset, this is descriptive evidence that relevant support examples matter for few-shot equipment-domain NER.

Configuration C further improves F1 by 0.013689 over B. Its recall increases from 0.615304 to 0.640811, while its mean FP count rises by approximately 10.3. Accordingly, the glossary is best interpreted as a domain-coverage and recall-oriented component, rather than a false-positive suppression mechanism.

### 6.2. RAG Precision and False-Positive Trade-Off

Configurations C and D are near-tied in F1. C has marginally higher F1 and recall (0.568858 and 0.640811) than D (0.565764 and 0.613208). D has higher precision, 0.525135 versus 0.511433, and its mean FP count falls from 584.0 to 529.0. The D-minus-C F1 difference is -0.003094, while the mean net FP reduction is 55.0.

The appropriate conclusion is thus a trade-off: RAG did not produce the best F1 in this comparison, but it shifted the extractor toward a more precision-oriented operating point with fewer entity-level false positives. No statistical significance test was performed, so the near-tie must not be described as evidence that C significantly or substantially outperforms D, nor that the numerical difference identifies a stable winner.

### 6.3. Qualitative C-versus-D False-Positive Analysis

To explain the FP trade-off, we compared seed-42 predictions from C and D at the per-query level. The analysis considered false-positive entities present in C but absent from D and grouped them by their relation to the reference annotations. D did not simply remove 55 incorrect entities: it removed or avoided 181 C-only false positives and introduced 126 new false positives, yielding the net reduction of 55.

**Table 5. Seed-42 categories of C-only false positives avoided by D.**

| Category of C-only false positive avoided by D | Count | Interpretation |
| --- | ---: | --- |
| Unsupported entity | 84 | The predicted span had no exact reference support. |
| Type or nested-overlap error | 34 | The prediction overlapped a reference entity but had an inconsistent type or nested boundary. |
| Over-labeled short alias or code | 25 | A short name, code, or common noun was promoted to an entity. |
| Boundary error | 24 | The prediction overlapped a same-type reference entity but had an imprecise span boundary. |
| Metric fragment | 14 | A metric-like fragment was not an exact reference METRIC. |

This seed-42 qualitative evidence is consistent with the precision/FP trade-off in the aggregate table, but it does not prove the same error mechanism for every seed, dataset, model, or entity type. RAG remains an imperfect constraint: it can introduce new errors. We therefore describe its observed contribution as a net reduction in entity-level false positives and higher precision in this scope, not as elimination of hallucination.

## 7. Discussion

The results support a narrow, conditional claim. Under frozen v1 labels, K = 5, and the current local-model configuration, kNN demonstrations and glossary injection improve F1/recall, while RAG yields near-tied F1 relative to C with higher precision and fewer false-positive entities. The practical value of RAG in this result is not maximizing F1; it is reducing the number of erroneous candidates that could enter manual review or later knowledge-base cleaning.

The modules have different effects. kNN reduces dependence on a fixed randomly selected demonstration set. The glossary broadens domain coverage but may also invite additional false positives. RAG moves the system to a more conservative precision-oriented point. These effects are not monotonically additive, and D's lower F1 than C must be retained as a real trade-off rather than hidden by reporting only the best value.

The calibration audit further narrows interpretation. Overall non-test calibration F1 of 0.8000 indicates that the locked guideline reached the original minimum on a small fresh sample, but TECH_SCHEME agreement of 0.153846 shows that this class remains unstable. Aggregate micro-F1 on the frozen v1 labels may therefore obscure class-specific label ambiguity. The four entity types should not be treated as equally reliable in future applications.

The evidence does not support a broader information-extraction claim. The final A/B/C/D package is NER-only, so relation extraction cannot be treated as a positive result. CoVe/self-verification has no positive final-test evidence. Public-benchmark generalization, robustness across K values, and statistical significance are likewise outside the completed evidence.

## 8. Limitations

First, the dataset is small: the final test set contains 170 equipment-domain passages. The frozen test set lacks full mutually blind double annotation and formal adjudication. Although a fresh two-human non-test calibration reached exact micro-F1 of 0.8000 and met the original minimum threshold, it did not reach the later conservative 0.85 target and cannot substitute for frozen-test formal IAA. TECH_SCHEME F1 of 0.153846 is the principal dataset-quality limitation.

Second, the final ablation covers only A/B/C/D on the self-built domain test split at K = 5 and three seeds, for 12 run units. There are no public-benchmark results, K = 1/K = 10 scans, or additional seeds. The reported means and sample standard deviations describe observed run variation only; they do not justify cross-dataset generalization, K robustness, or statistical-significance claims.

Third, this is an NER-only experiment. Relation extraction did not enter final evaluation, and self-verification/CoVe did not produce positive final test evidence. Neither should be interpreted as a verified contribution. Official CLUENER test files also lack directly usable offline gold labels, so any future public-benchmark extension requires a pre-specified valid evaluation protocol.

Fourth, false-positive entity count is an entity-level extraction-error quantity, not an open-domain factuality or broad hallucination metric. The qualitative C/D error analysis examines seed 42 only. It is useful for interpreting the observed trade-off, but it is insufficient to establish a stable error mechanism across seeds, models, or corpora.

## 9. Conclusion

This work presents a reproducible local-LLM pipeline for low-label Chinese equipment-domain NER and evaluates kNN demonstrations, glossary injection, and RAG evidence through frozen-test A/B/C/D ablations over three seeds. In the current v1 dataset and K = 5 setting, kNN and the glossary improve F1/recall. Configurations C and D are near-tied in F1: C is marginally higher in recall and F1, whereas D has higher precision and 55.0 fewer false-positive entity predictions on average. The available evidence therefore supports RAG as a precision-oriented component, not as the best-F1 module or a universal hallucination-removal method.

This conclusion applies only to the frozen Chinese equipment-domain NER setting studied here. The fresh non-test human calibration has overall F1 of 0.8000 but weak TECH_SCHEME agreement, and no frozen-test formal IAA is available. Relation extraction, CoVe gains, public-benchmark generalization, K-scan robustness, statistical significance, and a complete ablation matrix remain unverified. The paper's contribution is an evidence-bounded engineering baseline that preserves both gains and negative trade-offs rather than claiming a broader completed information-extraction solution.

## 10. Acknowledgements and AI-Assisted Tools Disclosure

[[INSERT VERIFIED NON-AI ACKNOWLEDGEMENTS OR DELETE THIS PLACEHOLDER.]]

Qwen2.5-7B-Instruct was the experimental named entity recognition extractor evaluated in this study. Qwen2.5-14B-Instruct-AWQ was used in the historical dataset-review workflow to generate candidate annotation suggestions; no machine suggestion was accepted as gold without human review. OpenAI Codex, a GPT-5-based agent, assisted with Chinese-to-English conversion, language editing, organization, and claim-evidence consistency checks. The authors reviewed and take responsibility for all text, citations, data, analyses, and conclusions. No generative AI produced the two-human calibration annotations, modified the frozen reference labels or numerical results, or generated any figure/image in the manuscript. Qwen2.5-7B-Instruct predictions are primary experimental outputs because the study directly evaluates an AI extraction system.

## 11. Declarations

**Funding:** [[SELECT AND VERIFY THE FINAL STATEMENT IN FILE 04.]]

**Conflicts of interest:** [[SELECT AND VERIFY THE FINAL STATEMENT IN FILE 04.]]

**Data availability:** [[SELECT THE LICENCE-COMPATIBLE STATEMENT IN FILE 04 AND ADD A STABLE REPOSITORY/DOI IF AVAILABLE.]]

**Code availability:** [[CITE A REACHABLE ARCHIVED RELEASE OR USE THE VERIFIED INTERIM STATEMENT IN FILE 04.]]

**Ethics statement:** [[OBTAIN THE INSTITUTION-SPECIFIC DETERMINATION DESCRIBED IN FILE 04.]]

**Author contributions:** [[INSERT VERIFIED CRediT ROLES FROM FILE 04.]]

## References

[1] N. Ding, G. Xu, Y. Chen, et al., “Few-NERD: A Few-shot Named Entity Recognition Dataset,” in *Proceedings of ACL-IJCNLP 2021*, 2021, pp. 3198-3213. https://doi.org/10.18653/v1/2021.acl-long.248.

[2] Y. Yang and A. Katiyar, “Simple and Effective Few-Shot Named Entity Recognition with Structured Nearest Neighbor Learning,” in *Proceedings of EMNLP 2020*, 2020, pp. 6365-6375. https://doi.org/10.18653/v1/2020.emnlp-main.516.

[3] T. Ma, H. Jiang, Q. Wu, et al., “Decomposed Meta-Learning for Few-Shot Named Entity Recognition,” in *Findings of ACL 2022*, 2022, pp. 1584-1596. https://doi.org/10.18653/v1/2022.findings-acl.124.

[4] Y. Lu, Q. Liu, D. Dai, et al., “Unified Structure Generation for Universal Information Extraction,” in *Proceedings of ACL 2022*, 2022, pp. 5755-5772. https://doi.org/10.18653/v1/2022.acl-long.395.

[5] X. Wang, W. Zhou, C. Zu, et al., “InstructUIE: Multi-task Instruction Tuning for Unified Information Extraction,” arXiv preprint arXiv:2304.08085, 2023. https://doi.org/10.48550/arXiv.2304.08085.

[6] S. Wang, X. Sun, X. Li, et al., “GPT-NER: Named Entity Recognition via Large Language Models,” arXiv preprint arXiv:2304.10428, 2023. https://doi.org/10.48550/arXiv.2304.10428.

[7] Y. Luo, X. Ru, K. Liu, et al., “OneKE: A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction System,” in *Companion Proceedings of the ACM Web Conference 2025*, 2025, pp. 2871-2874. https://doi.org/10.1145/3701716.3715189.

[8] T. Liu, J. G. Yao, and C.-Y. Lin, “Towards Improving Neural Named Entity Recognition with Gazetteers,” in *Proceedings of ACL 2019*, 2019, pp. 5301-5307. https://doi.org/10.18653/v1/P19-1524.

[9] P. Lewis, E. Perez, A. Piktus, et al., “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” *Advances in Neural Information Processing Systems*, vol. 33, pp. 9459-9474, 2020.

[10] Y. Gao, Y. Xiong, X. Gao, et al., “Retrieval-Augmented Generation for Large Language Models: A Survey,” arXiv preprint arXiv:2312.10997, 2023, revised 2024. https://doi.org/10.48550/arXiv.2312.10997.

[11] P. Manakul, A. Liusie, and M. Gales, “SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models,” in *Proceedings of EMNLP 2023*, 2023, pp. 9004-9017. https://doi.org/10.18653/v1/2023.emnlp-main.557.

[12] S. Dhuliawala, M. Komeili, J. Xu, et al., “Chain-of-Verification Reduces Hallucination in Large Language Models,” in *Findings of ACL 2024*, 2024, pp. 3563-3578. https://doi.org/10.18653/v1/2024.findings-acl.212.

[13] L. Xu, Y. Tong, Q. Dong, et al., “CLUENER2020: Fine-grained Named Entity Recognition Dataset and Benchmark for Chinese,” arXiv preprint arXiv:2001.04351, 2020. https://doi.org/10.48550/arXiv.2001.04351.

[14] Baidu Qianyan, “DuIE 2.0,” dataset resource. https://dataset-bj.cdn.bcebos.com/qianyan/DuIE_2_0.zip (accessed Jul. 28, 2026).

[15] M. Zhu, Z. Xu, K. Zeng, et al., “CMNEE: A Large-Scale Document-Level Event Extraction Dataset Based on Open-Source Chinese Military News,” in *Proceedings of LREC-COLING 2024*, 2024, pp. 3367-3379. https://aclanthology.org/2024.lrec-main.299/.

[16] J. Chen, S. Xiao, P. Zhang, et al., “M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation,” in *Findings of ACL 2024*, 2024, pp. 2318-2335. https://doi.org/10.18653/v1/2024.findings-acl.137.

[17] Qwen, A. Yang, B. Yang, et al., “Qwen2.5 Technical Report,” arXiv preprint arXiv:2412.15115, 2024, revised 2025. https://doi.org/10.48550/arXiv.2412.15115.
