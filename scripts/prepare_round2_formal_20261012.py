"""Materialize approved execution copies; hashes only, no model imports."""
import hashlib
import json
import subprocess
from pathlib import Path
import yaml

ROOT = Path('/root/autodl-tmp/round2_formal_20261012_r3')
UIE = ('uie_base_zero_shot', 'uie_base_ft30_s42', 'uie_base_ft30_s43', 'uie_base_ft30_s44')
QWEN = ('random5_s42', 'random5_s43', 'random5_s44', 'knn5', 'knn5_glossary')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    ROOT.mkdir(exist_ok=False)
    sources = ['scripts/run_round2_uie.py', 'scripts/round2_uie_gpu_python.sh',
               'src/equipment_ie/uie_runtime.py', 'src/equipment_ie/uie_cuda_guard.py',
               'src/equipment_ie/uie_adapter.py', 'scripts/run_round2_qwen.py',
               'scripts/run_p3_extraction.py', 'src/equipment_ie/extraction.py',
               'src/equipment_ie/llm_labeling.py', 'src/equipment_ie/schema.py',
               'scripts/audit_round2_uie_dev_pilot_v2_20261012.py',
               'scripts/audit_round2_formal_uie_20261012.py',
               'scripts/audit_round2_formal_qwen_20261012.py',
               'scripts/run_round2_formal_20261012.py']
    locks = {str(Path('/root/project')/s): sha(Path('/root/project')/s) for s in sources}
    source_dir = ROOT/'source_snapshot'
    source_dir.mkdir()
    for s in sources:
        target = source_dir/s
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((Path('/root/project')/s).read_bytes())
    originals = {}
    for family, conditions in [('uie', UIE), ('qwen', QWEN)]:
        family_root = ROOT/family
        (family_root/'configs').mkdir(parents=True)
        for name in conditions:
            if family == 'uie':
                original = Path('/root/autodl-tmp/round2_uie_nocard_20261010/runtime_configs_not_authorized')/(name+'.json')
                cfg = json.loads(original.read_text())
                cfg['execution'] = {'authorized': True, 'model_calls_allowed': True,
                                    'human_gate': 'ROUND2_UIE_FORMAL_APPROVED_20261010'}
                cfg['run_id'] = 'round2_formal_20261012_r3_'+name
                cfg['output_dir'] = str(family_root/name)
                cfg['status'] = 'HUMAN_APPROVED_FORMAL_EXECUTION_COPY'
                cfg['input_sha256'].update(locks)
                path = family_root/'configs'/(name+'.json')
                save(path, cfg)
                cmd = ['/root/autodl-tmp/venvs/equipment-ie/bin/python', '/root/project/scripts/run_round2_uie.py']
            else:
                original = Path('/root/autodl-tmp/round2_runtime_bundle_20261010_r3/qwen_configs_not_authorized')/(name+'_formal.yaml')
                cfg = yaml.safe_load(original.read_text())
                cfg['execution'].update(authorized=True, model_calls_allowed=True,
                                        human_gate='ROUND2_QWEN_FORMAL_APPROVED_20261010')
                cfg['run_id'] = 'round2_formal_20261012_r3_'+name
                out = family_root/name
                cfg['outputs'] = {k: str(out/Path(v).name) for k,v in cfg['outputs'].items()}
                cfg['cache']['dir'] = str(out/'cache')
                cfg['round2_input_sha256'].update(locks)
                path = family_root/'configs'/(name+'.yaml')
                with path.open('x') as f:
                    yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
                cmd = ['/root/autodl-tmp/venvs/equipment-ie/bin/python', '/root/project/scripts/run_round2_qwen.py']
            originals[str(original)] = sha(original)
            subprocess.run(cmd+['--config', str(path), '--dry-run'], check=True)
    save(ROOT/'source_locks.json', locks)
    save(ROOT/'original_disabled_config_hashes.json', originals)
    save(ROOT/'authority.json', {'gate': 'ROUND2_FORMAL_NINE_CELLS_APPROVED_20261012',
        'human_continue': '保持有卡，继续工作 / 继续', 'checkpoint_local_backup': True,
        'price_CNY_hour': 2.8, 'budget_CNY': 20,
        'deadline_UTC': '2026-10-12T06:15:00+00:00', 'conditions': {'uie': UIE, 'qwen': QWEN},
        'model_calls_during_preparation': 0})
    print('Nine fresh locked execution configurations passed dry validation; no models.')


if __name__ == '__main__':
    main()
