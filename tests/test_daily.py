import unittest
import pandas as pd
from src.fantasy.daily import current_from_games, recent_shot_usage, coherent_count_means


class DailyTests(unittest.TestCase):
    def history(self):
        return pd.DataFrame([dict(game_id=i,game_date=d,player_id=1,name='Test',team='DET',position='C',toi_seconds=600,
            toi_minutes=10,shots=s,goals=0,assists=0,points=0,hits=0,penalty_minutes=0,plus_minus=0,pp_points=0)
            for i,d,s in [(1,'2026-10-09',2),(2,'2026-10-10',100)]])

    def test_target_day_cannot_enter_player_aggregates_or_usage(self):
        h=self.history(); x=current_from_games(h,'2026-10-10',20262027)
        self.assertEqual(x.shots.iloc[0],2)
        u=recent_shot_usage(h,1,'2026-10-10',2,10)
        self.assertEqual(u['recent_games'],1)
        self.assertAlmostEqual(u['usage_shots_before_context'],2)

    def test_no_recent_history_uses_prior(self):
        u=recent_shot_usage(self.history(),99,'2026-10-10',3,20)
        self.assertEqual(u['recent_games'],0)
        self.assertAlmostEqual(u['usage_shots_before_context'],3)

    def test_sparse_calibration_keeps_count_support_valid(self):
        original=dict(shots=.05,goals=.1,assists=.09,pp_points=.2)
        m,f=coherent_count_means(original)
        self.assertAlmostEqual(m['shots'],.1)
        self.assertAlmostEqual(m['pp_points'],.19)
        self.assertTrue(all(f.values()))
        self.assertEqual(original['pp_points'],.2)

if __name__=='__main__': unittest.main()
