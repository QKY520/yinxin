#!/usr/bin/env python3
"""Predeclared seed42 paired F1 family and separate RAG endpoints; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

COMPARISONS=[('full','zero'),('full','bm25'),('full','dense'),('full','glossary'),('glossary','zero'),
             ('random42','zero'),('knn','random42'),('knn_g','knn'),('full','knn_g'),
             ('full','random42'),('full','knn'),('full','uie_zs'),('full','uie_ft42')]


def metrics(counts,metric):
    tp,fp,fn=np.moveaxis(counts,-1,0)
    denominator={'f1':2*tp+fp+fn,'precision':tp+fp,'recall':tp+fn}.get(metric)
    if metric=='fp':return fp.astype(float)
    numerator=2*tp if metric=='f1' else tp
    return np.divide(numerator,denominator,out=np.zeros_like(numerator,dtype=float),where=denominator!=0)


def holm(values):
    order=np.argsort(values);result=np.zeros(len(values));last=0.
    for i,index in enumerate(order):
        last=max(last,min(1.,values[index]*(len(values)-i)));result[index]=last
    return result.tolist()


def paired(left,right,metric,seed=20261010,replicates=10000):
    rng=np.random.default_rng(seed);n=len(left)
    delta=float(metrics(left.sum(axis=0),metric)-metrics(right.sum(axis=0),metric))
    boot=[];exceed=0
    for _ in range(0,replicates,100):
        batch=min(100,replicates-len(boot))
        indices=rng.integers(0,n,size=(batch,n))
        boot.extend((metrics(left[indices].sum(axis=1),metric)-metrics(right[indices].sum(axis=1),metric)).tolist())
        swap=rng.integers(0,2,size=(batch,n,1)).astype(bool)
        a=np.where(swap,left[None],right[None]).sum(axis=1)
        b=np.where(swap,right[None],left[None]).sum(axis=1)
        exceed+=int((np.abs(metrics(a,metric)-metrics(b,metric))>=abs(delta)-1e-12).sum())
    return {'difference_left_minus_right':delta,'ci95':np.quantile(boot,[.025,.975]).tolist(),
            'p_two_sided':(exceed+1)/(replicates+1),'replicates':replicates}


def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path);p.add_argument('--output',type=Path);p.add_argument('--protocol-only',action='store_true')
    args=p.parse_args()
    if args.protocol_only:
        print(json.dumps({'f1_family':COMPARISONS,'rag_secondary_family':['precision','recall','fp'],
                          'replicates':10000,'holm':'separate families 13 and3','test_unit':'170 paired original texts; never510 independent seed rows',
                          'random_seeds_and_ft_seeds':'42 main table;42/43/44 descriptive mean/sampleSD', 'no_equivalence_or_noninferiority_claim':True}))
        return
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    paths=json.loads(args.inputs.read_text());systems={};gold_reference=None;ids_reference=None
    for name,path in paths.items():
        rows=[json.loads(s) for s in Path(path).read_text().splitlines()]
        assert len(rows)==170 and len({r['id'] for r in rows})==170
        ids=[r['id'] for r in rows]
        gold=[r['gold'] for r in rows]
        if ids_reference is None:ids_reference,gold_reference=ids,gold
        else:assert ids==ids_reference and gold==gold_reference
        counts=[]
        for row in rows:
            g={(e['start'],e['end'],e['type']) for e in row['gold']['entities']}
            pset={(e['start'],e['end'],e['type']) for e in row['pred_raw']['entities']}
            if row['parse_failure']:assert not pset
            counts.append([len(g&pset),len(pset-g),len(g-pset)])
        systems[name]=np.asarray(counts,dtype='int64')
    results=[]
    for i,(left,right) in enumerate(COMPARISONS):results.append({'left':left,'right':right,**paired(systems[left],systems[right],'f1',20261010+i)})
    for r,padj in zip(results,holm([r['p_two_sided'] for r in results])):r['p_holm_13']=padj
    secondary=[{'metric':m,**paired(systems['full'],systems['knn_g'],m,20262010+i)} for i,m in enumerate(['precision','recall','fp'])]
    for r,padj in zip(secondary,holm([r['p_two_sided'] for r in secondary])):r['p_holm_3']=padj
    descriptive={}
    for name in ['random','uie_ft']:
        cell=[systems[f'{name}{seed}'] for seed in [42,43,44]]
        descriptive[name]={metric:{'mean':float(np.mean(values)),'sample_sd':float(np.std(values,ddof=1))}
                           for metric in ['precision','recall','f1','fp'] for values in [[float(metrics(c.sum(axis=0),metric)) for c in cell]]}
    report={'model_calls':0,'gold_changed':False,'inputs':{k:{'path':v,'sha256':hashlib.sha256(Path(v).read_bytes()).hexdigest()} for k,v in paths.items()},
            'f1_family':results,'rag_secondary_family':secondary,'seed_descriptive':descriptive}
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'comparisons.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
