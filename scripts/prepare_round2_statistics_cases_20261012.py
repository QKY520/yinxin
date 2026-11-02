"""No-card preparation: seal fourteen compatible prediction inputs and protocol."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import yaml

sys.path.insert(0, '/root/project/src')
from equipment_ie.schema import validate_record

ROOT = Path('/root/autodl-tmp/round2_statistics_cases_20261012_r1')
FORMAL = Path('/root/autodl-tmp/round2_formal_20261012_r3')
OLD = Path('/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def save(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    ROOT.mkdir(exist_ok=False)
    audit = read('/root/autodl-tmp/round2_runtime_bundle_20261010_r3/qwen_reuse_audit.json')
    inputs, locks = {}, {}
    old_names = {'zero': 'zero_shot', 'bm25': 'bm25_only', 'dense': 'rag_only', 'full': 'ec_fsie_full'}
    for name, original in old_names.items():
        cfg_path = OLD/(original+'.yaml')
        cfg = yaml.safe_load(cfg_path.read_text())
        assert sha(cfg_path) == audit['systems'][original]['config_sha256']
        inputs[name] = cfg['outputs']['per_query']
        assert sha(inputs[name]) == audit['systems'][original]['per_query_sha256']
        locks[str(cfg_path)] = sha(cfg_path)
    glossary = Path('/root/autodl-tmp/reviewer_qwen_glossary_only_formal_20260918')
    cfg_path = Path('/root/project')/read(glossary/'manifest.json')['config_path']
    assert sha(cfg_path) == audit['systems']['glossary_only']['config_sha256']
    inputs['glossary'] = str(glossary/'per_query.jsonl')
    assert sha(inputs['glossary']) == audit['systems']['glossary_only']['per_query_sha256']
    locks[str(cfg_path)] = sha(cfg_path)
    new_names = {'random42': ('qwen', 'random5_s42'), 'random43': ('qwen', 'random5_s43'),
                 'random44': ('qwen', 'random5_s44'), 'knn': ('qwen', 'knn5'),
                 'knn_g': ('qwen', 'knn5_glossary'), 'uie_zs': ('uie', 'uie_base_zero_shot'),
                 'uie_ft42': ('uie', 'uie_base_ft30_s42'), 'uie_ft43': ('uie', 'uie_base_ft30_s43'),
                 'uie_ft44': ('uie', 'uie_base_ft30_s44')}
    for name, (family, condition) in new_names.items():
        out = FORMAL/family/condition
        assert read(out/'independent_validation.json')['status'] == 'FORMAL_CELL_VERIFIED'
        rel = ('evaluation/' if family == 'uie' else '')+'per_query.jsonl'
        inputs[name] = str(out/rel)
        assert sha(out/rel) == read(out/'SHA256_manifest.json')[rel]
        cfg_path = FORMAL/family/'configs'/(condition+('.json' if family == 'uie' else '.yaml'))
        locks[str(cfg_path)] = sha(cfg_path)
    gold = rows('/root/autodl-tmp/data/domain_test.jsonl')
    assert len(gold) == 170 and sum(len(r['entities']) for r in gold) == 954
    ids = [r['id'] for r in gold]
    assert len(set(ids)) == 170
    integrity = {}
    for name, path in inputs.items():
        data = rows(path)
        assert len(data) == 170 and [r['id'] for r in data] == ids
        assert [r['gold'] for r in data] == gold
        for row in data:
            assert row['pred_raw']['id'] == row['id'] and row['pred_raw']['text'] == row['gold']['text']
            validate_record(row['pred_raw'])
            assert not row['pred_raw']['relations']
            assert all(e['type'] in {'EQUIPMENT', 'MODULE', 'TECH_SCHEME', 'METRIC'} for e in row['pred_raw']['entities'])
            if row['parse_failure']:
                assert not row['pred_raw']['entities']
        locks[path] = sha(path)
        integrity[name] = {'rows': 170, 'failures_preserved': sum(r['parse_failure'] for r in data), 'sha256': locks[path]}
    full, other = rows(inputs['full']), rows(inputs['knn_g'])
    for a, b in zip(full, other):
        assert a['example_ids'] == b['example_ids'] and a['glossary_terms'] == b['glossary_terms']
        assert not b['rag_passage_ids'] and len(a['rag_passage_ids']) == len(a['rag_passages'])
    for name in ('analyze_round2_comparisons.py', 'collect_round2_rag_cases.py',
                 'prepare_round2_statistics_cases_20261012.py', 'audit_round2_statistics_cases_20261012.py'):
        source = Path('/root/project/scripts')/name
        target = ROOT/'source_snapshot/scripts'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        locks[str(source)] = sha(source)
    protocol = FORMAL/'frozen_statistics_protocol.json'
    shutil.copy2(protocol, ROOT/'frozen_statistics_protocol.json')
    locks[str(protocol)] = sha(protocol)
    save(ROOT/'inputs.json', inputs)
    save(ROOT/'input_code_locks.json', locks)
    save(ROOT/'integrity_preflight.json', {'status': 'PASS', 'systems': integrity, 'paired_texts': 170,
        'gold_entities': 954, 'full_knn_g_examples_glossary_matched': 170, 'model_calls': 0,
        'gate': 'ROUND2_STATISTICS_CASES_APPROVED_20261012'})
    print(json.dumps({'preflight': 'PASS', 'systems': len(inputs), 'paired_texts': 170, 'model_calls': 0}))


if __name__ == '__main__':
    main()
