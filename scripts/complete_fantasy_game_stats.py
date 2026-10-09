#!/usr/bin/env python3
"""Enrich preserved boxscores with scoring-summary PPP; retain goalie denominators."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
import truststore
from src.fantasy.per_game import require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boxscore-snapshots', nargs='+', type=Path, required=True)
    parser.add_argument('--landing-snapshot', type=Path)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    raw = args.landing_snapshot or Path('data/raw/nhl/snapshots') / f'fantasy_game_details_{stamp}'
    raw.mkdir(parents=True, exist_ok=args.landing_snapshot is not None)
    sources, skaters, goalies = [], [], []
    files = {}
    for snapshot in args.boxscore_snapshots:
        for path in snapshot.glob('boxscore_*.json'):
            box = json.loads(path.read_text())
            if box['id'] in files:
                require(files[box['id']].read_bytes() == path.read_bytes(), 'Conflicting saved game boxscores')
            files[box['id']] = path
    def acquire_landing(game_id):
        landing_path=raw/f'landing_{game_id}.json'
        if not landing_path.exists():
            url=f'https://api-web.nhle.com/v1/gamecenter/{game_id}/landing'
            request=Request(url,headers={'User-Agent':'Rink-Lab/0.1','Accept':'application/json'})
            with urlopen(request,context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=60) as response:
                landing_path.write_bytes(response.read())
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(acquire_landing,sorted(files)))
    for game_id, path in sorted(files.items()):
        box = json.loads(path.read_text())
        require(box['gameState'] in ['OFF','FINAL'] and box['season'] == 20262027 and box['gameType'] == 2, 'Wrong game population')
        url = f'https://api-web.nhle.com/v1/gamecenter/{game_id}/landing'
        landing_path = raw / f'landing_{game_id}.json'
        if not landing_path.exists():
            request = Request(url, headers={'User-Agent':'Rink-Lab/0.1','Accept':'application/json'})
            with urlopen(request, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=60) as response:
                landing_path.write_bytes(response.read())
        landing = json.loads(landing_path.read_text())
        require(landing['id'] == game_id and landing['gameState'] in ['OFF','FINAL'], 'Wrong landing game/status')
        counts = {key: Counter() for key in ['goals','assists','pp_goals','pp_assists']}
        require(isinstance(landing.get('summary',{}).get('scoring'), list), 'Missing scoring coverage')
        for period in landing['summary']['scoring']:
            if period['periodDescriptor']['periodType'] == 'SO':
                continue
            for goal in period['goals']:
                require(goal['strength'] in ['ev','pp','sh'], 'Unknown scoring strength')
                counts['goals'][goal['playerId']] += 1
                if goal['strength'] == 'pp':
                    counts['pp_goals'][goal['playerId']] += 1
                for assist in goal.get('assists',[]):
                    counts['assists'][assist['playerId']] += 1
                    if goal['strength'] == 'pp':
                        counts['pp_assists'][assist['playerId']] += 1
        for side in ['homeTeam','awayTeam']:
            players = box['playerByGameStats'][side]
            for p in players['forwards'] + players['defense']:
                pid = p['playerId']
                require(counts['goals'][pid] == p['goals'] and counts['assists'][pid] == p['assists'], 'Landing/boxscore scoring disagreement')
                require(counts['pp_goals'][pid] == p['powerPlayGoals'], 'PP goal disagreement')
                minutes, seconds = map(int,p['toi'].split(':'))
                pp = counts['pp_goals'][pid] + counts['pp_assists'][pid]
                require(pp <= p['points'], 'PPP exceeds points')
                skaters.append(dict(game_id=game_id,game_date=box['gameDate'],player_id=pid,
                    name=p['name']['default'],team=box[side]['abbrev'],position=p['position'],
                    goals=p['goals'],assists=p['assists'],points=p['points'],shots=p['sog'],
                    hits=p['hits'],penalty_minutes=p['pim'],plus_minus=p['plusMinus'],
                    pp_goals=counts['pp_goals'][pid],pp_assists=counts['pp_assists'][pid],pp_points=pp,
                    toi_seconds=minutes*60+seconds,toi_minutes=minutes+seconds/60))
            for p in players['goalies']:
                minutes, seconds = map(int,p['toi'].split(':'))
                toi = minutes*60+seconds
                sa, sv, ga = p.get('shotsAgainst'),p.get('saves'),p.get('goalsAgainst')
                goalies.append(dict(game_id=game_id,game_date=box['gameDate'],player_id=p['playerId'],
                    name=p['name']['default'],team=box[side]['abbrev'],starter=p['starter'],
                    decision=p.get('decision'),wins=int(p.get('decision')=='W'),toi_seconds=toi,
                    shots_against=sa,saves=sv,goals_against=ga,
                    save_percentage=sv/sa if sa else None,gaa=ga*3600/toi if toi else None,
                    count_identity_ok=sa is not None and sv is not None and ga is not None and sa==sv+ga))
        sources.append(dict(game_id=game_id,boxscore=str(path),boxscore_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            landing=str(landing_path),url=url,landing_sha256=hashlib.sha256(landing_path.read_bytes()).hexdigest()))
        print('Validated fantasy game:',game_id,flush=True)
    if not (raw/'metadata.json').exists():
        (raw/'metadata.json').write_text(json.dumps(dict(sources=sources),indent=2)+'\n')
    out = Path('data/processed/forecasts') / f'fantasy_game_details_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    for name,rows in [('skater_game_stats',skaters),('goalie_game_stats',goalies)]:
        frame=pd.DataFrame(rows)
        require(not frame.duplicated(['game_id','player_id']).any(),'Duplicate game/player')
        frame.to_csv(out/f'{name}.csv',index=False)
    (out/'manifest.json').write_text(json.dumps(dict(raw_snapshot=str(raw),sources=sources,games=len(files),
        skater_rows=len(skaters),goalie_rows=len(goalies),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')},
        dates_covered=sorted({r['game_date'] for r in skaters}),
        limitations=['Boxscores include unused backup goalies; zero TOI ratios remain missing.',
                     'Goalie count exceptions are flagged, not repaired.',
                     'Historical retrievals are corrected observations, not original as-of forecast inputs.']),indent=2)+'\n')
    print('Fantasy game output:',out)


if __name__=='__main__':
    main()
