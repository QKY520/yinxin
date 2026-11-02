"""No-card human-readable tables and four distinct deterministic real cases."""
import hashlib
import json
from pathlib import Path

ROOT = Path('/root/autodl-tmp/round2_statistics_cases_20261012_r1')
LABELS = {'zero': 'Qwen零样本', 'bm25': 'BM25-only', 'dense': 'dense RAG-only', 'full': 'Full（历史复用）',
          'glossary': 'glossary-only', 'random42': 'random5示例seed42', 'random43': 'random5示例seed43',
          'random44': 'random5示例seed44', 'knn': 'kNN5', 'knn_g': 'kNN5+词表', 'uie_zs': 'UIE零样本',
          'uie_ft42': 'UIE FT30 seed42', 'uie_ft43': 'UIE FT30 seed43', 'uie_ft44': 'UIE FT30 seed44'}
CATEGORIES = {'FP_removed_by_set_difference': 'Full少预测了kNN+词表的错误实体',
              'TP_lost_new_FN': 'Full漏掉了kNN+词表原本正确的实体', 'new_FP': 'Full新增错误实体',
              'unchanged_control': '两条件预测相同的对照'}


def load(path):
    return json.loads(path.read_text())


def keys(entities):
    return {(e['start'], e['end'], e['type']) for e in entities}


def dump(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def entity_lines(entities):
    return '\n'.join(f"- [{e['start']},{e['end']}) {e['type']}：{e['span']}" for e in entities) or '（空）'


def main():
    assert not list(Path('/dev').glob('nvidia[0-9]*'))
    validated = load(ROOT/'metrics_and_independent_validation.json')
    assert validated['status'] == 'PASS'
    stats = load(ROOT/'statistics/comparisons.json')
    lines = ['# 第二轮统计证据汇总（无模型分析）', '',
             '同一冻结test170、954个gold实体；旧失败行保留，所有种子保留。独立重算16项通过。', '',
             '| 系统 | TP | FP | FN | P | R | F1 | 解析失败 |', '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in validated['raw_table']:
        lines.append(f"| {LABELS[row['system']]} | {row['tp']} | {row['fp']} | {row['fn']} | {row['precision']:.6f} | {row['recall']:.6f} | {row['f1']:.6f} | {row['parse_failures']} |")
    lines += ['', '## 预定13项F1检验族', '', '差值为左−右；CI是10000次文本配对bootstrap的边际95%CI，p为双侧配对随机化、13项Holm校正。CI未作多重性校正。', '',
              '| 左 | 右 | ΔF1 | 95%CI | 原p | Holm p |', '| --- | --- | ---: | --- | ---: | ---: |']
    for row in stats['f1_family']:
        lines.append(f"| {LABELS[row['left']]} | {LABELS[row['right']]} | {row['difference_left_minus_right']:.6f} | [{row['ci95'][0]:.6f}, {row['ci95'][1]:.6f}] | {row['p_two_sided']:.6f} | {row['p_holm_13']:.6f} |")
    lines += ['', '## 独立3项RAG次要终点族', '', '比较Full−kNN5+词表；P/R差值是比例，FP差值是实体数。3项单独Holm校正。', '',
              '| 终点 | 差值 | 95%CI | 原p | Holm p |', '| --- | ---: | --- | ---: | ---: |']
    for row in stats['rag_secondary_family']:
        lines.append(f"| {row['metric']} | {row['difference_left_minus_right']:.6f} | [{row['ci95'][0]:.6f}, {row['ci95'][1]:.6f}] | {row['p_two_sided']:.6f} | {row['p_holm_3']:.6f} |")
    lines += ['', '## 三种子描述汇总', '', '仅描述，不把三次同一文本视作510个独立样本。sample SD使用ddof=1。', '',
              '| 组别 | F1均值 | 样本SD |', '| --- | ---: | ---: |']
    for group in ('random', 'uie_ft'):
        entry = stats['seed_descriptive'][group]['f1']
        lines.append(f"| {group} | {entry['mean']:.6f} | {entry['sample_sd']:.6f} |")
    lines += ['', '## 支持边界', '',
              'Full相对zero/BM25/dense/glossary/UIE零样本，以及random42相对zero的F1通过13项校正检验。',
              'kNN−random42、词表−kNN、Full−kNN+词表、Full−random42、Full−kNN、Full−UIE微调seed42均未达到校正后显著。',
              'RAG的精确率和FP改善获得支持；召回率下降只有描述性证据。本轮不能写成RAG显著提高F1、全面优于微调NER、等价或不劣。',
              'BM25/dense沿用各自历史语料政策，不能改写成同一语料检索算法优劣。结果局限于本设备域小数据集。', '']
    with (ROOT/'EVIDENCE_REPORT.md').open('x') as f:
        f.write('\n'.join(lines))
    events = [json.loads(s) for s in (ROOT/'cases/all_paired_differences.jsonl').read_text().splitlines()]
    used, selected = set(), {}
    for category in CATEGORIES:
        candidates = sorted((e for e in events if category in e['categories'] and e['id'] not in used), key=lambda e:e['id'])
        assert candidates, category
        selected[category] = candidates[0]
        used.add(candidates[0]['id'])
    assert len(used) == 4
    # This supplements the preserved predeclared first-ID-per-category file.
    # It changes presentation only, never the tests or category membership.
    dump(ROOT/'cases/distinct_four_cases.json', {'selection': 'fixed category order, first lexicographic unused ID; original selection preserved',
                                              'model_calls': 0, 'not_a_causal_mechanism_proof': True, 'selected': selected})
    case_lines = ['# 四条不同文本的真实RAG成对案例', '',
                  '保留原first-ID-per-category选择。下列补充展示依固定类别顺序选择首个未使用ID，四条不同文本，不按效果大小挑选。',
                  '集合差异不意味着显式删除算法，也不证明检索片段与输出变化的内部因果机制。', '']
    for category, event in selected.items():
        gold, full, other = keys(event['gold']), keys(event['full']), keys(event['knn_g'])
        for array in (event['gold'], event['full'], event['knn_g']):
            assert all(event['text'][e['start']:e['end']] == e['span'] for e in array)
        if category == 'FP_removed_by_set_difference':
            changed = [e for e in event['knn_g'] if (e['start'],e['end'],e['type']) in (other-full)-gold]
        elif category == 'TP_lost_new_FN':
            changed = [e for e in event['knn_g'] if (e['start'],e['end'],e['type']) in (other-full)&gold]
        elif category == 'new_FP':
            changed = [e for e in event['full'] if (e['start'],e['end'],e['type']) in (full-other)-gold]
        else:
            changed = []
            assert full == other
        case_lines += [f"## {CATEGORIES[category]}：{event['id']}", '',
                       f"该文本可属于多个类别：{', '.join(event['categories'])}", '', '原文：', event['text'], '',
                       '本类别对应的实际差异实体：', entity_lines(changed), '', 'Gold：', entity_lines(event['gold']), '',
                       'Full实际输出：', entity_lines(event['full']), '', 'kNN+词表实际输出：', entity_lines(event['knn_g']), '',
                       'Full实际检索片段（逐字保留）：', '']
        for pid, passage in zip(event['actual_rag_passage_ids'], event['actual_rag_passages']):
            case_lines += [f'检索ID：{pid}', '', passage, '']
    with (ROOT/'cases/FOUR_DISTINCT_REAL_CASES.md').open('x') as f:
        f.write('\n'.join(case_lines))
    dump(ROOT/'presentation_provenance.json', {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                             'distinct_case_ids': {k:v['id'] for k,v in selected.items()}, 'model_calls': 0})
    print(json.dumps({'report': str(ROOT/'EVIDENCE_REPORT.md'), 'distinct_case_ids': {k:v['id'] for k,v in selected.items()}, 'model_calls': 0}))


if __name__ == '__main__':
    main()
