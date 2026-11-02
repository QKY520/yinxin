"""No-model closeout: verified nine cells, local receipts, costs and light seal."""
import csv
import hashlib
import json
import shutil
import socket
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/autodl-tmp/round2_formal_20261012_r3')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def main():
    authority = json.loads((ROOT/'authority.json').read_text())
    for filename in ('uie_local_backup_verified.json', 'qwen_local_backup_verified.json'):
        local = json.loads((ROOT/filename).read_text())
        assert all(r['verified'] for r in local['conditions'].values())
    for lock_file in ('source_locks.json', 'supplemental_source_locks_v2.json', 'original_disabled_config_hashes.json'):
        for path, digest in json.loads((ROOT/lock_file).read_text()).items():
            assert sha(Path(path)) == digest, path
    rows = []
    for family in ('uie', 'qwen'):
        controller = json.loads((ROOT/family/'controller_final_v2.json').read_text())
        assert controller['all_completed']
        for condition in authority['conditions'][family]:
            report = json.loads((ROOT/family/condition/'independent_validation.json').read_text())
            assert report['status'] == 'FORMAL_CELL_VERIFIED'
            if family == 'uie':
                metric = report['test170']
                training = report['training']
                row = {'condition': condition, 'framework': 'UIE', 'dtype': 'FP32',
                       'seed': None if training is None else training['seed'], 'example_selection_seed': None,
                       'selected_dev_epoch': None if training is None else training['selected_epoch'],
                       'epochs': None if training is None else training['epochs'],
                       'model_calls': report['model_calls'], 'request_attempts': None,
                       'parse_failures': 0, 'truncated_responses': 0}
            else:
                result = report['result']
                metric = result['entity_micro']
                row = {'condition': condition, 'framework': 'Qwen', 'dtype': 'BF16',
                       'seed': 42, 'example_selection_seed': int(condition[-2:]) if condition.startswith('random5_') else None,
                       'selected_dev_epoch': None, 'epochs': None,
                       'model_calls': result['attempts'], 'request_attempts': result['attempts'],
                       'parse_failures': result['parse_failures'],
                       'truncated_responses': result['length_truncation_responses']}
            row.update(queries=170, **{k: metric[k] for k in ('tp', 'fp', 'fn', 'precision', 'recall', 'f1')})
            rows.append(row)
    assert len(rows) == 9 and sum(r['request_attempts'] or 0 for r in rows) <= 1700
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True).strip()
    assert gpu == '0', 'Expected all owned model processes stopped and GPU idle'
    sock = socket.socket()
    sock.settimeout(2)
    assert sock.connect_ex(('127.0.0.1', 8000)) != 0, 'Model API port must be closed'
    sock.close()
    now = datetime.now(timezone.utc)
    started = datetime.fromisoformat('2026-10-12T02:12:07+00:00')
    elapsed = (now-started).total_seconds()
    report = {'status': 'NINE_FORMAL_CELLS_VERIFIED_AND_LOCALLY_BACKED_UP',
              'formal_cells_completed': 9, 'results': rows, 'new_model_calls_during_closeout': 0,
              'statistics_computed': False, 'paper_changed': False, 'push_performed': False,
              'gpu_memory_MiB': 0, 'port8000_closed': True,
              'data_disk_free_bytes': shutil.disk_usage('/root/autodl-tmp').free,
              'cost': {'price_CNY_hour': authority['price_CNY_hour'], 'budget_CNY': authority['budget_CNY'],
                       'observed_formal_phase_start_UTC': started.isoformat(), 'observed_end_UTC': now.isoformat(),
                       'observed_seconds': elapsed, 'rate_based_CNY_estimate': elapsed/3600*authority['price_CNY_hour'],
                       'actual_platform_bill_available': False, 'note': 'Estimate includes observed preparation/backup/idle; excludes earlier phases, boot and later idle. Platform bill authoritative.'},
              'next': 'Human may switch to no-card; separately confirm frozen13F1+3RAG statistical analysis. No manuscript/push/other experiment implied.'}
    for name in ('close_round2_formal_20261012.py', 'status_round2_formal_20261012.py', 'prepare_round2_formal_20261012.py'):
        source = Path('/root/project/scripts')/name
        target = ROOT/'source_snapshot/scripts'/name
        if not target.exists():
            shutil.copy2(source, target)
    save(ROOT/'formal_closeout.json', report)
    with (ROOT/'formal_metrics.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    backup = Path('/root/autodl-tmp/backup/round2/formal_20261012_r3')
    mirror = backup/'lightweight_complete'
    mirror.mkdir(exist_ok=False)
    # The three learned weight files are independently sealed in per-cell
    # archives and verified on Windows already. Avoid redundant weight copies.
    exclusions = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if path.name == 'model_state.pdparams' and path.parent.name == 'best_checkpoint':
            exclusions.append({'path': str(rel), 'bytes': path.stat().st_size, 'sha256': sha(path),
                               'backup': 'Previously verified per-cell Windows archive and extracted checkpoint'})
            continue
        target = mirror/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    for revision in ('r1', 'r2'):
        source = ROOT.parent/('round2_formal_20261012_'+revision)
        if source.exists():
            shutil.copytree(source, mirror/'preparation_history'/revision)
    save(mirror/'checkpoint_backup_exclusions.json', exclusions)
    files = {str(p.relative_to(mirror)): sha(p) for p in sorted(mirror.rglob('*')) if p.is_file()}
    save(mirror/'SHA256_manifest.json', files)
    archive = backup/'formal_lightweight_complete.tar.gz'
    with tarfile.open(archive, 'x:gz', compresslevel=1) as tar:
        tar.add(mirror, arcname='formal_lightweight_complete')
    receipt = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive),
               'manifest_sha256': sha(mirror/'SHA256_manifest.json'), 'files': len(files)}
    save(backup/'formal_lightweight_complete_receipt.json', receipt)
    print(json.dumps({'closeout': report, 'lightweight_backup': receipt}), flush=True)


if __name__ == '__main__':
    main()
