# LaTeX 论文证据传播与框架定位收尾报告

日期：2026-08-07

门禁：`NER_PUBLIC_CLUENER_ABCD_K5_LATEX_PROPAGATION_APPROVED`

状态：`DONE`（已消耗）

## 1. 本步骤做了什么

本步骤只修改活跃论文工程
`docs/JISE_OVERLEAF_LATEX_20260729/` 中获批的 LaTeX 正文文件。`main.tex`
继续作为 Overleaf 入口；论文内容由 `frontmatter.tex` 和 `sections/*.tex`
承载。历史 Markdown 不是本步骤的论文目标。

- 提交 `8189f71`（`docs: propagate CLUENER evidence into LaTeX paper`）把
  装备领域三种子 NER、完整 1,343 条 CLUENER labeled-dev 的 12 格结果、
  F4a/F4b/F7 证据、标注质量限制和 `16/60` 机械记账传播到论文。
- 提交 `8f1f3e1`（`docs: frame LaTeX contribution as EC-FSIE framework`）把
  方法统一定位为新的 Evidence-Controlled Few-Shot Information Extraction
  (`EC-FSIE`) framework，并移除“本文不提出新基础模型”“engineering
  baseline”等自我弱化措辞。
- 第二次修改只增强框架定位和表达，没有改变数据、预测、配置、结果数字或
  result-to-claim 边界。

本步骤没有运行 Python、GPU、模型、vLLM、实验、结果重算或测试集 prompt，
也没有生成 DOCX、投稿或同步 GitHub。

## 2. 论文当前主线

论文当前以 EC-FSIE 为方法框架，以低标注中文装备领域 NER 为主贡献，以一个
额外中文公开 NER 基准上的有限方向复现作为外部支持。RE 只作为探索性负结果和
局限，不作为正向贡献。

可写的核心证据是：

1. 在冻结的低标注中文装备领域 NER 中，kNN 示例选择和领域词表分别带来观察到
   的 F1/recall 改善；RAG 在与词表配置 F1 near-tie 时提高 precision，并减少
   实体级 FP。
2. 在完整 1,343 条 CLUENER labeled official dev 的 focused evaluation 中，
   B-A、C-B 和 D-C 的方向与装备领域观察描述性一致；这只构成一个额外中文 NER
   基准上的有限方向复现。
3. F7 证明锁定的 Stage N + Stage R 管线可复现、逐条可审计，但 exact RE 很弱，
   D 不优于 C，四格均无 `HAS_METRIC` TP，因此只具有辅助方法学价值。

仍然不支持：统计显著性、SOTA、广泛公域/跨域泛化、正向 RE、public RE、
RAG-for-RE、CoVe/self-verification、K=1/5/10 稳健性、formal frozen-test IAA、
高质量关系标注、60-cell 完整矩阵、完整 F8/F9 或完整端到端 IE 成功。

## 3. 静态核验

2026-08-07 在 Windows 控制工作区进行了只读轻量静态核验：

- `.tex` 文件：13；`.bib` 文件：1；
- LaTeX environment 名称计数不匹配：0；
- 重复 `\label`：0；
- 缺失交叉引用目标：0；
- 缺失 BibTeX 键：0；
- 已删除的弱化创新短语匹配：0。

本机未安装 `latexmk`、`pdflatex` 或 `bibtex`，所以本版本尚未编译，也没有完成
PDF 视觉检查。静态核验通过不能替代实际 LaTeX 编译。

## 4. 当前断点与下一步

论文源文件已传播并提交，实验记账仍为 `16/60`，其余 44 个单元继续
`CLOSED`。没有实验或论文门禁存活，不需要 GPU。

下一步应先由作者提供并核实以下人工信息：作者顺序、单位、通信作者和邮箱、
致谢、资助、利益冲突、数据与代码可用性、伦理说明以及 CRediT 贡献。之后再由
人工批准一个新的精确 paper-only 最终化与编译门禁，限定可写文件与编译环境，
完成 LaTeX 编译、PDF 视觉审计和投稿格式检查。正式投稿、外部上传和 GitHub
同步仍需单独授权。

## 5. 需要记住的经验

- 论文事实必须从版本化 result-to-claim 传播，框架措辞可以增强，但不能把缺失
  证据写成已完成结果。
- `main.tex` 是入口，不是唯一正文；精修对象是完整 LaTeX 工程。
- 公共基准只支持有限方向复现，不能因加入 CLUENER 就升级为广泛泛化。
- RAG 的受支持价值是 precision/FP operating point，不是 F1 提升或“消除幻觉”。
- `CLOSED` 表示人工路线决策不再执行，不是失败实验；负结果和失败修复历史必须
  原样保留。
- 源码静态审计、可编译 PDF、投稿就绪是三个不同门槛，不能相互替代。
