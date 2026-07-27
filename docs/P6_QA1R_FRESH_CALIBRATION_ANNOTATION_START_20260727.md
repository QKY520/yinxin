# P6-QA1R 全新校准双人独立标注启动记录

日期：2026-07-27

批准门禁：`P6_QA1R_FRESH_CALIBRATION_ANNOTATION_APPROVED`

状态：`authorized_waiting_for_two_human_returns`。本门禁只授权两名不同真人领取各自
隔离的空白交付目录并独立完成全部 20 行；尚未授权协调端比较、验证、裁决或计算分数。

## 1. 交给标注者 A

只交付整个目录：

`D:\yinsir\backups\P6\p6_qa1r_fresh_calibration_20260727\annotator_a_delivery\`

其中空白表为：

`annotator_a_fresh_calibration.csv`

原始 SHA256：

`df8b99c99b83ecbe71b38b352d584fd1e0dc67df93ba4b1a9c347c14e984c89c`

A 完成自己的单表 preflight 后，必须“另存为”：

`annotator_a_fresh_calibration_completed.csv`

不得覆盖或删除原始空白表。

## 2. 交给标注者 B

只交付整个目录：

`D:\yinsir\backups\P6\p6_qa1r_fresh_calibration_20260727\annotator_b_delivery\`

其中空白表为：

`annotator_b_fresh_calibration.csv`

原始 SHA256：

`b7e7df0c7331c1af379cda8e01c6287c8de2e644d82758e170ad3c26699c6ff1`

B 完成自己的单表 preflight 后，必须“另存为”：

`annotator_b_fresh_calibration_completed.csv`

不得覆盖或删除原始空白表。

## 3. 两人共同遵守但互不交流标签

1. A 和 B 必须是两名不同真人，各自完成自己文件中的全部 20 行，不能分工。
2. 只依据各自目录中的锁定 v4 指南和角色说明；不得打开另一人的目录。
3. 不得查看旧 24 条、dev gold、frozen test、预测、建议答案或 coordinator map。
4. 不得使用 AI/LLM、共享答案字典或自动补 mention、自动裁决重叠、自动写标签脚本。
5. 可以使用普通全文查找，以及只报告格式/offset 问题且不修改标签的结构检查工具。
6. 对疑难项仍填写当前最佳标签并使用合法疑点码；不得留空或跳过整类。
7. 两份完成文件均返回并分别锁定 SHA256 前，不讨论具体样本，不比较文件，不反馈
   中间一致度。

若有人误看另一份文件、看到答案/预测、收到非空表，或发现必须新增规则才能继续，
立即停止并向协调员报告；不得事后补造独立来源。

## 4. 协调员回收协议

两份完成文件分别返回后，协调员将其保存到：

`D:\yinsir\backups\P6\p6_qa1r_fresh_calibration_completed_20260727\`

在任何比较前：

1. 确认文件名分别为上述 A/B completed 名称；
2. 只计算并记录每份文件 SHA256，不修改内容；
3. 确认两人书面声明未查看对方文件、未使用 AI/自动写标签脚本；
4. 保留两台电脑上的原始完成副本，不让任何一方根据分数回改。

完成回收后，下一门禁为：

```text
P6_QA1R_FRESH_CALIBRATION_VALIDATION_APPROVED
```

该后续门禁才授权在 AutoDL 无卡环境做结构验证和 exact span+type 文件一致度计算；
仍不授权 formal test、裁决、gold/frozen 修改、模型调用或重评分。
