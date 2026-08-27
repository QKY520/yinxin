# JISE EC-FSIE reviewer-baseline B1 runner preparation (2026-08-27)

## Gate and scope

- Human gate: `JISE_ECFSIE_REVIEW_BASELINE_B1_RUNNER_PREP_APPROVED`.
- This step implemented and validated runners only. It did not start a GPU,
  vLLM, Qwen inference, BERT training, or any evaluation, and did not read
  frozen-test records.

## Implemented

- `scripts/run_reviewer_baselines.py` now materializes 24 non-authorized B1
  Qwen configs (four variants x two datasets x three seeds), refuses overwrite,
  and delegates authorized execution to the canonical P3 runner.
- `scripts/run_p3_extraction.py` now supports a deterministic BM25-only mode.
  Unauthorised RAG-only dry-runs automatically downgrade to lexical preview so
  no dense model can load during preparation.
- `scripts/run_bert_crf_baseline.py` now contains deterministic BIO vocabulary,
  tokenizer/label alignment, support-only BERT+CRF training with tune-only
  early stopping, prediction decoding, and an evaluation safety flag.
- `scripts/dispatch_reviewer_baseline.py` now routes one locked run to the
  canonical Qwen or BERT runner; BERT evaluation remains opt-in.
- Added tests for config materialization, overwrite protection, BIO vocabulary,
  and BERT evaluation gating.

## Verification

- Remote tests: `30 passed` (`tests/test_reviewer_baselines.py` and
  `tests/test_extraction.py`).
- All three modified scripts compile remotely.
- 24 B1 YAML configs are stored under
  `configs/reviewer_baselines_20260827/m3_b1_configs/`; every config is
  explicitly unauthorized and writes to the dated reviewer-baseline output
  root.
- Representative domain zero-shot, glossary-only, BM25-only, and RAG-only
  dry-runs completed with `api_called=false`, `model_calls=0`, and no GPU.
  RAG-only used lexical preview under the safety downgrade.
- Dispatcher Qwen dry-run completed with `model_calls=0`; BERT dispatcher config
  validation rejects incomplete configs before any data access.
- AutoDL probe remained `No devices were found`; no experiment process ran.

## Risks and boundary

The BERT runner is now executable in a later approved run, but this step does
not establish model-quality evidence. Formal Qwen dense RAG requires a paid GPU
and an authorized vLLM session. Frozen-test evaluation remains a separately
locked final action; no test data was opened here.

## Next step (paused)

Await an exact bounded gate for the B1 pilot or execution. The recommended next
step is a small paid-GPU pilot covering one seed and both datasets across the
four Qwen variants, followed by output/latency/cost audit before scaling to all
30 B1 units. Do not launch the complete matrix automatically.
