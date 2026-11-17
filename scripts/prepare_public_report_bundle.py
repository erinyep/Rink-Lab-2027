#!/usr/bin/env python3
"""Build a temporary report-compatible view of a sanitized frozen release.

This lets a clean CI runner build the fantasy report from the committed public
forecast without needing the ignored, full local forecast tree.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import ssl
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd
import truststore


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', required=True, help='Eastern calendar date (YYYY-MM-DD)')
    parser.add_argument('--out', required=True, type=Path, help='New, temporary output directory')
    parser.add_argument('--public-root', type=Path, default=Path('outputs/per_game_forecast/frozen'))
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Output already exists; use a new temporary directory')

    candidates = []
    for folder in args.public_root.glob(f'daily_{args.date}_*'):
        manifest_path = folder / 'manifest.json'
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            candidates.append((manifest.get('released_at_utc', ''), folder, manifest))
    if not candidates:
        raise ValueError(f'No committed frozen forecast found for {args.date}')
    _, public_bundle, source = max(candidates, key=lambda item: item[0])

    for filename, expected in source['files'].items():
        path = public_bundle / filename
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f'Frozen public forecast hash mismatch: {filename}')

    url = f'https://api-web.nhle.com/v1/schedule/{args.date}'
    request = Request(url, headers={'User-Agent': 'Rink-Lab/0.1 fantasy report'})
    context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with urlopen(request, context=context, timeout=60) as response:
        schedule_bytes = response.read()
    schedule = json.loads(schedule_bytes)
    games = [game for day in schedule.get('gameWeek', []) if day.get('date') == args.date
             for game in day.get('games', [])
             if game.get('season') == 20262027 and game.get('gameType') == 2]
    if not games or len({game['id'] for game in games}) != len(games):
        raise ValueError('NHL schedule is missing or has duplicate regular-season games')

    forecast_games = set(pd.read_csv(public_bundle / 'team_projections.csv').game_id.astype(int))
    schedule_games = {int(game['id']) for game in games}
    if forecast_games != schedule_games:
        raise ValueError('Frozen forecast game coverage differs from today’s NHL schedule')

    args.out.mkdir(parents=True)
    raw = args.out / 'raw_context'
    raw.mkdir()
    schedule_path = raw / 'schedule.json'
    schedule_path.write_bytes(schedule_bytes)
    schedule_sha = digest(schedule_path)
    (raw / 'metadata.json').write_text(json.dumps({
        'url': url,
        'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
        'sha256': schedule_sha,
    }, indent=2) + '\n')

    for name in ['player_projections.csv', 'team_projections.csv',
                 'goalie_projections.csv', 'game_team_coverage.csv']:
        shutil.copyfile(public_bundle / name, args.out / name)

    # The sanitized release intentionally omits historical GP. Keep that field
    # null in the temporary report input so the page displays “—”, not a guess.
    players = pd.read_csv(args.out / 'player_projections.csv')
    history = players[['player_id']].drop_duplicates().copy()
    history['historical_gp'] = pd.NA
    inputs = args.out / 'inputs'
    inputs.mkdir()
    history_path = inputs / 'current_per_game_forecast.csv'
    history.to_csv(history_path, index=False)
    (inputs / 'manifest.json').write_text(json.dumps({
        'espn': {'status': 'private_snapshot'},
        'files': {'current_per_game_forecast.csv': digest(history_path)},
    }, indent=2) + '\n')

    source_files = {name: digest(args.out / name) for name in [
        'player_projections.csv', 'team_projections.csv',
        'goalie_projections.csv', 'game_team_coverage.csv']}
    manifest = {
        'date': args.date,
        'created_at_utc': source['released_at_utc'],
        'finalized_at_utc': source['released_at_utc'],
        'raw_context': str(raw.resolve()),
        'sources': [{'file': 'schedule.json', 'sha256': schedule_sha}],
        'config': {'models': source['models']},
        'availability_status': 'disabled_public_data_only',
        'injuries_as_of_utc': None,
        'files': source_files,
        'source_public_manifest_sha256': digest(public_bundle / 'manifest.json'),
    }
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared temporary fantasy report context for {args.date}: '
          f'{len(games)} games, {len(history)} NHL player IDs; prior NHL GP unavailable')


if __name__ == '__main__':
    main()
