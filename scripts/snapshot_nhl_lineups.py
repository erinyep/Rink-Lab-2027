#!/usr/bin/env python3
"""Save official projected lineups and resolve names against current NHL rosters."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
import unicodedata
from urllib.request import Request, urlopen

import pandas as pd
import truststore

# Explicit spelling corrections checked against the team's official NHL roster.
# Preserve the article's original spelling and record the identity method per row.
ROSTER_NAME_ALIASES = {
    ('BOS', 'Michael Eyssiont'): 'Michael Eyssimont',
    ('WSH', 'Alaiksei Protas'): 'Aliaksei Protas',
    ('CHI', 'Wyat Kaiser'): 'Wyatt Kaiser',
    ('NSH', 'Nicolas Hauge'): 'Nicolas Hague',
    ('NSH', 'Deamon Hunt'): 'Daemon Hunt',
}


class ArticleParagraphs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.article = False
        self.collect = False
        self.parts = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'article':
            self.article = True
        if self.article and tag in {'p', 'h1', 'h2', 'h3'}:
            self.collect = True
            self.parts = []
        if self.collect and tag == 'br':
            self.parts.append(' ')

    def handle_data(self, data):
        if self.collect:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.collect and tag in {'p', 'h1', 'h2', 'h3'}:
            self.paragraphs.append(' '.join(''.join(self.parts).split()))
            self.collect = False
        if tag == 'article':
            self.article = False


def normalized_name(name):
    text = unicodedata.normalize('NFKD', name)
    return ''.join(c for c in text.lower() if c.isalnum() and not unicodedata.combining(c))


def parse_lineups(paragraphs, teams):
    rows = []
    current = None
    unit = 0
    goalies = 0
    for text in paragraphs:
        if text.lower().endswith(' projected lineup'):
            label = text[:-len(' projected lineup')].lower()
            matches = [team for team, name in teams.items() if name.lower().endswith(label)]
            if len(matches) != 1:
                raise ValueError('Unresolved lineup team: ' + text)
            current = matches[0]
            unit = goalies = 0
        elif text.lower() == 'status report':
            current = None
        elif current and text.startswith(('Scratched:', 'Injured:')):
            status, names = text.split(':', 1)
            for name in re.sub(r'\([^)]*\)', '', names).split(','):
                if name.strip() and name.strip().lower() not in {'none', 'none.'}:
                    rows.append(dict(team=current, player_name=name.strip(), projected_status=status.lower(), unit=None, role=None))
        elif current and text:
            names = re.split(r'\s*(?:--|–|—)\s*', text)
            if len(names) in {2, 3}:
                unit += 1
                role = 'F' if unit <= 4 else 'D'
                for name in names:
                    rows.append(dict(team=current, player_name=name, projected_status='projected_skater', unit=unit, role=role))
            elif len(names) == 1 and goalies < 2 and unit >= 6:
                goalies += 1
                rows.append(dict(team=current, player_name=text, projected_status='projected_goalie' if goalies == 1 else 'listed_backup', unit=goalies, role='G'))
    return rows


def partition_ambiguous_teams(rows):
    """Keep other teams usable without guessing which duplicate name/status wins.

    A repeated name may describe distinct players (Vancouver's Petterssons) or
    conflicting availability. Preserve the source HTML and quarantine that team's
    entire published scenario; downstream selection retains its usual fallback.
    """
    seen, ambiguous = set(), set()
    for row in rows:
        key = (row['team'], normalized_name(row['player_name']))
        if key in seen:
            ambiguous.add(row['team'])
        seen.add(key)
    return [row for row in rows if row['team'] not in ambiguous], ambiguous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', required=True)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    raw = Path('data/raw/nhl/snapshots') / now.strftime('projected_lineups_%Y%m%dT%H%M%SZ')
    raw.mkdir(parents=True)
    sources = []

    def fetch(url, filename):
        with urlopen(Request(url, headers={'User-Agent': 'Rink-Lab/0.1 research'}), context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=60) as response:
            data = response.read()
        (raw / filename).write_bytes(data)
        return data, dict(file=filename, url=url, retrieved_at_utc=datetime.now(timezone.utc).isoformat(), sha256=hashlib.sha256(data).hexdigest())

    data, source = fetch('https://api-web.nhle.com/v1/schedule/' + args.date, 'schedule.json')
    sources.append(source)
    games = [g for day in json.loads(data)['gameWeek'] if day['date'] == args.date for g in day['games'] if g['gameType'] == 2]
    if not games:
        raise ValueError('No official games for requested date')
    rows, coverage = [], []

    def acquire_game(game):
        names = {game[side]['abbrev']: game[side]['placeName']['default'] + ' ' + game[side]['commonName']['default'] for side in ['awayTeam', 'homeTeam']}
        slug = '-'.join(re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') for name in names.values())
        date_slug = pd.Timestamp(args.date).strftime('%B-%-d-%Y').lower()
        url = f'https://www.nhl.com/news/{slug}-game-preview-{date_slug}'
        try:
            html, article_source = fetch(url, f'lineup_{game["id"]}.html')
            article = ArticleParagraphs()
            article.feed(html.decode())
            parsed = parse_lineups(article.paragraphs, names)
            if not parsed or not all(team in {r['team'] for r in parsed} for team in names):
                raise ValueError('Incomplete article lineup coverage')
        except Exception as error:
            return [], [dict(game_id=game['id'], team=team, status='source_unavailable', detail=str(error), source_url=url) for team in names], []
        parsed, ambiguous_teams = partition_ambiguous_teams(parsed)
        game_sources = [article_source]
        for team in names:
            if team in ambiguous_teams:
                continue
            roster_data, roster_source = fetch(f'https://api-web.nhle.com/v1/roster/{team}/current', f'roster_{team}.json')
            game_sources.append(roster_source)
            roster = json.loads(roster_data)
            identities = {}
            for group in ['forwards', 'defensemen', 'goalies']:
                for player in roster[group]:
                    name = player['firstName']['default'] + ' ' + player['lastName']['default']
                    identities.setdefault(normalized_name(name), []).append(player['id'])
            for row in parsed:
                if row['team'] != team:
                    continue
                identity_name = ROSTER_NAME_ALIASES.get((team, row['player_name']), row['player_name'])
                matches = identities.get(normalized_name(identity_name), [])
                row.update(game_id=game['id'], date=args.date, player_id=matches[0] if len(matches) == 1 else None,
                           match_status='matched' if len(matches) == 1 else 'unresolved', source_url=url,
                           identity_name=identity_name, match_method='explicit_roster_spelling_alias' if identity_name != row['player_name'] else 'normalized_exact_name',
                           retrieved_at_utc=article_source['retrieved_at_utc'], source_status='projected_not_confirmed')
        return parsed, [dict(game_id=game['id'], team=team,
                            status='ambiguous_player_names_or_statuses' if team in ambiguous_teams else 'projected_lineup_available',
                            source_url=url) for team in names], game_sources

    with ThreadPoolExecutor(max_workers=6) as pool:
        for game_rows, game_coverage, game_sources in pool.map(acquire_game, games):
            rows.extend(game_rows)
            coverage.extend(game_coverage)
            sources.extend(game_sources)
    out = Path('data/processed/forecasts') / raw.name
    out.mkdir(parents=True)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError('No projected lineups acquired')
    if frame.duplicated(['game_id', 'team', 'player_name']).any():
        raise ValueError('Duplicate player in projected lineup source')
    frame.to_csv(out / 'projected_lineups.csv', index=False)
    pd.DataFrame(coverage).to_csv(out / 'coverage.csv', index=False)
    metadata = dict(date=args.date, retrieved_at_utc=datetime.now(timezone.utc).isoformat(), raw_snapshot=str(raw), sources=sources,
                    interpretation='Published projected lineups. First-listed goalies are projected, including any game-time decisions; ordering does not establish confirmation.',
                    files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')})
    (raw / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (out / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('Projected lineups:', out)
    print(frame.groupby(['team', 'projected_status']).size().to_string())
    print('Unresolved names:', frame.loc[frame.match_status.ne('matched'), ['team', 'player_name', 'projected_status']].to_dict('records'))


if __name__ == '__main__':
    main()
