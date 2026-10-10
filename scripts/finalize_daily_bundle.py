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
    guide='''# Daily projections — {date}

Start with **player_projections.csv**, **team_projections.csv**, and **goalie_projections.csv**.
Filter `issue_timing=pregame` for games that had not started at issuance. All 14
games are retained; three earlier games are labeled late_not_pregame.

- Player: one row per player/game/model. `expected_shots_if_plays` is the primary
  conditional shot mean. Filter team, fantasy_team_name and model. A row does
  not mean the player is dressed: check injury_status and selected_for_trial.
- Team: `expected_shots` and `expected_shots_against` are the primary means;
  `shots_whole_number_guess` is the count mode. Models use the same lineup scenario.
- Goalies: full-start shot/save/goal means; `start_share_provisional` is not a
  confirmed starter. Conditioned on 60 minutes, with injury exclusions applied.

Default is the baseline. Candidate adds fixed calibration. Opponent adds the
original team factor. Calibrated opponent combines them. usage_shot_context_trial
adds recent usage and prior-season/lagged chance context. All trials need validation.

Montreal and Philadelphia require one unidentified defense replacement in the
team scenario. Position-prior production is explicit; no invented NHL player ID
or assertion that the remaining 17 named players are the confirmed lineup.

Detailed distributions: simulation_summary.csv and team_projected_vs_actual.csv.
Input context/audits: player_context.csv, team_context.csv, game_team_coverage.csv,
inputs/lineup_audit.csv. Manifest records frozen sources. Actual columns remain
blank until evaluation. No outcome from the target day entered statistical fitting.
'''.format(date=m['date'])
    (p/'README.md').write_text(guide)
    report=Path('outputs/per_game_forecast')/f"{m['date']}_pregame_readout.md"
    forecast_table=tw[tw.issue_timing=='pregame'].pivot(index=['team','opponent','unidentified_replacement_skaters'],columns='model',values='expected_shots').reset_index()
    report.write_text('# October 10 projections\n\n'+
        f'Bundle: `{p}`. Issued {m["created_at_utc"]}. All 14 games retained: 11 pregame, 3 late. '+
        'Statistical inputs end October 9; current availability is timestamped at retrieval.\n\n'+
        f'[Player projections](../../{p}/player_projections.csv) · [Team projections](../../{p}/team_projections.csv) · [Goalies](../../{p}/goalie_projections.csv) · [Reading guide](../../{p}/README.md)\n\n'+
        '## Tonight’s team shots\n\n'+table(forecast_table)+'\n\n'+
        'Montreal uses one unidentified defense replacement with a past-position prior. All lineups remain scenarios. '+
        'The fifth model uses recent shot rate and TOI shrunk toward completed-season rates plus conservative team/chance factors. '+
        'PP/EV usage, rest and ESPN projections are exposed as context; their coefficients have not been fitted.\n\n'+
        '## Data and remaining validation\n\n'+
        'Refreshed NHL current season reports, ESPN rosters/injuries, all 69 completed games through October 9, '+
        'game scoring/goalie stats, 2,484 player-game EV/PP/SH TOI rows, and ESPN projected SOG/GP. '+
        'MoneyPuck team history retrieved October 10 supplies completed prior-season and lagged current-season context. '+
        'Nine current games have shot-count disagreements and are excluded from chance updates, retaining official NHL SOG.\n\n'+
        'Current NHL EDGE aggregates lack a reliable prior-date cutoff and are not used. Confirmed lineups/starters, '+
        'calibrated participation, goalie duration/pulls, and chronological testing remain open. '+
        'No model is promoted based on October 9. Sparse zero-rate means are preserved unless the separately labeled usage/shrinkage model changes them. '+
        'Simulation feasibility constraints cap PPP at G+A and enforce goals ≤ shots, with original means and flags retained.\n')
    print('Reading guide:',report)
    print('Player rows:',len(wide),'Team rows:',len(tw),'Goalie rows:',len(g))

if __name__=='__main__':main()
