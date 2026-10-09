import unittest
import numpy as np
import pandas as pd
from src.fantasy.goalies import goalie_rates,simulate_goalie,start_shares


class GoalieTests(unittest.TestCase):
    def test_injuries_excluded_and_uncertain_status_not_confirmed(self):
        shares=start_shares({1:10,2:3,3:0},{1:'OUT',2:'DAY_TO_DAY',3:'UNKNOWN'})
        self.assertEqual(shares[1],0)
        self.assertEqual(shares[2],.8)
        self.assertAlmostEqual(sum(shares.values()),1)
        self.assertTrue(np.isnan(start_shares({1:2},{1:'INJURY_RESERVE'})[1]))
    def test_exception_exclusion_and_no_history_prior(self):
        h=pd.DataFrame(dict(player_id=[1,2],season_id=[20252026]*2,weight=[1,1],
            eligible_for_valuation=[True,False],shots_against=[100,10],saves=[90,8],
            goals_against=[10,3],time_on_ice=[12000,3600]))
        prior=goalie_rates(h,999)
        self.assertAlmostEqual(prior['save_probability'],.9)
        self.assertAlmostEqual(prior['shots_against_per_60'],30)
        h.loc[1,'saves']=999
        self.assertEqual(prior,goalie_rates(h,999))
        self.assertEqual(prior['fallback'],'past_league_prior')

    def test_simulated_counts_and_win_proxy(self):
        samples,win=simulate_goalie(30,.9,3,draws=100000)
        np.testing.assert_array_equal(samples['saves']+samples['goals_against'],samples['shots_against'])
        self.assertAlmostEqual(samples['saves'].mean(),27,delta=.1)
        self.assertAlmostEqual(win,.5,delta=.01)


if __name__=='__main__': unittest.main()
