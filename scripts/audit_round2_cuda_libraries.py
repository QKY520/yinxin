#!/usr/bin/env python3
"""Load user-space libraries only: no CUDA context, tensors, model or forward."""
import ctypes
import importlib.metadata
import json
import os
import time
from pathlib import Path


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    names=['libcudart.so.11.0','libcublas.so.11','libcublasLt.so.11','libcudnn.so.8',
           'libcudnn_ops_infer.so.8','libcudnn_ops_train.so.8','libcudnn_cnn_infer.so.8',
           'libcudnn_cnn_train.so.8','libcudnn_adv_infer.so.8','libcudnn_adv_train.so.8',
           'libcusolver.so.11','libcusparse.so.11','libcurand.so.10','libcufft.so.10','libnvrtc.so.11.2']
    errors={};loaded=[];handles=[]
    for name in names:
        try:handles.append(ctypes.CDLL(name,mode=ctypes.RTLD_GLOBAL));loaded.append(name)
        except OSError as exc:errors[name]=str(exc)
    mapped=sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                   if '/site-packages/nvidia/' in line and '.so' in line})
    report={'model_calls':0,'cuda_api_calls':0,'gpu_forward_validated':False,
            'loaded':loaded,'errors':errors,'mapped_isolated_library_paths':mapped,
            'LD_LIBRARY_PATH':os.environ.get('LD_LIBRARY_PATH')}
    stage=Path('/root/autodl-tmp/round2_uie_nocard_20261010')
    destination=stage/('cuda_libraries_validation.json' if not errors else 'cuda_libraries_missing_initial.json')
    if errors and destination.exists():
        destination=stage/f'cuda_libraries_missing_{time.time_ns()}.json'
    print(json.dumps(report),flush=True)
    with destination.open('x') as f:json.dump(report,f,indent=2)
    if errors:raise RuntimeError('User-space CUDA libraries missing; no-card preparation not complete')


if __name__=='__main__':main()
