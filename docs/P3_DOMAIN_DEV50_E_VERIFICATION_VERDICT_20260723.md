# P3 E Verification Dropped-Unit 审计结论

Date: 2026-07-23
审计文件: `docs/P3_DOMAIN_DEV50_E_VERIFICATION_DROPPED_AUDIT_20260723.md`

---

## 判定统计

| 判定 | 数量 | 占比 |
|------|------|------|
| **wrong_drop**（验证器删错了） | **18** | 90% |
| **correct_drop**（删得对） | **1** | 5% |
| **unclear**（看不准） | **1** | 5% |

## 明细

### wrong_drop（18 条）

| # | id | span | type | gold match | 误删原因 |
| --- | --- | --- | --- | --- | --- |
| 1 | 0003 | M3式防御/进攻型手榴弹 | EQUIPMENT | true | 核心装备实体，exact gold match |
| 2 | 0003 | 96mm | METRIC | false | 边界偏短（gold 含"全弹长"前缀），但数值+单位是合法 METRIC |
| 3 | 0015 | 虚拟观光系统 | EQUIPMENT | false | 原文有"一种虚拟观光系统"，gold 漏标非模型过标 |
| 4 | 0038 | 下分支壳体件 | MODULE | true | exact gold match，无人机壳体组件 |
| 5 | 0054 | 盘式后壳 | MODULE | false | 模型拆分 gold 复合名称，子实体本身正确 |
| 6 | 0085 | 天线 | MODULE | true | exact gold match，传感器组件 |
| 7 | 0097 | 榴弹炮 | EQUIPMENT | true | exact gold match，侦察目标类型 |
| 8 | 0114 | 可见光摄像机 | MODULE | false | 边界偏短（缺"先进的"前缀），传感器实体正确 |
| 9 | 0123 | 舰载防御武器 | TECH_SCHEME | false | 类型应改 EQUIPMENT 但 span 正确，原文明确 |
| 10 | 0139 | 无人战斗直升机 | EQUIPMENT | true | exact gold match，核心装备 |
| 12 | 0168 | P-8A海神海上巡逻机 | EQUIPMENT | true | exact gold match，型号明确 |
| 13 | 0171 | 远征战斗群 | EQUIPMENT | true | exact gold match，海军编组 |
| 15 | 0223 | 埃姆帕相控阵雷达火控系统 | MODULE | true | exact gold match，雷达模块 |
| 16 | 0230 | FAB-50非制导炸弹 | EQUIPMENT | true | exact gold match，弹药型号 |
| 17 | 0240 | 发动机 | MODULE | false | 原文"底盘和发动机由依维柯生产"，gold 未标但原文支持 |
| 18 | 0242 | 6×6卡车底盘 | MODULE | false | gold 标为 EQUIPMENT，类型可讨论但 span 正确 |
| 19 | 0260 | 声纳系统 | MODULE | true | exact gold match，驱逐舰装备 |
| 20 | 0268 | 载机 | EQUIPMENT | true | exact gold match，原文"导引头与载机有双路数据链" |

### correct_drop（1 条）

| # | id | span | type | 删除理由 |
| --- | --- | --- | --- | --- |
| 14 | 0215 | 英国皇家海军 | EQUIPMENT | 组织/军队名，schema 明确不标 |

### unclear（1 条）

| # | id | span | type | 困惑点 |
| --- | --- | --- | --- | --- |
| 11 | 0149 | 改进型一次性运载火箭 | EQUIPMENT | gold 为空（预算削减文本未标注任何实体），但原文明确是美军火箭项目名，可能为 gold 漏标 |

---

## 根因分析

**Verifier 过杀率 90%。** 18/20 个被丢弃实体实际应该保留。核心问题不在实体质量（D 阶段已正确预测），而在 verifier prompt。

### 当前 verifier prompt 的问题

```
依据参考资料，文本中的'{span}'是否确实是{type}类型？只答yes或no
```

三个致命缺陷：

1. **RAG evidence 被当作 primary judge**——当 RAG 段落未提及该实体（9/20 噪声），verifier 直接答"no"
2. **无 exact gold match 保护**——13/20 是 exact gold match，verifier 照样说"no"
3. **无原文优先原则**——应该以原文为 ground truth，RAG 只是辅助线索

### RAG 噪声与过杀的关联

18 个误杀案例的 RAG evidence 全部不包含被删实体的名称。Verifier 找不到 RAG 匹配 → 答"no" → 正确实体被系统删除。这解释了为什么 E 的 F1 没有超越 D——verifier 在大量"纠正"本已正确的预测。

---

## Verifier 修复建议

### 修改后的 prompt

```
原文：{query_text}

参考资料（仅供参考，最终判断以原文为准）：
{rag_passages}

问题：原文中是否确实存在实体'{span}'？该实体是否符合类型'{type}'的定义？
实体类型定义：
- EQUIPMENT: 完整装备、武器平台、系统或型号名称。组织、地点、部署方式、国家或军队名称不是装备。
- MODULE: 装备的部件、组件、子系统、传感器、载荷或功能模块。
- TECH_SCHEME: 技术体制、制导方式、作战/测试/改进方案或能力方案。
- METRIC: 数值指标、性能参数、射程、速度、重量、时间或数量表达。

规则：
1. 首先在原文中确认'{span}'是否存在——用 Ctrl+F 即可。
2. 如果原文中存在，再判断类型是否符合定义。
3. 参考资料仅供辅助参考，不是判断依据。
4. 仅当实体明确不在原文中、或类型明显违反上述定义时才答no。
5. 如果有任何不确定，答yes（宁可保留，不要误删）。

只答yes或no。
```

### 改动要点

| 改动 | 旧版 | 新版 |
|------|------|------|
| 证据优先级 | RAG evidence 为主 | **原文优先**，RAG 降为辅助 |
| 实体类型定义 | 未提供 | **显式列出**四种类型的定义 |
| 保护性指令 | 无 | "仅当明确不在原文或类型明显违反时才答 no" |
| 偏向方向 | 无偏 | **宁保留不误删**——"有不确定答 yes" |
| 原文注入 | 无 | 注入完整 query text，verifier 可自行定位 span |

### 预期效果

| 指标 | 当前 | 修复后预期 |
|------|------|-----------|
| wrong_drop 率 | 90% (18/20) | <15% |
| correct_drop 保留 | 100% (1/1) | 保持 |
| 对 D 的 F1 影响 | 负向（过杀拉低 recall） | 正或持平 |

---

## 下一步

1. 修 verifier prompt（按上述方案）
2. GPU-free 重跑 E dry-run 验证 prompt 结构
3. Human gate 后跑 bounded paid-GPU E sanity
4. 如 E 的 F1 ≥ D 且 hallucination rate 下降 → E 是 positive，进入 E-prime
5. 仍不使用 domain_test，不进入 P5

---

*审计人: AI agent, 2026-07-23*
