#!/usr/bin/env python3
"""Copy verified CPU dependencies into a NEW isolated GPU venv, excluding CPU Paddle."""
import hashlib
import json
import shutil
import sys
from pathlib import Path


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    destination=Path('/root/autodl-tmp/venvs/uie-base-round2-gpu/lib/python3.12/site-packages')
    source=Path('/root/autodl-tmp/venvs/uie-base-round2-cpu/lib/python3.12/site-packages')
    assert sys.prefix=='/root/autodl-tmp/venvs/uie-base-round2-gpu'
    receipt=Path('/root/autodl-tmp/round2_uie_nocard_20261010/gpu_dependency_copy.json')
    assert not receipt.exists()
    # Excluding only the CPU framework and the new venv's own pip prevents
    # relocation of console-script shebangs and avoids any shared hardlinks.
    copied=[]
    for path in sorted(source.iterdir()):
        if path.name=='paddle' or path.name.startswith('paddlepaddle-') or path.name=='pip' or path.name.startswith('pip-'):
            continue
        target=destination/path.name
        if target.exists():
            raise RuntimeError(f'Unexpected existing destination: {target}')
        if path.is_dir():shutil.copytree(path,target)
        else:shutil.copyfile(path,target)
        copied.append(path.name)
    receipt.write_text(json.dumps({'method':'independent byte copy; no hardlinks; no model import',
                                  'excluded':['CPU paddle','pip'],'packages_or_files':copied,'source_environment_unchanged':True},indent=2))
    print('DEPENDENCIES_COPIED_WITHOUT_CPU_PADDLE',len(copied))


if __name__=='__main__':main()
