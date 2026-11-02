import unittest
from equipment_ie.uie_adapter import SCHEMA_MAP
from equipment_ie.uie_runtime import decode_native, merge_window_outputs, pad_inputs, require_authority


class UIERuntimeTest(unittest.TestCase):
    def config(self):
        return {'phase':'dev_pilot','query_path':'/root/autodl-tmp/data/domain_dev.jsonl', 'query_limit':20,
                'schema_mapping':SCHEMA_MAP,'position_prob':.5,'max_seq_len':512,
                'window_max_chars':400,'window_overlap_chars':64,'input_sha256':{'locked':'abc'},
                'execution':{'authorized':False,'model_calls_allowed':False,'human_gate':'NOT_GRANTED'}}

    def test_disabled_gate_cannot_execute(self):
        require_authority(self.config(),dry_run=True)
        with self.assertRaises(RuntimeError): require_authority(self.config())

    def test_pilot_cannot_read_test(self):
        cfg=self.config();cfg['query_path']='/root/autodl-tmp/data/domain_test.jsonl'
        with self.assertRaises(RuntimeError): require_authority(cfg,dry_run=True)

    def test_threshold_not_tunable_via_config(self):
        cfg=self.config();cfg['position_prob']=.7
        with self.assertRaises(RuntimeError): require_authority(cfg,dry_run=True)

    def recheck(self):
        cfg=self.config()
        cfg.update(mode='zero_shot',seed=42)
        cfg['execution']={'authorized':True,'model_calls_allowed':True,
                          'human_gate':'ROUND2_UIE_DEV_PILOT_LOADER_RECHECK_APPROVED_20261012'}
        return cfg

    def test_repaired_dev_recheck_gate_can_validate(self):
        require_authority(self.recheck())

    def test_recheck_gate_cannot_authorize_formal(self):
        cfg=self.recheck();cfg.update(phase='formal',query_path='/root/autodl-tmp/data/domain_test.jsonl')
        with self.assertRaises(RuntimeError): require_authority(cfg)

    def test_recheck_gate_cannot_expand_training_or_seed(self):
        cfg=self.recheck();cfg['mode']='finetune'
        with self.assertRaises(RuntimeError): require_authority(cfg)
        cfg=self.recheck();cfg['seed']=43
        with self.assertRaises(RuntimeError): require_authority(cfg)
        cfg=self.recheck();cfg.update(mode='learning_sanity',sanity_steps=31)
        with self.assertRaises(RuntimeError): require_authority(cfg)

    def test_no_silent_truncation(self):
        class Tokenizer: pad_token_id=0
        with self.assertRaises(ValueError): pad_inputs(Tokenizer(),{'input_ids':[1]*513})

    def test_native_product_no_extra_cutoff(self):
        enc={'input_ids':[0,1,2,3],'token_type_ids':[0,1,1,1], 'offset_mapping':[(0,0),(0,1),(1,2),(0,0)]}
        def pairer(s,e,with_prob): return {(s[0],e[0])}
        entities,bad=decode_native('雷达',enc,[0,.6,0,0],[0,0,.6,0],pairer)
        self.assertFalse(bad);self.assertEqual(entities[0]['text'],'雷达');self.assertAlmostEqual(entities[0]['probability'],.36)

    def test_prompt_spans_do_not_become_content(self):
        enc={'input_ids':[0,1],'token_type_ids':[0,1], 'offset_mapping':[(0,1),(0,1)]}
        def pairer(s,e,with_prob): return {(s[0],e[0])}
        entities,bad=decode_native('雷',enc,[.9,0],[.9,0],pairer)
        self.assertFalse(entities);self.assertEqual(len(bad),1)

    def test_nan_probabilities_stop(self):
        with self.assertRaises(ValueError): decode_native('a',{'input_ids':[1]},[float('nan')],[.8],None)

    def test_second_occurrence_merged_without_gold(self):
        raw={'window':{'start':3,'end':5,'text':'雷达'},'prompt':'装备','native':[{'start':0,'end':2,'text':'雷达','probability':.9}]}
        entities,bad,drops=merge_window_outputs('雷达，雷达',[raw,raw])
        self.assertFalse(bad);self.assertEqual(entities[0]['start'],3);self.assertEqual(len(drops),1)


if __name__ == '__main__': unittest.main()
