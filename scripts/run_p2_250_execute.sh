#!/usr/bin/env bash
set -euo pipefail

cd /root/project
mkdir -p logs
exec >> /root/project/logs/p2_250_execute_stdout.log 2>&1

echo "started_at=$(date -Is)"
. /root/autodl-tmp/venvs/equipment-ie/bin/activate
python scripts/run_p2_llm_labeling.py \
  --config configs/p2_llm_label_250_v1.yaml \
  --execute
echo "finished_at=$(date -Is)"
