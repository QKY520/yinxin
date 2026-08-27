# JISE EC-FSIE reviewer-baseline M2 sanity closeout (2026-08-27)

## Gate and scope

- Human gate: `JISE_ECFSIE_REVIEW_BASELINE_M2_SANITY_APPROVED`.
- Scope was limited to GPU-free AutoDL sanity checks. No paid GPU, vLLM, Qwen
  weights, model inference, or complete evaluation was run.
- Only declared support/dev/tune data were read: `domain_dev.jsonl` and
  `cluener_tune.jsonl` (three rows per prompt dry-run); frozen test files were
  not read.
- Existing A/B/C/D results and the manuscript were not modified.

## Actions

1. Ran the reviewer-baseline unit suite remotely in the project environment:
   `5 passed`.
2. Ran BERT-CRF support-only synthetic sanity: BIO round-trip, overlap
   rejection, finite CRF loss/backpropagation, masked decode, and a three-step
   toy optimization. Output: `bert_crf_sanity.json`.
3. Generated six Qwen prompt dry-runs (domain/CLUENER × zero-shot,
   glossary-only, lexical-RAG-only), three tune/dev queries per variant. All
   manifests report `api_called=false`, `model_calls=0`, and no GPU device.
4. Generated deterministic BM25 top-3 retrieval manifests for three domain-dev
   and three CLUENER-tune queries per dataset. These manifests contain no gold
   labels and no test rows.

## Verification

- Remote GPU probe: `No devices were found`.
- No vLLM/Qwen/reviewer runner process was active after the checks.
- Prompt variants differ as intended: zero-shot has no examples/glossary/RAG;
  glossary-only enables the 73-entry project glossary (up to 20 matches);
  RAG-only uses the lexical preview with top-3 passages. Prompt maximum sizes
  were 816/907/1692 chars (domain) and 590/590/919 chars (CLUENER).
- Remote M2 artifacts were copied to
  `/root/autodl-tmp/reviewer_baselines_20260827/m2_sanity/` and mirrored to
  `results/reviewer_baselines_20260827/m2_sanity/`.
- Local mirror contains 11 lightweight JSON/JSONL artifacts plus the six
  generated YAML configs (retained on the remote M2 directory); no frozen-test
  path appears in the M2 config/prompt/manifest audit.

## Result and risks

M2 sanity passed. The baseline matrix is executable in principle, but this
step provides no model-quality evidence. BERT-CRF still requires a later
approved remote preparation/training run and `bert-base-chinese` availability.
The BM25 manifests are retrieval-only previews; they are not final baseline
metrics. A separate gate is required before any paid GPU inference or any
frozen-test evaluation.

## Next step (paused)

Stop here and await an exact human gate for M3 preparation/launch. Do not
start vLLM, download/train BERT-CRF, read frozen test, aggregate metrics, or
edit LaTeX without that gate.
