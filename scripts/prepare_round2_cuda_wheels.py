#!/usr/bin/env python3
"""Official PyPI digests before mirror transport; no install/model/GPU calls."""
import concurrent.futures
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STAGE=Path('/root/autodl-tmp/round2_uie_nocard_20261010')


def fetch(line):
    name,version=line.split('==')
    with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json',timeout=60) as r:info=json.load(r)
    assert info['info']['version']==version
    candidates=[item for item in info['urls'] if item['filename'].endswith('x86_64.whl') and 'manylinux' in item['filename'] and '-py3-none-' in item['filename']]
    preferred=[item for item in candidates if 'manylinux2014_x86_64' in item['filename']]
    if preferred:candidates=preferred
    assert len(candidates)==1,(name,[item['filename'] for item in candidates])
    item=candidates[0]
    assert item['url'].startswith('https://files.pythonhosted.org/packages/')
    return {'package':name,'version':version,'filename':item['filename'],'url':item['url'],
            'mirror_url':item['url'].replace('https://files.pythonhosted.org/packages/','https://mirrors.aliyun.com/pypi/packages/'),
            'bytes':item['size'],'sha256':item['digests']['sha256']}


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    manifest=STAGE/'cuda11_vendor_wheels.json'
    if manifest.exists():items=json.loads(manifest.read_text())['files']
    else:
        lines=[line.strip() for line in (ROOT/'configs/round2_uie_nocard_20261010/requirements-cuda11.txt').read_text().splitlines() if line and not line.startswith('#')]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:items=list(pool.map(fetch,lines))
        with manifest.open('x') as f:json.dump({'model_calls':0,'files':items},f,indent=2)
    for item in items:
        target=STAGE/'gpu_wheelhouse'/item['filename']
        if target.exists():
            from download_round2_verified_ranges import digest
            assert digest(target,'sha256')==item['sha256'];continue
        print('DOWNLOAD',item['filename'],item['bytes'],flush=True)
        subprocess.run([sys.executable,str(ROOT/'scripts/download_round2_verified_ranges.py'),
                        '--url',item['url'],'--target',str(target),'--size',str(item['bytes']),
                        '--sha256',item['sha256'],'--chunk-bytes','262144','--workers','32'],check=True)
    print('ALL_CUDA11_VENDOR_WHEELS_HASH_PASS',flush=True)


if __name__=='__main__':main()
