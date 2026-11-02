#!/usr/bin/env python3
"""AutoDL-only offline prompt-replay audit. No model calls or new predictions."""
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT/'scripts'))
from run_p3_extraction import build_query_plan
from equipment_ie.extraction import build_ner_prompt, prompt_hash


def main():
    if list(Path('/dev').glob('nvidia[0-9]*')):
        raise RuntimeError('no-card mode required')
    out = Path('/root/autodl-tmp/round2_nocard_preparation_20261010')
    target = out/'offline_prompt_audit.json'
    if target.exists():
        raise FileExistsError(target)
    old = Path('/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917')
    old_rows = [json.loads(s) for s in (old/'formal/ec_fsie_full/per_query.jsonl').read_text().splitlines()]
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained('/root/autodl-tmp/models/qwen2.5-7b', local_files_only=True)
    report = {'model_calls': 0, 'tokenizer_only': True, 'prediction_or_f1_recomputed': False,
              'full_prompt_matches': 0, 'systems': {}, 'ui_environment_status': 'NOT_INSTALLED'}
    config_paths = list(sorted((out/'configs_not_authorized').glob('*5*.yaml')))
    anchor_cfg = yaml.safe_load((old/'ec_fsie_full.yaml').read_text())
    for name, config, path in [('full_reuse_anchor', anchor_cfg, old/'ec_fsie_full.yaml')] + [
        (p.stem, yaml.safe_load(p.read_text()), p) for p in config_paths]:
        # build_query_plan dry_run only loads frozen resources/replay selectors.
        plan = build_query_plan(config=config, config_path=path, dry_run=True)
        _, records, select_examples, select_glossary, select_rag, *_ = plan
        details = []
        for row, previous in zip(records, old_rows):
            examples, glossary, rag = select_examples(row), select_glossary(row), select_rag(row)
            prompt = build_ner_prompt(query_text=row['text'], entity_types=config['schema']['entity_types'],
                                     examples=examples, glossary_entries=glossary,
                                     rag_passages=[r['display'] for r in rag], include_relations=False,
                                     output_instruction=config['prompt']['output_instruction'],
                                     output_mode=config['parsing']['output_mode'])
            tokens = len(tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}],
                                                       tokenize=True, add_generation_prompt=True))
            if name == 'full_reuse_anchor':
                assert row['id'] == previous['id']
                assert prompt_hash(prompt) == previous['prompt_hash'], f"Full prompt mismatch: {row['id']}"
                assert glossary == previous['glossary_terms']
                assert [r['id'] for r in rag] == previous['rag_passage_ids']
                assert [e['id'] for e in examples] == previous['example_ids']
                report['full_prompt_matches'] += 1
            else:
                assert not rag
                if name != 'knn5_glossary':
                    assert not glossary
                if name.startswith('knn'):
                    assert [e['id'] for e in examples] == previous['example_ids']
                    if name == 'knn5_glossary':
                        assert glossary == previous['glossary_terms']
            details.append({'id': row['id'], 'example_ids': [e['id'] for e in examples],
                            'input_tokens': tokens, 'prompt_sha256': prompt_hash(prompt)})
        assert len(details) == 170
        max_tokens = max(r['input_tokens'] for r in details)
        assert max_tokens+int(config['generation']['max_tokens']) <= 8192
        detail_path = out/(name+'_request_plan.jsonl')
        with detail_path.open('x', encoding='utf-8') as f:
            for row in details:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
        item = {'queries': len(details), 'max_input_tokens': max_tokens,
                'generation_reserve': config['generation']['max_tokens'], 'context_limit': 8192,
                'request_plan_sha256': hashlib.sha256(detail_path.read_bytes()).hexdigest()}
        if name.startswith('random'):
            assert all(r['example_ids'] == details[0]['example_ids'] for r in details)
            item['fixed_example_ids'] = details[0]['example_ids']
        report['systems'][name] = item
    assert report['full_prompt_matches'] == 170
    report['full_input_prompt_glossary_and_rag_replay'] = 'PASS_170_OF_170'
    report['full_reuse_remaining'] = ['raw-output parser replay equality', 'model-weight manifest verification',
                                      'dependency/environment provenance audit', 'dev inference pilot']
    with target.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
