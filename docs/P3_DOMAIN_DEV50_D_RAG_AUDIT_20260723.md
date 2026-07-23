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

## 样本审计记录

复制下面这个块，填 20 次左右即可。

### 样本 1

```text
id:
D vs C: 更好 / 持平 / 更差

C 的主要问题:

D 的主要变化:

RAG evidence 是否相关:

D 是否删掉 C 的错误实体:

D 是否误删 C 的正确实体:

D 是否新增错误实体:

结论: GOOD / OK / POOR
一句话理由:
```

### 样本 2

```text
id:
D vs C: 更好 / 持平 / 更差

C 的主要问题:

D 的主要变化:

RAG evidence 是否相关:

D 是否删掉 C 的错误实体:

D 是否误删 C 的正确实体:

D 是否新增错误实体:

结论: GOOD / OK / POOR
一句话理由:
```

### 样本 3

```text
id:
D vs C: 更好 / 持平 / 更差

C 的主要问题:

D 的主要变化:

RAG evidence 是否相关:

D 是否删掉 C 的错误实体:

D 是否误删 C 的正确实体:

D 是否新增错误实体:

结论: GOOD / OK / POOR
一句话理由:
```

### 样本 4

```text
id:
D vs C: 更好 / 持平 / 更差

C 的主要问题:

D 的主要变化:

RAG evidence 是否相关:

D 是否删掉 C 的错误实体:

D 是否误删 C 的正确实体:

D 是否新增错误实体:

结论: GOOD / OK / POOR
一句话理由:
```

### 样本 5

```text
id:
D vs C: 更好 / 持平 / 更差

C 的主要问题:

D 的主要变化:

RAG evidence 是否相关:

D 是否删掉 C 的错误实体:

D 是否误删 C 的正确实体:

D 是否新增错误实体:

结论: GOOD / OK / POOR
一句话理由:
```

## 汇总区

审计完后，只填这里即可。

```text
审计样本数:

D 明显好于 C:
D 明显差于 C:
D 基本持平:

GOOD:
OK:
POOR:

D 删除 C 错误实体的样本数:
D 误删 C 正确实体的样本数:
D 新增错误实体的样本数:

RAG evidence 明显相关:
RAG evidence 部分相关:
RAG evidence 明显噪声:

最终判断:
D(RAG) 是 acceptable positive / mixed / harmful

三句话总结:
1.
2.
3.

下一步选择:
1. 批准准备 E/E-prime verification GPU-free
2. 先做更多 D dev-only 分析
3. 暂停增强路线
```

## 最终结论模板

可以直接改下面这段：

```text
D(RAG) 审计结论：D 是 acceptable positive / mixed / harmful。
主要原因是：
第一，D 相比 C 的 FP 下降主要来自_______，说明_______。
第二，RAG evidence 在多数样本中_______，但仍存在_______问题。
第三，下一步建议_______，仍然不使用 domain_test，不进入 P5。
```
