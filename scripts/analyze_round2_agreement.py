#!/usr/bin/env python3
"""Text-paired annotation bootstrap only; no semantic relabeling or identity certification."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

BASE=Path('/root/autodl-tmp/round2_submission_check_20261010')
OUT=Path('/root/autodl-tmp/round2_agreement_ci_20261010')
MAP=Path('/root/autodl-tmp/round2_nocard_preparation_20261010/calibration100/coordinator_only/coordinator_map.jsonl')
TYPES=['ALL','EQUIPMENT','MODULE','TECH_SCHEME','METRIC']
HASHES={'a':'8ccb7bda38205a53ed8968fb91a7393bd455ced149c5f68a5e3941c7a8695062','b':'19274b874c10c914deb5f6018ab07ea4ad63ce8baedb60afa7e76871a892050b'}


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    verified=json.loads((BASE/'independent_verification.json').read_text())
    assert verified['numeric_verdict']=='PASS' and not verified['errors']
    mapping=[json.loads(s) for s in MAP.read_text().splitlines()]
    annotations={}
    for role in ['a','b']:
        path=BASE/f'annotator_{role}_100_firstpass.csv'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==HASHES[role]
        with path.open(encoding='utf-8-sig',newline='') as f:
            annotations[role]={r['blind_id']:{(e['start'],e['end'],e['type']) for e in json.loads(r['entities_json'])} for r in csv.DictReader(f)}
    counts=[]
    for row in mapping:
        a,b=annotations['a'][row['a_blind_id']],annotations['b'][row['b_blind_id']]
        counts.append([[len(a) if t=='ALL' else sum(x[2]==t for x in a),len(b) if t=='ALL' else sum(x[2]==t for x in b),
                        len(a&b) if t=='ALL' else sum(x[2]==t for x in a&b)] for t in TYPES])
    counts=np.asarray(counts,dtype='int64')
    rng=np.random.default_rng(20261010)
    boot=np.empty((10000,len(TYPES)))
    zeros=np.zeros(len(TYPES),dtype='int64')
    for begin in range(0,10000,100):
        totals=counts[rng.integers(0,100,size=(100,100))].sum(axis=1)
        denom=totals[:,:,0]+totals[:,:,1]
        zeros+=(denom==0).sum(axis=0)
        boot[begin:begin+100]=np.divide(2*totals[:,:,2],denom,out=np.zeros_like(denom,dtype=float),where=denom!=0)
    total=counts.sum(axis=0)
    report={'texts':100,'model_calls':0,'labels_changed':False,'bootstrap_replicates':10000,'seed':20261010,
            'sampling_unit':'paired complete text with both annotations','ci':'percentile95','zero_denominator_rule':'F1=0; count replicates explicitly',
            'source_hashes':HASHES,'author_statement':'Two human annotators; some AI questions were asked. Numerical/file audit does not certify the annotation process.',
            'scope':'new non-test calibration; not frozen-test IAA','results':{}}
    for i,t in enumerate(TYPES):
        a,b,m=map(int,total[i]);lo,hi=np.quantile(boot[:,i],[.025,.975])
        report['results'][t]={'a':a,'b':b,'matched':m,'f1':2*m/(a+b) if a+b else 0,'ci95':[float(lo),float(hi)],'zero_denominator_replicates':int(zeros[i])}
    assert report['results']['ALL']['matched']==509
    OUT.mkdir(exist_ok=False)
    (OUT/'agreement_ci.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    with (OUT/'per_text_counts.jsonl').open('x') as f:
        for row,values in zip(mapping,counts):f.write(json.dumps({'id':row['id'],'counts':values.tolist()})+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
