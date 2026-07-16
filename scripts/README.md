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
