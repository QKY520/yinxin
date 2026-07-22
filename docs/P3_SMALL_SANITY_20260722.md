# P3 Small GPU Sanity Report - 2026-07-22

## Scope

The human approved only a small P3 sanity run after switching AutoDL to paid
GPU mode.

Approved live price:

- RTX 4090: `2.7 CNY/hour`

Bounded scope:

- model: Qwen2.5-7B
- dataset: first 20 rows of CLUENER dev
- config family: A
- examples: fixed random
- K: 5
- seed: 42
- no glossary
- no RAG
- no self-verification
- no P4/P5
- no full CLUENER dev gate
- no full ablation grid

## GPU Status

Before vLLM startup:

- GPU: NVIDIA GeForce RTX 4090
- memory: `0 MiB / 24564 MiB`
- running GPU processes: none

After every vLLM attempt, the server was stopped and GPU memory returned to
`0 MiB`.

## Inputs

The 20-row sanity subset was created from CLUENER dev:

```text
head -n 20 /root/autodl-tmp/data/cluener_dev.jsonl > /root/project/cache/p3_cluener_dev20_seed42.jsonl
```

Fixed K-shot examples:

- `cluener-train-10227`
- `cluener-train-1774`
- `cluener-train-3916`
- `cluener-train-510`
- `cluener-train-8450`

## Results

| Run | Prompt change | Parse failures | Parse rate | Precision | Recall | F1 | Gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| v1 | initial P3 prompt | 2/20 | 10.0% | 0.4032 | 0.5435 | 0.4630 | failed |
| v2 | forbid unsupported schema types and occurrence overflow | 1/20 | 5.0% | 0.4259 | 0.5000 | 0.4600 | failed by strict `<5%` |
| v3 | additionally forbid overlap/nesting and title+name whole spans | 2/20 | 10.0% | 0.3636 | 0.4348 | 0.3960 | failed |

The best run was v2, but it still does not satisfy the P3 parse-failure gate
because the gate requires parse failures below 5 percent, not equal to 5
percent.

## Failure Diagnosis

v1 failures:

- `cluener-dev-4`: occurrence overflow for `牛奶海`.
- `cluener-dev-9`: unsupported entity type `event`.

v2 failure:

- `cluener-dev-11`: overlapping entities, likely a title/name boundary issue.

v3 failures:

- `cluener-dev-9`: unsupported entity type `event` returned again.
- `cluener-dev-11`: overlapping entities returned again.

Interpretation:

- The model can produce nonzero NER signal on the 20-row sanity subset.
- Prompt-only tightening is unstable on this small subset.
- The current retry prompt is too generic because it appends only
  `只返回合法JSON`; it does not feed the parser error back to the model.

## Artifacts

Remote files are backed up under:

- `/root/autodl-tmp/backup/p3/p3_cluener_dev20_sanity_attempts_20260722.tar.gz`

Local backup:

- `D:\yinsir\backups\P3\p3_cluener_dev20_sanity_attempts_20260722.tar.gz`

Archive size:

- `48277` bytes

Remote/local archive SHA256:

- `111f72dead0c77904ec350cdefe6bfd5106e1c9915fcb32c4ab5daa4c7317df4`

Important per-query files inside the archive:

- `results/p3/p3_cluener_dev20_a_k5_sanity_per_query.jsonl`
- `results/p3/p3_cluener_dev20_a_k5_sanity_v2_per_query.jsonl`
- `results/p3/p3_cluener_dev20_a_k5_sanity_v3_per_query.jsonl`

## Cost Estimate

Observed agent-managed paid-GPU window was approximately 09:26-09:44
Asia/Shanghai on 2026-07-22, about 18 minutes.

At 2.7 CNY/hour, the estimated cost is:

- `0.30 hours * 2.7 = 0.81 CNY`

AutoDL billing is the authoritative cost record.

## Gate Status

P3 small sanity did not pass the strict parse-failure gate.

Do not proceed to full CLUENER dev, P4, P5, or the ablation grid.

Recommended next step in GPU-free mode:

- implement an error-aware retry prompt that includes the parser error;
- preserve strict parser semantics for evaluation;
- rerun only a dry-run/preflight first;
- request explicit approval before another small paid-GPU sanity retry.

## Post-Shutdown Preparation

After the human shut down the paid GPU instance, the next GPU-free retry
preparation was implemented locally only:

- added parser-error-aware retry prompt construction;
- updated the P3 runner so the second attempt includes the concrete parser
  error instead of only appending `只返回合法JSON`;
- added a unit test for the retry prompt;
- added `configs/p3_cluener_dev20_a_k5_sanity_v4_error_retry.yaml`.

This v4 config is intentionally unauthorized:

- `execution.authorized=false`;
- `model_calls_allowed=false`;
- `human_gate=null`.

Remote GPU-free validation after reboot:

- AutoDL was booted in GPU-free mode.
- Remote tests passed:
  `python -m unittest tests.test_extraction tests.test_schema tests.test_llm_labeling tests.test_public_data tests.test_domain_data`
  reported 52 tests OK.
- v4 dry-run passed with:
  - query records: `20`;
  - model calls: `0`;
  - GPU device present: `false`;
  - max prompt chars: `1981`;
  - config SHA256:
    `c5919803c9a8b14f96bae06ea73d02db28a88395ed004337d9f5b7878f990481`;
  - prompt manifest SHA256:
    `f995a43846151f18560dad9b00716f835b81898d2baac8f49cf20555f4620380`.

Local dry-run backup:

- `D:\yinsir\backups\P3\p3_cluener_dev20_v4_error_retry_dryrun_20260722\`

Remote/local tar backup:

- Remote:
  `/root/autodl-tmp/backup/p3/p3_cluener_dev20_v4_error_retry_dryrun_20260722.tar.gz`
- Local:
  `D:\yinsir\backups\P3\p3_cluener_dev20_v4_error_retry_dryrun_20260722.tar.gz`
- bytes: `3582`
- SHA256:
  `92962e68a45ee92b1368e3b3f5ecc3cdf53664e83bdd282c1be257f96f7a4a00`

Pending before any further GPU use:

- ask for explicit human approval before any paid-GPU v4 retry.
