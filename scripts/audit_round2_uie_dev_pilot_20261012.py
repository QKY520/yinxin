"""Offline audit of the approved UIE dev pilot. Run only through AutoDL SSH."""
import argparse
import gzip
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, '/root/project/src')
from equipment_ie.uie_adapter import SCHEMA_MAP
from equipment_ie.uie_runtime import decode_native, encode_pair, merge_window_outputs
from equipment_ie.uie_cuda_guard import require_isolated_runtime
from paddlenlp.transformers import AutoTokenizer
from paddlenlp.utils.tools import get_span


def read_json(path):
    return json.loads(Path(path).read_text())


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def keys(record):
    return {(e['start'], e['end'], e['type']) for e in record['entities']}


def audit_predictions(directory, expected, tokenizer):
    directory = Path(directory)
    rows = read_rows(directory / 'per_query.jsonl')
    assert [r['id'] for r in rows] == [r['id'] for r in expected]
    raw_by_id = defaultdict(list)
    with gzip.open(directory / 'native_probabilities.jsonl.gz', 'rt', encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            encoded = encode_pair(tokenizer, item['prompt'], item['window']['text'])
            assert encoded['input_ids'] == item['input_ids']
            assert [list(v) for v in encoded['offset_mapping']] == item['offset_mapping']
            assert len(encoded['input_ids']) <= 512
            native, invalid = decode_native(item['window']['text'], encoded, item['start_probs'], item['end_probs'], get_span, .5)
            assert native == item['native'] and invalid == item['decoder_invalid']
            raw_by_id[item['id']].append(item)
    tp = fp = fn = predicted = invalid_count = drops = 0
    for row, original in zip(rows, expected):
        assert row['gold'] == original and row['parse_failure'] is False
        items = raw_by_id[row['id']]
        assert {item['prompt'] for item in items} == set(SCHEMA_MAP)
        entities, invalid, dropped = merge_window_outputs(original['text'], items)
        assert entities == row['pred_raw']['entities']
        assert invalid == row['native_invalid'] and dropped == row['overlap_and_duplicate_drops']
        assert row['pred_raw']['relations'] == []
        for e in entities:
            assert e['type'] in SCHEMA_MAP.values()
            assert original['text'][e['start']:e['end']] == e['span']
        gold, pred = keys(original), keys(row['pred_raw'])
        tp += len(gold & pred)
        fp += len(pred - gold)
        fn += len(gold - pred)
        predicted += len(entities)
        invalid_count += len(invalid)
        drops += len(dropped)
    summary = read_json(directory / 'summary.json')
    measured = {'queries': len(rows), 'tp': tp, 'fp': fp, 'fn': fn,
                'predicted_entities': predicted, 'precision': tp/(tp+fp) if tp+fp else 0.,
                'recall': tp/(tp+fn) if tp+fn else 0., 'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.}
    for field, value in measured.items():
        assert math.isclose(summary[field], value, abs_tol=1e-12), field
    return {**measured, 'native_requests_replayed': sum(map(len, raw_by_id.values())),
            'invalid_decoder_events_preserved': invalid_count, 'overlap_drop_events_preserved': drops,
            'accepted_span_schema_errors': 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    assert root.parent == Path('/root/autodl-tmp/round2_uie_nocard_20261010/future_pilot')
    assert (root / 'controller.completed').exists()
    assert all((root/f'{phase}.exit_code').read_text().strip() == '0' for phase in ('zero_shot', 'support4_sanity'))
    configs = {p: read_json(root/'configs'/f'{p}.json') for p in ('zero_shot', 'support4_sanity')}
    tokenizer = AutoTokenizer.from_pretrained(configs['zero_shot']['model_path'])
    dev = read_rows('/root/autodl-tmp/data/domain_dev.jsonl')[:20]
    support = read_rows('/root/autodl-tmp/data/domain_support.jsonl')[:4]
    reports = {}
    for phase, config in configs.items():
        assert config['query_path'] == '/root/autodl-tmp/data/domain_dev.jsonl' and config['phase'] == 'dev_pilot'
        assert config['execution']['human_gate'] in ('ROUND2_UIE_DEV_PILOT_APPROVED_20261010',
                                                   'ROUND2_UIE_DEV_PILOT_LOADER_RECHECK_APPROVED_20261012')
        out = Path(config['output_dir'])
        assert read_json(out/'executed_config.json') == config
        completion = read_json(out/'completion.json')
        assert completion['completed'] and completion['elapsed_seconds'] < 1200
        reports[phase] = audit_predictions(out/'evaluation', dev, tokenizer)
        reports[phase]['model_calls'] = completion['model_calls']
    sanity_out = Path(configs['support4_sanity']['output_dir'])
    learning = read_json(sanity_out/'learning_sanity.json')
    training = [r for r in read_rows(sanity_out/'training.jsonl') if 'step' in r]
    assert len(training) == learning['steps'] == 30
    assert [r['step'] for r in training] == list(range(1, 31))
    assert all(math.isfinite(r['grad_norm']) and r['grad_norm'] > 0 and math.isfinite(r['loss']) for r in training)
    initial = statistics.mean(r['loss'] for r in training[:3])
    final = statistics.mean(r['loss'] for r in training[-3:])
    assert final < initial and learning['loss_decreased']
    support_report = audit_predictions(sanity_out/'support_sanity', support, tokenizer)
    assert support_report['tp'] > 0 and support_report['predicted_entities'] > 0
    if configs['zero_shot']['execution']['human_gate'] == 'ROUND2_UIE_DEV_PILOT_LOADER_RECHECK_APPROVED_20261012':
        runtime = {}
        for phase,config in configs.items():
            out = Path(config['output_dir'])
            before = read_json(out/'runtime_before_model.json')
            reports = [before['before_device'], before['before_model'],
                       read_json(out/'runtime_after_model_load.json'), read_json(out/'runtime_after_execution.json')]
            runtime[phase] = [require_isolated_runtime(report) for report in reports]
        isolated = True
    else:
        runtime = read_json(root/'runtime_cudnn_audit.json')
        isolated = runtime['paddle_runtime_cudnn_version'] == runtime['isolated_cudnn8_version'] == 8600
    report = {'data_and_prediction_validation': 'PASS', 'learning_sanity': 'PASS',
              'runtime_cudnn_isolation': 'PASS' if isolated else 'FAILED',
              'overall_status': 'PILOT_QUALIFIED' if isolated else 'DIAGNOSTIC_COMPLETED_RUNTIME_ISOLATION_FAILED',
              'formal_cells_completed': 0, 'new_model_calls_during_audit': 0,
              'results': reports, 'support4_result': support_report,
              'learning': {'steps': 30, 'initial_mean_loss': initial, 'final_mean_loss': final,
                           'min_grad_norm': min(r['grad_norm'] for r in training),
                           'max_grad_norm': max(r['grad_norm'] for r in training)},
              'runtime_cudnn_audit': runtime,
              'next': 'Stop models; preserve and back up; repair process-local library selection in no-card mode under a new bounded decision.'}
    with (root/'independent_validation.json').open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
