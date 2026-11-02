#!/usr/bin/env python3
"""UIE no-card preflight: tokenizer/offset/data checks only, no model instantiation."""
import hashlib
import importlib.metadata
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from equipment_ie.schema import iter_jsonl
from equipment_ie.uie_adapter import SCHEMA_MAP, character_windows, native_training_rows, native_to_global, resolve_predictions

STAGE = Path('/root/autodl-tmp/round2_uie_nocard_20261010')
MODEL = Path('/root/autodl-tmp/models/uie-base-round2-official')
EXPECTED = {'support': '9633c7f6ceee8592408034e26834233e3f03b2f58a104783757ae664a4bab22a',
            'dev': 'ade6eda3547349117b5fa212c6567bd76722bb1996844b0de4f2d5a01ffc0c6b'}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')


def write_rows(path, rows):
    with path.open('x', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')


def encode(tokenizer, prompt, text):
    return tokenizer(text=prompt, text_pair=text, truncation=False, return_offsets_mapping=True,
                     return_attention_mask=True, return_position_ids=True)


def feature_row(tokenizer, row):
    encoded = encode(tokenizer, row['prompt'], row['content'])
    ids, types, offsets = encoded['input_ids'], encoded['token_type_ids'], encoded['offset_mapping']
    if len(ids) > 512:
        raise ValueError('input exceeds512; silent truncation forbidden')
    start_labels, end_labels = [0]*512, [0]*512
    problems = []
    for entity in row['result_list']:
        s, e = entity['start'], entity['end']
        a = [i for i, (kind, offset) in enumerate(zip(types, offsets)) if kind == 1 and offset[0] <= s < offset[1]]
        b = [i for i, (kind, offset) in enumerate(zip(types, offsets)) if kind == 1 and offset[0] <= e-1 < offset[1]]
        if len(a) != 1 or len(b) != 1:
            problems.append({'entity': entity, 'reason': 'unmappable_offset'})
            continue
        if offsets[a[0]][0] != s or offsets[b[0]][1] != e:
            problems.append({'entity': entity, 'reason': 'gold_boundary_inside_token',
                             'token_boundary': [offsets[a[0]][0], offsets[b[0]][1]]})
        start_labels[a[0]] = 1
        end_labels[b[0]] = 1
    features = {k: encoded[k]+[0]*(512-len(ids)) for k in ['input_ids', 'token_type_ids', 'position_ids', 'attention_mask']}
    # Input pad ID is tokenizer-owned, never assume zero.
    features['input_ids'] = ids+[tokenizer.pad_token_id]*(512-len(ids))
    features.update(start_positions=start_labels, end_positions=end_labels,
                    source_id=row['source_id'], prompt=row['prompt'], input_length=len(ids))
    return features, problems


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*')), 'No-card required'
    destination = STAGE/'prepared_data'
    # Imports/tokenizer only. Never instantiate UIE or Taskflow.
    from paddlenlp.transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL))
    resource = json.loads((STAGE/'model_resource_manifest.json').read_text())
    assert all(sha(MODEL/name) == value['sha256'] for name, value in resource['files'].items())
    destination.mkdir(exist_ok=False)
    report = {'gate': 'ROUND2_UIE_NOCARD_PREFLIGHT_APPROVED_20261010', 'model_calls': 0,
              'model_instantiated': False, 'model_weight_deserialized': False,
              'frozen_test_labels_read': False, 'calibration_labels_read': False,
              'schema_mapping': SCHEMA_MAP, 'position_prob': 0.5, 'max_seq_len': 512,
              'window_max_chars': 400, 'window_overlap_chars': 64,
              'overlap_policy': 'highest native probability; length/start/end/type tie-break; audit every drop',
              'weight_resource_hash_verified': True, 'splits': {}, 'problems': [],
              'versions': {n: importlib.metadata.version(n) for n in ['paddlepaddle', 'paddlenlp', 'numpy', 'datasets', 'pyarrow']}}
    for split, count in [('support', 30), ('dev', 50)]:
        path = Path(f'/root/autodl-tmp/data/domain_{split}.jsonl')
        assert sha(path) == EXPECTED[split]
        records = list(iter_jsonl(path))
        assert len(records) == count
        native, features, query_windows, problems = [], [], [], []
        partial_skips = 0
        max_length = 0
        for record in records:
            assert all(e['type'] in SCHEMA_MAP.values() for e in record['entities'])
            windows = character_windows(record['text'], lambda text: all(len(encode(tokenizer, p, text)['input_ids']) <= 512 for p in SCHEMA_MAP))
            query_windows.append({'id': record['id'], 'windows': windows})
            nrows, missing, skipped = native_training_rows(record, windows)
            partial_skips += len(skipped)
            if missing:
                problems.append({'id': record['id'], 'reason': 'gold_not_fully_covered_by_text_only_windows', 'entities': missing})
            for row in nrows:
                feature, issues = feature_row(tokenizer, row)
                features.append(feature)
                max_length = max(max_length, feature['input_length'])
                problems.extend({'id': record['id'], 'prompt': row['prompt'], **issue} for issue in issues)
            # A synthetic perfect-native-output roundtrip checks adapter wiring,
            # not model accuracy. Use frozen support/dev only, never test gold.
            simulated = []
            for w in windows:
                result = {p: [{'start': e['start']-w['start'], 'end': e['end']-w['start'],
                                'text': e['span'], 'probability': .9} for e in record['entities']
                               if e['type'] == t and w['start'] <= e['start'] < e['end'] <= w['end']]
                          for p, t in SCHEMA_MAP.items()}
                converted, invalid = native_to_global(record['text'], w, result)
                assert not invalid
                simulated.extend(converted)
            roundtrip, _ = resolve_predictions(simulated)
            assert {(e['start'],e['end'],e['type']) for e in roundtrip} == {(e['start'],e['end'],e['type']) for e in record['entities']}
            native.extend(nrows)
        write_rows(destination/f'{split}_native.jsonl', native)
        write_rows(destination/f'{split}_features512.jsonl', features)
        write_rows(destination/f'{split}_query_windows.jsonl', query_windows)
        report['splits'][split] = {'source_rows': len(records), 'source_sha256': sha(path),
                                   'source_entities': sum(len(r['entities']) for r in records),
                                   'source_entities_per_type': dict(Counter(e['type'] for r in records for e in r['entities'])),
                                   'native_schema_window_rows': len(native), 'negative_rows': sum(not r['result_list'] for r in native),
                                   'windows': sum(len(r['windows']) for r in query_windows), 'partial_label_schema_windows_skipped': partial_skips,
                                   'max_input_tokens': max_length, 'gold_adapter_roundtrip': 'PASS_NOT_MODEL_RESULT',
                                   'token_offset_problems': len(problems)}
        report['problems'].extend({'split': split, **p} for p in problems)
    # Configs remain gated. A later runner/pilot must separately check training and CUDA.
    configs = STAGE/'configs_not_authorized'
    configs.mkdir(exist_ok=False)
    for seed in [None, 42, 43, 44]:
        name = 'uie_base_zero_shot' if seed is None else f'uie_base_ft30_s{seed}'
        config = {'run_id': name, 'execution': {'authorized': False, 'model_calls_allowed': False, 'human_gate': 'NOT_GRANTED'},
                  'model_path': str(MODEL), 'schema_mapping': SCHEMA_MAP,
                  'window_max_chars': 400, 'window_overlap_chars': 64, 'max_seq_len': 512, 'position_prob': 0.5,
                  'train_native_path': None if seed is None else str(destination/'support_native.jsonl'),
                  'dev_native_path': str(destination/'dev_native.jsonl'),
                  'checkpoint_selection': None if seed is None else 'dev_original_text_entity_micro_f1_after_window_merge',
                  'test_path': '/root/autodl-tmp/data/domain_test.jsonl', 'test_tuning': False,
                  'seed': seed, 'training': None if seed is None else {'batch_size': 8, 'optimizer': 'AdamW',
                    'learning_rate': 1e-5, 'weight_decay': 0, 'max_epochs': 20, 'early_stop_patience': 3,
                    'checkpoint_tie_rule': 'earliest', 'checkpoint_storage': 'only_best_weights_keep_all_epoch_predictions_and_hashes',
                    'workers': 0, 'precision': 'fp32'},
                  'overlap_policy': report['overlap_policy'], 'status': 'OFFLINE_READY_GPU_PILOT_NOT_EXECUTED',
                  'phase': 'formal', 'mode': 'zero_shot' if seed is None else 'finetune',
                  'query_path': '/root/autodl-tmp/data/domain_test.jsonl',
                  'train_features_path': None if seed is None else str(destination/'support_features512.jsonl'),
                  'time_limit_seconds': 3600,
                  'output_dir': str(STAGE/'future_runs'/name),
                  'input_sha256': {str(MODEL/k): v['sha256'] for k, v in resource['files'].items()}}
        for s in ['support', 'dev']:
            path = Path(f'/root/autodl-tmp/data/domain_{s}.jsonl')
            config['input_sha256'][str(path)] = EXPECTED[s]
        config['input_sha256']['/root/autodl-tmp/data/domain_test.jsonl'] = '42f6ecbbfd1eb57937cd74a04e5b8362fe0976b5bf108e52523a4778dd53bfd0'
        if seed is not None:
            config['input_sha256'][str(destination/'support_features512.jsonl')] = sha(destination/'support_features512.jsonl')
        save(configs/(name+'.json'), config)
        if seed in [None, 42]:
            import copy
            pilot = copy.deepcopy(config)
            pilot.update(phase='dev_pilot', query_path='/root/autodl-tmp/data/domain_dev.jsonl', query_limit=20,
                         time_limit_seconds=1200, output_dir=str(STAGE/'future_pilot'/name))
            pilot['input_sha256'].pop('/root/autodl-tmp/data/domain_test.jsonl')
            if seed == 42:
                pilot.update(mode='learning_sanity', sanity_steps=30)
            save(configs/(name+'_dev_pilot.json'), pilot)
    before, after = STAGE/'qwen_environment_before.txt', STAGE/'qwen_environment_after.txt'
    report['qwen_environment_unchanged'] = sha(before) == sha(after)
    report['verdict'] = 'PASS_OFFLINE_ONLY' if not report['problems'] and report['qwen_environment_unchanged'] else 'BLOCKED_OFFLINE_ISSUES'
    report['not_validated'] = ['model loading/forward', 'native start/end decoder on real output', 'gradient/overfit learning sanity',
                               'GPU Paddle/CUDA/cuDNN compatibility', 'formal test inference']
    save(STAGE/'uie_preflight_report.json', report)
    save(STAGE/'prepared_artifacts_sha256.json', {str(p.relative_to(STAGE)): sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file() and p.name != 'prepared_artifacts_sha256.json'})
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
