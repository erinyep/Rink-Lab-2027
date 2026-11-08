import unittest
import pandas as pd
from src.fantasy.opportunity import historical_pp_prior, power_play_opportunity, apply_opportunity_means


class OpportunityTests(unittest.TestCase):
    def fixture(self):
        h=pd.DataFrame([dict(game_id=i,player_id=1,game_date=date,toi_seconds=1200,pp_points=points)
                        for i,date,points in [(1,'2026-11-01',1),(2,'2026-11-02',99)]])
        e=h.drop(columns='pp_points').assign(pp_toi_seconds=[180,1200])
        return h,e

    def test_target_and_future_outcomes_cannot_change_forecast(self):
        h,e=self.fixture()
        a=power_play_opportunity(h,e,1,'2026-11-02',2,.1,20)
        b=power_play_opportunity(h.iloc[:1],e.iloc[:1],1,'2026-11-02',2,.1,20)
        self.assertEqual(a,b)
        self.assertAlmostEqual(a['expected_pp_minutes'],23/11)
        self.assertAlmostEqual(a['pp_points_per_minute'],13/123)

    def test_no_recent_games_preserves_prior_and_zero_role(self):
        h,e=self.fixture()
        a=power_play_opportunity(h,e,2,'2026-11-02',2,.1,20)
        self.assertAlmostEqual(a['opportunity_pp_points'],.2)
        self.assertEqual(power_play_opportunity(h,e,2,'2026-11-02',0,.1,20)['opportunity_pp_points'],0)

    def test_missing_or_inconsistent_exposure_fails_closed(self):
        h,e=self.fixture()
        with self.assertRaisesRegex(ValueError,'Missing PP exposure'):
            power_play_opportunity(h,e.iloc[0:0],1,'2026-11-02',2,.1,20)
        e.loc[0,'toi_seconds']=1800
        with self.assertRaisesRegex(ValueError,'total differs'):
            power_play_opportunity(h,e,1,'2026-11-02',2,.1,20)

    def test_count_changes_do_not_scale_shots_or_goals(self):
        means=dict(shots=3.,goals=.2,assists=.3,points=.5,pp_points=.1,toi_minutes=18.)
        new=apply_opportunity_means(means,22,dict(opportunity_pp_points=1.))
        self.assertEqual(new['pp_points'],.5)
        self.assertEqual(new['shots'],3.)
        self.assertEqual(new['goals'],.2)
        self.assertEqual(means['toi_minutes'],18.)
        self.assertEqual(apply_opportunity_means(means,22)['pp_points'],.1)

    def test_prior_excludes_current_season_and_supports_rookie(self):
        panel=pd.DataFrame([dict(player_id=1,season_id=season,position_group='F',games_played=10,
            toi_minutes=200,pp_toi_minutes=minutes,pp_points=points)
            for season,minutes,points in [(20252026,20,2),(20262027,200,200)]])
        prior=historical_pp_prior(panel,1,'F',20262027)
        self.assertEqual(prior['prior_pp_minutes'],2.)
        self.assertAlmostEqual(prior['prior_pp_rate'],.1)
        self.assertEqual(historical_pp_prior(panel,2,'F',20262027)['pp_prior_source'],'position_completed_seasons')
