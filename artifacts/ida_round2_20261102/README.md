# IDA reproducibility artifacts (2026-11-02)

This directory accompanies the updated project code in the repository root. It provides frozen numerical results, the executed configuration snapshots, the inference glossary, source-selection metadata, and text-free annotation/prediction exports. The original frozen labels and model outputs were not changed. No model inference, training, or new bootstrap analysis was run to prepare this release.

## Contents

- `data/`: original aggregate results, the 13-contrast F1 family, the separately corrected three-endpoint RAG family, calibration results, and BERT metric cells.
- `evaluation/`: 14 aligned systems, each with 170 text-free records; gold and predicted character offsets/types, parse-failure flags, and text hashes. `EXPORT_MANIFEST.json` records source and export hashes. Raw paragraphs, entity surface strings, model replies, and retrieved passages are excluded from these exports.
- `dataset/`: frozen support/dev/test annotations as offsets/types, with 30/50/170 records and 183/307/954 mentions; the 400-candidate provenance ledger; and the 73-entry inference glossary. `source_split` in the candidate ledger describes the upstream split; `frozen_split` in the three offset files describes this project's support/dev/test split.
- `frozen_configs/`: configuration files checked byte-for-byte against the frozen statistics input locks. Their historical authorization flags and absolute data/output paths document the executed setup; adapt paths for a new environment and do not treat those flags as permission to run an experiment.
- `scripts/analyze_round2_comparisons.py`: unchanged paired-analysis script used for the frozen 13/3 protocol. `scripts/build_public_tables.py` and `scripts/audit_public_metrics.py` are explicitly identified aggregate-only publication helpers, rather than original model runners.
- `prompts/template_body.tex`: unchanged placeholder display template. It is not a filled runtime request. Runtime prompt construction is implemented in the project code; filled examples remain in the submitted evidence package.

## Code and runtime

The root `src/equipment_ie/`, `scripts/`, `configs/`, environment files, and matching tests were synchronized from the experiment workspace. Qwen and UIE entry points include `scripts/run_round2_qwen.py` and `scripts/run_round2_uie.py`; the existing BERT reference runner is `scripts/run_bert_crf_baseline.py`. Model weights and full text corpora are obtained separately. The snapshots preserve the execution code; they are not a claim that every historical exploratory script or environment is required for the manuscript.

The equipment setting uses 30 support texts, 50 development texts and 170 test texts. The CLUENER BERT reference uses 50 support texts, 1,075 tuning texts and 1,343 evaluation texts. The 100-passage annotation calibration is separate from the frozen equipment test and is not test-set IAA.

## Statistical reproduction

The text-free exports preserve exactly the IDs, gold/predicted span-and-type tuples, parse-failure treatment, and paired order consumed by the original statistics script. Their aggregate TP/FP/FN were checked against the frozen results. They are sufficient for reproducing the numerical 13/3 paired analysis without redistributing source paragraphs. To run the unchanged analysis in a suitable CPU-only Python/NumPy environment, start in `evaluation/`:

```text
python ../scripts/analyze_round2_comparisons.py --inputs inputs_relative.json --output /path/to/new-output-directory
```

Use a new output directory. The script retains its CPU-only runtime guard. The 13 F1 contrasts and three RAG endpoints have separate Holm corrections. Seed 42 supplies primary comparisons; seeds 42/43/44 are descriptive repeats on the same texts, not 510 independent observations. Marginal intervals are not simultaneous confidence bounds. This release preserves existing results and does not add tests, seeds, or new experimental evidence.

## Source texts and licenses

Original text is acquired from its providers under their applicable terms. Text-free records identify frozen inputs by hash; they do not replace the source corpus for training or inference. Source links and license checks are documented in `SOURCES.md`. No repository-wide license for third-party text is inferred from its public accessibility. This release does not include model weights or the two full-text retrieval replay manifests. Earlier directories in this repository may contain historical text-bearing artifacts; the text-free scope above applies specifically to this release directory.

The manuscript's submitted source/evidence package contains the fuller paired cases and literal requests. This public export is a separate derivative; its hashes intentionally differ from the text-bearing originals. See `RELEASE_MANIFEST.json` for each file's bytes and SHA256, and `evaluation/EXPORT_MANIFEST.json` and `dataset/DATASET_EXPORT_MANIFEST.json` for original source hashes and export transformations.
