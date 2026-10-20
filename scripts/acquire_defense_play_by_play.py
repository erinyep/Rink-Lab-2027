#!/usr/bin/env python3
"""Acquire official PBP for every final game in a verified boxscore snapshot."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
import sys
import time
from urllib.request import Request, urlopen
import pandas as pd
import truststore

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.fantasy.play_by_play import parse_game, team_measures
from src.fantasy.per_game import require


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--boxscores', type=Path, required=True)
    ap.add_argument('--raw-snapshot', type=Path, help='Reprocess a preserved acquisition offline')
    a = ap.parse_args()
    bm = json.loads((a.boxscores/'metadata.json').read_text())
    sources = [s for s in bm['sources'] if s['file'].startswith('boxscore_')]
    require(len(sources) == bm['final_games'], 'Incomplete boxscore metadata')
    boxes = {}
    for s in sources:
        p = a.boxscores/s['file']; require(sha(p) == s['sha256'], 'Boxscore hash mismatch')
        b = json.loads(p.read_text()); boxes[b['id']] = b
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    raw = a.raw_snapshot or Path('data/raw/nhl/snapshots')/f'defense_pbp_{stamp}'
    if a.raw_snapshot:
        old = json.loads((raw/'metadata.json').read_text())
        require(set(old['game_ids']) == set(boxes), 'PBP game coverage mismatch')
        for s in old['sources']:
            require(sha(raw/s['file']) == s['sha256'], 'PBP source hash mismatch')
    else:
        raw.mkdir(parents=True, exist_ok=False)
    def fetch(gid):
        p = raw/f'play_by_play_{gid}.json'; url = f'https://api-web.nhle.com/v1/gamecenter/{gid}/play-by-play'
        if not a.raw_snapshot:
            for attempt in range(3):
                try:
                    with urlopen(Request(url, headers={'User-Agent':'Rink-Lab/0.1 research'}),
                        context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=60) as r:
                        payload = r.read()
                    json.loads(payload); p.write_bytes(payload); break
                except Exception:
                    if attempt == 2: raise
                    time.sleep(2**attempt)
        game = json.loads(p.read_text())
        require(game['id'] == gid and game['season'] == bm['season_id'], 'Wrong PBP game/season')
        return dict(file=p.name, url=url, sha256=sha(p)), parse_game(game)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, sorted(boxes)))
    if not a.raw_snapshot:
        (raw/'metadata.json').write_text(json.dumps(dict(retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            game_ids=sorted(boxes), sources=[r[0] for r in results]), indent=2)+'\n')
    events = pd.concat([r[1] for r in results], ignore_index=True)
    require(not events.duplicated(['game_id','event_id']).any(), 'Duplicate PBP event')
    team = team_measures(events)
    require(len(team) == 4*len(boxes), 'Incomplete team/strength coverage')
    audit = []
    for row in team[team.strength.eq('all')].itertuples():
        b = boxes[row.game_id]; side = next(k for k in ['homeTeam','awayTeam'] if b[k]['abbrev']==row.team)
        observed = events[(events.game_id==row.game_id) & (events.team==row.team)]
        audit.append(dict(game_id=row.game_id, team=row.team, pbp_sog=int(observed.on_goal.sum()),
            official_sog=b[side]['sog'], sog_match=int(observed.on_goal.sum())==b[side]['sog']))
    out = Path('data/processed/forecasts')/f'defense_pbp_{stamp}'; out.mkdir(parents=True)
    for name, frame in [('shot_attempt_events',events), ('defense_team_games',team), ('source_audit',pd.DataFrame(audit))]:
        frame.to_csv(out/(name+'.csv'), index=False)
    (out/'manifest.json').write_text(json.dumps(dict(raw_snapshot=str(raw), boxscores=str(a.boxscores),
        games=len(boxes), events=len(events), unique_shooters=events.player_id.nunique(),
        missing_position=int(events.position.isna().sum()), missing_coordinates=int(events.distance_to_attacking_net.isna().sum()),
        sog_disagreement_team_games=sum(not r['sog_match'] for r in audit),
        latest_game_date=events.game_date.max(), files={p.name:sha(p) for p in out.glob('*.csv')},
        limitations=['Corrected final PBP; not historical as-of data.', '10s continuations are temporal associations, not passes or possession chains.',
            'Near-net means within 25 feet of attacking net, not an xG or high-danger model.',
            '5v5 labels condition on attempt state; continuation anchor may be in another state.',
            'No on-ice pair attribution or exposure rates without shift data.']), indent=2)+'\n')
    print('Defense PBP output:', out)
    print('Games:',len(boxes),'Attempts:',len(events),'SOG disagreement team-games:',sum(not r['sog_match'] for r in audit))


if __name__ == '__main__': main()
