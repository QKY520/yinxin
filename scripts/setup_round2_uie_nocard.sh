#!/usr/bin/env bash
set -euo pipefail
stage=/root/autodl-tmp/round2_uie_nocard_20261010
uie_env=/root/autodl-tmp/venvs/uie-base-round2-cpu
old_python=/root/autodl-tmp/venvs/equipment-ie/bin/python
if compgen -G '/dev/nvidia[0-9]*' >/dev/null; then
  echo 'Refusing: numbered GPU devices are exposed' >&2
  exit 1
fi
if [[ "${1:-}" == '--resume-install-only' ]]; then
  test -f "$stage/qwen_environment_before.txt"
  test -x "$uie_env/bin/python"
  "$uie_env/bin/python" -c 'import sys; assert sys.prefix == "/root/autodl-tmp/venvs/uie-base-round2-cpu"'
else
  test ! -e "$stage"
  test ! -e "$uie_env"
  mkdir "$stage"
  "$old_python" -m pip freeze > "$stage/qwen_environment_before.txt"
  "$old_python" -m venv "$uie_env"
fi
source /etc/network_turbo
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NO_PROXY=mirrors.aliyun.com,bj.bcebos.com no_proxy=mirrors.aliyun.com,bj.bcebos.com
"$uie_env/bin/python" -m pip install --no-cache-dir --index-url https://mirrors.aliyun.com/pypi/simple 'setuptools==75.8.0' wheel
"$uie_env/bin/python" -m pip install --no-cache-dir --no-build-isolation --index-url https://mirrors.aliyun.com/pypi/simple --prefer-binary -r /root/project/configs/round2_uie_nocard_20261010/requirements-cpu.txt
"$uie_env/bin/python" -m pip check
"$uie_env/bin/python" -m pip freeze > "$stage/uie_cpu_environment.freeze.txt"
"$old_python" -m pip freeze > "$stage/qwen_environment_after.txt"
cmp "$stage/qwen_environment_before.txt" "$stage/qwen_environment_after.txt"
# Import-only: do not instantiate Taskflow/UIE or call forward().
"$uie_env/bin/python" -c 'import paddle,paddlenlp; from paddlenlp.transformers import UIE,AutoTokenizer; print("UIE_IMPORT_OK",paddle.__version__,paddlenlp.__version__,paddle.is_compiled_with_cuda())'
