# P6-QA2 双盲标注提交验证报告

日期：2026-07-26

结论：`blocked`。本轮提交不能形成 human IAA，不能进入裁决、`v2` 冻结或结果重评。

## 1. 门禁范围

本轮仅在 AutoDL GPU-free 模式下读取：

- QA0 的 A/B 空白表和 coordinator-only blind-ID map；
- 本轮提交的 `annotator_a_completed.csv`、`annotator_b_completed.csv`。

未读取旧 frozen gold、A/B/C/D 预测、prompt 或实验结果；未启动 vLLM、模型、
dry-run 或 paid GPU；未修改、排序、补全或裁决任何标签。

输入 completed 文件 SHA256：

- A：`f07a650688c9cafcf4d16f5be906a0f45a3623838994cc9af2954385eb2183b7`
- B：`90e8e2458de3dd1f847a730759a353efb0a493bbbe385bbaa88fecf6acccd8ef`

## 2. Provenance 审计

仓库根目录存在两个未跟踪的标注生成脚本，均保持原样且未被 QA2 执行：

- `p6_complete_annotate.py`：
  `f0a801d4beec90672000eafebf0832726d5f6931ad3451be0fd416153ae95df2`
- `p6_annotate_complete.py`：
  `1101f5ca14b625007ed0bf706affb266578daec5c9cf7fc3d23abf8a5180fcc6`

其中 `p6_complete_annotate.py` 明确读取 A/B 两份 QA0 空白表，以同一个 `ANNO`
字典和同一个 `process_rows` 函数生成两套标签，并写入本轮同名 completed 文件。
即便 B 文件此后有人工修改，两位标注者也没有从相互独立的空白起点开始。因此：

- shared-script 输出不能充当两个真人独立标注；
- 文件间一致度不能命名为 human IAA；
- 修补当前文件不能追溯性恢复独立性；
- `formal_human_iaa` 必须保持 `null`。

这是 provenance 阻塞，不是单纯的 CSV 格式问题。

## 3. 结构验证

blind ID、170 行文本和 text SHA256 均能与 QA0 map 全量回环，但标签字段未通过：

| 问题 | A | B | 合计 | 判定 |
| --- | ---: | ---: | ---: | --- |
| `ENTITIES_NOT_SORTED` | 19 行 | 0 | 19 | hard error |
| `EMPTY_ENTITIES_FIELD` | 0 | 2 行 | 2 | hard error；空白不能当 `[]` |
| `REPEATED_MENTION_UNRESOLVED` | 180 项/59 行 | 1 项/1 行 | 181 | blocking human review |

总计 21 个 hard errors、181 个 blocking reviews。按严格结构门，仅 149/170 对可进入
诊断性 exact-set 比较。验证器没有对这些问题做静默修复。

## 4. 文件级诊断一致度

以下仅为 149 对严格有效文件的 diagnostic concordance，不是 human IAA：

| 指标 | 值 |
| --- | ---: |
| A 实体数 | 824 |
| B 实体数 | 931 |
| exact `(start,end,type)` matches | 489 |
| B-vs-A precision | 0.5252 |
| B-vs-A recall | 0.5934 |
| exact F1 | 0.5573 |
| 完全一致行 | 19/149 (0.1275) |
| 含差异行 | 130/149 |

分类别诊断：

| 类型 | A/B 数量 | exact matches | F1 |
| --- | ---: | ---: | ---: |
| `EQUIPMENT` | 586/535 | 362 | 0.6459 |
| `MODULE` | 220/232 | 124 | 0.5487 |
| `TECH_SCHEME` | 18/164 | 3 | 0.0330 |
| `METRIC` | 0/0 | 0 | 不可解释的空类，不得写成 1.0 一致性 |

诊断 F1 低于硬门 0.80，也低于建议投稿目标 0.85。`TECH_SCHEME` 的数量差异表明
两套文件对 schema 的理解极不一致；`METRIC` 在有效子集中完全为空，不能据此宣称
该类型取得一致标注。

## 5. 产物与复核

远端 coordinator-only 目录：

`/root/autodl-tmp/backup/p6/p6_qa2_annotation_validation_20260726/`

本地忽略备份：

`backups/P6/p6_qa2_annotation_validation_20260726/`

输出 SHA256：

- `validation_report.json`：
  `aa614ad12cf9b7babf0ebb0e950ec44b960cb259226027142c7a0180acef6292`
- `issues.csv`：
  `c66181a7af82e796d2bb2de00c872c438a1ac1ee47c19eec8b3097658f746e18`
- `disagreements.jsonl`：
  `19192b8880dc3acadd2312cb63afd41b2b0048619f621f6cd237f7f2910ada5c`
- `manifest.json`：
  `55e9829d4a8588fea07186606d07f56557519c7fbea7430a64aad5285ac00d07`

4 项聚焦单元测试在 AutoDL GPU-free 模式下全部通过。远端和本地报告哈希一致，
生成后服务器仍为无卡状态。本轮 paid-GPU 成本为 0 CNY。

## 6. 门禁裁决与下一步

P6-QA2：`blocked`。

禁止继续：

- 不得把 `0.5573` 或任何当前文件指标写成 human IAA；
- 不得自动修复后进入裁决；
- 不得生成 `domain_test_v2.jsonl`、重评分或修改论文 gold 质量声明；
- 不得删除本次负面产物或两个 provenance 脚本。

要恢复“真人双标数据集”路线，必须由两名真实人类重新从原 QA0 空白表独立标注，
双方都不得看到当前 completed 文件、共享脚本、旧 gold、预测或对方结果。建议下一
门禁命名为：

```text
P6_QA1R_TRUE_HUMAN_REANNOTATION_APPROVED
```

若无法安排两名真人，只能改为“单人/专家审查的机器辅助数据集”并删除 human IAA
和高质量双标数据集贡献，此路线的 SCI-Q4 审稿风险明显更高。
