#!/usr/bin/env python3
"""Issue the fitted team goal/win model, retaining the simple baseline alongside it."""
import argparse
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import ssl
import sys
from urllib.request import Request,urlopen
import numpy as np
import pandas as pd
import truststore
from scipy.stats import poisson
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.fantasy.team_goal_model import load_history,build_features,predict_goals
from src.fantasy.team_probability import scoring_win_probability
from src.fantasy.history import archive_snapshot
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest
from scripts.publish_results_update import page


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--date',required=True)
    for key in ['model-release','moneypuck','boxscores','out']:ap.add_argument('--'+key,type=Path,required=True)
    ap.add_argument('--schedule-snapshot',type=Path)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve previous issuances')
    mm=verify_manifest_files(a.model_release,[]);model=json.loads((a.model_release/'fitted_model.json').read_text())
    if model['training_through']>=a.date:raise ValueError('Fitted model contains target-date outcomes')
    if model['code_sha256']!=digest(Path('src/fantasy/team_goal_model.py')):raise ValueError('Model implementation changed since training')
    cutoff=str(pd.Timestamp(a.date).date()-timedelta(days=1))
    history,audit,_=load_history(a.moneypuck,a.boxscores,cutoff)
    now=datetime.now(timezone.utc)
    raw=a.schedule_snapshot or Path('data/raw/nhl/snapshots')/('team_model_schedule_'+now.strftime('%Y%m%dT%H%M%S%fZ'))
    if not a.schedule_snapshot:
        raw.mkdir(parents=True)
        url='https://api-web.nhle.com/v1/schedule/'+a.date
        with urlopen(Request(url,headers={'User-Agent':'Rink-Lab/0.1 research'}),context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=60) as r:
            (raw/'schedule.json').write_bytes(r.read())
        (raw/'metadata.json').write_text(json.dumps(dict(url=url,retrieved_at_utc=datetime.now(timezone.utc).isoformat(),sha256=digest(raw/'schedule.json')),indent=2)+'\n')
    sm=json.loads((raw/'metadata.json').read_text())
    if digest(raw/'schedule.json')!=sm['sha256']:raise ValueError('Changed schedule source')
    games=[g for d in json.loads((raw/'schedule.json').read_text())['gameWeek'] if d['date']==a.date for g in d['games'] if g['season']==20262027 and g['gameType']==2]
    if not games or len({g['id'] for g in games})!=len(games):raise ValueError('Missing/duplicate scheduled games')
    fixtures=[]
    for g in games:
        if pd.Timestamp(g['startTimeUTC'])<=pd.Timestamp(now)+pd.Timedelta(minutes=10):raise ValueError('Insufficient pregame lead')
        for side,opp in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            fixtures.append(dict(game_id=g['id'],date=a.date,season=2026,team=g[side]['abbrev'],opponent=g[opp]['abbrev'],is_home=int(side=='homeTeam')))
    features=build_features(history,pd.DataFrame(fixtures),model['config']['recent_games'],model['config']['prior_games'])
    means=features.baseline.to_numpy() if model['model'] is None else predict_goals(features,model['model'])
    features['expected_goals']=means;features['poisson_p10']=poisson.ppf(.1,means).astype(int);features['poisson_p90']=poisson.ppf(.9,means).astype(int)
    rows=[]
    for g in games:
        f=features[features.game_id.eq(g['id'])].set_index('team');h=g['homeTeam']['abbrev'];away=g['awayTeam']['abbrev']
        prob=scoring_win_probability(f.loc[h,'expected_goals'],f.loc[away,'expected_goals'])
        base=scoring_win_probability(f.loc[h,'baseline'],f.loc[away,'baseline'])
        rows.append(dict(game_id=g['id'],date=a.date,start_time_utc=g['startTimeUTC'],home=h,away=away,
            home_goal_mean=f.loc[h,'expected_goals'],away_goal_mean=f.loc[away,'expected_goals'],home_win_probability=prob,away_win_probability=1-prob,
            baseline_home_goals=f.loc[h,'baseline'],baseline_away_goals=f.loc[away,'baseline'],baseline_home_win_probability=base,
            probability_change_vs_baseline=prob-base,issued_at_utc=now.isoformat(),model=model['version'],specification=model['selected_model'],
            training_through=model['training_through'],status='updated_team_model_pending_prospective_validation',actual_home_win=None))
    predictions=pd.DataFrame(rows);a.out.mkdir(parents=True)
    predictions.to_csv(a.out/'team_win_probabilities.csv',index=False)
    features.to_csv(a.out/'team_goal_forecasts.csv',index=False)
    audit.to_csv(a.out/'input_reconciliation.csv',index=False)
    view=predictions[['away','home','away_goal_mean','home_goal_mean','home_win_probability','baseline_home_win_probability','probability_change_vs_baseline']].copy()
    for c in ['home_win_probability','baseline_home_win_probability','probability_change_vs_baseline']:view[c]=100*view[c]
    view=view.rename(columns={'home_win_probability':'home_win_percent','baseline_home_win_probability':'baseline_home_win_percent','probability_change_vs_baseline':'change_percentage_points'})
    body=f'<p>{len(games)} games issued before puck drop. Fitted through {model["training_through"]}; includes yesterday’s official games. Team offense, opposing defense, home ice, rest and lagged xG now affect goal means.</p><main>'+view.round(3).to_html(index=False)+'</main>'
    body+='<p>Win probabilities are derived from the goal model, not a second independently fitted model. Positive change means higher home-win probability than the simple goal-history baseline. Lineups and starters are not confirmed inputs; p10–p90 goal ranges remain uncalibrated.</p><p><a href="team_win_probabilities.csv">Probability CSV</a> · <a href="team_goal_forecasts.csv">Goals and feature inputs CSV</a> · <a href="../history/'+a.model_release.name+'/README.md">Training and validation results</a></p>'
    (a.out/'index.html').write_text(page('Updated team model — '+a.date,body))
    (a.out/'README.md').write_text(f'''# Updated team model — {a.date}

[Interactive forecasts](index.html) · [Goal and win forecasts](team_win_probabilities.csv) · [Lagged model inputs](team_goal_forecasts.csv).

{len(games)} games, all issued before puck drop. Model `{model['selected_model']}` fit through {model['training_through']}.
Learned home ice, rest/back-to-back, own scoring and opposing goals allowed, plus lagged xG where applicable.
The simple baseline is preserved alongside every updated prediction. Player/fantasy conditional means are unchanged;
these are direct team forecasts, not a redistribution of player goals. No confirmed-goalie or injury effect is claimed.
Winner probabilities use independent Poisson scoring and equal tie splitting; intervals are not calibrated.
Model choice used the prior full season. Coefficients remain frozen through {model['training_through']};
today's lagged feature inputs include official history through {cutoff}, without refitting coefficients.
Future performance must be scored against this frozen release. Credit MoneyPuck.com for lagged xG data; absent or
disagreeing xG rows remain excluded from rate updates, with official goals and schedule retained.
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=now.isoformat(),date=a.date,method=model['version'],
        model_release=str(a.model_release),model_release_sha256=digest(a.model_release/'manifest.json'),
        moneypuck=str(a.moneypuck),moneypuck_sha256=digest(a.moneypuck/'all_teams.csv'),boxscores=str(a.boxscores),
        boxscores_sha256=digest(a.boxscores/'metadata.json'),schedule_snapshot=str(raw),schedule_sha256=digest(raw/'schedule.json'),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    archive_snapshot(a.out,Path('data/processed/prediction_history'),'team_context_predictions')
    print('Updated team forecast:',a.out);print(view.round(3).to_string(index=False))


if __name__=='__main__':main()
