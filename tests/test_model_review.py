import unittest

import pandas as pd

from scripts.write_october_13_review import clustered_difference


class ModelReviewTests(unittest.TestCase):
    def sample(self):
        # Two appearances in one game and one in another: weighting matters.
        rows = []
        for game, player, trial in [(1, 10, 2.), (1, 11, 2.), (2, 12, 0.)]:
            for model, error in [('default', 1.), ('candidate', trial)]:
                rows.append(dict(game_id=game, player_id=player, model=model, absolute_error=error))
        return pd.DataFrame(rows)

    def test_clustered_comparison_retains_appearance_weights(self):
        result = clustered_difference(self.sample(), 'test').set_index('model')
        self.assertAlmostEqual(result.loc['candidate', 'mae_delta_vs_default'], 1/3)
        self.assertEqual(result.loc['candidate', 'appearances'], 3)
        self.assertEqual(result.loc['candidate', 'games'], 2)
        self.assertEqual(result.loc['candidate', 'games_improved'], 1)
        self.assertEqual(result.loc['default', 'lower_95'], 0.)
        self.assertEqual(result.loc['default', 'upper_95'], 0.)

    def test_incomplete_model_pairing_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'share every scored appearance'):
            clustered_difference(self.sample().iloc[:-1], 'test')


if __name__ == '__main__':
    unittest.main()
