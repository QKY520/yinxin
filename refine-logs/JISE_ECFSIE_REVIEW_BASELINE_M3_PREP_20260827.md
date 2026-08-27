# JISE EC-FSIE reviewer-baseline M3 preparation closeout (2026-08-27)

## Gate and scope

- Human gate: `JISE_ECFSIE_REVIEW_BASELINE_M3_PREP_APPROVED`.
- This was preparation only: no paid GPU, vLLM, Qwen inference, BERT training,
  frozen-test read, or final metric evaluation.
- Existing A/B/C/D artifacts, manuscript files, `HANDOFF.md`, and M1 source
  files were left unchanged.

## Preparation actions

1. Audited AutoDL environment and available packages.
2. Revalidated the 54-run M1 manifest (24 Qwen K=5 baselines, 24 A/D K-scan
   runs, and 6 BERT-CRF runs), including unique IDs and output collision
   protection.
3. Checked only declared support/tune/RAG inputs. Evaluation paths were
   recorded for later execution but not opened.
4. Wrote the immutable preparation package under
   `/root/autodl-tmp/reviewer_baselines_20260827/m3_prep/` and mirrored it to
   `results/reviewer_baselines_20260827/m3_prep/`.

## Verification

- GPU probe: `No devices were found`; no experiment process was running.
- `torch`, `transformers`, `modelscope`, and `yaml` imports are available.
- Required support/dev/tune and labels-stripped retrieval corpora exist.
- Run count is 54 and all run IDs are unique; all final output directories were
  absent before preparation.
- Reviewer-baseline tests: `5 passed`; all three new scripts compile remotely.
- Manifest hashes: M1 run manifest
  `85e89f3f060c6e393fc461ed43b439a0a86f634bff74d6cfe6e6dfa21b7bb646`; source
  YAML `4bb2328ea2ed05c28f0945ac1bc97b2fc5352e07a1769e3b6a0bc130149cf657`.
- `test_accessed=false`, `model_calls=0`, and `paid_gpu_started=false` are
  recorded in `m3_prep_manifest.json`.

## Open item and risk

`bert-base-chinese` is not present on AutoDL. The Python dependencies and
custom CRF implementation are ready, but model acquisition must be handled in
a separately approved, GPU-free preparation step (or explicitly excluded from
the paid run). This is not a failed experiment.

## Next step (paused)

Stop and await a precise gate for BERT model acquisition and/or the M4 paid-GPU
execution. Do not launch vLLM, train BERT-CRF, read evaluation files, aggregate
metrics, or edit LaTeX without that gate.
