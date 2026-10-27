#!/usr/bin/env python3
"""Chronological goal/xG development screen, defense description and injury audit.

Credit MoneyPuck.com. Corrected downloads are not historical as-of vintages.
No learned coefficients, automated promotion, or changes to issued forecasts.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import digest, verify_manifest_files
from scripts.evaluate_october_9 import table
from src.fantasy.team_probability import scoring_win_probability
from src.fantasy.feature_screen import paired_delta

ALIASES = {'T.B':'TBL','L.A':'LAK','S.J':'SJS','N.J':'NJD'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ['review','moneypuck','quality','out']:
        ap.add_argument('--'+key, type=Path, required=True)
    ap.add_argument('--feature-results', type=Path, nargs='+', required=True,
                    help='One evaluation directory per frozen feature slate, using this actuals vintage')
    a = ap.parse_args()
    if a.out.exists(): raise ValueError('Preserve previous screens')
    rm = verify_manifest_files(a.review, [])
    qm = verify_manifest_files(a.quality, [])
    mp = a.moneypuck/'all_teams.csv'
    if digest(mp) != json.loads((a.moneypuck/'metadata.json').read_text())['sha256']:
        raise ValueError('Changed team source')
    cols = ['season','gameId','gameDate','team','opposingTeam','home_or_away','situation','playoffGame',
            'goalsFor','goalsAgainst','xGoalsFor','xGoalsAgainst','shotsOnGoalFor','shotsOnGoalAgainst']
    f = pd.read_csv(mp, usecols=cols)
    f = f[f.season.isin([2024,2025,2026]) & f.playoffGame.eq(0) & f.situation.eq('all')].copy()
    f['date'] = pd.to_datetime(f.gameDate.astype(str), format='%Y%m%d').dt.strftime('%Y-%m-%d')
    f = f[f.date.le(rm['through'])]
    for c in ['team','opposingTeam']: f[c] = f[c].replace(ALIASES)
    if f.duplicated(['gameId','team']).any() or not f.groupby('gameId').size().eq(2).all():
        raise ValueError('Duplicate or incomplete source games')
    numeric = ['goalsFor','goalsAgainst','xGoalsFor','xGoalsAgainst','shotsOnGoalFor','shotsOnGoalAgainst']
    if not np.isfinite(f[numeric]).all().all() or not f[numeric].ge(0).all().all():
        raise ValueError('Invalid source values')
    reverse = f[['gameId','team','opposingTeam']+numeric].rename(columns={'team':'opposingTeam','opposingTeam':'team'})
    paired = f.merge(reverse, on=['gameId','team','opposingTeam'], suffixes=('','_opp'), validate='one_to_one')
    if len(paired)!=len(f): raise ValueError('Opponent mismatch')
    for metric in ['goals','xGoals','shotsOnGoal']:
        if not np.allclose(paired[metric+'For'],paired[metric+'Against_opp'],atol=.002):
            raise ValueError('For/against identity mismatch')
    actual = pd.read_csv(Path(rm['actuals'])/'skater_game_stats.csv')
    actual = actual[actual.toi_seconds.gt(0)]
    official = actual.groupby(['game_id','team']).agg(goals=('goals','sum'),shots=('shots','sum')).reset_index()
    audit = f[f.season.eq(2026)].merge(official,left_on=['gameId','team'],right_on=['game_id','team'],how='outer',validate='one_to_one')
    audit['valid'] = audit.goalsFor.eq(audit.goals)&audit.shotsOnGoalFor.eq(audit.shots)
    bad = set(audit.loc[~audit.valid,'gameId'].dropna())
    # Quarantine both teams for features AND scoring, with all exclusions retained.
    clean = f[~f.gameId.isin(bad)].copy()
    predictions = []
    for season in [2025,2026]:
        prior = clean[clean.season.eq(season-1)]
        current = clean[clean.season.eq(season)]
        league = prior[numeric].mean(); team_prior = prior.groupby('team')[numeric].mean()
        for date, day in current.groupby('date'):
            past = current[current.date.lt(date)].sort_values(['date','gameId'])
            rates = {}
            for team in set(day.team)|set(day.opposingTeam):
                history = past[past.team.eq(team)].tail(20)
                p = team_prior.loc[team] if team in team_prior.index else league
                rates[team] = (history[numeric].sum()+20*p)/(len(history)+20)
            for row in day.itertuples():
                own, opp = rates[row.team], rates[row.opposingTeam]
                goals = (own.goalsFor+opp.goalsAgainst)/2
                xg = (own.xGoalsFor+opp.xGoalsAgainst)/2
                for model, pred in [('lagged_goals',goals),('lagged_xg',xg),('equal_blend',.5*(goals+xg))]:
                    predictions.append(dict(season=season,game_id=row.gameId,date=date,team=row.team,
                        home_or_away=row.home_or_away,model=model,prediction=pred,actual=row.goalsFor,
                        absolute_error=abs(pred-row.goalsFor)))
    pred = pd.DataFrame(predictions)
    metrics = pred.groupby(['season','model']).agg(games=('game_id','nunique'),team_rows=('team','size'),mae=('absolute_error','mean')).reset_index()
    intervals = pd.concat([paired_delta(z,baseline='lagged_goals').assign(season=s) for s,z in pred.groupby('season')])
    boxes = {}
    br = Path(rm['boxscores'])
    for source in json.loads((br/'metadata.json').read_text())['sources']:
        if source['file'].startswith('boxscore_'):
            path=br/source['file']
            if digest(path)!=source['sha256']: raise ValueError('Changed official boxscore')
            b=json.loads(path.read_text());boxes[b['id']]=b
    probs=[]
    for (gid,model),z in pred[pred.season.eq(2026)].groupby(['game_id','model']):
        b=boxes[gid];z=z.set_index('team');h=b['homeTeam'];away=b['awayTeam']
        probability=scoring_win_probability(z.loc[h['abbrev'],'prediction'],z.loc[away['abbrev'],'prediction'])
        won=int(h['score']>away['score'])
        probs.append(dict(game_id=gid,model=model,home_probability=probability,actual_home_win=won,brier=(probability-won)**2))
    probs=pd.DataFrame(probs)
    probability_metrics=probs.groupby('model').agg(games=('game_id','size'),brier=('brier','mean')).reset_index()
    probability_intervals=[]
    wide=probs.pivot(index='game_id',columns='model',values='brier')
    for name in wide.columns:
        delta=(wide[name]-wide.lagged_goals).to_numpy();rng=np.random.default_rng(20261024)
        boot=rng.choice(delta,(10000,len(delta)),replace=True).mean(axis=1)
        probability_intervals.append(dict(model=name,games=len(delta),delta_vs_lagged_goals=delta.mean(),lower_95=np.quantile(boot,.025),upper_95=np.quantile(boot,.975)))
    # Defense offense describes production; it does not measure on-ice prevention.
    actual['role']=np.where(actual.position.eq('D'),'D','F')
    roles=actual.groupby('role').agg(appearances=('player_id','size'),players=('player_id','nunique'),goals=('goals','sum'),assists=('assists','sum'),shots=('shots','sum'),pp_points=('pp_points','sum'),toi_minutes=('toi_minutes','sum')).reset_index()
    shot_path=Path(qm['raw_snapshot'])/'shots.zip'
    if digest(shot_path)!=qm['sha256']:raise ValueError('Changed shot source')
    with zipfile.ZipFile(shot_path) as z:
        shots=pd.read_csv(z.open('shots_2026.csv'))
    shots['game_id']=2026000000+shots.game_id
    shots=shots[shots.game_id.isin(boxes)&shots.isPlayoffGame.eq(0)].copy()
    shots['team']=shots.teamCode.replace(ALIASES)
    goal_audit=shots.groupby(['game_id','team']).goal.sum().rename('shot_file_goals').reset_index().merge(official,on=['game_id','team'],how='outer')
    goal_bad=set(goal_audit.loc[~goal_audit.shot_file_goals.eq(goal_audit.goals),'game_id'])
    excluded=set(qm['quarantined_games'])|goal_bad
    usable=shots[~shots.game_id.isin(excluded)]
    totals=usable.groupby(['game_id','shooterPlayerId']).agg(xg=('xGoal','sum'),unblocked_attempts=('xGoal','size'),shot_file_goals=('goal','sum')).reset_index().rename(columns={'shooterPlayerId':'player_id'})
    quality=actual[~actual.game_id.isin(excluded)].merge(totals,on=['game_id','player_id'],how='left',validate='one_to_one')
    for c in ['xg','unblocked_attempts','shot_file_goals']:quality[c]=quality[c].fillna(0)
    if not quality.goals.eq(quality.shot_file_goals).all():raise ValueError('Player-level shot goal disagreement')
    player_quality=quality.groupby(['player_id','name','role']).agg(games=('game_id','nunique'),goals=('goals','sum'),xg=('xg','sum'),shots=('shots','sum'),toi_minutes=('toi_minutes','sum')).reset_index()
    player_quality['goals_minus_xg']=player_quality.goals-player_quality.xg
    quality_roles=quality.groupby('role').agg(games=('game_id','nunique'),goals=('goals','sum'),xg=('xg','sum'),shots=('shots','sum')).reset_index()
    injury=[];coverage=[]
    for directory in rm['evaluations']:
        root=Path(directory);verify_manifest_files(root,[])
        p=pd.read_csv(root/'simulation_summary.csv');p=p[p.issue_timing.eq('pregame')&p.model.eq('default')&p.category.eq('shots')]
        p['appeared']=p.actual.notna()
        injury.append(p.groupby('injury_status',dropna=False).agg(candidates=('player_id','size'),appeared=('appeared','sum')).reset_index().assign(date=p.date.iloc[0]))
        c=pd.read_csv(root/'game_team_coverage.csv');coverage.append(c[c.issue_timing.eq('pregame')])
    # Compare only issued slates scored against the same corrected actuals vintage.
    for path in a.feature_results:
        fm=verify_manifest_files(path,[])
        if fm['actuals_manifest_sha256'] != rm['actuals_sha256']:
            raise ValueError('Feature evaluations use a different actuals vintage')
    feature=pd.concat([pd.read_csv(p/'scored_predictions.csv') for p in a.feature_results])
    if feature.duplicated(['game_id','team','model']).any():raise ValueError('Overlapping feature trials')
    a.out.mkdir(parents=True)
    outputs=dict(team_source_audit=audit,chronological_goal_predictions=pred,goal_metrics=metrics,goal_uncertainty=intervals,
        current_season_probability_screen=probs,probability_metrics=probability_metrics,probability_uncertainty=pd.DataFrame(probability_intervals),
        defense_offense_all_games=roles,shot_goal_source_audit=goal_audit,player_goals_vs_xg=player_quality,role_goals_vs_xg=quality_roles,
        injury_participation_by_date=pd.concat(injury),lineup_coverage=pd.concat(coverage),
        prospective_feature_metrics=feature.groupby('model').agg(games=('game_id','nunique'),mae=('absolute_error','mean')).reset_index(),
        prospective_feature_uncertainty=paired_delta(feature))
    for name,z in outputs.items():z.to_csv(a.out/(name+'.csv'),index=False)
    (a.out/'README.md').write_text(f'''# Broader model development — through {rm['through']}

Question: does lagged expected-goal history improve next-game goal and winner forecasts, and what do defense production and saved injury labels add?

## More games, with distinct evidence

{table(metrics)}

2025 means the 2025–26 season; 2026 means 2026–27. Rolling features exclude the entire target date.
Each team's last 20 current-season games are combined with a fixed 20-game previous-season team prior;
missing prior teams use the previous-season league mean. Own offense and opponent defense receive equal weight.
Goal history, xG history and a fixed 50/50 blend were specified together; no fitted coefficients or winner promotion.
All {len(bad)} current-season team-file discrepancy games are excluded from features/scoring and retained in the audit.
Historical seasons have internal pair checks, not independent official boxscore reconciliation.
Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Corrected downloads are not historical pregame vintages;
MoneyPuck's current xG model was trained on 2023–26 shots. Older-season results are development evidence,
not a clean test of the upstream xG model. [Paired uncertainty](goal_uncertainty.csv).

## Current-season team probabilities

{table(probability_metrics)}

Official final winners include shootouts; goal-count targets exclude shootout deciding goals.
Independent Poisson counts and equally split ties are an uncalibrated approximation. No home advantage or
confirmed starter feature. [Paired Brier deltas](probability_uncertainty.csv). These reconstructed probabilities
are retrospective development results, separate from the 36-game frozen-main-model comparison.

## Defense scoring and expected versus actual goals

{table(roles)}

These are defensemen's offensive contributions, not a score of defensive prevention. Assists/PPP can involve
multiple players on the same goal and must not be added to goals as distinct scoring events.

{table(quality_roles)}

Shot-level xG uses only {quality.game_id.nunique()} fully reconciled games; {len(excluded)} games remain quarantined
for SOG or goal discrepancies. [Every player, with no GP threshold](player_goals_vs_xg.csv) includes goals minus xG
on the SAME usable games. This residual mixes finishing, sampling variation and model error; it is not established
repeatable finishing talent. Split PP/5v5, shrink toward longer history and test future games before adding effects.

## Frozen defense/quality trials: {len(a.feature_results)} prospective dates

{table(outputs['prospective_feature_metrics'])}

[Paired uncertainty](prospective_feature_uncertainty.csv). These {feature.game_id.nunique()} games test team shots, not defenseman goal
scoring or team win probabilities. They cannot validate a defense scoring coefficient for a different target.

## Injuries and opportunity

[Saved injury labels versus subsequent participation](injury_participation_by_date.csv) and
[actual lineup overlap](lineup_coverage.csv) retain each original date. ACTIVE means an availability label,
not confirmed dressing; absence can be scratch, demotion or injury. Current injury labels never backfill old games.
Next test: separate probability of dressing from conditional EV/PP minutes and production; redistribute missing
players' opportunity to actual replacement roles. Effects require saved lineups/PP units and starter/rest history.
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        review=str(a.review),review_sha256=digest(a.review/'manifest.json'),moneypuck=str(mp),moneypuck_sha256=digest(mp),
        quality=str(a.quality),quality_sha256=digest(a.quality/'manifest.json'),
        feature_evaluations={str(p):digest(p/'manifest.json') for p in a.feature_results},
        fixed_design=dict(recent_games=20,prior_games=20,blend_weight=.5),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print(metrics.to_string(index=False));print(probability_metrics.to_string(index=False));print('Broader screen:',a.out)


if __name__=='__main__':main()
