"""Bounded Qwen BF16 dev pilot controller; run only on approved AutoDL instance."""
import argparse
import json
import os
import signal
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENV = '/root/autodl-tmp/venvs/equipment-ie/bin'
CONDITIONS = ('random5_s42', 'knn5', 'knn5_glossary')


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)


def stop_owned(process):
    if process is None or process.poll() is not None:
        return
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if root != Path('/root/autodl-tmp/round2_runtime_bundle_20261010_r3/future_runs/dev_pilot_20261012_r1'):
        raise RuntimeError('Only this new approved dev directory is allowed')
    started = time.monotonic()
    write(root/'controller_started.json', {'utc': datetime.now(timezone.utc).isoformat(), 'pid': os.getpid()})
    env = dict(os.environ)
    for key in ('FLAGS_cudnn_dir', 'FLAGS_cuda_dir'):
        env.pop(key, None)
    if 'uie-base-round2' in env.get('LD_LIBRARY_PATH', ''):
        raise RuntimeError('Qwen cannot inherit UIE library paths')
    server = runner = monitor = None
    status = {'conditions': {}, 'all_completed': False}
    try:
        monitor_log = (root/'gpu_monitor.csv').open('x')
        monitor = subprocess.Popen(['bash', '-c', 'while true; do nvidia-smi --query-gpu=timestamp,memory.used,memory.free,utilization.gpu --format=csv,noheader; sleep 2; done'],
                                   stdout=monitor_log, stderr=subprocess.STDOUT, start_new_session=True)
        command = [ENV+'/vllm', 'serve', '/root/autodl-tmp/models/qwen2.5-7b',
                   '--host', '127.0.0.1', '--port', '8000', '--dtype', 'bfloat16',
                   '--max-model-len', '8192', '--gpu-memory-utilization', '0.9']
        server_log = (root/'vllm_bf16.log').open('x')
        server = subprocess.Popen(command, stdout=server_log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        write(root/'server_process.json', {'pid': server.pid, 'pgid': server.pid, 'command': command,
                                          'uiE_flags_removed': True, 'LD_LIBRARY_PATH': env.get('LD_LIBRARY_PATH')})
        ready = False
        for _ in range(150):
            if server.poll() is not None:
                raise RuntimeError('Owned vLLM server exited before health check')
            try:
                with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2) as response:
                    ready = response.status == 200
                if ready:
                    break
            except Exception:
                time.sleep(2)
        if not ready:
            raise RuntimeError('vLLM startup exceeded5minutes; no extraction request sent')
        write(root/'server_ready.json', {'utc': datetime.now(timezone.utc).isoformat(), 'model_calls': 0})
        for condition in CONDITIONS:
            if time.monotonic()-started >= 5400:
                raise RuntimeError('90minute bounded window exhausted')
            config = root/'configs'/f'{condition}.yaml'
            log = (root/f'{condition}.log').open('x')
            command = [ENV+'/python', '/root/project/scripts/run_round2_qwen.py', '--config', str(config)]
            runner = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            write(root/f'{condition}_process.json', {'pid': runner.pid, 'command': command})
            code = runner.wait(timeout=min(1200, max(1, 5400-(time.monotonic()-started))))
            log.close()
            runner = None
            status['conditions'][condition] = {'exit_code': code}
            if code:
                raise RuntimeError(f'{condition} exited{code}; do not launch next condition')
            summary = json.loads((root/condition/'summary.json').read_text())
            rows = [json.loads(line) for line in (root/condition/'per_query.jsonl').read_text().splitlines()]
            requests = sum(len(row['attempts']) for row in rows)
            entities = sum(len(row['pred_raw']['entities']) for row in rows)
            if len(rows) != 20 or requests > 40 or summary['parse_failures'] > 1 or entities == 0:
                raise RuntimeError(f'{condition} failed dev20 parser/nondegenerate/request bound')
            for row in rows:
                for entity in row['pred_raw']['entities']:
                    if row['gold']['text'][entity['start']:entity['end']] != entity['span']:
                        raise RuntimeError('Accepted entity slicing failed')
                    if entity['type'] not in {'EQUIPMENT', 'MODULE', 'TECH_SCHEME', 'METRIC'}:
                        raise RuntimeError('Accepted entity schema failed')
            status['conditions'][condition].update(requests=requests, predicted_entities=entities,
                                                  parse_failures=summary['parse_failures'], entity_micro=summary['entity_micro'])
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
