#!/usr/bin/env python3
"""New bounded authority wrapper, reusing unchanged historical Qwen inference/parser."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def validate(config, *, dry_run):
    phase=config.get('round2_phase')
    if phase not in ['dev_pilot','formal']:raise ValueError('Unknown bounded phase')
    expected='/root/autodl-tmp/data/domain_'+('dev' if phase=='dev_pilot' else 'test')+'.jsonl'
    if config['data']['query_path']!=expected:raise ValueError('Split/phase mismatch')
    if config.get('query_limit')!=(20 if phase=='dev_pilot' else 170):raise ValueError('Query bound mismatch')
    if config['generation']!={'temperature':0.0,'top_p':1.0,'max_tokens':768,'seed':42}:raise ValueError('Generation lock mismatch')
    if config['model']['name']!='/root/autodl-tmp/models/qwen2.5-7b':raise ValueError('Model mismatch')
    if config.get('rag'):raise ValueError('New Qwen conditions must not enable RAG')
    if config['examples']['k']!=5 or config['examples']['mode'] not in ['fixed_random','knn_replay']:raise ValueError('Example budget/mode mismatch')
    if config['parsing'].get('output_mode')!='occurrence' or config['parsing'].get('ner_only_envelope_policy')!='entities_or_entities_relations_v2':raise ValueError('Parser protocol mismatch')
    locked=config.get('round2_input_sha256',{})
    required=[expected,config['data']['support_path']]
    if config['examples']['mode']=='knn_replay':required.append(config['examples']['source_per_query_path'])
    if config.get('glossary'):required.append(config['glossary']['path'])
    if not set(required)<=locked.keys():raise ValueError('Missing frozen resources')
    for path,digest in locked.items():
        if sha(path)!=digest:raise ValueError(f'Frozen resource hash mismatch: {path}')
    if dry_run:return
    ex=config['execution']
    gate='ROUND2_QWEN_DEV_PILOT_APPROVED_20261010' if phase=='dev_pilot' else 'ROUND2_QWEN_FORMAL_APPROVED_20261010'
    if ex.get('authorized') is not True or ex.get('model_calls_allowed') is not True or ex.get('human_gate')!=gate:
        raise RuntimeError('New exact human gate required; model calls forbidden')
    for path in config['outputs'].values():
        if Path(path).exists():raise RuntimeError('Never overwrite an earlier execution artifact')


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
    args=p.parse_args();cfg=yaml.safe_load(args.config.read_text())
    validate(cfg,dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps({'configuration':str(args.config),'config_valid':True,'model_calls':0,'execution_authorized':False}))
        return 0
    import run_p3_extraction as historical
    # Only substitute authority validation. Prompts, retry, parser, cache,
    # native inference and metrics remain the original functions.
    historical.validate_execution_gate=lambda execution:validate(cfg,dry_run=False)
    return historical.run_execute(cfg,args.config)


if __name__=='__main__':raise SystemExit(main())
