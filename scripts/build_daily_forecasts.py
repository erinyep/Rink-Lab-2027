#!/usr/bin/env python3
"""Issue all-date models with past-only statistics and explicit late-game labels."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from urllib.request import Request,urlopen
import numpy as np
import pandas as pd
import truststore
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.fantasy.per_game import forecast, TARGETS, require
from src.fantasy.daily import current_from_games, recent_shot_usage, coherent_count_means
from src.fantasy.availability import excluded_by_status
from src.fantasy.simulation import simulate_counts
from src.fantasy.shot_context import load_nhl_team_games, build_shot_context, matchup_shot_factors
from scripts.build_per_game_forecast import attach_espn
from scripts.build_team_total_trial import select_lineup


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(folder):
    m=json.loads((folder/'manifest.json').read_text())
    for file,h in m['files'].items(): require(sha(folder/file)==h,f'Source hash mismatch: {file}')
    return m


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--date',required=True)
    ap.add_argument('--template-forecast',type=Path,required=True)
    ap.add_argument('--game-history',type=Path,required=True)
    ap.add_argument('--boxscore-history',type=Path,required=True)
    ap.add_argument('--moneypuck-snapshot',type=Path,required=True)
    ap.add_argument('--game-toi',type=Path,required=True)
    ap.add_argument('--espn-benchmark',type=Path,required=True)
    ap.add_argument('--raw-context',type=Path)
    a=ap.parse_args()
    cfg=json.loads(Path('config/daily_forecast_trial.json').read_text())
    template=verify(a.template_forecast); verify(a.game_history)
    season=template['config']['target_season']; require(season==20262027,'Season unsupported')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=Path('data/processed/forecasts')/f'daily_{a.date}_{stamp}'; out.mkdir(parents=True)
    inputs=out/'inputs'; inputs.mkdir()
    raw=a.raw_context or Path('data/raw/nhl/snapshots')/f'daily_context_{stamp}'
    raw.mkdir(parents=True,exist_ok=a.raw_context is not None)
    sources=[]
    def fetch(endpoint,name):
        p=raw/name;url='https://api-web.nhle.com/v1/'+endpoint
        if not p.exists():
            with urlopen(Request(url,headers={'User-Agent':'Rink-Lab/0.1'}),context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=60) as r:p.write_bytes(r.read())
        return name,url,sha(p),json.loads(p.read_text())
    name,url,h,schedule=fetch('schedule/'+a.date,'schedule.json');sources.append(dict(file=name,url=url,sha256=h))
    day=[d for d in schedule['gameWeek'] if d['date']==a.date]
    require(len(day)==1,'Missing target date')
    games=[g for g in day[0]['games'] if g['season']==season and g['gameType']==2]
    require(games,'No games')
    teams=sorted({g[s]['abbrev'] for g in games for s in ['homeTeam','awayTeam']})
    def roster(t):return fetch('roster/'+t+'/current',f'roster_{t}.json')
    rosters={}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name,url,h,data in pool.map(roster,teams):
            sources.append(dict(file=name,url=url,sha256=h));rosters[name[7:-5]]=data
    if not (raw/'metadata.json').exists():
        (raw/'metadata.json').write_text(json.dumps(dict(date=a.date,sources=sources,retrieved_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
    hist=pd.read_csv(a.game_history/'skater_game_stats.csv')
    require((hist.game_date<a.date).all(),'Input history must end before target day')
    toi=pd.read_csv(a.game_toi)
    require((toi.game_date<a.date).all() and (toi.season_id==season).all(),'TOI cutoff/season invalid')
    require(not toi.duplicated(['game_id','player_id']).any(),'Duplicate TOI records')
    require(set(zip(toi.game_id,toi.player_id))==set(zip(hist.game_id,hist.player_id)),'TOI/boxscore population differs')
    require(np.allclose(toi.ev_toi_seconds+toi.pp_toi_seconds+toi.sh_toi_seconds,toi.toi_seconds),'TOI component mismatch')
    bench=pd.read_csv(a.espn_benchmark)
    bench=bench[bench.nhl_player_id.notna() & bench.projection_status.eq('available_season_average_benchmark')].copy()
    require(not bench.nhl_player_id.duplicated().any(),'Duplicate NHL benchmark')
    bench=bench.set_index('nhl_player_id')
    panel=pd.read_csv(a.template_forecast/'validated_player_seasons.csv')
    panel=panel[panel.season_id<season]
    current=current_from_games(hist,a.date,season)
    panel=pd.concat([panel,current],ignore_index=True)
    require(not panel.duplicated(['player_id','season_id']).any(),'Duplicate player season')
    params={k:v for k,v in template['selected_on_validation'].items() if k!='score'}
    common=dict(lookback=template['config']['lookback_seasons'],toi_prior_games=template['config']['toi_prior_games'])
    rates=forecast(panel,season,include_current=True,**common,**params)
    preseason=forecast(panel,season,include_current=False,**common,**params).set_index('player_id')
    process=forecast(panel,season,include_current=True,**common,**{k:v for k,v in template['best_process'].items() if k!='score'}).set_index('player_id')
    rookie=rates.historical_gp==0
    for c in [f'{e}_per_game' for e in TARGETS]:rates.loc[rookie,c]=rates.loc[rookie,'player_id'].map(process[c])
    rates.loc[rookie,'fallback']='past_position_shrinkage_unvalidated_for_rookies'
    rates.to_csv(inputs/'current_per_game_forecast.csv',index=False)
    panel.to_csv(inputs/'validated_player_seasons.csv',index=False)
    current.to_csv(inputs/'current_observed_stats.csv',index=False)
    espn_info=attach_espn(rates,inputs,Path('data/raw/espn/snapshots'),Path('data/processed/espn'),season)
    fm=dict(template);fm['created_at_utc']=datetime.now(timezone.utc).isoformat()
    fm['current_season_source']=dict(game_history=str(a.game_history),before_date=a.date)
    fm['espn']=espn_info;fm['files']={p.name:sha(p) for p in inputs.glob('*.csv')}
    (inputs/'manifest.json').write_text(json.dumps(fm,indent=2)+'\n')
    rates=rates.set_index('player_id')
    espn=pd.read_csv(inputs/'espn_player_forecasts.csv')
    espn=espn[espn.nhl_player_id.notna()].sort_values('pool',ascending=False).drop_duplicates('nhl_player_id').set_index('nhl_player_id')
    injuries=espn[['injury_status','player_name']].reset_index().rename(columns={'nhl_player_id':'player_id'})
    injuries['status_retrieved_at_utc']=espn_info['retrieved_at_utc']
    injuries.to_csv(inputs/'pregame_injury_context.csv',index=False)
    mpmeta=json.loads((a.moneypuck_snapshot/'metadata.json').read_text())
    require(sha(a.moneypuck_snapshot/'all_teams.csv')==mpmeta['sha256'],'MoneyPuck hash mismatch')
    mp=pd.read_csv(a.moneypuck_snapshot/'all_teams.csv')
    team_context=build_shot_context(load_nhl_team_games([a.boxscore_history]),mp,a.date,season,teams=teams,prior_games=cfg['team_prior_games'])
    team_context.to_csv(out/'team_context.csv',index=False)
    cal=json.loads(Path('config/game_calibration_candidate.json').read_text())
    # No-history priors use completed seasons only, weighted like the baseline.
    past=panel[(panel.season_id<season)&(panel.season_id>=20232024)].copy()
    weight=.5**(2025-past.season_id//10000)
    prior=past[TARGETS+['games_played']].mul(weight,axis=0).groupby(past.position_group).sum()
    for e in TARGETS:prior[e]/=prior.games_played
    official_teams={p['id']:t for t,ro in rosters.items() for group in ['forwards','defensemen','goalies'] for p in ro[group]}
    summaries=[];team_rows=[];coverage=[];features=[];lineups=[];game_states={}
    for game in games:
        gid=game['id']; start=game['startTimeUTC']; game_states[gid]=game['gameState']
        for side,other in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            team=game[side]['abbrev'];opp=game[other]['abbrev'];factor=matchup_shot_factors(team_context,team,opp)
            previous=hist[(hist.team==team)&(hist.toi_seconds>0)].sort_values(['game_date','game_id'])
            last=previous[previous.game_id==previous.iloc[-1].game_id] if len(previous) else previous
            lastids=set(last.player_id)
            candidates=[]
            for group in ['forwards','defensemen']:
                for p in rosters[team][group]:
                    candidates.append(dict(player_id=p['id'],player_name=p['firstName']['default']+' '+p['lastName']['default'],position_group='D' if group=='defensemen' else 'F',roster_source='current_official_roster'))
            ids={p['player_id'] for p in candidates}
            for p in last.itertuples():
                if p.player_id not in ids and (p.player_id not in official_teams or official_teams[p.player_id]==team):
                    candidates.append(dict(player_id=p.player_id,player_name=p.name,position_group='D' if p.position=='D' else 'F',roster_source='prior_game_only_review_required'))
            player_means={};audit=[]
            for p in candidates:
                pid=p['player_id'];group=p['position_group'];known=pid in rates.index
                base={e:float(rates.loc[pid,f'{e}_per_game']) if known else float(prior.loc[group,e]) for e in TARGETS}
                status=espn.loc[pid,'injury_status'] if pid in espn.index else 'UNKNOWN'
                pr=preseason.loc[pid] if pid in preseason.index else None
                usage=recent_shot_usage(hist,pid,a.date,float(pr.shots_per_game) if pr is not None else prior.loc[group,'shots'],float(pr.toi_minutes_per_game) if pr is not None and pr.toi_minutes_per_game>0 else prior.loc[group,'toi_minutes'],window=cfg['recent_window_games'],toi_prior_games=cfg['toi_prior_games'],rate_prior_minutes=cfg['rate_prior_minutes'])
                identity=dict(game_id=gid,date=a.date,team=team,opponent=opp,start_time_utc=start,**p,injury_status=status,
                    fantasy_team_name=espn.loc[pid].get('fantasy_team_name',np.nan) if pid in espn.index else np.nan,
                    fallback='none' if known else 'past_position_prior',participation_probability=np.nan)
                rest=(pd.Timestamp(a.date)-pd.Timestamp(last.game_date.iloc[0])).days if len(last) else np.nan
                recent_toi=toi[toi.player_id==pid].sort_values(['game_date','game_id']).tail(cfg['recent_window_games'])
                pp=float(recent_toi.pp_toi_seconds.mean()/60) if len(recent_toi) else np.nan
                ev=float(recent_toi.ev_toi_seconds.mean()/60) if len(recent_toi) else np.nan
                benchmark=bench.loc[pid].espn_projected_sog_per_game if pid in bench.index else np.nan
                features.append(dict(**identity,**usage,**factor,home_away='home' if side=='homeTeam' else 'away',days_since_previous_team_game=rest,back_to_back=rest==1,baseline_toi_minutes=base['toi_minutes'],baseline_shots=base['shots'],excluded_by_injury=excluded_by_status(status),recent_pp_toi_minutes_per_game=pp,recent_ev_toi_minutes_per_game=ev,espn_projected_sog_per_game=benchmark,pp_usage_status='context_only_coefficient_not_fitted'))
                audit.append(dict(**identity,has_forecast=True,played_last_team_game=pid in lastids,toi_minutes_per_game=base['toi_minutes']))
                player_means[pid]={}
                for model in cfg['models']:
                    means=base.copy()
                    if model in ['candidate','calibrated_opponent_sog_trial','usage_shot_context_trial']:
                        for e in ['shots','assists']:means[e]*=cal['factors'][e]['multiplier']
                    if model in ['opponent_form_sog_trial','calibrated_opponent_sog_trial']:means['shots']*=factor['original_current_sog_factor']
                    if model=='usage_shot_context_trial':
                        means['shots']=usage['usage_shots_before_context']*cal['factors']['shots']['multiplier']*factor['blended_sog_factor']
                        means['toi_minutes']=usage['usage_toi_minutes']
                    original_shots=means['shots'];original_ppp=means['pp_points']
                    means,constraints=coherent_count_means(means)
                    player_means[pid][model]=means
                    draws=simulate_counts(means,draws=cfg['draws'],seed=int(a.date.replace('-','')),key=f'{gid}:{pid}')
                    for category,mean in means.items():
                        d=draws.get(category)
                        summaries.append(dict(**identity,model=model,category=category,model_projection_if_plays=mean,mean_if_plays=mean,
                            whole_number_guess=max(0,int(np.ceil(mean))-1) if d is not None else np.nan,
                            simulated_mean=float(d.mean()) if d is not None else np.nan,
                            simulation_p10=int(np.quantile(d,.1,method='inverted_cdf')) if d is not None else np.nan,
                            simulation_median=int(np.quantile(d,.5,method='inverted_cdf')) if d is not None else np.nan,
                            simulation_p90=int(np.quantile(d,.9,method='inverted_cdf')) if d is not None else np.nan,
                            probability_at_least_one_if_plays=float((d>0).mean()) if d is not None else np.nan,
                            **constraints,unconstrained_shots_mean=original_shots,unconstrained_pp_points_mean=original_ppp,actual=np.nan,absolute_error=np.nan,
                            distribution_status='provisional_not_calibrated' if d is not None else 'mean_only_no_count_simulation'))
            lineup=select_lineup(pd.DataFrame(audit),require_full_lineup=False);lineups.append(lineup)
            selected=lineup[lineup.selected_for_trial]
            missing_slots={pos:max(0,n-int((selected.position_group==pos).sum())) for pos,n in [('F',12),('D',6)]}
            for model in cfg['models']:
                totals={e:np.zeros(cfg['draws'],dtype=int) for e in ['goals','assists','shots','hits','points','pp_points']}
                means={e:0. for e in totals}
                for pid in selected.player_id:
                    mm=player_means[pid][model];dd=simulate_counts(mm,draws=cfg['draws'],seed=int(a.date.replace('-','')),key=f'{gid}:{pid}')
                    for e in totals:totals[e]+=dd[e];means[e]+=mm[e]
                replacement_shots=0.
                for pos,slots in missing_slots.items():
                    for slot in range(slots):
                        mm={e:float(prior.loc[pos,e]) for e in TARGETS}
                        if model in ['candidate','calibrated_opponent_sog_trial','usage_shot_context_trial']:
                            for e in ['shots','assists']:mm[e]*=cal['factors'][e]['multiplier']
                        if model in ['opponent_form_sog_trial','calibrated_opponent_sog_trial']:mm['shots']*=factor['original_current_sog_factor']
                        if model=='usage_shot_context_trial':mm['shots']*=factor['blended_sog_factor']
                        mm,_=coherent_count_means(mm);replacement_shots+=mm['shots']
                        dd=simulate_counts(mm,draws=cfg['draws'],seed=int(a.date.replace('-','')),key=f'{gid}:{team}:unidentified_{pos}:{slot}')
                        for e in totals:totals[e]+=dd[e];means[e]+=mm[e]
                for category,mean in means.items():
                    guess=max(0,int(np.ceil(mean))-1);d=totals[category]
                    team_rows.append(dict(game_id=gid,date=a.date,team=team,opponent=opp,start_time_utc=start,model=model,category=category,
                        projection_mean=mean,whole_number_guess=guess,probability_of_guess=float((d==guess).mean()),simulation_p10=int(np.quantile(d,.1,method='inverted_cdf')),
                        simulation_p90=int(np.quantile(d,.9,method='inverted_cdf')),assumed_skaters=len(selected)+sum(missing_slots.values()),identified_skaters=len(selected),unidentified_replacement_skaters=sum(missing_slots.values()),replacement_shots_mean=replacement_shots,actual=np.nan,absolute_error=np.nan,exact_guess_correct=np.nan,
                        lineup_version='refreshed_injury_prior_game_union_trial',lineup_status='unconfirmed_12F_6D_trial' if len(selected)==18 else 'unconfirmed_with_position_prior_replacement'))
            coverage.append(dict(game_id=gid,date=a.date,team=team,opponent=opp,start_time_utc=start,
                official_roster_skaters=len(rosters[team]['forwards'])+len(rosters[team]['defensemen']),modeled_candidates=len(candidates),prior_game_additions=sum(p['roster_source']!='current_official_roster' for p in candidates),
                position_prior_players=sum(p['player_id'] not in rates.index for p in candidates),selected_skaters=len(selected),missing_lineup_slots=18-len(selected),selected_prior_game_only=int((selected.roster_source!='current_official_roster').sum()),goalie_candidates=len(rosters[team]['goalies'])))
    created=datetime.now(timezone.utc)
    frames={'simulation_summary':pd.DataFrame(summaries),'team_projected_vs_actual':pd.DataFrame(team_rows),'game_team_coverage':pd.DataFrame(coverage),'player_context':pd.DataFrame(features),'lineup_audit':pd.concat(lineups,ignore_index=True)}
    for name,frame in frames.items():
        frame['issued_at_utc']=created.isoformat()
        frame['issue_timing']=np.where((pd.to_datetime(frame.start_time_utc,utc=True)>created)&frame.game_id.map(game_states).isin(['FUT','PRE']),'pregame','late_not_pregame')
        frame.to_csv((inputs if name=='lineup_audit' else out)/f'{name}.csv',index=False)
    tm=frames['team_projected_vs_actual'];lookup=tm.set_index(['game_id','team','model','category'])
    tm['opponent_projection_mean']=[lookup.loc[(r.game_id,r.opponent,r.model,r.category),'projection_mean'] for r in tm.itertuples()]
    tm.to_csv(out/'team_projected_vs_actual.csv',index=False)
    manifest=dict(created_at_utc=created.isoformat(),date=a.date,games=len(games),forecast=str(inputs),raw_context=str(raw),sources=sources,
        seed=int(a.date.replace('-','')),draws=cfg['draws'],config=cfg,calibration=cal,game_history=str(a.game_history),boxscore_history=str(a.boxscore_history),
        moneypuck_snapshot=str(a.moneypuck_snapshot),moneypuck_sha256=mpmeta['sha256'],injuries_as_of_utc=espn_info['retrieved_at_utc'],
        additional_sources={str(a.game_toi):sha(a.game_toi),str(a.espn_benchmark):sha(a.espn_benchmark)},
        game_issue_timing=frames['game_team_coverage'][['game_id','issue_timing']].drop_duplicates().to_dict('records'),
        limitations=['Current statistical inputs end before target day. Current rosters/injuries are retrieved at issuance; late rows are not historical pregame forecasts.',
            'No models promoted; added usage/context assumptions remain unvalidated.', 'Lineups and goalie starts are provisional; conditional forecasts are not participation forecasts.',
            'State-specific usage and source benchmarks are contextual inputs pending validation; no fitted PP effect or schedule/rest coefficient.',
            'Poisson intervals assume conditional independence across players and are not calibrated.'])
    manifest['files']={p.name:sha(p) for p in out.glob('*.csv')}
    manifest['input_manifest_sha256']=sha(inputs/'manifest.json')
    manifest['code_sha256']={str(p):sha(p) for p in [Path(__file__),Path('src/fantasy/daily.py'),Path('src/fantasy/shot_context.py'),Path('config/daily_forecast_trial.json')]}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Daily bundle:',out)
    print(frames['game_team_coverage'].groupby('issue_timing').game_id.nunique().to_string())

if __name__=='__main__':main()
