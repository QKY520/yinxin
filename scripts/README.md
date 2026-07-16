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
```

This command requires GPU-free mode. It performs exact longest-first seed-term
matching only, infers no relations, and leaves all LLM disagreement and human
annotation fields explicitly unstarted.
