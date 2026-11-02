#!/usr/bin/env python3
"""Deterministic full-vs-knn+G entity set differences; real evidence only."""
import argparse
import json
from pathlib import Path


def keys(row,key):return {(e['start'],e['end'],e['type']) for e in row[key]['entities']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--full',required=True,type=Path);p.add_argument('--knn-g',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();assert not list(Path('/dev').glob('nvidia[0-9]*'))
    full=[json.loads(s) for s in args.full.read_text().splitlines()];other=[json.loads(s) for s in args.knn_g.read_text().splitlines()]
    assert len(full)==len(other)==170
    events=[]
    for a,b in zip(full,other):
        assert a['id']==b['id'] and a['gold']==b['gold']
        assert a['example_ids']==b['example_ids'] and a['glossary_terms']==b['glossary_terms']
        assert not b['rag_passage_ids']
        gold,x,y=keys(a,'gold'),keys(a,'pred_raw'),keys(b,'pred_raw')
        types=[]
        if (y-x)-gold:types.append('FP_removed_by_set_difference')
        if (y-x)&gold:types.append('TP_lost_new_FN')
        if (x-y)-gold:types.append('new_FP')
        if x==y:types.append('unchanged_control')
        events.append({'id':a['id'],'categories':types,'text':a['gold']['text'],'gold':a['gold']['entities'],
                       'full':a['pred_raw']['entities'],'knn_g':b['pred_raw']['entities'],
                       'actual_rag_passage_ids':a['rag_passage_ids'],'actual_rag_passages':a['rag_passages']})
    categories=['FP_removed_by_set_difference','TP_lost_new_FN','new_FP','unchanged_control']
    summary={'model_calls':0,'not_a_causal_mechanism_proof':True,'selection':'first ID in each category; no invented examples',
             'counts':{t:sum(t in e['categories'] for e in events) for t in categories},
             'selected':{t:next((e for e in sorted(events,key=lambda v:v['id']) if t in e['categories']),None) for t in categories}}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'rag_cases.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    with (args.output/'all_paired_differences.jsonl').open('x',encoding='utf-8') as f:
        for row in events:f.write(json.dumps(row,ensure_ascii=False)+'\n')


if __name__=='__main__':main()
