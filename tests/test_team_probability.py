import unittest
import math
from src.fantasy.team_probability import scoring_win_probability


class ProbabilityTests(unittest.TestCase):
    def test_symmetry_and_complement(self):
        self.assertAlmostEqual(scoring_win_probability(3, 3), .5)
        self.assertAlmostEqual(scoring_win_probability(4, 2) + scoring_win_probability(2, 4), 1)
        self.assertGreater(scoring_win_probability(4, 2), .5)
        self.assertEqual(scoring_win_probability(0, 0), .5)
        self.assertAlmostEqual(scoring_win_probability(0, 3), .5 * math.exp(-3))

    def test_invalid(self):
        for x in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                scoring_win_probability(x, 3)
