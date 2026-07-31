# FULL-IE F2 关系校准验证报告

日期：2026-07-31

门禁：`FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED`（已执行并消耗）

状态：IE021 `BLOCKED`。返回表未通过锁定规范的结构门禁，当前不得进入 F3/F4。

## 1. 输入与完整性

本次只读取两份返回的非 test 关系表、两份原始空白交付表和 coordinator-only
映射。固定输入如下：

| 输入 | SHA256 |
| --- | --- |
| A 完成表 | `444f46428f8b3d3bc61c39cda7bd1330ab80b4ebd6d1fc4f83b92fb31083726a` |
| B 完成表 | `5489aa8128494e12655893dc54a6124250535f5116ed11417ed19733cab46066` |
| A 空白表 | `44157617b377178aba0a1a6a2881cfb759b9927526dbbd536deb1dc04dc57411` |
| B 空白表 | `3986d2e1654af3340abaf1cc81a5c41dbb94f261c9a419c61ec82c327842554d` |
| coordinator map | `0369b2a6837205440a61a95a3932d8db1e164ac20e9083118ed7db32a51e9489` |

A/B 均为 20 行；盲化 ID、文本、锁定实体 JSON、实体下标导引、行顺序、实体
哈希和 coordinator map 对齐全部保持不变。输入未被修复或覆盖。

## 2. 结构门禁结果

共发现 90 个硬结构错误：

| 错误 | 数量 | 含义 |
| --- | ---: | --- |
| `RELATION_CROSS_SENTENCE` | 70 | 关系端点跨越固定同句边界 |
| `RELATION_TYPE_MATRIX` | 18 | 端点类型或方向不符合审批矩阵，例如 `METRIC -> EQUIPMENT` 的 `HAS_METRIC` |
| `UNCERTAINTY_INVALID` | 2 | 使用了关系规范未批准的 `METRIC_SCOPE` 疑点码 |

只有 7/20 个对齐文本在两边都结构有效。由于成功标准是“零结构错误和完整披露”，
IE021 必须标记为 `BLOCKED`，不得通过放宽规则、删除关系或自动修表改成通过。

## 3. 残缺子集诊断

验证器仍保留了 7 个可评分文本的诊断：TP=10、FP=15、FN=9、precision
`0.400000`、recall `0.526316`、F1 `0.454545`。其中 `USES` F1 为
`0.888889`，`PART_OF` F1 为 `0.342857`；该子集没有可比较的
`HAS_METRIC` 标签。

这些数值只描述结构有效的残缺子集，不是完整 20 文本关系校准结果，不是 frozen
test formal IAA，也不得进入论文结果表或支持关系质量主张。

## 4. 来源边界

验证器只能证明文件完整性和文件间一致性，不能证明两名真人在不讨论、不互看、
不使用 AI/LLM 或自动脚本的条件下独立完成。工作区新增未跟踪文件
`p6_relation_annotate.py`；本门禁没有读取、执行、修改或提交该用户文件。因此在
协调员另行提供明确来源说明前，返回表不得描述为已验证的独立双人关系标注。

## 5. 验证、备份与边界

- 新增合成验证测试：`6/6` 通过；
- AutoDL 仓库全量测试：`164/164` 通过；
- AutoDL 模式：无卡，`nvidia-smi -L` 为 `No devices found`，`/dev/nvidia0`
  不存在，无 vLLM、Qwen、Stage R 或 verifier 进程；
- 未读取 `domain_test`，未生成真实 prompt，未调用模型/API/vLLM，未使用 GPU，
  未修改论文，未做 GitHub sync；
- 付费 GPU 费用：`0 CNY`；
- 远端报告目录：
  `/root/autodl-tmp/backup/full_ie/f2_relation_calibration_validation_20260731/`；
- 本地备份目录：
  `D:\yinsir\backups\FULL_IE\f2_relation_calibration_validation_20260731\`；
- 报告 SHA256：`7cf7123ac104597200b98a18368423f948593227e7a2ffdcd6b76c43edd8b6ed`；
- issues SHA256：`7d579cbac33ee9ce29167ca70e6f7e023b736571c92a4b6dc89981346aa40ad1`；
- disagreements SHA256：`8349edd9e2a14247ef0c725d2cfbd3ab291c3e3e71137ab94ba97fef9e0a4a4a`；
- manifest SHA256：`2cb4b1961a96aa8a68db052023eb6852db7aec3f3f2f208f9ad4ac6b122e8ef9`。

完整 full-IE cells 仍为 `0/60`。下一步必须先由人类澄清关系标注来源，再另行决定
是否废弃本轮返回表并使用新的未用非 test 文本重新准备独立人工校准。当前没有开放
任何修表、重标、F3 配置、dev sanity、GPU 实验或论文门禁。
