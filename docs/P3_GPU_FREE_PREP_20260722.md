# P3 GPU-Free Preparation Report - 2026-07-22

## Scope

This step prepared the P3 baseline extraction runner in AutoDL GPU-free mode.
No vLLM server was started, no model weights were loaded, no API/model calls
were made, and no paid GPU work was performed.

The implemented target is the first P3 sanity configuration:

- dataset: `CLUENER`
- split: `dev`
- config: `A`
- examples: `fixed_random`
- K: `5`
- seed: `42`
- glossary: disabled
- RAG: disabled
- self-verification: disabled

## Implemented Files

- `src/equipment_ie/extraction.py`
- `scripts/run_p3_extraction.py`
- `configs/p3_cluener_dev_a_k5_dryrun.yaml`
- `tests/test_extraction.py`

## Functionality

The new P3 extraction code supports:

- deterministic fixed-random K-shot example selection;
- prompt construction in the required block order:
  task definition, schema, optional glossary, optional RAG, demonstrations,
  query text;
- occurrence-based JSON entity output;
- exact span-plus-type parsing into the unified IE schema;
- OpenAI-compatible request-envelope hashing;
- dry-run prompt/request manifest generation without model calls;
- future authorized execution path with cache, one retry prompt, per-query
  rows, parse-failure handling, and entity micro P/R/F1 aggregation.

## Remote Tests

Executed on AutoDL in GPU-free mode:

```text
python -m unittest tests.test_extraction tests.test_schema tests.test_llm_labeling tests.test_public_data tests.test_domain_data
```

Result:

```text
Ran 51 tests in 0.917s
OK
```

## Dry-Run Result

Command:

```text
python scripts/run_p3_extraction.py --config configs/p3_cluener_dev_a_k5_dryrun.yaml --dry-run
```

Result summary:

- run ID: `p3-cluener-dev-a-k5-seed42-dryrun`
- query records checked: `20`
- fixed examples:
  - `cluener-train-10227`
  - `cluener-train-1774`
  - `cluener-train-3916`
  - `cluener-train-510`
  - `cluener-train-8450`
- maximum prompt length: `1781` characters
- API/model calls: `0`
- model weights loaded: `false`
- GPU device present: `false`
- config SHA256:
  `666bbff3ef271f25daf3a0598c6eaf0c4b353fc3e8fa2418319ffd5565c9337f`
- prompt manifest SHA256:
  `9cb95dcc5845c741d9ee7715539335981171367b8eb38554de1004a6c903c904`

Local backup:

- `D:\yinsir\backups\P3\p3_cluener_dev_a_k5_dryrun_20260722\`

Local backup hashes:

- `p3_cluener_dev_a_k5_dryrun_manifest.json`:
  `174ed1c8a7dfef2f4bfe062074558aae944dc8d1047ed52ab2c5d99e7f4c9e3f`
- `p3_cluener_dev_a_k5_dryrun_prompts.jsonl`:
  `9cb95dcc5845c741d9ee7715539335981171367b8eb38554de1004a6c903c904`

Remote/local tar backup:

- Remote:
  `/root/autodl-tmp/backup/p3/p3_cluener_dev_a_k5_dryrun_20260722.tar.gz`
- Local:
  `D:\yinsir\backups\P3\p3_cluener_dev_a_k5_dryrun_20260722.tar.gz`
- bytes: `2435`
- SHA256:
  `af6c21494ecfe8f7d246834e0cacabc8eaadd65c44cd799ce461ed610ab9afe7`

## Next Gate

The next step should be a bounded paid-GPU P3 sanity run only after explicit
human approval.

Recommended scope for the next gate:

- boot paid GPU mode with RTX 4090;
- verify live price, GPU model, free memory, and no conflicting process;
- serve Qwen2.5-7B with vLLM;
- run only config A on CLUENER dev K=5;
- verify P3 gate conditions:
  - entity micro-F1 is greater than zero;
  - no single entity type exceeds 90 percent of predictions;
  - parse-failure rate is below 5 percent;
  - per-query JSONL rows reload successfully.

Do not run P4/P5 or the full ablation grid until the P3 sanity gate passes and
the human approves the next phase.
