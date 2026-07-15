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
