"""Locked Qwen resource, environment and original chat token checks; no models."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
import yaml
from transformers import AutoTokenizer

sys.path[:0] = ['/root/project/src', '/root/project/scripts']
import run_p3_extraction as historical
from equipment_ie.extraction import build_ner_prompt

ROOT = Path('/root/autodl-tmp/round2_formal_20261012_r3')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    audit = json.loads(Path('/root/autodl-tmp/round2_runtime_bundle_20261010_r3/qwen_reuse_audit.json').read_text())
    for item in audit['weights']:
        assert sha(item['path']) == item['sha256'], item
    freeze = subprocess.check_output(['/root/autodl-tmp/venvs/equipment-ie/bin/python', '-m', 'pip', 'freeze'], text=True)
    assert freeze == Path('/root/autodl-tmp/round2_uie_loader_repair_20261012_r1/qwen_freeze_before.txt').read_text()
    tokenizer = AutoTokenizer.from_pretrained('/root/autodl-tmp/models/qwen2.5-7b', local_files_only=True)
    budgets = {}
    for path in sorted((ROOT/'qwen/configs').glob('*.yaml')):
        cfg = yaml.safe_load(path.read_text())
        _, queries, examples, glossary, rag, *_ = historical.build_query_plan(config=cfg, config_path=path, dry_run=True)
        lengths = []
        for query in queries:
            assert not rag(query)
            prompt = build_ner_prompt(query_text=query['text'], entity_types=cfg['schema']['entity_types'],
                                     examples=examples(query), glossary_entries=glossary(query), rag_passages=[],
                                     include_relations=False, output_instruction=cfg['prompt']['output_instruction'], output_mode='occurrence')
            count = len(tokenizer.apply_chat_template([{'role': 'user', 'content': prompt}], tokenize=True, add_generation_prompt=True))
            lengths.append(count)
        assert len(lengths) == 170 and max(lengths)+768 <= 8192
        budgets[path.stem] = {'queries': 170, 'max_chat_tokens': max(lengths), 'max_with_generation': max(lengths)+768}
    report = {'model_resources_verified': len(audit['weights']), 'qwen_freeze_unchanged': True,
              'token_budgets': budgets, 'model_calls': 0,
              'first_probe_failure': 'Attempted dict access on string prompt; no model, corrected to original user-only chat'}
    with (ROOT/'qwen_preflight.json').open('x') as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
