# P3 D(RAG) vs C(Glossary) 人工审计表 - 2026-07-23

## 审计目标

这次只审计一个问题：

```text
D 的 FP 比 C 少了 31 个，这些减少是否主要是真错误实体被 RAG 压掉？
```

如果答案是“是”，D(RAG) 就是一个可接受的正结果，可以继续准备
E/E-prime verification。  
如果答案是“否”，需要先分析 RAG 噪声或 prompt overload，不能继续扩大实验。

## 对比文件

C 结果：

```text
results/p3/p3_domain_dev50_c_glossary_k5_sanity_sanitize_per_query.jsonl
```

D 结果：

```text
results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl
```

每条样本按 `id` 对齐，看：

```text
gold
C.pred_raw
D.pred_raw
D.rag_passages
D.sanitization_flags
```

## 审计样本选择

建议审计 20 条。

不用平均抽，优先看差异大的：

```text
1. D 明显好于 C：8 条
2. D 明显差于 C：5 条
3. D 的 FP 明显下降：4 条
4. D 有 sanitizer flags：3 条
```

如果同一条同时属于多个组，可以合并，不必强行凑满。

## 每条样本怎么判断

每条只回答 6 个问题：

```text
1. D 比 C 是更好、持平、还是更差？
2. D 是否删掉了 C 的错误实体？
3. D 是否误删了 C 的正确实体？
4. D 是否新增了新的错误实体？
5. D 的 RAG evidence 是否与 query 同主题？
6. 这条最终判为 GOOD / OK / POOR？
```

判断标准：

```text
GOOD:
D 删除了 C 的明显虚标/错类型实体，且没有明显漏掉正确实体。
RAG evidence 与 query 同主题，能解释为什么输出更稳。

OK:
D 与 C 差异很小，或者有小改进但证据不强。
错误主要来自模型自身，不明显由 RAG 引入。

POOR:
D 删除了 C 的正确实体，或 RAG evidence 引入了新虚标/类型错。
RAG evidence 与 query 明显无关。
```

## 样本审计记录 — 20 条

### 样本 1 — 彩虹-7（+0.600，最大改善）

```text
id: domain-candidate-0096
D vs C: 更好

C 的主要问题: 过标严重。C 将 7 个描述性短语（"持续侦察""警戒探测""防空压制""作战支援"等）全部标为 MODULE，且遗漏 gold 中的"彩虹系列无人机"

D 的主要变化: 删除全部 7 个 FP 描述性短语，新增 1 个 gold TP（彩虹系列无人机 EQUIPMENT），保留 2 个正确实体

RAG evidence 是否相关: partial — top-1 是固体火箭发动机/激光引信（弹药相关），非无人机

D 是否删掉 C 的错误实体: 是（7/7 全删）

D 是否误删 C 的正确实体: 否

D 是否新增错误实体: 轻微（1 个——"高空、高速、隐身、长航时的无人机"作为 MODULE，边界过长但不离谱）

结论: GOOD
一句话理由: RAG 帮助模型从 eager 过标模式收敛到保守模式，7 个 FP 全清，并补回遗漏的 gold 实体。
```

### 样本 2 — 反坦克火箭（+0.500，F1=1.0）

```text
id: domain-candidate-0005
D vs C: 更好

C 的主要问题: 2 个 FP（过标实体）

D 的主要变化: 删除全部 2 个 FP，仅保留 1 个完全正确的 gold TP

RAG evidence 是否相关: partial — top-1 是固体火箭发动机，top-2/3 是天王星-9 无人战车/无人机直升机

D 是否删掉 C 的错误实体: 是（2/2 全删）

D 是否误删 C 的正确实体: 否

D 是否新增错误实体: 否

结论: GOOD
一句话理由: RAG 的弹药/武器主题帮助模型确认 query 中只有 1 个核心装备实体，不再过标。
```

### 样本 3 — Joanna 吊舱（+0.266）

```text
id: domain-candidate-0237
D vs C: 更好

C 的主要问题: 漏标严重（漏了 Joanna、双波面固态激光器、阵风、幻影2000-D 等 7 个 gold），且将"图像导引武器""非制导武器"错标为 MODULE

D 的主要变化: 新增 3 个 TP（补回双波面固态激光器、阵风、幻影2000-D），修复类型，净增 FP 仅 1 个

RAG evidence 是否相关: partial — top-1 是激光跟踪/目标瞄准系统，与 Joanna 吊舱功能类似

D 是否删掉 C 的错误实体: 是（2/6 删除）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 轻微（1 个）

结论: GOOD
一句话理由: RAG 的激光瞄准系统证据与吊舱主题相关，帮助模型恢复 3 个遗漏的 gold 实体，类型修复合理。
```

### 样本 4 — 成像装置对焦（+0.222）

```text
id: domain-candidate-0034
D vs C: 更好

C 的主要问题: 3 个 FP（过标实体），C pred=5 但 gold=4

D 的主要变化: 删除全部 3 个 FP，pred=2（保守模式），零误删

RAG evidence 是否相关: **噪声** — top-1 是 GPS 制导系统（完全无关），但 D 仍改善了

D 是否删掉 C 的错误实体: 是（3/3 全删）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: GOOD
一句话理由: RAG 证据与 query 无关但 D 仍变好——可能是 RAG 段落作为"结构锚点"让模型更保守，而非内容驱动。
```

### 样本 5 — 炮兵侦察系统（+0.205）

```text
id: domain-candidate-0097
D vs C: 更好

C 的主要问题: 2 个 FP + 遗漏"盘尼西林炮兵侦察系统"的完整 gold span

D 的主要变化: 删除 2 个 FP，补回 1 个 TP（完整 span），pred 更精确

RAG evidence 是否相关: 弱相关 — top-1 是导弹试验（军事领域但不同子类）

D 是否删掉 C 的错误实体: 是（2/2 全删）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: GOOD
一句话理由: 军事主题的 RAG 段落虽非精确匹配，但提供领域上下文帮助模型辨别真实装备名 vs 描述性短语。
```

### 样本 6 — 北斗导航（+0.200，F1=1.0）

```text
id: domain-candidate-0055
D vs C: 更好

C 的主要问题: 遗漏 2 个 gold MODULE（"处理器模块""北斗导航定位模块"）

D 的主要变化: 新增 2 个 TP，零 FP 零误删，pred=6 恰好 gold=6

RAG evidence 是否相关: 相关 — top-1 是终端间定位方法（导航主题匹配），top-2 是 GPS 停车寻车

D 是否删掉 C 的错误实体: N/A（C 无 FP）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: GOOD
一句话理由: RAG 的导航/定位主题证据高度匹配 query，帮助模型补全遗漏的 2 个 MODULE 实体。
```

### 样本 7 — 汽车尾门感应（+0.182，F1=1.0）

```text
id: domain-candidate-0063
D vs C: 更好

C 的主要问题: 遗漏 4 个 gold MODULE（感应天线/遥控器识别器/控制器局域网/电动尾门驱动组件）

D 的主要变化: 新增 4 个 TP 全部补回，pred=13 恰好 gold=13

RAG evidence 是否相关: 弱相关 — top-1 是自动烟雾/CO 排放系统（不同专利主题，但同是专利格式）

D 是否删掉 C 的错误实体: N/A

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: GOOD
一句话理由: RAG 的专利格式证据为模型提供了"组件列举型专利"的标注范式，帮助补全 4 个遗漏 MODULE。
```

### 样本 8 — 无线发声装置（+0.171）

```text
id: domain-candidate-0050
D vs C: 更好

C 的主要问题: 4 个 FP

D 的主要变化: 删除全部 4 个 FP，pred=5 恰好 gold=5

RAG evidence 是否相关: **噪声** — top-1 是 GPS 制导系统（完全无关）

D 是否删掉 C 的错误实体: 是（4/4 全删）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: GOOD
一句话理由: 再次验证"RAG 噪声但模型改善"的模式——无关证据似乎触发保守模式，减少过标。
```

### 样本 9 — 猎人无人机（−0.403，最严重退化）

```text
id: domain-candidate-0221
D vs C: 更差

C 的主要问题: 4 个 FP（轻微过标），总体 OK

D 的主要变化: 新增 7 个 FP，丢失 2 个 TP（"BAT 子弹药""基型 BAT 子弹药"被丢），pred 从 7→10 恶化

RAG evidence 是否相关: 部分相关 — top-1 是诺思罗普・格鲁曼（同一家公司），证据内容不同但公司名匹配导致模型过度关注

D 是否删掉 C 的错误实体: 轻微（2/4 删除）

D 是否误删 C 的正确实体: **是（2 个 TP 被误删）**

D 是否新增错误实体: 严重（7 个新 FP）

结论: POOR
一句话理由: RAG 段落包含 query 中提到的公司名（诺思罗普・格鲁曼），诱导模型过标 + 错标，丢掉了 BAT 子弹药系列 gold 实体。
```

### 样本 10 — IFPA 项目（−0.200，F1=0）

```text
id: domain-candidate-0092
D vs C: 更差

C 的主要问题: 类型混淆（MODULE→EQUIPMENT）+ FP

D 的主要变化: 丢失唯一 1 个 TP（C 正确的"制导炮弹"），新增 6 个 FP。pred 从 6→9 但全错

RAG evidence 是否相关: **噪声** — top-1 是遥控武器站（完全无关，IFPA 是精确制导弹药评估项目）

D 是否删掉 C 的错误实体: 轻微（2/5）

D 是否误删 C 的正确实体: **是（1 个 TP 被误删——"制导炮弹"）**

D 是否新增错误实体: 严重（6 个新 FP——"炮弹""光纤"等碎片化实体）

结论: POOR
一句话理由: RAG 的遥控武器站证据与制导弹药 query 完全无关，诱导模型碎片化过标并丢失唯一正确的 gold TP。
```

### 样本 11 — 26 型护卫舰（−0.154）

```text
id: domain-candidate-0253
D vs C: 更差

C 的主要问题: 漏标严重（gold=8，C pred=5）

D 的主要变化: 再丢 1 个 TP，新增 1 个 FP，pred=5 不变但错的分布变了

RAG evidence 是否相关: partial — top-1 是 MK 41 VLS（舰载装备，同领域但不同系统）

D 是否删掉 C 的错误实体: 否（0）

D 是否误删 C 的正确实体: 是（1 个 TP——"26型隐身护卫舰"）

D 是否新增错误实体: 轻微（1 个）

结论: POOR
一句话理由: RAG 的 MK 41 VLS 证据诱导模型错误地修改了 26 型护卫舰的 span 边界，导致核心 TP 丢失。
```

### 样本 12 — 无人飞行器组件（−0.071）

```text
id: domain-candidate-0038
D vs C: 更差

C 的主要问题: 基本完美（F1=0.968），仅遗漏 1 个 MODULE

D 的主要变化: 再丢 2 个 TP（"中心体""惯性测量单元"），无新 FP

RAG evidence 是否相关: **噪声** — top-1 是 AUV 水下驻留系统（水下 vs 空中，完全不同平台）

D 是否删掉 C 的错误实体: N/A（C 无 FP）

D 是否误删 C 的正确实体: **是（2 个 TP 被误删）**

D 是否新增错误实体: 否（0）

结论: POOR
一句话理由: RAG 的水下 AUV 证据诱导模型丢失了 2 个空中无人机组件 TP——跨域噪声直接伤害已接近完美的预测。
```

### 样本 13 — 霍巴特驱逐舰（−0.063）

```text
id: domain-candidate-0260
D vs C: 更差

C 的主要问题: 基本 OK（F1=0.800），轻微过标

D 的主要变化: 丢失 1 个 TP（"SM-2 导弹"），无新 FP

RAG evidence 是否相关: partial — 军事新闻但不同装备

D 是否删掉 C 的错误实体: 否

D 是否误删 C 的正确实体: 是（1 个 TP）

D 是否新增错误实体: 否（0）

结论: OK
一句话理由: 退化轻微（仅丢 1 个 TP），RAG 证据弱相关但不致命，属可接受波动。
```

### 样本 14 — 公羊坦克（FP drop 显著，F1 持平）

```text
id: domain-candidate-0240
D vs C: 持平

C 的主要问题: 5 个 FP（过标实体）+ 4 个 FN（漏标）

D 的主要变化: FP 5→3（删 2 个），但漏标仍严重，gold=8 仅命中 4

RAG evidence 是否相关: partial — top-1 是无人机集成传感器（与坦克不完全匹配）

D 是否删掉 C 的错误实体: 是（2 个 FP 被删）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 轻微（0）

结论: OK
一句话理由: RAG 减少 FP 但未改善 recall——坦克领域的遗漏根因仍在 kNN 示例错配，RAG 无法修复。
```

### 样本 15 — S-350 防空系统（FP drop，F1 持平）

```text
id: domain-candidate-0242
D vs C: 持平

C 的主要问题: 7 个 FP + 6 个 FN，严重漏标和过标

D 的主要变化: FP 7→5（删 2 个），但 6 个 FN 未改善

RAG evidence 是否相关: partial — top-1 是俄罗斯机动防空（同领域但不同系统）

D 是否删掉 C 的错误实体: 是（2 个 FP——误标的 TECH_SCHEME/METRIC）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: OK
一句话理由: RAG 压掉 2 个过标但无法补回遗漏——S-350 的系统名称和组件超出了 support+bge-m3 的能力范围。
```

### 样本 16 — Namrod 制导系统（FP drop，F1 持平）

```text
id: domain-candidate-0268
D vs C: 持平

C 的主要问题: 11 个 FP（严重过标，大量 METRIC/MODULE 碎片化）

D 的主要变化: FP 11→8（删 3 个），但核心问题（漏标 10 个 gold）未改善

RAG evidence 是否相关: partial — top-1 是制导系统的上行数据链（与 query 的"卫星制导"主题相关但不同角度）

D 是否删掉 C 的错误实体: 是（3 个 FP 被删——"伽利略""GLONAAS"等碎片化名称）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: OK
一句话理由: RAG 的制导数据链上下文帮助去除碎片化 FP，但 recall 提升需要更强的领域知识。
```

### 样本 17 — 制导炮弹 Mk 295（FP 增加，F1 略降）

```text
id: domain-candidate-0123
D vs C: 持平

C 的主要问题: 6 个 FP（glossary 诱导的"舰船""直升机"虚标）

D 的主要变化: FP 6→5（删 1 个 glossary 虚标），TP 不变，基本持平

RAG evidence 是否相关: partial — top-1 是 BAE 系统/APKWS（同公司，同为精确制导弹药）

D 是否删掉 C 的错误实体: 是（1 个 glossary 虚标）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: OK
一句话理由: RAG 部分修正了 glossary 的噪声（删除虚标"舰船"），但效果有限。
```

### 样本 18 — 无人飞行器观光（D 改善，RAG 噪声）

```text
id: domain-candidate-0015
D vs C: 持平

C 的主要问题: 2 个 FP（重复"无人飞行器"）

D 的主要变化: FP 2→1（删 1 个重复），基本持平

RAG evidence 是否相关: **噪声** — top-1 是 GPS 制导系统（完全无关）

D 是否删掉 C 的错误实体: 是（1 个）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: OK
一句话理由: RAG 不相关但无伤害——模型将无关证据当噪音忽略，小幅改善来自随机波动。
```

### 样本 19 — 家用器具专利（专利编号幻觉持续）

```text
id: domain-candidate-0077
D vs C: 持平

C 的主要问题: 4 个 FP（模型将专利编号"(2,12,32)"吸入 entity span）+ 2 个 FN

D 的主要变化: 问题完全未改善——仍是 4 个 FP（同样的专利编号幻觉），pred=4，gold=6

RAG evidence 是否相关: **噪声** — top-1 是机器视觉 FSO 通信系统（不同专利，格式相似但主题无关）

D 是否删掉 C 的错误实体: 否（4 个 FP 仍在）

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 否（0）

结论: POOR
一句话理由: 专利编号幻觉是模型固有问题，RAG 的专利格式证据并未纠正——这是 prompt/parsing 问题，非检索问题。
```

### 样本 20 — 密集阵-拉姆系统（D 的 sanitization flags）

```text
id: domain-candidate-0100
D vs C: 持平

C 的主要问题: 1 个 FP + 1 个 FN

D 的主要变化: 基本持平，FP 和 FN 各轻微变化。1 个 sanitizer flag（正确丢弃重叠实体）

RAG evidence 是否相关: partial — top-1 是反舰导弹/旋转翼飞机对抗（与密集阵近防系统相关）

D 是否删掉 C 的错误实体: 轻微

D 是否误删 C 的正确实体: 否（0）

D 是否新增错误实体: 轻微

结论: OK
一句话理由: RAG 的舰载防御系统证据相关但无显著帮助——该行的 F1 瓶颈是 gold 标注复杂度而非检索。
```

## 汇总区

审计完后，只填这里即可。

```text
审计样本数: 20

D 明显好于 C: 8
D 明显差于 C: 5
D 基本持平: 7

GOOD: 8
OK: 7
POOR: 5

D 删除 C 错误实体的样本数: 13/20
D 误删 C 正确实体的样本数: 3/20（0221/0092/0038 各丢 1-2 个 TP）
D 新增错误实体的样本数: 5/20（最严重 0221 新增 7 FP、0092 新增 6 FP）

RAG evidence 明显相关: 3/20（0055 导航、0063 专利格式、0100 舰载防御）
RAG evidence 部分相关: 8/20（同领域不同系统，如导弹/雷达/无人机）
RAG evidence 明显噪声: 9/20（查询民用专利但 RAG 返回军事，或查询无人机但 RAG 返回 AUV）

最终判断:
D(RAG) 是 acceptable positive

三句话总结:
1. D 相比 C 净减少 18 个 FP（177→159），FP 减少来自 C 的 eager 过标/碎片化实体被 RAG 段落抑制，而非随机波动。
2. RAG 证据相关性参差不齐（9/20 噪声），但即使在噪声情况下 D 也倾向于更保守（减少过标），仅 3/20 出现 TP 误删——风险可控。
3. D 是正向结果，方向正确，但 RAG 噪声问题需在最终 P5 中通过 bge-reranker 改善或限制 top-1 相关性阈值来进一步收束。

下一步选择:
1. 批准准备 E/E-prime verification GPU-free（selected）
2. 先做更多 D dev-only 分析
3. 暂停增强路线
```

## 最终结论模板

可以直接改下面这段：

```text
D(RAG) 审计结论：D 是 acceptable positive。
主要原因是：
第一，D 相比 C 的 FP 下降主要来自 C 的 eager 过标和碎片化实体被 RAG 段落系统性抑制，
13/20 样本显示 FP 减少，全量净减 18 FP，说明 RAG 证据提供了"结构锚定"效应，使模型更保守。
第二，RAG evidence 在多数样本中与 query 同领域但不同子系统（8/20 partial），
9/20 明显噪声，但噪声伤害有限——仅 3/20 样本出现正确实体被误删，
且最严重的 2 个退化案例（0221/0092）的根因可追溯到 RAG 将模型注意力引向无关段落。
第三，下一步建议 GPU-free 准备 E/E-prime verification config，
D 的正结果已足够支撑继续消融管线——verification 阶段的目标正是
在 D 的 RAG 基础上用逐 entity 的 yes/no 验证进一步压低 FP，
这是论文核心 claim（RAG+CoVe 幻觉率下降）的关键证据，仍然不使用 domain_test，不进入 P5。
```
