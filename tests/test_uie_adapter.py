import unittest
from equipment_ie.uie_adapter import character_windows, native_training_rows, native_to_global, resolve_predictions


class UIEAdapterTest(unittest.TestCase):
    def test_window_complete_coverage(self):
        text = '中A😀 ' * 250
        windows = character_windows(text, lambda s: len(s) <= 350)
        self.assertEqual(windows[0]['start'], 0)
        self.assertEqual(windows[-1]['end'], len(text))
        self.assertTrue(all(x['text'] == text[x['start']:x['end']] for x in windows))
        self.assertTrue(all(b['start'] < a['end'] for a, b in zip(windows, windows[1:])))

    def test_budget_too_small_blocks(self):
        with self.assertRaises(ValueError):
            character_windows('中'*500, lambda s: len(s) <= 20)

    def test_negative_schema_rows(self):
        record = {'id': 'x', 'text': '雷达', 'entities': [{'start': 0, 'end': 2, 'type': 'EQUIPMENT', 'span': '雷达'}]}
        rows, missing, _ = native_training_rows(record, [{'start': 0, 'end': 2, 'text': '雷达'}])
        self.assertEqual(len(rows), 4)
        self.assertEqual(sum(not r['result_list'] for r in rows), 3)
        self.assertFalse(missing)

    def test_partial_gold_never_negative(self):
        record = {'id': 'x', 'text': 'abc雷达xyz', 'entities': [{'start': 3, 'end': 5, 'type': 'MODULE', 'span': '雷达'}]}
        rows, missing, skipped = native_training_rows(record, [{'start': 0, 'end': 4, 'text': 'abc雷'}])
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(missing), 1)
        self.assertEqual(len(skipped), 1)

    def test_native_offset_not_surface_search(self):
        text = '雷达，雷达'
        result, invalid = native_to_global(text, {'start': 3, 'end': 5, 'text': '雷达'}, {'装备': [{'start': 0, 'end': 2, 'text': '雷达', 'probability': .8}]})
        self.assertFalse(invalid)
        self.assertEqual(result[0]['start'], 3)

    def test_invalid_slice_preserved(self):
        output, invalid = native_to_global('雷达', {'start': 0, 'text': '雷达'}, {'装备': [{'start': 0, 'end': 1, 'text': '雷达', 'probability': .8}]})
        self.assertFalse(output)
        self.assertEqual(len(invalid), 1)

    def test_overlap_dedup_and_no_product_threshold(self):
        candidates = [{'start': 0, 'end': 2, 'type': 'MODULE', 'span': '雷达', 'probability': .36},
                      {'start': 0, 'end': 2, 'type': 'MODULE', 'span': '雷达', 'probability': .4},
                      {'start': 0, 'end': 1, 'type': 'EQUIPMENT', 'span': '雷', 'probability': .3}]
        result, dropped = resolve_predictions(candidates)
        self.assertEqual(result[0]['type'], 'MODULE')
        self.assertEqual(len(dropped), 2)
        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()
