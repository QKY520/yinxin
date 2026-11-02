#!/usr/bin/env python3
"""No-card Qwen raw-cache/weight audit and disabled dev/formal execution package."""
import copy
import argparse
import hashlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from equipment_ie.extraction import parse_extraction_output, build_ner_prompt, prompt_hash
from equipment_ie.schema import iter_jsonl

OLD=Path('/root/autodl-tmp/reviewer_qwen_neutral_envelope_formal_20260917')
PREP=Path('/root/autodl-tmp/round2_nocard_preparation_20261010')
OUT=Path('/root/autodl-tmp/round2_runtime_bundle_20261010')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def save(path,data):
    with path.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,sort_keys=True)


def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUT)
    OUT=parser.parse_args().output
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    OUT.mkdir(exist_ok=False)
    report={'model_calls':0,'systems':{},'weights':[],'full_reuse':'OFFLINE_AUDIT_ONLY_DEV_PILOT_PENDING'}
    systems=[(s,OLD) for s in ['zero_shot','bm25_only','rag_only','ec_fsie_full']]
    glossary=Path('/root/autodl-tmp/reviewer_qwen_glossary_only_formal_20260918')
    systems.append(('glossary_only',glossary))
    for system,base in systems:
        config_path=base/(system+'.yaml')
        if system=='glossary_only':
            provenance=json.loads((base/'manifest.json').read_text())
            config_path=ROOT/provenance['config_path']
            assert sha(config_path)==provenance['config_sha256']
        if not config_path.exists():
            alternatives=list(base.glob('*.yaml'))
            if len(alternatives)!=1:raise ValueError(f'Config path unresolved: {base}')
            config_path=alternatives[0]
        cfg=yaml.safe_load(config_path.read_text())
        query_path=Path(cfg['outputs']['per_query'])
        cached=Path(cfg['cache']['dir'])
        items=rows(query_path)
        assert len(items)==170
        count=failed=0
        for item in items:
            attempt=item['attempts'][-1]
            key=attempt['request_hash']
            cache_path=cached/key[:2]/(key+'.json')
            cache=json.loads(cache_path.read_text())
            content=cache['content']
            assert hashlib.sha256(content.encode()).hexdigest()==cache['raw_output_hash']==attempt['raw_output_hash']==item['raw_llm_output_hash']
            try:
                parsed=parse_extraction_output(content,record_id=item['id'],text=item['gold']['text'],
                    entity_types=set(cfg['schema']['entity_types']),
                    output_mode=cfg['parsing']['output_mode'],
                    ner_only_envelope_policy=cfg['parsing'].get('ner_only_envelope_policy','strict'),
                    drop_invalid_entities=cfg['parsing'].get('drop_invalid_entities',False),
                    sanitization_flags=[],max_entities=cfg['parsing'].get('max_entities'))
            except Exception:
                assert item['parse_failure'] is True
                assert not item['pred_raw']['entities']
                failed+=1
            else:
                assert item['parse_failure'] is False
                assert parsed==item['pred_raw'],f'Parser replay mismatch {system}/{item["id"]}'
            count+=1
        report['systems'][system]={'parser_replayed':count,'failed_rows_preserved':failed,'config_sha256':sha(config_path),'per_query_sha256':sha(query_path)}
    for line in Path('/root/autodl-tmp/backup/p0/model_files.sha256').read_text().splitlines():
        expected,relative=line.split(None,1)
        if relative.startswith('models/qwen2.5-7b/'):
            path=Path('/root/autodl-tmp')/relative
            actual=sha(path)
            assert actual==expected,f'Qwen weight/resource mismatch {relative}'
            report['weights'].append({'path':str(path),'sha256':actual,'bytes':path.stat().st_size})
    assert report['weights'] and any(x['path'].endswith('.safetensors') for x in report['weights'])
    report['current_versions']={n:importlib.metadata.version(n) for n in ['torch','vllm','transformers','tokenizers','numpy']}
    log=(OLD/'vllm.log').read_text(errors='replace')
    match=re.search(r'API server version\s+([^\s]+)',log)
    report['historical_vllm_version_from_log']=match.group(1) if match else None
    report['vllm_version_matches']=report['historical_vllm_version_from_log']==report['current_versions']['vllm']
    report['historical_full_dependency_freeze_available']=False
    report['environment_boundary']='Current freeze and historical vLLM startup evidence; no claim of byte-identical historical full environment'
    save(OUT/'qwen_reuse_audit.json',report)
    # Dev examples are selected previously from support30, not test predictions.
    historical=Path('/root/project/results/p3/p3_domain_dev50_d_rag_k5_sanity_sanitize_per_query.jsonl')
    dev=list(iter_jsonl('/root/autodl-tmp/data/domain_dev.jsonl'))
    previous=rows(historical)
    assert len(previous)==50 and [r['id'] for r in previous]==[r['id'] for r in dev]
    support=list(iter_jsonl('/root/autodl-tmp/data/domain_support.jsonl'))
    support_ids={r['id'] for r in support}
    replay=[]
    for item in previous:
        assert len(item['example_ids'])==5 and set(item['example_ids'])<=support_ids
        replay.append({'id':item['id'],'example_ids':item['example_ids']})
    replay_path=OUT/'dev_examples_replay.jsonl'
    with replay_path.open('x',encoding='utf-8') as f:
        for item in replay:f.write(json.dumps(item)+'\n')
    from run_p3_extraction import build_query_plan
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained('/root/autodl-tmp/models/qwen2.5-7b',local_files_only=True)
    configs=OUT/'qwen_configs_not_authorized';configs.mkdir()
    budgets={}
    for system in ['random5_s42','random5_s43','random5_s44','knn5','knn5_glossary']:
        original=PREP/'configs_not_authorized'/(system+'.yaml')
        formal=yaml.safe_load(original.read_text())
        for phase in ['dev_pilot','formal']:
            cfg=copy.deepcopy(formal)
            cfg['execution']={'authorized':False,'model_calls_allowed':False,'human_gate':'NOT_GRANTED','phase':'ROUND2_QWEN_'+phase.upper()}
            cfg['round2_phase']=phase
            cfg['config_name']=cfg['run_id']=f'round2_{system}_{phase}'
            if phase=='dev_pilot':
                cfg['data']['query_path']='/root/autodl-tmp/data/domain_dev.jsonl'
                cfg['data']['dataset']='domain_dev'
                cfg['data']['expected_records']=50
                cfg['data']['expected_sha256']=sha(cfg['data']['query_path'])
                cfg['query_limit']=20
                if system.startswith('knn'):cfg['examples']['source_per_query_path']=str(replay_path)
            target=OUT/'future_runs'/phase/system
            cfg['cache']['dir']=str(target/'cache')
            cfg['outputs']={key:str(target/(key+'.jsonl' if key in ['per_query','dry_run_prompts'] else key+'.json')) for key in cfg['outputs']}
            cfg['round2_input_sha256']={cfg['data']['query_path']:sha(cfg['data']['query_path']),cfg['data']['support_path']:sha(cfg['data']['support_path'])}
            if system.startswith('knn'):cfg['round2_input_sha256'][cfg['examples']['source_per_query_path']]=sha(cfg['examples']['source_per_query_path'])
            if system=='knn5_glossary':cfg['round2_input_sha256'][cfg['glossary']['path']]=sha(cfg['glossary']['path'])
            path=configs/(system+'_'+phase+'.yaml')
            with path.open('x',encoding='utf-8') as f:yaml.safe_dump(cfg,f,allow_unicode=True,sort_keys=False)
            if phase=='dev_pilot':
                _,queries,ex,gl,rag,*_=build_query_plan(config=cfg,config_path=path,dry_run=True)
                lengths=[]
                for record in queries:
                    prompt=build_ner_prompt(query_text=record['text'],entity_types=cfg['schema']['entity_types'],examples=ex(record),
                        glossary_entries=gl(record),rag_passages=[],include_relations=False,
                        output_instruction=cfg['prompt']['output_instruction'],output_mode=cfg['parsing']['output_mode'])
                    size=len(tokenizer.apply_chat_template([{'role':'user','content':prompt}],tokenize=True,add_generation_prompt=True))
                    assert size+768<=8192
                    lengths.append(size)
                assert len(lengths)==20
                budgets[system]={'queries':20,'max_tokens':max(lengths),'generation_reserve':768,'context':8192}
    save(OUT/'qwen_dev_offline_budget.json',{'model_calls':0,'systems':budgets,'dev_replay_source':str(historical),'dev_replay_source_sha256':sha(historical)})
    save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()})
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
