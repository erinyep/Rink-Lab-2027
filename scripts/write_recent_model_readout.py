#!/usr/bin/env python3
"""Summarize issued models on identical appearances, with ownership strata."""
import argparse
import json
from pathlib import Path
import sys
import hashlib
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_october_9 import table


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--bundle',type=Path,required=True)
    ap.add_argument('--actuals',type=Path,required=True)
    ap.add_argument('--boxscores',type=Path,required=True)
    ap.add_argument('--older-review',type=Path,required=True)
    ap.add_argument('--evaluation',type=Path)
    args=ap.parse_args()
    for p in [args.bundle,args.actuals]:
        m=json.loads((p/'manifest.json').read_text())
        for file,h in m['files'].items():
            assert hashlib.sha256((p/file).read_bytes()).hexdigest()==h
    p=args.bundle
    a=pd.read_csv(args.actuals/'skater_game_stats.csv');a=a[a.toi_seconds>0]
    s=pd.read_csv(p/'simulation_summary.csv')
    targets=['goals','assists','shots','hits','points','pp_points','penalty_minutes','plus_minus','toi_minutes']
    actual=a.melt(id_vars=['game_id','player_id'],value_vars=targets,var_name='category',value_name='observed')
    s=s.merge(actual,on=['game_id','player_id','category'],how='left',validate='many_to_one')
    s=s[s.observed.notna()].copy();s['error']=s.model_projection_if_plays-s.observed;s['ae']=abs(s.error)
    pre=s[s.issue_timing=='pregame'];shot=pre[pre.category=='shots']
    summary=shot.groupby('model').agg(appearances=('ae','size'),player_mae=('ae','mean'),predicted_shots=('model_projection_if_plays','sum'),actual_shots=('observed','sum')).reset_index()
    teams=pd.read_csv(p/'team_projected_vs_actual.csv');teams=teams[teams.issue_timing=='pregame'].copy()
    observations=[]
    for gid in teams.game_id.unique():
        b=json.loads((args.boxscores/f'boxscore_{gid}.json').read_text())
        assert b['gameState'] in ['OFF','FINAL']
        for side in ['homeTeam','awayTeam']:
            observations.append(dict(game_id=gid,team=b[side]['abbrev'],shots=b[side]['sog']))
    ts=teams[teams.category=='shots'].merge(pd.DataFrame(observations),on=['game_id','team'],validate='many_to_one')
    ts['ae']=abs(ts.projection_mean-ts.shots);ts['exact']=ts.whole_number_guess==ts.shots
    tm=ts.groupby('model').agg(team_mae=('ae','mean'),team_exact_guesses=('exact','sum')).reset_index()
    summary=summary.merge(tm,on='model',validate='one_to_one')
    fantasy=shot[shot.fantasy_team_name.notna()].groupby('model').agg(appearances=('ae','size'),mae=('ae','mean'),predicted_shots=('model_projection_if_plays','sum'),actual_shots=('observed','sum')).reset_index()
    owner=shot[shot.fantasy_team_name.notna() & shot.model.isin(['default','candidate'])].groupby(['fantasy_team_name','model']).agg(appearances=('ae','size'),mae=('ae','mean'),predicted_shots=('model_projection_if_plays','sum'),actual_shots=('observed','sum')).reset_index()
    cats=pre.groupby(['model','category']).agg(appearances=('ae','size'),mae=('ae','mean'),bias=('error','mean'),predicted_total=('model_projection_if_plays','sum'),actual_total=('observed','sum')).reset_index()
    # Resample games rather than treating teammates as independent evidence.
    common=shot.pivot(index=['game_id','player_id'],columns='model',values='ae')
    assert common.notna().all().all()
    diffs=common.subtract(common['default'],axis=0).groupby(level=0).mean()
    rng=np.random.default_rng(20261012);indices=rng.integers(0,len(diffs),(20000,len(diffs)))
    boot=diffs.to_numpy()[indices].mean(axis=1)
    uncertainty=pd.DataFrame(dict(model=diffs.columns,mae_difference_vs_default=diffs.mean().values,
        bootstrap_95_lower=np.quantile(boot,.025,axis=0),bootstrap_95_upper=np.quantile(boot,.975,axis=0),games_improved=(diffs<0).sum().values))
    g=pd.read_csv(p/'goalie_projections.csv');ga=pd.read_csv(args.actuals/'goalie_game_stats.csv')
    g=g[g.issue_timing=='pregame'].merge(ga,on=['game_id','player_id'],validate='many_to_one',suffixes=('','_observed'))
    g=g[(g.starter==True)&(g.count_identity_ok==True)]
    for c in ['shots_against','saves','goals_against']:g[c+'_ae']=abs(g[c+'_if_full_start']-g[c])
    goalies=g.groupby('model').agg(starters=('player_id','size'),shots_against_mae=('shots_against_ae','mean'),saves_mae=('saves_ae','mean'),goals_against_mae=('goals_against_ae','mean')).reset_index()
    older=pd.read_csv(args.older_review/'game_metrics.csv')
    later=older[(older.group=='all_saved_pool') & older.date.isin(['2026-10-11','2026-10-12']) & older.category.isin(['goals','assists','shots'])]
    coverage=pd.read_csv(args.older_review/'game_coverage.csv')
    bench=pd.read_csv(p/'player_projections.csv')[['game_id','player_id','model','espn_projected_sog_per_game']]
    paired=shot.merge(bench,on=['game_id','player_id','model'],validate='one_to_one');paired=paired[paired.espn_projected_sog_per_game.notna()]
    bm=paired.groupby('model').agg(appearances=('ae','size'),mae=('ae','mean')).reset_index()
    b=paired[paired.model=='default'];bm=pd.concat([bm,pd.DataFrame([dict(model='ESPN_season_average_benchmark',appearances=len(b),mae=abs(b.espn_projected_sog_per_game-b.observed).mean())])],ignore_index=True)
    lineup=pd.read_csv(p/'inputs/lineup_audit.csv')
    pregames=set(pre.game_id)
    actual_keys=set(zip(a.game_id,a.player_id))
    selected=lineup[lineup.game_id.isin(pregames)&lineup.selected_for_trial]
    lineup_overlap=sum((r.game_id,r.player_id) in actual_keys for r in selected.itertuples())
    big=ts[ts.model=='default'].sort_values('ae',ascending=False)[['team','opponent','projection_mean','shots','ae']].head(8)
    report=['# Recent model results — October 12, 2026',
        '\nDecision: keep default for fantasy-rostered player decisions tonight; retain candidate as the leading all-skater/team challenger. Avoid a stronger global shot reduction. Candidate improves the full population but worsens the saved fantasy-rostered cohort. The opponent effect has no clear incremental benefit. The new usage model improves TOI but has not established a shot-accuracy advantage over candidate.',
        '\n## Coverage and timing',
        '\nAll 18 completed games from October 10 through the October 12 Florida–Buffalo matinee have an older October 9-issued default projection available. The five-model prospective test is limited to 11 October 10 games: 396/396 observed skaters, 22 teams and 22 starters. Three early October 10 daily projections were issued late and are excluded from the primary model comparison. October 11 has three saved default forecasts but no newly issued five-model or goalie slate; October 12’s matinee likewise uses the older default.',
        '\nTonight: Ottawa–New Jersey at 7:00 PM Eastern; Vegas–Minnesota at 8:00 PM Eastern. Florida–Buffalo is already final. Schedule checked against the [official NHL feed](https://api-web.nhle.com/v1/schedule/2026-10-12). This report does not issue new October 12 predictions.',
        '\n## October 10: identical pregame populations', '\n'+table(summary),
        '\nPlayer MAE measures absolute error per appearance. Team MAE uses official NHL SOG and the same assumed lineup for every model; shots-against mirrors are not counted as extra samples. Exact guesses are out of 22 team outcomes. Candidate improves player SOG MAE about 1.4% and team SOG MAE about 7.9% versus default. Its total being close to actual does not imply accurate player allocation.',
        '\n## Fantasy-rostered players: the recommendation changes', '\n'+table(fantasy),
        '\nThese 78 appearances are identified using the saved pregame fantasy ownership, not current ownership or outcomes. Default underpredicted their combined shots by 16.89; candidate underpredicted by 31.65. Candidate was worse in player MAE for each of the six fantasy teams. Do not calibrate directly to fantasy ownership; test prior projected shot rate, position and TOI/PP role as hockey-relevant strata in later untouched games.',
        '\n'+table(owner),
        '\nQuinn Short for Quinnificent illustrates the difference: candidate’s aggregate total is close to 26 actual shots, but default has lower individual-player error. Totals can cancel errors across players.',
        '\n## Other categories and goalies', '\n'+table(cats[cats.category!='shots']),
        '\nUsage-model TOI MAE fell from 2.266 to 2.115 minutes (about 6.7%); its SOG MAE is still slightly worse than candidate. All models predicted 69.55 goals versus 57 across these appearances. Assists remained high after calibration (112.98 versus 94); hits and PPP totals were much closer. PIM was underestimated. These are diagnostics, not new fitted correction factors.',
        '\n'+table(goalies),
        '\nAll 22 scored starters played between 55 and 65 minutes. The opponent goalie trial improves saves slightly but worsens shots-against and goals-against errors slightly. There is no broad goalie winner. Starting probabilities, relief and duration remain separate evaluation targets in the detailed artifact.',
        '\n## Strength of evidence', '\n'+table(uncertainty),
        '\nApproximate 95% intervals resample 11 games, 20,000 times with seed 20261012, using equal-game mean paired errors. Negative values favor the trial. This small-sample exploratory bootstrap does not account for all model-selection comparisons. Candidate improves 9/11 games; usage improves 5/11 and its interval includes no improvement.',
        '\n## Independent ESPN benchmark', '\n'+table(bm),
        '\nThese are the same 200 appearances with an available frozen ESPN season-average projection. Do not compare these MAEs directly with the 396-player table. ESPN is competitive but provides no clear improvement, and is not matchup-adjusted here.',
        '\n## October 11 and today’s completed matinee', '\n'+table(later[['date','category','player_games','predicted_total','actual_total','mae','bias','rmse']]),
        '\nOctober 11 coverage is 104/108 actual skaters; today’s matinee is 36/36. These are older, previously issued default conditional forecasts, not reconstructed versions of the new models. Retain their age and population distinction.',
        '\n## Lineups and large misses',
        f'\nOf {len(selected)} named skaters selected in the eleven pregame lineup scenarios, {lineup_overlap} appeared. Montreal’s team scenario also included an unidentified defense replacement. Actual player forecasts cover all 396 appearances even when the lineup selection was wrong. Team lineup error and player rate error are distinct.',
        '\n'+table(big),
        '\n## Adjustments to prioritize before the next release',
        '\n1. Keep default visible for fantasy-rostered decisions and retain candidate as the all-skater/team challenger; do not strengthen the global calibration multiplier.\n2. Refresh tonight’s eligible rosters, injury labels and goalie starter information before issuance; preserve all timing labels.\n3. Split the next usage experiment into TOI-only, shot-rate-only and context-only versions. Keep the same lineup and evaluate paired outcomes.\n4. Evaluate calibration by pregame shot/TOI/position strata; current ownership reversal suggests a blanket multiplier is too coarse. Fit on past games and test later games, rather than tuning tonight’s factors to these results.\n5. Investigate goal and assist overprediction separately from SOG; save shares and goalie duration need their own validation.\n6. Maintain frozen sources and write evaluations to separate folders. A display-only fallback-label bug was corrected prospectively; original rookie rates already used shrinkage, and frozen forecasts remain unchanged.',
        '\n## Inspect and reproduce',
        f'\nFrozen daily bundle: `{args.bundle}`. Final enriched observations: `{args.actuals}`. Older baseline evaluation: `{args.older_review}`.',
        '\n[All recent game results](../../'+str(args.older_review)+'/game_coverage.csv) · [Older default player comparisons](../../'+str(args.older_review)+'/frozen_forecast_vs_actual.csv)',
    ]
    if args.evaluation:
        report += ['\n[Detailed daily evaluation](../../'+str(args.evaluation)+'/README.md)']
    report += ['\n```sh\nrink-lab.venv/bin/python scripts/write_recent_model_readout.py \\\n'+f'  --bundle {args.bundle} \\\n  --actuals {args.actuals} \\\n  --boxscores {args.boxscores} \\\n  --older-review {args.older_review}'+(f' \\\n  --evaluation {args.evaluation}' if args.evaluation else '')+'\n```']
    out=Path('outputs/per_game_forecast/recent_results_2026-10-12.md');out.write_text('\n'.join(report)+'\n')
    print(out);print(table(summary));print(table(fantasy))

if __name__=='__main__':main()
