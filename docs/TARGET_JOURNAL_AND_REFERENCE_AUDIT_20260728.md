# 目标期刊筛选与参考文献真实性核验

日期：2026-07-28
范围：当前中文 Markdown 稿件，不补实验，不转换英文或期刊模板
核验方式：出版社/期刊官网、ACL Anthology、arXiv、DBLP 和官方数据下载页的普通网页；未调用模型、外部 LLM 或 API

## 1. 执行结论

当前稿件可以进入“人工确认 JCR 分区后选刊”的阶段。公开网页已经确认三本候选均由期刊官网声明进入 SCIE/SCI，且主题范围能够容纳 AI、信息系统或应用型 NER 工作；但是三本官网都没有公开展示可据以锁定投稿决策的当前 JCR quartile。因此，“SCI Q4”仍是投稿前必须由作者通过机构版 Journal Citation Reports 当日确认的人工门禁，不能用 JIF 数值、Scopus CiteScore 或 SJR quartile 替代。

建议顺序如下：

1. `Journal of Information Science and Engineering`（JISE）：当前首选。主题与应用型 AI/信息工程最贴近，官网只明确超页费，成本风险相对最低；缺点是官网称多数评审约需 6 个月。
2. `KSII Transactions on Internet and Information Systems`（KSII TIIS）：第一备选。官网明确 SCIE、开放获取、AI & Big Data/Information Systems 范围，但 700 USD 出版费与当前低预算路线不匹配。
3. `Computer Science and Information Systems`（ComSIS）：第二备选。官网明确 SCI/JCR、开放获取和应用型信息系统范围，但出版费为 600 EUR，官网还提示投稿过载，且不同页面对篇幅上限存在 20 页与 25-30 页的冲突。

如果机构版 JCR 不能确认某刊满足作者单位所采用年度、学科类别和 quartile 口径，该刊应立即从 Q4 路线移除，不应仅因官网写有 SCIE 而继续投稿。

## 2. 三本候选期刊

| 顺序 | 期刊 | 官网可确认的索引与指标 | 主题适配 | 费用与篇幅 | 周期与主要风险 |
| ---: | --- | --- | --- | --- | --- |
| 1 | Journal of Information Science and Engineering | 官网列出 SCIE；显示 2024 JIF 1.1；双月刊 | Scope 包含 Artificial Intelligence，适合突出低标注 NER、可复现管线与误报控制 | 12 页以内；超出后每页 100 USD。官网未明确列出常规 APC，投稿前需向编辑部确认 | 官网称多数稿件约 6 个月得到评审结果；当前 JCR quartile 未公开，必须机构确认 |
| 2 | KSII Transactions on Internet and Information Systems | 官网列出 SCIE；显示 2025 JIF 1.0；月刊、开放获取 | Scope 明列 Artificial Intelligence & Big Data 和 Information Systems；需将稿件定位为信息系统中的应用型实体抽取 | 13-21 页；700 USD 出版费 | 费用高；Internet 主题不是本文核心，cover letter 需解释信息系统适配；当前 JCR quartile 必须机构确认 |
| 3 | Computer Science and Information Systems | 官网列出 Science Citation Index 和 JCR；显示 2024 两年 JIF 1.8；开放获取 | 接收计算机科学、软件工程和信息系统的理论与产业/应用研究，可容纳工程型 NER | 600 EUR；作者指南写 25-30 页，政策页写 20 页，须投稿前书面确认 | 官网提示编辑部投稿过载；政策页称 4-8 个月；最终稿仅收 LaTeX；当前 JCR quartile 必须机构确认 |

### 2.1 JISE 官网证据

- Aims, scope, SCIE、JIF 和出版频率：<https://jise.iis.sinica.edu.tw/pages/jise/index.html>
- 篇幅、超页费和约 6 个月评审说明：<https://jise.iis.sinica.edu.tw/pages/authors/index.html>
- 风险控制：官网只明确“超过 12 页每页 100 USD”，不能据此推断常规发表一定免费；投稿前应邮件确认是否还有彩图、开放获取或其他费用。

### 2.2 KSII TIIS 官网证据

- Aim and Scope、SCIE、开放获取、月刊和 2025 JIF：<https://itiis.org/journals/tiis/about>
- 13-21 页、同行评审和 700 USD 出版费：<https://itiis.org/journals/tiis/author-guide>
- 风险控制：作者指南同页仍保留一段旧的 500 USD 历史规则，但较新的规则明确写明 2020-07-01 后为 700 USD，应按 700 USD 预算并在投稿前确认。

### 2.3 ComSIS 官网证据

- 首页、2024 JIF 和 SCI 声明：<https://www.comsis.org/>
- Aims and scope：<https://www.comsis.org/aims.php>
- Science Citation Index/JCR 收录说明：<https://www.comsis.org/indexing.php>
- 作者指南、投稿过载提示和 25-30 页说明：<https://www.comsis.org/information.php>
- 600 EUR 出版费及无额外超页费说明：<https://www.comsis.org/accepted-papers.php>
- 4-8 个月和 20 页说明：<https://www.comsis.org/policies.php>
- 风险控制：20 页与 25-30 页两套上限同时存在，不能自行选择较宽版本；应在格式转换前取得编辑部书面答复。

## 3. 未列入前三的候选

- `Cybernetics and Information Technologies`：期刊官网当前只列 Web of Science ESCI，不能作为本项目要求的 SCI/SCIE 候选；即使第三方页面给出某个 quartile，也不能覆盖索引类型不符的问题。
- `International Journal on Artificial Intelligence Tools`：主题可能匹配，但 World Scientific 官网被 Cloudflare 阻断，本轮未能从权威页面完整核验当前 SCIE、JCR、费用和篇幅，不纳入已核验前三。
- `Natural Language Engineering`：Cambridge 页面显示该刊现更名为 `Natural Language Processing` 并转为开放获取；本轮未完成当前 APC 和 JCR quartile 的权威闭环，因此不作为当前低预算 Q4 路线的前三。

## 4. 参考文献核验结果

当前论文已把“参考文献候选”改为 17 条编号参考文献，并在正文补入对应编号。核验时严格区分正式同行评审论文、arXiv 预印本和数据资源。

| 编号 | 条目 | 核验结论与稿件处理 |
| ---: | --- | --- |
| [1] | Few-NERD | ACL-IJCNLP 2021 正式论文，页 3198-3213，DOI `10.18653/v1/2021.acl-long.248` |
| [2] | Structured Nearest Neighbor NER | EMNLP 2020 正式论文，页 6365-6375，DOI `10.18653/v1/2020.emnlp-main.516` |
| [3] | Decomposed Meta-Learning for Few-Shot NER | Findings of ACL 2022 正式论文，DOI `10.18653/v1/2022.findings-acl.124`；替换无法核实的旧条目 `Ma et al., 2023, Coarse-to-fine...` |
| [4] | UIE | ACL 2022 正式论文，DOI `10.18653/v1/2022.acl-long.395` |
| [5] | InstructUIE | 仅按 arXiv:2304.08085 预印本引用，不写成正式会议/期刊论文 |
| [6] | GPT-NER | 仅按 arXiv:2304.10428 预印本引用；年份由错误的 2025 修正为 2023 |
| [7] | OneKE | WWW 2025 Companion 正式论文，页 2871-2874，DOI `10.1145/3701716.3715189`；不再使用 2024/2025 模糊年份 |
| [8] | Gazetteer NER | ACL 2019 正式论文，DOI `10.18653/v1/P19-1524` |
| [9] | 原始 RAG | NeurIPS 2020 正式论文，卷 33，页 9459-9474 |
| [10] | Gao RAG Survey | 仅按 arXiv:2312.10997 预印本引用，v1 为 2023、v5 修订于 2024；不附会 ACM DOI |
| [11] | SelfCheckGPT | EMNLP 2023 正式论文，DOI `10.18653/v1/2023.emnlp-main.557` |
| [12] | Chain-of-Verification | Findings of ACL 2024 正式论文，DOI `10.18653/v1/2024.findings-acl.212` |
| [13] | CLUENER2020 | 按 arXiv:2001.04351 预印本引用；不虚构正式出版信息 |
| [14] | DuIE 2.0 | 未找到可可靠对应的正式论文，改按百度千言官方数据压缩包引用，不伪装为同行评审论文 |
| [15] | CMNEE | LREC-COLING 2024 正式论文，页 3367-3379；正文明确其是文档级事件抽取数据集，不是 NER 数据集 |
| [16] | M3-Embedding | Findings of ACL 2024 正式论文，DOI `10.18653/v1/2024.findings-acl.137` |
| [17] | Qwen2.5 Technical Report | 按 arXiv:2412.15115 技术报告/预印本引用；v1 日期为 2024-12，正文参考文献采用 2024，并注明 v2 于 2025 修订 |

特别纠错：`10.1145/3701228` 对应 CRUD-RAG，不是 Gao 等人的 RAG survey，当前论文没有使用该错误 DOI。

`QAonMilitaryKG` 本轮未找到足以锁定论文作者、题名和正式出版信息的稳定权威条目。稿件已把它表述为“项目内记录的 QAonMilitaryKG 种子词典”，不把它伪装为已经核实的学术论文。正式投稿若公开该资源，应另补稳定项目页、版本、许可和访问日期。

## 5. 主要核验入口

- ACL Anthology：<https://aclanthology.org/>
- arXiv：<https://arxiv.org/>
- DBLP OneKE 正式记录：<https://dblp.org/rec/conf/www/LuoRLYS00Z0WZWC25.html>
- NeurIPS 2020 proceedings：<https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html>
- DuIE 2.0 官方数据包：<https://dataset-bj.cdn.bcebos.com/qianyan/DuIE_2_0.zip>

## 6. 投稿前人工门禁

作者需要完成且只有作者/机构订阅能够可靠完成的下一步是：

1. 在机构版 JCR 中逐刊查询准确刊名和 ISSN，记录采用的 JCR 年度、学科类别、rank、quartile 和查询日期。
2. 明确作者单位认定 SCI Q4 时采用“任一类别 Q4”“最低类别 Q4”还是“指定主类别 Q4”的规则。
3. 先确认 JISE；若不满足 Q4 或费用条件，再依次确认 KSII TIIS 和 ComSIS。
4. 向拟投期刊编辑部书面确认当前 APC、超页费和篇幅上限，尤其是 JISE 常规费用及 ComSIS 的冲突页数规则。
5. 目标期刊锁定后，再开一个仅限“英文转换和该刊格式适配”的人工门禁；本步骤不授权英文翻译、LaTeX 转换或新实验。

## 7. 剩余文献风险

- 当前 17 条已完成存在性、题名、年份、出版类型和主要 DOI/URL 核验，但尚未按某一本期刊的最终参考文献样式排版。
- InstructUIE、GPT-NER、Gao RAG survey、CLUENER2020 和 Qwen2.5 Technical Report 属于预印本/技术报告，投稿时应保留这一身份；若目标期刊限制预印本比例，需要再补正式替代文献，而不是改写出版类型。
- DuIE 2.0 目前是数据资源引用；QAonMilitaryKG、FAISS 和 `bge-reranker-v2-m3` 仍需要在目标期刊格式化阶段补稳定软件/模型资源元数据。
- 参考文献真实性修正不增加任何实验支持。RE、CoVe 增益、公开基准泛化、K 扫描稳健性、统计显著性和完整 P5 矩阵仍不受支持。
