import unittest
import numpy as np
from scripts.analyze_round2_comparisons import COMPARISONS, holm, paired, metrics


class Round2StatisticsTest(unittest.TestCase):
    def test_family_locked(self):
        self.assertEqual(len(COMPARISONS),13)
        self.assertIn(('full','knn_g'),COMPARISONS)

    def test_identical_p_is_one(self):
        a=np.asarray([[1,2,3],[2,0,1]])
        result=paired(a,a,'f1',replicates=200)
        self.assertEqual(result['difference_left_minus_right'],0)
        self.assertEqual(result['p_two_sided'],1)
        self.assertEqual(result['ci95'],[0,0])

    def test_holm(self):
        np.testing.assert_allclose(holm([.01,.04,.03]),[.03,.06,.06])

    def test_swap_reverses_difference(self):
        a=np.asarray([[4,0,0],[3,0,1]]);b=np.asarray([[1,3,3],[1,2,3]])
        left=paired(a,b,'f1',replicates=200)
        right=paired(b,a,'f1',replicates=200)
        self.assertAlmostEqual(left['difference_left_minus_right'],-right['difference_left_minus_right'])
        self.assertAlmostEqual(left['p_two_sided'],right['p_two_sided'])

    def test_zero_denominator(self):
        self.assertEqual(float(metrics(np.array([0,0,0]),'f1')),0)


if __name__=='__main__':unittest.main()
