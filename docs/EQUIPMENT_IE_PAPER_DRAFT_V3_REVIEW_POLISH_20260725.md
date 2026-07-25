# Reducing False-Positive Entity Predictions in Few-Shot Equipment-Domain Chinese NER via Retrieval-Augmented Generation

**中文题名暂译：** 基于检索增强生成的低标注中文装备领域命名实体识别假阳性抑制方法

**版本说明：** v3 投稿型中文初稿 Markdown 版。该版本根据 P0 审稿意见重写题目、摘要、引言开头、相关工作差异化和结果讨论表述。当前仍为人工修改用草稿，不是最终投稿版。

## 摘要

专业中文装备领域命名实体识别面临两个实际瓶颈：高质量标注样本稀缺，以及大语言模型抽取器容易产生实体级假阳性预测。本文在自建冻结装备领域测试集上比较四种少样本抽取配置：固定随机示例、kNN 示例检索、领域术语表注入，以及加入 RAG 证据的抽取流程，并统一使用 Qwen2.5-7B-Instruct 和固定实体 schema 进行评估。实验结果表明，kNN 示例检索相对固定随机基线带来 2.1 个 F1 点提升，术语表通过提高召回率进一步增加 1.4 个 F1 点；RAG 与最佳 F1 配置在 F1 上接近持平，但将假阳性实体数量减少 55 个，并取得最高精确率。结果说明，在低标注装备领域 NER 中，单纯最大化 F1 可能忽略输出洁净度的实际价值；RAG 更适合作为一种 precision-oriented 模块，用于在近似保持 F1 的同时降低实体级误报。

## 1 引言

设想一名情报分析人员正在处理大量中文军事技术文档。文档中散布着装备型号、部组件、技术方案和性能指标，但逐条人工标注这些实体代价很高，尤其当语料规模扩展到数千段时更难以承受。少样本 NER 系统可以利用少量标注示例快速建立抽取能力，但基于大语言模型的抽取器常会产生假阳性：例如把研制单位误标为 EQUIPMENT，把描述性短语误标为 MODULE，或者把指标片段当作完整 METRIC。这类错误会降低分析人员对系统的信任，并给后续知识库清洗带来额外成本。

因此，装备领域低标注 NER 的关键问题不只是“如何提高 F1”，还包括“如何减少无依据或边界不可靠的实体预测”。大语言模型具备强大的指令理解和少样本迁移能力，但其生成式输出也更容易受到示例、术语和上下文先验影响。对于专业领域应用而言，一个更实用的抽取系统应当在保持抽取性能的同时，尽可能降低实体级误报。

本文研究检索增强机制是否能够满足这一需求。我们构建了一个小规模中文装备领域标注数据集，并在冻结测试集上设计 A/B/C/D 四个递进配置：A 使用固定随机示例，B 使用 kNN 检索示例，C 加入领域术语表，D 进一步加入 RAG 证据。该设计使我们能够分别观察示例检索、术语表注入和检索证据对实体抽取 F1、precision、recall 和 false-positive entity predictions 的影响。

本文的贡献可以概括为三点。第一，我们构建并冻结了一个面向中文装备领域的低标注 NER 数据集，用于验证装备、模块、技术方案和指标四类实体抽取。第二，我们实现了一个基于本地开源 LLM 的可复现少样本抽取流程，避免依赖闭源商业 API 作为实验主体。第三，三种子消融结果表明，kNN 和术语表能够提升 F1/recall，而 RAG 在 F1 near-tie 的前提下显著降低假阳性实体数量并提高 precision。

## 2 相关工作

少样本 NER 研究已经证明，在标注样本有限时，示例选择和样本相似性对实体识别性能具有重要影响。Few-NERD 为细粒度 few-shot NER 提供了代表性基准，structured nearest-neighbor learning 和 coarse-to-fine few-shot NER 则从度量学习或层级类型角度提升少样本泛化能力。与这些工作不同，本文不训练新的 few-shot NER 模型，而是将近邻思想用于 LLM in-context 示例选择，并在装备领域真实低标注设置下验证其相对固定随机示例的收益。

生成式信息抽取和 LLM-based NER 近年来发展迅速。UIE 和 InstructUIE 展示了统一结构生成和指令调优在多任务 IE 中的潜力，GPT-NER 和 OneKE 进一步说明 LLM 可以通过 schema 或任务描述完成命名实体识别和知识抽取。本文与这些工作共享“结构化生成”的技术背景，但目标不同：我们不构建通用 IE 模型，而是研究在本地开源 LLM 和少量领域标注条件下，如何通过可解释的模块组合降低装备领域 NER 的实体级误报。

领域词典和 gazetteer 是 NER 中长期使用的外部知识来源。已有研究表明，gazetteer 可以提供实体候选和类型先验，中文 NER 中的 lexicon 或实体增强预训练也有助于缓解字级模型缺少词边界的问题。本文的 glossary injection 与静态 gazetteer 特征不同：系统根据查询文本动态匹配领域术语，并将相关术语以 prompt 块形式注入 LLM。实验显示，该模块主要增强召回率和 F1，但同时可能增加假阳性，因此不能被简单视为误报抑制机制。

RAG 通过外部检索为生成模型提供可追溯证据，近年已从基础检索增强扩展到多阶段检索、重排和可靠性优化。幻觉检测研究如 SelfCheckGPT、Chain-of-Verification 以及 LLM hallucination survey 说明，生成模型的无依据输出是高风险应用中的核心问题。本文不主张当前 verifier 已经有效；相反，我们更窄地检验 RAG 的证据约束是否能迁移到 few-shot domain NER，并减少实体级 false-positive predictions。

中文信息抽取已有 CLUENER、DuIE、Few-NERD 等公开资源，军事领域也有 CMNEE 等公开事件抽取数据。然而，这些数据集的 schema 与装备技术文本中的 EQUIPMENT、MODULE、TECH_SCHEME 和 METRIC 并不完全一致。本文因此构建小规模装备领域 NER 数据，并将论文定位为低标注专业领域的工程化消融验证，而非通用 NER 或关系抽取 SOTA 对比。

## 3 数据集与任务定义

本文使用公开装备相关文本构建小规模领域数据集。数据来源包括公开百科条目、专利摘要和军事/装备相关公开语料。经过候选收集、辅助预标注、人工审查与冻结划分后，形成 support、dev 和 test 划分。当前主要实验基于冻结的 domain_test，共 170 条样本。

| 实体类型 | 定义 |
| --- | --- |
| EQUIPMENT | 装备、武器系统、平台或型号名称。 |
| MODULE | 部件、模块、子系统或组成单元。 |
| TECH_SCHEME | 技术方案、技术体制、方法或机制。 |
| METRIC | 性能指标、参数或度量表达。 |

评价采用实体级 micro precision、recall 和 F1，并报告 false-positive entity count。本文将该指标限定为实体级 false-positive 或 false-discovery-style 误报，不将其泛化为开放域事实性 hallucination 分数。

## 4 方法

系统输入为待抽取文本和少量支持集样本，输出为 JSON 结构化实体列表。Prompt 由任务定义、实体 schema、可选术语表、可选 RAG 证据、少样本示例和查询文本构成。所有 LLM 请求按完整 prompt 和生成参数缓存，解析失败按无预测处理。

A 为 fixed-random 示例基线；B 使用 BGE-M3 的 kNN 示例检索；C 在 B 的基础上注入领域术语表；D 在 C 的基础上加入 RAG 证据。A→B→C→D 构成单因素递进消融链，用于分别分析示例检索、术语表和 RAG 的贡献。

## 5 实验设置

所有实验均在冻结 domain_test 上进行，K=5，seeds 42、43、44。当前配置均为 NER-only，不报告关系抽取正面结论。所有 reported rows 均有 170 条 per-query 记录且 parse failure 为 0。

## 6 结果与分析

| 配置 | Precision | Recall | F1 | FP |
| --- | ---: | ---: | ---: | ---: |
| A | 0.4841 +/- 0.0254 | 0.5992 +/- 0.0289 | 0.5346 +/- 0.0044 | 613.3 +/- 88.8 |
| B | 0.5057 +/- 0.0002 | 0.6153 +/- 0.0018 | 0.5552 +/- 0.0009 | 573.7 +/- 1.2 |
| C | 0.5114 +/- 0.0005 | 0.6408 +/- 0.0012 | 0.5689 +/- 0.0008 | 584.0 +/- 0.0 |
| D | 0.5251 +/- 0.0000 | 0.6132 +/- 0.0000 | 0.5658 +/- 0.0000 | 529.0 +/- 0.0 |

**表注：** A 的随机种子同时影响 fixed-random 示例选择和模型生成；B 使用确定性的 kNN 示例检索，C/D 通过 knn_replay 复用 B 的示例 ID，以保证 B→C→D 的比较分别隔离 glossary 和 RAG 的单因素贡献。因此，B/C/D 的标准差主要反映模型生成或缓存条件下的残余波动，而 A 的标准差还包含随机示例选择噪声。

kNN 示例检索带来了稳定提升。B 相比 A 提升 0.0205 F1，并减少约 39.7 个假阳性实体。这表明支持样本相关性对少样本装备领域 NER 有实际影响。

领域术语表进一步提升 recall 和 F1。C 相比 B 提升 0.0137 F1，recall 从 0.6153 提高到 0.6408。但 C 的 FP 相比 B 增加约 10.3，因此 glossary injection 更适合被解释为领域覆盖增强，而不是误报抑制。

D and C achieve near-identical F1 (0.5658 vs. 0.5689, Δ = 0.0031), yet D removes 55 false-positive entity predictions that C retains. This trade-off, marginal F1 for cleaner output, is the central practical finding of this study. 换言之，RAG 的贡献不是显著提高 F1，而是在几乎保持 F1 的同时提高 precision 并降低实体级误报。

### 6.1 C 与 D 的 false-positive 定性分析

为进一步解释 RAG 的 FP-reduction 来源，我们对 C 与 D 在 seed42 上的逐条预测进行了定性比较。统计对象为 C 中为 false positive 且 D 中不存在的 predicted entities，并按其与 gold annotations 的关系进行分类。结果显示，D 并不是简单地过滤掉 55 个错误实体，而是删除或避免了 181 个 C-only false-positive predictions，同时也引入了 126 个新的 false positives，最终形成 55 个 false positives 的净减少。

| 类别 | 数量 | 解释 |
| --- | ---: | --- |
| 无明确支持的实体 | 84 | 预测实体没有 exact gold 支持。 |
| 类型或嵌套重叠错误 | 34 | 与 gold 重叠但类型或嵌套边界不一致。 |
| 短别名/代号过度标注 | 25 | 短名、代号或普通名词被提升为实体。 |
| 边界错误 | 24 | 与同类型 gold 重叠但边界不精确。 |
| 指标片段误报 | 14 | metric-like span 不是 exact gold metric。 |

这说明 RAG 证据改变了模型的错误分布，使其更倾向于保留有上下文证据支持的实体候选。需要注意的是，RAG 并不是一个完美过滤器，它仍会引入新的错误；因此本文将其贡献表述为“净减少实体级 false positives 并提高 precision”，而不是“消除 hallucination”。

## 7 讨论

当前结果支持一个窄化但清晰的 domain NER claim：kNN 和 glossary 提升 F1/recall，RAG 提高 precision 并减少 FP。RAG 贡献的关键不是 F1 最大化，而是在专业领域中降低无依据实体写入知识库的风险。

不过，当前证据不能支撑更宽泛的 IE claim。由于 P5 A/B/C/D 是 NER-only 配置，关系抽取不能作为正面结论。由于 E/E-prime 尚未形成 P5 正面结果，且 dev verification 表现负面或混合，self-verification/CoVe 也不能作为当前贡献。公开基准和 K-sensitivity 也需要后续补充。

## 8 局限性

当前测试集规模有限，虽然已冻结并进行三种子实验，但仍属于小规模领域验证。当前只完成自建装备领域数据集，没有完成公开基准泛化验证。关系抽取和验证机制暂未形成可支持的正面证据。当前只完成 K=5 设置，尚不能说明 K=1 或 K=10 下的稳定性。

## 9 结论

本文面向低标注中文装备领域 NER，构建了一个基于本地开源 LLM 的可复现实验流程，并通过 A/B/C/D 消融分析了 kNN 示例检索、领域术语表和 RAG 证据的作用。实验表明，kNN 示例选择和术语表注入能够提升实体抽取 F1；RAG 证据与术语表配置在 F1 上接近持平，但提高 precision 并减少 false-positive entity predictions。当前工作为低标注装备领域 NER 提供了一个工程化、可复现且证据边界清晰的实验基础。

## 参考文献候选

- [Ding et al., 2021] Few-NERD: A Few-shot Named Entity Recognition Dataset.
- [Yang and Katiyar, 2020] Simple and Effective Few-Shot Named Entity Recognition with Structured Nearest Neighbor Learning.
- [Ma et al., 2023] Coarse-to-fine Few-shot Learning for Named Entity Recognition.
- [Wang et al., 2025] GPT-NER: Named Entity Recognition via Large Language Models.
- [Luo et al., 2024/2025] OneKE: A Dockerized Schema-Guided LLM Agent-based Knowledge Extraction System.
- [Liu et al., 2019] Towards Improving Neural Named Entity Recognition with Gazetteers.
- [Lewis et al., 2020] Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.
- [Gao et al., 2023/2024] Retrieval-Augmented Generation for Large Language Models: A Survey.
- [Dhuliawala et al., 2024] Chain-of-Verification Reduces Hallucination in Large Language Models.
- [Manakul et al., 2023] SelfCheckGPT.
- [Zhu et al., 2024] CMNEE.
- [Chen et al., 2024] BGE M3-Embedding.
- [Qwen Team, 2025] Qwen2.5 Technical Report.
