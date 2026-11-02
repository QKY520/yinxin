#!/usr/bin/env python3
"""AutoDL no-card: download official UIE resources without loading model weights."""
import ast
import hashlib
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

SOURCE = 'https://raw.githubusercontent.com/PaddlePaddle/PaddleNLP/release/2.8/paddlenlp/taskflow/information_extraction.py'
OUTPUT = Path('/root/autodl-tmp/models/uie-base-round2-official')
STAGE = Path('/root/autodl-tmp/round2_uie_nocard_20261010')


def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            md5.update(block)
            sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*')), 'No-card required'
    resume = sys.argv[1:] == ['--resume-download-only']
    if sys.argv[1:] and not resume:
        raise ValueError('Only --resume-download-only is accepted')
    OUTPUT.mkdir(exist_ok=resume)
    assert not (STAGE/'model_resource_manifest.json').exists(), 'Completed manifest must not be overwritten'
    assert shutil.disk_usage(OUTPUT.parent).free >= 2*1024**3, 'Less than 2GiB free: stop downloads'
    source_path = STAGE/'official_uie_resource_source.py'
    source_bytes = source_path.read_bytes() if resume and source_path.exists() else urllib.request.urlopen(SOURCE, timeout=60).read()
    if source_path.exists():
        assert source_path.read_bytes() == source_bytes, 'Official source changed during resume'
    else:
        source_path.write_bytes(source_bytes)
    tree = ast.parse(source_bytes)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'UIETask')
    attrs = {}
    for n in cls.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            if n.targets[0].id in ['resource_files_names', 'resource_files_urls']:
                attrs[n.targets[0].id] = ast.literal_eval(n.value)
    entries = attrs['resource_files_urls']['uie-base']
    report = {'source_url': SOURCE, 'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
              'model': 'uie-base', 'files': {}, 'model_loaded': False, 'model_calls': 0}
    for key, (url, md5_expected) in entries.items():
        name = attrs['resource_files_names'][key]
        target = OUTPUT/name
        part = OUTPUT/(name+'.partial')
        print('DOWNLOADING', name, flush=True)
        started = time.monotonic()
        if target.exists():
            assert resume and hashes(target)[0] == md5_expected, 'Existing resource mismatch'
        else:
            offset = part.stat().st_size if resume and part.exists() else 0
            request = urllib.request.Request(url, headers={'Range': f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(request, timeout=90) as response:
                if offset:
                    assert response.status == 206 and response.headers.get('Content-Range', '').startswith(f'bytes {offset}-'), 'Unsafe range resume refused'
                with part.open('ab' if offset else 'xb') as f:
                    shutil.copyfileobj(response, f, length=1024*1024)
            actual_md5, _ = hashes(part)
            if actual_md5 != md5_expected:
                raise ValueError(f'{name}: vendor MD5 mismatch; preserved partial')
            part.rename(target)
        actual_md5, actual_sha = hashes(target)
        report['files'][name] = {'url': url, 'vendor_md5': md5_expected, 'sha256': actual_sha,
                                 'bytes': target.stat().st_size, 'seconds': round(time.monotonic()-started, 3)}
        print('VERIFIED', name, target.stat().st_size, actual_sha, flush=True)
    with (STAGE/'model_resource_manifest.json').open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    print('ALL_FIVE_OFFICIAL_RESOURCES_VERIFIED', flush=True)


if __name__ == '__main__':
    main()
