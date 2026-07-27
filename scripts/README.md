# Scripts

Scripts load run settings from `configs/` rather than embedding experiment
parameters. Run project Python only on AutoDL.

P1 public-data preparation:

```bash
cd /root/project
source /root/venv/bin/activate
./scripts/download_public_data.sh
python scripts/prepare_public_data.py --config configs/p1_public_data.yaml
python scripts/verify_artifact_manifest.py
```

P2 candidate collection before schema Pause A:

```bash
source /etc/network_turbo
cd /root/project
source /root/venv/bin/activate
python scripts/prepare_domain_candidates.py --config configs/p2_domain_data.yaml
```

This command collects candidates only. It does not run the distant-supervision
prelabeler or any LLM annotation step.

P2 deterministic distant-supervision proposals after schema approval:

```bash
cd /root/project
source /root/venv/bin/activate
python scripts/prepare_domain_prelabels.py \
  --config configs/p2_distant_supervision.yaml
python scripts/verify_domain_prelabels.py \
  --config configs/p2_distant_supervision.yaml
```

This command requires GPU-free mode. It performs exact longest-first seed-term
matching only, infers no relations, and leaves all LLM disagreement and human
annotation fields explicitly unstarted.

P2 14B labeling preparation (GPU-free; no API call):

```bash
python scripts/run_p2_llm_labeling.py \
  --config configs/p2_llm_label_sanity.yaml --dry-run
python scripts/run_p2_llm_labeling.py \
  --config configs/p2_llm_label_full.yaml --dry-run
```

Actual execution uses `--execute`, but the checked-in configurations reject it
until `execution.authorized` and `approval_record` are changed in a separately
approved and committed decision. Dry-run loads the tokenizer only, verifies all
input/model metadata hashes, computes exact chat-template token counts, and
writes a deployment manifest without loading model weights or contacting vLLM.

P6-QA0 blank double-annotation preparation (AutoDL GPU-free only):

```bash
cd /root/project
source /root/venv/bin/activate
python scripts/prepare_p6_qa0_blind_annotation.py
```

This command requires the exact frozen `domain_test.jsonl` SHA256 and the P2
`FROZEN` marker. It creates independently shuffled blank NER sheets for two
human annotators plus a coordinator-only map and manifest under
`/root/autodl-tmp/backup/p6/`. It does not modify frozen data, expose old labels
to annotators, generate prompts, run a model, or authorize human annotation.

P6-QA2 completed-sheet validation (AutoDL GPU-free only):

```bash
cd /root/project
source /root/venv/bin/activate
python scripts/validate_p6_qa2_annotations.py
```

The validator locks the submitted completed sheets and QA0 blank/map hashes,
checks blind-ID/text alignment, parses exact NER spans, rejects blank or invalid
fields, flags duplicates/overlaps/unresolved repeated mentions, and computes
file-level exact span+type concordance. It never reads old gold or predictions,
never repairs labels, and cannot by itself establish independent human
provenance.

P6-QA1R diagnostic classification of the already blocked QA2 files (AutoDL
GPU-free only):

```bash
cd /root/project
source /root/venv/bin/activate
python scripts/analyze_p6_qa2_disagreements.py
```

This locks the existing QA2 hashes and classifies same-boundary type conflicts,
overlapping-boundary conflicts, and unmatched A/B entities. Its output is
coordinator-only diagnostic material, not human IAA or adjudication, and it
does not modify labels or read gold/predictions.

P6-QA1R non-test calibration preparation (AutoDL GPU-free only):

```bash
cd /root/project
source /root/venv/bin/activate
python scripts/prepare_p6_qa1r_calibration.py
```

This locks `domain_dev.jsonl`, selects 24 texts using text-only ambiguity
buckets, strips all existing labels/relations, and creates differently shuffled
blank A/B calibration sheets plus a coordinator-only map. Calibration is for
guideline repair and must not be reported as formal test IAA.

P6-QA1R completed calibration validation (AutoDL GPU-free only):

```bash
cd /root/project
source /root/venv/bin/activate
python scripts/validate_p6_qa1r_calibration.py
```

The validator locks both blank sheets, both submitted completed sheets, and the
coordinator map by SHA256. It checks row/text alignment, exact spans and types,
entity ordering, repeated mentions, and uncertainty codes, then writes a
coordinator-only report, issue table, disagreement JSONL, and manifest. It does
not read old dev gold, frozen test, predictions, prompts, or models; it never
repairs labels and cannot establish independent human provenance. Existing
output directories are refused. The 2026-07-27 result is `blocked`; see
`docs/P6_QA1R_CALIBRATION_VALIDATION_20260727.md`.
