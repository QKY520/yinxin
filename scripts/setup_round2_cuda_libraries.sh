#!/usr/bin/env bash
set -euo pipefail
if compgen -G '/dev/nvidia[0-9]*' >/dev/null; then exit 1; fi
source /etc/network_turbo
export NO_PROXY=mirrors.aliyun.com no_proxy=mirrors.aliyun.com
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
stage=/root/autodl-tmp/round2_uie_nocard_20261010
gpu_python=/root/autodl-tmp/venvs/uie-base-round2-gpu/bin/python
"$gpu_python" -m pip install --no-cache-dir --no-index --find-links "$stage/gpu_wheelhouse" --no-deps -r /root/project/configs/round2_uie_nocard_20261010/requirements-cuda11.txt
"$gpu_python" -m pip check
"$gpu_python" -m pip freeze > "$stage/uie_gpu_cuda11_environment.freeze.txt"
/root/autodl-tmp/venvs/equipment-ie/bin/python -m pip freeze > "$stage/qwen_environment_after_cuda11_setup.txt"
cmp "$stage/qwen_environment_before.txt" "$stage/qwen_environment_after_cuda11_setup.txt"
bash /root/project/scripts/round2_uie_gpu_python.sh /root/project/scripts/audit_round2_cuda_libraries.py
bash /root/project/scripts/round2_uie_gpu_python.sh /root/project/scripts/audit_round2_uie_gpu_import.py --report-name gpu_import_validation_cuda11.json
