#!/usr/bin/env python3
"""Score frozen team probabilities and pregame Kalshi quotes on official finals.

One home-team binary outcome per game avoids double-counting complementary teams.
This scores winner forecasts, not trading returns or exchange settlement records.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files,digest
from scripts.evaluate_october_9 import table
from src.fantasy.history import archive_snapshot


def score_game(forecast, quotes, box):
    """Validate identities, timing and complementary quotes before scoring."""
    if box['id'] != forecast['game_id'] or box['gameDate'] != forecast['date']:
        raise ValueError('Game/date identity mismatch')
    if box['season'] != 20262027 or box['gameType'] != 2:
        raise ValueError('Wrong season/type')
    if box['gameState'] not in ['FINAL','OFF']:
        raise ValueError('Unfinished game')
    if box['homeTeam']['abbrev'] != forecast['home'] or box['awayTeam']['abbrev'] != forecast['away']:
        raise ValueError('Home/away identity mismatch')
    if box['startTimeUTC'] != forecast['start_time_utc']:
        raise ValueError('Rescheduled fixture requires manual rules review')
    start=pd.Timestamp(forecast['start_time_utc'])
    if pd.Timestamp(forecast['issued_at_utc'])+pd.Timedelta(minutes=10)>=start:
        raise ValueError('Probability not issued with pregame lead')
    ph=float(forecast['home_win_probability']);pa=float(forecast['away_win_probability'])
    if not np.isfinite([ph,pa]).all() or not 0<=ph<=1 or not 0<=pa<=1 or not np.isclose(ph+pa,1):
        raise ValueError('Invalid model probability pair')
    if len(quotes)!=2 or {q['team'] for q in quotes}!={forecast['home'],forecast['away']}:
        raise ValueError('Missing/duplicate quote pair')
    for q in quotes:
        if q['game_id']!=forecast['game_id'] or pd.Timestamp(q['sampled_at_utc'])>=start:
            raise ValueError('Wrong game or non-pregame quote')
        if not 0<float(q['yes_bid'])<=float(q['yes_ask'])<1:
            raise ValueError('Invalid two-sided quote')
        if not np.isclose(float(q['quoted_midpoint']),(float(q['yes_bid'])+float(q['yes_ask']))/2):
            raise ValueError('Midpoint differs from saved bid/ask')
    home=next(q for q in quotes if q['team']==forecast['home'])
    hs,aws=box['homeTeam']['score'],box['awayTeam']['score']
    if hs==aws: raise ValueError('Final winner missing')
    outcome=int(hs>aws)
    rows=[]
    for model,prob in [('team_probability_trial',ph),('kalshi_home_midpoint',float(home['quoted_midpoint'])),('even_baseline',.5)]:
        rows.append(dict(game_id=forecast['game_id'],date=forecast['date'],home=forecast['home'],away=forecast['away'],
            home_score=hs,away_score=aws,actual_home_win=outcome,model=model,probability=prob,
            brier=(prob-outcome)**2,log_loss=-np.log(np.clip(prob if outcome else 1-prob,1e-12,1)),
            correct_favorite=float((prob>.5)==bool(outcome)) if prob!=.5 else np.nan))
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['probabilities','benchmark','boxscores','out']:ap.add_argument('--'+key,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve earlier evaluations')
    pm=verify_manifest_files(a.probabilities,[]);km=verify_manifest_files(a.benchmark,[])
    if km['probabilities_sha256']!=digest(a.probabilities/'manifest.json'):raise ValueError('Wrong benchmark forecast version')
    if 'bundle' in pm:
        if digest(Path(pm['bundle'])/'manifest.json')!=pm['bundle_sha256']:raise ValueError('Changed frozen bundle')
        verify_manifest_files(Path(pm['bundle']),[])
    elif pm.get('method')=='team_goal_context_v2':
        release=Path(pm['model_release'])
        if digest(release/'manifest.json')!=pm['model_release_sha256']:raise ValueError('Changed fitted model release')
        verify_manifest_files(release,[])
        if json.loads((release/'fitted_model.json').read_text())['training_through']>=pm['date']:
            raise ValueError('Model trained on target outcomes')
    else:raise ValueError('Unsupported probability release provenance')
    f=pd.read_csv(a.probabilities/'team_win_probabilities.csv');q=pd.read_csv(a.benchmark/'winner_benchmark.csv')
    if f.game_id.duplicated().any() or q.duplicated(['game_id','team']).any():raise ValueError('Duplicate source rows')
    if set(q.game_id)!=set(f.game_id):raise ValueError('Unequal benchmark populations')
    bm=json.loads((a.boxscores/'metadata.json').read_text());boxes={};source_hashes={}
    for s in bm['sources']:
        if s['file'].startswith('boxscore_'):
            p=a.boxscores/s['file']
            if digest(p)!=s['sha256']:raise ValueError('Changed official source')
            b=json.loads(p.read_text());boxes[b['id']]=b;source_hashes[s['file']]=s['sha256']
    rows=[];coverage=[]
    for record in f.to_dict('records'):
        gid=record['game_id'];coverage.append(dict(game_id=gid,scored=gid in boxes))
        if gid in boxes:rows.extend(score_game(record,q[q.game_id.eq(gid)].to_dict('records'),boxes[gid]))
    scored=pd.DataFrame(rows)
    if scored.empty:raise ValueError('No completed games to score')
    metrics=scored.groupby('model').agg(games=('game_id','nunique'),brier=('brier','mean'),log_loss=('log_loss','mean'),
        favorite_accuracy=('correct_favorite','mean')).reset_index()
    wide=scored.pivot(index='game_id',columns='model',values='brier');intervals=[]
    for comparison in ['even_baseline','kalshi_home_midpoint']:
        delta=(wide.team_probability_trial-wide[comparison]).to_numpy();rng=np.random.default_rng(20261024)
        boot=rng.choice(delta,(10000,len(delta)),replace=True).mean(axis=1)
        intervals.append(dict(model='team_probability_trial',comparison=comparison,games=len(delta),brier_delta=delta.mean(),
            lower_95=np.quantile(boot,.025),upper_95=np.quantile(boot,.975)))
    a.out.mkdir(parents=True)
    for name,z in [('scored_predictions',scored),('metrics',metrics),('paired_uncertainty',pd.DataFrame(intervals)),('coverage',pd.DataFrame(coverage))]:z.to_csv(a.out/(name+'.csv'),index=False)
    (a.out/'README.md').write_text(f'''# Prospective probability comparison — {pm['date']}

{table(metrics)}

[Every game and forecast](scored_predictions.csv) · [Paired game-bootstrap differences](paired_uncertainty.csv).
All scores use the exact separately frozen pregame probabilities and quotes, with one HOME outcome per game.
The market uses the home contract midpoint directly, not an after-the-fact normalized or blended estimate.
Official final winners include overtime/shootouts. No source forecast is refitted or overwritten.
{scored.game_id.nunique()} games scored; {sum(not c['scored'] for c in coverage)} remain unscored.
This is a single slate, too small for promotion or stable calibration conclusions.

These are NHL-outcome probability scores, not exchange settlement/P&L validation: no fees, execution,
depth or actual trade prices. Rescheduled starts fail closed for rules review. The same-game complementary
away contract is validated but does not count as another independent game. Tied 50/50 predictions have
no favorite-accuracy score. Original contract rules and quote timestamps remain in the benchmark.
The earlier retrospective probability-development screen is not pooled into this prospective sample.
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),date=pm['date'],
        probability_manifest_sha256=digest(a.probabilities/'manifest.json'),benchmark_manifest_sha256=digest(a.benchmark/'manifest.json'),
        boxscores=str(a.boxscores),boxscores_metadata_sha256=digest(a.boxscores/'metadata.json'),official_source_hashes=source_hashes,
        scoring='one home binary outcome per game; official NHL winners; not exchange settlement validation',
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    root=Path('data/processed/prediction_history')
    for source,kind in [(a.probabilities,'probability_predictions'),(a.benchmark,'market_benchmarks'),(a.out,'probability_evaluations')]:archive_snapshot(source,root,kind)
    print(metrics.to_string(index=False));print('Probability evaluation:',a.out)


if __name__=='__main__':main()
