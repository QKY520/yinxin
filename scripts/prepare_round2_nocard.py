#!/usr/bin/env python3
"""Round-two no-card audit and blind calibration preparation; AutoDL only.

No model API, inference, gold repair or old-output mutation. New outputs are
exclusive-create. Calibration selection uses text/source metadata, not labels.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import yaml

DATA = Path('/root/autodl-tmp/data')
FORMAL = Path('/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917')
EXPECTED = {
    'domain_candidates': '32622228a7e0d45b31ce7ee2c0f78bcad0a5aa4a07ad8d01212bd03d3c19ee4f',
    'domain_support': '9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a',
    'domain_dev': 'ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b',
    'domain_test': '42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0',
}
SEED = 2026101001
GUIDELINE = Path('/root/project/docs/P6_QA1R_ANNOTATION_GUIDELINE_V4_LOCKED_20260727.md')
GUIDELINE_HASH = 'a15289cd0f45bc23a0ce9d981db24745b814cfb94c6b03687e60a13b81b6ca80'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable(seed, value):
    return hashlib.sha256(f'{seed}:{value}'.encode()).hexdigest()


def read_rows(path):
    rows = [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s]
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError(f'duplicate IDs: {path}')
    return rows


def write_json(path, obj):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def write_rows(path, rows):
    with Path(path).open('x', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def grams(text):
    compact = re.sub(r'\s+', '', text.lower())
    return {compact[i:i+8] for i in range(len(compact)-7)}


def containment(left, right):
    return len(left & right) / min(len(left), len(right)) if left and right else 0.0


def historical_reasons(row):
    reasons = []
    if row['source_type'] == 'patent' and row['source_split'] == 'test':
        reasons.append('excluded_source_split:patent:test')
    if re.search(r'\d{6,}', row['text']):
        reasons.append('consecutive_digits_ge6')
    return reasons


def strata(row):
    length = len(row['text'])
    return f"{row['source_type']}:{'short' if length <= 150 else 'medium' if length <= 300 else 'long'}"


def proportional_sample(rows, n, seed):
    if len(rows) < n:
        raise ValueError(f'only {len(rows)} eligible, need {n}')
    groups = defaultdict(list)
    for row in rows:
        groups[strata(row)].append(row)
    quotas = {key: math.floor(n * len(value) / len(rows)) for key, value in groups.items()}
    ranked = sorted(groups, key=lambda key: (-(n*len(groups[key])/len(rows)-quotas[key]), key))
    for key in ranked[:n-sum(quotas.values())]:
        quotas[key] += 1
    selected = []
    for key in sorted(groups):
        selected += sorted(groups[key], key=lambda r: (stable(seed, r['id']), r['id']))[:quotas[key]]
    return selected, quotas


def build_sheet(selected, role, output):
    ordered = sorted(selected, key=lambda r: stable(f'{SEED}:{role}', r['id']))
    mapping = {}
    output.mkdir()
    fields = ['blind_id', 'text', 'entities_json', 'review_codes', 'notes']
    with (output / f'annotator_{role.lower()}_100_blank.csv').open('x', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(ordered, 1):
            bid = f'R2-{role}-{i:03d}'
            writer.writerow(dict(zip(fields, [bid, row['text'], '', '', ''])))
            mapping[row['id']] = bid
    shutil.copyfile(GUIDELINE, output / GUIDELINE.name)
    instructions = f'''# 标注者{role}：第二轮100条独立非测试复核

仅接收本目录，不接收另一标注者目录或coordinator_only。
阅读随附v4指南；本次使用其中NER类型、边界、重复mention及疑点规则。
其中2026-07的旧门禁及0.85目标是历史记录，本批次不以分数为验收门槛，
不因agreement偏低删样本、补样本或反复换批次；不修改旧gold。

逐行在entities_json填JSON数组，无实体填[]；未完成保持空白。
实体字段：start、end、type、span。位置从0开始，end不包含，按Unicode字符而非字节计数。
text、blind_id不得改；每次合格出现分别标。可填review_codes和notes。
不得查看旧标签、模型建议、另一人的答案；不得先讨论本批文本再提交。
保持本目录原始空白表，另存annotator_{role.lower()}_100_firstpass.csv。
你可使用自己的编辑工具定位字符，但不能让AI代标。
完成后先交协调员做本表结构检查，错误只由本人修正；锁定首轮文件和哈希，
两人都提交后先算独立agreement，再另存讨论/裁决文件。
本批不是训练集、检索证据或正式测试重标；勿将其加入原实验资源。
'''
    (output / 'README_先读.md').write_text(instructions, encoding='utf-8')
    # Ensure no prelabels, original IDs or source metadata leaked to CSV.
    with (output / f'annotator_{role.lower()}_100_blank.csv').open(encoding='utf-8-sig', newline='') as f:
        exported = list(csv.DictReader(f))
    assert len(exported) == 100 and all(not r['entities_json'] for r in exported)
    assert all(set(r) == set(fields) for r in exported)
    return mapping


def prepare_configs(output, support, full_rows):
    directory = output / 'configs_not_authorized'
    directory.mkdir()
    base = yaml.safe_load((FORMAL/'ec_fsie_full.yaml').read_text())
    for system in ['random5_s42', 'random5_s43', 'random5_s44', 'knn5', 'knn5_glossary']:
        cfg = copy.deepcopy(base)
        cfg['run_id'] = f'round2-{system}-formal-prep'
        cfg['config_name'] = cfg['run_id']
        cfg['execution'] = {'authorized': False, 'model_calls_allowed': False,
                            'phase': 'ROUND2_FORMAL_PENDING_PILOT', 'human_gate': 'NOT_GRANTED'}
        cfg.pop('rag', None)
        if system != 'knn5_glossary':
            cfg.pop('glossary', None)
        if system.startswith('random'):
            seed = int(system[-2:])
            cfg['examples'] = {'mode': 'fixed_random', 'k': 5, 'seed': seed}
        else:
            # Replay the actual Full choices, not merely an upstream nominal B file.
            cfg['examples']['source_per_query_path'] = str(output/'full_example_replay.jsonl')
        cfg['generation']['seed'] = 42
        cfg['protocol']['system'] = system
        cfg['protocol']['run_order'] = ['random5_s42', 'random5_s43', 'random5_s44', 'knn5', 'knn5_glossary']
        target = output/'formal_pending'/system
        cfg['cache']['dir'] = str(target/'cache')
        cfg['outputs'] = {key: str(target/(key+'.jsonl' if key in ['per_query', 'dry_run_prompts'] else key+'.json'))
                          for key in cfg['outputs']}
        with (directory/(system+'.yaml')).open('x', encoding='utf-8') as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
    write_rows(output/'full_example_replay.jsonl', [{'id': r['id'], 'example_ids': r['example_ids']} for r in full_rows])
    # Descriptors, not dispatchable configs: native-offset adapter/environment still need tests.
    for seed in [None, 42, 43, 44]:
        system = 'uie_base_zero_shot' if seed is None else f'uie_base_ft30_s{seed}'
        cfg = {'system': system, 'execution': {'authorized': False, 'model_calls_allowed': False, 'human_gate': 'NOT_GRANTED'},
               'implementation_status': 'DESCRIPTOR_ONLY_ADAPTER_AND_ENVIRONMENT_PENDING',
               'model': 'uie-base', 'framework': 'PaddleNLP', 'isolated_environment_required': True,
               'schema_mapping': {'装备': 'EQUIPMENT', '部件模块': 'MODULE', '技术方案': 'TECH_SCHEME', '性能指标': 'METRIC'},
               'position_prob': 0.5, 'max_seq_len': 512, 'native_offsets_required': True,
               'data': {'support': str(DATA/'domain_support.jsonl'), 'dev': str(DATA/'domain_dev.jsonl'),
                        'test': str(DATA/'domain_test.jsonl')},
               'training': None if seed is None else {'seed': seed, 'batch_size': 8, 'learning_rate': 1e-5,
                           'max_epochs': 20, 'early_stopping_patience': 3, 'selection': 'dev_entity_micro_f1'},
               'test_tuning_allowed': False, 'silent_truncation_allowed': False}
        with (directory/(system+'.yaml')).open('x', encoding='utf-8') as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('/root/autodl-tmp/round2_nocard_preparation_20261010'))
    args = parser.parse_args()
    if list(Path('/dev').glob('nvidia[0-9]*')):
        raise RuntimeError('GPU devices exposed; preparation requires no-card mode')
    paths = {key: DATA/(key+'.jsonl') for key in EXPECTED}
    for key, path in paths.items():
        if digest(path) != EXPECTED[key]:
            raise ValueError(f'frozen input SHA mismatch: {key}')
    if digest(GUIDELINE) != GUIDELINE_HASH:
        raise ValueError('locked guideline SHA mismatch')
    candidates = read_rows(paths['domain_candidates'])
    splits = {key: read_rows(paths[key]) for key in ['domain_support', 'domain_dev', 'domain_test']}
    assert [len(candidates), *(len(splits[k]) for k in splits)] == [400, 30, 50, 170]
    old = json.loads(Path('/root/autodl-tmp/backup/p2/p2_llm_label_250_v1_dry_run.json').read_text())
    historical_kept = [r for r in candidates if not historical_reasons(r)]
    historical_selected = historical_kept[:250]
    assert [r['id'] for r in historical_selected] == old['selection']['record_ids']
    selected_ids = {r['id'] for r in historical_selected}
    blocked = [r for rows in splits.values() for r in rows]
    assert {r['id'] for r in blocked} == selected_ids, '250 selection/split membership mismatch'
    blocked_grams = [(r['id'], grams(r['text'])) for r in blocked]
    ledger, eligible, accepted_grams = [], [], []
    for row in candidates:
        hits = historical_reasons(row)
        hreason = hits[0] if hits else ('selected_first250' if row['id'] in selected_ids else 'eligible_beyond250')
        reason, nearest, score = None, None, 0.0
        if row['id'] in selected_ids:
            reason = 'prior_annotation_or_frozen_split'
        elif hits:
            reason = 'historical_quality_or_source_exclusion'
        elif not row['text'].strip() or '\ufffd' in row['text'] or any(ord(c) < 32 and c not in '\n\r\t' for c in row['text']):
            reason = 'damaged_text'
        else:
            g = grams(row['text'])
            matches = [(containment(g, bg), bid) for bid, bg in blocked_grams+accepted_grams]
            score, nearest = max(matches, default=(0.0, None))
            if any(row['text'] == b['text'] for b in blocked+eligible):
                reason = 'exact_duplicate'
            elif score >= 0.8:
                reason = '8gram_near_duplicate'
            else:
                eligible.append(row)
                accepted_grams.append((row['id'], g))
        ledger.append({'id': row['id'], 'source_type': row['source_type'], 'source_split': row['source_split'],
                       'historical_all_rule_hits': hits, 'historical_primary_reason': hreason,
                       'calibration_exclusion': reason, 'nearest_compared_id': nearest, 'max_8gram_containment': score,
                       'text_sha256': hashlib.sha256(row['text'].encode()).hexdigest()})
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    write_rows(output/'candidate_400_audit.jsonl', ledger)
    report = {'mode': 'no_card_preparation', 'model_calls': 0, 'test_tuning': False, 'input_sha256': EXPECTED,
              'historical_selection_exactly_reproduced': True,
              'historical_reasons': dict(Counter(r['historical_primary_reason'] for r in ledger)),
              'selected250_source_counts': dict(Counter(r['source_type'] for r in historical_selected)),
              'calibration_exclusions': dict(Counter(r['calibration_exclusion'] or 'eligible' for r in ledger)),
              'eligible_calibration_count': len(eligible), 'calibration_target': 100,
              'calibration_eligible_sources': dict(Counter(r['source_type'] for r in eligible)),
              'gpu_devices_exposed': False, 'calibration_labels_read_or_exported': False,
              'rules': {'sampling_seed': SEED, 'length_strata': [150, 300], 'ngram': 8, 'containment_threshold': 0.8,
                        'sampling': 'source_length_proportional_largest_remainder_sha256_ranking'},
              'formal_execution_authorized': False, 'full_reuse_final_verdict': 'PENDING_CODE_AND_REQUEST_AUDIT'}
    full_path = FORMAL/'formal/ec_fsie_full/per_query.jsonl'
    full_rows = read_rows(full_path)
    assert [r['id'] for r in full_rows] == [r['id'] for r in splits['domain_test']]
    support_ids = {r['id'] for r in splits['domain_support']}
    assert all(len(r['example_ids']) == 5 and len(set(r['example_ids'])) == 5 and set(r['example_ids']) <= support_ids for r in full_rows)
    assert all(r['gold']['text'] == q['text'] and r['gold']['entities'] == q['entities'] for r, q in zip(full_rows, splits['domain_test']))
    report['full_per_query_sha256'] = digest(full_path)
    report['full_query_gold_and_support_example_membership_verified'] = True
    report['old_configs_and_outputs_inventory'] = {}
    for system in ['zero_shot', 'bm25_only', 'rag_only', 'ec_fsie_full']:
        files = [FORMAL/(system+'.yaml'), FORMAL/'formal'/system/'per_query.jsonl', FORMAL/'formal'/system/'summary.json']
        report['old_configs_and_outputs_inventory'][system] = {str(p): digest(p) for p in files}
    prepare_configs(output, splits['domain_support'], full_rows)
    if len(eligible) >= 100:
        selected, quotas = proportional_sample(eligible, 100, SEED)
        package = output/'calibration100'
        package.mkdir()
        coordinator = package/'coordinator_only'
        coordinator.mkdir()
        a = build_sheet(selected, 'A', package/'annotator_a_delivery')
        b = build_sheet(selected, 'B', package/'annotator_b_delivery')
        corpus = read_rows(DATA/'domain_rag_corpus.jsonl')
        corpus_ids = {r['id'] for r in corpus}
        write_rows(coordinator/'coordinator_map.jsonl', [
            {'id': r['id'], 'a_blind_id': a[r['id']], 'b_blind_id': b[r['id']], 'text': r['text'],
             'text_sha256': hashlib.sha256(r['text'].encode()).hexdigest(), 'source_type': r['source_type'],
             'source_id': r.get('source_id'), 'source_url': r.get('source_url'), 'source_license': r.get('source_license'),
             'stratum': strata(r), 'prior_unlabeled_rag_corpus_member': r['id'] in corpus_ids} for r in selected])
        report.update({'calibration_package_status': 'PREPARED_BLANK_NOT_ANNOTATED', 'sample_strata': quotas,
                       'sample_prior_unlabeled_rag_members': sum(r['id'] in corpus_ids for r in selected),
                       'guideline_sha256': GUIDELINE_HASH})
    else:
        report['calibration_package_status'] = 'BLOCKED_INSUFFICIENT_NEW_TEXTS_NO_SILENT_EXPANSION'
    write_json(output/'preparation_report.json', report)
    files = {str(p.relative_to(output)): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    write_json(output/'artifact_sha256_manifest.json', files)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
