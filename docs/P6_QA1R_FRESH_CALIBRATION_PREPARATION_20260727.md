# P6-QA1R 全新非 test 校准材料准备报告

日期：2026-07-27

执行门禁：`P6_QA1R_FRESH_CALIBRATION_PREP_APPROVED`

结论：全新空白校准包已经生成并独立重载验证，状态为
`prepared_blank_not_started`。本门禁只完成材料准备；两名真人尚未开始标注，当前
没有校准分数或 formal IAA。

## 1. 范围与锁定输入

本轮只在 AutoDL GPU-free 模式下使用：

- `domain_dev.jsonl` 的 ID 与文本，SHA256：
  `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`；
- 已退役首轮 24 条的 coordinator map，SHA256：
  `a42511bd41bef0666c703c8d4e6ca1eb623688bba0e3b872786f164fedb3b18b`；
- 锁定指南 v4，SHA256：
  `a15289cd0f45bc23a0ce9d981db24745b814cfb94c6b03687e60a13b81b6ca80`；
- A/B 独立说明，SHA256 分别为
  `5f0cf56819a10e76e0a2639257b8c051af213e4ee2dfe6accdbf077509e9b136`
  和
  `432acf0f19315e9eb089726126c33aabc9e7830d2fe7ea243078c4f3ea180c65`。

旧 map 仅用于按文本哈希排除旧题。现有 dev 实体/关系未导出，也未用于选择或作为
答案；未读取 frozen test、P5 预测、prompt 或模型输出。

## 2. 容量审计与确定性选择

50 条 `domain_dev` 被严格分为：

| 分区 | 条数 |
| --- | ---: |
| 已退役首轮校准 | 24 |
| 本轮新选 | 20 |
| 未使用后备 | 6 |

旧题与新题文本哈希交集为 0。剩余 26 条的纯文本风险线索候选数为：

| 风险桶 | 候选数 | 本轮分配 |
| --- | ---: | ---: |
| `METRIC` | 20 | 5 |
| `TECH_SCHEME` | 18 | 5 |
| `EQUIPMENT_MODULE` | 23 | 5 |
| `REPEATED_MENTION` | 18 | 5 |

选择方法是“退役哈希排除后，按 seed `2026072701` 做确定性桶匹配”。20 条用于本轮，
保留 6 条作为 coordinator-only 后备。风险桶只是文本覆盖线索，不是 gold 标签；四类
是否被两人实际标出，只能在独立标注完成后验证。

## 3. 交付包与哈希

远端：

`/root/autodl-tmp/backup/p6/p6_qa1r_fresh_calibration_20260727/`

本地：

`backups/P6/p6_qa1r_fresh_calibration_20260727/`

根 manifest SHA256：

`bc404d4aeb6c2cab1c303ac063f9fdd43b950a587787cc222dcabbc4a9adba00`

主要文件：

| 角色 | 文件 | 行数 | SHA256 |
| --- | --- | ---: | --- |
| A-only | `annotator_a_delivery/annotator_a_fresh_calibration.csv` | 20 | `df8b99c99b83ecbe71b38b352d584fd1e0dc67df93ba4b1a9c347c14e984c89c` |
| B-only | `annotator_b_delivery/annotator_b_fresh_calibration.csv` | 20 | `b7e7df0c7331c1af379cda8e01c6287c8de2e644d82758e170ad3c26699c6ff1` |
| coordinator-only | `coordinator_only/coordinator_map.jsonl` | 20 | `6a902ab6e2063b52c1d8103cf777ed25dc2def31371a3f26866f51d3d9664e18` |
| coordinator-only | `coordinator_only/reserve_map.jsonl` | 6 | `20fe19da3911ad56d478e23c32c021f6fb3c5b340bf784d72963b6d88f228c9b` |

A/B delivery manifest SHA256 分别为：

- A：`8b004c671577f7fb8fc8507d46e596331aa1ec5837735187273d251ed78cb086`；
- B：`28676033ca10381d22e3f9127d542628368ea56ca6d2da7d4939d910636d3a0a`。

每个 annotator 目录只包含自己的空白 CSV、自己的说明、共同的锁定 v4 指南和自己的
delivery manifest。任何 coordinator 文件都不在 A/B 目录中。

## 4. 验证结果

新增准备器和 4 项专门测试；连同旧准备器 3 项回归测试，AutoDL 无卡环境共 7 项全部
通过：

- `scripts/prepare_p6_qa1r_fresh_calibration.py`；
- `tests/test_prepare_p6_qa1r_fresh_calibration.py`。

对实际输出重新打开并验证：

- A/B 各 20 行，字段名完全一致；
- `entities_json`、`notes`、`uncertainty_code` 全部为空；
- A/B 文本集合相同但顺序不同，blind ID 前缀分别为 `P6FRESH-A/B`；
- A/B/map 文本哈希完全对齐；
- 退役 24、新选 20、后备 6 互不重叠并完整分割 50 条 dev；
- A/B 目录物理隔离，均不含 coordinator map；
- 本地、远端及 delivery 副本哈希一致。

## 5. 下一人工门禁与交付红线

当前不要让两人填写。下一步需要明确批准：

```text
P6_QA1R_FRESH_CALIBRATION_ANNOTATION_APPROVED
```

批准后：

1. 只把完整 `annotator_a_delivery` 目录交给标注者 A；
2. 只把完整 `annotator_b_delivery` 目录交给标注者 B；
3. 必须是两名不同真人，各自独立完成全部 20 行；
4. 不得发送根 manifest、`coordinator_only`、另一人的目录或旧 24 条文件；
5. 不得使用 AI/LLM、共享答案字典或自动补 mention/裁决重叠的脚本；
6. 两人各自完成单表 preflight 后分别返回，协调员先锁 SHA256；两份均锁定前不比较、
   不反馈中间分数。

标注完成后的结构验证和 exact span+type 一致度计算仍需后续独立门禁。本轮没有修改
任何 gold 或 frozen 文件，没有模型、dry-run、vLLM 或 paid GPU 活动，成本为 0 CNY。
