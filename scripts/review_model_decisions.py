#!/usr/bin/env python3
"""Compare saved fantasy/role forecasts and screen a new team probability baseline."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files, digest, summarize_errors
from scripts.write_october_13_review import clustered_difference
from scripts.evaluate_october_9 import table
from src.fantasy.team_probability import scoring_win_probability


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--review', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise ValueError('Preserve earlier decision reviews')
    m = verify_manifest_files(a.review, [])
    players, teams, goalies, starters = [], [], [], []
    for path in m['evaluations']:
        root = Path(path)
        em = verify_manifest_files(root, [])
        if em['actuals_manifest_sha256'] != m['actuals_sha256']:
            raise ValueError('Mixed actual vintages')
        if digest(Path(em['frozen_bundle'])/'manifest.json') != em['frozen_bundle_manifest_sha256']:
            raise ValueError('Changed frozen predictions')
        for target, filename in [(players, 'simulation_summary'), (teams, 'team_projected_vs_actual'),
                                 (goalies, 'goalie_metrics'), (starters, 'goalie_starter_scores')]:
            file = root/(filename+'.csv')
            if file.exists():
                z = pd.read_csv(file)
                if 'issue_timing' in z:
                    z = z[z.issue_timing.eq('pregame')]
                target.append(z.assign(date=em['date']))
    p = pd.concat(players, ignore_index=True)
    p = p[p.actual.notna()]
    if p.duplicated(['game_id', 'player_id', 'model', 'category']).any():
        raise ValueError('Overlapping forecast cohorts')
    populations = [('all_players', p), ('saved_fantasy_roster', p[p.fantasy_team_name.fillna('').str.strip().ne('')])]
    populations += [('role_'+str(k), z) for k, z in p.groupby('position_group')]
    metrics, intervals, sensitivity = [], [], []
    for label, z in populations:
        metrics.append(summarize_errors(z, 'model_projection_if_plays').assign(population=label))
        for category, part in z.groupby('category'):
            intervals.append(clustered_difference(part, label).assign(category=category))
        for excluded in sorted(z.date.unique()):
            part = z[z.date.ne(excluded)]
            sensitivity.append(summarize_errors(part, 'model_projection_if_plays').assign(population=label, excluded_date=excluded))
    boxes = {}
    br = Path(m['boxscores'])
    for source in json.loads((br/'metadata.json').read_text())['sources']:
        if source['file'].startswith('boxscore_'):
            path = br/source['file']
            if digest(path) != source['sha256']:
                raise ValueError('Changed official outcome')
            b = json.loads(path.read_text()); boxes[b['id']] = b
    t = pd.concat(teams); t = t[t.category.eq('goals') & t.actual.notna()]
    probabilities = []
    for (gid, model), z in t.groupby(['game_id', 'model']):
        b = boxes[gid]; h, away = b['homeTeam'], b['awayTeam']
        z = z.set_index('team')
        if set(z.index) != {h['abbrev'], away['abbrev']} or len(z) != 2:
            raise ValueError('Incomplete team pair')
        prob = scoring_win_probability(z.loc[h['abbrev'], 'projection_mean'], z.loc[away['abbrev'], 'projection_mean'])
        outcome = int(h['score'] > away['score'])
        probabilities.append(dict(game_id=gid, date=b['gameDate'], model=model, home=h['abbrev'], away=away['abbrev'],
            home_win_probability=prob, home_won=outcome, brier=(prob-outcome)**2,
            log_loss=-np.log(np.clip(prob if outcome else 1-prob, 1e-12, 1)),
            evidence='retrospective_probability_transform_of_frozen_means'))
    probs = pd.DataFrame(probabilities)
    pm = []
    for model, z in probs.groupby('model'):
        rng = np.random.default_rng(20261024)
        delta = z.brier.to_numpy() - .25
        boot = rng.choice(delta, (10000, len(delta)), replace=True).mean(axis=1)
        pm.append(dict(model=model, games=len(z), brier=z.brier.mean(), log_loss=z.log_loss.mean(),
            delta_vs_even=delta.mean(), lower_95=np.quantile(boot,.025), upper_95=np.quantile(boot,.975)))
    pm = pd.DataFrame(pm)
    reliability = probs.assign(bin=pd.cut(probs.home_win_probability, [0,.4,.5,.6,1], include_lowest=True)).groupby(['model','bin'], observed=True).agg(games=('game_id','size'),mean_probability=('home_win_probability','mean'),home_win_rate=('home_won','mean')).reset_index()
    a.out.mkdir(parents=True)
    outputs = dict(population_metrics=pd.concat(metrics), paired_uncertainty=pd.concat(intervals),
        leave_one_date_out=pd.concat(sensitivity), goalie_metrics_by_date=pd.concat(goalies),
        team_probability_screen=probs, team_probability_metrics=pm, team_probability_reliability=reliability)
    if starters: outputs['starter_metrics_by_date'] = pd.concat(starters)
    for name, frame in outputs.items(): frame.to_csv(a.out/(name+'.csv'), index=False)
    fantasy = outputs['population_metrics']; fantasy = fantasy[fantasy.population.eq('saved_fantasy_roster') & fantasy.category.eq('shots')]
    (a.out/'README.md').write_text(f'''# Model decision evidence through {m['through']}

Research question: do saved forecasts justify changing fantasy category projections or introducing team win probabilities?

{p.game_id.nunique()} games across {p.date.nunique()} saved dates. All original forecasts remain unchanged.
Saved fantasy ownership defines the fantasy population; no current-roster relabeling.

## Fantasy shots

{table(fantasy[['model','rows_scored','mae','bias','interval_p10_p90_coverage']])}

[Paired game-bootstrap uncertainty, all categories and roles](paired_uncertainty.csv).
[Leave-one-date-out sensitivity](leave_one_date_out.csv). These are exploratory comparisons;
{p.date.nunique()} dates do not establish stable subgroup improvement. Do not tune corrections on the same evaluation sample.

## Team win-probability development screen

{table(pm)}

Independent Poisson counts from frozen team goal means; tied counts split 50/50.
Official final scores determine winners, including overtime/shootouts. Saved means cover full-game
scoring, so this is an approximate scoring-count model, not regulation/OT decomposition.
This pooled table applies the transform to all saved means and is a development screen.
Only separately timestamped probability releases qualify for prospective probability scoring;
evaluate those releases separately rather than labeling this entire pool prospective. No fitted calibration or home-ice
adjustment. Compare with the 50/50 baseline (Brier .25, log loss .6931).
Intervals resample games and do not resolve within-date dependence or multiple comparisons.
[Reliability bins](team_probability_reliability.csv) expose the small sample. Keep any new probabilities
as a separately frozen experimental release until future calibration and accuracy are assessed.

Goalie interval coverage and starter scores retain their own populations and dates in the CSVs.
No goalie interval widening or fantasy model promotion is automated by this script.
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        review=str(a.review), review_sha256=digest(a.review/'manifest.json'),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}), indent=2)+'\n')
    print(fantasy[['model','mae']].to_string(index=False)); print(pm.to_string(index=False))


if __name__ == '__main__': main()
