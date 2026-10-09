#!/usr/bin/env python3
"""Add goalie-only baseline and opponent-context trial without rewriting frozen skaters."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from src.fantasy.per_game import require
from src.fantasy.goalies import goalie_rates,simulate_goalie,start_shares
from src.fantasy.availability import excluded_by_status


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulation',type=Path,required=True)
    parser.add_argument('--injury-context',type=Path)
    args=parser.parse_args()
    sim=json.loads((args.simulation/'manifest.json').read_text())
    raw=Path(sim['raw_context']); forecast=Path(sim['forecast'])
    team_coverage=pd.read_csv(args.simulation/'game_team_coverage.csv')
    skaters=pd.read_csv(args.simulation/'simulation_summary.csv')
    deadline=pd.to_datetime(skaters.start_time_utc,utc=True).min().to_pydatetime()
    require(datetime.now(timezone.utc)<deadline,'Cannot issue new full-slate pregame goalies after puck drop')
    history=[]; sources=[]
    for season in [20232024,20242025,20252026,20262027]:
        directories=sorted(Path('data/processed/fantasy').glob(f'fantasy_{season}_*'))
        require(bool(directories),'Missing goalie season')
        path=directories[-1]/'historical_goalies.csv'
        h=pd.read_csv(path); require(not h.player_id.duplicated().any() and (h.season_id==season).all(),'Invalid goalie population')
        h['weight']=1 if season==20262027 else .5**(2025-season//10000)
        history.append(h); sources.append(dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    history=pd.concat(history,ignore_index=True)
    invalid=history[~history.eligible_for_valuation | (history.shots_against!=history.saves+history.goals_against)].copy()
    game_root=Path('data/raw/nhl/snapshots/current_game_history_20262027_20261009T192852Z')
    gm=json.loads((game_root/'metadata.json').read_text())
    team_games=[]
    for source in gm['sources']:
        if not source['file'].startswith('boxscore_'): continue
        path=game_root/source['file']
        require(hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256'],'Game source hash mismatch')
        b=json.loads(path.read_text()); require(b['gameDate']<sim['date'],'Target outcome leakage')
        for side,opposite in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            # Team shots use official totals; scoring goals exclude shootout deciding goals.
            goals=sum(p['goals'] for p in b['playerByGameStats'][side]['forwards']+b['playerByGameStats'][side]['defense'])
            team_games.append(dict(game_id=b['id'],team=b[side]['abbrev'],shots_for=b[side]['sog'],shots_against=b[opposite]['sog'],goals_for=goals))
    games=pd.DataFrame(team_games); league_shots=games.shots_for.mean(); league_goals=games.goals_for.mean()
    context={}
    for team,g in games.groupby('team'):
        context[team]=dict(games=len(g),shots_for=(g.shots_for.sum()+10*league_shots)/(len(g)+10),
            shots_against=(g.shots_against.sum()+10*league_shots)/(len(g)+10),
            goals_for=(g.goals_for.sum()+10*league_goals)/(len(g)+10))
    appearances=pd.read_csv('data/processed/forecasts/fantasy_game_details_20261009T192950Z/goalie_game_stats.csv')
    require((appearances.game_date<sim['date']).all(),'Future goalie role observations')
    espn=pd.read_csv(forecast/'espn_player_forecasts.csv')
    espn=espn[espn.primary_position.isin(['Goalie','G']) & espn.nhl_player_id.notna()].sort_values('pool',ascending=False).drop_duplicates('nhl_player_id').set_index('nhl_player_id')
    injury_context=pd.read_csv(args.injury_context).set_index('player_id') if args.injury_context else None
    rows=[]; summary=[]
    for _,g in team_coverage.iterrows():
        roster=json.loads((raw/f'roster_{g.team}.json').read_text())['goalies']
        require(len({p['id'] for p in roster})==len(roster),'Duplicate goalie roster identity')
        starts={p['id']:int(appearances[(appearances.team==g.team)&(appearances.player_id==p['id'])].starter.sum()) for p in roster}
        statuses={p['id']:(injury_context.loc[p['id'],'injury_status'] if injury_context is not None and p['id'] in injury_context.index
            else espn.loc[p['id'],'injury_status'] if p['id'] in espn.index else 'UNKNOWN') for p in roster}
        eligible={pid:not excluded_by_status(statuses[pid]) for pid in starts}
        shares=start_shares(starts,statuses)
        for player in roster:
            pid=player['id']; rates=goalie_rates(history,pid)
            share=shares[pid]
            for model in ['goalie_history_baseline','goalie_opponent_context_trial']:
                baseline_sa=rates['shots_against_per_60']
                # Blend opponent offense and own defense, both shrunk to current league mean.
                sa=baseline_sa if model=='goalie_history_baseline' else .5*(context[g.team]['shots_against']+context[g.opponent]['shots_for'])
                seed=20261009+pid+int(g.game_id)
                samples,win_proxy=simulate_goalie(sa,rates['save_probability'],context[g.team]['goals_for'],seed=seed)
                identity=dict(game_id=g.game_id,date=sim['date'],team=g.team,opponent=g.opponent,player_id=pid,
                    player_name=player['firstName']['default']+' '+player['lastName']['default'],model=model)
                row=dict(**identity,**rates,start_share_provisional=share,current_team_starts=starts[pid],
                    starter_status='not_confirmed',conditional_minutes_assumption=60,
                    shots_against_if_full_start=sa,saves_if_full_start=sa*rates['save_probability'],
                    goals_against_if_full_start=sa*(1-rates['save_probability']),
                    gaa_if_full_60=sa*(1-rates['save_probability']),save_percentage_projection=rates['save_probability'],
                    team_win_probability_proxy_if_full_start=win_proxy,
                    wins_start_share_scenario=share*win_proxy,
                    saves_start_share_scenario=share*sa*rates['save_probability'],
                    opponent_shots_for_shrunk=context[g.opponent]['shots_for'],
                    own_team_shots_against_shrunk=context[g.team]['shots_against'],
                    injury_status=statuses[pid],excluded_from_start_scenario=not eligible[pid],
                    fantasy_team_name=espn.loc[pid,'fantasy_team_name'] if pid in espn.index else None,
                    forecast_status='provisional_goalie_full_start_scenario')
                rows.append(row)
                for event,values in samples.items():
                    summary.append(dict(**identity,category=event,simulated_mean=float(values.mean()),
                        simulation_p10=int(np.quantile(values,.1,method='inverted_cdf')),
                        simulation_median=int(np.quantile(values,.5,method='inverted_cdf')),
                        simulation_p90=int(np.quantile(values,.9,method='inverted_cdf')),
                        basis='conditional_60_minute_start_provisional'))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=Path('data/processed/forecasts')/f'goalies_{sim["date"]}_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(rows).to_csv(out/'goalie_game_forecasts.csv',index=False)
    pd.DataFrame(summary).to_csv(out/'goalie_simulation_summary.csv',index=False)
    invalid.to_csv(out/'excluded_goalie_source_rows.csv',index=False)
    fantasy_rates=[]
    for pid,e in espn[espn.pool=='rostered'].iterrows():
        r=goalie_rates(history,pid)
        fantasy_rates.append(dict(player_id=pid,player_name=e.player_name,fantasy_team_name=e.fantasy_team_name,
            injury_status=injury_context.loc[pid,'injury_status'] if injury_context is not None and pid in injury_context.index else e.injury_status,
            **r,gaa_if_full_60=r['shots_against_per_60']*(1-r['save_probability']),
            status='rate_only_use_game_forecasts_for_opponent_and_start_context'))
    pd.DataFrame(fantasy_rates).to_csv(out/'espn_rostered_goalie_rates.csv',index=False)
    pd.DataFrame(context).T.reset_index(names='team').to_csv(out/'opponent_context.csv',index=False)
    require(datetime.now(timezone.utc)<deadline,'Run finished after puck drop')
    (out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),sources=sources,
        date=sim['date'],skater_simulation=str(args.simulation),games=int(team_coverage.game_id.nunique()),
        goalies=len(rows)//2,priors=dict(save_shots=200,exposure_minutes=600,team_context_games=10,start_pseudocount=1),
        role_source='Current-team observed starts plus one per nonblocked official roster goalie; uncalibrated, no confirmed starter source.',
        injury_context=str(args.injury_context) if args.injury_context else 'saved_forecast_espn_labels',
        injury_context_sha256=hashlib.sha256(args.injury_context.read_bytes()).hexdigest() if args.injury_context else None,
        excluded_player_seasons=len(invalid),draws=10000,
        limitations=['Historical goalie count exceptions excluded from event-rate fitting and retained in an audit.',
            'Conditional 60-minute scenario ignores pulls, relief, empty nets and overtime.',
            'Win proxy is full-game team support with ties split equally, not validated goalie decision probability.',
            'Start shares assume current goalie candidates complete; injuries and rest are not fitted.',
            'Opponent trial uses early-season shot environment, not shot quality or adjusted defensive talent.',
            'No goalie chronological validation yet; skater forecasts and prior artifacts remain unchanged.'],
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}),indent=2)+'\n')
    print('Goalie output:',out)
    print(pd.DataFrame(rows).query("model=='goalie_opponent_context_trial'")[[
        'team','opponent','player_name','start_share_provisional','saves_if_full_start','gaa_if_full_60','save_percentage_projection']].to_string(index=False))


if __name__=='__main__': main()
