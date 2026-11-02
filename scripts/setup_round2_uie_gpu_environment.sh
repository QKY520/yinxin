#!/usr/bin/env bash
# Installs an isolated GPU build in no-card mode. Import-only; never run_check/forward.
set -euo pipefail
stage=/root/autodl-tmp/round2_uie_nocard_20261010
cpu_env=/root/autodl-tmp/venvs/uie-base-round2-cpu
gpu_env=/root/autodl-tmp/venvs/uie-base-round2-gpu
old_python=/root/autodl-tmp/venvs/equipment-ie/bin/python
if compgen -G '/dev/nvidia[0-9]*' >/dev/null; then exit 1; fi
source /etc/network_turbo
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NO_PROXY=mirrors.aliyun.com no_proxy=mirrors.aliyun.com
if [[ "${1:-}" == '--resume-install-only' ]]; then
  test -x "$gpu_env/bin/python"
  "$gpu_env/bin/python" -c 'import sys; assert sys.prefix == "/root/autodl-tmp/venvs/uie-base-round2-gpu"'
else
  test ! -e "$gpu_env"
  "$old_python" -m venv "$gpu_env"
  "$gpu_env/bin/python" /root/project/scripts/copy_round2_uie_dependencies.py
fi
# Existing compatible dependencies were independently copied above, not linked.
test -f "$stage/gpu_dependency_copy.json"
"$gpu_env/bin/python" -m pip check
"$gpu_env/bin/python" -m pip install --no-deps "$stage/gpu_wheelhouse/paddlepaddle_gpu-2.6.2-cp312-cp312-manylinux1_x86_64.whl"
"$gpu_env/bin/python" -m pip check
"$gpu_env/bin/python" -m pip freeze > "$stage/uie_gpu_environment.freeze.txt"
"$old_python" -m pip freeze > "$stage/qwen_environment_after_gpu_setup.txt"
cmp "$stage/qwen_environment_before.txt" "$stage/qwen_environment_after_gpu_setup.txt"
# Dynamic-library loading and import only. No tensors, model or forward.
"$gpu_env/bin/python" /root/project/scripts/audit_round2_uie_gpu_import.py
