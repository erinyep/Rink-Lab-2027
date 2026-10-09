import unittest
import pandas as pd
from scripts.build_team_total_trial import select_lineup


class TeamTrialTests(unittest.TestCase):
    def test_lineup_slots_injury_exclusion_and_prior_appearance_preference(self):
        players=pd.DataFrame(dict(player_id=list(range(24)),position_group=['F']*16+['D']*8,
            injury_status=['OUT']+['ACTIVE']*23,has_forecast=[True]*24,
            played_last_team_game=[True]*10+[False]*6+[True]*5+[False]*3,
            toi_minutes_per_game=list(range(24))))
        result=select_lineup(players)
        selected=result[result.selected_for_trial]
        self.assertEqual(len(selected),18)
        self.assertEqual(sum(selected.position_group=='F'),12)
        self.assertEqual(sum(selected.position_group=='D'),6)
        self.assertFalse(result.iloc[0].selected_for_trial)
        self.assertTrue(set(range(1,10))<=set(selected.player_id))
        players.loc[players.position_group=='D','has_forecast']=False
        with self.assertRaises(ValueError): select_lineup(players)


if __name__=='__main__': unittest.main()
