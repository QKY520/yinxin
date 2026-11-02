"""Run only on AutoDL; no model dependency."""
import unittest
from scripts.prepare_round2_nocard import historical_reasons, grams, containment, proportional_sample


class PreparationTest(unittest.TestCase):
    def row(self, i, n=200):
        return {'id': str(i), 'text': '技术文档内容' * (n//6), 'source_type': 'cmnee', 'source_split': 'train'}

    def test_quality_order_and_all_hits(self):
        row = self.row(0)
        row.update(source_type='patent', source_split='test', text='技术123456')
        self.assertEqual(historical_reasons(row), ['excluded_source_split:patent:test', 'consecutive_digits_ge6'])

    def test_five_digits_not_rejected(self):
        row = self.row(0)
        row['text'] = '型号12345'
        self.assertEqual(historical_reasons(row), [])

    def test_containment_and_short_text(self):
        self.assertEqual(containment(grams('abcdefghijk'), grams('abcdefghijk')), 1)
        self.assertEqual(containment(grams('abc'), grams('abc')), 0)

    def test_stratified_sample_reproducible(self):
        rows = [self.row(i, 100 if i < 30 else 200) for i in range(132)]
        a, q = proportional_sample(rows, 100, 17)
        b, _ = proportional_sample(list(reversed(rows)), 100, 17)
        self.assertEqual([r['id'] for r in a], [r['id'] for r in b])
        self.assertEqual(sum(q.values()), 100)
        self.assertEqual(len({r['id'] for r in a}), 100)

    def test_insufficient_blocks(self):
        with self.assertRaises(ValueError):
            proportional_sample([self.row(i) for i in range(99)], 100, 17)


if __name__ == '__main__':
    unittest.main()
