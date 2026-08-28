#!/usr/bin/env bash
set -euo pipefail
ROOT=/root/autodl-tmp/reviewer_baselines_20260828_span_index
screen -dmS reviewer-b1-span-run bash -lc \
  "source /root/autodl-tmp/venvs/equipment-ie/bin/activate; cd /root/project; for f in ${ROOT}/configs/*.yaml; do echo START \${f} \$(date -Is); python scripts/run_p3_extraction.py --config \${f}; rc=\$?; echo EXIT \${rc} \${f} \$(date -Is); test \${rc} -eq 0 || exit \${rc}; done 2>&1 | tee ${ROOT}/logs/span_index.log"
echo runner_started
