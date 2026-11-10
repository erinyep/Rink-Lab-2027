#!/usr/bin/env python3
"""Publish a non-overwriting MoneyPuck team-row delta and dated shot archive."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import pandas as pd


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--team-snapshot', type=Path, required=True)
    ap.add_argument('--shots-snapshot', type=Path, required=True)
    ap.add_argument('--base-team', type=Path, required=True,
                    help='Previously committed current-season team context to extend')
    ap.add_argument('--team-out', type=Path, required=True)
    ap.add_argument('--shots-out', type=Path, required=True)
    args = ap.parse_args()
    if args.team_out.exists() or args.shots_out.exists():
        raise FileExistsError('Refusing to overwrite an existing MoneyPuck publication')

    team_meta = json.loads((args.team_snapshot / 'metadata.json').read_text())
    team_source = args.team_snapshot / 'all_teams.csv'
    if sha(team_source) != team_meta['sha256']:
        raise ValueError('Team snapshot checksum mismatch')
    base = pd.read_csv(args.base_team / 'all_teams.csv', usecols=['season', 'gameDate'])
    base_date = str(base.loc[base.season.astype(str).eq('2026'), 'gameDate'].astype(str).max())
    if base_date in {'nan', 'NaT'}:
        raise ValueError('Base release has no 2026-27 data')

    selected = []
    reader = pd.read_csv(team_source, dtype=str, chunksize=50000)
    for chunk in reader:
        keep = (chunk.season.eq('2026') & chunk.position.eq('Team Level') &
                chunk.playoffGame.eq('0') & chunk.gameDate.gt(base_date))
        selected.append(chunk.loc[keep])
    delta = pd.concat(selected, ignore_index=True)
    if delta.empty:
        raise ValueError('No new 2026-27 team rows beyond the base release')
    expected_situations = {'all', '5on5', '4on5', '5on4', 'other'}
    pairs = delta.groupby(['gameId', 'situation']).team.nunique()
    counts = Counter(delta.situation)
    if set(delta.situation) != expected_situations or not pairs.eq(2).all():
        raise ValueError('New team rows do not contain paired teams in all five situations')
    if not delta.groupby('gameId').situation.apply(set).map(lambda x: x == expected_situations).all():
        raise ValueError('At least one new game is missing a MoneyPuck situation')
    if delta.duplicated(['gameId', 'team', 'situation']).any():
        raise ValueError('Duplicate MoneyPuck team-game rows')
    latest_date = str(delta.gameDate.max())
    source_latest = str(team_meta.get('latest_game_date_by_season', {}).get('2026', latest_date))
    source_latest = source_latest.replace('-', '')
    if latest_date != source_latest:
        raise ValueError(f'Delta ends {latest_date}, but source metadata says {source_latest}')

    args.team_out.mkdir(parents=True)
    delta.to_csv(args.team_out / 'all_teams.csv', index=False)
    dates = sorted(delta.gameDate.unique().tolist())
    metadata = dict(source='MoneyPuck published game-by-game team download',
        url=team_meta['url'], retrieved_at_utc=team_meta['retrieved_at_utc'],
        license='Non-commercial research with MoneyPuck attribution; see https://moneypuck.com/data.htm',
        source_sha256=team_meta['sha256'], source_rows=team_meta['rows'],
        sha256=sha(args.team_out / 'all_teams.csv'), rows=len(delta), season='2026',
        date_range_inclusive=[dates[0], dates[-1]], regular_season_only=True,
        position='Team Level', situations=sorted(expected_situations),
        rows_by_situation=dict(sorted(counts.items())),
        rows_by_game_date={d: int(n) for d, n in delta.groupby('gameDate').size().items()},
        games=int(delta.gameId.nunique()), paired_team_rows_validated=True,
        base_release=str(args.base_team), base_latest_game_date=base_date,
        filter=f'season == 2026; position == Team Level; playoffGame == 0; gameDate > {base_date}',
        purpose='Append-only MoneyPuck team context after the previously published current-season delta.',
        published_at_utc=datetime.now(timezone.utc).isoformat())
    (args.team_out / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (args.team_out / 'README.md').write_text(
        '# MoneyPuck team-game context delta\n\n'
        f'This non-overlapping update adds {metadata["games"]} games, {len(delta)} paired team-situation rows, '
        f'for {dates[0]} through {dates[-1]}. Use it with [`{args.base_team.name}`](../{args.base_team.name}/). '
        'Source, retrieval time, selected row counts, filters and hashes are recorded in `metadata.json`.\n\n'
        'Source: [MoneyPuck team-game data](https://moneypuck.com/data.htm). Non-commercial research use; credit MoneyPuck.com.\n')

    shots_meta = json.loads((args.shots_snapshot / 'metadata.json').read_text())
    archive = args.shots_snapshot / 'shots.zip'
    if sha(archive) != shots_meta['sha256']:
        raise ValueError('Shot archive checksum mismatch')
    args.shots_out.mkdir(parents=True)
    published = args.shots_out / 'shots_2026.zip'
    shutil.copyfile(archive, published)
    public_meta = {k: v for k, v in shots_meta.items() if k not in {'raw_snapshot', 'boxscores'}}
    public_meta.update(filename=published.name, sha256=sha(published),
        note='Original MoneyPuck ZIP copied byte-for-byte; local acquisition and NHL boxscore paths omitted.',
        published_at_utc=datetime.now(timezone.utc).isoformat())
    (args.shots_out / 'metadata.json').write_text(json.dumps(public_meta, indent=2) + '\n')
    (args.shots_out / 'README.md').write_text(
        '# MoneyPuck 2026-27 unblocked shots — refreshed snapshot\n\n'
        f'`shots_2026.zip` is the original MoneyPuck download copied byte-for-byte. '
        f'This retrieval contains {shots_meta["rows"]:,} unblocked-shot events across '
        f'{shots_meta["eligible_games"]} validated official games.\n\n'
        'Source: [MoneyPuck published downloads](https://moneypuck.com/data.htm). '
        'Non-commercial research use; credit MoneyPuck.com. The archive is source data, '
        'not an as-of xG forecast. See `metadata.json` for coverage and reconciliation notes.\n')
    print(f'Team delta: {args.team_out} ({len(delta)} rows, {dates[0]}–{dates[-1]})')
    print(f'Shot archive: {args.shots_out} ({shots_meta["rows"]} events)')


if __name__ == '__main__':
    main()
