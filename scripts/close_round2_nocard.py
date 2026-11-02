#!/usr/bin/env python3
"""Seal and back up verified no-card prep only; never start a model."""
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGE=Path('/root/autodl-tmp/round2_uie_nocard_20261010')
BUNDLE=Path('/root/autodl-tmp/round2_runtime_bundle_20261010_r3')
AGREEMENT=Path('/root/autodl-tmp/round2_agreement_ci_20261010')
OUT=Path('/root/autodl-tmp/round2_nocard_closeout_20261010')
BACKUP=Path('/root/autodl-tmp/backup/round2')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    report=json.loads((STAGE/'uie_preflight_report.json').read_text())
    assert report['verdict']=='PASS_OFFLINE_ONLY' and not report['problems']
    assert (STAGE/'uie_gpu_environment.freeze.txt').exists(), 'GPU install not complete'
    assert (STAGE/'gpu_import_validation.json').exists(), 'GPU import/link validation missing'
    validation=json.loads((STAGE/'gpu_import_validation.json').read_text())
    assert validation['compiled_with_cuda'] is True and validation['model_calls']==0
    combined=json.loads((STAGE/'gpu_import_validation_cuda11.json').read_text())
    assert combined['compiled_with_cuda'] and combined['model_calls']==0 and not combined['model_instantiated']
    assert combined['compiled_cuda']=='11.8' and combined['compiled_cudnn']=='8.6.0'
    cuda_validation=json.loads((STAGE/'cuda_libraries_validation.json').read_text())
    assert not cuda_validation['errors'] and cuda_validation['model_calls']==0 and cuda_validation['cuda_api_calls']==0
    assert len(cuda_validation['loaded'])==15
    offline=json.loads((STAGE/'final_offline_verification_r3.json').read_text())
    assert offline['tests_passed']==offline['tests_total']==25
    assert offline['uie_disabled_configs_checked']==6 and offline['qwen_disabled_configs_checked']==10
    assert offline['all_disabled_configs_refused_actual_execution'] and offline['model_calls']==0
    assert (STAGE/'uie_gpu_cuda11_environment.freeze.txt').exists()
    assert sha(STAGE/'qwen_environment_before.txt')==sha(STAGE/'qwen_environment_after_gpu_setup.txt')
    assert sha(STAGE/'qwen_environment_before.txt')==sha(STAGE/'qwen_environment_after_cuda11_setup.txt')
    resource=json.loads((STAGE/'model_resource_manifest.json').read_text())
    cuda_wheels=json.loads((STAGE/'cuda11_vendor_wheels.json').read_text())['files']
    assert len(cuda_wheels)==8
    for info in cuda_wheels:
        assert sha(STAGE/'gpu_wheelhouse'/info['filename'])==info['sha256']
    model=Path('/root/autodl-tmp/models/uie-base-round2-official')
    for name,info in resource['files'].items():assert sha(model/name)==info['sha256']
    wheel=STAGE/'gpu_wheelhouse/paddlepaddle_gpu-2.6.2-cp312-cp312-manylinux1_x86_64.whl'
    assert sha(wheel)=='289d9dac958bbb075a62c0a3ede821d67415e23df9bd3f94807d2a4ddc68c879'
    OUT.mkdir(exist_ok=False)
    for source,name in [(STAGE,'uie'),(BUNDLE,'qwen'),(AGREEMENT,'agreement')]:
        destination=OUT/name;destination.mkdir()
        for p in source.rglob('*'):
            relative=p.relative_to(source)
            if 'gpu_wheelhouse' in relative.parts or any('range_chunks' in part for part in relative.parts):continue
            if p.is_file():
                target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    code=OUT/'code';code.mkdir()
    owned=list((ROOT/'scripts').glob('*round2*.py'))+list((ROOT/'scripts').glob('*round2*.sh'))+list((ROOT/'src/equipment_ie').glob('uie*.py'))+list((ROOT/'tests').glob('test_uie*.py'))+[ROOT/'tests/test_round2_statistics.py']
    # Snapshot unchanged shared execution dependencies too; never edit them.
    owned += [ROOT/'tests/test_prepare_round2_nocard.py',ROOT/'scripts/run_p3_extraction.py']
    owned += [ROOT/'src/equipment_ie'/name for name in ['__init__.py','schema.py','extraction.py','llm_labeling.py','domain_data.py']]
    for path in owned:
        target=code/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    locked=OUT/'configs';locked.mkdir()
    for name in ['requirements-cpu.txt','requirements-cuda11.txt']:
        shutil.copyfile(ROOT/'configs/round2_uie_nocard_20261010'/name,locked/name)
    logs=OUT/'logs';logs.mkdir()
    for path in Path('/root/autodl-tmp').glob('round2*.log'):shutil.copyfile(path,logs/path.name)
    # Old phase manifests retain their original snapshot semantics. This is the
    # final immutable transfer manifest, excluding mutable failed download chunks.
    summary={'model_calls':0,'paid_gpu_boot':False,'paper_edited':False,'formal_runs_completed':0,
             'offline_tests':'25/25','qwen_parser_replay':'850/850','qwen_weight_manifest':'15/15',
             'uie_gold_native_token_roundtrip':'490 entities,80 texts; synthetic scores only',
             'gpu_import_and_cuda11_user_libraries':'PASS_IMPORT_ONLY; no context/forward',
             'gpu_runtime_forward_and_learning':'PENDING_SEPARATE_DEV_GATE',
             'next_gate':'dev pilot only; confirm Qwen BF16 and current hourly price',
             'disk_free_bytes':shutil.disk_usage(STAGE).free}
    (OUT/'closeout_summary.json').write_text(json.dumps(summary,indent=2))
    manifest={str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
    (OUT/'artifact_sha256_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True))
    BACKUP.mkdir(exist_ok=True)
    light=BACKUP/'round2_nocard_closeout_20261010.tar.gz'
    assert not light.exists()
    with tarfile.open(light,'w:gz') as archive:archive.add(OUT,arcname=OUT.name)
    weights=BACKUP/'round2_uie_weights_and_gpu_wheel_20261010.tar'
    assert not weights.exists()
    with tarfile.open(weights,'w') as archive:
        for name in resource['files']:archive.add(model/name,arcname='uie-base/'+name)
        archive.add(wheel,arcname='gpu_wheel/'+wheel.name)
        archive.add(STAGE/'model_resource_manifest.json',arcname='model_resource_manifest.json')
        archive.add(wheel.parent/(wheel.name+'.download.json'),arcname='gpu_wheel_download.json')
        archive.add(STAGE/'cuda11_vendor_wheels.json',arcname='cuda11_vendor_wheels.json')
        for info in cuda_wheels:
            archive.add(STAGE/'gpu_wheelhouse'/info['filename'],arcname='cuda11_wheels/'+info['filename'])
    result={str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in [light,weights]}
    receipt=BACKUP/'round2_nocard_archives_20261010.json'
    with receipt.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({'summary':summary,'mirror_files':len(manifest),'archives':result}))


if __name__=='__main__':main()
