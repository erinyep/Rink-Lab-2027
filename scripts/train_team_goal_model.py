#!/usr/bin/env python3
"""Train, validate, test and freeze a team goal-context model for future games."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.special import gammaln
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.fantasy.team_goal_model import load_history,build_features,fit_poisson,predict_goals
from src.fantasy.team_probability import scoring_win_probability
from scripts.evaluate_daily_forecasts import digest
from scripts.evaluate_october_9 import table


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['moneypuck','boxscores','out']:ap.add_argument('--'+key,type=Path,required=True)
    ap.add_argument('--through',required=True)
    ap.add_argument('--config',type=Path,default=Path('config/team_goal_model_v2.json'))
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve previous model releases')
    cfg=json.loads(a.config.read_text());history,audit,boxes=load_history(a.moneypuck,a.boxscores,a.through)
    target=history[history.season.ge(min(cfg['training_seasons']))]
    features=build_features(history,target,cfg['recent_games'],cfg['prior_games'])
    features=features.merge(target[['game_id','team','actual']],on=['game_id','team'],validate='one_to_one')
    if not (features.latest_input_date<features.date).all():raise ValueError('Target-date leakage')
    train=features[features.season.isin(cfg['training_seasons'])]
    valid=features[features.season.eq(cfg['validation_season'])]
    test=features[features.season.eq(cfg['test_season'])]
    def scored(frame,pred,name,stage):
        return frame[['game_id','date','team','opponent','is_home','actual']].assign(model=name,stage=stage,prediction=pred,
            mae=np.abs(pred-frame.actual),nll=pred-frame.actual*np.log(pred)+gammaln(frame.actual+1))
    validation=[scored(valid,valid.baseline,'lagged_goals_baseline','validation')];models={}
    for name,cols in cfg['feature_sets'].items():
        models[name]=fit_poisson(train,cols,cfg['ridge_penalty'])
        validation.append(scored(valid,predict_goals(valid,models[name]),name,'validation'))
    validation=pd.concat(validation)
    vm=validation.groupby('model').agg(games=('game_id','nunique'),mae=('mae','mean'),poisson_nll=('nll','mean')).reset_index()
    # Baseline remains eligible; a new model must earn deployment on validation.
    selected=vm.sort_values(['poisson_nll','model']).model.iloc[0]
    historical=features[features.season.lt(cfg['test_season'])]
    test_rows=[scored(test,test.baseline,'lagged_goals_baseline','recent_test')];test_models={}
    for name,cols in cfg['feature_sets'].items():
        test_models[name]=fit_poisson(historical,cols,cfg['ridge_penalty'])
        test_rows.append(scored(test,predict_goals(test,test_models[name]),name,'recent_test'))
    tests=pd.concat(test_rows)
    tm=tests.groupby('model').agg(games=('game_id','nunique'),mae=('mae','mean'),poisson_nll=('nll','mean')).reset_index()
    paired=[]
    for stage,frame in [('validation',validation),('recent_test',tests)]:
        for metric in ['mae','nll']:
            wide=frame.pivot(index=['game_id','team'],columns='model',values=metric)
            for name in cfg['feature_sets']:
                delta=(wide[name]-wide.lagged_goals_baseline).groupby('game_id').mean().to_numpy()
                rng=np.random.default_rng(20261027);boot=rng.choice(delta,(10000,len(delta)),replace=True).mean(axis=1)
                paired.append(dict(stage=stage,metric=metric,model=name,games=len(delta),delta=delta.mean(),lower_95=np.quantile(boot,.025),upper_95=np.quantile(boot,.975)))
    probabilities=[]
    for (gid,name),z in tests.groupby(['game_id','model']):
        b=boxes[gid];z=z.set_index('team');home=b['homeTeam'];away=b['awayTeam'];won=int(home['score']>away['score'])
        p=scoring_win_probability(z.loc[home['abbrev'],'prediction'],z.loc[away['abbrev'],'prediction'])
        probabilities.append(dict(game_id=gid,date=b['gameDate'],model=name,home=home['abbrev'],away=away['abbrev'],
            probability=p,actual_home_win=won,brier=(p-won)**2,log_loss=-np.log(np.clip(p if won else 1-p,1e-12,1))))
    probs=pd.DataFrame(probabilities)
    pm=probs.groupby('model').agg(games=('game_id','nunique'),brier=('brier','mean'),log_loss=('log_loss','mean')).reset_index()
    pw=probs.pivot(index='game_id',columns='model',values='brier')
    for name in cfg['feature_sets']:
        delta=(pw[name]-pw.lagged_goals_baseline).to_numpy();rng=np.random.default_rng(20261027)
        boot=rng.choice(delta,(10000,len(delta)),replace=True).mean(axis=1)
        paired.append(dict(stage='recent_test',metric='brier',model=name,games=len(delta),delta=delta.mean(),lower_95=np.quantile(boot,.025),upper_95=np.quantile(boot,.975)))
    # Freeze the validation-selected specification, refit including yesterday for future use.
    production=None if selected=='lagged_goals_baseline' else fit_poisson(features,cfg['feature_sets'][selected],cfg['ridge_penalty'])
    out_model=dict(version=cfg['version'],selected_model=selected,config=cfg,training_through=a.through,model=production,
        selection='2025-26 goal likelihood only; 2026-27 not used to choose the specification',
        code_sha256=digest(Path('src/fantasy/team_goal_model.py')))
    a.out.mkdir(parents=True)
    (a.out/'fitted_model.json').write_text(json.dumps(out_model,indent=2)+'\n')
    (a.out/'historical_test_models.json').write_text(json.dumps(test_models,indent=2)+'\n')
    for name,z in [('validation_metrics',vm),('recent_goal_metrics',tm),('recent_probability_metrics',pm),('paired_uncertainty',pd.DataFrame(paired)),
        ('recent_predictions',tests),('recent_probabilities',probs),('source_audit',audit)]:z.to_csv(a.out/(name+'.csv'),index=False)
    bydate=tests.groupby(['date','model']).agg(games=('game_id','nunique'),mae=('mae','mean'),poisson_nll=('nll','mean')).reset_index()
    bydate.to_csv(a.out/'recent_metrics_by_date.csv',index=False)
    local=Path('data/processed/forecasts')/('team_goal_training_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));local.mkdir(parents=True)
    features.to_csv(local/'lagged_features.csv',index=False);validation.to_csv(local/'validation_predictions.csv',index=False)
    (a.out/'README.md').write_text(f'''# Team goal model update — through {a.through}

Selected specification: **{selected}**, chosen solely on 2025–26 Poisson goal likelihood.
Training: {train.game_id.nunique()} games from 2023–24 and 2024–25. Validation: {valid.game_id.nunique()} games
from 2025–26. Recent test: **{test.game_id.nunique()} games** from 2026–27, including all games through {a.through}.
No games-played threshold. Both teams, same fixtures for every model. No new per-slate correction.

The model learns team offense and opponent goals-against effects, home ice, back-to-backs and rest difference.
A second declared candidate adds lagged own xG and opponent xGA. Both use training-only standardization and
fixed ridge penalty 20. The simple baseline averages shrunk own scoring and opponent goals allowed.
Rates use the last 20 current-season games plus a fixed 20-game prior from the previous season.
Every feature excludes the entire target date. Goals are official NHL counts in the recent test; discrepancies
in downloaded xG are quarantined while retaining official goal and schedule observations.

## Full-season validation

{table(vm)}

## Recent goal forecasts

{table(tm)}

## Recent win-probability forecasts

{table(pm)}

[Paired game-bootstrap differences](paired_uncertainty.csv) · [Every recent date](recent_metrics_by_date.csv)
· [Goal predictions](recent_predictions.csv) · [Win probabilities](recent_probabilities.csv).

Poisson likelihood is the model-selection target, not MAE or a hand-picked winning slate. Winner probabilities
use independent Poisson scores and equal tie splitting; there is no fitted overtime model. These historical
predictions are a chronological development test, NOT original issued probabilities. Current-season results
do not enter the specification choice. The final deployed coefficients are refit through {a.through}; they
must only be used for later dates and their future scores tracked separately.

Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Historical sources are corrected downloads rather than
as-of snapshots; the upstream xG model used 2023–26 training shots. Therefore xG candidate validation is
development evidence with upstream overlap, not an independent validation of MoneyPuck. Historical goal
counts have internal checks; recent targets are reconciled against official NHL finals. Rest excludes travel
distance and timezone changes. Missing confirmed starters/lineups remain an improvement opportunity.

[Production parameters](fitted_model.json) · [Frozen pre-test parameters](historical_test_models.json).
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),through=a.through,
        selected_model=selected,moneypuck=str(a.moneypuck),moneypuck_sha256=digest(a.moneypuck/'all_teams.csv'),
        boxscores=str(a.boxscores),boxscores_sha256=digest(a.boxscores/'metadata.json'),config_sha256=digest(a.config),
        local_training_features=str(local),local_files={p.name:digest(p) for p in local.iterdir()},
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print('Selected:',selected);print('Validation:\n'+vm.to_string(index=False));print('Recent goals:\n'+tm.to_string(index=False));print('Recent probabilities:\n'+pm.to_string(index=False))


if __name__=='__main__':main()
