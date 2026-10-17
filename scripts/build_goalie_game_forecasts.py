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


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def current_goalie_history(appearances, target_date, season):
    """Build current rates only from prior dates; keep bad source counts visible.

    A player with any count exception keeps the whole player-season exclusion
    used by the original baseline. Dropping just the bad game would change the
    population contributing to the rate without a validated replacement rule.
    """
    require(not appearances.duplicated(['game_id','player_id']).any(), 'Duplicate goalie appearance identity')
    require(appearances.game_date.notna().all(), 'Missing goalie appearance date')
    current = appearances[appearances.game_date.lt(target_date)].copy()
    require(not current.empty, 'No goalie history before forecast date')
    require(current.game_id.astype(str).str.startswith(str(season)[:4]+'02').all(),
            'Wrong goalie history season or game type')
    require(current.starter.isin([True,False]).all(), 'Invalid goalie starter flags')
    used = current[current.toi_seconds.gt(0)].copy()
    used['eligible_for_valuation'] = (used.count_identity_ok.eq(True)
        & used[['shots_against','saves','goals_against']].notna().all(axis=1)
        & used.shots_against.eq(used.saves+used.goals_against))
    history = used.groupby('player_id',as_index=False).agg(
        shots_against=('shots_against','sum'), saves=('saves','sum'),
        goals_against=('goals_against','sum'), time_on_ice=('toi_seconds','sum'),
        eligible_for_valuation=('eligible_for_valuation','all'))
    history['season_id'] = season
    history['weight'] = 1.0
    return current, history, int(len(appearances)-len(current))


def issue_timing(start_time, issued_at):
    return 'pregame' if pd.Timestamp(issued_at) < pd.Timestamp(start_time) else 'late_not_pregame'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulation',type=Path,required=True)
    parser.add_argument('--injury-context',type=Path)
    parser.add_argument('--game-history',type=Path,required=True,
                        help='Processed enriched game-history directory with goalie_game_stats.csv and manifest.json')
    parser.add_argument('--boxscore-history',type=Path,required=True,
                        help='Raw completed-game snapshot directory with metadata.json')
    parser.add_argument('--output-root',type=Path,default=Path('data/processed/forecasts'))
    args=parser.parse_args()
    sim=json.loads((args.simulation/'manifest.json').read_text())
    raw=Path(sim['raw_context']); forecast=Path(sim['forecast'])
    fm=json.loads((forecast/'manifest.json').read_text())
    season=int(fm['config']['target_season'])
    # goalie_rates has a completed-prior boundary fitted for this season.
    require(season==20262027,'Goalie baseline supports dates in season 20262027; revise prior boundary for another season')
    sources=[dict(file=str(path),sha256=sha256(path)) for path in
             [args.simulation/'manifest.json',forecast/'manifest.json',args.game_history/'manifest.json',
              args.boxscore_history/'metadata.json']]
    for name in ['game_team_coverage.csv','simulation_summary.csv']:
        require(sha256(args.simulation/name)==sim['files'][name], 'Skater simulation source hash mismatch')
    public_only=fm['espn'].get('status')=='disabled_public_data_only'
    if not public_only:
        require(sha256(forecast/'espn_player_forecasts.csv')==fm['files']['espn_player_forecasts.csv'],
                'ESPN forecast source hash mismatch')
    team_coverage=pd.read_csv(args.simulation/'game_team_coverage.csv')
    skaters=pd.read_csv(args.simulation/'simulation_summary.csv')
    starts_by_game=skaters[['game_id','start_time_utc']].drop_duplicates()
    require(not starts_by_game.game_id.duplicated().any(),'Conflicting game start times')
    require(not team_coverage.duplicated(['game_id','team']).any(), 'Duplicate game/team coverage')
    require(team_coverage.groupby('game_id').size().eq(2).all(), 'Expected two teams per game')
    require(set(starts_by_game.game_id)==set(team_coverage.game_id), 'Incomplete slate start times')
    starts_by_game=starts_by_game.set_index('game_id').start_time_utc.to_dict()
    history=[]
    for past_season in [season-30003,season-20002,season-10001]:
        # Pin history to the forecast's recorded inputs, never whichever file is latest.
        snapshots={Path(s['file']).parent for s in fm['source_snapshots'] if int(s['season_id'])==past_season}
        require(len(snapshots)==1, f'Missing or ambiguous historical season {past_season}')
        path=Path('data/processed/fantasy')/next(iter(snapshots)).name/'historical_goalies.csv'
        h=pd.read_csv(path)
        require(not h.player_id.duplicated().any() and (h.season_id==past_season).all(),'Invalid goalie population')
        h['weight']=.5**((season-past_season)//10001-1)
        history.append(h); sources.append(dict(file=str(path),sha256=sha256(path)))
    appearances_path=args.game_history/'goalie_game_stats.csv'
    am=json.loads((args.game_history/'manifest.json').read_text())
    require(sha256(appearances_path)==am['files']['goalie_game_stats.csv'], 'Goalie appearance source hash mismatch')
    appearances,current_history,excluded_role_rows=current_goalie_history(pd.read_csv(appearances_path),sim['date'],season)
    sources.append(dict(file=str(appearances_path),sha256=sha256(appearances_path)))
    current_history['source_snapshot']=str(args.game_history)
    history.append(current_history)
    history=pd.concat(history,ignore_index=True)
    invalid=history[~history.eligible_for_valuation | (history.shots_against!=history.saves+history.goals_against)].copy()
    game_root=args.boxscore_history
    gm=json.loads((game_root/'metadata.json').read_text())
    require(gm['season_id']==season and gm['game_type']==2, 'Wrong boxscore history season/game type')
    team_games=[]; excluded_game_ids=[]
    for source in gm['sources']:
        if not source['file'].startswith('boxscore_'): continue
        path=game_root/source['file']
        require(hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256'],'Game source hash mismatch')
        b=json.loads(path.read_text())
        require(b['season']==season and b['gameType']==2 and b['gameState'] in ['OFF','FINAL'],
                'Invalid history game season/type/state')
        if b['gameDate']>=sim['date']:
            excluded_game_ids.append(b['id'])
            continue
        sources.append(dict(file=str(path),sha256=source['sha256']))
        for side,opposite in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            # Team shots use official totals; scoring goals exclude shootout deciding goals.
            goals=sum(p['goals'] for p in b['playerByGameStats'][side]['forwards']+b['playerByGameStats'][side]['defense'])
            team_games.append(dict(game_id=b['id'],team=b[side]['abbrev'],shots_for=b[side]['sog'],shots_against=b[opposite]['sog'],goals_for=goals))
    games=pd.DataFrame(team_games)
    require(not games.empty and not games.duplicated(['game_id','team']).any(), 'Empty or duplicate team game history')
    require(set(games.game_id)==set(appearances.game_id), 'Boxscore/goalie history games differ')
    league_shots=games.shots_for.mean(); league_goals=games.goals_for.mean()
    context={}
    for team,g in games.groupby('team'):
        context[team]=dict(games=len(g),shots_for=(g.shots_for.sum()+10*league_shots)/(len(g)+10),
            shots_against=(g.shots_against.sum()+10*league_shots)/(len(g)+10),
            goals_for=(g.goals_for.sum()+10*league_goals)/(len(g)+10))
    for team in set(team_coverage.team):
        context.setdefault(team,dict(games=0,shots_for=league_shots,shots_against=league_shots,goals_for=league_goals))
    espn=(pd.DataFrame(columns=['primary_position','nhl_player_id','pool','injury_status','fantasy_team_name'])
          if public_only else pd.read_csv(forecast/'espn_player_forecasts.csv'))
    espn=espn[espn.primary_position.isin(['Goalie','G']) & espn.nhl_player_id.notna()].sort_values('pool',ascending=False).drop_duplicates('nhl_player_id').set_index('nhl_player_id')
    injury_context=pd.read_csv(args.injury_context).set_index('player_id') if args.injury_context else None
    require(injury_context is None or not injury_context.index.duplicated().any(),'Duplicate injury-context identity')
    rows=[]; summary=[]
    for _,g in team_coverage.iterrows():
        roster_path=raw/f'roster_{g.team}.json'
        roster_source=next((s for s in sim['sources'] if s['file']==roster_path.name),None)
        require(roster_source is not None and sha256(roster_path)==roster_source['sha256'], 'Goalie roster source hash mismatch')
        sources.append(dict(file=str(roster_path),sha256=sha256(roster_path)))
        roster=json.loads(roster_path.read_text())['goalies']
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
                seed=int(sim['date'].replace('-',''))+pid+int(g.game_id)
                samples,win_proxy=simulate_goalie(sa,rates['save_probability'],context[g.team]['goals_for'],seed=seed)
                identity=dict(game_id=g.game_id,date=sim['date'],start_time_utc=starts_by_game[g.game_id],
                    team=g.team,opponent=g.opponent,player_id=pid,
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
                    duration_model_status='fixed_60_minute_scenario_not_fitted',
                    history_last_game_date=appearances.game_date.max(),
                    own_team_context_games=context[g.team]['games'],
                    opponent_context_games=context[g.opponent]['games'],
                    fantasy_team_name=espn.loc[pid,'fantasy_team_name'] if pid in espn.index else None,
                    forecast_status='provisional_goalie_full_start_scenario')
                rows.append(row)
                for event,values in samples.items():
                    summary.append(dict(**identity,category=event,simulated_mean=float(values.mean()),
                        simulation_p10=int(np.quantile(values,.1,method='inverted_cdf')),
                        simulation_median=int(np.quantile(values,.5,method='inverted_cdf')),
                        simulation_p90=int(np.quantile(values,.9,method='inverted_cdf')),
                        basis='conditional_60_minute_start_provisional'))
    issued_at=datetime.now(timezone.utc)
    for row in rows+summary:
        row['issued_at_utc']=issued_at.isoformat()
        row['issue_timing']=issue_timing(row['start_time_utc'],issued_at)
    stamp=issued_at.strftime('%Y%m%dT%H%M%SZ')
    out=args.output_root/f'goalies_{sim["date"]}_{stamp}'
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
    (out/'manifest.json').write_text(json.dumps(dict(created_at_utc=issued_at.isoformat(),sources=sources,
        date=sim['date'],skater_simulation=str(args.simulation),games=int(team_coverage.game_id.nunique()),
        availability_status=sim.get('availability_status','timestamped_espn_labels'),
        game_history=str(args.game_history),boxscore_history=str(args.boxscore_history),
        history_last_game_date=str(appearances.game_date.max()),
        excluded_target_or_future_role_rows=excluded_role_rows,
        excluded_target_or_future_game_ids=excluded_game_ids,
        issue_timing_by_game={str(gid):issue_timing(start,issued_at) for gid,start in starts_by_game.items()},
        goalies=len(rows)//2,priors=dict(save_shots=200,exposure_minutes=600,team_context_games=10,start_pseudocount=1),
        role_source='Current-team observed starts plus one per nonblocked official roster goalie; uncalibrated, no confirmed starter source.',
        injury_context=str(args.injury_context) if args.injury_context else 'saved_forecast_espn_labels',
        injury_context_sha256=hashlib.sha256(args.injury_context.read_bytes()).hexdigest() if args.injury_context else None,
        excluded_player_seasons=len(invalid),draws=10000,
        limitations=['Historical goalie count exceptions excluded from event-rate fitting and retained in an audit.',
            'Conditional 60-minute scenario ignores pulls, relief, empty nets and overtime.',
            'Every input outcome is strictly before the target date; late rows are not issued pregame forecasts.',
            'Win proxy is full-game team support with ties split equally, not validated goalie decision probability.',
            'Start shares assume current goalie candidates complete; injuries and rest are not fitted.',
            'Opponent trial uses early-season shot environment, not shot quality or adjusted defensive talent.',
            'No goalie chronological validation yet; skater forecasts and prior artifacts remain unchanged.'],
        code_sha256={str(Path(__file__).relative_to(ROOT)):sha256(__file__),
                     'src/fantasy/goalies.py':sha256(ROOT/'src/fantasy/goalies.py')},
        files={p.name:sha256(p) for p in out.glob('*.csv')}),indent=2)+'\n')
    print('Goalie output:',out)
    print(pd.DataFrame(rows).query("model=='goalie_opponent_context_trial'")[[
        'team','opponent','player_name','start_share_provisional','saves_if_full_start','gaa_if_full_60','save_percentage_projection']].to_string(index=False))


if __name__=='__main__': main()
