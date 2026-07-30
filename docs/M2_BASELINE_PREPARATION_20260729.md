# M2 Dev Baseline Audit

**Date**: 2026-07-30

**Status**: B001 and B003 complete; local closeout hash-verified

**Scope**: Deterministic exact-glossary baseline G and one locked schema-only
zero-shot baseline Z, both evaluated on `domain_dev50` only.

## 1. Authorization and safeguards

M2 used two separately bounded human gates. The first authorized only the
deterministic G run and Z protocol freeze in AutoDL no-card mode. The second
authorized one paid-card Qwen2.5-7B Z run on `domain_dev50`, with a 0.5-hour
and 1.35 CNY cap. It explicitly excluded dry-run generation, `domain_test`,
support data, glossary, RAG, verification, prompt/config tuning, LaTeX edits,
GitHub synchronization, and secondary review.

- The G runner refused visible GPUs, paths containing `domain_test`, unexpected
  input hashes, existing output paths, and configs permitting model calls.
- Z used the prelocked protocol without changing its prompt, model settings,
  data hash, schema, or sanitizer policy.
- `domain_dev.jsonl`: 50 records, SHA256
  `ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b`.
- `domain_dict.jsonl`: 73 records, SHA256
  `01b857822894bb09268cbb7fb14ad0988630137bb7efae0b9d90f7d75a2f3ef6`.
- G outputs and the Z audit package were written atomically. No label, frozen
  prediction, retrieval artifact, or manuscript file was changed.
- Z completed all 50 records, the vLLM process was stopped, and the 2026-07-30
  closeout check found no GPU device and no relevant process.
- The observed vLLM log window was approximately 19:52:36-19:57:45 CST, about
  5 minutes 9 seconds or 0.23 CNY at 2.7 CNY/hour. Platform billing remains
  authoritative.

## 2. Locked G protocol

G is a deterministic lexical lower bound, not a tuned dictionary system.

- Match every literal, case-sensitive occurrence of each canonical term and
  alias in the frozen 73-entry glossary.
- Exclude surfaces shorter than two characters.
- Apply no normalization and no fuzzy matching.
- Resolve overlaps longest-first. Remaining tie-breakers are dictionary
  priority descending, start offset ascending, surface lexicographic order,
  schema type order, and dictionary row order.
- Score exact character span plus entity type using entity-level micro
  precision, recall, F1, FP, FDR, FP per passage, per-type metrics, and
  zero-gold over-labeling.

The locked config SHA256 is
`1397a5051b21610c2e80c66db7bac8b1162ba4ab4bc7e11f61d75350f1528ee6`.

## 3. Raw dev results

| Scope | TP | FP | FN | Precision | Recall | F1 | FDR | FP/passage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall | 4 | 233 | 303 | 0.016878 | 0.013029 | 0.014706 | 0.983122 | 4.66 |
| EQUIPMENT | 4 | 158 | 146 | 0.024691 | 0.026667 | 0.025641 | 0.975309 | 3.16 |
| MODULE | 0 | 59 | 111 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 1.18 |
| TECH_SCHEME | 0 | 4 | 26 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.08 |
| METRIC | 0 | 12 | 20 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.24 |

Additional deterministic counts:

- 88 eligible glossary surfaces produced 240 candidate matches.
- Longest-first non-overlap removed 3 candidates and retained 237 entity
  predictions.
- Only 4 of 50 passages contained any exact TP; each of those passages had one
  TP, and every TP was EQUIPMENT.
- Both zero-gold passages received predictions: 5 predicted entities total,
  mean 2.5 per zero-gold passage.
- The most frequent selected surfaces were `导弹` (51, EQUIPMENT), `传感器`
  (23, MODULE), `雷达` (23, MODULE), `无人机` (19, EQUIPMENT), and `飞行器`
  (13, EQUIPMENT).

## 4. Locked Z protocol and raw dev results

The schema-only zero-shot protocol is frozen in
`configs/m2_domain_dev_z_schema_only_protocol_locked_20260729.yaml`, SHA256
`2ad29153ca0d5bc377d8cd3618fb3880566a3fa190a883a975f54d91b13267a0`.
The separately approved execution config SHA256 is
`b73066c4fbb405fa63603da53dfff7885ebbadb1975cde48df9529df1288f107`.

- `examples.mode: none`, `k: 0`, and no support-file read.
- No glossary, RAG, demonstration, or verification context.
- Qwen2.5-7B, temperature 0, seed 42, and the existing proposal-stage
  sanitizer for comparability with A/B/C/D.
- No dry-run prompt artifact was generated.

| Scope | TP | FP | FN | Precision | Recall | F1 | FDR | FP/passage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Overall | 137 | 206 | 170 | 0.399417 | 0.446254 | 0.421538 | 0.600583 | 4.12 |
| EQUIPMENT | 71 | 71 | 79 | 0.500000 | 0.473333 | 0.486301 | 0.500000 | 1.42 |
| MODULE | 61 | 78 | 50 | 0.438849 | 0.549550 | 0.488000 | 0.561151 | 1.56 |
| TECH_SCHEME | 2 | 19 | 24 | 0.095238 | 0.076923 | 0.085106 | 0.904762 | 0.38 |
| METRIC | 3 | 38 | 17 | 0.073171 | 0.150000 | 0.098361 | 0.926829 | 0.76 |

Z produced 343 entities. Both zero-gold passages received predictions, with 11
predictions total and a mean of 5.5. Thirteen rows initially failed parsing and
were repaired by the fixed one-retry ladder: 63 distinct requests all received
HTTP 200, and final parse failures were zero. The proposal sanitizer recorded
38 events on 17 passages: 33 invalid-unit drops and 5 overlap drops. End-to-end
extraction elapsed 160.59 seconds, of which 160.26 seconds was model latency.

## 5. Key findings and evidence boundary

1. **G is an extremely weak lexical lower bound on dev.** Its F1 is 0.014706
   and 98.31% of predicted entities are false positives. This provides no
   evidence that exact frozen-glossary matching alone is competitive, but it
   does not isolate the glossary effect in C because G and C differ in more
   than one component and are reported on different evaluation stages.
2. **Z is materially stronger than G on the same dev split, but still has high
   false discovery.** Its F1 is 0.421538 and FDR is 0.600583. This is a
   descriptive dev-side baseline comparison, not frozen-test evidence and not
   a new A/B/C/D test-table row.
3. **The difficult types remain weak.** Z F1 is 0.085106 for TECH_SCHEME and
   0.098361 for METRIC. These diagnostics are consistent with a schema-quality
   limitation, especially the independently observed TECH_SCHEME calibration
   weakness, but they are not the same agreement measurement.
4. **Neither baseline controls zero-gold over-labeling.** G predicts five and Z
   predicts eleven entities across the two zero-gold dev passages.
5. **No post-hoc tuning is authorized.** Do not alter G or Z in response to
   these results under the same names. B002/B004 frozen-test scoring remains a
   separate, unapproved gate.

B001 and B003 are complete on `domain_dev50`. Nothing in M2 supports
frozen-test baseline performance, public-benchmark generalization, K
robustness, RE, CoVe, or statistical significance.

## 6. Artifacts and integrity

- Runner: `scripts/run_m2_exact_glossary_baseline.py`, SHA256
  `fd155e38d06c55e7be4599f4159597450a5daf28d8b4adece98328a7d3cacd5a`.
- Focused tests: `tests/test_run_m2_exact_glossary_baseline.py` plus extraction
  regression tests; 25 tests passed on AutoDL before and after execution.
- Remote output:
  `/root/autodl-tmp/backup/m2/m2_domain_dev_g_exact_glossary_20260729/`.
- Local hash-verified copy:
  `refine-logs/m2_domain_dev_g_exact_glossary_20260729/`.
- Output SHA256 values:
  - predictions: `02cade94bb9f6450afe37517b763568bf48b2fffd312aba0304219abab94aa45`;
  - per-query: `6fd4b25f8105c0a966e211139495d70fb47e71e91fdd9b08ec82eb6d8b5bf6b5`;
  - summary: `30c11f046d79c25aeee88033ff6d99e1dc5ed31b2c9cdb13ca6b0d4aae5f4984`;
  - manifest: `f42ce06404783912c375ab8f7e8663768ce79007f4ee425717a3ecbd646e9f34`.

The local predictions, per-query file, and summary were independently checked
against the copied manifest; every hash matched. The remote and local manifest
hashes also match the value above.

Z artifacts:

- Audit script: `scripts/analyze_m2_zero_shot_baseline.py`, SHA256
  `26cf23342099b4ed014b9d8aca5220003c46530f5b077ef904bcdff8188d5341`.
- Remote package:
  `/root/autodl-tmp/backup/m2/m2_domain_dev_z_schema_only_20260729/`.
- Local hash-verified copy:
  `refine-logs/m2_domain_dev_z_schema_only_20260729/`.
- Analysis SHA256:
  `504d901f6aeccc8043071d92ed9e8505248ab6fbad4aaa5e086406c9f8db4f25`.
- Manifest SHA256:
  `49479141750af9b44bd03226454b0d42081c6997490676f8ceb69210f7505109`.
- Per-query SHA256:
  `b75c87cd994e52ac3e01ce3b10579b115233292cdef414deeba46b792bc3110b`.
- Runner summary SHA256:
  `cd1e3e0f2151b1b85c5d6faf54ea97b89cdf931c1722939b6212cc1779e25ab4`.

On 2026-07-30, PowerShell independently checked all 74 manifest-listed files
in the local copy. File count, byte size, and SHA256 all matched, with zero
failures. No project Python was run on Windows.
