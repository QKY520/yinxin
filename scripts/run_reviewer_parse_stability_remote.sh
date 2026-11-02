#!/usr/bin/env bash
set -euo pipefail

ROOT=/root/autodl-tmp/reviewer_baselines_20260828_parse_stability20
PROJECT=/root/project
ENV=/root/autodl-tmp/venvs/equipment-ie

screen -dmS reviewer-b1-stability-vllm bash -lc \
  "source ${ENV}/bin/activate; exec vllm serve /root/autodl-tmp/models/qwen2.5-7b --served-model-name /root/autodl-tmp/models/qwen2.5-7b --max-model-len 8192 --gpu-memory-utilization 0.90 --port 8000 2>&1 | tee ${ROOT}/logs/vllm.log"

for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1:8000/v1/models >/dev/null; then
    break
  fi
  sleep 2
done
curl -sf http://127.0.0.1:8000/v1/models >/dev/null

screen -dmS reviewer-b1-stability-run bash -lc \
  "source ${ENV}/bin/activate; cd ${PROJECT}; for f in ${ROOT}/configs/*.yaml; do echo START \${f} \$(date -Is); python scripts/run_p3_extraction.py --config \${f}; rc=\$?; echo EXIT \${rc} \${f} \$(date -Is); test \${rc} -eq 0 || exit \${rc}; done 2>&1 | tee ${ROOT}/logs/stability.log"

echo "vllm_and_stability_started"
