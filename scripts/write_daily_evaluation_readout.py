#!/usr/bin/env python3
"""Readable results from an immutable daily evaluation, with issue-time scope."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_october_9 import table


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--evaluation',type=Path,required=True)
    ap.add_argument('--previous-evaluation',type=Path)
    args=ap.parse_args();p=args.evaluation;m=json.loads((p/'manifest.json').read_text())
    for f,h in m['files'].items():assert hashlib.sha256((p/f).read_bytes()).hexdigest()==h
    bundle=Path(m['frozen_bundle']);bm=json.loads((bundle/'manifest.json').read_text())
    def metrics(name):
        x=pd.read_csv(p/(name+'.csv'));return x[x.issue_timing=='pregame']
    pm=metrics('player_metrics');tm=metrics('team_metrics');fm=metrics('fantasy_player_metrics')
    summary=pm[pm.category=='shots'][['model','rows_scored','mae','predicted_total','actual_total']].rename(columns={'mae':'player_sog_mae'})
    summary=summary.merge(tm[tm.category=='shots'][['model','mae']].rename(columns={'mae':'team_sog_mae'}),on='model')
    summary=summary.merge(fm[fm.category=='shots'][['model','mae']].rename(columns={'mae':'fantasy_player_sog_mae'}),on='model')
    teams=pd.read_csv(p/'team_projections.csv');teams=teams[teams.issue_timing=='pregame']
    comparison=teams.pivot(index=['game_id','team','opponent','actual_shots'],columns='model',values='expected_shots').reset_index()
    coverage=metrics('game_team_coverage');ngames=coverage.game_id.nunique()
    matches=[]
    for gid in coverage.game_id.unique():
        b=json.loads((Path(m['boxscores'])/f'boxscore_{gid}.json').read_text())
        matches.append(dict(game_id=gid,matchup=b['awayTeam']['abbrev']+' @ '+b['homeTeam']['abbrev'],score=str(b['awayTeam']['score'])+'–'+str(b['homeTeam']['score'])))
    age=(pd.Timestamp(bm['created_at_utc'])-pd.Timestamp(bm['injuries_as_of_utc'])).total_seconds()/3600
    lines=[f'# {m["date"]} model results',
        f'\nPrimary comparison: {ngames} games with forecasts issued before puck drop, {coverage.actual_skaters.sum()} actual skater appearances. All five models cover the same appearances. Saved issue: {bm["created_at_utc"]}.',
        '\n'+table(pd.DataFrame(matches)),
        '\n## Shot performance', '\n'+table(summary),
        '\nMAE is average absolute error; lower is better. Player totals refer to actual appearances. Team projections use frozen assumed lineups and may differ from the player total. Candidate was best on all-player, team and fantasy-player SOG MAE for this slate. The opponent-only model increased error; adding it to candidate also hurt. The usage model improved on default for all players but did not beat candidate.',
        '\n## Team shots projected versus actual', '\n'+table(comparison),
        '\nWhole-number exact team SOG guess rates (small samples):\n'+table(tm[tm.category=='shots'][['model','exact_guess_rows','exact_guess_rate']]),
        '\n## Other categories', '\n'+table(pm[pm.model.isin(['default','candidate','usage_shot_context_trial']) & pm.category.ne('shots')][['model','category','rows_scored','mae','predicted_total','actual_total']]),
        '\nGoals, hits, PIM, plus/minus and PPP means are shared across these models. Candidate changes assists and derived points. Usage changes shots and TOI. This is a small-slate diagnostic; aggregate overprediction does not justify fitting a new correction on these same outcomes.',
        '\n## Goalies',
    ]
    if (p/'goalie_metrics.csv').exists():
        gm=metrics('goalie_metrics');gm=gm[gm.population=='actual_starters']
        lines += ['\n'+table(gm[['model','category','rows_scored','mae','predicted_total','actual_total']]),
            '\nGoalie opponent context improves shot/save errors on these four starts, but goals-against error is slightly worse. These are full-60-minute conditional forecasts; actual starts may end early for empty-net play. Team shots and goals can include empty-net events and need not equal goalie-denominator totals. Starter probabilities remain provisional.']
    else:lines += ['\nNo saved goalie projections were available to evaluate.']
    if args.previous_evaluation:
        older=pd.read_csv(args.previous_evaluation/'fantasy_player_metrics.csv')
        pooled=pd.concat([older,fm]);pooled=pooled[(pooled.issue_timing=='pregame')&(pooled.category=='shots')].copy()
        pooled['absolute_error_sum']=pooled.mae*pooled.rows_scored
        agg=pooled.groupby('model').agg(appearances=('rows_scored','sum'),absolute_error_sum=('absolute_error_sum','sum'))
        agg['mae']=agg.absolute_error_sum/agg.appearances
        lines += ['\n## Does this change the fantasy recommendation?', '\n'+table(agg.reset_index()[['model','appearances','mae']]),
            '\nThis combines the October 10 and October 12 prospective fantasy cohorts. Candidate wins the latest night, while default still has slightly lower combined error. Keep both visible; do not promote or retune a model based on two games. Test role/TOI-based calibration and isolate the usage model’s TOI, rate and context changes.']
    lines += ['\n## Coverage and input limitations', '\n'+table(coverage[['team','actual_skaters','actual_skaters_with_forecast','selected_lineup_actual_overlap','selected_identified_nonparticipants']]),
        f'\nInjury labels were retrieved at {bm["injuries_as_of_utc"]}, approximately {age:.1f} hours before issuance. MoneyPuck inputs came from `{bm["moneypuck_snapshot"]}` and lacked more recent game updates. NHL statistical inputs were cut off before the target date; no target-day outcomes were used.',
        '\nFlorida–Buffalo’s afternoon game was already final at issuance. Its late rows are retained in the evaluation files and excluded from every pregame table above. The separately saved goalie run and wide reading views are joined only in the evaluation output; frozen forecasts are preserved.',
        '\nBefore the next release, refresh ESPN injuries and MoneyPuck context, check starters and lineup coverage, then freeze the full skater/goalie bundle before first puck drop. Do not silently treat older availability data as freshly retrieved.',
        '\n## Files',
        f'\n[Player-by-player results](../../{p}/player_projections.csv) · [Team results](../../{p}/team_projections.csv) · [Evaluation guide](../../{p}/README.md)',
    ]
    if (p/'goalie_projections.csv').exists():lines += [f'\n[Goalie results](../../{p}/goalie_projections.csv)']
    lines += [f'\nEvaluation: `{p}`. Frozen skaters: `{bundle}`. Frozen goalies: `{m.get("external_goalie_source")}`.',
        '\n```sh\nrink-lab.venv/bin/python scripts/write_daily_evaluation_readout.py \\\n'+f'  --evaluation {p}'+(f' \\\n  --previous-evaluation {args.previous_evaluation}' if args.previous_evaluation else '')+'\n```']
    out=Path('outputs/per_game_forecast')/(m['date']+'_results_readout.md');out.write_text('\n'.join(lines)+'\n');print(out)

if __name__=='__main__':main()
