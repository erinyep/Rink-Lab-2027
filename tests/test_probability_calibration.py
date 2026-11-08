import unittest
import numpy as np
import pandas as pd
from src.fantasy.probability_calibration import fit_probability_calibration, calibrated_probability, reliability_table


class ProbabilityCalibrationTests(unittest.TestCase):
    def rows(self):
        return pd.DataFrame(dict(game_id=range(40),date=[f'2026-10-{d:02}' for d in range(1,9) for _ in range(5)],
                                 probability=[.3,.4,.5,.6,.7]*8,actual_home_win=[0,0,1,1,1]*8))

    def test_future_outcomes_never_enter_training(self):
        r=self.rows();a=fit_probability_calibration(r,'2026-10-08')
        b=fit_probability_calibration(r[r.date.lt('2026-10-08')],'2026-10-08')
        self.assertEqual(a,b)
        self.assertEqual(a['games'],35)
        with self.assertRaisesRegex(ValueError,'target-date'):
            calibrated_probability([.5],a,'2026-10-07')

    def test_small_history_keeps_identity_even_at_probability_boundaries(self):
        a=fit_probability_calibration(self.rows(),'2026-10-03')
        np.testing.assert_array_equal(calibrated_probability([0,.2,.7,1],a,'2026-10-03'),[0,.2,.7,1])

    def test_valid_monotone_probabilities_and_empty_reliability_bins(self):
        a=fit_probability_calibration(self.rows(),'2026-10-09')
        p=calibrated_probability(np.linspace(0,1,11),a,'2026-10-09')
        self.assertTrue(((p>=0)&(p<=1)).all())
        self.assertTrue((np.diff(p)>=0).all())
        bins=reliability_table(self.rows())
        self.assertEqual(bins.games.sum(),40)
        self.assertTrue(bins.games.eq(0).any())

    def test_duplicate_and_invalid_training_rows_rejected(self):
        r=self.rows()
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            fit_probability_calibration(pd.concat([r,r.iloc[:1]]),'2026-10-09')
        r.loc[0,'actual_home_win']=2
        with self.assertRaisesRegex(ValueError,'Nonbinary'):
            fit_probability_calibration(r,'2026-10-09')
