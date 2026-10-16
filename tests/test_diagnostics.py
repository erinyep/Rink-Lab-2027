import unittest
import pandas as pd
from src.fantasy.diagnostics import defense_opportunity, shot_contributions


class DiagnosticsTests(unittest.TestCase):
    def test_target_day_never_enters_defense_inputs(self):
        g = pd.DataFrame([
            dict(game_id=1, player_id=1, game_date='2026-10-12', team='A', position='D', shots=2, assists=1, toi_seconds=1200),
            dict(game_id=1, player_id=2, game_date='2026-10-12', team='A', position='C', shots=3, assists=0, toi_seconds=900),
            dict(game_id=2, player_id=1, game_date='2026-10-13', team='A', position='D', shots=99, assists=99, toi_seconds=1200)])
        r = defense_opportunity(g, '2026-10-13').iloc[0]
        self.assertEqual(r.defense_shots_per_game, 2)
        self.assertEqual(r.defense_shot_share, .4)
        self.assertEqual(r.defense_shots_per60_player_minutes, 6)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            defense_opportunity(pd.concat([g, g]), '2026-10-13')

    def test_contributions_telescope_and_distinguish_rate_from_toi(self):
        c = pd.DataFrame([dict(baseline_toi_minutes=10, baseline_shots=2,
            usage_toi_minutes=20, usage_shots_before_context=3, blended_sog_factor=1.2)])
        r = shot_contributions(c, .9).iloc[0]
        self.assertAlmostEqual(r.toi_contribution, 2)
        self.assertAlmostEqual(r.shot_rate_contribution, -1)
        self.assertAlmostEqual(r.reconstructed_usage_shots, 3.24)


if __name__ == '__main__':
    unittest.main()
