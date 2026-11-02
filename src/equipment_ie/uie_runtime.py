"""Tokenizer and native UIE decoding helpers; importing does not load a model."""
import math
from equipment_ie.uie_adapter import SCHEMA_MAP, native_to_global, resolve_predictions

INPUT_KEYS = ('input_ids', 'token_type_ids', 'position_ids', 'attention_mask')


def encode_pair(tokenizer, prompt, text):
    return tokenizer(text=prompt, text_pair=text, truncation=False,
                     return_offsets_mapping=True, return_attention_mask=True,
                     return_position_ids=True)


def pad_inputs(tokenizer, encoded, length=512):
    size = len(encoded['input_ids'])
    if size > length:
        raise ValueError('Silent truncation forbidden')
    return {key: list(encoded[key])+[tokenizer.pad_token_id if key == 'input_ids' else 0]*(length-size)
            for key in INPUT_KEYS}


def decode_native(text, encoded, start_probs, end_probs, span_pairer, threshold=.5):
    """Use PaddleNLP's native pairing; offsets always refer to the content pair."""
    size = len(encoded['input_ids'])
    if len(start_probs) < size or len(end_probs) < size:
        raise ValueError('Probability array shorter than input')
    if any(not math.isfinite(float(p)) or not 0 <= p <= 1 for p in list(start_probs)+list(end_probs)):
        raise ValueError('Invalid probability array')
    starts = [(i, float(p)) for i, p in enumerate(start_probs[:size]) if p > threshold]
    ends = [(i, float(p)) for i, p in enumerate(end_probs[:size]) if p > threshold]
    decoded, invalid = [], []
    for (a, pa), (b, pb) in sorted(span_pairer(starts, ends, with_prob=True)):
        offsets, types = encoded['offset_mapping'], encoded['token_type_ids']
        if a > b or types[a] != 1 or types[b] != 1 or not offsets[a][1] or not offsets[b][1]:
            invalid.append({'start_token': a, 'end_token': b, 'reason': 'not_a_content_span'})
            continue
        s, e = offsets[a][0], offsets[b][1]
        if not 0 <= s < e <= len(text):
            invalid.append({'start_token': a, 'end_token': b, 'reason': 'invalid_content_offset'})
            continue
        decoded.append({'start': s, 'end': e, 'text': text[s:e], 'probability': pa*pb})
    return decoded, invalid


def merge_window_outputs(text, outputs):
    candidates, invalid = [], []
    for item in outputs:
        accepted, rejected = native_to_global(text, item['window'], {item['prompt']: item['native']})
        candidates.extend(accepted)
        invalid.extend(rejected)
        invalid.extend(item.get('decoder_invalid', []))
    result, dropped = resolve_predictions(candidates)
    return result, invalid, dropped


def require_authority(config, *, dry_run=False):
    phase = config.get('phase')
    if phase not in ('dev_pilot', 'formal'):
        raise RuntimeError('Unknown phase')
    query = config.get('query_path', '')
    if phase == 'dev_pilot' and query != '/root/autodl-tmp/data/domain_dev.jsonl':
        raise RuntimeError('Pilot may only read domain_dev')
    if phase == 'formal' and query != '/root/autodl-tmp/data/domain_test.jsonl':
        raise RuntimeError('Formal query path mismatch')
    if config.get('schema_mapping') != SCHEMA_MAP or config.get('position_prob') != .5:
        raise RuntimeError('Schema/threshold lock mismatch')
    if config.get('max_seq_len') != 512:
        raise RuntimeError('Context lock mismatch')
    if config.get('window_max_chars') != 400 or config.get('window_overlap_chars') != 64:
        raise RuntimeError('Window lock mismatch')
    if not config.get('input_sha256'):
        raise RuntimeError('Frozen input hash locks required')
    if phase == 'dev_pilot' and config.get('query_limit') != 20:
        raise RuntimeError('Pilot limited to first20 dev rows')
    ex = config.get('execution', {})
    recheck_gate = 'ROUND2_UIE_DEV_PILOT_LOADER_RECHECK_APPROVED_20261012'
    if ex.get('human_gate') == recheck_gate:
        if phase != 'dev_pilot' or config.get('mode') not in ('zero_shot', 'learning_sanity') or config.get('seed') != 42:
            raise RuntimeError('Loader recheck gate is only dev20/seed42 zero or learning sanity')
        if config['mode'] == 'learning_sanity' and config.get('sanity_steps') != 30:
            raise RuntimeError('Loader recheck learning sanity is locked to30 updates')
    if dry_run:
        return
    expected = {'ROUND2_UIE_DEV_PILOT_APPROVED_20261010', recheck_gate} if phase == 'dev_pilot' else {'ROUND2_UIE_FORMAL_APPROVED_20261010'}
    if ex.get('authorized') is not True or ex.get('model_calls_allowed') is not True or ex.get('human_gate') not in expected:
        raise RuntimeError('New exact human gate required; no model calls permitted')
