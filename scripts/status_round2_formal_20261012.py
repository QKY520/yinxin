"""Read-only bounded status snapshot; no experiment imports or model/API calls."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/root/autodl-tmp/round2_formal_20261012_r3')
status = {'utc': datetime.now(timezone.utc).isoformat(), 'cells': {}, 'verified': 0}
for family, conditions in {'uie': ('uie_base_zero_shot', 'uie_base_ft30_s42', 'uie_base_ft30_s43', 'uie_base_ft30_s44'),
                           'qwen': ('random5_s42', 'random5_s43', 'random5_s44', 'knn5', 'knn5_glossary')}.items():
    for condition in conditions:
        directory = ROOT/family/condition
        audit = directory/'independent_validation.json'
        cache = directory/'cache'
        item = {'cache_responses': len(list(cache.glob('*/*.json'))) if cache.exists() else 0,
                'independently_verified': audit.exists()}
        if audit.exists():
            report = json.loads(audit.read_text())
            assert report['status'] == 'FORMAL_CELL_VERIFIED'
            metric = report['test170'] if family == 'uie' else report['result']['entity_micro']
            item.update({k: metric[k] for k in ('tp', 'fp', 'fn', 'f1')})
            status['verified'] += 1
        status['cells'][condition] = item
    final = ROOT/family/'controller_final_v2.json'
    if final.exists():
        controller = json.loads(final.read_text())
        status[family+'_controller'] = {k: controller[k] for k in ('all_completed', 'error', 'elapsed_seconds') if k in controller}
status['gpu'] = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu', '--format=csv,noheader'], text=True).strip()
print(json.dumps(status, ensure_ascii=False), flush=True)
