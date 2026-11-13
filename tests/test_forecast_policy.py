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

    def test_policy_history_preserves_prior_source_and_applies_new_source_on_effective_date(self):
        f=pd.DataFrame([dict(game_id=1,player_id=9,model=m,expected_toi_minutes_if_plays=t,expected_shots_if_plays=s)
                        for m,t,s in [('default',20,3),('usage_shot_context_trial',23,4),('usage_toi_only_trial',24,5)]])
        policy=dict(baseline='default',version='fantasy_category_policy_v3',effective_from='2026-11-14',
                    category_models={'toi_minutes':'usage_toi_only_trial'},
                    policy_history=[dict(version='fantasy_category_policy_v2',effective_from='2026-10-27',
                                         effective_through='2026-11-13',
                                         category_models={'toi_minutes':'usage_shot_context_trial'})])
        prior=select_fantasy_projections(f,'2026-11-13',policy).iloc[0]
        current=select_fantasy_projections(f,'2026-11-14',policy).iloc[0]
        self.assertEqual(prior.model,'fantasy_category_policy_v2')
        self.assertEqual(prior.expected_toi_minutes_if_plays,23)
        self.assertEqual(prior.expected_shots_if_plays,3)
        self.assertEqual(current.model,'fantasy_category_policy_v3')
        self.assertEqual(current.expected_toi_minutes_if_plays,24)
        self.assertEqual(current.expected_shots_if_plays,3)
