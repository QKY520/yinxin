# P5 Paper Draft — SCI Q4 Review Audit

Date: 2026-07-25

> **历史审计说明（2026-07-27）：** 下列审计对象 DOCX 已按用户要求删除。
> 本文件仅保留审稿与修改依据，不是可编辑论文版本。当前唯一论文正文为
> `docs/EQUIPMENT_IE_PAPER_DRAFT_V3_REVIEW_POLISH_20260725.md`。

审计对象: `docs/EQUIPMENT_IE_PAPER_DRAFT_WITH_RELATED_WORK_20260725.docx`
参照: `docs/P5_DOMAIN_REPLICATION_20260724.md`（三 seed 结果）

---

## 一、论文结构评估

| 章节 | 状态 | 主要问题 |
|------|------|----------|
| Title | ⚠️ 需改 | 含项目内部代号 "P5 domain A/B/C/D"，正式投稿须替换 |
| Abstract | ✅ | Story line 清晰：kNN 提 F1，glossary 提 recall，RAG 降 FP |
| Introduction | ✅ | 贡献声明可，未夸大 |
| Related Work | ✅ | 覆盖核心领域，对 Q4 足够 |
| Method | ✅ | 四 config 描述准确，A→B→C→D 消融链清晰 |
| Results | ⚠️ 缺解释 | 方差异常（A 大 B/C/D 极小）未说明 |
| Discussion | ✅ | 诚实，未硬吹 RAG |
| Limitations | ✅ | 写了 K-scan 缺失、RE 缺失、verification 未进 P5 |
| Conclusion | ✅ | 与 evidence 一致 |
| References | ✅ | 覆盖面够，CMNEE 引用年份需核实 |

---

## 二、Related Work 分层评估

| 子节 | 与本文距离 | 评价 |
|------|-----------|------|
| 2.1 Few-shot NER | 背景 | 偏泛。建议补中文 few-shot NER 工作或精简 |
| 2.2 LLM-based IE | 方法背景 | GPT-NER、OneKE 直接相关，保留 |
| 2.3 Gazetteer/Domain NER | **核心** | C 的直接前身。需展开差异 |
| 2.4 RAG + Hallucination | **核心** | 覆盖面好。需解释为什么最终未用 CoVe |
| 2.5 Benchmarks | 背景 | 必要。CMNEE 引用年份核实 |

---

## 三、Results 诚实度检查

| 声称 | 数据 | 诚实？ |
|------|------|--------|
| B > A, kNN 提 F1 | +0.0205 F1, −39.7 FP | ✅ |
| C > B, glossary 提 recall | +0.0255 recall, FP +10.3 | ✅ 诚实写了 FP 反升 |
| C/D F1 near-tie | ΔF1 = 0.0031 | ✅ |
| D 降 FP | −55 FP vs C, precision 最高 | ✅ |
| 未涉及 verification | E/E-prime 未跑，Limitation 写了 | ✅ |
| 未涉及 RE | NER-only，Limitation 写了 | ✅ |

**需修正的技术项**：

Table 6 中 B/C/D 标准差极小（0.0002-0.0012），A 大 10-25 倍（0.0044-0.0289）。C/D 使用 `knn_replay` 回放 B 的示例 ID，导致 3 seed 间示例相同。必须在论文中解释——否则审稿人会质疑 "为什么加模块后方差归零"。

```text
建议脚注：
"B/C/D use the same kNN example IDs across seeds (knn_replay for C
and D), so their reported variance reflects only model-generation
noise. A's variance additionally includes fixed-random example-
selection noise."
```

---

## 四、Claims 审计

### 4.1 有证据的 Claim（8 条，保留）

| # | Claim | 证据 | 强度 |
|---|-------|------|------|
| C1 | kNN examples improve few-shot NER F1 over fixed-random baseline | B−A = +0.0205 F1, −39.7 FP, 3 seeds | 强 |
| C2 | Glossary injection improves recall (+0.0255) and F1 (+0.0137) over kNN alone | C−B, 3 seeds | 中强（FP 反升 +10.3 需诚实写） |
| C3 | RAG reduces false-positive entity predictions while preserving near-tied F1 | D−C = −55 FP, F1 Δ = −0.0031, precision +0.0137 | 中强 |
| C4 | The A/B/C/D ablation design isolates one factor per config jump | diff 干净，knn_replay 锁定示例 | 强 |
| C5 | kNN contributes the largest single-module F1 gain | B-A +0.0205 > C-B +0.0137 > D-C −0.0031 | 强 |
| C6 | A fixed-random K=5 baseline achieves usable few-shot NER on domain test | F1=0.5346, 0 parse failures, 170 test | 中强 |
| C7 | Self-built equipment-domain dataset supports reproducible ablation | support=30/dev=50/test=170, 3 seeds, FROZEN | 强 |
| C8 | Qwen2.5-7B + vLLM as reproducible local-model baseline | all runs 0 parse failure, 3 seeds | 中强 |

### 4.2 必须删除或重写的 Claim（6 条）

| # | 当前问题 | 根因 | 处理 |
|---|---------|------|------|
| D1 | 任何 "RAG improved F1" 的措辞 | D−C F1 = **−0.0031**，不是正数 | 改为 "RAG preserved F1 while reducing FP" |
| D2 | 任何暗示 verification/CoVe 有效的 claim | E/E-prime **未进入 P5**，dev 上为 negative | 删掉 claim。Discussion 可提一句 "preliminary dev experiments showed over-deletion; further work needed" |
| D3 | 任何 "RAG + verification 联合降低 hallucination" 的 claim | 联合效果没测 | **删掉。** 这是最想 claim 但缺少证据的东西 |
| D4 | 任何暗示 RE 结果的 claim | P5 全 NER-only | 删掉。Limitation 已写 |
| D5 | 任何暗示 CLUENER 或 public benchmark 比较的 claim | 没跑 | 删掉。Limitation 已写 |
| D6 | "RAG significantly reduces hallucination" | 55 FP 减少是 entity-level FP，不是 open-domain hallucination | 改为 "reduces entity-level false-positive predictions" |

---

## 五、可选补实验（按性价比排序）

| 优先级 | 实验 | GPU 费 | 价值 | 说明 |
|--------|------|--------|------|------|
| **P0** | 定性 FP 分析 | **0 CNY** | 高 | 从 D per-query 抽 20 条，做表：D 删掉的 C 的 FP 按类型分布（ORG/描述性短语/边界错/地名） |
| **P0** | 方差异常解释 | **0 CNY** | 高 | Table 6 加脚注或 Section 5 加段落 |
| **P1** | K-scan: A/D K=1/10, 3 seeds | **~3-5 CNY** | 中 | 12 cell × 170 query, ~1-2 GPU时 |
| **P2** | CLUENER validation: A/D K=5, 3 seeds | **~8-14 CNY** | 中 | 需先确认 gold-bearing split |
| **P3** | 单行 E v3 negative verification | **~1-2 CNY** | 低 | 大概率仍 negative，仅作定性证据 |
| 不推荐 | RE on domain_test | 高 | 低 | RE 是 auxiliary，主证据线不依赖 |

### 最省钱方案（总预算 <5 CNY）

1. **定性 FP 分析**（0 CNY）：写脚本对比 D vs C per-query，分类 D 删掉的 FP 实体。20 分钟。
2. **方差脚注**（0 CNY）：论文 Table 6 下加一行注释。5 分钟。
3. **K-scan**（~3-5 CNY）：domain A/D K=1/10，3 seeds，12 cell。

**三项合计 ≤5 CNY，从 "borderline-sufficient" 提升到 "solid for Q4"。**

---

## 六、总体判断

| 维度 | 评级 | 说明 |
|------|------|------|
| 题目/摘要 | ✅ 可接受 | 去掉内部代号即可，方向对 |
| Related Work | ✅ 可接受 | 覆盖面够，核心子节需加强 differentiation |
| Results 诚实度 | ✅ 通过 | 无夸大，near-tie 表述恰当 |
| Claims 证据 | ⚠️ 6 条需删/改 | 主要是 scope 边界和措辞精确度 |
| 实验充分度 | ⚠️ borderline | 补 P0 两项（0 CNY）后足够 Q4 |

**一句话**：论文的 claim 骨架诚实，没有捏造数据。当前 domain-only 3-seed 消融证据对 SCI Q4 应用论文基本够用。补两处零 GPU 费的文本修改（方差解释 + 定性 FP 分析）后可以开始写全文草稿。CLUENER 和 K-scan 如预算允许再补，不阻塞投稿。

---

*审计人: AI agent, 2026-07-25*
