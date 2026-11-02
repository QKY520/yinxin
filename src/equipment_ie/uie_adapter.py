"""UIE native char-offset adapter. No Paddle import or model execution here."""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping

SCHEMA_MAP = {'装备': 'EQUIPMENT', '部件模块': 'MODULE', '技术方案': 'TECH_SCHEME', '性能指标': 'METRIC'}


def character_windows(text: str, fits: Callable[[str], bool], *, max_chars: int = 400, overlap: int = 64):
    """Use text/token budgets only; no gold-aware boundaries or silent truncation."""
    if not text or not 0 < overlap < max_chars:
        raise ValueError('nonempty text and 0 < overlap < max_chars required')
    result, start = [], 0
    while start < len(text):
        end = min(start+max_chars, len(text))
        while end > start and not fits(text[start:end]):
            end -= 1
        if end <= start or (end < len(text) and end-start <= overlap):
            raise ValueError('token budget too small for progressing overlap windows')
        result.append({'start': start, 'end': end, 'text': text[start:end]})
        if end == len(text):
            break
        start = end-overlap
    return result


def native_training_rows(record: Mapping, windows: list[dict]):
    """One positive or negative example per schema/window. Original labels immutable.

    Reject partial-label windows instead of training cut-off entity fragments
    as negatives. Window boundaries themselves never use gold. Other overlapping
    windows can supply the full span; caller must audit coverage, never hide loss.
    """
    output, covered, skipped = [], set(), []
    for wi, window in enumerate(windows):
        a, b = window['start'], window['end']
        for prompt, kind in SCHEMA_MAP.items():
            gold = [e for e in record['entities'] if e['type'] == kind]
            partial = [e for e in gold if e['start'] < b and a < e['end'] and not (a <= e['start'] < e['end'] <= b)]
            if partial:
                skipped.append({'window': wi, 'type': kind, 'reason': 'partially_visible_gold'})
                continue
            entities = [e for e in gold if a <= e['start'] < e['end'] <= b]
            result_list = [{'start': e['start']-a, 'end': e['end']-a, 'text': e['span']} for e in entities]
            for e in entities:
                if window['text'][e['start']-a:e['end']-a] != e['span']:
                    raise ValueError('gold slicing mismatch')
                covered.add((e['start'], e['end'], e['type']))
            output.append({'content': window['text'], 'prompt': prompt, 'result_list': result_list,
                           'source_id': record['id'], 'window_start': a, 'window_end': b})
    missing = sorted({(e['start'], e['end'], e['type']) for e in record['entities']}-covered)
    return output, missing, skipped


def native_to_global(full_text: str, window: Mapping, result: Mapping):
    """Validate native start/end and probability. Never locate spans using gold."""
    output, invalid = [], []
    for prompt, values in result.items():
        if prompt not in SCHEMA_MAP or not isinstance(values, list):
            invalid.append({'prompt': prompt, 'reason': 'unknown_schema_or_invalid_list'})
            continue
        for value in values:
            try:
                s, e, p = value['start'], value['end'], float(value['probability'])
                if type(s) is not int or type(e) is not int or not 0 <= s < e <= len(window['text']):
                    raise ValueError('offset_range')
                if not math.isfinite(p) or not 0 <= p <= 1:
                    raise ValueError('probability')
                a, b = s+window['start'], e+window['start']
                if window['text'][s:e] != value['text'] or full_text[a:b] != value['text']:
                    raise ValueError('exact_slice')
                output.append({'start': a, 'end': b, 'type': SCHEMA_MAP[prompt], 'span': value['text'], 'probability': p})
            except (KeyError, TypeError, ValueError) as exc:
                invalid.append({'prompt': prompt, 'raw': value, 'reason': str(exc)})
    return output, invalid


def resolve_predictions(candidates: list[dict]):
    """Dedup and choose highest native probability for overlaps; deterministic ties.

    No gold/other-system predictions. Keep dropped candidates for audit.
    Probability threshold is on native start/end probabilities at UIE decoding,
    NOT an additional threshold on their product stored in probability.
    """
    ranked = sorted(candidates, key=lambda e: (-e['probability'], -(e['end']-e['start']), e['start'], e['end'], e['type']))
    accepted, dropped, seen = [], [], set()
    for entity in ranked:
        key = (entity['start'], entity['end'], entity['type'])
        if key in seen:
            dropped.append({'reason': 'duplicate_window_prediction', 'entity': entity})
        elif any(entity['start'] < other['end'] and other['start'] < entity['end'] for other in accepted):
            dropped.append({'reason': 'overlap_probability_policy', 'entity': entity})
        else:
            accepted.append(entity)
        seen.add(key)
    accepted.sort(key=lambda e: (e['start'], e['end'], e['type']))
    return [{k: e[k] for k in ['start', 'end', 'type', 'span']} for e in accepted], dropped
