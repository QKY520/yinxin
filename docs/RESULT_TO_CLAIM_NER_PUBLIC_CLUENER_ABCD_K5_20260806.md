# CLUENER 公共 NER Result-to-Claim 与论文主张冻结报告

日期：2026-08-06

门禁：`NER_PUBLIC_CLUENER_ABCD_K5_RTC_APPROVED`

状态：`DONE`

Result-to-claim 判定：`partial`

置信度：`high`

论文路线：**NER 主贡献；RE 仅作为探索性负结果与局限**

## 1. 门禁范围

本门禁只解释已经完成、验证并备份的证据，冻结后续论文可写主张，并同步控制
文档。它没有运行或授权任何 Python、数据处理、prompt 生成、模型/API 调用、
vLLM、GPU、实验、结果重算、LaTeX/论文正文修改、DOCX、投稿或 GitHub 同步。

复核范围为：

- CLUENER labeled official dev 全部 1,343 条、A/B/C/D、K=5、seeds
  42/43/44 的 12 个 NER final cells；
- 冻结 `domain_test` 上 A/B/C/D、K=5、三种子的 NER 证据；
- F4a/F4b、F7、实体/关系标注质量及当前 `16/60` 矩阵记账；
- 公共结果与既有装备领域结果的干净对比方向是否一致。

## 2. 公共 NER 机械证据

CLUENER 使用完整 labeled official dev 作为冻结的离线 final split；官方 test
没有 gold，未被用于离线评估。所有资源均来自冻结的 CLUENER 协议：30 条
support bank、61 项 support-derived schema-specific lexicon 和 labels-stripped、
去重后的 train-text RAG replay。它们不是装备领域词表或装备领域 RAG 语料。

| 配置 | Precision | Recall | F1 | FP |
| --- | ---: | ---: | ---: | ---: |
| A | `0.448636 +/- 0.036890` | `0.413086 +/- 0.056862` | `0.428519 +/- 0.037917` | `1569.0 +/- 306.8` |
| B | `0.528488 +/- 0.001929` | `0.500217 +/- 0.002118` | `0.513964 +/- 0.001907` | `1371.0 +/- 7.2` |
| C | `0.530932 +/- 0.001140` | `0.504774 +/- 0.001316` | `0.517521 +/- 0.000619` | `1370.0 +/- 8.7` |
| D | `0.540764 +/- 0.002162` | `0.488715 +/- 0.000940` | `0.513424 +/- 0.001493` | `1275.0 +/- 8.7` |

干净对比为：

- `B-A`：F1 `+0.085445`，precision `+0.079852`，recall `+0.087131`，
  FP `-198.0`；
- `C-B`：F1 `+0.003557`，precision `+0.002444`，recall `+0.004557`，
  FP `-1.0`，属于很小的方向性增量；
- `D-C`：F1 `-0.004097`，precision `+0.009832`，recall `-0.016059`，
  FP `-95.0`，属于 precision/FP 与 recall 的 operating-point 权衡。

A seed44 的低值被原样保留，未选择性删除或重跑。12 个单元共 16,116 条
query-cell rows，parse failures 为 `138/16116 = 0.856292%`，所有单元均低于
冻结的 5% stop threshold。版本化 v2、`205/205` clean tracked suite、18,239
项远端备份和 63 项本地轻量镜像均已通过。

## 3. 跨设置方向复核

| 干净对比 | 装备领域 frozen test | CLUENER labeled dev | 可解释范围 |
| --- | --- | --- | --- |
| `B-A` kNN | F1 `+0.020524` | F1 `+0.085445` | 两个设置均观察到正向 F1，但不能称为普遍或显著效应 |
| `C-B` 词表 | F1 `+0.013689`，recall 上升 | F1 `+0.003557`，recall 上升 | 方向一致；公共增量很小，只支持有限复现 |
| `D-C` RAG | F1 `-0.003094`，precision 上升，FP `-55` | F1 `-0.004097`，precision 上升，FP `-95` | 两个设置均复现 near-tied F1 与 precision/FP 权衡 |

因此，公共块支持的是**在一个额外中文 NER 基准协议上的方向性复现和有限
可迁移性证据**。它没有把单域结果升级为广泛公共基准或跨域泛化结论。

## 4. 既有负面与质量证据不变

- F4a 是 domain-dev sanity：A/B/C/D exact RE F1 为
  `0.056680/0.040404/0.039024/0.010989`，D 关系解析失败率 `6%`，四格均无
  `HAS_METRIC` TP。E-prime 只有局部 dev 正向信号，E 为负向，不能形成 CoVe
  final claim。
- F4b 是 50 条 CLUENER tune sanity：A/B/C/D NER F1 为
  `0.524444/0.563107/0.571429/0.638889`；E-prime 降低 F1，E 只小幅提高，两个
  deletion audits 均未达到预设 `70%` 正向门槛。
- F7 final seed42 exact RE F1 为
  `0.040541/0.056972/0.057971/0.045381`；D 低于 C，四格均无
  `HAS_METRIC` TP。F7 只支持两阶段 IE 管线的可复现、可审计辅助价值。
- 实体标注的 20 条 fresh non-test 双人校准 F1 为 `0.800000`，其中
  `TECH_SCHEME=0.153846`；关系修订文件一致性 F1 为 `0.417391`，其中
  `PART_OF=0.246154`。二者都不是 frozen-test formal IAA。
- 机械记账是 `16/60`，不是完整矩阵。公共块没有改变上述 RE、CoVe、标注质量
  或完整 IE 的负面/限制结论。

## 5. 独立 Result-to-Claim 评审

技能指定的 `gpt-5.4` 次级模型在当前协作接口不可用，因此沿用上一次 RTC 的
已记录替代方案，使用 `gpt-5.6-sol`、`xhigh` 进行只读独立判断。评审者未写入
仓库，也未获得任何执行权限。

- `claim_supported`: `partial`
- `confidence`: `high`
- `what_results_support`: kNN、schema-specific support lexicon 和 RAG 的三个
  干净对比方向在装备领域与一个额外中文公开 NER 基准上描述性一致；公共块完整、
  可复算并保留不利 seed。
- `what_results_dont_support`: 广泛公域/跨域泛化、统计显著性、SOTA、K 稳健性、
  public RE、CoVe 和完整 IE 均不支持。
- `missing_evidence`: 更多有 gold 的公开基准、CLUENER 配对不确定性、真正独立的
  随机重复、K 扫描、监督基线、public RE 与 final verifier cells。它们是冻结证据
  的科学限制，不是当前执行 backlog。
- `suggested_claim_revision`: 将 CLUENER 写成一个 focused external-benchmark
  replication；只陈述方向一致的 NER 结果，不写广义迁移成功。

## 6. 最终主张分层

### 支持

1. 在冻结的低标注中文装备领域 NER 设置中，kNN 示例选择和领域词表分别带来
   观察到的 F1/recall 改善；RAG 在与词表配置 F1 near-tie 时提高 precision、
   减少实体级 FP。
2. 在完整 1,343 条 CLUENER labeled official dev 的 focused evaluation 中，
   kNN 相对 fixed-random 提高观察到的 mean NER F1；support-derived、
   schema-specific lexicon 带来很小但方向一致的 F1/recall 增量。
3. CLUENER 上的 RAG 对比复现了装备领域的同型 operating-point：相对词表配置，
   F1 near-tie、precision 更高、FP 更少、recall 更低。可以称为一个额外中文 NER
   基准上的有限方向复现，不能称为广泛公域泛化。

以上均是范围受限的描述性主张。B-A/C-B 不使用“显著”措辞；RAG 不写成 F1
提升、事实性提升或“消除幻觉”。

### 辅助价值

1. F7 证明锁定的 Stage N + Stage R 两阶段 IE 管线可以产生可复现、逐条可审计
   的最终单元，并保留解析、清理、缓存、失败修复与备份证据；这不是正向 RE
   性能贡献。
2. CLUENER 12-cell block 证明 frozen support/glossary/replay、完整 final rows、
   prompt/cache/raw hashes、失败保留和版本化 finalizer 可以复算、审计和备份；
   这是公共 NER 复现性证据，不是完整 F8/F9 或完整矩阵。

### 不支持

- 广泛公共基准、跨域或公域泛化成功；
- 统计显著性、SOTA 或优于监督基线；
- 正向 RE、public RE、RAG-for-RE 或 `HAS_METRIC` 可用；
- CoVe/self-verification 有效；
- K=1/5/10 稳健性；
- frozen-test formal IAA 或高质量关系标注；
- 60-cell 完整矩阵、完整 F8/F9、完整 IE 或端到端 IE 成功。

## 7. 路线与记账冻结

- 总体 result-to-claim 继续为 `partial`，置信度 `high`。
- 论文路线不变：NER 是主贡献，RE 仅作为探索性负结果/局限。
- 机械记账保持 `16/60`：4 个 domain Stage N+R、12 个 CLUENER NER、8 个
  domain Stage N-only、36 个完全缺失。
- 其余 44 个未完成身份继续 `CLOSED`。IE051 未执行且因人工路线决策不再执行，
  不是失败、阻塞或负面实验。
- 不执行 E/E-prime、K 扫描、RE/Stage R、domain rerun、完整 F8/F9 或新测试。
- 当前冻结路线下不需要追加 GPU 实验。缺失证据进入论文局限，不转成实验待办。

## 8. 下一纸面门禁

本门禁不修改论文。下一步只能由人工另行批准精确的
`NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED`，把本报告的受限主张、
公共结果表和限制传播到完整
`docs/JISE_OVERLEAF_LATEX_20260729/` LaTeX 工程。`main.tex` 仅是 Overleaf
入口；正文目标是 `frontmatter.tex` 和 `sections/*.tex`，实际允许修改的文件必须
在该门禁中逐项列出。

该未来门禁不自动授权实验、Python、GPU、模型、prompt、结果重算、DOCX、投稿或
GitHub 同步。本次 RTC 文档提交后停止并等待人工确认。
