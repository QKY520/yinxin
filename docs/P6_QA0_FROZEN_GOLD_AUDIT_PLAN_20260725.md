# P6-QA0 冻结 gold 双人盲审方案

日期：2026-07-25

状态：`P6-QA0` 已完成；尚未开始人工标注、IAA 计算、裁决或重评实验。

## 1. 审计目的与证据问题

本审计针对冻结 `domain_test.jsonl` 的 gold 质量，不修改既有冻结文件。旧 P2
材料中的 `0.9909` 实体一致性 F1 来自机器/规则生成的伪 A/B 标注，不能作为两名
真人独立标注的一致性证据。当前 170 条 test 的 prior label provenance 也同时包含
名义上的双标裁决来源与单人来源。因此，投稿前必须用两名真人从空白文本独立复核
全部 170 条 NER 标注，才能决定是否建立版本化的 corrected gold `v2`。

coordinator map 复核确认 test provenance 为：名义
`adjudicated_double_annotation` 61 条、`annotator_a_single_annotation` 109 条。
这里的字段名只描述旧流程分支，不等于已经取得真人双标证据。

本步骤只解决“如何盲审”与“材料是否不泄漏”两个问题。它不把旧 gold 判为错误，
也不授权改数据、看模型预测后修 gold，或重算任何论文结果。

## 2. P6-QA0 允许范围

- 输入：冻结 test 文本、`FROZEN` 标记和 coordinator-only source map。
- 输出：A/B 两份空白盲表、coordinator-only blind-ID map 和生成 manifest。
- 任务：仅 NER；关系标注不在本门禁范围内。
- 算力：AutoDL 无卡模式；不加载模型，不启动 vLLM，不执行 dry-run。
- 数据保护：旧 `domain_test.jsonl`、source map 和 `FROZEN` 只读，禁止覆盖。

标注者 CSV 只允许四列：

```text
blind_id,text,entities_json,notes
```

严禁向标注者展示 original ID、旧实体/关系、预测、机器建议、prompt、标题、来源
元数据、blind-ID map 或另一位标注者的结果。A/B 使用不同 deterministic seed、不同
顺序和不同 blind ID。协调员不得把含映射的整个备份目录直接发给标注者。

## 3. 下一门禁中的真人标注协议

只有负责人明确批准 `P6_QA1_HUMAN_ANNOTATION_START_APPROVED` 后，才可开始：

1. 两名真实人类标注者各自领取一份 CSV，独立完成全部 170 条，不讨论个案。
2. `entities_json` 填写 JSON 数组；单实体格式为：

```json
{"start":0,"end":4,"type":"EQUIPMENT","span":"..."}
```

3. 合法类型仅为 `EQUIPMENT`、`MODULE`、`TECH_SCHEME`、`METRIC`。
4. `start`/`end` 使用 Python 字符偏移，`end` 为右开区间，必须满足
   `text[start:end] == span`。
5. 同一实体每次显式出现都必须分别标注；代词和省略成分不标。
6. 默认禁止嵌套或重叠；保留语义完整边界。无法确定时在 `notes` 中说明，不猜测。
7. 本轮不填写关系。Agent 不能代替真人标注者或真人裁决者，却在论文中声称
   human gold / human adjudication。

## 4. 回收后的结构质检与一致性门

回收 A/B 表后，先做不参考旧 gold 和模型结果的结构校验。以下任一问题都必须失败
并退回对应标注者，不得静默修复：

- 非法 JSON、非法类型或非整数偏移；
- 越界、空 span 或 `text[start:end] != span`；
- 重复实体、嵌套/重叠实体；
- blind ID 缺失、重复、跨表错配或文本哈希不一致；
- 标注规范要求的显式重复 mention 尚未解决。

两位标注者的主一致性指标为 exact `(start, end, type)` entity micro-F1：

- 硬门：`F1 >= 0.80`；
- 投稿建议目标：`F1 >= 0.85`；
- 若低于 `0.80`，停止，按边界/类型/漏标类别汇总分歧，修订规范并重新独立标注；
- 无论通过与否，同时报告 precision、recall、F1、每类一致性和分歧数量，不只报单值。

## 5. 盲裁决、版本化与结果隔离

IAA 计算后，所有 A/B 分歧由第三名真人或预先指定的真人共识流程进行盲裁决。
裁决者可见原文和 A/B 标签，但在 corrected gold 重新冻结前不得查看旧 gold、任何
P5 预测、配置身份或误差分析。不能用“更有利于某配置”的标签作为裁决依据。

旧冻结文件永久保留，不原地修复、不改写哈希。若裁决完成，另建明确版本化文件，
例如 `domain_test_v2.jsonl`，生成新的 provenance、结构验证报告、`FROZEN_V2` 与
SHA256 manifest。只有 `v2` 冻结后，才可申请新的 bounded gate，在所有 A/B/C/D
配置上以完全相同预测统一重评分；不得只重评有利配置，也不得先看结果再改标签。

## 6. 投稿使用边界

在 QA1/QA2 未完成前：

- 论文不得声称现有 170 条 test 是“两名真人独立标注并裁决”的 gold；
- 不得引用 `0.9909` 作为 human IAA；
- 数据集贡献只能写成机器辅助构建且质量审计尚待完成；
- 当前 A/B/C/D 数字仍是旧冻结 `v1` 上的结果，方法趋势可作为 preliminary evidence，
  但数据质量会构成投稿的主要审稿风险。

## 7. P6-QA0 完成验收表

以下项目已由脚本、4 项远端无卡单元测试、远端 shell 和本地 PowerShell 独立复核：

| 检查项 | 要求 | 状态/值 |
| --- | --- | --- |
| 冻结 test | 170 行，原 SHA256 不变 | 通过；`42f6ecbb...53bfd0` |
| A 空白表 | 170 行，仅四列，人工字段全空 | 通过；`3a360826...2e1171` |
| B 空白表 | 170 行，仅四列，人工字段全空 | 通过；`39b5ee77...ae685` |
| A/B 盲化 | seed 不同、顺序不同、blind ID 不同 | 通过；seeds `2026072501/2026072502` |
| coordinator map | 170 行，不交付标注者 | 通过；`d39d2252...38eb1` |
| manifest | 输入、输出、哈希、seed、allowlist、safeguards 完整 | 通过；`45fa9fd6...95451` |
| 原数据写保护 | test/source map/FROZEN 哈希不变 | 通过；三项生成后复核不变 |
| 模型与成本 | 0 次模型调用、0 paid-GPU 成本 | 通过；服务器保持 GPU-free |

完整产物位置：

- 远端：`/root/autodl-tmp/backup/p6/p6_qa0_blind_annotation_20260725/`
- 本地忽略备份：`backups/P6/p6_qa0_blind_annotation_20260725/`

输入审计哈希：

- `domain_test.jsonl`：
  `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`
- `domain_gold_source_map.jsonl`：
  `9b77f3da190371a47196b0e8e1192172801e20d8f12945657da53dabb684e748`
- `FROZEN`：
  `e12517324c90a7261fcb46df698112dac8f83c2f5c6441e39c4340ada2cee0dd`

输出完整 SHA256：

- `annotator_a_blind.csv`：
  `3a36082631b45339d8b8e6ecd724ca3bbb7f74196531339ddb4621c4a72e1171`
- `annotator_b_blind.csv`：
  `39b5ee7755ee48bd1c0d762e1ecdfd8c6a4251bdf8a0e1cf82a4c7ad149ae685`
- `blind_id_map.jsonl`：
  `d39d2252400cdc17a37eef78ed3a276c1f86c804d65e03f43cef31d752e38eb1`
- `manifest.json`：
  `45fa9fd6cb7886ad7b7bc58078de4391b57e3233bd41a9960be1368a88695451`

P6-QA0 验收后必须停止，等待：

```text
P6_QA1_HUMAN_ANNOTATION_START_APPROVED
```

## 8. 2026-07-26 QA2 结果

后续提交的 A/B completed 文件未通过 QA2：21 个 hard errors、181 个重复 mention
blocking reviews；149 个严格有效配对的文件级 diagnostic F1 为 `0.5573`。更关键的
是，provenance 脚本使用同一标签字典同时生成 A/B 初始文件，违反“两名真人从空白
文本独立标注”的前提。因此 formal human IAA 保持 `null`，不得进入裁决或 v2。

完整结论见 `docs/P6_QA2_ANNOTATION_VALIDATION_20260726.md`。当前推荐门禁退回
`P6_QA1R_TRUE_HUMAN_REANNOTATION_APPROVED`，而不是向后进入 adjudication。
