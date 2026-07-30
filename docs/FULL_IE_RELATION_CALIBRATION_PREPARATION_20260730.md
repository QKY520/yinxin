# FULL-IE F2 关系校准材料准备报告

日期：2026-07-30

门禁：`FULL_IE_RELATION_CALIBRATION_PREP_APPROVED`（已执行并消耗）

状态：IE020 `DONE`；材料已准备但人工关系标注尚未开始。

## 1. 本步范围

本步仅使用既有 fresh 20-text 非 test 人工实体提交，为 A、B 分别准备关系标注表。
每位标注者只获得自己此前锁定的实体列表。未读取 `domain_test`、dev gold、旧关系、
模型输出或另一标注者的实体，未生成任何真实数据 prompt。

锁定输入：

| 输入 | SHA256 |
| --- | --- |
| A 实体 CSV | `6906142d5894c3a4f1332bed326258b4f9c35958baa17f8e8475339b435f8877` |
| B 实体 CSV | `40428a8ed642685dd7940c60e3dc08af929dcaa4e71c0b7530e89eaa7dbb732e` |
| coordinator map | `6a902ab6e2063b52c1d8103cf777ed25dc2def31371a3f26866f51d3d9664e18` |

## 2. 实现与输出

新增 `scripts/prepare_full_ie_relation_calibration.py`，其生产入口硬性要求环境变量
`FULL_IE_RELATION_CALIBRATION_PREP_APPROVED=1`。脚本执行以下约束：

- 固定核验三份输入及规范/说明文件 SHA256；
- 核验 A/B 各 20 行、coordinator map 完整覆盖和同文本映射；
- 校验实体类型、偏移和词面，并逐单元保留原 `entities_json`；
- 保留 A/B 各自原盲化 ID 和不同顺序；
- 仅新增实体下标导览及三个空白关系字段；
- 使用 staging、原子替换和拒绝覆盖策略；
- 将 A、B delivery 与 coordinator-only map 物理隔离；
- 提供只读 `--audit-only`，对现有包进行输入重锁定、字段、清单、哈希和隔离审计。

远端包：
`/root/autodl-tmp/backup/full_ie/f2_relation_calibration_20260730/`

本地轻量备份：
`D:\yinsir\backups\FULL_IE\f2_relation_calibration_20260730\`

关键输出哈希：

| 输出 | SHA256 |
| --- | --- |
| A relation CSV | `44157617b377178aba0a1a6a2881cfb759b9927526dbbd536deb1dc04dc57411` |
| B relation CSV | `3986d2e1654af3340abaf1cc81a5c41dbb94f261c9a419c61ec82c327842554d` |
| coordinator-only relation map | `0369b2a6837205440a61a95a3932d8db1e164ac20e9083118ed7db32a51e9489` |
| root manifest | `5d2c55c60e24a1cdec12335f567ab5457dd8ee24e1d111ed1692694a48a840a4` |

## 3. 验证结果

AutoDL 在执行前确认为无卡模式：`nvidia-smi -L` 返回 `No devices found`，
`/dev/nvidia0` 不存在，vLLM、Qwen、Stage R 和 verifier 相关进程为空。

- 新增合成测试：`6/6` 通过；
- 仓库全量测试：`158/158` 通过；
- 真实包只读审计：`status=passed`；
- A/B：各 20 行，20 条文本对齐且顺序不同；
- 关系字段：40/40 行保持空白；
- 锁定实体单元：逐单元原样保留；
- A/B delivery：文件清单物理隔离，无 coordinator map；
- 禁止内容文件名扫描：0 命中；
- 本地 10 个回传文件与远端逐项 SHA256 一致。

一次未落盘的一次性 SSH 审计命令因 Bash 引号解析失败而退出；它未执行项目 Python、
未修改包。随后将审计实现为有合成防篡改测试的 `--audit-only` 入口并成功执行。

## 4. 边界、费用和下一门禁

本步未使用 GPU、vLLM、模型/API，未执行 Stage R 或 relation-aware verifier，未读取
`domain_test`，未生成 support/dev/test prompt，未修改论文，也未做 GitHub sync。
付费 GPU 费用为 `0 CNY`。

IE020 完成不构成 RE、CoVe 或完整矩阵证据；完整 full-IE cells 仍为 `0/60`。A/B
不得在当前门禁下开始填写。下一步必须由人工单独开放：

`FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED`

两份返回文件的校验和 exact directed relation calibration 诊断还必须另行开放：

`FULL_IE_RELATION_CALIBRATION_VALIDATION_APPROVED`
