#!/usr/bin/env python3
"""Final targeted offline tests/configuration checks. No model/framework calls."""
import importlib.util
import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
STAGE=Path('/root/autodl-tmp/round2_uie_nocard_20261010')
BUNDLE=Path('/root/autodl-tmp/round2_runtime_bundle_20261010_r3')


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report-name',default='final_offline_verification.json')
    args=parser.parse_args()
    assert Path(args.report_name).name==args.report_name and args.report_name.endswith('.json')
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')}
    result=subprocess.run([sys.executable,'-m','unittest','tests.test_prepare_round2_nocard',
                           'tests.test_uie_adapter','tests.test_uie_runtime','tests.test_round2_statistics',
                           'tests.test_uie_cuda_guard'],
                          cwd=ROOT,env=env,capture_output=True,text=True)
    print(result.stdout+result.stderr,flush=True)
    assert result.returncode==0
    count=int(re.search(r'Ran (\d+) tests',result.stderr).group(1));assert count==34
    compiled=[];shell=[]
    for path in list((ROOT/'scripts').glob('*round2*.py'))+list((ROOT/'src/equipment_ie').glob('uie*.py')):
        py_compile.compile(str(path),doraise=True);compiled.append(str(path.relative_to(ROOT)))
    for path in (ROOT/'scripts').glob('*round2*.sh'):
        subprocess.run(['bash','-n',str(path)],check=True);shell.append(str(path.relative_to(ROOT)))
    uie=module('run_round2_uie');qwen=module('run_round2_qwen')
    ui_configs=sorted((STAGE/'runtime_configs_not_authorized').glob('*.json'))
    qw_configs=sorted((BUNDLE/'qwen_configs_not_authorized').glob('*.yaml'))
    assert len(ui_configs)==6 and len(qw_configs)==10
    for paths,runner in [(ui_configs,uie),(qw_configs,qwen)]:
        for path in paths:
            cfg=json.loads(path.read_text()) if path.suffix=='.json' else yaml.safe_load(path.read_text())
            runner.validate(cfg,dry_run=True)
            try:runner.validate(cfg,dry_run=False)
            except RuntimeError as exc:
                assert 'gate' in str(exc).lower(),str(exc)
            else:raise AssertionError('Disabled configuration could execute')
    report={'model_calls':0,'tests_passed':count,'tests_total':count,'compiled_python':compiled,
            'shell_syntax_passed':shell,'uie_disabled_configs_checked':len(ui_configs),
            'qwen_disabled_configs_checked':len(qw_configs),'all_disabled_configs_refused_actual_execution':True}
    with (STAGE/args.report_name).open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))


if __name__=='__main__':main()
