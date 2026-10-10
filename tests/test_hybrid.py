import unittest
import numpy as np
from src.fantasy.hybrid import hybrid_shots


class HybridTests(unittest.TestCase):
    def test_context_and_calibration_compose(self):
        self.assertAlmostEqual(hybrid_shots(3, .9, 1.1)[0], 2.97)

    def test_missing_inputs_and_true_zeros(self):
        mean, rate, context = hybrid_shots(np.nan, .9, np.nan, fallback=2)
        self.assertAlmostEqual(mean, 1.8)
        self.assertEqual(rate, 'pregame_position_prior')
        self.assertEqual(context, 'missing_neutral_factor')
        self.assertEqual(hybrid_shots(0, .9, 1.1, fallback=2)[0], 0)
        with self.assertRaises(ValueError):
            hybrid_shots(np.nan, .9, 1)

if __name__ == '__main__':
    unittest.main()
