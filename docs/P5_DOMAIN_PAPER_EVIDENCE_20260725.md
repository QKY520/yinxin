# P5 Domain A/B/C/D Paper Evidence Package - 2026-07-25

## Scope

This document converts the completed P5 domain-test A/B/C/D three-seed results
into paper-facing evidence. It does not add new experiments.

Evidence covered:

- dataset: frozen `domain_test`
- task: NER only
- K: 5
- seeds: 42, 43, 44
- configs: A/B/C/D
- model path: Qwen2.5-7B via vLLM during the completed paid runs
- current result-to-claim verdict: `partial`

## Paper-Ready Main Table Draft

Use this as the domain NER ablation table draft. Sample standard deviation is
reported over seeds 42/43/44.

| Row | Configuration | Demonstrations | Glossary | RAG | Precision | Recall | F1 | FP |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| A | Baseline | fixed random | no | no | 0.4841 +/- 0.0254 | 0.5992 +/- 0.0289 | 0.5346 +/- 0.0044 | 613.3 +/- 88.8 |
| B | kNN demos | kNN | no | no | 0.5057 +/- 0.0002 | 0.6153 +/- 0.0018 | 0.5552 +/- 0.0009 | 573.7 +/- 1.2 |
| C | kNN + glossary | kNN | yes | no | 0.5114 +/- 0.0005 | 0.6408 +/- 0.0012 | 0.5689 +/- 0.0008 | 584.0 +/- 0.0 |
| D | kNN + glossary + RAG | kNN | yes | yes | 0.5251 +/- 0.0000 | 0.6132 +/- 0.0000 | 0.5658 +/- 0.0000 | 529.0 +/- 0.0 |

Recommended table caption:

> Ablation results on the frozen equipment-domain NER test set. Scores are
> mean +/- sample standard deviation over three seeds. C and D are near-tied in
> F1; C is marginally better in recall, while D achieves the best precision and
> the lowest false-positive count.

## Clean Comparisons

| Comparison | Isolated factor | Paper-facing interpretation |
| --- | --- | --- |
| B - A | kNN demonstration selection | kNN gives a stable positive gain: +0.0205 F1 and about 39.7 fewer FP. |
| C - B | glossary injection | Glossary improves recall/F1: +0.0137 F1, but it is not a FP reducer. |
| D - C | RAG evidence | RAG is F1 near-neutral (-0.0031) but reduces FP by about 55 and improves precision. |
| D - A | combined practical pipeline | The full A-to-D path improves F1 by +0.0311 and reduces FP by about 84.3. |

## Claim-Evidence Map

| Candidate claim | Supported? | Evidence | Paper wording |
| --- | --- | --- | --- |
| kNN examples improve few-shot domain NER over fixed-random examples. | yes, within domain_test | B - A: +0.0205 F1, -39.7 FP | "kNN demonstration retrieval consistently improves over fixed-random demonstrations in the frozen domain test set." |
| Glossary injection improves entity extraction F1. | yes, within domain_test | C - B: +0.0137 F1, recall increases from 0.6153 to 0.6408 | "Glossary injection mainly improves recall and F1." |
| RAG improves F1 over glossary-only. | no / near-tie | D - C: -0.0031 F1 | Do not claim this. |
| RAG reduces false-positive entity predictions while preserving similar F1. | yes, within domain_test | D - C: -55 FP, precision 0.5251 vs 0.5114, F1 near-tie | "RAG evidence shifts the system toward higher precision and lower false positives with near-tied F1." |
| The full A-to-D pipeline improves extraction quality and reduces FP. | partial, domain NER only | D - A: +0.0311 F1, -84.3 FP | "The combined domain-oriented pipeline improves F1 over the fixed-random baseline and reduces false positives." |
| Verification / CoVe reduces hallucination. | not supported by P5 | E/E-prime absent; dev verifier was negative/mixed | Do not claim as a positive result. Mention as future work or negative/mixed exploratory branch. |
| Relation extraction is improved. | not supported | A/B/C/D are NER-only; relation output absent by configuration | Do not claim. If RE remains, report limitation or run a separate dev-first diagnostic. |
| Results generalize to public benchmarks. | not supported yet | CLUENER/P5 public benchmark not run | Do not claim until a protocol and results exist. |

## Chinese Results Paragraph Draft

在冻结的装备领域测试集上，表 X 给出了 A-D 四个配置在 5-shot、三个随机种子下的实体抽取结果。与固定随机示例的基线 A 相比，采用 kNN 检索示例的 B 将 F1 从 0.5346 提高到 0.5552，同时平均减少约 39.7 个假阳性实体，说明示例选择对低标注领域 NER 具有稳定收益。在 B 的基础上加入领域术语表后，C 的 F1 进一步提高到 0.5689，主要来自召回率提升，但其假阳性数量并未下降，表明术语表更偏向于补充领域实体覆盖，而不是抑制误报。加入 RAG 证据后的 D 与 C 在 F1 上接近持平（0.5658 对 0.5689），但 D 的精确率最高，并将平均假阳性数量从 584.0 降至 529.0。因此，RAG 的主要贡献不是显著提高 F1，而是在几乎保持 F1 的同时降低实体级误报，使系统更偏向保守且证据约束的预测。

## English Results Paragraph Draft

On the frozen equipment-domain test set, kNN demonstration retrieval improves
the F1 score from 0.5346 to 0.5552 and reduces false-positive entities by about
39.7 on average compared with the fixed-random baseline. Adding the domain
glossary further improves F1 to 0.5689, mainly through recall gains, although it
does not reduce false positives. With RAG evidence, the system is near-tied with
the glossary-only configuration in F1 (0.5658 versus 0.5689), but it achieves
the best precision and reduces the average false-positive count from 584.0 to
529.0. These results suggest that RAG contributes primarily as a precision and
false-positive reduction mechanism rather than as a direct F1 maximizer.

## Statements To Avoid

Do not write:

- "C significantly outperforms D."
- "RAG improves F1 over glossary-only."
- "Verification reduces hallucination."
- "The method improves relation extraction."
- "The method generalizes across public benchmarks."
- "The full IE pipeline is validated."

Safe wording:

- "C and D are near-tied on F1."
- "C is marginally ahead on recall/F1."
- "D is clearly ahead on precision and FP reduction."
- "The current evidence supports a scoped domain NER claim."
- "Verification, RE, and public-benchmark generalization require additional
  evidence."

## Recommended Next Step

Before any paid GPU gate, continue GPU-free paper preparation:

1. convert this evidence package into a Results subsection outline;
2. decide whether RE is removed, weakened to limitation, or diagnosed on dev;
3. decide whether public benchmark evidence is required for the target journal.
