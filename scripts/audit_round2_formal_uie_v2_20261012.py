"""Independent native-probability replay and dev-only checkpoint selection audit."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, '/root/project/scripts')
from audit_round2_uie_dev_pilot_v2_20261012 import audit_predictions, read_json, read_rows
from equipment_ie.uie_cuda_guard import require_isolated_runtime
from paddlenlp.transformers import AutoTokenizer


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--condition', required=True)
    args = p.parse_args()
    root = Path('/root/autodl-tmp/round2_formal_20261012_r3/uie')
    assert args.condition in ('uie_base_zero_shot', 'uie_base_ft30_s42', 'uie_base_ft30_s43', 'uie_base_ft30_s44')
    cfg = read_json(root/'configs'/(args.condition+'.json'))
    out = root/args.condition
    assert read_json(out/'executed_config.json') == cfg
    assert cfg['phase'] == 'formal' and cfg['query_path'] == '/root/autodl-tmp/data/domain_test.jsonl'
    assert cfg['execution']['human_gate'] == 'ROUND2_UIE_FORMAL_APPROVED_20261010'
    for path, digest in cfg['input_sha256'].items():
        assert sha(Path(path)) == digest, path
    completion = read_json(out/'completion.json')
    assert completion['completed'] and completion['elapsed_seconds'] < 3600
    before = read_json(out/'runtime_before_model.json')
    runtime = [before['before_device'], before['before_model'], read_json(out/'runtime_after_model_load.json'),
               read_json(out/'runtime_after_execution.json')]
    for r in runtime:
        require_isolated_runtime(r)
    tokenizer = AutoTokenizer.from_pretrained(cfg['model_path'])
    test = read_rows(cfg['query_path'])
    assert len(test) == 170
    measured = audit_predictions(out/'evaluation', test, tokenizer)
    training_report = None
    if cfg['mode'] == 'finetune':
        dev = read_rows('/root/autodl-tmp/data/domain_dev.jsonl')
        support = read_rows('/root/autodl-tmp/data/domain_support.jsonl')
        assert len(dev) == 50 and len(support) == 30
        assert not {r['id'] for r in support} & {r['id'] for r in dev+test}
        features = read_rows(cfg['train_features_path'])
        assert {r['source_id'] for r in features} <= {r['id'] for r in support}
        logs = read_rows(out/'training.jsonl')
        steps = [r for r in logs if 'step' in r]
        assert [r['step'] for r in steps] == list(range(1, len(steps)+1))
        assert all(math.isfinite(r['loss']) and math.isfinite(r['grad_norm']) and r['grad_norm'] > 0 for r in steps)
        epochs = [r for r in logs if 'dev' in r]
        assert [r['epoch'] for r in epochs] == list(range(1, len(epochs)+1))
        best, best_epoch, stale, selections = -1., None, 0, []
        epoch_results = {}
        for row in epochs:
            epoch = row['epoch']
            replay = audit_predictions(out/f'dev_epoch_{epoch:02d}', dev, tokenizer)
            epoch_results[str(epoch)] = replay
            assert math.isclose(replay['f1'], row['dev']['f1'], abs_tol=1e-12)
            if row['dev']['f1'] > best:
                best, best_epoch, stale = row['dev']['f1'], epoch, 0
                selections.append(epoch)
            else:
                stale += 1
            assert math.isclose(row['best_f1'], best, abs_tol=1e-12) and row['stale'] == stale
            if epoch < len(epochs):
                assert stale < 3
            assert sum(r['epoch'] == epoch for r in steps) == math.ceil(len(features)/8)
        assert 1 <= len(epochs) <= 20 and (len(epochs) == 20 or stale == 3)
        changes = [r for r in logs if 'selected_epoch' in r]
        assert [r['selected_epoch'] for r in changes] == selections
        for i, change in enumerate(changes):
            assert change['checkpoint_previous_hashes'] == ({} if i == 0 else changes[i-1]['checkpoint_current_hashes'])
        hashes = {path.name: sha(path) for path in (out/'best_checkpoint').iterdir() if path.is_file()}
        assert hashes == changes[-1]['checkpoint_current_hashes']
        selection = read_json(out/'checkpoint_selection.json')
        assert selection == {'best_f1': best, 'checkpoint': str(out/'best_checkpoint'), 'tie_rule': 'earliest'}
        training_report = {'seed': cfg['seed'], 'epochs': len(epochs), 'steps': len(steps),
                           'selected_epoch': best_epoch, 'best_dev_f1': best,
                           'dev_selection_audit': epoch_results, 'checkpoint_sha256': hashes,
                           'selection_uses_test': False}
    report = {'status': 'FORMAL_CELL_VERIFIED', 'condition': args.condition,
              'test170': measured, 'training': training_report, 'runtime_cudnn': 8600,
              'model_calls': completion['model_calls'], 'new_model_calls_during_audit': 0}
    with (out/'independent_validation.json').open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({'condition': args.condition, 'test170': measured,
                      'training': None if training_report is None else {k:v for k,v in training_report.items() if k != 'dev_selection_audit'}}))


if __name__ == '__main__':
    main()
