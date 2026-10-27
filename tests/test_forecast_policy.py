import unittest
import pandas as pd
from src.fantasy.forecast_policy import select_fantasy_projections


class ForecastPolicyTests(unittest.TestCase):
    def test_only_validated_category_changes(self):
        f=pd.DataFrame([dict(game_id=1,player_id=9,model=m,expected_toi_minutes_if_plays=t,expected_shots_if_plays=s)
                        for m,t,s in [('default',20,3),('usage',23,4)]])
        policy=dict(baseline='default',version='v2',effective_from='2026-10-27',category_models={'toi_minutes':'usage'})
        selected=select_fantasy_projections(f,'2026-10-27',policy).iloc[0]
        self.assertEqual(selected.expected_toi_minutes_if_plays,23)
        self.assertEqual(selected.expected_shots_if_plays,3)
        self.assertEqual(selected.baseline_expected_toi_minutes_if_plays,20)
        self.assertEqual(select_fantasy_projections(f,'2026-10-24',policy).iloc[0].model,'default')
        with self.assertRaisesRegex(ValueError,'coverage mismatch'):
            select_fantasy_projections(f[f.model.eq('default')],'2026-10-27',policy)
