import unittest
import numpy as np
import pandas as pd
from src.fantasy.game_calibration import apply_calibration, fit_calibration, shot_error_components


def rows():
    return pd.DataFrame(dict(game_id=[1,1,1], player_id=[1,2,3], appeared=[True,True,False],
        shots_if_plays=[4.,2.,100.], shots=[2.,1.,np.nan],
        assists_if_plays=[1.,1.,100.], assists=[1.,0.,np.nan],
        goals_if_plays=[.4,.2,np.nan], points_if_plays=[1.4,1.2,np.nan],
        toi_minutes_if_plays=[20.,10.,15.], toi_minutes=[10.,10.,np.nan],
        injury_status=['ACTIVE','OUT',None], probability_of_playing=[np.nan]*3))


class CalibrationTests(unittest.TestCase):
    def test_shrinkage_and_absent_player_exclusion(self):
        fitted = fit_calibration(rows(), prior_expected_events=6)
        self.assertAlmostEqual(fitted['shots']['multiplier'], .75)
        self.assertEqual(fitted['shots']['player_games'], 2)
        duplicate = pd.concat([rows(), rows().iloc[[0]]], ignore_index=True)
        with self.assertRaises(ValueError):
            fit_calibration(duplicate)

    def test_candidate_preserves_unknowns_goals_and_baseline(self):
        source = rows()
        result = apply_calibration(source, fit_calibration(source))
        pd.testing.assert_series_equal(result.goals_if_plays, source.goals_if_plays)
        self.assertTrue(result.probability_of_playing.isna().all())
        self.assertTrue(np.isnan(result.points_if_plays.iloc[2]))
        np.testing.assert_allclose(result.points_if_plays, result.goals_if_plays + result.assists_if_plays)
        np.testing.assert_allclose(result.baseline_shots_if_plays, source.shots_if_plays)
        self.assertEqual(result.lineup_review_required.tolist(), [False,True,True])

    def test_decomposition_reconciles_exactly(self):
        result = shot_error_components(rows())
        np.testing.assert_allclose(result.shot_error_toi_component + result.shot_error_rate_residual,
                                   result.shots_if_plays-result.shots)


if __name__ == '__main__':
    unittest.main()
