#!/usr/bin/env python3
"""Snapshot MoneyPuck's published team-game download with coverage metadata.

Credit MoneyPuck.com. Published non-commercial research download only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import ssl
from urllib.request import Request, urlopen
import pandas as pd
import truststore

URL = 'https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--season', type=int, default=2026, help='Season start year')
    ap.add_argument('--download', type=Path, help='Process an already downloaded published CSV')
    a = ap.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw = Path('data/raw/moneypuck/snapshots')/f'team_games_{stamp}'; raw.mkdir(parents=True)
    path = raw/'all_teams.csv'
    if a.download:
        shutil.copyfile(a.download, path)
    else:
        with urlopen(Request(URL, headers={'User-Agent':'Rink-Lab/0.1 research'}),
            context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=180) as r, path.open('wb') as out:
            shutil.copyfileobj(r, out)
    columns = ['season','gameId','gameDate','team','opposingTeam','situation','playoffGame','shotsOnGoalFor','shotsOnGoalAgainst']
    f = pd.read_csv(path, usecols=columns)
    c = f[(f.season==a.season) & f.playoffGame.eq(0) & f.situation.eq('all')]
    if c.duplicated(['gameId','team']).any() or not c.groupby('gameId').size().eq(2).all():
        raise ValueError('MoneyPuck duplicate or incomplete game pairs')
    metadata = dict(url=URL, retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), rows=len(f), columns=len(columns),
        source='MoneyPuck published game-by-game team download',
        license='Non-commercial use with MoneyPuck attribution; see https://moneypuck.com/data.htm',
        season_start_year=a.season, current_games=c.gameId.nunique(),
        latest_game_by_team=c.groupby('team').gameDate.max().to_dict(),
        note='Retrieval freshness is not coverage freshness; NHL reconciliation occurs in build_shot_context.')
    (raw/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('MoneyPuck snapshot:',raw)
    print('Current regular-season games:',len(c)//2)


if __name__ == '__main__': main()
