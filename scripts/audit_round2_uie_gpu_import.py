#!/usr/bin/env python3
"""No-card import and shared-library inspection only; NEVER run_check or a model."""
import importlib.metadata
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from equipment_ie.uie_cuda_guard import inspect_runtime


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report-name',default='gpu_import_validation.json')
    args=parser.parse_args()
    assert Path(args.report_name).name==args.report_name and args.report_name.endswith('.json')
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    import paddle,paddlenlp
    from paddlenlp.transformers import UIE,AutoTokenizer
    assert paddle.is_compiled_with_cuda()
    runtime = inspect_runtime(paddle)
    libs=Path(paddle.__file__).parent/'base/libpaddle.so'
    linked=subprocess.run(['ldd',str(libs)],capture_output=True,text=True,check=True).stdout
    missing=[line.strip() for line in linked.splitlines() if 'not found' in line]
    # Driver absence in no-card mode is expected; user-space CUDA libraries are not.
    unexpected=[v for v in missing if 'libcuda.so' not in v]
    if unexpected:raise RuntimeError({'missing_user_space_libraries':unexpected})
    report={'model_calls':0,'model_instantiated':False,'compiled_with_cuda':True,
            'paddle':importlib.metadata.version('paddlepaddle-gpu'),'paddlenlp':importlib.metadata.version('paddlenlp'),
            'compiled_cuda':paddle.version.cuda(),'compiled_cudnn':paddle.version.cudnn(),
            'ldd_missing':missing,'actual_runtime_library_check':runtime,
            'gpu_runtime_forward_validated':False,'learning_validated':False}
    destination=Path('/root/autodl-tmp/round2_uie_nocard_20261010')/args.report_name
    with destination.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))


if __name__=='__main__':main()
