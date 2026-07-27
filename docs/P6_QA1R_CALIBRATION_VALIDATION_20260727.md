# P6-QA1R 非 test 校准验证报告

日期：2026-07-27

结论：本轮校准质量门为 `blocked`。严格结构有效的 19 对文件级 exact
span+type F1 为 `0.6098`；在确认 5 个 hard error 全部只是实体顺序错误后，补充计算的
24 对顺序无关诊断 F1 为 `0.6455`，仍明显低于校准目标 `0.85`。该数值只是
`domain_dev` 校准文件一致度，不是 frozen-test formal human IAA。

## 1. 范围与保护

本轮仅在 AutoDL GPU-free 模式下验证以下锁定输入：

| 输入 | SHA256 |
| --- | --- |
| A blank | `a9d36939a8e91f5ee90b3b7b67740416976e3662a1eec1469e72df7abdb7bc38` |
| B blank | `ce6c9771bf17815280215382b67089e125362fb079a544a137e16f0d82fe3d00` |
| A completed | `36613af484210ea7b916e744e1785b37ee5c47ed7bf41149ef5ac19af230bb0a` |
| B completed | `9017bf65c8bd5e02a529bdef73f0ff845edc46d4471a84d80bb72615fc7aa8c7` |
| coordinator map | `a42511bd41bef0666c703c8d4e6ca1eb623688bba0e3b872786f164fedb3b18b` |

A/B 各 24 行，blind ID、文本和文本哈希均与空白表及 coordinator map 对齐；四个
校准桶各 6 行。验证器未读取旧 dev gold、frozen test、预测、prompt 或模型输出，未
修改标签，也未运行模型、vLLM、dry-run 或 paid GPU。

## 2. 原始结果表

### 2.1 总体文件一致度

| 口径 | 配对行 | A/B 实体 | exact matches | P(B vs A) | R(B vs A) | F1 | 完全一致行 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 严格结构有效 | 19/24 | 188/140 | 100 | 0.7143 | 0.5319 | 0.6098 | 1/19 |
| 仅忽略顺序错误的补充诊断 | 24/24 | 243/197 | 142 | 0.7208 | 0.5844 | 0.6455 | 1/24 |

补充诊断与 `0.85` 校准目标的绝对差为 `-0.2045`，相对短缺约 `24.1%`。它只用于
判断指南是否已经足够一致，不能绕过结构错误或替代正式 IAA。

### 2.2 分类型顺序无关诊断

| 类型 | A/B 数量 | exact matches | P(B vs A) | R(B vs A) | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `EQUIPMENT` | 116/93 | 74 | 0.7957 | 0.6379 | 0.7081 |
| `MODULE` | 92/81 | 51 | 0.6296 | 0.5543 | 0.5896 |
| `TECH_SCHEME` | 19/6 | 4 | 0.6667 | 0.2105 | 0.3200 |
| `METRIC` | 16/17 | 13 | 0.7647 | 0.8125 | 0.7879 |

## 3. 结构与复核问题

| 问题 | 数量 | 位置 | 影响 |
| --- | ---: | --- | --- |
| `ENTITIES_NOT_SORTED` | 5 | 全部为 B | 5 行不能进入严格主结果 |
| `REPEATED_MENTION_UNRESOLVED` | 29 | 全部为 B | 属于 blocking review，不能通过质量门 |
| `DUPLICATE_UNCERTAINTY_CODE` | 4 | 全部为 B | 警告，不改变标签或分数 |

严格有效的 19 行中有 18 行存在实体分歧。按校准桶统计，这 18 行包括
`EQUIPMENT_MODULE` 4 行、`TECH_SCHEME` 4 行、`METRIC` 5 行和
`REPEATED_MENTION` 5 行，说明问题并非集中在一个偶然样本。

## 4. 关键发现

1. **观察**：A 标了 243 个实体，B 标了 197 个；B 相对 A 的补充诊断 recall 只有
   `0.5844`。**解释**：双方不仅有类型冲突，也有大量单边漏标或边界差异。
   **影响**：不能靠格式排序使一致度接近目标。**下一步**：逐条讨论分歧规则，不能
   直接改当前 24 行后重新报分。
2. **观察**：`TECH_SCHEME` F1 仅 `0.3200`，A/B 数量为 19/6；`MODULE` F1 也只有
   `0.5896`。**解释**：物理系统、部件和非物理技术方法的判定仍未形成共同操作规则。
   **影响**：这是当前最大 schema 风险。**下一步**：指南 v4 必须增加最小对照、
   决策顺序和边界反例。
3. **观察**：29 个重复 mention 复核项全部来自 B。**解释**：逐次 mention 全覆盖
   规则仍未稳定执行。**影响**：漏标会系统性压低 recall 和 exact F1。**下一步**：
   在 v4 中加入逐行全文检索和提交前 checklist。
4. **观察**：`METRIC` 已不再是空类，但 F1 仍为 `0.7879`，且样本量只有 16/17。
   **解释**：v3 对指标覆盖有改善，但边界口径尚未完全一致。**影响**：不能据此认定
   四类标注质量已经达标。**下一步**：补充“完整指标短语 vs 裸数字/单位片段”案例。

## 5. Provenance 限制

验证器只证明文件内容和锁定输入的一致性，不证明两位真人的独立标注过程，因此
`formal_human_iaa` 保持 `null`。工作区另有未跟踪脚本
`p6_cal_b_annotate.py`，SHA256 为
`aadacb02cffd336e2681039d54ae3f4409690071a4edd2b0581dfa56cbac455f`；它包含硬编码
B 标注并可写出 B completed CSV。本轮未执行、未修改、未提交该脚本。其存在意味着
独立-human provenance 仍需协调员另行核验，不能仅凭两个文件名作论文声明。

## 6. 产物与完整性

远端与本地均保留初始报告 `r1` 和增加顺序无关补充诊断的 `r2`。`r2` 是本报告采用
的最终诊断版本；它没有修复或重排输入标签。

最终协调员目录：

- remote：`/root/autodl-tmp/backup/p6/p6_qa1r_calibration_validation_20260727_r2/`；
- local：`backups/P6/p6_qa1r_calibration_validation_20260727_r2/`。

`r2` 主要产物 SHA256：

- `validation_report.json`：
  `f8f6d7faca763aee97e5fa160482061dd838c65640613108fd18a920bcb11f1e`；
- `manifest.json`：
  `483547a8d90409b9d368eb237e0b13bec99a94266a55d6732cae19929d3dbe8b`；
- `issues.csv`：
  `1afef5b586611c7b2e1d7061ae10f5b58087eaf100258e411a5e2cc7a23c84bc`；
- `disagreements.jsonl`：
  `134a2a2b5ad0cea23d48d06092258266f099888fa297b037e179ef8077a3d4b7`。

验证前后 frozen `domain_test.jsonl` SHA256 均为
`42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`，
`FROZEN` SHA256 均为
`e12517324c90a7261fcb46df698112dac8f83c2f5c6441e39c4340ada2cee0dd`。

## 7. 下一门禁

当前必须停在质量门。建议的下一独立批准是：

```text
P6_QA1R_GUIDELINE_RECONCILIATION_APPROVED
```

该门禁只能授权双方在独立首轮已经结束后，由协调员组织讨论这 24 条校准分歧并形成
指南 v4。指南锁定后，应从未使用过的非 test 文本生成一套全新、空白、互盲校准集，
再做另一轮独立标注；不得修改这 24 条后把复评分数当作独立一致度。fresh test 重标、
裁决、`v2` 冻结、模型调用和重评分仍需更后的独立门禁。
