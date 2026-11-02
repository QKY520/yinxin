#!/usr/bin/env python3
"""Gated UIE GPU runner. --dry-run validates configuration without importing Paddle."""
import argparse
import gzip
import hashlib
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from equipment_ie.schema import iter_jsonl
from equipment_ie.extraction import entity_micro_counts
from equipment_ie.uie_adapter import SCHEMA_MAP, character_windows
from equipment_ie.uie_runtime import INPUT_KEYS, encode_pair, pad_inputs, decode_native, merge_window_outputs, require_authority
from equipment_ie.uie_cuda_guard import inspect_runtime


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, sort_keys=True)


def read_rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def validate(config, dry_run):
    require_authority(config, dry_run=dry_run)
    for path, expected in config.get('input_sha256', {}).items():
        if digest(path) != expected:
            raise RuntimeError(f'Frozen resource mismatch: {path}')
    if config['mode'] not in ('zero_shot', 'finetune', 'learning_sanity'):
        raise ValueError('Unknown mode')
    if config['mode'] == 'learning_sanity' and config['phase'] != 'dev_pilot':
        raise ValueError('Learning sanity may not execute formal test')
    if config['mode'] != 'zero_shot':
        cfg = config['training']
        if cfg['batch_size'] != 8 or cfg['learning_rate'] != 1e-5 or cfg['precision'] != 'fp32':
            raise ValueError('Training lock mismatch')
        if not 1 <= cfg['max_epochs'] <= 20 or cfg['early_stop_patience'] != 3:
            raise ValueError('Epoch/early-stop lock mismatch')
    if dry_run:
        # No labels are read here: only hash the locked sources/features.
        return {'dry_run': True, 'model_calls': 0, 'config_valid': True,
                'mode': config['mode'], 'phase': config['phase'], 'authorized': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    checked = validate(cfg, args.dry_run)
    if args.dry_run:
        print(json.dumps(checked))
        return
    if not list(Path('/dev').glob('nvidia[0-9]*')):
        raise RuntimeError('GPU not exposed; refusing all model loading/forward')
    memory_limit = Path('/sys/fs/cgroup/memory.max').read_text().strip()
    if memory_limit != 'max' and int(memory_limit) < 8*1024**3:
        raise RuntimeError('Less than8GiB container memory; refuse model loading')
    if shutil.disk_usage('/root/autodl-tmp').free < 5*1024**3:
        raise RuntimeError('Less than 5GiB free: stop before training/inference')
    # Lazy imports are deliberate: offline validation cannot instantiate models.
    import numpy as np
    import paddle
    from paddlenlp.transformers import UIE, AutoTokenizer
    from paddlenlp.utils.tools import get_span
    if not paddle.is_compiled_with_cuda():
        raise RuntimeError('CPU-only Paddle cannot run the paid phase')
    # Compile metadata/import alone cannot qualify actual dynamic libraries.
    # Query Paddle's own selected cuDNN and maps before device/model loading.
    runtime_before_device = inspect_runtime(paddle)
    paddle.set_device('gpu:0')
    runtime_before_model = inspect_runtime(paddle)
    seed = cfg.get('seed') if cfg.get('seed') is not None else 42
    random.seed(seed)
    np.random.seed(seed)
    paddle.seed(seed)
    started = time.monotonic()
    timeout = cfg['time_limit_seconds']
    def budget():
        if time.monotonic()-started > timeout:
            raise RuntimeError('Bounded phase time stop; partial evidence retained')
        if shutil.disk_usage('/root/autodl-tmp').free < 5*1024**3:
            raise RuntimeError('Disk stop; partial evidence retained')
    out = Path(cfg['output_dir'])
    out.mkdir(parents=True, exist_ok=False)
    save(out/'executed_config.json', cfg)
    save(out/'runtime_before_model.json', {'before_device': runtime_before_device,
                                         'before_model': runtime_before_model})
    save(out/'provenance.json', {'config_sha256': digest(args.config), 'runner_sha256': digest(__file__),
                               'seed': seed, 'start_unix': time.time(), 'input_sha256': cfg['input_sha256'],
                               'paddle': paddle.__version__, 'paddlenlp': __import__('paddlenlp').__version__})
    tokenizer = AutoTokenizer.from_pretrained(cfg['model_path'])
    model = UIE.from_pretrained(cfg['model_path'])
    save(out/'runtime_after_model_load.json', inspect_runtime(paddle))
    model_calls = 0

    def tensors(rows):
        return {key: paddle.to_tensor(np.asarray([r[key] for r in rows], dtype='int64')) for key in INPUT_KEYS}

    def predict(records, destination):
        nonlocal model_calls
        model.eval()
        predictions = []
        with gzip.open(destination/'native_probabilities.jsonl.gz', 'xt', encoding='utf-8') as raw, \
             (destination/'per_query.jsonl').open('x', encoding='utf-8') as final:
            for record in records:
                budget()
                windows = character_windows(record['text'], lambda text: all(len(encode_pair(tokenizer,p,text)['input_ids']) <= 512 for p in SCHEMA_MAP),
                                            max_chars=cfg['window_max_chars'], overlap=cfg['window_overlap_chars'])
                requests = [(w, p, encode_pair(tokenizer, p, w['text'])) for w in windows for p in SCHEMA_MAP]
                outputs = []
                for batch_start in range(0, len(requests), 8):
                    budget()
                    batch = requests[batch_start:batch_start+8]
                    inputs = tensors([pad_inputs(tokenizer, enc) for _, _, enc in batch])
                    with paddle.no_grad():
                        sp, ep = model(**inputs)
                    model_calls += 1
                    inspect_runtime(paddle)
                    sp, ep = sp.numpy(), ep.numpy()
                    for (window, prompt, encoded), starts, ends in zip(batch, sp, ep):
                        native, invalid = decode_native(window['text'], encoded, starts.tolist(), ends.tolist(), get_span, cfg['position_prob'])
                        item = {'id': record['id'], 'window': window, 'prompt': prompt, 'native': native, 'decoder_invalid': invalid}
                        raw.write(json.dumps({**item, 'input_ids': encoded['input_ids'], 'offset_mapping': encoded['offset_mapping'],
                                              'start_probs': starts.tolist(), 'end_probs': ends.tolist()}, ensure_ascii=False)+'\n')
                        outputs.append(item)
                entities, invalid, dropped = merge_window_outputs(record['text'], outputs)
                prediction = {'id': record['id'], 'text': record['text'], 'entities': entities, 'relations': []}
                predictions.append(prediction)
                final.write(json.dumps({'id': record['id'], 'gold': record, 'pred_raw': prediction,
                                        'parse_failure': False, 'native_invalid': invalid, 'overlap_and_duplicate_drops': dropped}, ensure_ascii=False)+'\n')
                final.flush()
        summary = {'queries': len(records), **entity_micro_counts(records, predictions).report(),
                   'predicted_entities': sum(len(p['entities']) for p in predictions),
                   'per_type': {kind: entity_micro_counts(
                       [{**r, 'entities': [e for e in r['entities'] if e['type']==kind]} for r in records],
                       [{**r, 'entities': [e for e in r['entities'] if e['type']==kind]} for r in predictions]).report() for kind in SCHEMA_MAP.values()}}
        save(destination/'summary.json', summary)
        return summary

    if cfg['mode'] != 'zero_shot':
        features = read_rows(cfg['train_features_path'])
        support = list(iter_jsonl('/root/autodl-tmp/data/domain_support.jsonl'))
        if cfg['mode'] == 'learning_sanity':
            ids = {r['id'] for r in support[:4]}
            features = [r for r in features if r['source_id'] in ids]
        assert features and all(r['source_id'] in {q['id'] for q in support} for r in features)
        tcfg = cfg['training']
        optimizer = paddle.optimizer.AdamW(learning_rate=tcfg['learning_rate'], parameters=model.parameters(), weight_decay=0.)
        criterion = paddle.nn.BCELoss()
        best_f1, best_dir, stale, steps = -1., None, 0, 0
        losses = []
        dev = list(iter_jsonl('/root/autodl-tmp/data/domain_dev.jsonl'))
        with (out/'training.jsonl').open('x', encoding='utf-8') as log:
            for epoch in range(1, tcfg['max_epochs']+1):
                model.train()
                order = np.random.permutation(len(features))
                for begin in range(0, len(order), 8):
                    budget()
                    batch = [features[i] for i in order[begin:begin+8]]
                    sp, ep = model(**tensors(batch))
                    model_calls += 1
                    inspect_runtime(paddle)
                    ys = paddle.to_tensor(np.asarray([r['start_positions'] for r in batch], dtype='float32'))
                    ye = paddle.to_tensor(np.asarray([r['end_positions'] for r in batch], dtype='float32'))
                    loss = (criterion(sp, ys)+criterion(ep, ye))/2
                    value = float(loss.numpy().item())
                    if not math_is_finite(value):
                        raise RuntimeError('Non-finite training loss; no baseline result accepted')
                    loss.backward()
                    grad_norm = sum(float(paddle.sum(p.grad*p.grad).numpy().item()) for p in model.parameters() if p.grad is not None)**.5
                    if not math_is_finite(grad_norm) or grad_norm <= 0:
                        raise RuntimeError('Non-finite or zero learning gradients')
                    optimizer.step()
                    optimizer.clear_grad()
                    steps += 1
                    losses.append(value)
                    log.write(json.dumps({'epoch': epoch, 'step': steps, 'loss': value, 'grad_norm': grad_norm})+'\n')
                    log.flush()
                if cfg['mode'] == 'learning_sanity':
                    if steps >= cfg['sanity_steps']:
                        break
                    continue
                epoch_dir = out/f'dev_epoch_{epoch:02d}'
                epoch_dir.mkdir()
                measured = predict(dev, epoch_dir)
                if measured['f1'] > best_f1:
                    best_f1, stale = measured['f1'], 0
                    staged = out/f'checkpoint_epoch_{epoch:02d}_staging'
                    staged.mkdir()
                    model.save_pretrained(str(staged))
                    tokenizer.save_pretrained(str(staged))
                    # Keep every epoch's predictions/metrics, but only one best
                    # weight set per run. Replace only files made by this run.
                    if best_dir is None:
                        best_dir = out/'best_checkpoint'
                        best_dir.mkdir()
                    assert best_dir.resolve().parent == out.resolve()
                    previous = {p.name: digest(p) for p in best_dir.iterdir() if p.is_file()}
                    for path in staged.iterdir():
                        if not path.is_file():
                            raise RuntimeError('Unexpected nested checkpoint artifact')
                        path.replace(best_dir/path.name)
                    log.write(json.dumps({'selected_epoch': epoch, 'checkpoint_previous_hashes': previous,
                                          'checkpoint_current_hashes': {p.name: digest(p) for p in best_dir.iterdir()}})+'\n')
                else:
                    stale += 1
                log.write(json.dumps({'epoch': epoch, 'dev': measured, 'best_f1': best_f1, 'stale': stale})+'\n')
                log.flush()
                if stale >= tcfg['early_stop_patience']:
                    break
        if cfg['mode'] == 'learning_sanity':
            learning_ok = len(losses)>=6 and sum(losses[-3:])/3 < sum(losses[:3])/3
            sanity = out/'support_sanity'
            sanity.mkdir()
            measured = predict(support[:4], sanity)
            save(out/'learning_sanity.json', {'steps': steps, 'initial_losses': losses[:3], 'final_losses': losses[-3:],
                                            'loss_decreased': learning_ok, 'support_prediction': measured,
                                            'is_paper_result': False})
            if not learning_ok or measured['predicted_entities'] == 0 or measured['tp'] == 0:
                raise RuntimeError('Learning sanity failed; do not run formal cells')
        else:
            save(out/'checkpoint_selection.json', {'best_f1': best_f1, 'checkpoint': str(best_dir), 'tie_rule': 'earliest'})
            del optimizer, model
            paddle.device.cuda.empty_cache()
            model = UIE.from_pretrained(str(best_dir))
    queries = list(iter_jsonl(cfg['query_path']))
    if cfg['phase'] == 'dev_pilot':
        queries = queries[:cfg['query_limit']]
    destination = out/'evaluation'
    destination.mkdir()
    summary = predict(queries, destination)
    save(out/'runtime_after_execution.json', inspect_runtime(paddle))
    save(out/'completion.json', {'completed': True, 'phase': cfg['phase'], 'model_calls': model_calls,
                                'elapsed_seconds': time.monotonic()-started, 'summary': summary,
                                'nondegenerate': summary['predicted_entities']>0})
    print(json.dumps(summary))


def math_is_finite(x):
    import math
    return math.isfinite(x)


if __name__ == '__main__':
    main()
