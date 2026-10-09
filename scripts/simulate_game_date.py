#!/usr/bin/env python3
"""Verify all date-specific NHL games and simulate official roster skaters."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import truststore
from src.fantasy.per_game import require
from src.fantasy.simulation import simulate_counts,poisson_diagnostics


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',required=True)
    parser.add_argument('--forecast',type=Path,required=True)
    parser.add_argument('--draws',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=20261009)
    parser.add_argument('--raw-snapshot',type=Path)
    args=parser.parse_args()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    raw=args.raw_snapshot or Path('data/raw/nhl/snapshots')/f'simulation_context_{stamp}'
    raw.mkdir(parents=True,exist_ok=args.raw_snapshot is not None)
    sources=[]
    def fetch(endpoint,name):
        path=raw/name; url='https://api-web.nhle.com/v1/'+endpoint
        if not path.exists():
            request=Request(url,headers={'User-Agent':'Rink-Lab/0.1','Accept':'application/json'})
            with urlopen(request,context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=60) as response:
                path.write_bytes(response.read())
        payload=path.read_bytes()
        sources.append(dict(file=name,url=url,sha256=hashlib.sha256(payload).hexdigest()))
        return json.loads(payload)
    schedule=fetch('schedule/'+args.date,'schedule.json')
    day=[d for d in schedule['gameWeek'] if d['date']==args.date]
    require(len(day)==1,'Date absent from authoritative schedule')
    games=[g for g in day[0]['games'] if g['season']==20262027 and g['gameType']==2]
    require(len(games)>0,'No regular-season games')
    cutoff=datetime.now(timezone.utc)
    require(all(g['gameState'] in ['FUT','PRE'] and g['gameScheduleState']=='OK' and
        datetime.fromisoformat(g['startTimeUTC'].replace('Z','+00:00'))>cutoff for g in games),
        'Some games already started or are postponed; cannot claim complete pregame coverage')
    forecast_manifest=json.loads((args.forecast/'manifest.json').read_text())
    for f in ['current_per_game_forecast.csv','espn_player_forecasts.csv']:
        require(hashlib.sha256((args.forecast/f).read_bytes()).hexdigest()==forecast_manifest['files'][f],'Input hash mismatch')
    rates=pd.read_csv(args.forecast/'current_per_game_forecast.csv').set_index('player_id')
    espn=pd.read_csv(args.forecast/'espn_player_forecasts.csv')
    espn=espn[espn.nhl_player_id.notna()].sort_values('pool',ascending=False).drop_duplicates('nhl_player_id').set_index('nhl_player_id')
    calibration=json.loads(Path('config/game_calibration_candidate.json').read_text())
    require(calibration['calibration_dates']==['2026-10-06','2026-10-07'],'Calibration window changed')
    summaries=[]; sample_rows=[]; coverage=[]; skipped=[]
    for game in games:
        for side,other in [('homeTeam','awayTeam'),('awayTeam','homeTeam')]:
            team=game[side]['abbrev']
            roster=fetch('roster/'+team+'/current','roster_'+team+'.json')
            require(all(k in roster for k in ['forwards','defensemen','goalies']),'Malformed roster')
            players=roster['forwards']+roster['defensemen']
            require(len({p['id'] for p in players})==len(players),'Duplicate official roster ID')
            covered=0
            for player in players:
                pid=player['id']
                identity=dict(game_id=game['id'],date=args.date,player_id=pid,
                    player_name=player['firstName']['default']+' '+player['lastName']['default'],
                    team=team,opponent=game[other]['abbrev'],start_time_utc=game['startTimeUTC'])
                if pid not in rates.index:
                    skipped.append(dict(**identity,status='no_model_history_retained_not_simulated'))
                    continue
                covered+=1
                injury=espn.loc[pid,'injury_status'] if pid in espn.index else 'UNKNOWN'
                base={e:float(rates.loc[pid,f'{e}_per_game']) for e in ['goals','assists','shots','hits','pp_points']}
                for model in ['default','candidate']:
                    means=base.copy()
                    if model=='candidate':
                        for e in ['shots','assists']:
                            means[e]*=calibration['factors'][e]['multiplier']
                    samples=simulate_counts(means,draws=args.draws,seed=args.seed,key=f"{game['id']}:{pid}")
                    for event,values in samples.items():
                        mean=means.get(event,means['goals']+means['assists'])
                        summaries.append(dict(**identity,model=model,category=event,mean_if_plays=mean,
                            simulated_mean=float(values.mean()),simulation_p10=int(np.quantile(values,.1,method='inverted_cdf')),
                            simulation_median=int(np.quantile(values,.5,method='inverted_cdf')),
                            simulation_p90=int(np.quantile(values,.9,method='inverted_cdf')),
                            probability_at_least_one_if_plays=float((values>0).mean()),injury_status=injury,
                            population='official_roster_not_confirmed_dressed_lineup',distribution_status='provisional_not_calibrated'))
                    for draw in range(min(100,args.draws)):
                        sample_rows.append(dict(**identity,model=model,simulation=draw+1,
                            **{e:int(v[draw]) for e,v in samples.items()}))
            coverage.append(dict(game_id=game['id'],team=team,opponent=game[other]['abbrev'],
                official_roster_skaters=len(players),simulated_skaters=covered,missing_model_history=len(players)-covered,
                goalie_rows_retained_not_simulated=len(roster['goalies'])))
    require(set(r['game_id'] for r in coverage)=={g['id'] for g in games},'Game coverage incomplete')
    if not (raw/'metadata.json').exists():
        (raw/'metadata.json').write_text(json.dumps(dict(sources=sources,date=args.date),indent=2)+'\n')
    out=Path('data/processed/forecasts')/f'simulation_{args.date}_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(summaries).to_csv(out/'simulation_summary.csv',index=False)
    pd.DataFrame(sample_rows).to_csv(out/'integer_simulation_examples.csv',index=False)
    pd.DataFrame(coverage).to_csv(out/'game_team_coverage.csv',index=False)
    pd.DataFrame(skipped,columns=['game_id','date','player_id','player_name','team','opponent','start_time_utc','status']).to_csv(out/'players_without_model_history.csv',index=False)
    # Score already-observed October 8 without tuning dispersion or recalibrating means.
    observed=pd.read_csv('data/processed/forecasts/october_8_comparison_20261009T193905Z/evaluated_player_appearances.csv')
    diagnostics=[]
    for model in ['default','candidate']:
        for e in ['goals','assists','shots','hits']:
            col=f'{e}_if_plays' if model=='default' else f'candidate_{e}'
            subset=observed
            diagnostics.append(dict(model=model,category=e,**poisson_diagnostics(subset[e],subset[col])))
    pd.DataFrame(diagnostics).to_csv(out/'october_8_poisson_diagnostics.csv',index=False)
    require(datetime.now(timezone.utc)<min(datetime.fromisoformat(g['startTimeUTC'].replace('Z','+00:00')) for g in games),
            'Run completed after first puck drop')
    manifest=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),forecast=str(args.forecast),
        raw_context=str(raw),sources=sources,date=args.date,games=len(games),seed=args.seed,draws=args.draws,
        calibration=calibration,forecast_created_at_utc=forecast_manifest['created_at_utc'],
        simulated_player_games=len(summaries)//12,missing_history=len(skipped),
        model='Poisson SOG; binomial goals conditional on SOG; Poisson assists/HIT; points=G+A; binomial PPP conditional on points',
        limitations=['All simulations conditional on playing; no participation or goalie model.',
                     'Official rosters are not confirmed dressed lineups; injured players remain conditional.',
                     'No calibrated predictive intervals; no team/opponent or teammate dependence.',
                     'PIM, plus/minus and continuous TOI are not simulated.',
                     'Negative binomial dispersion and temporal updates require prior chronological validation.'])
    manifest['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}
    manifest['code_sha256']={str(p.resolve().relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),ROOT/'src/fantasy/simulation.py']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Simulation output:',out)
    print(pd.DataFrame(coverage).to_string(index=False))
    print(pd.DataFrame(diagnostics).to_string(index=False))


if __name__=='__main__':
    main()
