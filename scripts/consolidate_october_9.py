#!/usr/bin/env python3
"""Create one reader-facing bundle without changing frozen source artifacts."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from src.fantasy.simulation import simulate_counts
from src.fantasy.availability import excluded_by_status
from src.fantasy.per_game import require


def main():
    root=Path('data/processed/forecasts')
    individual=root/'simulation_2026-10-09_20261009T195119Z'
    team=root/'team_trial_2026-10-09_20261009T201330Z'
    context=root/'opponent_sog_trial_2026-10-09_20261009T225456Z'
    goalie=root/'goalies_2026-10-09_20261009T225533Z'
    sources=[individual,team,context,goalie]; manifests={}
    for source in sources:
        m=json.loads((source/'manifest.json').read_text()); manifests[source]=m
        for file,expected in m['files'].items():
            require(hashlib.sha256((source/file).read_bytes()).hexdigest()==expected,'Frozen source hash mismatch')
    out=root/'october_9_review'; out.mkdir(exist_ok=True)
    for existing in out.glob('*.csv'):
        saved=pd.read_csv(existing)
        actual_columns=[c for c in saved if c=='actual' or c.startswith('actual_')]
        require(not any(saved[c].notna().any() for c in actual_columns),
            'Consolidated view contains actual results; preserve evaluated run before regenerating')
    base=pd.read_csv(individual/'simulation_summary.csv')
    injury=pd.read_csv(context/'pregame_injury_context.csv').set_index('player_id')
    base['injury_status_at_original_issue']=base.injury_status
    base['injury_status_latest']=base.player_id.map(injury.injury_status).fillna('UNKNOWN')
    base['injury_status_as_of_utc']=manifests[context]['injuries_as_of_utc']
    base['excluded_from_trial_lineup']=base.injury_status_latest.map(excluded_by_status)
    base['source_model_issued_at_utc']=manifests[individual]['created_at_utc']
    adjusted=base[base.model=='default'].copy(); adjusted['model']='opponent_form_sog_trial'
    adjusted['source_model_issued_at_utc']=manifests[context]['created_at_utc']
    updates=pd.read_csv(context/'player_sog_simulation_summary.csv').set_index(['game_id','player_id'])
    for idx,row in adjusted[adjusted.category=='shots'].iterrows():
        upd=updates.loc[(row.game_id,row.player_id)]
        for c in ['mean_if_plays','simulated_mean','simulation_p10','simulation_median','simulation_p90']:
            adjusted.at[idx,c]=upd[c]
        adjusted.at[idx,'probability_at_least_one_if_plays']=1-np.exp(-upd.mean_if_plays)
    players=pd.concat([base,adjusted],ignore_index=True).rename(columns={'mean_if_plays':'model_projection_if_plays'})
    players['actual']=np.nan; players['absolute_error']=np.nan
    primary=['game_id','team','opponent','player_name','player_id','model','category','model_projection_if_plays',
        'actual','absolute_error','injury_status_latest','excluded_from_trial_lineup','simulation_median','simulation_p10','simulation_p90',
        'probability_at_least_one_if_plays','simulated_mean','injury_status_at_original_issue','injury_status_as_of_utc',
        'source_model_issued_at_utc','population','distribution_status']
    players=players[primary].sort_values(['game_id','team','player_name','category','model'])
    players.to_csv(out/'simulation_summary.csv',index=False)
    old_team=pd.read_csv(team/'team_projected_vs_actual.csv')
    old_team['lineup_version']='original_trial'
    old_team['source_inputs_frozen_at_utc']=manifests[team]['created_at_utc']
    old_team['derivation_status']='original_pregame_team_artifact'
    lineup=pd.read_csv(context/'trial_lineup_audit.csv')
    new_team=[]
    for (gid,t),selection in lineup[lineup.selected_for_trial].groupby(['game_id','team']):
        ids=set(selection.player_id); opponent=selection.opponent.iloc[0]
        for model,frame in players[(players.game_id==gid)&(players.team==t)&players.player_id.isin(ids)].groupby('model'):
            totals={e:np.zeros(10000,dtype=np.int64) for e in ['goals','assists','shots','hits','points','pp_points']}
            means={e:0. for e in totals}
            for pid,p in frame.groupby('player_id'):
                values=p.set_index('category').model_projection_if_plays.to_dict()
                sample=simulate_counts(values,draws=10000,seed=manifests[individual]['seed'],key=f'{gid}:{pid}')
                for e in totals: totals[e]+=sample[e]; means[e]+=values[e]
            for e,draws in totals.items():
                guess=max(0,int(np.ceil(means[e]))-1)
                new_team.append(dict(game_id=gid,team=t,opponent=opponent,model=model,category=e,
                    projection_mean=means[e],whole_number_guess=guess,probability_of_guess=float((draws==guess).mean()),
                    simulation_p10=int(np.quantile(draws,.1,method='inverted_cdf')),
                    simulation_p90=int(np.quantile(draws,.9,method='inverted_cdf')),assumed_skaters=len(ids),
                    actual=np.nan,absolute_error=np.nan,exact_guess_correct=pd.NA,
                    lineup_version='refreshed_injury_trial',lineup_status='unconfirmed_12F_6D',
                    distribution_status='provisional_not_calibrated',
                    source_inputs_frozen_at_utc=manifests[context]['created_at_utc'],
                    derivation_status='derived_now_from_frozen_pregame_means_and_lineup'))
    teams=pd.concat([old_team,pd.DataFrame(new_team)],ignore_index=True).sort_values(['game_id','team','category','lineup_version','model'])
    teams.to_csv(out/'team_projected_vs_actual.csv',index=False)
    goalies=pd.read_csv(goalie/'goalie_game_forecasts.csv')
    gs=pd.read_csv(goalie/'goalie_simulation_summary.csv')
    for e in ['shots_against','saves','goals_against']:
        sub=gs[gs.category==e].drop(columns=['category','date','team','opponent','player_name','basis'])
        sub=sub.rename(columns={c:f'{e}_{c}' for c in ['simulated_mean','simulation_p10','simulation_median','simulation_p90']})
        goalies=goalies.merge(sub,on=['game_id','player_id','model'],how='left',validate='one_to_one')
    for e in ['shots_against','saves','goals_against','wins','gaa','save_percentage']:
        goalies[f'actual_{e}']=np.nan
    goalies.to_csv(out/'goalie_projected_vs_actual.csv',index=False)
    cover=pd.read_csv(individual/'game_team_coverage.csv')
    cover.to_csv(out/'game_team_coverage.csv',index=False)
    lineage=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),sources=[str(p) for p in sources],
        source_manifest_sha256={str(p):hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest() for p in sources},
        note='Reader-facing consolidation. Added team aggregates are derived from frozen pregame inputs, not newly issued pregame forecasts. Actuals not acquired.',
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')})
    (out/'manifest.json').write_text(json.dumps(lineage,indent=2)+'\n')
    guide='''# October 9: consolidated comparison files

Start here. Four CSVs replace the need to navigate multiple runs.

- **simulation_summary.csv**: all skater models. `model_projection_if_plays` is the primary forecast; medians/ranges are simulation summaries. `opponent_form_sog_trial` changes shots only. Fresh injury labels are separate from original issue labels; excluded players retain conditional means.
- **team_projected_vs_actual.csv**: decimal means, whole-number modal guesses, probabilities, ranges and blank actual/error fields. Filter `lineup_version=refreshed_injury_trial` for the latest trial. Compare models within the same lineup version. `original_trial` preserves the earlier roster scenario.
- **goalie_projected_vs_actual.csv**: both goalie models, latest injury exclusions, conditional full-60-minute forecasts, start shares, simulation summaries and blank actuals. Start shares and win proxies are provisional, not confirmed starters.
- **game_team_coverage.csv**: all four games/eight teams and original official-roster model coverage. The team scenarios assume 18 selected skaters; coverage refers to the larger official roster.

Actual/error columns intentionally remain empty until final outcomes are acquired. These are conditional or assumed-lineup scenarios, not calibrated unconditional predictions. Team goals exclude shootout deciding goals. Never sum player SV% or GAA.

The folder is a derived view; frozen source runs are preserved and listed in manifest.json. Refreshed-lineup team aggregates were assembled during consolidation from already-frozen pregame means and selection rules. Their creation time must not be mistaken for a new pregame forecast issue time.

Regenerate with `rink-lab.venv/bin/python scripts/consolidate_october_9.py`. Regeneration replaces this derived view and resets actual columns; after evaluation, preserve the evaluated version in a new run before regeneration.
'''
    (out/'README.md').write_text(guide)
    require(cover.game_id.nunique()==4,'Missing game coverage')
    require(len(players)==178*3*6 and len(teams)==8*6*5 and len(goalies)==36,'Unexpected consolidated coverage')
    print('Consolidated folder:',out)
    print('Player summary rows:',len(players),'Team rows:',len(teams),'Goalie rows:',len(goalies))


if __name__=='__main__': main()
