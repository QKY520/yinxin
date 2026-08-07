# F7 后 NER 保底路线 Result-to-Claim 与冻结报告

日期：2026-08-04

门禁：`FULL_IE_STOP_AND_NER_FALLBACK_RTC_APPROVED`

状态：`DONE`

Result-to-claim 判定：`partial`

置信度：`high`

论文路线：**NER 主贡献；RE 仅作为探索性负结果与局限**

## 1. 门禁范围

本门禁只复核已有证据、冻结研究路线并同步项目文档。它没有运行或授权任何
Python、数据处理、prompt 生成、模型/API 调用、vLLM、GPU、实验、聚合、结果文件
修改、论文正文修改或 GitHub 同步。

复核范围为：

- P5 `domain_test` A/B/C/D、K=5、seeds 42/43/44 的三种子 NER；
- F4a `domain_dev50` 的两阶段 IE 与 relation-aware E/E-prime sanity；
- F4b 50 条 CLUENER tune sanity；
- F7 `domain:A/B/C/D:k5:s42` 四个最终 Stage R 单元；
- 实体与关系标注质量证据；
- 原始 60-cell 协议的实际完成度。

## 2. 证据复核

### 2.1 三种子装备领域 NER

冻结 `domain_test` 上的三种子均值与样本标准差如下：

| 配置 | Precision | Recall | F1 | FP |
| --- | ---: | ---: | ---: | ---: |
| A | `0.484066 +/- 0.025428` | `0.599231 +/- 0.028904` | `0.534645 +/- 0.004375` | `613.3 +/- 88.8` |
| B | `0.505743 +/- 0.000234` | `0.615304 +/- 0.001816` | `0.555169 +/- 0.000880` | `573.7 +/- 1.2` |
| C | `0.511433 +/- 0.000472` | `0.640811 +/- 0.001210` | `0.568858 +/- 0.000769` | `584.0 +/- 0.0` |
| D | `0.525135 +/- 0.000000` | `0.613208 +/- 0.000000` | `0.565764 +/- 0.000000` | `529.0 +/- 0.0` |

干净对比为：

- `B-A`：观察到 F1 `+0.020524`，FP 约 `-39.7`；
- `C-B`：观察到 F1 `+0.013689`，主要来自 recall 提升，FP 约 `+10.3`；
- `D-C`：F1 `-0.003094`，属于 near-tie；precision 提高，FP `-55.0`；
- `D-A`：F1 `+0.031119`，FP 约 `-84.3`。

已有 passage-cluster bootstrap 结论显示 B-A、C-B 的 F1 区间跨 0，不能写成
统计显著优越；D-C 的 FP 差异区间不跨 0。三种子输出又接近确定性，因此这里的
不确定性主要是给定输出下的 passage-sampling uncertainty，不能扩张为广义随机
稳健性。

### 2.2 F4a/F4b sanity

F4a 是 dev-only 诊断，不是最终单元。A/B/C/D exact RE F1 分别为
`0.056680/0.040404/0.039024/0.010989`；D 的关系解析失败率为 `6%`，四格均无
`HAS_METRIC` TP。E-prime 在该 dev 协议上局部提高 NER/RE F1，而 E 同时降低二者。
这只能说明验证机制具有配置依赖的局部信号和明显失败风险，不能形成 CoVe 正向
主张。

F4b 同样只是 tune-only sanity。A/B/C/D NER F1 为
`0.524444/0.563107/0.571429/0.638889`；E-prime 将 F1 降至 `0.546512`，E 仅小幅
升至 `0.644444`。两项删除审计分别为 `65.79%` 和 `69.44%`，均未达到预设 `70%`
正向主张阈值。F4b 不能证明公开基准泛化或 CoVe 有效。

### 2.3 F7 四格最终 RE

F7 只完成 `domain:A/B/C/D:k5:s42` 四个单种子最终单元：

| 配置 | Exact RE P | Exact RE R | Exact RE F1 | TP/FP/FN |
| --- | ---: | ---: | ---: | --- |
| A | `0.047923` | `0.035129` | `0.040541` | `15/298/412` |
| B | `0.079167` | `0.044496` | `0.056972` | `19/221/408` |
| C | `0.076046` | `0.046838` | `0.057971` | `20/243/407` |
| D | `0.073684` | `0.032787` | `0.045381` | `14/176/413` |

`D-C=-0.012590`，所以 F7 不支持 RAG-for-RE。四格全部为零 `HAS_METRIC` TP。
680 行审计保留了 647 次模型请求、52 次确定性跳过、19 次 retry、`10/680`
关系解析失败和 1,840 个无效关系单元清理事件。四格、prompt/cache/raw/per-query、
哈希、备份和 v1 收尾失败/v2 无模型修复均可追溯。

因此 F7 的价值是证明**锁定的两阶段 IE 管线能够产生可复现、可审计的最终单元**，
并提供诚实的负面诊断；它不是正向 RE 贡献。

### 2.4 标注质量

- 实体：20 条全新 non-test 双人校准 exact span+type micro-F1 为 `0.800000`，
  恰好达到人工接受的原始 `>=0.80` 下限，但低于后来保守的 `>=0.85` 目标。
  `TECH_SCHEME` F1 仅 `0.153846`。该结果不是 frozen-test formal IAA。
- 关系：人工修订文件 20/20 结构有效，但 exact-directed 文件一致性 F1 仅
  `0.417391`，其中 `PART_OF=0.246154`。该结果不是 formal IAA，也不支持高质量
  关系标注主张。

### 2.5 矩阵完成度

F5 冻结的是 60 个协议身份，不是 60 个经验结果。F7 后实际状态为：

- 4 个完整单元：domain A/B/C/D、K=5、seed42，具有 Stage N+R；
- 8 个部分单元：domain A/B/C/D、K=5、seeds43/44，仅有 Stage N；
- 48 个单元完全缺失；
- 字面完成度 `4/60`，未完整 `56/60`。

F4a/F4b sanity、F5 协议冻结和 F6 replay 准备均不计入最终单元。

## 3. 独立 Result-to-Claim 评审

技能指定的 `gpt-5.4` 次级模型在当前协作接口不可用，因此使用可用的
`gpt-5.6-sol`、`xhigh` 进行只读独立判断。评审者未写入仓库，也未获得任何执行
权限。

- `claim_supported`: `partial`
- `confidence`: `high`
- `what_results_support`: 单一冻结中文装备领域测试集上，三种子结果支持范围受限的
  kNN 与词表 NER 观察收益；RAG 在 F1 near-tie 下提高 precision 并减少 FP。
- `auxiliary_value`: F7 证明两阶段 IE 执行链具有锁定输入、逐条记录、prompt/cache
  哈希、解析审计和可验证备份，可用于可复现性与负结果分析。
- `what_results_dont_support`: 正向 RE、RAG-for-RE、CoVe、完整 IE、公域泛化、K
  稳健性和完整矩阵均不支持；标注证据也不构成 formal frozen-test IAA 或高关系
  一致性。
- `missing_evidence`: 三种子最终 RE、final E/E-prime、K 扫描、公开基准 final、
  更强关系标注一致性和 formal test 可靠性仍是科学证据缺口，但不再是执行待办。
- `suggested_claim_revision`: 主贡献应是可复现的低标注中文装备领域 NER 工作流；
  RE 只能作为得到弱/负结果的可审计探索，CoVe 与 full-IE benefit 不得主张。

## 4. 最终主张分层

### 支持

> 在冻结的低标注中文装备领域 NER 设置中，kNN 示例选择和领域词表分别带来
> 观察到的 F1/recall 改善；加入 RAG 后，系统与词表配置在 F1 上近似持平，但
> precision 更高、实体级 false positives 更少。

该结论仅适用于当前 frozen v1 装备领域 NER。B-A/C-B 不使用“显著”措辞；RAG 的
作用表述为 precision/FP operating-point trade-off，而不是 F1 增益或广义幻觉消除。

### 辅助价值

> F7 证明锁定的 Stage N + Stage R 两阶段 IE 管线可以产生可复现、逐条可审计的
> 最终单元，并保留解析、清理、缓存、失败修复和备份证据。

这是一项工程可复现性与负结果分析价值，不是 RE 性能贡献。

### 不支持

- 正向关系抽取贡献或“RE 成功”；
- RAG 改善 RE；
- CoVe/self-verification 有效；
- `HAS_METRIC` 可用；
- 公共基准或跨域泛化；
- K=1/5/10 稳健性；
- 60-cell 完整矩阵、完整 IE 或统计显著性主张。

## 5. 人工路线决策与状态语义

人工决策如下，立即覆盖此前“继续补全 60-cell”的计划方向：

1. 停止补全原始 60-cell 矩阵；实际完成度永久按现有证据记录为 `4/60`。
2. 不执行 IE051、E/E-prime、K 扫描、CLUENER final、F8 或 F9。
3. IE051 作为历史提案保留，状态改为 `CLOSED`：它因人工路线选择而**未执行且不再
   计划执行**，不是失败实验、阻塞实验或负面实验结果。
4. 所有已有负结果、sanity、失败日志和部分单元继续保留，不删除、不改写。
5. 论文路线冻结为“NER 主贡献，RE 作为探索性负结果/局限”。

未补证据继续列为论文限制，而不是实验 backlog。任何未来重开实验都必须由新的
人工“路线变更 + 精确 bounded execution”门禁明确授权，不能从历史提案推断权限。

## 6. 下一纸面门禁

本门禁不修改任何论文正文。下一步只能在人工另行明确批准
`NER_FALLBACK_MANUSCRIPT_PROPAGATION_APPROVED` 后，才把本报告的主张分层和限制
传播到指定的中文 Markdown、英文 Markdown 与/或 LaTeX 稿件。该未来纸面门禁不应
授权实验、结果重算、DOCX、投稿或 GitHub 同步，除非人工另行逐项写明。

当前该纸面门禁未授予。项目在本次文档提交后停止并等待人工确认。

## 7. 后续状态注记（2026-08-07）

以上第 6 节是本路线冻结时的历史状态。随后人工批准并消耗了
`NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED`，并在完整
`docs/JISE_OVERLEAF_LATEX_20260729/` 工程中完成了受限证据传播和 EC-FSIE
框架定位（提交 `8189f71`、`8f1f3e1`）。这没有改变本报告的 `NER 主贡献、RE
探索性负结果/局限` 决策，也没有重开 60-cell 路线。当前论文收尾与静态审计见
`docs/NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_CLOSEOUT_20260807.md`。
