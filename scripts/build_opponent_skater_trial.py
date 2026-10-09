#!/usr/bin/env python3
"""Freeze a small opponent/form SOG trial with explicit pregame injury context."""
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
from src.fantasy.availability import excluded_by_status
from src.fantasy.simulation import simulate_counts
from scripts.build_team_total_trial import select_lineup


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulation',type=Path,required=True)
    parser.add_argument('--espn-snapshot',type=Path,required=True)
    args=parser.parse_args()
    sim=json.loads((args.simulation/'manifest.json').read_text())
    old=pd.read_csv(args.simulation/'simulation_summary.csv')
    deadline=pd.to_datetime(old.start_time_utc,utc=True).min().to_pydatetime()
    require(datetime.now(timezone.utc)<deadline,'Cannot freeze all-game pregame trial after puck drop')
    raw=Path(sim['raw_context']); forecast=Path(sim['forecast'])
    metadata=json.loads((args.espn_snapshot/'metadata.json').read_text())
    require(all(metadata['validation'].values()),'Invalid ESPN snapshot')
    crosswalk=Path('data/processed/espn')/args.espn_snapshot.name/'espn_nhl_crosswalk.csv'
    require(hashlib.sha256((args.espn_snapshot/'rosters.csv').read_bytes()).hexdigest()==metadata['files']['rosters.csv']['sha256'],'ESPN roster hash')
    pools=pd.concat([pd.read_csv(args.espn_snapshot/'rosters.csv').assign(pool='rostered'),
                    pd.read_csv(args.espn_snapshot/'available_players.csv').assign(pool='available')],ignore_index=True)
    pools=pools.merge(pd.read_csv(crosswalk)[['espn_player_id','nhl_player_id']],on='espn_player_id',how='left',validate='many_to_one')
    pools=pools[pools.nhl_player_id.notna()].sort_values('pool',ascending=False).drop_duplicates('nhl_player_id')
    injuries=pools[['nhl_player_id','player_name','injury_status','pool']].rename(columns={'nhl_player_id':'player_id'})
    injuries['excluded_by_saved_status']=injuries.injury_status.map(excluded_by_status)
    injuries['status_retrieved_at_utc']=metadata['retrieval_completed_at_utc']
    injury_index=injuries.set_index('player_id')
    history_root=Path('data/raw/nhl/snapshots/current_game_history_20262027_20261009T192852Z')
    hm=json.loads((history_root/'metadata.json').read_text()); rows=[]
    for source in hm['sources']:
        if not source['file'].startswith('boxscore_'):continue
        payload=(history_root/source['file']).read_bytes()
        require(hashlib.sha256(payload).hexdigest()==source['sha256'],'Historical boxscore hash')
        b=json.loads(payload); require(b['gameDate']<sim['date'],'Future context leakage')
        for side,other in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            rows.append(dict(team=b[side]['abbrev'],sf=b[side]['sog'],sa=b[other]['sog']))
    team_games=pd.DataFrame(rows); league=team_games.sf.mean()
    context={t:dict(gp=len(g),sf=(g.sf.sum()+20*league)/(len(g)+20),sa=(g.sa.sum()+20*league)/(len(g)+20)) for t,g in team_games.groupby('team')}
    team_coverage=pd.read_csv(args.simulation/'game_team_coverage.csv')
    rates=pd.read_csv(forecast/'current_per_game_forecast.csv').set_index('player_id')
    history=pd.read_csv('data/processed/forecasts/fantasy_game_details_20261009T192950Z/skater_game_stats.csv')
    require((history.game_date<sim['date']).all(),'Lineup leakage')
    lineup_rows=[]; projections=[]; simulations=[]; teams=[]
    for _,g in team_coverage.iterrows():
        factor=np.sqrt(context[g.team]['sf']/league * context[g.opponent]['sa']/league)
        roster=json.loads((raw/f'roster_{g.team}.json').read_text())
        previous=history[(history.team==g.team)&(history.toi_seconds>0)].sort_values(['game_date','game_id'])
        latest_id=previous.iloc[-1].game_id; ids=set(previous[previous.game_id==latest_id].player_id)
        players=[]
        for group,rs in [('F',roster['forwards']),('D',roster['defensemen'])]:
            for p in rs:
                pid=p['id']; has=pid in rates.index
                status=injury_index.loc[pid,'injury_status'] if pid in injury_index.index else 'UNKNOWN'
                identity=dict(game_id=g.game_id,team=g.team,opponent=g.opponent,player_id=pid,
                    player_name=p['firstName']['default']+' '+p['lastName']['default'],injury_status=status)
                players.append(dict(**identity,position_group=group,has_forecast=has,played_last_team_game=pid in ids,
                    toi_minutes_per_game=rates.loc[pid,'toi_minutes_per_game'] if has else np.nan))
                if not has: continue
                base=old[(old.player_id==pid)&(old.game_id==g.game_id)&(old.model=='default')].set_index('category').mean_if_plays.to_dict()
                means=base.copy(); means['shots']*=factor
                draws=simulate_counts(means,draws=10000,seed=sim['seed'],key=f'{g.game_id}:{pid}')
                projections.append(dict(**identity,model='opponent_form_sog_trial',baseline_shots_if_plays=base['shots'],
                    adjusted_shots_if_plays=means['shots'],opponent_factor=context[g.opponent]['sa']/league,
                    team_form_factor=context[g.team]['sf']/league,combined_factor=factor,
                    excluded_from_lineup_scenario=excluded_by_status(status),participation_probability=np.nan,
                    scope='conditional_if_plays_goals_and_other_means_unchanged'))
                values=draws['shots']
                simulations.append(dict(**identity,mean_if_plays=means['shots'],simulated_mean=float(values.mean()),
                    simulation_p10=int(np.quantile(values,.1,method='inverted_cdf')),
                    simulation_median=int(np.quantile(values,.5,method='inverted_cdf')),
                    simulation_p90=int(np.quantile(values,.9,method='inverted_cdf'))))
        lineup=select_lineup(pd.DataFrame(players)); lineup_rows.append(lineup)
        selected=set(lineup[lineup.selected_for_trial].player_id)
        p=[r for r in projections if r['game_id']==g.game_id and r['team']==g.team and r['player_id'] in selected]
        teams.append(dict(game_id=g.game_id,team=g.team,opponent=g.opponent,assumed_skaters=len(selected),
            baseline_shots=sum(r['baseline_shots_if_plays'] for r in p),adjusted_shots=sum(r['adjusted_shots_if_plays'] for r in p),
            combined_factor=factor,lineup_status='unconfirmed_12F_6D_refreshed_injury_labels'))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=Path('data/processed/forecasts')/f'opponent_sog_trial_{sim["date"]}_{stamp}'; out.mkdir(parents=True,exist_ok=False)
    for name,data in [('player_sog_forecasts',projections),('player_sog_simulation_summary',simulations),('team_sog_scenario',teams)]:
        pd.DataFrame(data).to_csv(out/f'{name}.csv',index=False)
    pd.concat(lineup_rows,ignore_index=True).to_csv(out/'trial_lineup_audit.csv',index=False)
    injuries.to_csv(out/'pregame_injury_context.csv',index=False)
    require(datetime.now(timezone.utc)<deadline,'Trial finished after puck drop')
    (out/'manifest.json').write_text(json.dumps(dict(created_at_utc=datetime.now(timezone.utc).isoformat(),
        simulation=str(args.simulation),espn_snapshot=str(args.espn_snapshot),injuries_as_of_utc=metadata['retrieval_completed_at_utc'],
        games=int(team_coverage.game_id.nunique()),team_prior_games=20,
        formula='SOG_if_plays * sqrt(shrunken_own_SF/league_SF * shrunken_opponent_SA/league_SF)',
        limitations=['Unvalidated current-season team-form/opponent trial; no historical team priors or strength-of-schedule adjustment.',
            'Own team form may double-count environment already in individual history; compare incremental value.',
            'Goals, assists and other marginal means unchanged; no skater shot-quality adjustment.',
            'Status labels are not confirmed dressed lineups; DTD and unknown remain uncertain.',
            'Original frozen artifacts preserved; no fitted participation probabilities.'],
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}),indent=2)+'\n')
    print('Opponent trial:',out); print(pd.DataFrame(teams).to_string(index=False))


if __name__=='__main__': main()
