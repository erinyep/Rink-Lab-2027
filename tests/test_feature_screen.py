import unittest
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np
import pandas as pd
from src.fantasy.feature_screen import fit_residual,apply_residual,lagged_team_rows,paired_delta


class FeatureScreenTests(unittest.TestCase):
    def test_training_only_scaling_and_missing_imputation(self):
        training=pd.DataFrame({'x':[1.,3.,np.nan],'residual':[1.,3.,2.],'baseline':[20.,20.,20.]})
        model=fit_residual(training,['x'],20)
        self.assertEqual(model['center']['x'],2.)
        future=pd.DataFrame({'x':[1000.,np.nan],'baseline':[20.,20.]})
        prediction,effects=apply_residual(future,model)
        self.assertEqual(effects.loc[1,'x'],0.)
        self.assertEqual(prediction.loc[1],22.)
        self.assertEqual(model['center']['x'],2.)
        self.assertTrue(np.allclose(prediction,future.baseline+model['intercept']+effects.sum(axis=1)))

    def test_target_date_events_and_quarantined_games_cannot_enter_features(self):
        history=pd.DataFrame([dict(game_id=i,game_date=date,team=t,opponent=o,shots=s,shots_against=a)
            for i,date,s,a in [(1,'2026-10-01',20,30),(2,'2026-10-02',900,800)]
            for t,o in [('A','B'),('B','A')]])
        fixtures=pd.DataFrame([dict(game_id=3,game_date='2026-10-02',team='A',opponent='B')])
        measures=['defense_attempts','defense_unblocked_attempts','defense_sog','defense_near_net_attempts','defense_assist_credits','goals_with_defense_involvement','followup_attempts_after_defense']
        pbp=pd.DataFrame([dict(game_id=i,game_date=date,team=t,strength=strength,team_attempts=40,**{c:5 for c in measures})
            for i,date in [(1,'2026-10-01'),(2,'2026-10-02')]
            for t in ['A','B'] for strength in ['all','5v5']])
        quality=pd.DataFrame([dict(game_id=1,game_date='2026-10-01',team=t,strength=s,source_quarantined=True,
            defense_xg=100,defense_expected_rebounds=100,defense_unblocked_attempts=100,team_xg=100)
            for t in ['A','B'] for s in ['all','5v5']])
        result=lagged_team_rows(history,fixtures,pbp,pd.DataFrame({'game_id':[1,2],'sog_match':[True,True]}),quality)
        self.assertEqual(result.own_games.iloc[0],1)
        self.assertEqual(result.latest_input_date.iloc[0],'2026-10-01')
        self.assertEqual(result.own_pbp_games.iloc[0],1)
        self.assertEqual(result.own_quality_games.iloc[0],0)
        self.assertTrue(pd.isna(result.own_defense_xg_per_game.iloc[0]))
        self.assertLess(result.baseline.iloc[0],30)

    def test_frozen_trial_scores_identical_completed_games_and_preserves_missing_finals(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);evidence=root/'evidence';actuals=root/'actuals';evidence.mkdir();actuals.mkdir()
            forecasts=pd.DataFrame([dict(game_id=gid,game_date='2026-10-20',team=team,model=model,
                experimental_team_sog=pred,issued_at_utc='2026-10-20T19:00:00Z',start_time_utc='2026-10-20T23:00:00Z')
                for gid in [1,2] for team in ['A','B'] for model,pred in [('bias_control',20.),('new',21.)]])
            forecasts.to_csv(evidence/'tonight_experimental_team_forecasts.csv',index=False)
            pd.DataFrame([dict(game_id=1,game_date='2026-10-20',team=team,player_id=pid,shots=20,toi_seconds=60)
                          for team,pid in [('A',1),('B',2)]]).to_csv(actuals/'skater_game_stats.csv',index=False)
            for path in [evidence,actuals]:
                files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in path.iterdir()}
                (path/'manifest.json').write_text(json.dumps(dict(target_date='2026-10-20',files=files)))
            script=Path(__file__).resolve().parents[1]/'scripts/evaluate_feature_evidence.py'
            run=subprocess.run([sys.executable,str(script),'--evidence',str(evidence),'--actuals',str(actuals),'--out',str(root/'score')],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            metrics=pd.read_csv(root/'score/metrics.csv').set_index('model')
            self.assertEqual(metrics.loc['bias_control','mae'],0.)
            self.assertEqual(metrics.loc['new','mae'],1.)
            self.assertTrue(metrics.team_rows.eq(2).all())
            self.assertEqual(json.loads((root/'score/manifest.json').read_text())['unscored_games'],1)

    def test_paired_inference_requires_identical_team_populations(self):
        frame=pd.DataFrame({'game_id':[1,1,2],'team':['A','A','B'],'model':['bias_control','new','bias_control'],'absolute_error':[2.,1.,3.]})
        with self.assertRaises(ValueError):paired_delta(frame)


if __name__=='__main__':unittest.main()
