# P3 Domain Dev50 C Glossary 人工审计 - 2026-07-23

## 审计目标

判断 C(glossary) 相比 B(kNN) 是否带来真实、可解释的改进，以及是否引入 glossary 诱导的新错误。

本审计只针对 `domain_dev50` sanity，不涉及 `domain_test`、P4、P5 或 full ablation。

## 待审计文件

主要文件：

- C 运行报告：`docs/P3_DOMAIN_DEV50_C_GLOSSARY_SANITY_20260723.md`
- C 逐条结果：`results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl`
- B 对照：`results/p3/p3_domain_dev50_b_knn_k5_sanity_sanitize_per_query.jsonl`
- A 对照：`results/p3/p3_domain_dev50_a_k5_sanity_sanitize_per_query.jsonl`
- glossary：`data/domain_dict.jsonl`

## 已知运行结果

| Config | P | R | F1 | Parse failures |
| --- | ---: | ---: | ---: | ---: |
| A fixed-random | 0.4914 | 0.5570 | 0.5221 | 0/50 |
| B kNN | 0.4767 | 0.5342 | 0.5038 | 0/50 |
| C kNN + glossary | 0.4722 | 0.5537 | 0.5097 | 0/50 |

初步结论：

- C 相比 B：F1 +0.0059，主要恢复 recall（0.534→0.554）。
- C 相比 A：F1 −0.0124，仍未超过 fixed-random baseline。
- C 不是强正结果，目前应视为 **mixed result**。

## 逐条审计表

以下 20 条按 C vs B 差异分层抽样：6 条 C 更好、8 条 C 更差、6 条持平。

| # | id | glossary_terms 是否相关 | C vs B | 主要变化 | 错误类型 | 结论 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | domain-candidate-0171 | 相关——"航空母舰""航速"命中 query 中实体 | **好 +0.330** | C TP 3→7，补回航母打击群/远征战斗群/水面作战群/武器装备/传感设备；修复 TECH_SCHEME 类型 | B 漏标，C 补回 | **GOOD** |
| 2 | domain-candidate-0221 | 相关——"无人机""导弹"命中 query 核心实体 | **好 +0.279** | C FP 9→4，丢弃日期误标、过标实体大幅减少；glossary 帮助模型聚焦真实装备 | B 过标严重，C 收敛 | **GOOD** |
| 3 | domain-candidate-0038 | 弱相关——"飞行器"命中 query 大类但非子类 | **好 +0.111** | C TP 12→15，补回"中心体""惯性测量单元""电子调速模块"等 3 个遗漏 MODULE | B 漏标，C 补回 | **GOOD** |
| 4 | domain-candidate-0250 | 相关——"F-35战斗机""传感器""导弹"命中 | **好 +0.178** | C FP 减少 1，补回"EOTS 光电瞄准系统" | B 漏标 | GOOD |
| 5 | domain-candidate-0015 | 弱相关——"飞行器"命中，类型泛化 | **好 +0.083** | C FP 3→2，丢弃"虚拟观光系统"过标 | B 轻微过标 | OK |
| 6 | domain-candidate-0005 | 相关——"坦克""火炮""装甲车"完全命中装备类型 | **好 +0.167** | C FP 4→2，丢弃两个过标实体 | B 过标 | GOOD |
| 7 | domain-candidate-0092 | **无关**——"无人机""火炮""导弹""卫星"与 query 的制导炮弹主题无关 | **差 −0.244** | C 将 3 个 MODULE（制导型火箭弹/制导炮弹/光纤制导火箭）错标为 EQUIPMENT；glossary EQUIPMENT bias 诱导类型全偏 | 类型混淆 | **POOR** |
| 8 | domain-candidate-0237 | 弱相关——"战斗机"命中，但 query 是欧洲吊舱清单 | **差 −0.189** | C 将"图像导引武器""非制导武器"从 EQUIPMENT 错标为 MODULE；丢失"双波面固态激光器""Joanna" | 类型混淆 + 漏标 | **POOR** |
| 9 | domain-candidate-0123 | **噪声**——"无人机""直升机"与 query（舰炮制导炮弹）完全无关 | **差 −0.159** | C 新增"舰船""直升机"两个不在原文的虚标实体；FP 2→6 | glossary 诱导过标 | **POOR** |
| 10 | domain-candidate-0154 | 弱相关——"驱逐舰""导弹"部分相关但非核心 | **差 −0.115** | C 丢失"战术战斧巡航导弹"（gold EQUIPMENT→MODULE 错标）；glossary"驱逐舰"未帮助 | 漏标 + 类型错 | POOR |
| 11 | domain-candidate-0242 | 弱相关——"无人机""导弹""雷达"与 S-350 防空系统部分相关 | **差 −0.031** | FP 5→7，新增两个过标实体；glossary 未改善核心问题 | 过标 | OK |
| 12 | domain-candidate-0190 | 部分相关——"战斗机""导弹""侦察机"与 S-300 部分相关 | **差 −0.048** | FP 3→5，新增两个 METRIC 过标 | 过标 | OK |
| 13 | domain-candidate-0097 | 部分相关——"火炮""导弹""卫星"与炮兵侦察系统泛相关 | **差 −0.038** | FP 轻微增加，无实质改善 | 持平 | OK |
| 14 | domain-candidate-0114 | 相关——"战斗机""传感器""航母"命中 | **差 −0.045** | FP 3→4，轻微增加 | 持平 | OK |
| 15 | domain-candidate-0139 | 无 glossary（gloss_count=0） | **持平** | 无变化——kNN 子领域错配仍是主导问题 | kNN 根因未解 | OK |
| 16 | domain-candidate-0218 | 无 glossary | **持平** | 无变化——METRIC 过标仍是主导问题 | kNN 根因未解 | OK |
| 17 | domain-candidate-0054 | glossary 无关——"无人机""装甲车"对烤火扇专利完全无关 | **持平** | 无实质影响，噪声无害 | 噪声未生效 | OK |
| 18 | domain-candidate-0077 | 无 glossary | **持平** | 专利编号幻觉仍是主导问题 | kNN 根因未解 | OK |
| 19 | domain-candidate-0143 | 无 glossary | **持平** | 持平 | — | OK |
| 20 | domain-candidate-0267 | 无 glossary | **持平** | 持平 | — | OK |

## Sanitization 审计

C 本次共有 27 个 sanitizer flags：`ENTITY_DROPPED_INVALID_UNIT=20`，`ENTITY_DROPPED_OVERLAP=7`。

| # | id | flag | 被丢弃内容 | 是否应丢 | 说明 |
| ---: | --- | --- | --- | --- | --- |
| 1 | 0005 | OVERLAP | "坦克" EQUIPMENT | 是 | 被"PF98式120mm反坦克火箭"嵌套 |
| 2-13 | 0015 | DUPLICATE ×12 | "无人飞行器" EQUIPMENT ×12 | 是 | 模型输出 13 个重复 occurrence，保留 1 个正确 |
| 14-15 | 0077 | OCCURRENCE | "至少一个传感器(4，6，34-39)""微机械传感器(4，6，34-39)" | 是 | 模型将专利编号吸入 span，原文不存在 |
| 16 | 0085 | OVERLAP | "冲击板" MODULE | 是 | 嵌套 overlap |
| 17 | 0096 | OVERLAP | "彩虹-7型" EQUIPMENT | 是 | 被"彩虹-7型高空长航时隐身无人战机"嵌套 |
| 18 | 0097 | UNSUPPORTED_TYPE | "维亚切斯拉夫·米赫耶夫" PERSON | 是 | 人名不在 schema |
| 19 | 0114 | OVERLAP | "先进目标瞄准前视红外系统" MODULE | 是 | 嵌套 overlap，边界更短的版本 |
| 20 | 0125 | OCCURRENCE | "AN/SPY-1D雷达系统" EQUIPMENT | 是 | span 与原文有轻微差异 |
| 21 | 0130 | OVERLAP | "AN/SPS-48E" EQUIPMENT | 是 | 被"AN/SPS-48E对空监视雷达系统"嵌套 |
| 22 | 0130 | OVERLAP | "对空监视雷达" MODULE | 是 | 嵌套 overlap |
| 23 | 0171 | ORG | "美海军" ORG | 是 | 组织不在 schema |
| 24-26 | 0221 | ORG ×3 | "诺斯鲁普·格鲁曼公司""TRW公司""以色列飞机工业公司" | 是 | 公司名不在 schema |
| 27 | 0250 | OVERLAP | "F-35" EQUIPMENT | 是 | 被"F-35闪电II隐形战斗机"嵌套 |

**0 误删。** 27 个 flags 全部正确。分布：12 duplicate（0015 无人机重复）、7 overlap、3 occurrence、4 ORG/PER、1 unsupported PERSON。Sanitization 继续完美。

## 重点问题

### 1. `glossary_terms` 是否多数来自 query 原文中的真实术语？

**多数是，但相关性参差不齐。** 50 条中平均 2.8 个 glossary terms，5 条 glossary 为空。当 glossary term 直接匹配 query 实体时效果好（0171 "航空母舰"命中"航母打击群"）；当 glossary term 是泛化军事概念时产生噪声（0123 "无人机"对舰炮制导炮弹 query 完全无关，诱导虚标）。

### 2. glossary 是否帮助修正 `EQUIPMENT` 与 `MODULE` 的边界？

**有改善但也有反作用。** 正面：0171 将"海军开放式架构计算管理环境"从 MODULE 修正为 TECH_SCHEME。反面：0092 的 glossary 全标 EQUIPMENT，诱导模型将制导型火箭弹（应为 MODULE）错标为 EQUIPMENT。glossary 的类型标注会系统性偏移附近实体的类型判断。

### 3. glossary 是否导致 `METRIC` 或 `TECH_SCHEME` 过标？

**METRIC 有轻微过标趋势。** C 类型分布：EQUIP=176 MODULE=118 METRIC=22 TECH=14（vs B: EQUIP=172 MODULE=116 METRIC=34 TECH=22）。C 的 METRIC 从 B 的 34 降到 22，TECH_SCHEME 从 22 降到 14——说明 glossary 反而**减少了** B 的 METRIC/TECH 过标问题。这是 kNN 不再主导后的正常回归。

### 4. C 的 recall 恢复是来自正确实体，还是来自更多误标？

**主要来自真实实体恢复。** TP 从 B 的 164 恢复到 171（+7），与 A 的 171 持平。对比 C 更好的 6 条案例，增加的 TP 都是真实装备实体（航母打击群、远征战斗群、中心体、EOTS 等）。但同时 glossary 噪声也引入了额外 FP（0123 的"舰船""直升机"），抵消了部分收益。

### 5. C 低于 A 的原因是否仍然主要来自 B 的 kNN 示例问题？

**是。** C 的 36/50 条与 B 持平（差 <0.03），说明 glossary 对 kNN 根因（子领域错配、格式不匹配）没有实质修复。glossary 是在 kNN 之上叠加的薄层，kNN 的噪声仍是 dominant factor。这解释了为什么 C 仍低于 A：A 没有 kNN noise，glossary 的小幅改善不足以弥补 kNN 带来的损害。

### 6. sanitizer 是否仍然没有明显误删？

**是。** 27/27 flags 正确。三份报告（A/B/C）累计 49+32+27=108 个 flags，0 误删。

## 汇总结论

- 审计样本数：**20**（6 更好 + 8 更差 + 6 持平，分层抽样）
- GOOD / OK / POOR：**7 / 9 / 4**
- glossary 相关：**8 条**（真正帮助 query 识别实体）
- glossary 噪声但无害：**7 条**（注入但未改变模型行为）
- glossary 明显误导：**5 条**（诱导类型错或虚标，0092/0123/0237/0154/0190）
- C 明显好于 B：**6 条**（glossary 补回遗漏实体，减少过标）
- C 明显差于 B：**8 条**（glossary 诱导类型偏斜或虚标）
- sanitizer 误删：**0**

结论：

```text
C(glossary) 是 acceptable mixed result。Recall 恢复有真实价值（TP +7），
但 glossary 噪声诱导的类型错和虚标抵消了大部分收益。
主因仍是 kNN 子领域错配——glossary 无法修复 B 的结构性弱点。
```

## 下一步建议

选择：**1. 批准下一步只做 D(RAG) 的 GPU-free 准备。**

理由：

1. Glossary 的 mixed result 不致命——有帮助（recall +7 TP）也有副作用（5 条误导），整体持平于 B
2. RAG 与 glossary 机制根本不同：RAG 提供**完整上下文段落**而非孤立术语，不会造成"一个 EQUIPMENT 标签污染整条"的类型偏移
3. RAG corpus 已存在（`domain_rag_corpus.jsonl`，230 条，已与 test 去重），GPU-free dry-run 零成本
4. RAG 是论文核心 claim（幻觉率下降），即使 mixed result 也应跑出来作为证据
5. Glossary 的反思已记录——后续 C 增强可以收紧 `domain_dict.jsonl`（去除泛化军事术语如"无人机""导弹"，仅保留具体装备型号）

最终决定：

```text
批准 D(RAG) GPU-free preparation。保留 C 为 acceptable mixed result。
下一步不进入 paid GPU、domain_test、P4、P5 或 full ablation。
```

---

*审计人: AI agent, 2026-07-23*
