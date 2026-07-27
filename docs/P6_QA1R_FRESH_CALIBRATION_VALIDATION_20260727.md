# P6-QA1R 全新非 test 双人真人校准验证报告

日期：2026-07-27

执行门禁：`P6_QA1R_FRESH_CALIBRATION_VALIDATION_APPROVED`

结论：协调员已明确确认两份提交均为两名真人的独立标注结果。本轮 20 条全新非 test
校准的 exact span+type micro-F1 为 **`0.8000`**，结构门全部通过，达到项目原始最低线
`>=0.80`；但未达到锁定 v4 的保守校准目标 `>=0.85`，所以自动验证器状态仍为
`blocked`。该数值是 human calibration agreement，不是 frozen-test formal IAA。

## 1. 锁定输入与来源确认

| 输入 | SHA256 |
| --- | --- |
| A blank | `df8b99c99b83ecbe71b38b352d584fd1e0dc67df93ba4b1a9c347c14e984c89c` |
| B blank | `b7e7df0c7331c1af379cda8e01c6287c8de2e644d82758e170ad3c26699c6ff1` |
| A completed | `6906142d5894c3a4f1332bed326258b4f9c35958baa17f8e8475339b435f8877` |
| B completed（最终重写版） | `40428a8ed642685dd7940c60e3dc08af929dcaa4e71c0b7530e89eaa7dbb732e` |
| coordinator map | `6a902ab6e2063b52c1d8103cf777ed25dc2def31371a3f26866f51d3d9664e18` |
| fresh-package manifest | `bc404d4aeb6c2cab1c303ac063f9fdd43b950a587787cc222dcabbc4a9adba00` |

B 最终文件覆盖了此前待验证副本；旧 B 哈希未进入本次计算。协调员在项目对话中明确
确认两份最终 CSV 均为真人标注，并要求按真人结果验证。该确认记录在
`human_provenance_attestation.json` 中。

## 2. 结构门

| 检查 | 结果 |
| --- | ---: |
| A/B/map 行数 | 20/20/20 |
| blind ID、文本、文本哈希对齐 | 通过 |
| hard errors | 0 |
| non-order hard errors | 0 |
| blocking reviews | 0 |
| issue rows | 0 |
| 严格有效配对 | 20/20 |
| 四类均由双方实际覆盖 | 是 |

验证器未修改、排序、补齐或裁决任何实体；所有指标直接来自两份锁定 completed CSV。

## 3. 总体一致度

| 指标 | 值 |
| --- | ---: |
| A/B 实体数 | 175 / 220 |
| exact matches | 158 |
| P（B 对 A） | `0.718182` |
| R（B 对 A） | `0.902857` |
| exact span+type micro-F1 | **`0.800000`** |
| 完全一致行 | 5/20 |
| 含分歧行 | 15/20 |

本轮刚好达到原始项目最低要求 `0.80`，没有安全余量。B 比 A 多标 45 个实体，是总体
precision 较低、15 行仍含分歧的主要数量背景。

## 4. 分类型结果

| 类型 | A/B 数量 | exact | F1 |
| --- | ---: | ---: | ---: |
| `EQUIPMENT` | 75/109 | 67 | `0.728261` |
| `MODULE` | 84/94 | 80 | `0.898876` |
| `TECH_SCHEME` | 6/7 | 1 | `0.153846` |
| `METRIC` | 10/10 | 10 | `1.000000` |

`MODULE` 与 `METRIC` 已具有较好一致度；风险集中在 `TECH_SCHEME`，其次为
`EQUIPMENT` 的是否纳入/边界差异。总体 micro-F1 被实体数量较多的 MODULE 和完全一致
的 METRIC 拉高，不能用总体 `0.80` 掩盖 TECH_SCHEME 的明显不稳定。

## 5. 阈值判定与可写范围

- 原始项目最低门 `>=0.80`：**达到，且恰好达到**；
- 锁定 v4 保守校准目标 `>=0.85`：**未达到**；
- 自动验证器 `agreement_target_met`：`false`；
- fresh human calibration agreement：`0.8000`；
- frozen-test formal human IAA：`null`，尚未执行 formal test 双标/盲裁决。

当前可以准确写成：

> 在 20 条未用于旧校准的非 test 文本上，两名真人依据锁定 v4 指南独立标注，exact
> span+type micro-F1 为 0.8000；其中 TECH_SCHEME 一致度仍低，是后续正式审计前的
> 主要限制。

不能写成“正式测试集 IAA=0.80”“全部类别一致性良好”或“质量控制已经全部完成”。

## 6. 产物与完整性

远端：

`/root/autodl-tmp/backup/p6/p6_qa1r_fresh_calibration_validation_20260727_r2/`

本地：

`backups/P6/p6_qa1r_fresh_calibration_validation_20260727_r2/`

| 文件 | SHA256 |
| --- | --- |
| `validation_report.json` | `d41ac655264cf3127f6d9e92a2f8173c19bbf08983a3aad675aec1e4b67f7bc5` |
| `issues.csv` | `731c21b07f2b82920c02a31b6eebc1c255e4d041dc508506c7b36c124cb4aa50` |
| `disagreements.jsonl` | `8937721b61c25597cd37972c3987a1dd419fc56fedfcdec59a4b5e3aaaa7b24a` |
| `manifest.json` | `a257e2133d07415344b4d8b598a467fd551977041dcc6700bf391c429aa12e1a` |
| `human_provenance_attestation.json` | `2268052ccccbdc5ed060d2fd1d308497c2965d9f717b66f02a11513a02959c5b` |
| `overall_summary.json` | `3340e329e41f6b5de7785dd0b3702e3eb0de56d4250fcfdc45f1108a7824350d` |

六项现有验证器测试在 AutoDL 无卡环境全部通过。`domain_test.jsonl` 与 `FROZEN` 哈希
保持不变；未读取 test、旧 dev gold、预测、prompt 或模型输出，未运行模型、dry-run、
vLLM 或 paid GPU，成本为 0 CNY。

## 7. 下一决策

不得修改这 20 条后重新计算以追求更高分。后续需要在两个诚实选项中明确选择：

1. 接受原始最低门 `0.80`，保留 TECH_SCHEME 限制，GPU-free 规划 formal test 双标
   审计；或
2. 坚持 v4 的 `0.85` 保守目标，先做新的 guideline v5 协调，并另外准备全新非 test
   文本重新校准。

两条路线都不自动授权读取/修改 frozen test、裁决、重评分或模型调用。
