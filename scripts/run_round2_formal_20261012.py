"""Sequential approved formal controller; owned processes and immutable seals."""
import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/autodl-tmp/round2_formal_20261012_r3')
ENV = '/root/autodl-tmp/venvs/equipment-ie/bin'
CONDITIONS = {'uie': ('uie_base_zero_shot', 'uie_base_ft30_s42', 'uie_base_ft30_s43', 'uie_base_ft30_s44'),
              'qwen': ('random5_s42', 'random5_s43', 'random5_s44', 'knn5', 'knn5_glossary')}


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stop_owned(process):
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=15)


def seal(directory, family, condition):
    backup = Path('/root/autodl-tmp/backup/round2/formal_20261012_r3')
    backup.mkdir(parents=True, exist_ok=True)
    files = {str(p.relative_to(directory)): sha(p) for p in sorted(directory.rglob('*')) if p.is_file()}
    manifest = directory/'SHA256_manifest.json'
    write(manifest, files)
    archive = backup/(family+'_'+condition+'.tar.gz')
    with tarfile.open(archive, 'x:gz', compresslevel=1) as tar:
        tar.add(directory, arcname=family+'/'+condition)
    receipt = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive),
               'manifest_sha256': sha(manifest), 'files': len(files)}
    write(backup/(family+'_'+condition+'_receipt.json'), receipt)
    return receipt


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--family', required=True, choices=tuple(CONDITIONS))
    args = p.parse_args()
    family = args.family
    root = ROOT/family
    authority = json.loads((ROOT/'authority.json').read_text())
    deadline = datetime.fromisoformat(authority['deadline_UTC']).timestamp()
    def available():
        remaining = deadline-time.time()
        if remaining <= 0 or shutil.disk_usage('/root/autodl-tmp').free < 5*1024**3:
            raise RuntimeError('Approved deadline/disk stop; preserve all partial evidence')
        return min(3600, remaining)
    available()
    if family == 'qwen':
        prior = json.loads((ROOT/'uie'/'controller_final.json').read_text())
        assert prior['all_completed'] and len(prior['conditions']) == 4
        assert (ROOT/'uie_local_backup_verified.json').exists()
    for path, digest in json.loads((ROOT/'source_locks.json').read_text()).items():
        assert sha(Path(path)) == digest, path
    for path, digest in json.loads((ROOT/'original_disabled_config_hashes.json').read_text()).items():
        assert sha(Path(path)) == digest, path
    write(root/'controller_started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid()})
    env = dict(os.environ)
    for key in ('FLAGS_cudnn_dir', 'FLAGS_cuda_dir'):
        env.pop(key, None)
    if 'uie-base-round2' in env.get('LD_LIBRARY_PATH', ''):
        raise RuntimeError('UIE library paths must not enter controller/Qwen parent environment')
    server = runner = monitor = None
    status = {'family': family, 'conditions': {}, 'all_completed': False}
    started = time.monotonic()
    try:
        monitor_log = (root/'gpu_monitor.csv').open('x')
        monitor = subprocess.Popen(['bash', '-c', 'while true; do nvidia-smi --query-gpu=timestamp,memory.used,memory.free,utilization.gpu --format=csv,noheader; sleep 2; done'],
                                   stdout=monitor_log, stderr=subprocess.STDOUT, start_new_session=True)
        if family == 'qwen':
            command = [ENV+'/vllm', 'serve', '/root/autodl-tmp/models/qwen2.5-7b', '--host', '127.0.0.1',
                       '--port', '8000', '--dtype', 'bfloat16', '--max-model-len', '8192', '--gpu-memory-utilization', '0.9']
            log = (root/'vllm_bf16.log').open('x')
            server = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            write(root/'server_process.json', {'pid': server.pid, 'command': command, 'LD_LIBRARY_PATH': env.get('LD_LIBRARY_PATH')})
            ready = False
            for _ in range(150):
                available()
                if server.poll() is not None:
                    raise RuntimeError('Owned vLLM exited before health check')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2) as response:
                        ready = response.status == 200
                    if ready:
                        break
                except Exception:
                    time.sleep(2)
            if not ready:
                raise RuntimeError('Server startup exceeded5minutes')
        for condition in CONDITIONS[family]:
            timeout = available()
            if family == 'uie':
                command = ['bash', '/root/project/scripts/round2_uie_gpu_python.sh', '/root/project/scripts/run_round2_uie.py',
                           '--config', str(root/'configs'/(condition+'.json'))]
                audit = ['bash', '/root/project/scripts/round2_uie_gpu_python.sh', '/root/project/scripts/audit_round2_formal_uie_20261012.py']
            else:
                command = [ENV+'/python', '/root/project/scripts/run_round2_qwen.py', '--config', str(root/'configs'/(condition+'.yaml'))]
                audit = [ENV+'/python', '/root/project/scripts/audit_round2_formal_qwen_20261012.py']
            with (root/(condition+'.log')).open('x') as log:
                runner = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                write(root/(condition+'_process.json'), {'pid': runner.pid, 'command': command})
                code = runner.wait(timeout=timeout)
            runner = None
            if code:
                raise RuntimeError(f'{condition} exited{code}; next cell forbidden')
            with (root/(condition+'_audit.log')).open('x') as log:
                runner = subprocess.Popen(audit+['--condition', condition], stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
                code = runner.wait(timeout=available())
            runner = None
            if code:
                raise RuntimeError(f'{condition} independent audit failed; next cell forbidden')
            receipt = seal(root/condition, family, condition)
            status['conditions'][condition] = {'verified': True, 'backup': receipt}
            write(root/(condition+'_verified.json'), status['conditions'][condition])
        status['all_completed'] = True
    except Exception as exc:
        status['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        stop_owned(runner)
        stop_owned(server)
        stop_owned(monitor)
        status.update(ended_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started)
        write(root/'controller_final.json', status)
    if not status['all_completed']:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
