# 项目路线与 SCI 四区投稿计划 / Project Route and SCI Q4 Plan

Date: 2026-07-20

## 中文版

### 1. 路线确认

本项目不换题。当前路线仍然是：

1. 构建装备领域小样本标注数据集；
2. 建立可复现实验流程；
3. 使用 RAG、领域词典/schema 规则约束、输出格式约束和原子级验证机制降低幻觉；
4. 通过对比实验和消融实验证明各模块有效。

这条路线适合定位为应用型/工程型 SCI 四区论文。核心不是宣称超过全监督 SOTA，而是在低标注装备领域场景下证明：检索证据和验证机制能降低无依据实体预测，同时尽量保持或提升抽取 F1。

### 2. 投稿口径

- 目标：SCI 四区可投论文。
- 时间：尽量一个月内形成可投稿版本。
- 预算：总预算目标 400 CNY 内；接近预算时必须停下汇报。
- 语言：先完成中文技术稿，再翻译和改写为英文 SCI 稿。
- 任务主次：NER 是主任务和主贡献；RE 是辅助任务和补充证据。
- 模型路线：本地部署开源模型仍是可复现实验主体；商业 LLM API 只能作为辅助标注、质检、审稿和润色工具，除非另行记录路线变更。

### 3. 论文贡献点

建议写成三条贡献：

1. 提出并整理一个面向装备领域中文文本的小样本 NER/RE 标注数据集，包含标注规范、一致性评估、冻结划分和去重记录。
2. 构建一条可复现的装备领域小样本信息抽取流程，集成 kNN 示例检索、领域词典/schema 约束、RAG 证据注入和原子级自验证。
3. 通过三种随机种子和消融矩阵证明：不同模块对 NER F1、关系抽取和实体级幻觉率下降的贡献是可量化、可复算的。

### 4. 实验主线

主实验仍采用 A 到 E-prime 的消融矩阵：

| 配置 | 示例选择 | 词典/schema约束 | RAG | 自验证 | 作用 |
| --- | --- | --- | --- | --- | --- |
| A | fixed random | no | no | no | 基线 |
| B | kNN | no | no | no | 示例检索贡献 |
| C | kNN | yes | no | no | 词典/schema约束贡献 |
| D | kNN | yes | yes | no | RAG 贡献 |
| E | kNN | yes | yes | yes | 完整方法 |
| E-prime | kNN | yes | no | yes | 分离验证与 RAG |

报告原则：

- 每个正式结果必须是 seeds 42/43/44 的 mean ± std；
- 不报告单个好看的 seed；
- 负结果保留并解释；
- test 冻结后不得根据 test 调 prompt、阈值或词典；
- 所有汇总结果必须能从 per-query JSONL 复算。

### 5. 一个月执行建议

优先保证论文可发，而不是无限扩大实验：

1. 第 1 周：完成 P2 标注候选质量控制、LLM 辅助建议稳定性、人工标注规范和 100 条双人一致性。
2. 第 2 周：冻结 domain support/dev/test，完成 P3 基线和 kNN 示例检索。
3. 第 3 周：完成 RAG、词典约束、自验证和主要消融矩阵。
4. 第 4 周：汇总结果、补必要消融、画图、写中文稿、再转英文稿。

风险优先级：

1. 数据集质量和一致性最高优先；
2. 14B 辅助标注只服务于人工审阅，不应拖垮主线；
3. 如果 RE 质量不足，降低为辅助分析，不让它阻塞 NER 主论文；
4. 如果 RAG/F1 提升不明显，重点转向幻觉率下降和错误类型分析；
5. 如果 4090 时间紧张，优先跑最小可发表矩阵，再补扩展实验。

## English version

### 1. Locked route

The project does not change topic. The locked route is:

1. build a small annotated equipment-domain dataset;
2. provide a reproducible few-shot IE pipeline;
3. reduce hallucination using RAG, glossary/schema constraints, output-format constraints, and atomic verification;
4. validate the modules through comparative ablations.

The paper should be framed as an applied/engineering SCI Q4 submission. The central claim is not supervised SOTA, but reproducible low-label domain IE with measurable reduction of unsupported entity predictions.

### 2. Submission framing

- Target: SCI Q4.
- Deadline: one month if feasible.
- Budget target: within 400 CNY unless separately approved.
- Writing order: Chinese technical draft first, then English SCI manuscript.
- Main task: NER.
- Auxiliary task: RE.
- Local open-source models remain the reproducible experimental backbone. Commercial LLM APIs may support labeling QA, review, and polishing, but should not silently replace the core local-model claims.

### 3. Recommended contributions

1. A small quality-controlled Chinese equipment-domain NER/RE dataset with annotation guideline, agreement report, frozen splits, and deduplication logs.
2. A reproducible few-shot extraction pipeline combining kNN demonstrations, domain glossary/schema constraints, RAG evidence injection, and atomic self-verification.
3. A recomputable ablation study showing module-level effects on NER F1, relation extraction, and entity-level false-discovery-style hallucination rate.

