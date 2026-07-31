# FULL-IE F2 关系校准复验报告

日期：2026-07-31

门禁：`FULL_IE_RELATION_CALIBRATION_REVALIDATION_APPROVED`（已执行并消耗）

状态：IE022 `DONE`。人工修订后的 A/B 返回表通过结构门禁，20/20 个配对文本均可完整计算 exact-directed 文件一致性。该结果不是冻结测试 formal IAA，也不支持“关系标注高一致性”主张。

## 1. 输入锁与来源边界

复验使用版本化 `revised_v2` 输入锁，未覆盖首轮 IE021 输入或失败报告。

| 输入 | SHA256 |
| --- | --- |
| A 修订完成表 | `579a1a368e492fa1f3d49f13f3fb4dabe4129eb4ac8b6ecfeea9829d92a63fe3` |
| B 修订完成表 | `4acc4b05358027cb61b4e9ddd3e0d72c10b48468547ad9e06db49f727a24861f` |
| A 原始空白表 | `44157617b377178aba0a1a6a2881cfb759b9927526dbbd536deb1dc04dc57411` |
| B 原始空白表 | `3986d2e1654af3340abaf1cc81a5c41dbb94f261c9a419c61ec82c327842554d` |
| coordinator map | `0369b2a6837205440a61a95a3932d8db1e164ac20e9083118ed7db32a51e9489` |

A/B 各 20 行；四个只读列、盲化顺序、文本、实体 JSON、实体哈希/数量和 coordinator map 均保持不变。用户以协调员身份明确确认两份关系标注均由真人完成。文件校验不能进一步证明修订阶段是否完全无讨论、无互看或无脚本，因此本报告只称“人工修订后的文件一致性”，不称新的首轮盲法 IAA。

## 2. 负结果与实现缺陷留痕

首轮 IE021 的 90 个结构错误及 7 行残缺诊断原样保留，未删除、覆盖或选择性过滤。

修订表第一次复验仍报告 8 个 `RELATION_CROSS_SENTENCE`，且全部集中在同一原文 `domain-candidate-0050`。A/B 在该原文上的五条关系完全一致；人工备注将分号分隔的装备部件枚举视为同一中文句子。检查发现共享 `same_sentence()` 实现错误地把中文/英文分号 `；;` 当作句末边界，而锁定规范只禁止句号等真正句界上的跨句关系。

因此修复共享句界实现：句末边界保留 `。！？!?` 与换行，分号不再切断同一句内的装备枚举。句号跨句拒绝逻辑保持不变，并新增 Stage R 分号枚举回归测试。第一次复验失败产物仍保存在：

- AutoDL：`/root/autodl-tmp/backup/full_ie/f2_relation_calibration_revalidation_20260731/`
- 本地：`D:\yinsir\backups\FULL_IE\f2_relation_calibration_revalidation_20260731\`
- report SHA256：`2bf53cd42c9d030c6e00f498c0572f3dc4804f4dff5937d6cebe1d3138d0e00c`
- issues SHA256：`089de669aba120113dc05311185d970371e9f172a805fa561b2463788f60fac7`

## 3. 最终结构门禁

句界实现修复后，以相同 `revised_v2` 输入在新目录复验：

- 结构错误：`0`
- 完整有效配对文本：`20/20`
- A 关系数：`44`
- B 关系数：`71`
- 零关系文本：A `4`，B `2`
- 完全一致文本：`9/20`
- 分歧文本：`11/20`

疑点码按行统计：A 共 8 行，其中 `SAME_SENTENCE=6`、`ENDPOINT_ENTITY=1`、`USES_VS_PART_OF=1`；B 共 6 行，其中 `SAME_SENTENCE=4`、`EXPLICITNESS=1`、`USES_VS_PART_OF=1`。`SAME_SENTENCE` 表示按规范放弃依赖代词或跨句回指的候选关系；一行仍可保留其他具有同句显式端点的关系。

## 4. Exact-Directed 文件一致性

以下 precision/recall 以 A 文件为参照、B 文件为比较侧；F1 是对称的集合重合诊断。所有关系同时要求端点跨度、端点类型、方向和关系类型完全一致。

| 范围 | TP | FP | FN | P | R | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall | 24 | 47 | 20 | 0.338028 | 0.545455 | 0.417391 |
| `USES` | 13 | 11 | 3 | 0.541667 | 0.812500 | 0.650000 |
| `HAS_METRIC` | 3 | 4 | 0 | 0.428571 | 1.000000 | 0.600000 |
| `PART_OF` | 8 | 32 | 17 | 0.200000 | 0.320000 | 0.246154 |

成功标准预先定义为“零结构错误并完整披露诊断”，没有事后设置 F1 阈值。因此 IE022 结构门禁完成，但低 F1 明确削弱关系质量主张，尤其 `PART_OF`。不得把 `0.417391` 描述为高一致性、冻结测试 IAA 或模型 RE 结果。

## 5. 验证、备份与边界

- 分号句界与 Stage R 核心定向测试：`14/14` 通过。
- 版本化输入锁与关系校验器定向测试：`7/7` 通过。
- AutoDL 最终全量测试：`166/166` 通过；其中涉及 `domain_test` 名称的测试只使用临时合成 fixture，未读取真实冻结数据。
- AutoDL 为无卡模式：`nvidia-smi -L` 返回 `No devices found`，`/dev/nvidia0` 不存在；无 vLLM、Qwen、Stage R 或 verifier 模型进程。
- 未读取真实 `domain_test`，未生成真实 support/dev/test prompt，未调用模型/API/vLLM，未使用 GPU，未修改论文，未做 GitHub sync。
- 未读取、执行、修改或提交任何未跟踪 P6 用户脚本。
- 付费 GPU 费用：`0 CNY`。

最终成功产物：

- AutoDL：`/root/autodl-tmp/backup/full_ie/f2_relation_calibration_revalidation_v2_20260731/`
- 本地：`D:\yinsir\backups\FULL_IE\f2_relation_calibration_revalidation_v2_20260731\`
- report SHA256：`9fc15cf720f470b5f37366eb70fb1657eb42d52527e7859ebf44ee52ebb6bef8`
- issues SHA256：`731c21b07f2b82920c02a31b6eebc1c255e4d041dc508506c7b36c124cb4aa50`
- disagreements SHA256：`13ef169c0a0c93248b5e31f9c59c1a4c2683e05d74385bc9734381dbda0b3a0c`
- manifest SHA256：`b6d95de65bdf16b16daca56e762eaad6c0c7d3496cf2b32367fc057f2f056fdd`

完整 full-IE 单元仍为 `0/60`。F2 校准诊断已完成并披露；这没有授权 F3/F4、真实 Stage R、dev sanity、GPU 实验或论文更新。下一步只能在新的明确门禁下进行 F3 无卡配置与资源冻结。
