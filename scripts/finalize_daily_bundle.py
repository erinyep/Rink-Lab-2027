#!/usr/bin/env python3
"""Create compact team/player reading views without changing frozen means."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np
import sys
from datetime import datetime, timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_october_9 import table
from src.fantasy.issuance import validate_release
from src.fantasy.per_game import require
from scripts.evaluate_daily_forecasts import verify_manifest_files


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',type=Path,required=True);ap.add_argument('--goalies',type=Path,required=True)
    ap.add_argument('--max-age-hours',type=float,default=6)
    ap.add_argument('--lead-minutes',type=float,default=10)
    ap.add_argument('--allow-context-lag',action='store_true')
    a=ap.parse_args();p=a.bundle;m=json.loads((p/'manifest.json').read_text())
    for f,h in m['files'].items():require(sha(p/f)==h,'Changed skater file: '+f)
    gm=json.loads((a.goalies/'manifest.json').read_text())
    for f,h in gm['files'].items():require(sha(a.goalies/f)==h,'Changed goalie file: '+f)
    for source in gm['sources']: require(sha(source['file'])==source['sha256'],'Changed goalie source')
    require(sha(Path(m['forecast'])/'manifest.json')==m['input_manifest_sha256'],'Changed fitting input manifest')
    verify_manifest_files(Path(m['forecast']),[])
    verify_manifest_files(Path(m['game_history']),[])
    for source,h in m['additional_sources'].items(): require(sha(source)==h,'Changed TOI/benchmark source')
    require(sha(Path(m['moneypuck_snapshot'])/'all_teams.csv')==m['moneypuck_sha256'],'Changed MoneyPuck source')
    s=pd.read_csv(p/'simulation_summary.csv');t=pd.read_csv(p/'team_projected_vs_actual.csv')
    require(not (p/'player_projections.csv').exists() and not m.get('finalized_at_utc'), 'Preserve issued bundle; build a new run')
    report=Path('outputs/per_game_forecast')/f"{m['date']}_{p.name.rsplit('_',1)[-1]}_pregame_readout.md"
    require(not report.exists(), 'Dated readout exists; preserve prior release')
    raw=Path(m['raw_context'])
    for source in m['sources']:
        require(sha(raw/source['file'])==source['sha256'], 'Changed schedule/roster source')
    schedule=json.loads((raw/'schedule.json').read_text())
    games=[g for d in schedule['gameWeek'] if d['date']==m['date'] for g in d['games'] if g['gameType']==2 and g['season']==20262027]
    hist=pd.read_csv(Path(m['game_history'])/'skater_game_stats.csv')
    require((hist.game_date<m['date']).all(), 'Target-day statistical outcomes')
    bm=json.loads((Path(m['boxscore_history'])/'metadata.json').read_text())
    previous=(pd.Timestamp(m['date'])-pd.Timedelta(days=1)).date().isoformat()
    require(bm['through_eastern_date']==previous and not bm['unfinished_games'], 'Incomplete prior-day history')
    require(hist.game_id.nunique()==bm['final_games'], 'Missing history games')
    now=datetime.now(timezone.utc)
    for label,stamp in [('official context',json.loads((raw/'metadata.json').read_text())['retrieved_at_utc']),
                        ('MoneyPuck',json.loads((Path(m['moneypuck_snapshot'])/'metadata.json').read_text())['retrieved_at_utc'])]:
        age=(pd.Timestamp(now)-pd.Timestamp(stamp)).total_seconds()/3600
        require(0<=age<=a.max_age_hours, 'Stale/future '+label+' retrieval')
    validation=validate_release(m,games,s,t,pd.read_csv(a.goalies/'goalie_game_forecasts.csv'),pd.read_csv(p/'team_context.csv'),now,a.max_age_hours,a.lead_minutes,a.allow_context_lag)
    keys=['game_id','player_id','model']
    wide=s.pivot(index=keys,columns='category',values='model_projection_if_plays').reset_index()
    wide=wide.rename(columns={c:'expected_'+c+'_if_plays' for c in ['goals','assists','shots','hits','points','pp_points','penalty_minutes','plus_minus','toi_minutes']})
    identity=['player_name','team','opponent','fantasy_team_name','injury_status','roster_source','fallback','issue_timing','start_time_utc']
    wide=s[keys+identity].drop_duplicates(keys).merge(wide,on=keys,validate='one_to_one')
    lineup=pd.read_csv(p/'inputs/lineup_audit.csv')
    wide=wide.merge(lineup[['game_id','player_id','selected_for_trial','selection_reason']],on=['game_id','player_id'],validate='many_to_one')
    pc=pd.read_csv(p/'player_context.csv')
    wide=wide.merge(pc[['game_id','player_id','recent_pp_toi_minutes_per_game','recent_ev_toi_minutes_per_game','espn_projected_sog_per_game']],on=['game_id','player_id'],validate='many_to_one')
    tk=['game_id','team','model'];tw=t.pivot(index=tk,columns='category',values='projection_mean').reset_index()
    tw=tw.rename(columns={c:'expected_'+c for c in ['goals','assists','shots','hits','points','pp_points']})
    ident=['opponent','issue_timing','start_time_utc','lineup_status','identified_skaters','unidentified_replacement_skaters']
    tw=t[tk+ident].drop_duplicates(tk).merge(tw,on=tk,validate='one_to_one')
    shots=t[t.category=='shots'][tk+['whole_number_guess','opponent_projection_mean']].rename(columns={'whole_number_guess':'shots_whole_number_guess','opponent_projection_mean':'expected_shots_against'})
    tw=tw.merge(shots,on=tk,validate='one_to_one')
    reverse=tw[['game_id','team','model','expected_shots']].rename(columns={'team':'opponent','expected_shots':'opponent_sf'})
    check=tw.merge(reverse,on=['game_id','opponent','model'],validate='many_to_one')
    require(np.allclose(check.expected_shots_against,check.opponent_sf),'Team SF/opponent SA identity')
    g=pd.read_csv(a.goalies/'goalie_game_forecasts.csv');gs=pd.read_csv(a.goalies/'goalie_simulation_summary.csv')
    for category in ['shots_against','saves','goals_against']:
        subset=gs[gs.category==category][['game_id','player_id','model','simulation_p10','simulation_median','simulation_p90']]
        subset=subset.rename(columns={c:category+'_'+c for c in ['simulation_p10','simulation_median','simulation_p90']})
        g=g.merge(subset,on=['game_id','player_id','model'],validate='one_to_one')
    for c in ['shots_against','saves','goals_against','wins','gaa','save_percentage']:g['actual_'+c]=np.nan
    released=datetime.now(timezone.utc)
    validate_release(m,games,s,t,g,pd.read_csv(p/'team_context.csv'),released,a.max_age_hours,a.lead_minutes,a.allow_context_lag)
    for frame in [wide,tw,g]: frame['released_at_utc']=released.isoformat()
    wide.to_csv(p/'player_projections.csv',index=False)
    tw.to_csv(p/'team_projections.csv',index=False)
    g.to_csv(p/'goalie_projections.csv',index=False)
    m['finalized_at_utc']=released.isoformat()
    m['release_validation']=validation
    m['statistical_history_last_game_date']=hist.game_date.max()
    m['goalie_source']=str(a.goalies);m['goalie_manifest_sha256']=sha(a.goalies/'manifest.json')
    m['files']={f.name:sha(f) for f in p.glob('*.csv')}
    (p/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    replacements=tw[tw.model.eq('default') & tw.unidentified_replacement_skaters.gt(0)][['team','unidentified_replacement_skaters']]
    guide=(f"# Daily projections — {m['date']}\n\nReleased {released.isoformat()}: {len(games)} games, all pregame. "
        f"Statistical history ends {hist.game_date.max()} ({hist.game_id.nunique()} games).\n\n"
        "Start with player_projections.csv, team_projections.csv and goalie_projections.csv. Player means condition on playing; "
        "selected_for_trial is an assumed lineup, not a confirmed roster. Goalies condition on a full start; start shares are provisional. "
        "Default remains baseline; other models remain trials.\n\n"
        "## Unidentified lineup replacements\n\n"+(table(replacements) if len(replacements) else "None.")+"\n\n"
        "Source coverage/discrepancies: team_context.csv. Release checks: manifest.json. Actuals remain blank. "
        "Evaluate results separately and preserve this bundle.\n")
    (p/'README.md').write_text(guide)
    forecast_table=tw[tw.model.eq('default')][['team','opponent','expected_shots','expected_shots_against']]
    report.write_text(guide+f"\nBundle: `{p}`.\n\n"+
        f'[Player projections](../../{p}/player_projections.csv) · [Team projections](../../{p}/team_projections.csv) · [Goalies](../../{p}/goalie_projections.csv)\n\n'+
        table(forecast_table)+'\n')
    print('Finalized bundle:',p)
    print('Reading guide:',report)
    print('Player rows:',len(wide),'Team rows:',len(tw),'Goalie rows:',len(g))

if __name__=='__main__':main()
