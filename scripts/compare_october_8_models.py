#!/usr/bin/env python3
"""Evaluate frozen October 8 means; never refit calibration using these outcomes."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from src.fantasy.per_game import require, forecast
from src.fantasy.game_calibration import apply_calibration


def table(frame):
    def cell(v):
        return f'{v:.3f}' if isinstance(v,float) else str(v)
    return '\n'.join(['| '+' | '.join(frame.columns)+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+
        ['| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path,required=True)
    parser.add_argument('--fantasy-games',type=Path)
    parser.add_argument('--latest-forecast',type=Path,required=True)
    args=parser.parse_args()
    baseline=Path('data/processed/forecasts/per_game_20262027_20261008T203040Z')
    candidate=Path('data/processed/forecasts/calibration_candidate_20261009T192106Z')
    frozen=json.loads((candidate/'manifest.json').read_text())
    for filename,expected in frozen['files'].items():
        require(hashlib.sha256((candidate/filename).read_bytes()).hexdigest()==expected,'Candidate hash mismatch')
    require(frozen['config']['calibration_dates']==['2026-10-06','2026-10-07'],'Calibration dates changed')
    review_manifest=json.loads((args.review/'manifest.json').read_text())
    require(review_manifest['frozen_forecast']==str(baseline),'Unexpected evaluation baseline')
    joined=pd.read_csv(args.review/'frozen_forecast_vs_actual.csv')
    cand=pd.read_csv(candidate/'october_8_candidate_conditional_forecasts.csv')
    cols=['goals','assists','shots','points','hits','penalty_minutes','plus_minus','toi_minutes']
    candidate_cols={f'{c}_if_plays':f'candidate_{c}' for c in cols}
    joined=joined.merge(cand[['game_id','espn_player_id']+list(candidate_cols)].rename(columns=candidate_cols),
        on=['game_id','espn_player_id'],how='left',validate='one_to_one')
    if args.fantasy_games:
        stats=pd.read_csv(args.fantasy_games/'skater_game_stats.csv')
        joined=joined.merge(stats[['game_id','player_id','pp_points']],on=['game_id','player_id'],how='left',validate='many_to_one')
        cols.append('pp_points')
        joined['candidate_pp_points']=joined.pp_points_if_plays
    valid=joined[(joined.appeared==True)&joined.shots_if_plays.notna()].copy()
    require(set(valid.game_date)=={'2026-10-08'},'Unexpected evaluation dates')
    # Extra interpretable comparators use the original pregame panel, not refreshed inputs.
    panel=pd.read_csv(baseline/'validated_player_seasons.csv')
    bm=json.loads((baseline/'manifest.json').read_text())
    common=dict(lookback=bm['config']['lookback_seasons'],toi_prior_games=bm['config']['toi_prior_games'])
    for method,params in [('last_season',{}),('process',{k:v for k,v in bm['best_process'].items() if k not in ['score','method']})]:
        pred=forecast(panel,20262027,method=method,include_current=True,**common,**params)
        mapping={f'{c}_per_game':f'{method}_{c}' for c in cols}
        valid=valid.merge(pred[['player_id']+list(mapping)].rename(columns=mapping),on='player_id',how='left',validate='many_to_one')
    metrics=[]
    for group,frame in [('all_saved_pool',valid),('saved_scoring_roster',valid[valid.pool=='rostered'])]:
        for method in ['baseline','candidate','last_season','process']:
            for c in cols:
                pred_col=f'{c}_if_plays' if method=='baseline' else f'{method}_{c}'
                require(frame[[pred_col,c]].notna().all().all(),'Nonidentical model coverage')
                error=frame[pred_col]-frame[c]
                metrics.append(dict(group=group,model=method,category=c,player_games=len(frame),
                    projected=frame[pred_col].sum(),actual=frame[c].sum(),mae=error.abs().mean(),bias=error.mean(),rmse=(error.pow(2).mean())**.5))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=Path('data/processed/forecasts')/f'october_8_comparison_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    joined.to_csv(out/'projected_vs_actual_all_rows.csv',index=False)
    comparison_columns=['game_id','player_name','nhl_team_abbrev','opponent','pool','fantasy_team_name',
                        'injury_status','forecast_status','appearance_status']
    readable=joined[comparison_columns].copy()
    readable['projection_basis']='conditional_if_plays'
    readable['participation_forecast_status']='not_fitted'
    readable['candidate_timing']='retrospective_from_saved_pregame_inputs'
    readable['included_in_production_evaluation']=(joined.appeared==True)&joined.shots_if_plays.notna()
    for c in cols:
        readable[f'{c}_original_projection_if_plays']=joined[f'{c}_if_plays']
        readable[f'{c}_candidate_projection_if_plays']=joined[f'candidate_{c}']
        readable[f'{c}_actual']=joined[c]
    readable.to_csv(out/'player_comparison_readable.csv',index=False)
    readable[readable.included_in_production_evaluation].to_csv(out/'evaluated_player_comparison_readable.csv',index=False)
    valid.to_csv(out/'evaluated_player_appearances.csv',index=False)
    m=pd.DataFrame(metrics); m.to_csv(out/'model_metrics.csv',index=False)
    game_metrics=[]
    for gid,frame in valid.groupby('game_id'):
        for method in ['baseline','candidate']:
            for c in ['goals','assists','shots']:
                pred=frame[f'{c}_if_plays' if method=='baseline' else f'candidate_{c}']
                game_metrics.append(dict(game_id=gid,model=method,category=c,appearances=len(frame),
                    projected=pred.sum(),actual=frame[c].sum(),mae=(pred-frame[c]).abs().mean()))
    pd.DataFrame(game_metrics).to_csv(out/'by_game_metrics.csv',index=False)
    # ESPN ratio audit: empirical snapshot identities, not assumptions about all platform rules.
    latest=json.loads((args.latest_forecast/'manifest.json').read_text())
    future=pd.read_csv(args.latest_forecast/'scheduled_skater_game_forecasts.csv')
    apply_calibration(future,frozen['config']['factors']).to_csv(out/'latest_scheduled_candidate_forecasts.csv',index=False)
    espn=Path(latest['espn']['snapshot'])
    categories=pd.read_csv(espn/'matchup_categories.csv')
    wide=categories.pivot(index=['team_id','team_name'],columns='category',values='score').reset_index()
    checks=[]
    for _,r in wide.iterrows():
        for name,observed,calculated in [('ATOI',r['ATOI'],r['TTOI ?']/r['GP']),
            ('GAA',r['GAA'],r['GA']*3600/r['MIN ?']),('SV%',r['SV%'],r['SV']/r['SA'])]:
            checks.append(dict(team_id=r.team_id,team_name=r.team_name,category=name,observed=observed,
                recalculated=calculated,passed=bool(np.isclose(observed,calculated,rtol=1e-6,atol=1e-6))))
    audit=pd.DataFrame(checks); audit.to_csv(out/'espn_ratio_audit.csv',index=False)
    categories.to_csv(out/'current_espn_matchup_categories.csv',index=False)
    display=m[(m.group=='all_saved_pool')&m.model.isin(['baseline','candidate'])&m.category.isin(['goals','assists','shots'])]
    report=['# October 8 projected versus actual',
        '\nThe candidate was frozen using October 6–7 only and evaluated without retuning. '
        'Its October 8 predictions were reconstructed on October 9 from saved pregame features; '
        'the baseline was genuinely saved before puck drop. Do not call the candidate a forecast issued pregame.',
        '\n## Matched appearances',
        '\n'+table(display[['model','category','player_games','projected','actual','mae','bias','rmse']]),
        '\nResults concern production conditional on playing. Only actual appearances with baseline and '
        'candidate means enter these metrics. Absent/unknown players remain in the all-rows export; no zero '
        'production or appearance probability is invented. PPP comes from validated official scoring summaries.',
        '\n## Saved scoring-roster players across all six fantasy teams',
        '\n'+table(m[(m.group=='saved_scoring_roster')&m.model.isin(['baseline','candidate'])][['model','category','player_games','projected','actual','mae','bias']]),
        '\n## Additional frozen-input comparators',
        '\n'+table(m[(m.group=='all_saved_pool')&m.model.isin(['last_season','process'])&m.category.isin(['goals','assists','shots'])][['model','category','player_games','projected','actual','mae','bias']]),
        '\nThese diagnostic comparators use the same original October 8 panel and preselected parameters. '
        'Do not choose a new winner from this single night.',
        '\n## Coverage and stored sources',
        '\n'+table(pd.read_csv(args.review/'game_coverage.csv')[['game_date','matchup','score','actual_skater_rows']]),
        f'\nEvaluated {len(valid)} player appearances and {len(valid[valid.pool=="rostered"])} scoring-roster appearances. '
        f'Preserved {len(joined)} forecast rows. ESPN aliases are retained in `{args.review}/espn_alias_rows.csv` '
        'and deduplicated by NHL player/game for evaluation only. Forecast values for aliases agreed.',
        '\n## Latest stats and fantasy coverage',
        f'\nNew forecast build: `{args.latest_forecast}`. ESPN source: `{espn}`. '
        'Official current-season skater summary/TOI/realtime and separate goalie summary were refreshed; '
        'all historical season inputs were validated during the rebuild. NHL schedule and ESPN ownership, '
        'eligibility, injuries, current matchups and scored categories are refreshed.',
        f'\nESPN ratio checks passed: {int(audit.passed.sum())}/{len(audit)}. '
        'In this snapshot ATOI equals total skater TOI seconds divided by GP; GAA equals GA×3600/goalie TOI '
        'seconds; SV% equals SV/SA. ATOI is a ratio, not summed player average TOI. '
        'These empirical identities do not establish historical lineup eligibility or the unknown minimum goalie starts.',
        '\nPPP coverage is filled by goal/assist attribution using official strength labels; all skater G/A '
        'and PP goals must reconcile with boxscores. Separate goalie game rows preserve SA, SV, GA, '
        'TOI, wins and start flags. Unused backups have undefined ratios. Source-count exceptions remain flagged.',
        '\nThe full current-season archive covers all **65 completed regular-season games**, September 29 '
        'through October 8: **2,340 skater/game rows** and **260 goalie/game rows**, including unused backups. '
        'All ten cumulative skater categories reconcile for all **642 skaters** with latest NHL season reports '
        '(TOI within 0.02 minutes). The current goalie summary contains 60 appeared goalies and one '
        'SA=SV+GA exception; one game-level goalie count exception is also retained. Four October 9 '
        'games are not final and were excluded from actuals.',
        '\n## Decision and next work',
        '\nOn the full matched population, candidate SOG MAE fell 1.65% and assist MAE fell 1.05%. '
        'SOG bias changed from +0.062 to −0.057 per appearance; assist bias worsened from −0.003 to −0.015. '
        'Assist RMSE was essentially unchanged and slightly higher. Among scoring-roster players, '
        'SOG MAE improved 2.37%; assist MAE improved only 0.12% while underprediction increased. '
        'This mixed, small one-night result does not justify replacing the default.',
        '\nKeep the baseline as the live default. Compare changes in MAE as well as bias; lower totals alone '
        'do not prove better predictions. Preserve these candidate factors as tested, and collect more '
        'chronological games before considering promotion. Extend prior-season game logs and historical roster '
        'eligibility before fitting participation or rolling TOI. No opponent or goalie forecasting model '
        'has been fitted. October 8 is now observed evaluation data, not an untouched future tuning holdout.',
        '\n## Exports',
        f'\n[Readable player comparison](../../{out}/player_comparison_readable.csv) · '
        f'[Readable evaluated appearances](../../{out}/evaluated_player_comparison_readable.csv) · '
        f'[Full technical export](../../{out}/projected_vs_actual_all_rows.csv) · '
        f'[Evaluated player appearances](../../{out}/evaluated_player_appearances.csv) · '
        f'[Model metrics](../../{out}/model_metrics.csv) · [Per-game metrics](../../{out}/by_game_metrics.csv) · '
        f'[ESPN ratio audit](../../{out}/espn_ratio_audit.csv) · '
        f'[Latest future-game candidate forecasts](../../{out}/latest_scheduled_candidate_forecasts.csv)',
        f'\n[Full current-season skater game stats](../../{args.fantasy_games}/skater_game_stats.csv) · '
        f'[Separate goalie game stats](../../{args.fantasy_games}/goalie_game_stats.csv) · '
        f'[Game/season reconciliation](../../{args.fantasy_games}/cumulative_category_audit.csv)',
        f'\nGame review: `{args.review}`. Enriched fantasy games: `{args.fantasy_games}`. '
        f'Frozen candidate: `{candidate}`.',
        '\nThe readable comparison groups original projection if plays, candidate projection if plays, '
        'and actual for each category. It preserves absent players and missing forecasts with status labels. '
        'Actuals for players without matched boxscore rows stay missing, not zero. Participation-adjusted '
        '`expected_*` fields remain in the technical export and are undefined until a participation model is fitted.',
    ]
    Path('outputs/per_game_forecast/october_8_readout.md').write_text('\n'.join(report)+'\n')
    (out/'manifest.json').write_text(json.dumps(dict(review=str(args.review),candidate=str(candidate),
        baseline=str(baseline),fantasy_games=str(args.fantasy_games),latest_forecast=str(args.latest_forecast),
        candidate_sha256=hashlib.sha256((candidate/'manifest.json').read_bytes()).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}),indent=2)+'\n')
    print('Comparison output:',out)
    print(display.to_string(index=False))
    print('ESPN ratio audit:',audit.passed.value_counts().to_dict())


if __name__=='__main__':
    main()
