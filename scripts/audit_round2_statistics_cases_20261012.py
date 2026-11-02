"""Independent weighted-count resampling, Holm, descriptive and case audit."""
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path
import numpy as np

ROOT = Path('/root/autodl-tmp/round2_statistics_cases_20261012_r1')
TYPES = ('EQUIPMENT', 'MODULE', 'TECH_SCHEME', 'METRIC')


def load(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def entity_keys(entities):
    return {(e['start'], e['end'], e['type']) for e in entities}


def score(counts, metric):
    tp, fp, fn = counts
    if metric == 'fp':
        return float(fp)
    numerator, denominator = {'f1': (2*tp, 2*tp+fp+fn), 'precision': (tp, tp+fp), 'recall': (tp, tp+fn)}[metric]
    return float(numerator/denominator) if denominator else 0.


def independent_pair(left, right, metric, seed):
    rng = np.random.default_rng(seed)
    n = len(left)
    observed = score(left.sum(axis=0), metric)-score(right.sum(axis=0), metric)
    bootstrap, extreme = [], 0
    both = left.sum(axis=0)+right.sum(axis=0)
    # Reproduce the frozen RNG schedule, but aggregate via per-text weights
    # and matrix products rather than the production indexed/swap arrays.
    for _ in range(100):
        indices = rng.integers(0, n, size=(100, n))
        multiplicities = np.stack([np.bincount(sample, minlength=n) for sample in indices])
        boot_left, boot_right = multiplicities@left, multiplicities@right
        bootstrap.extend(score(a, metric)-score(b, metric) for a,b in zip(boot_left, boot_right))
        swap = rng.integers(0, 2, size=(100, n))
        first = swap@left+(1-swap)@right
        for a in first:
            delta = score(a, metric)-score(both-a, metric)
            extreme += abs(delta) >= abs(observed)-1e-12
    return {'difference_left_minus_right': observed, 'ci95': np.quantile(bootstrap, [.025,.975]).tolist(),
            'p_two_sided': (extreme+1)/10001, 'replicates': 10000}


def adjusted(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    output, ceiling = [None]*len(values), 0.
    for rank, i in enumerate(order):
        ceiling = max(ceiling, min(1., values[i]*(len(values)-rank)))
        output[i] = ceiling
    return output


def compare_numbers(actual, expected):
    for key in ('difference_left_minus_right', 'p_two_sided'):
        assert math.isclose(actual[key], expected[key], abs_tol=1e-12), (key, actual, expected)
    assert np.allclose(actual['ci95'], expected['ci95'], atol=1e-12, rtol=0)
    assert actual['replicates'] == expected['replicates'] == 10000


def write_csv(path, data):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    for path, digest in load(ROOT/'input_code_locks.json').items():
        assert sha(path) == digest, path
    report = load(ROOT/'statistics/comparisons.json')
    protocol = load(ROOT/'frozen_statistics_protocol.json')
    assert [(r['left'], r['right']) for r in report['f1_family']] == [tuple(pair) for pair in protocol['f1_family']]
    assert [r['metric'] for r in report['rag_secondary_family']] == protocol['rag_secondary_family']
    inputs = load(ROOT/'inputs.json')
    records = {name: rows(path) for name,path in inputs.items()}
    arrays, raw, typed = {}, [], {}
    for name, data in records.items():
        assert report['inputs'][name]['sha256'] == sha(inputs[name])
        counts, per_type = [], {t: np.zeros(3, dtype='int64') for t in TYPES}
        for row in data:
            g, p = entity_keys(row['gold']['entities']), entity_keys(row['pred_raw']['entities'])
            if row['parse_failure']:
                assert not p
            common, extra, missing = g&p, p-g, g-p
            counts.append([len(common), len(extra), len(missing)])
            for t in TYPES:
                per_type[t] += [sum(e[2] == t for e in keys) for keys in (common, extra, missing)]
        arrays[name] = np.asarray(counts, dtype='int64')
        sums = arrays[name].sum(axis=0)
        assert int(sums[0]+sums[2]) == 954
        raw.append({'system': name, 'texts': 170, 'tp': int(sums[0]), 'fp': int(sums[1]), 'fn': int(sums[2]),
                    'precision': score(sums, 'precision'), 'recall': score(sums, 'recall'), 'f1': score(sums, 'f1'),
                    'predicted_entities': int(sums[0]+sums[1]), 'parse_failures': sum(r['parse_failure'] for r in data)})
        typed[name] = {t: {'tp': int(c[0]), 'fp': int(c[1]), 'fn': int(c[2]),
                          **{m: score(c, m) for m in ('precision','recall','f1')}} for t,c in per_type.items()}
    comparisons = []
    for i, result in enumerate(report['f1_family']):
        check = independent_pair(arrays[result['left']], arrays[result['right']], 'f1', 20261010+i)
        compare_numbers(check, result)
    for result, corrected in zip(report['f1_family'], adjusted([r['p_two_sided'] for r in report['f1_family']])):
        assert math.isclose(result['p_holm_13'], corrected, abs_tol=1e-12)
        baseline = score(arrays[result['right']].sum(axis=0), 'f1')
        comparisons.append({**result, 'ci95_low': result['ci95'][0], 'ci95_high': result['ci95'][1],
                            'relative_f1_change_percent': 100*result['difference_left_minus_right']/baseline if baseline else None})
    for i, result in enumerate(report['rag_secondary_family']):
        compare_numbers(independent_pair(arrays['full'], arrays['knn_g'], result['metric'], 20262010+i), result)
    for result, corrected in zip(report['rag_secondary_family'], adjusted([r['p_two_sided'] for r in report['rag_secondary_family']])):
        assert math.isclose(result['p_holm_3'], corrected, abs_tol=1e-12)
    for group in ('random', 'uie_ft'):
        for metric in ('precision', 'recall', 'f1', 'fp'):
            values = [score(arrays[group+str(seed)].sum(axis=0), metric) for seed in (42,43,44)]
            actual = report['seed_descriptive'][group][metric]
            assert math.isclose(actual['mean'], statistics.mean(values), abs_tol=1e-12)
            assert math.isclose(actual['sample_sd'], statistics.stdev(values), abs_tol=1e-12)
    summary = load(ROOT/'cases/rag_cases.json')
    events = rows(ROOT/'cases/all_paired_differences.jsonl')
    assert len(events) == 170
    categories = ['FP_removed_by_set_difference', 'TP_lost_new_FN', 'new_FP', 'unchanged_control']
    for event, a, b in zip(events, records['full'], records['knn_g']):
        assert event['id'] == a['id'] == b['id']
        g = entity_keys(a['gold']['entities'])
        x, y = entity_keys(a['pred_raw']['entities']), entity_keys(b['pred_raw']['entities'])
        expected = [label for label,flag in zip(categories, [bool((y-x)-g),bool((y-x)&g),bool((x-y)-g),x==y]) if flag]
        assert event['categories'] == expected
        assert event['gold'] == a['gold']['entities'] and event['text'] == a['gold']['text']
        assert event['full'] == a['pred_raw']['entities'] and event['knn_g'] == b['pred_raw']['entities']
        assert event['actual_rag_passage_ids'] == a['rag_passage_ids'] and event['actual_rag_passages'] == a['rag_passages']
    for category in categories:
        matching = sorted((e for e in events if category in e['categories']), key=lambda e: e['id'])
        assert summary['counts'][category] == len(matching)
        assert summary['selected'][category] == (matching[0] if matching else None)
    write_csv(ROOT/'raw_metrics_14_systems.csv', raw)
    write_csv(ROOT/'f1_comparisons_13.csv', comparisons)
    write_csv(ROOT/'rag_secondary_3.csv', report['rag_secondary_family'])
    with (ROOT/'metrics_and_independent_validation.json').open('x') as f:
        json.dump({'status': 'PASS', 'raw_table': raw, 'per_type': typed, 'statistics_independently_replayed': 16,
                   'bootstrap_and_randomization_replicates': 10000, 'paired_original_texts': 170,
                   'holm_families': [13,3], 'seed_descriptive': report['seed_descriptive'],
                   'case_category_counts': summary['counts'], 'selected_case_ids': {k: None if v is None else v['id'] for k,v in summary['selected'].items()},
                   'model_calls': 0, 'paper_changed': False}, f, ensure_ascii=False, indent=2)
    print(json.dumps({'status': 'PASS', 'raw_table': raw, 'case_counts': summary['counts'],
                      'seed_descriptive': report['seed_descriptive'], 'model_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
