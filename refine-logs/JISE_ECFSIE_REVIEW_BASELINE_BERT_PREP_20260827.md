# JISE EC-FSIE reviewer-baseline BERT preparation closeout (2026-08-27)

## Gate and scope

- Human gate: `JISE_ECFSIE_REVIEW_BASELINE_BERT_PREP_APPROVED`.
- Downloaded only the required `bert-base-chinese` PyTorch safetensors and
  tokenizer/configuration files in AutoDL no-card mode.
- No GPU, vLLM, training, inference, evaluation, or frozen-test access occurred.

## Artifact

Remote model directory: `/root/autodl-tmp/models/bert-base-chinese/`.

The model tensor is 411,553,788 bytes; the total six-file payload is
approximately **412 MB**. The complete repository's redundant Flax/PyTorch-bin/TensorFlow files
were intentionally not downloaded.

Source: `google-bert/bert-base-chinese@master` via ModelScope.

## Verification

- All six requested files match ModelScope API byte sizes and SHA256 values.
- `AutoConfig` and `AutoTokenizer` load locally with `local_files_only=True`.
- Safetensors metadata is valid (`format=pt`), with 206 tensors, BERT-base
  hidden size 768, 12 layers, and vocabulary size 21,128.
- GPU probe remains `No devices were found`; no experiment process is active.
- AutoDL free space remains about 68 GB.
- Hash manifests are stored remotely and mirrored locally under
  `results/reviewer_baselines_20260827/m3_prep/`:
  `bert_file_manifest.json` SHA256
  `6d40e471a89bfba841ff05bae7f51ba50c888407319c8159cc98c726fcd16479` and
  `bert_load_sanity.json` SHA256
  `0b28081cd97ca8a90847c9c6dd13895a4660f95bfbd13755657ceff536c3dee0`.

## Next step (paused)

BERT-CRF model preparation is complete. A separate exact gate is still needed
before any training or final evaluation (for example,
`JISE_ECFSIE_REVIEW_BASELINE_M4_GPU_EXECUTION_APPROVED`).
