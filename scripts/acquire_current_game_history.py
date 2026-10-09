#!/usr/bin/env python3
"""Acquire complete current-season final boxscores through a specified Eastern date."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import ssl
from urllib.request import Request, urlopen
import truststore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through',type=date.fromisoformat,required=True)
    parser.add_argument('--reuse',nargs='*',type=Path,default=[])
    args=parser.parse_args()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=Path('data/raw/nhl/snapshots')/f'current_game_history_20262027_{stamp}'
    out.mkdir(parents=True,exist_ok=False)
    def download(url):
        request=Request(url,headers={'User-Agent':'Rink-Lab/0.1','Accept':'application/json'})
        with urlopen(request,context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),timeout=60) as r:
            return r.read()
    sources=[]; games={}; dates=set()
    start=date(2026,9,1)
    day=start
    while day<=args.through:
        url=f'https://api-web.nhle.com/v1/schedule/{day}'
        payload=download(url); name=f'schedule_{day}.json'; (out/name).write_bytes(payload)
        data=json.loads(payload)
        for entry in data['gameWeek']:
            dates.add(entry['date'])
            for game in entry['games']:
                if game['season']==20262027 and game['gameType']==2 and date.fromisoformat(entry['date'])<=args.through:
                    games[game['id']]=game
        sources.append(dict(file=name,url=url,sha256=hashlib.sha256(payload).hexdigest()))
        day+=timedelta(days=7)
    expected={(start+timedelta(days=i)).isoformat() for i in range((args.through-start).days+1)}
    if not expected<=dates:
        raise ValueError('Incomplete schedule date coverage')
    reuse={}
    for snapshot in args.reuse:
        for path in snapshot.glob('boxscore_*.json'):
            reuse[json.loads(path.read_text())['id']]=path
    final=[g for g in games.values() if g['gameState'] in ['OFF','FINAL']]
    def acquire(game):
        gid=game['id']; url=f'https://api-web.nhle.com/v1/gamecenter/{gid}/boxscore'
        payload=reuse[gid].read_bytes() if gid in reuse else download(url)
        box=json.loads(payload)
        if box['id']!=gid or box['season']!=20262027 or box['gameType']!=2 or box['gameState'] not in ['OFF','FINAL']:
            raise ValueError('Invalid final boxscore')
        name=f'boxscore_{gid}.json'; (out/name).write_bytes(payload)
        return dict(file=name,url=url,sha256=hashlib.sha256(payload).hexdigest(),
            reused_source=str(reuse[gid]) if gid in reuse else None)
    with ThreadPoolExecutor(max_workers=4) as pool:
        sources.extend(list(pool.map(acquire,final)))
    metadata=dict(season_id=20262027,game_type=2,through_eastern_date=str(args.through),
        created_at_utc=datetime.now(timezone.utc).isoformat(),dates_checked=sorted(expected),
        final_games=len(final),unfinished_games=[g['id'] for g in games.values() if g not in final],sources=sources,
        scope='All final regular-season games reported by complete schedule date coverage; not historical as-of snapshots.')
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('Current history snapshot:',out)
    print('Final games:',len(final),'Unfinished:',len(metadata['unfinished_games']))


if __name__=='__main__':
    main()
