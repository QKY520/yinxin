"""Replay cached Qwen dev outputs and independently count entities; no model/API."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import yaml

sys.path.insert(0, '/root/project/scripts')
sys.path.insert(0, '/root/project/src')
import run_p3_extraction as historical
from equipment_ie.extraction import build_ner_prompt, build_request_envelope, build_error_retry_prompt, parse_extraction_output, prompt_hash
from equipment_ie.llm_labeling import request_hash


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def count_keys(record):
    return {(e['start'], e['end'], e['type']) for e in record['entities']}


def audit_condition(root, condition):
    cfg_path = root/'configs'/f'{condition}.yaml'
    cfg = yaml.safe_load(cfg_path.read_text())
    _, queries, select_examples, select_glossary, select_rag, config_hash, *_ = historical.build_query_plan(config=cfg, config_path=cfg_path, dry_run=True)
    rows = [json.loads(line) for line in (root/condition/'per_query.jsonl').read_text().splitlines()]
    summary = json.loads((root/condition/'summary.json').read_text())
    assert len(rows) == len(queries) == 170
    assert [row['id'] for row in rows] == [r['id'] for r in queries]
    tp = fp = fn = failures = attempts = hits = truncated = invalid_units = 0
    per_type = {kind: {'tp': 0, 'fp': 0, 'fn': 0} for kind in cfg['schema']['entity_types']}
    for row, gold in zip(rows, queries):
        assert row['gold'] == gold and not select_rag(gold)
        examples, glossary = select_examples(gold), select_glossary(gold)
        assert row['example_ids'] == [e['id'] for e in examples]
        assert row['glossary_terms'] == glossary and not row['rag_passages'] and not row['rag_passage_ids']
        prompt = build_ner_prompt(query_text=gold['text'], entity_types=cfg['schema']['entity_types'], examples=examples,
                                  glossary_entries=glossary, rag_passages=[], include_relations=False,
                                  output_instruction=cfg['prompt']['output_instruction'], output_mode='occurrence')
        assert prompt_hash(prompt) == row['prompt_hash']
        current_prompt = prompt
        flags = []
        parsed = None
        assert 1 <= len(row['attempts']) <= 2
        for number, attempt in enumerate(row['attempts'], 1):
            envelope = build_request_envelope(prompt=current_prompt, model=cfg['model']['name'], generation=cfg['generation'],
                                              run_id=cfg['run_id'], config_hash=config_hash)
            digest = request_hash(envelope)
            assert digest == attempt['request_hash']
            cache = json.loads((Path(cfg['cache']['dir'])/digest[:2]/f'{digest}.json').read_text())
            assert cache['request'] == envelope and cache['request_hash'] == digest
            assert hashlib.sha256(cache['content'].encode()).hexdigest() == cache['raw_output_hash'] == attempt['raw_output_hash']
            if cache['response']['choices'][0].get('finish_reason') == 'length':
                truncated += 1
            try:
                parsed = parse_extraction_output(cache['content'], record_id=gold['id'], text=gold['text'],
                                                  entity_types=set(cfg['schema']['entity_types']), drop_invalid_entities=True,
                                                  sanitization_flags=flags, output_mode='occurrence',
                                                  ner_only_envelope_policy='entities_or_entities_relations_v2', max_entities=12)
                error = None
            except Exception as exc:
                error = f'{type(exc).__name__}: {exc}'
            assert error == attempt['parse_error']
            if number == 1 and error is not None:
                current_prompt = build_error_retry_prompt(base_prompt=prompt, parse_error=error,
                                                          output_mode='occurrence', retry_suffix=cfg['prompt']['retry_suffix'])
            attempts += 1
            hits += int(attempt['cache_hit'])
        # In-memory tuple keys become JSON lists in the persisted audit record.
        assert json.loads(json.dumps(flags, ensure_ascii=False)) == row['sanitization_flags']
        if parsed is None:
            assert row['parse_failure'] and not row['pred_raw']['entities']
            failures += 1
        else:
            assert not row['parse_failure'] and parsed == row['pred_raw']
        assert row['raw_llm_output_hash'] == row['attempts'][-1]['raw_output_hash']
        for e in row['pred_raw']['entities']:
            assert e['type'] in per_type and gold['text'][e['start']:e['end']] == e['span']
        gold_keys, pred_keys = count_keys(gold), count_keys(row['pred_raw'])
        matched, extra, missing = gold_keys & pred_keys, pred_keys-gold_keys, gold_keys-pred_keys
        tp += len(matched); fp += len(extra); fn += len(missing)
        for kind in per_type:
            per_type[kind]['tp'] += sum(k[2] == kind for k in matched)
            per_type[kind]['fp'] += sum(k[2] == kind for k in extra)
            per_type[kind]['fn'] += sum(k[2] == kind for k in missing)
        invalid_units += row['invalid_unit_drops']
    measured = {'tp': tp, 'fp': fp, 'fn': fn, 'precision': tp/(tp+fp) if tp+fp else 0.,
                'recall': tp/(tp+fn) if tp+fn else 0., 'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.}
    for key, value in measured.items():
        assert math.isclose(summary['entity_micro'][key], value, abs_tol=1e-12), key
    assert sha(root/condition/'per_query.jsonl') == summary['per_query_sha256']
    assert summary['parse_failures'] == failures
    good = failures <= 34
    return {'queries': 170, 'attempts': attempts, 'cache_hits': hits, 'parse_failures': failures,
            'length_truncation_responses': truncated, 'invalid_unit_drops_preserved': invalid_units,
            'accepted_slice_schema_errors': 0, 'entity_micro': measured, 'per_type': per_type,
            'formal_checks_passed': good}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--condition', required=True)
    args = parser.parse_args()
    assert args.condition in ('random5_s42', 'random5_s43', 'random5_s44', 'knn5', 'knn5_glossary')
    root = Path('/root/autodl-tmp/round2_formal_20261012_r3/qwen')
    cfg = yaml.safe_load((root/'configs'/(args.condition+'.yaml')).read_text())
    assert cfg['round2_phase'] == 'formal' and cfg['data']['query_path'] == '/root/autodl-tmp/data/domain_test.jsonl'
    assert cfg['execution']['human_gate'] == 'ROUND2_QWEN_FORMAL_APPROVED_20261010'
    for path, digest in cfg['round2_input_sha256'].items():
        assert sha(path) == digest, path
    result = audit_condition(root, args.condition)
    assert result['attempts'] <= 340 and result['formal_checks_passed']
    assert 'dtype=torch.bfloat16' in (root/'vllm_bf16.log').read_text()
    report = {'status': 'FORMAL_CELL_VERIFIED', 'condition': args.condition, 'result': result,
              'server_runtime_dtype': 'torch.bfloat16', 'new_model_calls_during_audit': 0,
              'historical_prompt_parser_retry_preserved': True}
    with (root/args.condition/'independent_validation.json').open('x') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()