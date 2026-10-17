#!/usr/bin/env python3
"""Acquire immutable MoneyPuck team history without running an evaluation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
from urllib.request import Request, urlopen

import pandas as pd
import truststore

URL = 'https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=Path('data/raw/moneypuck/snapshots'))
    args = parser.parse_args()
    started = datetime.now(timezone.utc)
    out = args.output_root / ('team_games_' + started.strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    request = Request(URL, headers={'User-Agent': 'Rink-Lab/0.1 research'})
    with urlopen(request, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=120) as response:
        payload = response.read()
    path = out / 'all_teams.csv'
    path.write_bytes(payload)
    frame = pd.read_csv(path)
    keys = ['season', 'gameId', 'team', 'situation']
    metrics = ['shotsOnGoalFor', 'shotsOnGoalAgainst', 'xOnGoalFor', 'xOnGoalAgainst']
    if frame.empty or frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError('Empty, missing or duplicate MoneyPuck identities')
    if frame[metrics].isna().any().any() or (frame[metrics] < 0).any().any():
        raise ValueError('Invalid MoneyPuck shot metrics')
    completed = datetime.now(timezone.utc)
    metadata = dict(url=URL, retrieval_started_at_utc=started.isoformat(),
        retrieved_at_utc=completed.isoformat(), sha256=hashlib.sha256(payload).hexdigest(),
        rows=len(frame), source='MoneyPuck published game-by-game team download',
        license='Non-commercial use with MoneyPuck attribution',
        latest_game_date_by_season=frame.groupby('season').gameDate.max().to_dict(),
        scope='Retrieval time is not statistical coverage; daily model applies date cutoff and NHL reconciliation.')
    (out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('MoneyPuck snapshot:', out)
    print('Latest source game date:', frame.gameDate.max())


if __name__ == '__main__':
    main()
