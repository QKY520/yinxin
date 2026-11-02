#!/usr/bin/env python3
"""Perfect synthetic token scores roundtrip; NO UIE model, forward, or test labels."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from equipment_ie.schema import iter_jsonl
from equipment_ie.uie_runtime import encode_pair, decode_native, merge_window_outputs


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    from paddlenlp.transformers import AutoTokenizer
    from paddlenlp.utils.tools import get_span
    stage=Path('/root/autodl-tmp/round2_uie_nocard_20261010')
    tokenizer=AutoTokenizer.from_pretrained('/root/autodl-tmp/models/uie-base-round2-official')
    report={'model_calls':0,'model_instantiated':False,'synthetic_scores_not_model_results':True,'splits':{}}
    for split in ['support','dev']:
        records=list(iter_jsonl(f'/root/autodl-tmp/data/domain_{split}.jsonl'))
        native=[json.loads(s) for s in (stage/'prepared_data'/f'{split}_native.jsonl').read_text().splitlines()]
        features=[json.loads(s) for s in (stage/'prepared_data'/f'{split}_features512.jsonl').read_text().splitlines()]
        gathered={r['id']:[] for r in records}
        for row,feature in zip(native,features):
            encoded=encode_pair(tokenizer,row['prompt'],row['content'])
            pred,bad=decode_native(row['content'],encoded,feature['start_positions'],feature['end_positions'],get_span)
            assert not bad
            gathered[row['source_id']].append({'window':{'start':row['window_start'],'end':row['window_end'],'text':row['content']},
                'prompt':row['prompt'],'native':pred})
        for r in records:
            pred,bad,_=merge_window_outputs(r['text'],gathered[r['id']])
            assert not bad
            assert {(e['start'],e['end'],e['type']) for e in pred}=={(e['start'],e['end'],e['type']) for e in r['entities']}
        report['splits'][split]={'source_rows':len(records),'gold_entities':sum(len(r['entities']) for r in records),'native_feature_decoder_roundtrip':'PASS'}
    with (stage/'native_token_roundtrip.json').open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))


if __name__=='__main__':main()
