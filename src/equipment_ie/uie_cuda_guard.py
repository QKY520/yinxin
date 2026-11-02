"""Check actual UIE library selection before models; no implicit CUDA tensor check."""
import ctypes
import os
from pathlib import Path

GPU_ENV = Path('/root/autodl-tmp/venvs/uie-base-round2-gpu')
LIB_ROOT = GPU_ENV/'lib/python3.12/site-packages/nvidia'
LOADER = GPU_ENV/'round2_cuda11_loader_v1'
LIB_PREFIXES = ('libcudnn', 'libcudart', 'libcublas', 'libcusolver', 'libcusparse',
                'libcurand', 'libcufft', 'libnvrtc')


def require_isolated_runtime(report):
    if report['compiled_cuda'] != '11.8' or report['compiled_cudnn'] != '8.6.0':
        raise RuntimeError('UIE compile target differs from locked CUDA11.8/cuDNN8.6')
    if report['isolated_cudnn_version'] != 8600 or report['paddle_runtime_cudnn_version'] != 8600:
        raise RuntimeError('Paddle actual cuDNN differs from isolated8.6; refuse model loading')
    if report['FLAGS_cudnn_dir'] != str(LOADER) or report['FLAGS_cuda_dir'] != str(LOADER):
        raise RuntimeError('UIE process-local loader flags missing or changed')
    paths = report['loaded_cuda_library_paths']
    if not any(Path(path).name.startswith('libcudnn.so.8') for path in paths):
        raise RuntimeError('Actual cuDNN8 library mapping not observed')
    for path in paths:
        if not Path(path).resolve().is_relative_to(LIB_ROOT.resolve()):
            raise RuntimeError(f'Non-isolated CUDA/cuDNN mapped: {path}')
    return report


def inspect_runtime(paddle):
    isolated = ctypes.CDLL(str(LIB_ROOT/'cudnn/lib/libcudnn.so.8'))
    isolated.cudnnGetVersion.restype = ctypes.c_size_t
    # This is a library-version query, not set_device/run_check/model/forward.
    actual = int(paddle.base.core.cudnn_version())
    paths = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                    if len(line.split()) >= 6 and
                    Path(line.split()[-1]).name.startswith(LIB_PREFIXES)})
    report = {'compiled_cuda': paddle.version.cuda(), 'compiled_cudnn': paddle.version.cudnn(),
              'isolated_cudnn_version': int(isolated.cudnnGetVersion()),
              'paddle_runtime_cudnn_version': actual, 'loaded_cuda_library_paths': paths,
              'FLAGS_cudnn_dir': os.environ.get('FLAGS_cudnn_dir'),
              'FLAGS_cuda_dir': os.environ.get('FLAGS_cuda_dir')}
    return require_isolated_runtime(report)
