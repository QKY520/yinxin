"""Create UIE-only dlopen aliases to existing verified wheels; AutoDL/no-card only."""
import hashlib
import json
from pathlib import Path

ENV = Path('/root/autodl-tmp/venvs/uie-base-round2-gpu')
SITE = ENV/'lib/python3.12/site-packages/nvidia'
LOADER = ENV/'round2_cuda11_loader_v1'
TARGETS = {
    'libcudart.so': 'cuda_runtime/lib/libcudart.so.11.0',
    'libcublas.so': 'cublas/lib/libcublas.so.11',
    'libcublasLt.so': 'cublas/lib/libcublasLt.so.11',
    'libcudnn.so': 'cudnn/lib/libcudnn.so.8',
    'libcusolver.so': 'cusolver/lib/libcusolver.so.11',
    'libcusparse.so': 'cusparse/lib/libcusparse.so.11',
    'libcurand.so': 'curand/lib/libcurand.so.10',
    'libcufft.so': 'cufft/lib/libcufft.so.10',
    'libnvrtc.so': 'cuda_nvrtc/lib/libnvrtc.so.11.2',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    if list(Path('/dev').glob('nvidia[0-9]*')):
        raise RuntimeError('Loader preparation requires no-card mode')
    if LOADER.exists() and (LOADER.is_symlink() or LOADER.resolve().parent != ENV.resolve()):
        raise RuntimeError('Loader directory must stay inside UIE environment')
    targets = {name: (SITE/rel).resolve(strict=True) for name, rel in TARGETS.items()}
    for target in targets.values():
        if not target.is_relative_to(SITE.resolve()) or not target.is_file():
            raise RuntimeError('Library target outside isolated UIE wheels')
    LOADER.mkdir(exist_ok=True)
    for name, target in targets.items():
        alias = LOADER/name
        if alias.exists() or alias.is_symlink():
            if not alias.is_symlink() or alias.resolve(strict=True) != target:
                raise RuntimeError(f'Refusing to replace existing loader entry: {alias}')
        else:
            alias.symlink_to(target)
    report = {'loader_dir': str(LOADER), 'model_calls': 0, 'system_modified': False,
              'entries': {name: {'target': str(target), 'sha256': digest(target)} for name, target in targets.items()}}
    manifest = LOADER/'loader_manifest.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != report:
            raise RuntimeError('Existing loader manifest differs; preserve and diagnose')
    else:
        with manifest.open('x') as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
