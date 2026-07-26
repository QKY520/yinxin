# P6-QA1R 低一致度诊断与校准准备报告

日期：2026-07-26

结论：现有失败文件已完成诊断，非 test 校准包已准备；尚未形成正式 human IAA，
也未进入重标、裁决、`v2` 冻结或重评分。

## 1. 范围与保护

本轮仅在 AutoDL GPU-free 模式下使用：

- 已锁定的 A/B completed 文件；
- QA2 的 `validation_report.json`、`issues.csv` 和 `disagreements.jsonl`；
- `domain_dev.jsonl` 的 ID 与文本，用于生成空白校准表。

未读取 frozen test gold、模型预测、prompt 或实验结果；未修改任何标签；未运行模型、
vLLM、dry-run 或 paid GPU。当前 A/B 文件只作为失败案例诊断，不能通过分析或修补
转化为独立 human IAA。

## 2. 原始诊断数据表

### 2.1 QA2 文件级结果

| 指标 | 值 | 解释 |
| --- | ---: | --- |
| A/B 行数 | 170/170 | blind ID 与文本对齐 |
| hard errors | 21 | A 未排序 19；B 空字段 2 |
| repeated-mention reviews | 181 | A 180；B 1 |
| 严格可比较行 | 149/170 | 21 个 hard-error 行被排除 |
| A/B 实体数 | 824/931 | 仅严格可比较行 |
| exact matches | 489 | exact `(start,end,type)` |
| diagnostic P/R/F1 | 0.5252/0.5934/0.5573 | 不是 human IAA |
| 完全一致行 | 19/149 | 130 行含分歧 |

分类别文件诊断：

| 类型 | A/B 数量 | exact matches | F1 |
| --- | ---: | ---: | ---: |
| `EQUIPMENT` | 586/535 | 362 | 0.6459 |
| `MODULE` | 220/232 | 124 | 0.5487 |
| `TECH_SCHEME` | 18/164 | 3 | 0.0330 |
| `METRIC` | 0/0 | 0 | 空类，不可解释为 1.0 |

### 2.2 分歧分类

| 分歧类别 | 实体实例数 | 涉及行数 |
| --- | ---: | ---: |
| 同边界、异类型 | 127 | 60 |
| 同类型、重叠但边界不同 | 40 | 28 |
| 边界和类型均不同且重叠 | 10 | 10 |
| A 单边未匹配 | 158 | 130 |
| B 单边未匹配 | 265 | 130 |

同边界或重叠配对的主要方向：

| A 类型 -> B 类型 | 数量 |
| --- | ---: |
| `EQUIPMENT -> TECH_SCHEME` | 104 |
| `EQUIPMENT -> EQUIPMENT` | 28 |
| `MODULE -> EQUIPMENT` | 19 |
| `MODULE -> TECH_SCHEME` | 13 |
| `MODULE -> MODULE` | 10 |
| `TECH_SCHEME -> TECH_SCHEME` | 2 |
| `TECH_SCHEME -> MODULE` | 1 |

完整协调员数据位于：

`/root/autodl-tmp/backup/p6/p6_qa1r_diagnosis_20260726/`

其中：

- `summary.json`：聚合统计；
- `taxonomy_by_row.csv`：130 条分歧行的类别计数；
- `disagreement_pairs.csv`：600 条配对或单边实体诊断记录；
- `manifest.json`：输入输出哈希和保护声明。

## 3. 关键发现

### 发现 1：首要问题是类型政策，而非单纯边界误差

- **观察**：127 个同边界类型冲突中，104 个为 A 的 `EQUIPMENT` 对 B 的
  `TECH_SCHEME`。
- **解释**：一套文件把大量具体系统或装备名称按“具有技术含义”归入
  `TECH_SCHEME`，没有坚持“物理对象 vs 非物理方法”的优先判据。
- **影响**：继续编辑原文件无法建立一致、可复现的 schema 理解。
- **下一步**：指南 v3 增加固定判定顺序和物理系统/技术方法最小对照；校准包为
  `TECH_SCHEME` 线索单独保留 6 条。

### 发现 2：重复 mention 规则未被实际执行

- **观察**：181 个重复 mention 待审，其中 A 占 180 个，涉及 A 的 59 行。
- **解释**：很可能只标了首次出现，或按词典一次性生成而没有逐次检查全文。
- **影响**：大量单边漏标会同时拉低 recall、exact F1 和行级一致度。
- **下一步**：每行提交前必须全文搜索每个已标词面；校准包为重复 mention 线索
  单独保留 6 条。

### 发现 3：`METRIC` 的空类是覆盖失败

- **观察**：149 个有效配对中双方均为 0 个 `METRIC`。
- **解释**：不能据此证明一致，反而说明指标识别规则没有被执行或数据生成过程遗漏
  了该类。
- **影响**：即使总体 F1 被大类拉高，数据集四类贡献仍不能成立。
- **下一步**：指南 v3 明确完整指标边界和数字组件反例；校准包为数值/指标线索
  单独保留 6 条，并要求四类实际覆盖。

### 发现 4：格式问题可以机械预防，但不能机械补标签

- **观察**：19 行未排序、2 行空字段；另有 50 个重叠边界相关冲突。
- **解释**：提交前缺少结构自检，同时边界政策仍不够操作化。
- **影响**：正式 IAA 只能在完整结构有效集合上计算。
- **下一步**：提交前检查 JSON、offset、排序、重叠和空数组；验证器只能报错，不能
  自动修复或裁决。

## 4. 已准备的非 test 校准包

远端目录：

`/root/autodl-tmp/backup/p6/p6_qa1r_calibration_20260726/`

输入为 50 条 `domain_dev`，SHA256：

`ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`

按纯文本线索选择 24 条：

| 校准桶 | 条数 |
| --- | ---: |
| `METRIC` | 6 |
| `TECH_SCHEME` | 6 |
| `EQUIPMENT_MODULE` | 6 |
| `REPEATED_MENTION` | 6 |

产物：

- A 空白表：`annotator_a_calibration.csv`，SHA256
  `a9d36939a8e91f5ee90b3b7b67740416976e3662a1eec1469e72df7abdb7bc38`；
- B 空白表：`annotator_b_calibration.csv`，SHA256
  `ce6c9771bf17815280215382b67089e125362fb079a544a137e16f0d82fe3d00`；
- coordinator-only map：`coordinator_map.jsonl`，SHA256
  `a42511bd41bef0666c703c8d4e6ca1eb623688bba0e3b872786f164fedb3b18b`；
- manifest：`manifest.json`，SHA256
  `c7780076bcfc26b9bdc1095c468a8af4398ebc64271e64a39be426aa1cf6fbd7`。

A/B 顺序不同，标注字段全空；annotator 文件不包含原始 ID、现有 dev 标签、test
gold、预测、建议或 coordinator map。该校准数字不得写入论文 formal IAA。

## 5. 下一人工步骤

1. 两位真人分别领取自己的 24 条校准表和
   `docs/P6_QA1R_ANNOTATION_GUIDELINE_V3_20260726.md`；不得交换文件。
2. 双方独立填写 `entities_json`，疑点写入 `uncertainty_code`。
3. 文件返回协调员后，先做结构验证，再计算校准 exact F1 和分类别覆盖。
4. 双方只在独立首轮结束后讨论分歧，形成指南 v4；校准建议目标为 `>=0.85`。
5. 指南锁定后，才准备全新的 170 条 test 空白表。当前 QA2 文件不得修补复用。

本轮到此停止。校准标注、正式 test 重标、裁决、`v2` 冻结和重评分均需后续独立
门禁。
