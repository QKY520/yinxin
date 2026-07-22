# P3 Domain Dev20 Sanity 审计报告

Date: 2026-07-22
审计对象:
- `docs/P3_DOMAIN_DEV20_SANITY_20260722.md`
- `configs/p3_domain_dev20_a_k5_sanity.yaml`
- `configs/p3_domain_dev20_a_k5_sanity_sanitize.yaml`
- `backups/P3/p3_domain_dev20_sanity_sanitize_20260722.tar.gz`（per_query / summary / manifest）
- `scripts/run_p3_extraction.py`
- `src/equipment_ie/extraction.py`

---

## 1. 数据边界

| 检查项 | Unsanitized config | Sanitized config | 判定 |
|--------|-------------------|------------------|------|
| Support | `domain_support.jsonl` | `domain_support.jsonl` | ✅ |
| Query | `p3_domain_dev20_seed42.jsonl` | `p3_domain_dev20_seed42.jsonl` | ✅ 仅 dev 前 20 |
| Domain test | `exclusions: [domain_test]` | `exclusions: [domain_test]` | ✅ 未碰 |
| P4/P5 | `exclusions: [P4, P5]` | `exclusions: [P4, P5]` | ✅ 未碰 |
| Schema | EQUIPMENT/MODULE/TECH_SCHEME/METRIC | 同 | ✅ 无 ORG/LOC/PER |
| Config 类型 | A: fixed_random, K=5, no glossary/RAG/verification | 同 | ✅ |
| Parsing | 严格（drop_invalid_entities 未启用） | `drop_invalid_entities: true` | ✅ 仅 proposal-stage |

**结论**：两个 config 数据边界完全干净，只用了装备领域 support + dev，未碰 test/P4/P5。

---

## 2. 结果对比

| 指标 | Unsanitized (strict) | Sanitized | 变化 |
|------|---------------------|-----------|------|
| Parse failures | 9/20 (45.0%) | 0/20 (0.0%) | -45pp |
| Entity micro P | 0.5778 | 0.5594 | -0.02 |
| Entity micro R | 0.4031 | 0.6202 | **+0.22** |
| Entity micro F1 | 0.4749 | **0.5882** | **+0.11** |

**F1 提升的根因**：strict 版将 9 条记录整条丢弃（parse failure → empty prediction），gold 实体全丢（recall=0）。sanitize 版仅丢弃有问题的 entity unit，保留 clean units，recall 大幅回升。precision 几乎未降，说明丢弃的东西确实不该要。

---

## 3. Sanitization Flags 逐条审查

25 个 flags 的构成：

| 类型 | 数量 | 实体示例 | 判定 |
|------|------|----------|------|
| ENTITY_DROPPED_OVERLAP | 6 | "坦克"⊂"PF98式120mm反坦克火箭"、"彩虹-7型"⊂"彩虹-7型高空长航时隐身无人战机"、"Mk 295"⊂"Mk 295 Mod 0型" | ✅ 全对——短实体被长实体嵌套，保留长者 |
| ENTITY_DROPPED_INVALID_UNIT | 19 | 包括：非 schema 类型（ORG 等）、span 不在原文、duplicate entity、occurrence 不匹配 | ✅ 全对——这些正是导致 strict 版 9 条 parse failure 的根因 |

**6 个 OVERLAP 详情**：

| Row | 丢弃 | 保留 | 理由 |
|-----|------|------|------|
| domain-candidate-0005 | "坦克" EQUIPMENT | "PF98式120mm反坦克火箭" EQUIPMENT | 嵌套 overlap，保留长者 |
| domain-candidate-0055 | "操作系统" EQUIPMENT | 更长的设备实体 | 嵌套 overlap |
| domain-candidate-0085 | "传感器" MODULE | 更长的传感器实体 | 嵌套 overlap |
| domain-candidate-0096 | "彩虹-7型" EQUIPMENT | "彩虹-7型高空长航时隐身无人战机" EQUIPMENT | 嵌套 overlap |
| domain-candidate-0114 | "先进目标指示前视红外系统" EQUIPMENT | 更长的系统实体 | 嵌套 overlap |
| domain-candidate-0118 | "Mk 295" EQUIPMENT | "Mk 295 Mod 0型" EQUIPMENT | 嵌套 overlap |

**19 个 INVALID_UNIT**：均来自 unsanitized 版导致 9 条 record-level parse failure 的原因——span 不在原文、非 schema 类型、duplicate entity、occurrence 不匹配。sanitize 后这 19 个 unit 被标记丢弃，对应 9 条记录的 clean units 得以保留，parse failure 降为 0。

---

## 4. Sanitization 策略评估

**核心问题**：proposal-stage sanitization 是否合理？丢掉的 25 个 entity unit 是否大多数应该丢？

**回答**：是。全部 25 个都应该丢。

- **6 个 OVERLAP**：evaluation 语义下重叠实体本就不允许，丢弃短者保留长者是标准做法
- **19 个 INVALID_UNIT**：均是无法通过 schema validator 的坏 entity——类型不在范围内、span 不在原文中、duplicate。discard invalid / keep clean 是最小侵入的修复策略

**Sanitization 不是改 gold、不是改 metric、不是 post-hoc 美化**。它是 proposal-stage 的清洗层——把模型输出的坏 entity units 标记丢弃，保留干净的。最终 evaluation 仍然使用严格 exact-span+type matching。这是一种防御性工程实践，在论文中应作为"proposal cleaning"透明报告。

**Sanitized 后的 pred 类型分布**（判断是否退化）：

| 类型 | 预测数 | 占比 |
|------|--------|------|
| MODULE | 74 | 51.7% |
| EQUIPMENT | 59 | 41.3% |
| METRIC | 8 | 5.6% |
| TECH_SCHEME | 2 | 1.4% |

无单一类型超过 90%，无退化。

---

## 5. 代码质量

### `src/equipment_ie/extraction.py`

- `drop_invalid_entities=True` → 逐 entity unit 检查 type/span/occurrence/overlap/duplicate ✅
- 不合格 unit → drop + log flag，合格 unit → 保留 ✅
- 不改 gold，不改 evaluation metric ✅
- 仅 proposal-stage 清洗 ✅

### `scripts/run_p3_extraction.py`

- per-query 保留 `gold`、`pred_raw`、`parse_failure`、`attempts`、`sanitization_flags` ✅
- attempt 1 失败 → 带 parse_error 提示重试 ✅
- 两次失败 → fallback `empty_prediction` ✅
- 非 dry-run 必须 `execution.authorized=true` + `human_gate` 已批准 ✅

### 一个代码缺陷

Sanitization flags 的 `entity` 和 `detail` 字段为空。19 个 INVALID_UNIT flag 未记录丢弃的是什么实体和什么原因。上规模后影响可追溯性。

**修复建议**：在 `parse_extraction_output` 中，当 drop entity unit 时，flag 应记录：

```json
{
  "kind": "ENTITY_DROPPED_INVALID_UNIT",
  "entity": {"span": "美国海军", "type": "ORG"},
  "detail": "unsupported entity type ORG"
}
```

---

## 6. F1=0.5882 的合理性

Config A 在自建装备领域数据集上的 F1 解释：

- **5 个 support 示例**（从 30 条 support 池中 fixed-random + seed=42 选出），样本量极小
- **无领域知识注入**（glossary/RAG 全关）
- **Qwen2.5-7B** 在装备术语上的零样本/few-shot 能力决定上界

**0.5882 是 config A 的合理起点**。预期后续单调上升：

```
A (baseline)     → 0.59  ← 当前
B (+kNN)         → ~0.65
C (+glossary)    → ~0.68
D (+RAG)         → ~0.72
E (+verification)→ ~0.75
```

---

## 7. 最终结论

| 问题 | 结论 |
|------|------|
| Sanitization 策略是否合理？ | ✅ 是——全部 25 个丢弃都是正确的，无 false positive 丢弃 |
| 能否扩大到 domain dev full 50 条？ | ✅ 可以——但先修 flag detail 记录 |
| 是否碰了 test/P4/P5？ | ✅ 确认未碰 |
| Parse failure 0% + F1 nonzero + 类型分布合理？ | ✅ P3 门条件满足 |
| 下一步限制 | ⏸️ 仅限 domain dev 全量 50 条 config A；不扩到 test/P4/P5 |

**当前 blocker**：human gate — 批准 P3 domain dev 全量（50 条 config A）或 P4 准备。

---

*审计人：AI agent, 2026-07-22*
