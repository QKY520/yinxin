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

- C 相比 B：F1 +0.0059，主要恢复 recall。
- C 相比 A：F1 -0.0124，仍未超过 fixed-random baseline。
- C 不是强正结果，目前应视为 mixed result。

## 审计抽样建议

建议审计 20 条左右：

| 样本组 | 数量 | 目的 |
| --- | ---: | --- |
| C 明显好于 B | 5 | 判断 glossary 是否真的补回正确实体 |
| C 明显差于 B | 5 | 判断 glossary 是否诱导误标 |
| glossary_terms 多的样本 | 5 | 检查术语注入是否过强 |
| METRIC / TECH_SCHEME 较多样本 | 5 | 检查指标和技术体制是否过标 |
| glossary_terms 为空样本 | 可选 5 | 确认其表现应接近 B |

## 逐条审计表

| # | id | glossary_terms 是否相关 | C vs B | 主要变化 | 错误类型 | 结论 |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 2 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 3 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 4 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 5 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 6 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 7 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 8 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 9 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 10 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 11 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 12 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 13 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 14 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 15 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 16 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 17 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 18 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 19 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |
| 20 |  | 相关 / 噪声 / 误导 | 好 / 持平 / 差 |  | 边界 / 类型 / 漏标 / 过标 / occurrence | GOOD / OK / POOR |

## Sanitization 审计

C 本次共有 27 个 sanitizer flags：

| Flag | Count |
| --- | ---: |
| `ENTITY_DROPPED_INVALID_UNIT` | 20 |
| `ENTITY_DROPPED_OVERLAP` | 7 |

抽查建议：至少看 10 个 flags。

| # | id | flag | 被丢弃内容 | 是否应丢 | 说明 |
| ---: | --- | --- | --- | --- | --- |
| 1 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 2 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 3 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 4 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 5 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 6 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 7 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 8 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 9 |  |  |  | 是 / 否 / 可惜但合理 |  |
| 10 |  |  |  | 是 / 否 / 可惜但合理 |  |

## 重点问题

审计时优先回答下面几个问题：

1. `glossary_terms` 是否多数来自 query 原文中的真实术语？
2. glossary 是否帮助修正 `EQUIPMENT` 与 `MODULE` 的边界？
3. glossary 是否导致 `METRIC` 或 `TECH_SCHEME` 过标？
4. C 的 recall 恢复是来自正确实体，还是来自更多误标？
5. C 低于 A 的原因是否仍然主要来自 B 的 kNN 示例问题？
6. sanitizer 是否仍然没有明显误删？

## 汇总结论

请填：

- 审计样本数：
- GOOD / OK / POOR：
- glossary 相关：
- glossary 噪声但无害：
- glossary 明显误导：
- C 明显好于 B：
- C 明显差于 B：
- sanitizer 误删：

结论：

```text
待填写：C(glossary) 是 acceptable mixed result / harmful / promising。
```

## 下一步建议

请选择其一：

1. 如果 glossary 多数相关、误导少：批准下一步只做 D(RAG) 的 GPU-free 准备。
2. 如果 glossary 明显诱导 `METRIC/TECH_SCHEME` 过标：先收紧 `data/domain_dict.jsonl`，再重新 C dry-run 或小跑 C。
3. 如果 C 明显没有价值：保留 C 为 mixed/negative result，暂停增强路线，先分析 A 为什么更稳。

最终决定：

```text
待填写。
```
