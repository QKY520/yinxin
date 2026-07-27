# P6-QA1R 标注指南 v4 锁定记录

日期：2026-07-27

批准门禁：`P6_QA1R_GUIDELINE_V4_LOCK_APPROVED`

## 1. 锁定对象

- 锁定前草案：
  `docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_DRAFT_20260727.md`；
- 锁定前草案 SHA256：
  `7b9c9b89b280ad03f90799d1130c1826bc7508544d6c6b08ed99d4de423af38e`；
- 唯一生效的锁定版：
  `docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md`；
- 锁定版 SHA256：
  `a15289cd0f45bc23a0ce9d981db24745b814cfb94c6b03687e60a13b81b6ca80`。

锁定操作只将文件改名为 `LOCKED`，更新标题、状态和后续门禁表述；实体范围、类型、
边界、重复 mention、疑点码和单表 preflight 等标注决策规则均未实质改写。

## 2. 本门禁授权与未授权事项

本门禁只授权锁定 v4、记录哈希、同步文档和更新最新状态源。

本门禁未授权：

- 修改、裁决或重新计分首轮 24 条校准标签；
- 生成下一轮校准表或选择下一轮文本；
- 读取 dev gold、frozen test、P5 预测或 coordinator map 作为标注答案；
- 正式 test 重标、裁决、`v2` 冻结或统一重评分；
- 模型调用、dry-run、vLLM 或 paid GPU。

## 3. 完整性边界

- `domain_test.jsonl` SHA256：
  `42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0`；
- `FROZEN` SHA256：
  `e12517324c90a7261fcb46df698112dac8f83c2f5c6441e39c4340ada2cee0dd`。

首轮 24 条继续作为教学/复盘材料退役，不得修改后重新声称为独立校准。

## 4. 下一门禁

只有负责人另行批准以下门禁，才可准备新的空白校准材料：

```text
P6_QA1R_FRESH_CALIBRATION_PREP_APPROVED
```

该后续门禁也不自动授权真人标注、正式 test 重标、裁决或 frozen 数据变更。
