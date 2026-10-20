#!/usr/bin/env python3
"""Audit every final season game, with saved-forecast gaps and issue cohorts.

For the baseline, use the latest saved pregame *game-level* snapshot, not the
best-performing snapshot or a postgame refit. Compare daily models separately.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import CATEGORIES, evaluate, verify_manifest_files, digest, score_goalies
from scripts.review_forecast_week import summarize
from scripts.write_october_13_review import clustered_difference
from scripts.evaluate_october_9 import table
from src.fantasy.play_by_play import lagged_defense_context
from src.fantasy.per_game import require


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--actuals',type=Path,required=True); ap.add_argument('--boxscores',type=Path,required=True)
    ap.add_argument('--defense-pbp',type=Path,required=True); ap.add_argument('--through',required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); require(not a.out.exists(),'Preserve published review; choose a new directory')
    root=Path('data/processed/forecasts'); audit=[]
    am=verify_manifest_files(a.actuals,audit); verify_manifest_files(a.defense_pbp,audit)
    for source in am['sources']:
        for k in ['boxscore','landing']: require(digest(source[k])==source[k+'_sha256'],'Changed actual source')
    bm=json.loads((a.boxscores/'metadata.json').read_text())
    require(bm['through_eastern_date']==a.through and not bm['unfinished_games'],'Incomplete season schedule')
    boxes={}
    for source in bm['sources']:
        path=a.boxscores/source['file']; require(digest(path)==source['sha256'],'Changed official source')
        if source['file'].startswith('boxscore_'):
            b=json.loads(path.read_text()); boxes[b['id']]=b
    sk=pd.read_csv(a.actuals/'skater_game_stats.csv')
    require(set(sk.game_id)==set(boxes),'Actual/schedule coverage differs')
    require(not sk.duplicated(['game_id','player_id']).any(),'Duplicate actuals')
    require(sk[CATEGORIES].notna().all().all(),'Missing actual categories')
    positive=sk[sk.toi_seconds.gt(0)].copy()
    inventory=[]; forecasts=[]
    for folder in sorted(root.glob('per_game_*')):
        if not (folder/'manifest.json').exists() or not (folder/'scheduled_skater_game_forecasts.csv').exists(): continue
        m=verify_manifest_files(folder,audit)
        f=pd.read_csv(folder/'scheduled_skater_game_forecasts.csv')
        f=f[f.game_id.isin(boxes) & f.player_id.notna()].copy()
        before=pd.to_datetime(f.start_time_utc,utc=True)>pd.Timestamp(m['created_at_utc'])
        inventory.append(dict(source=str(folder),issued_at_utc=m['created_at_utc'],pregame_games=f.loc[before,'game_id'].nunique(),
            excluded_late_games=f.loc[~before,'game_id'].nunique()))
        f=f[before].sort_values('pool',ascending=False).drop_duplicates(['game_id','player_id'])
        f['issued_at_utc']=m['created_at_utc']; f['source']=str(folder)
        forecasts.append(f)
    f=pd.concat(forecasts,ignore_index=True)
    # One version per entire game avoids filling missing players with stale runs.
    chosen=f[['game_id','source','issued_at_utc']].drop_duplicates().sort_values(['issued_at_utc','source']).drop_duplicates('game_id',keep='last')
    f=f.merge(chosen,on=['game_id','source','issued_at_utc'],validate='many_to_one')
    means=[c+'_if_plays' for c in CATEGORIES]
    baseline=positive.merge(f[['game_id','player_id','source','issued_at_utc','pool','fantasy_team_name']+means],
        on=['game_id','player_id'],how='left',validate='one_to_one')
    coverage=[]
    for gid,b in sorted(boxes.items()):
        z=baseline[baseline.game_id.eq(gid)]
        coverage.append(dict(game_id=gid,date=b['gameDate'],away=b['awayTeam']['abbrev'],home=b['homeTeam']['abbrev'],
            appearances=len(z),covered=int(z.shots_if_plays.notna().sum()),missing=int(z.shots_if_plays.isna().sum()),
            baseline_source=z.source.dropna().iloc[0] if z.source.notna().any() else 'not_issued',
            issued_at_utc=z.issued_at_utc.dropna().iloc[0] if z.issued_at_utc.notna().any() else None))
    coverage=pd.DataFrame(coverage)
    baseline_rows=[]
    for pop,z in [('all_covered',baseline),('saved_fantasy_roster',baseline[baseline.pool.eq('rostered')])]:
        for c in CATEGORIES:
            zz=z.copy(); zz['population']=pop; zz['category']=c
            baseline_rows.append(summarize(zz,['population','category'],c+'_if_plays',c))
    base_metrics=pd.concat(baseline_rows)
    by_date=[]
    for c in CATEGORIES:
        z=summarize(baseline,['game_date'],c+'_if_plays',c); z['category']=c; by_date.append(z)
    # Canonical daily bundle per date: most recent completed build, independent of outcomes.
    bundles={}
    for folder in sorted(root.glob('daily_*')):
        if folder.name.startswith('daily_evaluation_') or not (folder/'manifest.json').exists(): continue
        m=json.loads((folder/'manifest.json').read_text())
        if m.get('date','9999')>a.through: continue
        if not (folder/'simulation_summary.csv').exists(): continue
        if m['date'] not in bundles or m['created_at_utc']>bundles[m['date']][0]: bundles[m['date']]=(m['created_at_utc'],folder)
    ps=[]; ts=[]; gs=[]; eval_paths=[]
    for _,folder in sorted(bundles.values()):
        m=json.loads((folder/'manifest.json').read_text()); goalie=None
        if not m.get('goalie_source'):
            choices=[]
            for candidate in root.glob('goalies_'+m['date']+'_*'):
                gm=json.loads((candidate/'manifest.json').read_text())
                choices.append((gm['created_at_utc'],candidate))
            goalie=str(max(choices)[1]) if choices else None
        ev=evaluate(folder,a.actuals,a.boxscores,root,goalie); eval_paths.append(str(ev))
        for collection,name in [(ps,'simulation_summary'),(ts,'team_projected_vs_actual'),(gs,'goalie_projections')]:
            path=ev/(name+'.csv')
            if path.exists():
                z=pd.read_csv(path); collection.append(z[z.issue_timing.eq('pregame')])
    p=pd.concat(ps); t=pd.concat(ts); g=pd.concat(gs)
    model_metrics=[]
    for level,z,pred in [('player',p,'model_projection_if_plays'),('team',t,'projection_mean')]:
        m=summarize(z,['model','category'],pred,'actual'); m['level']=level; model_metrics.append(m)
    fantasy=p[p.fantasy_team_name.fillna('').str.strip().ne('')]
    m=summarize(fantasy,['model','category'],'model_projection_if_plays','actual'); m['level']='saved_fantasy_player'; model_metrics.append(m)
    for c in ['shots_against','saves','goals_against']:
        z=g[g.eligible_for_conditional_count_scoring.eq(True) & g.actual_starter.eq(1)]
        m=summarize(z,['model'],c+'_if_full_start','actual_'+c); m['category']=c; m['level']='goalie'; model_metrics.append(m)
    metrics=pd.concat(model_metrics,ignore_index=True)
    shot=p[p.category.eq('shots') & p.actual.notna()]
    uncertainty=clustered_difference(shot,'daily_trial_all_players')
    # October 9 issued simulations are retained as a distinct older trial cohort.
    archived=[]
    for folder in sorted(root.glob('simulation_*')):
        if not (folder/'simulation_summary.csv').exists(): continue
        m=verify_manifest_files(folder,audit); z=pd.read_csv(folder/'simulation_summary.csv')
        if 'start_time_utc' not in z or 'mean_if_plays' not in z: continue
        z=z[z.game_id.isin(boxes) & (pd.to_datetime(z.start_time_utc,utc=True)>pd.Timestamp(m['created_at_utc']))]
        if z.empty: continue
        observed=positive.melt(id_vars=['game_id','player_id'],value_vars=CATEGORIES,var_name='category',value_name='actual')
        z=z.merge(observed,on=['game_id','player_id','category'],how='left',validate='many_to_one')
        z['source']=str(folder)
        archived.append(summarize(z,['source','model','category'],'mean_if_plays','actual'))
    # Independently issued October 9 opponent SOG and goalie trials precede the
    # daily-bundle format. Score their actual saved means as separate cohorts.
    legacy=[]; legacy_goalies=[]
    opponent_runs=sorted(root.glob('opponent_sog_trial_2026-10-09_*'))
    if opponent_runs:
        folder=opponent_runs[-1]; om=verify_manifest_files(folder,audit)
        q=pd.read_csv(folder/'player_sog_forecasts.csv')
        q=q[q.game_id.isin(boxes)].copy()
        q['start'] = q.game_id.map({gid:b['startTimeUTC'] for gid,b in boxes.items()})
        q=q[pd.to_datetime(q.start,utc=True)>pd.Timestamp(om['created_at_utc'])]
        q=q.merge(positive[['game_id','player_id','shots']],on=['game_id','player_id'],how='left',validate='many_to_one')
        q['source']=str(folder); q['category']='shots'
        legacy.append(summarize(q,['source','model','category'],'adjusted_shots_if_plays','shots'))
    goalie_runs=sorted(root.glob('goalies_2026-10-09_*'))
    if goalie_runs:
        folder=goalie_runs[-1]; gm=verify_manifest_files(folder,audit)
        q=pd.read_csv(folder/'goalie_game_forecasts.csv')
        q=q[q.game_id.isin(boxes)].copy()
        q['start_time_utc']=q.game_id.map({gid:b['startTimeUTC'] for gid,b in boxes.items()})
        q['issue_timing']=np.where(pd.to_datetime(q.start_time_utc,utc=True)>pd.Timestamp(gm['created_at_utc']),'pregame','late_not_pregame')
        simulations=pd.read_csv(folder/'goalie_simulation_summary.csv')
        for c in ['shots_against','saves','goals_against']:
            sims=simulations[simulations.category.eq(c)][['game_id','player_id','model','simulation_p10','simulation_p90']]
            q=q.merge(sims.rename(columns={k:c+'_'+k for k in ['simulation_p10','simulation_p90']}),on=['game_id','player_id','model'],validate='one_to_one')
        q,_,_=score_goalies(q,pd.read_csv(a.actuals/'goalie_game_stats.csv'))
        q=q[q.issue_timing.eq('pregame') & q.eligible_for_conditional_count_scoring.eq(True) & q.actual_starter.eq(1)]
        q['source']=str(folder)
        for c in ['shots_against','saves','goals_against']:
            z=summarize(q,['source','model'],c+'_if_full_start','actual_'+c); z['category']=c
            legacy_goalies.append(z)
    defense=lagged_defense_context(pd.read_csv(a.defense_pbp/'defense_team_games.csv'),
        pd.read_csv(a.defense_pbp/'source_audit.csv'),str(pd.Timestamp(a.through).date()+pd.Timedelta(days=1)))
    coverage['daily_trial']=coverage.game_id.isin(p.game_id)
    a.out.mkdir(parents=True)
    files=dict(game_coverage=coverage,baseline_metrics=base_metrics,baseline_by_date=pd.concat(by_date),
        model_metrics=metrics,game_cluster_uncertainty=uncertainty,defense_context=defense,
        saved_run_inventory=pd.DataFrame(inventory))
    if archived: files['archived_issued_simulation_metrics']=pd.concat(archived)
    if legacy: files['archived_opponent_metrics']=pd.concat(legacy)
    if legacy_goalies: files['archived_goalie_metrics']=pd.concat(legacy_goalies)
    for name,z in files.items(): z.to_csv(a.out/(name+'.csv'),index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,4))
    daily=coverage.groupby('date')[['appearances','covered']].sum()
    ax.bar(daily.index,daily.appearances,label='All final appearances',color='#ccd6dd')
    ax.bar(daily.index,daily.covered,label='Saved baseline coverage',color='#246b88')
    ax.tick_params(axis='x',rotation=65); ax.set_ylabel('Positive-TOI skater appearances'); ax.legend()
    fig.tight_layout(); fig.savefig(a.out/'season_coverage.png',dpi=150); plt.close(fig)
    headline=metrics[metrics.category.eq('shots')][['level','model','rows','games','mae','bias']]
    goalie=metrics[metrics.level.eq('goalie')][['model','category','rows','games','mae','bias']]
    (a.out/'README.md').write_text(f'# Season-to-date review through {a.through}\n\n'
        f'{len(boxes)} final regular-season games, {len(positive):,} positive-TOI skater appearances; '
        f'{int(baseline.shots_if_plays.notna().sum()):,} have saved baseline means. '
        f'{int(coverage.covered.eq(0).sum())} games have no saved baseline forecast. '
        f'Daily challenger comparison covers {p.game_id.nunique()} pregame games. No missing predictions are reconstructed.\n\n'
        '## Coverage\n\n![Season coverage](season_coverage.png)\n\n'
        '[Every game and missing-player count](game_coverage.csv). The baseline selects the most recently created saved pregame '
        'season-rate snapshot for each entire game, before examining errors. This is a changing forecast policy, not one fixed '
        'model/version or a complete season backtest. It does not fill missing players from older runs. '
        'No-appearance forecasts are not scored as zeros. Skaters and goalies remain separate.\n\n'
        '## Baseline, all covered appearances\n\n'+table(base_metrics[base_metrics.population.eq('all_covered')])+ '\n\n'
        '## Issued daily trial comparison\n\n'+table(headline)+'\n\n'
        '[All categories, fantasy subgroup, RMSE and bias](model_metrics.csv). Same saved games/positive-TOI appearances per model; '
        'team errors use issued lineup scenarios, not postgame participant sums. '
        '[Paired game-bootstrap deltas](game_cluster_uncertainty.csv) are exploratory; player rows are not independent games. '
        'The five-model comparative sample remains October 10/12. The October 9 issued simulation cohort is exported '
        'separately; retrospective October 8 calibration reconstructions and October 9 combined-model reconstructions are excluded '
        'from prospective comparisons. Independently issued October 9 trials are refreshed against the same official actuals '
        'in [opponent SOG metrics](archived_opponent_metrics.csv) and [goalie metrics](archived_goalie_metrics.csv). '
        'Keep these older input/format cohorts separate from the daily trial.\n\n'
        '## Goalies\n\n'+table(goalie)+'\n\n'
        'Eligible actual starts only; full-start means do not model pulls or empty-net duration. Keep saves and GA conclusions separate.\n\n'
        '## Defense chance-creation data\n\n[Past-only team context](defense_context.csv): all-strength and 5v5 D attempts, '
        'unblocked attempts, SOG, near-net attempts, assist credits, goals involving a D shooter/assistant, and short same-team '
        'followups after a D attempt. Near-net uses a 25-foot attacking-net distance, not a learned xG definition. '
        'Followups are within 10 seconds, stop at whistles/period changes/opponent shot attempts or recorded puck actions, '
        'and are temporal associations rather than passes or verified possessions. '
        'PBP/boxscore disagreements quarantine both teams of the affected games. Counts per game are not per-60 on-ice rates. '
        'No D feature coefficient is fitted. See [source strategy](../../../docs/DATA_SOURCE_STRATEGY.md).\n\n'
        '## Release fixes\n\nA single command now refreshes inputs, builds all five skater/two goalie models and finalizes '
        'reader views. Publication checks require prior-day history, fresh injury/context retrievals, official game/team '
        'coverage, finite means, goalie count identities, no outcomes and at least ten minutes before every start. '
        'Late builds fail instead of becoming an issued pregame bundle. See NEXT_STEPS.md for the command and limits.\n')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        through=a.through,actuals=str(a.actuals),actuals_sha256=digest(a.actuals/'manifest.json'),
        boxscores=str(a.boxscores),defense_pbp=str(a.defense_pbp),evaluations=eval_paths,
        baseline_selection='latest saved pregame snapshot per game; no performance selection',hash_checks=len(audit),
        files={f.name:digest(f) for f in a.out.iterdir() if f.is_file()}),indent=2)+'\n')
    print('Season review:',a.out)
    print('Final games:',len(boxes),'Covered player games:',int(baseline.shots_if_plays.notna().sum()))


if __name__=='__main__': main()
