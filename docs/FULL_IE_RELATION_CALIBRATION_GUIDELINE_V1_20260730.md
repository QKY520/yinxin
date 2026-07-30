# FULL-IE 关系校准标注规范 v1（锁定候选版）

日期：2026-07-30

适用范围：固定的 20 条非 test 关系校准文本。本文只规定在每位标注者自己此前
提交并已锁定的实体列表上标注显式有向关系。不得修改、增加、删除或重排实体。

当前状态：材料准备阶段。只有协调员明确开放
`FULL_IE_RELATION_CALIBRATION_ANNOTATION_APPROVED` 并单独交付经哈希核验的
个人材料后，标注者才能开始填写。

## 1. 输出格式

每行提供：

- `blind_id`：该标注者此前材料中的盲化编号，只读；
- `text`：原文，只读；
- `entities_json_locked`：该标注者此前独立提交的实体列表，只读；
- `entity_index_guide`：实体下标、类型和词面的只读显示；
- `relations_json`：本轮唯一必填标签字段；
- `relation_notes`：可选说明；
- `relation_uncertainty_code`：可选疑点码。

关系数组格式：

```json
[{"head":0,"tail":1,"type":"USES"}]
```

`head` 和 `tail` 必须是 `entities_json_locked` 的零基下标。关系按
`(head,tail,type)` 升序，不得重复，不得自指。无关系必须填写 `[]`，不能留空。
不得修改 `blind_id`、`text`、`entities_json_locked` 或 `entity_index_guide`。

如果原文存在关系但个人锁定实体列表缺少必要端点，不得补实体、改边界或引用虚构
下标；该关系不写入数组，并填写 `ENDPOINT_ENTITY` 疑点码和简短说明。

## 2. 固定关系类型与方向

以下矩阵来自已审批的 `p2-schema-draft-v3`，名称、端点类型和方向均不得改变。

| 关系 | 允许的 head | 允许的 tail | 判定规则 |
| --- | --- | --- | --- |
| `USES` | `EQUIPMENT` / `MODULE` | `EQUIPMENT` / `MODULE` / `TECH_SCHEME` | head 明确使用、采用、搭载、部署、挂载、装备、配装、安装或配置 tail |
| `HAS_METRIC` | `EQUIPMENT` / `MODULE` | `METRIC` / `TECH_SCHEME` | tail 明确描述 head 的规格、能力、参数概念或可测技术属性 |
| `PART_OF` | `EQUIPMENT` / `MODULE` | `EQUIPMENT` / `MODULE` | head 明确是 tail 的组成部分，方向固定为“部分 -> 整体” |

`USES` 与 `PART_OF` 必须区分：

- `搭载`、`部署`、`挂载`、`装备`、`配装`、`携带`、`装载`、`加装`通常支持
  `USES`，不能仅因物理接触改成 `PART_OF`；
- `组成`、`包括`、`包含`、`构成`、`是……的一部分`、`归属`、`隶属`、`下辖`、
  `由……组成`才支持 `PART_OF`；
- 没有明确使用或组成证据时，不凭领域常识补关系。

## 3. 显式证据规则

1. 关系两端必须是同一句中的显式实体词面。
2. 不通过“它”“该平台”“该系统”等代词或省略成分建立关系。
3. 不做跨句共指、逆关系、对称关系或传递关系推断。
4. 否定、假设、疑问或未证实的关系不标；普通引述中的明确事实可以按原文标。
5. 控制、调度、测试、打击、研制、评价或共同出现本身不自动构成三类关系。
6. 一对端点只有在原文分别明确支持时才可同时具有多种关系。
7. 实体类型矩阵不匹配时不得强行选择最接近的关系类型。

## 4. 合成示例

示例一：

```text
苍穹无人机搭载侦察雷达并采用卫星导航技术，最大航程达到500公里。
```

若锁定实体依次为 `苍穹无人机(EQUIPMENT)`、`侦察雷达(MODULE)`、
`卫星导航技术(TECH_SCHEME)`、`最大航程达到500公里(METRIC)`，则关系为：

```json
[
  {"head":0,"tail":1,"type":"USES"},
  {"head":0,"tail":2,"type":"USES"},
  {"head":0,"tail":3,"type":"HAS_METRIC"}
]
```

示例二：

```text
信号处理模块是海岳雷达的组成部分。
```

若锁定实体依次为 `信号处理模块(MODULE)`、`海岳雷达(EQUIPMENT)`，则关系为：

```json
[{"head":0,"tail":1,"type":"PART_OF"}]
```

示例三：

```text
试验人员评估了北辰雷达，该系统随后完成测试。
```

“评估”“完成测试”不属于三类关系，且不得通过“该系统”建立关系，因此填写：

```json
[]
```

## 5. 疑点码

可以使用一个或多个下列代码，多个代码用分号分隔并去重：

- `DIRECTION`
- `TYPE_MATRIX`
- `USES_VS_PART_OF`
- `EXPLICITNESS`
- `SAME_SENTENCE`
- `NEGATION_HYPOTHETICAL`
- `ENDPOINT_ENTITY`
- `OTHER`

疑点码不能代替 `relations_json`。除缺少锁定端点的情况外，仍应填写当前独立判断。

## 6. 独立性和停止条件

- A、B 必须各自完成全部 20 行，不得分工、讨论具体样本或交换文件。
- 不得查看 dev gold、另一人的实体或关系、coordinator map、模型预测、prompt、旧关系
  标签或中间一致度。
- 不得使用 AI/LLM、共享答案字典或自动生成、补全、修复关系的脚本。
- 如误看到另一人的材料、答案或评分，或发现需要新增规则，立即停止并报告。
- 两份完成文件都被独立锁定 SHA256 前，不得比较或反馈中间结果。

本轮以后计算的 exact directed relation F1 只作为非 test 人工校准诊断，不是 frozen
test formal IAA，也不证明 frozen test 关系标签经过独立双人标注。
