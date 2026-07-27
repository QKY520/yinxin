# Reducing False-Positive Entity Predictions in Few-Shot Equipment-Domain Chinese NER via Retrieval-Augmented Generation

**中文题名暂译：** 基于检索增强生成的低标注中文装备领域命名实体识别假阳性抑制方法

**版本说明：** v3 投稿型中文初稿 Markdown 精修版。本版已纳入 2026-07-27 完成的双人非测试集校准，并按已验证的 A/B/C/D 证据收紧全文主张。当前仍为投稿前中文技术草稿。

## 摘要

专业中文装备领域命名实体识别面临两个实际瓶颈：人工标注资源有限，以及生成式大语言模型抽取器容易产生实体级假阳性预测。本文构建了一个来自公开装备相关文本的小规模冻结数据集，划分为 30 条 support、50 条 dev 和 170 条 test，并以 Qwen2.5-7B-Instruct 为抽取器，在冻结测试集上比较固定随机示例、kNN 示例检索、领域术语表注入和 RAG 证据四种递进配置。两名真人在 20 条此前未用于旧校准的非测试文本上独立标注，exact span+type micro-F1 为 0.8000，恰好达到项目原定最低门槛；该结果不是冻结测试集的正式 IAA，且 TECH_SCHEME 的分类型 F1 仅为 0.153846。K=5、随机种子 42/43/44 的描述性消融结果显示，kNN 相对固定随机基线提高 0.020524 F1，术语表通过提高召回率进一步增加 0.013689 F1。加入 RAG 后，D 与术语表配置 C 的 F1 接近持平（0.565764 对 0.568858），但 D 的 precision 更高，并将平均假阳性实体数从 584.0 降至 529.0。结果表明，在当前冻结的低标注装备领域 NER 设置中，RAG 的主要价值是以较小的 F1 权衡换取更高 precision 和更少实体级误报，而不是提高最佳 F1。

**关键词：** 中文命名实体识别；低标注学习；装备领域；检索增强生成；领域术语表；大语言模型

## 1 引言

设想一名情报分析人员正在处理大量中文军事技术文档。文档中散布着装备型号、部组件、技术方案和性能指标，但逐条人工标注这些实体代价很高，尤其当语料规模扩展到数千段时更难以承受。少样本 NER 系统可以利用少量标注示例快速建立抽取能力，但基于大语言模型的抽取器常会产生假阳性：例如把研制单位误标为 EQUIPMENT，把描述性短语误标为 MODULE，或者把指标片段当作完整 METRIC。这类错误会降低分析人员对系统的信任，并给后续知识库清洗带来额外成本。

因此，装备领域低标注 NER 的关键问题不只是“如何提高 F1”，还包括“如何减少无依据或边界不可靠的实体预测”。大语言模型具备强大的指令理解和少样本迁移能力，但其生成式输出也更容易受到示例、术语和上下文先验影响。对于专业领域应用而言，一个更实用的抽取系统应当在保持抽取性能的同时，尽可能降低实体级误报。

本文研究检索增强机制是否能够满足这一需求。我们构建了一个小规模中文装备领域标注数据集，并在冻结测试集上设计 A/B/C/D 四个递进配置：A 使用固定随机示例，B 使用 kNN 检索示例，C 加入领域术语表，D 进一步加入 RAG 证据。该单因素递进链用于分别观察示例检索、术语表注入和检索证据对实体抽取 F1、precision、recall 和 false-positive entity count 的影响。本文报告的是这一限定范围内的 NER 证据，而不是原计划中关系抽取、自我验证、公开基准和 K 扫描均已完成的完整信息抽取矩阵。

本文的贡献限定为以下三点：

1. 构建并冻结一个面向中文装备领域的小规模低标注 NER 数据集，覆盖 EQUIPMENT、MODULE、TECH_SCHEME 和 METRIC 四类实体；同时报告独立的双人非测试集校准，而不将其误称为冻结测试集正式 IAA。
2. 实现一个以本地开源 LLM 为主体的可复现少样本抽取流程，通过 A/B/C/D 递进配置比较固定随机与 kNN 示例、查询匹配术语表和重排后的 RAG 证据。
3. 在冻结领域测试集 K=5、三个随机种子的结果中，给出 kNN 与术语表的 F1/recall 收益，以及 C/D 的 F1 近似持平（near-tie）时 RAG 提高 precision、平均净减少 55.0 个假阳性实体的描述性证据；本文不据此声称统计显著性。

## 2 相关工作

少样本 NER 研究已经证明，在标注样本有限时，示例选择和样本相似性对实体识别性能具有重要影响。Few-NERD 为细粒度 few-shot NER 提供了代表性基准，structured nearest-neighbor learning 和 coarse-to-fine few-shot NER 则从度量学习或层级类型角度提升少样本泛化能力。与这些工作不同，本文不训练新的 few-shot NER 模型，而是将近邻思想用于 LLM in-context 示例选择，并在装备领域真实低标注设置下验证其相对固定随机示例的收益。

生成式信息抽取和 LLM-based NER 近年来发展迅速。UIE 和 InstructUIE 展示了统一结构生成和指令调优在多任务 IE 中的潜力，GPT-NER 和 OneKE 进一步说明 LLM 可以通过 schema 或任务描述完成命名实体识别和知识抽取。本文与这些工作共享“结构化生成”的技术背景，但目标不同：我们不构建通用 IE 模型，而是研究在本地开源 LLM 和少量领域标注条件下，如何通过可解释的模块组合降低装备领域 NER 的实体级误报。

领域词典和 gazetteer 是 NER 中长期使用的外部知识来源。已有研究表明，gazetteer 可以提供实体候选和类型先验，中文 NER 中的 lexicon 或实体增强预训练也有助于缓解字级模型缺少词边界的问题。本文的 glossary injection 与静态 gazetteer 特征不同：系统根据查询文本动态匹配领域术语，并将相关术语以 prompt 块形式注入 LLM。实验显示，该模块主要增强召回率和 F1，但同时可能增加假阳性，因此不能被简单视为误报抑制机制。

RAG 通过外部检索为生成模型提供可追溯证据，近年已从基础检索增强扩展到多阶段检索、重排和可靠性优化。幻觉检测研究如 SelfCheckGPT、Chain-of-Verification 以及 LLM hallucination survey 说明，生成模型的无依据输出是高风险应用中的核心问题。本文不主张当前 verifier 已经有效；相反，我们更窄地检验 RAG 的证据约束是否能迁移到 few-shot domain NER，并减少实体级 false-positive predictions。

公开 NER/IE 资源中，CLUENER 和 DuIE 面向中文任务，Few-NERD 提供英文 few-shot NER 参照，军事领域还有 CMNEE 等公开事件抽取数据。然而，这些数据集的语言、任务或 schema 与装备技术文本中的 EQUIPMENT、MODULE、TECH_SCHEME 和 METRIC 并不完全一致。本文因此构建小规模装备领域 NER 数据，并将论文定位为低标注专业领域的工程化消融验证，而非通用 NER 或关系抽取 SOTA 对比。当前实验没有验证跨公开基准泛化。

## 3 数据集与任务定义

### 3.1 数据构建、划分与冻结

本文从公开百科条目、专利摘要和军事/装备相关公开语料中收集 400 条候选文本，其中百科 7 条、专利 84 条、CMNEE 来源文本 309 条。QAonMilitaryKG 的精确字符串匹配和 Qwen2.5-14B-Instruct-AWQ 仅用于生成辅助标注建议，建议本身不作为 gold。经人工审查与结构验证后，最终形成 250 条冻结 v1 数据：support 30 条、dev 50 条、test 170 条。support 是 kNN 或固定随机示例的唯一候选池，dev 用于冻结前开发，test 仅用于最终配置评估。

冻结测试集具有固定文件哈希和冻结标记。RAG 语料由公开百科、专利和术语条目构成，并按固定 8-gram 协议与测试文本去重；测试文本不进入示例池或 RAG 语料。数据冻结后，本文未根据测试结果修改 prompt、schema、阈值或实验配置。

冻结流程不等于对 170 条测试文本完成了双人独立标注。现有测试集未建立全量、相互盲法的双标与裁决链路，因此本文不报告 frozen-test formal IAA，也不将冻结 v1 描述为“全部独立双标的人类 gold”。

### 3.2 实体类型与评价指标

| 实体类型 | 定义 |
| --- | --- |
| EQUIPMENT | 装备、武器系统、平台或型号名称。 |
| MODULE | 部件、模块、子系统或组成单元。 |
| TECH_SCHEME | 技术方案、技术体制、方法或机制。 |
| METRIC | 性能指标、参数或度量表达。 |

实体预测仅在边界与类型均完全匹配时计为 true positive。评价采用实体级 micro precision、recall 和 F1，并报告 false-positive entity count。后者是错误预测实体的数量；若以 FP 除以全部预测实体，则属于实体级 false-discovery-style 指标，不是通常意义的开放域事实性 hallucination 分数。本文不将 FP count 扩展解释为模型事实性。

### 3.3 双人非测试集校准

为独立检查标注规范的可操作性，两名真人依据锁定的 v4 指南，对 20 条此前未用于旧校准且不属于冻结测试集的文本进行校准。两人分别从空白表开始，使用不同的随机顺序和盲 ID 独立标注；验证阶段只对齐文本与实体结果，不修改、排序、补齐或裁决任何标签。20/20 对均通过结构检查，结构性硬错误和需阻断处理的复核项均为 0，双方都实际覆盖了四种实体类型。

标注者 A/B 分别给出 175/220 个实体，其中 158 个 exact span+type 匹配。以 B 相对 A 记 precision/recall 时，P/R/F1 为 0.718182/0.902857/0.800000；F1 在交换 A/B 后不变。20 条中 5 条完全一致，15 条仍存在分歧。分类型结果如下。

| 实体类型 | A/B 实体数 | Exact matches | F1 |
| --- | ---: | ---: | ---: |
| EQUIPMENT | 75/109 | 67 | 0.728261 |
| MODULE | 84/94 | 80 | 0.898876 |
| TECH_SCHEME | 6/7 | 1 | 0.153846 |
| METRIC | 10/10 | 10 | 1.000000 |

总体 F1 0.8000 恰好达到项目原定的 `>=0.80` 最低门槛，因而被接受用于进入当前论文阶段，但没有安全余量，也未达到后续锁定指南采用的保守目标 `>=0.85`。尤其是 TECH_SCHEME F1 仅为 0.153846，且双方在该类上仅标出 6/7 个实体，说明技术方案与物理装备/模块之间仍存在严重类别歧义和较高估计不确定性。该结果只能称为双人非测试集校准一致度（fresh two-human non-test calibration agreement），不能称为冻结测试集正式 IAA，也不能说明四类实体均具有良好一致性。

## 4 方法

### 4.1 结构化少样本抽取

系统输入为待抽取文本和 K 条支持集示例，输出为 JSON 结构化实体列表。Prompt 块依次为任务定义、实体 schema、可选术语表、可选 RAG 证据、K 条示例和查询文本。输出约束要求模型只返回 JSON。请求以完整 prompt 和模型相关生成参数的 SHA256 为键缓存；解析时依次去除代码围栏、执行结构化 JSON 解析，并在失败后追加合法 JSON 提醒重试一次，第二次失败则记为无预测并保留原始输出。

### 4.2 示例选择、术语表与 RAG

固定随机模式在 support 中按运行 seed 选择一组 K 条示例；kNN 模式使用 BGE-M3 生成归一化向量，并通过 FAISS 内积检索每个查询最相近的 K 条 support 示例。领域术语表以 QAonMilitaryKG 和语料高频术语为种子，根据查询文本的子串或关键词匹配条目，每个查询最多注入 20 条。

RAG 语料先切分为约 200-300 字的段落。查询时由 BGE-M3/FAISS 召回 top-20，再使用 bge-reranker-v2-m3 重排并将 top-3 证据放入 prompt。检索证据用于约束初始抽取，而不是一个事后规则过滤器。

### 4.3 对比配置

| 配置 | 示例 | 术语表 | RAG | 当前比较含义 |
| --- | --- | --- | --- | --- |
| A | fixed random | 否 | 否 | 基线 |
| B | kNN | 否 | 否 | B-A：示例检索 |
| C | kNN replay | 是 | 否 | C-B：术语表 |
| D | kNN replay | 是 | 是 | D-C：RAG 证据 |

B 使用 BGE-M3 的 kNN 示例检索；C/D 复用 B 的示例 ID，使 B→C→D 的比较分别隔离术语表和 RAG。原始工程还探索过 self-verification/CoVe，但其 dev 结果为负面或混合，且没有最终测试集正面证据，因此不作为本文已验证的方法贡献。

## 5 实验设置

本文报告的最终测试结果均来自冻结的 170 条 domain test，K=5，seeds 为 42、43、44，主模型为以 FP16 部署的 Qwen2.5-7B-Instruct。实验范围仅包含 A/B/C/D 共 12 个运行单元；每个单元均有 170 条可回溯的 per-query 记录，parse failure 为 0。表中报告三个随机种子的均值与样本标准差。

当前配置的任务均为 NER-only，关系类型为空，因此不报告关系抽取性能，也不将零关系预测解释为关系抽取实验的负面结果。本文没有完成 E/E′、公开基准、K=1/K=10 或更多 seed 的最终测试。由于只使用三个 seed 且未进行假设检验，所有配置差异均作描述性解释，不使用“统计显著”措辞。

## 6 结果与分析

| 配置 | Precision (mean +/- std) | Recall (mean +/- std) | F1 (mean +/- std) | FP (mean +/- std) |
| --- | ---: | ---: | ---: | ---: |
| A | 0.484066 +/- 0.025428 | 0.599231 +/- 0.028904 | 0.534645 +/- 0.004375 | 613.3 +/- 88.8 |
| B | 0.505743 +/- 0.000234 | 0.615304 +/- 0.001816 | 0.555169 +/- 0.000880 | 573.7 +/- 1.2 |
| C | 0.511433 +/- 0.000472 | 0.640811 +/- 0.001210 | 0.568858 +/- 0.000769 | 584.0 +/- 0.0 |
| D | 0.525135 +/- 0.000000 | 0.613208 +/- 0.000000 | 0.565764 +/- 0.000000 | 529.0 +/- 0.0 |

**表注：** A 的随机种子同时影响 fixed-random 示例选择和模型生成；B 使用确定性的 kNN 示例检索，C/D 通过 knn_replay 复用 B 的示例 ID，以保证 B→C→D 的比较分别隔离 glossary 和 RAG 的单因素贡献。因此，B/C/D 的标准差主要反映模型生成或缓存条件下的残余波动，而 A 的标准差还包含随机示例选择噪声。

kNN 示例检索带来了正向描述性变化。B 相比 A 提升 0.020524 F1，并平均减少约 39.7 个假阳性实体。这表明在当前冻结数据上，支持样本相关性对少样本装备领域 NER 有实际影响。

领域术语表进一步提升 recall 和 F1。C 相比 B 提升 0.013689 F1，recall 从 0.615304 提高到 0.640811；但 C 的平均 FP 相比 B 增加约 10.3。因此，glossary injection 更适合被解释为领域覆盖增强，而不是误报抑制。

C 和 D 在 F1 上近似持平（near-tie）：C 的 F1/recall 为 0.568858/0.640811，略高于 D 的 0.565764/0.613208；D 的 precision 为 0.525135，高于 C 的 0.511433。D-C 的 F1 差为 -0.003094，但平均 FP 从 584.0 降至 529.0，即净减少 55.0。因而，RAG 的贡献不是 F1 提升，而是在 F1 近似持平的同时提高 precision 并降低实体级误报。由于没有统计显著性检验，本文不声称 C 显著优于 D，也不声称 0.003094 的差异代表稳定优势。

### 6.1 C 与 D 的 false-positive 定性分析

为进一步解释 RAG 的 FP-reduction 来源，我们对 C 与 D 在 seed42 上的逐条预测进行了定性比较。统计对象为 C 中为 false positive 且 D 中不存在的 predicted entities，并按其与 gold annotations 的关系进行分类。结果显示，D 并不是简单地过滤掉 55 个错误实体，而是删除或避免了 181 个 C-only false-positive predictions，同时也引入了 126 个新的 false positives，最终形成 55 个 false positives 的净减少。

| 类别 | 数量 | 解释 |
| --- | ---: | --- |
| 无明确支持的实体 | 84 | 预测实体没有 exact gold 支持。 |
| 类型或嵌套重叠错误 | 34 | 与 gold 重叠但类型或嵌套边界不一致。 |
| 短别名/代号过度标注 | 25 | 短名、代号或普通名词被提升为实体。 |
| 边界错误 | 24 | 与同类型 gold 重叠但边界不精确。 |
| 指标片段误报 | 14 | metric-like span 不是 exact gold metric。 |

该 seed 42 定性结果与主表中的 precision/FP 权衡一致，表明在该比较中模型的错误分布发生了变化，但不能证明其对所有 seed、数据集或错误类型均有相同作用。RAG 也不是一个完美过滤器，它仍会引入新的错误；因此本文将其贡献表述为“净减少实体级 false positives 并提高 precision”，而不是“消除 hallucination”。

## 7 讨论

当前结果支持一个窄化且有条件的领域 NER 主张：在冻结 v1 标签、K=5 和当前模型设置下，kNN 和 glossary 提升 F1/recall，RAG 在 C/D 的 F1 近似持平时提高 precision 并减少 FP。RAG 贡献的关键不是 F1 最大化，而是减少进入后续人工审查或知识库清洗环节的错误实体候选。

从模块作用看，kNN 降低了固定随机示例选择带来的不稳定性；术语表提高领域实体覆盖，但也可能引入额外 FP；RAG 则把输出推向更保守的 precision-oriented 工作点。这三种作用并非单调叠加，D 的 F1 低于 C 也应作为真实权衡保留，而不能通过只报告最佳指标掩盖。

标注校准进一步限定了结果的解释范围。总体 agreement F1 0.8000 说明锁定规范在小规模非测试样本上达到原始最低可用门槛，但 TECH_SCHEME 的 0.153846 显示该类别定义仍不稳定。因此，当前 v1 上的总体 micro-F1 可能掩盖技术方案类别的标签噪声，后续应用不应把四类实体视为同等可靠。

不过，当前证据不能支撑更宽泛的信息抽取主张。A/B/C/D 是 NER-only 配置，关系抽取不能作为正面结论；self-verification/CoVe 在 dev 上表现负面或混合，且没有最终测试集正面证据，也不能作为当前贡献。公开基准泛化、不同 K 下的稳健性以及统计显著性同样不在现有证据范围内。

## 8 局限性

第一，数据规模有限，最终测试仅包含 170 条装备领域文本。冻结测试集没有完成全量、相互盲法的双人独立标注与正式裁决；20 条 fresh non-test calibration 的 exact span+type micro-F1 虽达到原定 0.80 最低门槛，但未达到更保守的 0.85 目标，也不能替代 frozen-test formal IAA。TECH_SCHEME F1 仅为 0.153846，是最主要的数据质量风险。

第二，最终消融仅覆盖自建领域测试集上的 A/B/C/D、K=5 和三个 seed，共 12 个运行单元。本文没有公开基准结果、K=1/K=10 扫描或更多 seed，因而不能主张跨数据集泛化、K 稳健性或统计显著性。三个 seed 的均值和样本标准差仅用于描述当前运行波动。

第三，当前实验为 NER-only。关系抽取没有进入最终评估，self-verification/CoVe 也没有形成正面最终测试证据；二者均不能被视为本文已验证贡献。公开 CLUENER 的官方 test 缺少可直接用于离线评估的 gold，任何未来补充都需先锁定有效协议。

第四，false-positive entity count 是实体级错误数量，不是开放域事实性或广义 hallucination 指标。C/D 错误类型分析只检查了 seed 42，适合解释当前误报构成，不足以证明错误机制在其他 seed、模型或语料上稳定复现。

## 9 结论

本文面向低标注中文装备领域 NER，构建了一个以本地开源 LLM 为主体的可复现实验流程，并通过冻结测试集上三个随机种子的 A/B/C/D 消融分析 kNN 示例检索、领域术语表和 RAG 证据的作用。在当前 v1 数据和 K=5 设置下，kNN 与术语表分别带来 F1/recall 收益；C 和 D 的 F1 近似持平，C 的 recall/F1 略高，而 D 的 precision 更高并平均少 55.0 个 false-positive entity predictions。因此，现有结果支持将 RAG 视为 precision-oriented 模块，而不是最佳 F1 模块或通用 hallucination 消除机制。

这一结论仅适用于当前冻结的中文装备领域 NER 设置。双人非测试集校准的总体 F1 为 0.8000，但 TECH_SCHEME 一致性很低，且不存在 frozen-test formal IAA；关系抽取、CoVe、公开基准泛化、K 扫描稳健性和统计显著性均未由当前实验验证。本文的价值在于提供一个范围明确、数字可回溯且保留负面权衡的工程证据基础，而不是声称完成了更宽泛的信息抽取方案。

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
