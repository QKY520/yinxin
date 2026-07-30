# FULL-IE 关系校准标注者 A 独立说明

日期：2026-07-30

当前状态：仅准备材料，尚未授权开始标注。等待协调员明确开放
`FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED`，并只接收 A 专属目录。

## 开始前

1. 完整阅读同目录的 `FULL_IE_RELATION_CALIBRATION_GUIDELINE_V1_20260730.md`。
2. 核对 A 表文件名、20 行记录和 delivery manifest 中的 SHA256。
3. 确认 `relations_json`、`relation_notes`、`relation_uncertainty_code` 均为空。
4. 确认没有 B 文件、coordinator map、gold、关系答案、预测或评分。
5. `blind_id`、`text`、`entities_json_locked` 和 `entity_index_guide` 均为只读；
   `entities_json_locked` 是 A 自己此前锁定的实体提交，不得修改或重排。

## 填写要求

- 独立完成 A 表全部 20 行。
- 只填写 `relations_json`、`relation_notes` 和 `relation_uncertainty_code`。
- 有关系时使用实体零基下标；无关系填写 `[]`。
- 缺少必要实体端点时不补实体，使用 `ENDPOINT_ENTITY` 并说明。
- 不读取 B 材料，不与 B 讨论样本，不使用 AI/LLM 或自动标签脚本。

提交前确认每行 `relations_json` 可解析、关系类型和方向合法、无重复或自指、所有行
均已完成。只返回 A 表。协调员锁定 SHA256 后不得自行继续修改。
