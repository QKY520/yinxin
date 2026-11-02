#!/usr/bin/env bash
# Process-local CUDA 11 libraries. Never export these into the Qwen environment.
set -euo pipefail
gpu_env=/root/autodl-tmp/venvs/uie-base-round2-gpu
site="$gpu_env/lib/python3.12/site-packages"
loader="$gpu_env/round2_cuda11_loader_v1"
# Paddle2.6 dlopens unversioned names; the NVIDIA wheels provide versioned names.
# Prepare only UIE-owned aliases, never system symlinks or global CUDA settings.
test -d "$loader"
test "$(readlink -f "$loader/libcudnn.so")" = "$site/nvidia/cudnn/lib/libcudnn.so.8"
test "$(readlink -f "$loader/libcublas.so")" = "$site/nvidia/cublas/lib/libcublas.so.11"
export FLAGS_cudnn_dir="$loader" FLAGS_cuda_dir="$loader"
runtime_libs="$site/nvidia/cuda_runtime/lib:$site/nvidia/cublas/lib:$site/nvidia/cudnn/lib:$site/nvidia/cusolver/lib:$site/nvidia/cusparse/lib:$site/nvidia/curand/lib:$site/nvidia/cufft/lib:$site/nvidia/cuda_nvrtc/lib"
export LD_LIBRARY_PATH="$loader:$runtime_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec "$gpu_env/bin/python" "$@"
