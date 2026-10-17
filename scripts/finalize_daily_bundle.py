#!/usr/bin/env python3
"""Create compact team/player reading views without changing frozen means."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_october_9 import table


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--goalies',type=Path,required=True)
    a=ap.parse_args();p=a.bundle;m=json.loads((p/'manifest.json').read_text())
    report=Path('outputs/per_game_forecast')/f"{m['date']}_pregame_readout.md"
    if report.exists():
        report=report.with_name(f"{m['date']}_{p.name}_pregame_readout.md")
    if report.exists() or (p/'player_projections.csv').exists():
        raise FileExistsError('Reading views already issued; refusing to overwrite')
    for f,h in m['files'].items():assert sha(p/f)==h
    gm=json.loads((a.goalies/'manifest.json').read_text())
    for f,h in gm['files'].items():assert sha(a.goalies/f)==h
    s=pd.read_csv(p/'simulation_summary.csv');t=pd.read_csv(p/'team_projected_vs_actual.csv')
    keys=['game_id','player_id','model']
    wide=s.pivot(index=keys,columns='category',values='model_projection_if_plays').reset_index()
    wide=wide.rename(columns={c:'expected_'+c+'_if_plays' for c in ['goals','assists','shots','hits','points','pp_points','penalty_minutes','plus_minus','toi_minutes']})
    identity=['player_name','team','opponent','fantasy_team_name','injury_status','roster_source','fallback','issue_timing','start_time_utc']
    wide=s[keys+identity].drop_duplicates(keys).merge(wide,on=keys,validate='one_to_one')
    lineup=pd.read_csv(p/'inputs/lineup_audit.csv')
    wide=wide.merge(lineup[['game_id','player_id','selected_for_trial','selection_reason']],on=['game_id','player_id'],validate='many_to_one')
    pc=pd.read_csv(p/'player_context.csv')
    wide=wide.merge(pc[['game_id','player_id','recent_pp_toi_minutes_per_game','recent_ev_toi_minutes_per_game','espn_projected_sog_per_game']],on=['game_id','player_id'],validate='many_to_one')
    wide.sort_values(['issue_timing','team','player_name','model']).to_csv(p/'player_projections.csv',index=False)
    tk=['game_id','team','model'];tw=t.pivot(index=tk,columns='category',values='projection_mean').reset_index()
    tw=tw.rename(columns={c:'expected_'+c for c in ['goals','assists','shots','hits','points','pp_points']})
    ident=['opponent','issue_timing','start_time_utc','lineup_status','identified_skaters','unidentified_replacement_skaters']
    tw=t[tk+ident].drop_duplicates(tk).merge(tw,on=tk,validate='one_to_one')
    shots=t[t.category=='shots'][tk+['whole_number_guess','opponent_projection_mean']].rename(columns={'whole_number_guess':'shots_whole_number_guess','opponent_projection_mean':'expected_shots_against'})
    tw=tw.merge(shots,on=tk,validate='one_to_one')
    tw.to_csv(p/'team_projections.csv',index=False)
    g=pd.read_csv(a.goalies/'goalie_game_forecasts.csv');gs=pd.read_csv(a.goalies/'goalie_simulation_summary.csv')
    for category in ['shots_against','saves','goals_against']:
        subset=gs[gs.category==category][['game_id','player_id','model','simulation_p10','simulation_median','simulation_p90']]
        subset=subset.rename(columns={c:category+'_'+c for c in ['simulation_p10','simulation_median','simulation_p90']})
        g=g.merge(subset,on=['game_id','player_id','model'],validate='one_to_one')
    for c in ['shots_against','saves','goals_against','wins','gaa','save_percentage']:g['actual_'+c]=np.nan
    g.to_csv(p/'goalie_projections.csv',index=False)
    m['goalie_source']=str(a.goalies);m['goalie_manifest_sha256']=sha(a.goalies/'manifest.json')
    m['files']={f.name:sha(f) for f in p.glob('*.csv')}
    (p/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    coverage=pd.read_csv(p/'game_team_coverage.csv')
    timing=coverage[['game_id','issue_timing']].drop_duplicates()
    if timing.game_id.duplicated().any():
        raise ValueError('Conflicting game timing labels')
    if timing.game_id.nunique()!=m['games']:
        raise ValueError('Manifest/coverage game count mismatch')
    counts=timing.issue_timing.value_counts()
    replacements=coverage[coverage.missing_lineup_slots.gt(0)]
    guide=f"""# Daily projections — {m['date']}

Issued {m['created_at_utc']}. {m['games']} games:
{counts.get('pregame',0)} pregame, {counts.get('late_not_pregame',0)} late.
Filter `issue_timing=pregame` for prospective forecasts.

- `player_projections.csv`: conditional means by player/game/model. Filter
  fantasy_team_name and model; check injury_status and selected_for_trial.
  Selection is an unconfirmed lineup scenario, not confirmation of dressing.
- `team_projections.csv`: scenario totals, including explicit unidentified
  position-prior replacements where required.
- `goalie_projections.csv`: provisional start shares and full-60-minute means,
  not confirmed starters or expected duration. Check goalie issue timing too.

Default remains the baseline; all challengers are experimental.
Availability coverage: {m.get('availability_status','see manifest')}.
Statistical history is strictly before {m['date']}; injuries as of
{m['injuries_as_of_utc']}. Simulation ranges are provisional, not calibrated.
Actuals remain blank until separate evaluation. See manifest and context/audit
CSVs for source cutoffs, missingness and scenario assumptions.

## Teams needing unidentified replacements

{table(replacements[['team','missing_lineup_slots']])}
"""
    (p/'README.md').write_text(guide)
    forecast_table=tw[tw.issue_timing=='pregame'].pivot(index=['team','opponent','unidentified_replacement_skaters'],columns='model',values='expected_shots').reset_index()
    report.write_text(f"# {m['date']} projections\n\n"+
        f"Issued {m['created_at_utc']}: {counts.get('pregame',0)} pregame games; " +
        f"{counts.get('late_not_pregame',0)} late games.\n\n"+
        f'[Players](../../{p}/player_projections.csv) · [Teams](../../{p}/team_projections.csv) · [Goalies](../../{p}/goalie_projections.csv) · [Guide](../../{p}/README.md)\n\n'+
        f"Availability: {m.get('availability_status','see manifest')}. Filter to default model; check injury status. "+
        'Means are conditional on playing. No optimized start/sit or transaction recommendation is issued.\n\n'+
        '## Pregame team shots\n\n'+table(forecast_table)+'\n\n'+
        f"Statistical history ends before {m['date']}; injuries as of {m['injuries_as_of_utc']}. "+
        'Lineups and goalie starts are provisional. Default remains the baseline; challengers and simulation ranges need validation.\n')
    print('Reading guide:',report)
    print('Player rows:',len(wide),'Team rows:',len(tw),'Goalie rows:',len(g))

if __name__=='__main__':main()
