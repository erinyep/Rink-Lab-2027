import json
import unittest
import numpy as np
import pandas as pd
from src.fantasy.team_goal_model import build_features,fit_poisson,predict_goals


class TeamGoalModelTests(unittest.TestCase):
    def test_date_cutoff_and_missing_xg(self):
        history=pd.DataFrame([dict(game_id=i,date=d,season=s,team=t,opponent=o,is_home=int(t=='A'),goalsFor=g,goalsAgainst=3,
            xGoalsFor=x,xGoalsAgainst=3) for i,d,s,g,x in [(1,'2025-10-01',2025,3,3),(2,'2026-10-01',2026,4,np.nan),(3,'2026-10-02',2026,99,99)]
            for t,o in [('A','B'),('B','A')]])
        fixture=pd.DataFrame([dict(game_id=4,date='2026-10-02',season=2026,team='A',opponent='B',is_home=1)])
        a=build_features(history,fixture)
        history.loc[history.date.eq('2026-10-02'),'goalsFor']=1000
        b=build_features(history,fixture)
        pd.testing.assert_frame_equal(a,b)
        self.assertEqual(a.latest_input_date.iloc[0],'2026-10-01')
        self.assertEqual(a.own_back_to_back.iloc[0],1)
        self.assertAlmostEqual(a.log_own_xg_rate.iloc[0],np.log(3))

    def test_fitted_home_effect_serialization(self):
        rng=np.random.default_rng(8);home=np.tile([0,1],500)
        frame=pd.DataFrame(dict(game_id=np.arange(1000),date='2025-10-01',is_home=home,actual=rng.poisson(np.exp(.8+.3*home))))
        fit=fit_poisson(frame,['is_home'])
        model=json.loads(json.dumps(fit))
        pred=predict_goals(pd.DataFrame({'is_home':[0,1]}),model)
        self.assertGreater(pred[1],pred[0]);self.assertTrue(np.isfinite(pred).all())
        with self.assertRaises(ValueError):predict_goals(pd.DataFrame({'is_home':[np.nan]}),model)
