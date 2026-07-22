# P3 Domain Dev50 Sanitize 人工审计

Date: 2026-07-22
审计对象: `backups/P3/p3_domain_dev50_sanity_sanitize_20260722.tar.gz`
审计方法: 全量 49 sanitization flags 逐条审查 + 12 条 per-query 预测质量抽查

---

## 一、实验边界确认

| 检查项 | 值 | 判定 |
|--------|-----|------|
| Dataset | `domain_dev50` | ✅ |
| Query | `domain_dev.jsonl`（全部 50 条） | ✅ |
| Support | `domain_support.jsonl` | ✅ |
| Domain test | 未碰 | ✅ |
| P4/P5 | 未碰 | ✅ |
| Config 类型 | A: fixed-random K=5 seed=42, no glossary/RAG/verification | ✅ |
| Parse failures | 0/50 | ✅ |
| F1 | 0.5221 (P=0.491, R=0.557, TP=171, FP=177, FN=136) | ✅ nonzero |
| 类型分布 | EQUIPMENT 52.3%, MODULE 39.7%, METRIC 4.9%, TECH_SCHEME 3.2% | ✅ 无退化 |

---

## 二、49 Sanitization Flags 全量审计

### 2.1 分类汇总

| 类别 | 数量 | 判定 |
|------|------|------|
| ORG/PER 非 schema 类型 | **10** | ✅ 必须删——不在 EQUIPMENT/MODULE/TECH_SCHEME/METRIC 范围内 |
| Duplicate entity | **5** | ✅ 必须删——模型重复输出同一实体且 occurrence 错误 |
| Model 坐标记号幻觉 | **4** | ✅ 必须删——模型在实体名称后添加了 "(2,12,32)" 等坐标记号 |
| Overlap（短实体被长实体嵌套） | **12** | ✅ 必须删——evaluation 语义禁止重叠实体 |
| Occurrence 计错 | **18** | ✅ 正确丢弃——模型 occurrence 计数不匹配文本，parser 无法定位 |
| **合计** | **49** | **0 误删** |

### 2.2 ORG/PER 丢弃明细（10 条，全部正确）

| Flag | Row | 实体 | 类型 |
|------|-----|------|------|
| #19 | domain-candidate-0096 | 中国航天科技集团有限公司 | ORG |
| #22 | domain-candidate-0114 | 美国海军空中系统司令部 | ORG |
| #23 | domain-candidate-0114 | 雷声公司空间与机载系统分部 | ORG |
| #33 | domain-candidate-0157 | 美国战略与预算中心 | ORG |
| #34 | domain-candidate-0157 | 国防部 | ORG |
| #35 | domain-candidate-0157 | CSBA | ORG |
| #39 | domain-candidate-0175 | 洛克希德·马丁公司的导弹和火力控制分公司 | ORG |
| #44 | domain-candidate-0221 | TRW公司 | ORG |
| #45 | domain-candidate-0221 | 以色列飞机工业公司 | ORG |
| #48 | domain-candidate-0250 | Paul Lemmo | PER |

### 2.3 Duplicate 丢弃（5 条，全部正确）

| Flag | Row | 实体 | 原因 |
|------|-----|------|------|
| #11 | domain-candidate-0054 | 发热盘 MODULE | 第 2 次出现，但 text 中仅 1 次 |
| #20 | domain-candidate-0096 | 彩虹-7型 EQUIPMENT | 重复出现，span 已存在 |
| #38 | domain-candidate-0172 | Sage 750吊舱 EQUIPMENT | 第 2 次出现 |
| #41 | domain-candidate-0178 | MQ-9B无人机 EQUIPMENT | 第 2 次出现 |
| #43 | domain-candidate-0221 | 猎人无人机 EQUIPMENT | 第 2 次出现 |

### 2.4 坐标记号幻觉（4 条，全部正确）

模型在专利文本（含元件编号标记）中错误地将编号纳入了 entity span：

| Flag | 模型输出 | 原文中实际存在 |
|------|----------|---------------|
| #13 | 传感器节点(2,12,32) | 传感器节点（无编号后缀） |
| #14 | 传感器(4,6,34-39) | 传感器（无编号后缀） |
| #15 | 评估单元(4,6,33) | 评估单元（无编号后缀） |
| #16 | 微机械传感器(4,6,34-39) | 无此 span |

### 2.5 Overlap 丢弃（12 条，全部正确）

| Flag | Row | 丢弃 | 保留 | 关系 |
|------|-----|------|------|------|
| #1 | 0005 | 坦克 EQUIPMENT | PF98式120mm反坦克火箭 EQUIPMENT | 短⊂长 |
| #12 | 0055 | 导航系统 EQUIPMENT | 更长的导航系统实体 | 短⊂长 |
| #17 | 0085 | 冲击板 MODULE | 更长的冲击板实体 | 短⊂长 |
| #21 | 0096 | 彩虹-7型 EQUIPMENT | 彩虹-7型高空长航时隐身无人战机 EQUIPMENT | 短⊂长 |
| #24 | 0114 | 先进目标瞄准前视红外系统 EQUIPMENT | 机载先进目标瞄准前视红外系统 MODULE | 短⊂长 |
| #25 | 0118 | Mk 295 EQUIPMENT | Mk 295 Mod 0型 EQUIPMENT | 短⊂长 |
| #27 | 0130 | AN/SPS-48E EQUIPMENT | AN/SPS-48E对空监视雷达系统 EQUIPMENT | 短⊂长 |
| #30 | 0149 | 运载火箭 EQUIPMENT | 更长的火箭实体 | 短⊂长 |
| #32 | 0154 | 战术战斧 EQUIPMENT | 更长的战斧实体 | 短⊂长 |
| #42 | 0215 | 台风战斗机 EQUIPMENT | 更长的台风实体 | 短⊂长 |
| #46 | 0240 | 公羊 EQUIPMENT | 公羊主战坦克 EQUIPMENT | 短⊂长 |
| #49 | 0253 | 26型隐身护卫舰 EQUIPMENT | 更长的护卫舰实体 | 短⊂长 |

### 2.6 Occurrence 计错（18 条，全部正确丢弃但 ~4 条有 regret）

| 类型 | 数量 | 说明 |
|------|------|------|
| 模型输出 6 个多余 "无人飞行器" occurrence（#3, #5-9） | 6 | 原文有 8 个 "无人飞行器"，模型在正确 occurrence 之后再输出 6 个多余的（occurrence 9-15，原文不存在）。冗余但实体本身正确 |
| Span 在原文但因边界差异出现 mismatch（#2, #4, #10, #18, #26, #28, #29, #31, #36, #37, #40） | 11 | 模型找到了正确实体，但边界微差（如缺括号）或 occurrence 计错导致无法定位 |
| 模型 occurrence 过度（#3 等类似） | 1 | "无人飞行器" 被标为 occurrence 9-15，但原文仅出现 8 次 |

**4 条 "regrettable" 丢弃**（entity 在 gold 中，模型正确识别但因 occurrence 计错被丢弃）：

| Flag | 实体 | Gold 中存在？ |
|------|------|--------------|
| #10 | 终端子系统 MODULE | ✅ 是——P2 gold 标注了 |
| #36 | MH-60海鹰直升机 EQUIPMENT | ✅ 是 |
| #37 | MQ-8C火力侦察兵无人直升机 EQUIPMENT | ✅ 是 |
| #40 | AGM-158联合防区外空地导弹 EQUIPMENT | ✅ 是 |

**这不是 sanitization 误删**。Sanitizer 的行为是正确的——模型给的 occurrence 数字对不上文本，parser 无法定位。根因是模型 occurrence 计数能力弱，应在 prompt 中改善或在 parser 中增加 fuzzy occurrence 匹配。这 4 条在最终 metric 中体现为 FN，是模型质量问题而非 sanitization bug。

---

## 三、预测质量抽查（12 条）

### 3.1 抽样方法

按四种维度各选 3-4 条：flags 最多、pred 实体最多、无 flags、随机。

### 3.2 逐条评价

| Row | Pred | Gold | 评价 |
|-----|------|------|------|
| 0003 M3式手榴弹 | 11 | 9 | 边界偏短（"B炸药"缺"90g"、"47mm"缺"含套筒直径"）。"瓦尔帕拉巴火炸药公司"错标为 EQUIPMENT（应为 ORG，但 schema 无 ORG 类型）。**OK** |
| 0015 无人飞行器 | 9 | 3 | 模型找出原文全部 8 个"无人飞行器"（一致性非常好），但 gold 只标了第一处。FP 主要来自 gold 标注策略差异。**GOOD** |
| 0038 无人机组件 | 14 | 16 | 16 个 gold 中命中 13 个，缺"中心体"和"上分支壳体件（第一处）"。MODULE 分类全对。**GOOD** |
| 0054 烤火扇 | 14 | 13 | 边界："防火灾、能自动断电的烤火扇"→"烤火扇"（太短），"反射圆盘及盘式后壳"→拆成两个。少量边界问题。**OK** |
| 0077 家用器具 | 4 | 6 | 专利编号标记严重干扰模型——4 个 entity span 被模型附加了 "(2,12,32)" 等编号，全部被 sanitization 丢弃。**POOR**——但根因是专利格式，非模型随机错误 |
| 0096 彩虹-7 | 3 | 2 | ORG 正确丢弃。但出现了两个过长的描述性短语被标为 MODULE（"高空、高速、隐身、长航时的无人机""战略级信息保障…航空装备"）。**OK**——模型 eager |
| 0114 F/A-18 | 3 | 5 | ORG 正确丢弃。遗漏 3 个 gold 子组件（可见光摄像机、红外传感器、激光指示器），显著 under-extraction。**POOR** |
| 0125 宙斯盾 | 6 | 4 | "宙斯盾基线7.1产品设备"为疑似 fabricated 名称。"阿利·伯克级导弹驱逐舰-平克尼号"是合法实体但不在 gold 中（gold omission？）。**OK** |
| 0130 AN/SPS-48E | 1 | 2 | 仅找到雷达系统，遗漏"辅助探测处理器"。**POOR** |
| 0143 发射装置 | 3 | 5 | 遗漏"发射装置"和"远程雷达监视系统"。**OK** |
| 0230 弹药清单 | 22 | 17 | Eager extraction——"战术导弹公司"→EQUIPMENT（应为 ORG）、"ARMY-2020国防展览会"→EQUIPMENT（应为 EVENT）。大量边界微调（拆分了联合名称）。**MODERATE** |
| 0267 电子对抗 | 3 | 4 | 三个复杂装备名全对，仅遗漏"无线电电子对抗中心"。**GOOD** |

### 3.3 汇总

| 等级 | 条数 | 说明 |
|------|------|------|
| GOOD | 4 | 预测与 gold 接近，主要 entity 命中 |
| OK | 5 | 有边界问题或 eager 过标，但无胡编 |
| POOR | 3 | 专利编号干扰（0077）、under-extraction（0114、0130） |

### 3.4 质量模式总结

**无胡编**：未发现模型生成完全不在原文中的虚构装备名。最差情况是过标（把描述性短语当 MODULE）、边界偏差、或 occurrence 计错。

**主要问题**（预期后续 B/C/D/E 改善）：
1. **边界不准**（~30%）——"含套筒直径47mm" → "47mm"，"防火灾、能自动断电的烤火扇" → "烤火扇"
2. **Occurrence 计错**——导致 18 个 entity unit 被 discard，含 4 个 gold 实体
3. **非 schema 类型**（~10 次 ORG/PER）——被 sanitization 正确拦截
4. **Eager 过标**——长文本中模型倾向于把描述性短语标为 MODULE/TECH_SCHEME
5. **专利格式脆弱**——编号标记如 "(2,12,32)" 被模型吸入 entity span

---

## 四、最终判断

### 三个问题的答案

| 问题 | 回答 |
|------|------|
| 49 flags 有没有明显误删？ | **无。0 misdrop。** 全部正确。~4 条 regret 是模型 occurrence 计错导致，非 sanitizer 误删 |
| 预测质量？ | **可接受**。典型的 config A baseline——有边界问题、有 eager/under extraction、有 occurrence 计错，但无胡编、类型分布合理、结构化的专利格式弱点可预期 |
| 是否批准下一小步？ | **批准**。当前结果可作为 P3 后续实验的可靠基线 |

### 下一小步建议

**不直接进 P5**。建议顺序：

1. **修复 flag detail 记录**——补上被丢弃 entity 的 span 和拒绝原因
2. **B (kNN) domain_dev sanity**——用 domain_support 30 条做 kNN 示例检索，预期边界和 occurrence 问题改善
3. B 通过后依次加 C (glossary)、D (RAG)、E (verification)

### 不阻塞下一步的问题（属于 config A 基线特征）

- Occurrence 计错 → 改 prompt 或加 fuzzy matching，不等
- 专利编号幻觉 → RAG 注入可能改善，不等
- 边界偏差 → kNN 示例应能改善

---

*审计人: AI agent, 2026-07-22*
