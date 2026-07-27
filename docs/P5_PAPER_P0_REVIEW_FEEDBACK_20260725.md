# P5 Paper Draft — P0 Fixes 版审稿意见

Date: 2026-07-25

> **历史审计说明（2026-07-27）：** 下列审计对象 DOCX 已按用户要求删除。
> 本文件仅保留审稿与修改依据，不是可编辑论文版本。当前唯一论文正文为
> `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`。

审计对象: `docs/EQUIPMENT_IE_PAPER_DRAFT_WITH_P0_FIXES_20260725.docx`

---

## 一、题目

**当前**：偏学术报告化，"消融研究"是方法论标签而非论文卖点。Q4 应用期刊审稿人想看的是解决了什么实际问题。

**三个备选方向**：

| 方向 | 示例 | 适合期刊 |
|------|------|----------|
| 强调 FP 减少 | *Reducing False-Positive Entity Predictions in Few-Shot Equipment-Domain Chinese NER via Retrieval-Augmented Generation* | 工程应用（*Applied Sciences*, *Electronics*） |
| 强调低标注 | *Few-Shot Named Entity Recognition for Chinese Equipment Texts: When kNN Demonstrations Meet Retrieval-Augmented Generation* | 低资源 NLP 方向 |
| 强调可复现 pipeline | *A Reproducible Few-Shot Pipeline for Chinese Equipment-Domain NER: Ablation Evidence from kNN, Glossary, and RAG Modules* | 强调可复现性的工程期刊 |

**推荐第一个**。"Reducing False-Positive"是论文最独特的贡献（D 区别于 C 的核心），放进题目让审稿人一眼看到 contribution 不是刷 F1。

---

## 二、摘要

**当前问题**：太像实验报告。"kNN 提 F1 0.0205，glossary 提 recall 0.0255，RAG 降 FP 55"——这些数字在摘要中过于细粒度。摘要不是 results section 的浓缩版。

**建议四句式结构**：

```
句1 (Problem):
  "Few-shot NER in specialized Chinese domains such as military
  equipment suffers from two bottlenecks: scarce labeled data and
  entity-level false-positive predictions from LLM-based extractors."

句2 (Method):
  "We compare four few-shot configurations on a self-built 170-record
  equipment test set — fixed-random examples (A), kNN retrieval (B),
  glossary injection (C), and RAG-augmented extraction (D) — using
  Qwen2.5-7B-Instruct under a unified schema."

句3 (Results):
  "kNN improves F1 by 2.1 points over the fixed-random baseline;
  glossary adds 1.4 points through recall; RAG preserves F1 within
  a near-tie while reducing false-positive entity predictions by 55
  (9.4%) compared to the best-F1 configuration."

句4 (Significance):
  "These results show that RAG is a practical, precision-oriented
  module for low-label domain NER, and that simply maximizing F1 may
  overlook the value of cleaner model outputs in high-stakes
  equipment-domain applications."
```

数字细节（0.0205、0.0255、0.0031、584→529）应移到 Results，摘要中保留方向和量级。

---

## 三、引言

**当前问题**：动机段写了"低标注"和"装备领域"，但说服力不够。读起来像"因为低资源 NER 是个研究方向，所以我们做了"——缺少一个具体的、让读者点头的应用场景。

**建议在引言第一段加入具象化场景**（3-4 句）：

```text
"Consider an intelligence analyst processing Chinese military-
technical documents. Manually annotating every equipment name,
component, and specification across thousands of passages is
prohibitively expensive. A few-shot NER system trained on only 30
annotated examples can extract entities, but LLM-based extractors
often produce false positives — labeling an organization name as
EQUIPMENT, or treating a descriptive phrase as a MODULE. These
false positives erode analyst trust and create downstream cleanup
work. This paper asks: can retrieval-augmented generation reduce
such false-positive predictions without sacrificing extraction F1?"
```

这个场景直接锚定三个要素：（1）为什么是装备领域；（2）为什么需要小样本；（3）为什么 FP 减少是实际需求。

---

## 四、相关工作

**当前状态**：从 v1 的 5 个子节压缩为单个 Section 2，比 v1 紧凑。

**建议调整**：

| 当前引用 | 建议 | 理由 |
|----------|------|------|
| Few-NERD, structured NN, coarse-to-fine | **保留但精简**为 1 句 | 与装备领域距离远，仅作为"few-shot NER exists"的背景 |
| UIE, InstructUIE | **可删** | 本文不是 instruction-tuned model，与 UIE 线差异太大 |
| GPT-NER, OneKE | **保留** | LLM-based NER 的 hallucination 问题是本文出发点 |
| Gazetteer NER (Liu 2019, etc.) | **保留并展开** | C 的直接前身。加 1 句"unlike static gazetteers, our glossary is dynamically matched per query" |
| RAG survey, SelfCheckGPT, CoVe | **保留** | D 的理论基础。加 1 句"we test whether RAG's claimed hallucination benefit transfers to few-shot domain NER" |
| CLUENER, DuIE, Few-NERD, CMNEE | **精简**为 1 句 | 仅作为"no existing Chinese equipment NER benchmark exists"的引证 |

**核心原则**：Section 2 应从"这个领域有哪些工作"转向"这些工作与本文的差异是什么"。每个引用后面跟半句 differentiation。

---

## 五、结果与讨论

**当前状态**：Section 6 narrative 诚实。Section 6.1 的 FP 分析表（84/34/25/24/14）是 P0 最大的增值。

**三个微调**：

### 5a. C/D near-tie 的措辞

当前措辞偏被动："D 相比 C F1 差 0.0031，属于 near-tie"。

```text
建议改为：
"D and C achieve near-identical F1 (0.5658 vs 0.5689, Δ = 0.0031),
yet D removes 55 false-positive entity predictions that C retains.
This trade-off — marginal F1 for cleaner output — is the central
practical finding of this study."
```

这样 RAG 读起来不像"失败了"，而是"做了不同的事情"。

### 5b. FP 分析表需确认语义方向

Section 6.1 表头为"类别"和"数量"，按 84/34/25/24/14 分类。**需确认统计方向**：

- 如果统计的是 **"D 比 C 多删掉的 FP"**：84 个 exact gold match 被删意味着 D 误杀了 gold 实体——这是严重问题，必须如实写
- 如果统计的是 **"D 删掉的 FP 按与 gold 的关系分类"**：84 个 exact gold match 说明 D 在删除 FP 的同时也误删了 gold 实体——需要在论文中明确标注 "84 entities matched gold but were removed by the RAG evidence block — the primary failure mode of D"

**建议**：在表下方加一行注释，明确表统计的是 "C 有但 D 没有的 predicted entities, categorized by their relationship to gold"。如果是误删，诚实写出来——这反而让论文更可信。

### 5c. 方差异常

Table 6 脚注已加，保留。这句脚注非常关键，目前措辞合理。

---

## 六、总体评价

| 维度 | v1 | v2 (P0 fixes) | 仍需改进 |
|------|-----|---------------|----------|
| 题目 | 含内部代号 | 偏学术报告 | **改应用导向** |
| 摘要 | 像实验报告 | 改善但仍像 | **四句式重构** |
| 引言 | 动机偏弱 | 未变 | **加应用场景** |
| 相关工作 | 5 节偏冗长 | 压缩为 1 节 | **每引用加 differentiation** |
| 结果与讨论 | 诚实但被动 | 加了 FP 分析表 | **near-tie 积极化 + 确认 FP 表语义** |

**五处修改均为文字层面，0 GPU 费。改完后即可定位目标期刊、写全文草稿。**

---

## 七、投稿前待确认清单

- [ ] 题目改为应用导向（推荐 "Reducing False-Positive..." 方向）
- [ ] 摘要改为 Problem-Method-Results-Significance 四句式
- [ ] 引言第一段加入具象化应用场景
- [ ] 相关工作每引用加 differentiation 半句
- [ ] Section 6 near-tie 措辞积极化（"trade-off marginal F1 for cleaner output"）
- [ ] Section 6.1 FP 分析表语义确认并加注释
- [ ] Section 6 方差脚注保留
- [ ] 全文检查 D1-D6 删除的 claim 是否已清理干净
- [ ] 全文检查无 "P5""A/B/C/D""domain_test" 等内部代号

---

*审稿人: AI agent, 2026-07-25*
