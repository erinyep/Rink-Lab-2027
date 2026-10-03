"""Descriptive MIN pair usage and goal attribution; Python standard library only.

Run with --acquire for a new immutable NHL snapshot, or --snapshot PATH to reuse.
Goals use official HTML on-ice lists, avoiding shift-boundary attribution guesses.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import itertools
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SEASON = 20252026
TEAM = 30


class Plays(HTMLParser):
    """Extract outer play rows while retaining nested on-ice player titles."""
    def __init__(self, html):
        super().__init__()
        self.rows = []
        self.depth = 0
        self.cells = None
        self.font = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            if self.cells is not None:
                self.depth += 1
            elif attrs.get('id', '').startswith('PL-'):
                self.depth = 1
                self.cells = []
        if self.cells is None:
            return
        if tag == 'td' and self.depth == 1:
            self.cells.append({'text': '', 'players': []})
        if tag == 'br' and self.cells:
            self.cells[-1]['text'] += '|'
        if tag == 'font' and 'title' in attrs:
            self.font = [attrs['title'], '']

    def handle_data(self, data):
        if self.cells:
            self.cells[-1]['text'] += data
        if self.font is not None:
            self.font[1] += data

    def handle_endtag(self, tag):
        if tag == 'font' and self.font is not None:
            self.cells[-1]['players'].append(tuple(self.font))
            self.font = None
        if tag == 'tr' and self.cells is not None:
            self.depth -= 1
            if self.depth == 0:
                self.rows.append(self.cells)
                self.cells = None


def seconds(value):
    m, s = map(int, value.split(':'))
    return 60 * m + s


def dump_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def acquire():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT / 'data/raw/nhl/snapshots' / f'min_pairs_{SEASON}_{stamp}'
    folder.mkdir(parents=True, exist_ok=False)
    manifest = []

    def fetch(item):
        name, url = item
        path = folder / name
        subprocess.run(['curl', '-sS', '-L', '--fail', '--retry', '3',
                        '--max-time', '90', url, '-o', str(path)], check=True)
        return {'file': name, 'url': url,
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    manifest.append(fetch(('schedule.json', f'https://api-web.nhle.com/v1/club-schedule-season/MIN/{SEASON}')))
    schedule = json.loads((folder / 'schedule.json').read_text())
    games = [g for g in schedule['games'] if g['gameType'] == 2]
    jobs = []
    for game in games:
        gid = game['id']
        jobs.extend([
            (f'{gid}_pbp.json', f'https://api-web.nhle.com/v1/gamecenter/{gid}/play-by-play'),
            (f'{gid}_shifts.json', f'https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={gid}&limit=10000'),
            (f'{gid}_report.html', f'https://www.nhl.com/scores/htmlreports/{SEASON}/PL{str(gid)[4:]}.HTM')])
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, result in enumerate(pool.map(fetch, jobs), 1):
            manifest.append(result)
            if i % 30 == 0:
                print(f'Retrieved {i}/{len(jobs)} game sources', flush=True)
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f'Snapshot: {folder.relative_to(ROOT)}', flush=True)
    return folder


def analyze(folder):
    schedule = json.loads((folder / 'schedule.json').read_text())
    games = [g for g in schedule['games'] if g['gameType'] == 2]
    assert len(games) == len({g['id'] for g in games}) == 82
    names, totals, goal_rows, stint_rows, audit = {}, defaultdict(Counter), [], [], []
    pair_games, scorers = defaultdict(set), defaultdict(Counter)
    for game in games:
        gid = game['id']
        pbp = json.loads((folder / f'{gid}_pbp.json').read_text())
        shifts = json.loads((folder / f'{gid}_shifts.json').read_text())
        assert pbp['season'] == SEASON and pbp['gameType'] == 2
        assert pbp['gameState'] in ('OFF', 'FINAL')
        assert len(shifts['data']) == shifts['total'], 'Shift pagination incomplete'
        assert len({s['id'] for s in shifts['data']}) == len(shifts['data'])
        roster = {r['playerId']: r for r in pbp['rosterSpots']}
        assert len(roster) == len(pbp['rosterSpots'])
        for pid, r in roster.items():
            names[pid] = r['firstName']['default'] + ' ' + r['lastName']['default']
        defenders = {pid for pid, r in roster.items() if r['teamId'] == TEAM and r['positionCode'] == 'D'}
        sweaters = {r['sweaterNumber']: pid for pid, r in roster.items() if r['teamId'] == TEAM}
        intervals = defaultdict(list)
        duplicate_intervals = 0
        seen = set()
        for s in shifts['data']:
            if s['typeCode'] != 517 or s['playerId'] not in defenders:
                continue
            assert s['gameId'] == gid and s['teamId'] == TEAM
            start, end = seconds(s['startTime']), seconds(s['endTime'])
            assert 0 <= start <= end <= (1200 if s['period'] <= 3 else 300)
            key = (s['playerId'], s['period'], start, end)
            if key in seen:
                duplicate_intervals += 1
                continue
            seen.add(key)
            if end > start:
                intervals[s['period']].append((start, end, s['playerId']))
        # A showing is a maximal uninterrupted overlap of this pair, within a
        # period. Three-D usage includes every co-present pair, explicitly.
        for period, spans in intervals.items():
            points = sorted({t for a, b, _ in spans for t in (a, b)})
            pair_spans = defaultdict(list)
            for a, b in zip(points, points[1:]):
                active = {pid for start, end, pid in spans if start <= a and end >= b}
                for pair in itertools.combinations(sorted(active), 2):
                    runs = pair_spans[pair]
                    if runs and runs[-1][1] == a:
                        runs[-1][1] = b
                    else:
                        runs.append([a, b])
            for pair, runs in pair_spans.items():
                pair_games[pair].add(gid)
                totals[pair]['showings'] += len(runs)
                totals[pair]['seconds'] += sum(b-a for a, b in runs)
                for a, b in runs:
                    stint_rows.append(dict(game_id=gid, period=period, player_1_id=pair[0], player_2_id=pair[1], start_seconds=a, end_seconds=b, duration_seconds=b-a))
        html_goals = [r for r in Plays((folder / f'{gid}_report.html').read_text()).rows
                      if len(r) >= 8 and r[4]['text'].strip() == 'GOAL'
                      and r[1]['text'].strip() in ('1', '2', '3', '4')]
        api_goals = [p for p in pbp['plays'] if p['typeDescKey'] == 'goal' and p['periodDescriptor']['periodType'] != 'SO']
        assert len(html_goals) == len(api_goals), (gid, 'goal count mismatch')
        used = set()
        away = pbp['awayTeam']['id'] == TEAM
        gf = ga = 0
        for p in api_goals:
            period, time = p['periodDescriptor']['number'], seconds(p['timeInPeriod'])
            matched = [(i, r) for i, r in enumerate(html_goals) if i not in used
                       and int(r[1]['text'].strip()) == period and seconds(r[3]['text'].strip().split('|')[0]) == time]
            assert len(matched) == 1, (gid, period, time)
            i, row = matched[0]
            used.add(i)
            for_us = p['details']['eventOwnerTeamId'] == TEAM
            assert row[5]['text'].strip().startswith('MIN ') == for_us
            onice = row[6 if away else 7]['players']
            assert onice, (gid, 'missing on-ice list')
            d_ids = sorted(sweaters[int(number.strip())] for title, number in onice if title.startswith('Defense -'))
            assert set(d_ids) <= defenders and len(d_ids) == len(set(d_ids))
            scorer = p['details']['scoringPlayerId']
            assert scorer in roster
            gf += int(for_us)
            ga += int(not for_us)
            pairs = list(itertools.combinations(d_ids, 2))
            for pair in pairs:
                totals[pair]['goals_for' if for_us else 'goals_against'] += 1
                if for_us:
                    scorers[pair][scorer] += 1
            goal_rows.append(dict(game_id=gid, date=game['gameDate'], period=period,
                                  time=p['timeInPeriod'], event_id=p['eventId'], wild_goal=int(for_us),
                                  scorer_player_id=scorer, scorer=names[scorer],
                                  defense_count=len(d_ids), defense_player_ids=';'.join(map(str, d_ids)),
                                  defense_names=';'.join(names[d] for d in d_ids), situation=p.get('situationCode', '')))
        # Final scores include one extra winner goal for shootouts; events do not.
        own, opp = (game['awayTeam'], game['homeTeam']) if away else (game['homeTeam'], game['awayTeam'])
        shootout = game.get('gameOutcome', {}).get('lastPeriodType') == 'SO'
        assert gf == own['score'] - int(shootout and own['score'] > opp['score'])
        assert ga == opp['score'] - int(shootout and opp['score'] > own['score'])
        audit.append(dict(game_id=gid, shift_rows=len(shifts['data']), duplicate_defense_intervals=duplicate_intervals,
                          goals_for=gf, goals_against=ga, matched_html_goals=len(used)))
    denominator = sum(r['wild_goal'] for r in goal_rows)
    summary, scorer_rows = [], []
    for pair, values in sorted(totals.items(), key=lambda kv: (-kv[1]['goals_for'], -kv[1]['seconds'])):
        gf, ga = values['goals_for'], values['goals_against']
        summary.append(dict(player_1_id=pair[0], player_1=names[pair[0]], player_2_id=pair[1], player_2=names[pair[1]],
                            games_together=len(pair_games[pair]), showings=values['showings'], shared_minutes=round(values['seconds']/60, 2),
                            wild_goals=gf, share_of_wild_goals_pct=round(100*gf/denominator, 2), goals_against=ga,
                            on_ice_goal_share_pct=round(100*gf/(gf+ga), 2) if gf+ga else '',
                            scorers='; '.join(f'{names[p]}: {n}' for p, n in scorers[pair].most_common())))
        assert sum(scorers[pair].values()) == gf
        for scorer, count in scorers[pair].most_common():
            scorer_rows.append(dict(player_1_id=pair[0], player_2_id=pair[1], scorer_player_id=scorer,
                                    scorer=names[scorer], goals=count, pct_of_pair_goals=round(100*count/gf, 2)))
    output = ROOT / 'data/processed/min_defense_pairs_2025_26'
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in [('pairs', summary), ('scorers', scorer_rows), ('goals', goal_rows), ('stints', stint_rows), ('validation', audit)]:
        dump_csv(output / f'{name}.csv', rows)
    coverage = dict(snapshot=str(folder.relative_to(ROOT)), games=len(games), wild_goals=denominator,
                    wild_goals_by_defense_count=dict(Counter(r['defense_count'] for r in goal_rows if r['wild_goal'])),
                    pair_count=len(summary), stint_count=len(stint_rows), defensemen=len({p for pair in totals for p in pair}),
                    source_files_verified=len(json.loads((folder / 'manifest.json').read_text())))
    for source in json.loads((folder / 'manifest.json').read_text()):
        assert hashlib.sha256((folder / source['file']).read_bytes()).hexdigest() == source['sha256']
    (output / 'coverage.json').write_text(json.dumps(coverage, indent=2))
    lines = ['# Minnesota Wild defense pairs — 2025–26 regular season', '',
             'Question: How often did each defense pair play together, and what share of Wild goals occurred with them on the ice?', '',
             f'All {len(games)} games; {denominator} Wild goals excluding shootout-deciding team goals. All strengths, including overtime and empty-net play. No minimum usage filter.', '',
             'Share of Wild goals = goals with the pair on ice / all Wild goals. A showing is a continuous overlap of the two defensemen’s shifts within a period, not a game or possession. Games together and shared minutes provide additional exposure context. If three defensemen are on ice, each co-present pair is counted; pair percentages therefore need not sum to 100%. One-defenseman goals remain in the denominator but have no pair.', '',
             'Goal assignments use official NHL HTML on-ice lists matched to API goal events by period/time and scoring team. Shift intervals determine usage only. These are descriptive results, not estimates of pair skill or causation.', '',
             '| Pair | Games | Showings | Minutes | Wild goals | % of Wild goals | Wild scorers (goals) |',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in summary:
        lines.append(f"| {r['player_1']} / {r['player_2']} | {r['games_together']} | {r['showings']} | {r['shared_minutes']:.2f} | {r['wild_goals']} | {r['share_of_wild_goals_pct']:.2f}% | {r['scorers'] or 'None'} |")
    lines += ['', '## Validation and reproduction', '', f'Coverage: `{json.dumps(coverage)}`', '',
              'Checked all 82 completed games, unique game/roster/shift IDs, complete shift API totals, valid shift times, nonmissing goal scorers and on-ice lists, HTML/API goal agreement, final-score reconciliation including shootout adjustments, scorer totals, and source SHA-256 hashes. Exact duplicate defense shift intervals are deduplicated and counted in validation.csv. Zero-duration shifts contribute no usage. Source positions define defensemen; no games-played or TOI thresholds.', '',
              'Sources: [NHL schedule](https://api-web.nhle.com/v1/club-schedule-season/MIN/20252026), [NHL play-by-play example](https://api-web.nhle.com/v1/gamecenter/2025020015/play-by-play), [NHL shift charts](https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId=2025020015&limit=10000), [official on-ice report example](https://www.nhl.com/scores/htmlreports/20252026/PL020015.HTM). Full URLs, retrieval timestamps and hashes are in the snapshot manifest.', '',
              'Standard-library Python plus curl; no new Python dependencies.', '',
              f'Reuse snapshot: `python3 src/analysis/min_defense_pairs.py --snapshot {folder.relative_to(ROOT)}`', '',
              'New acquisition: `python3 src/analysis/min_defense_pairs.py --acquire`', '',
              'CSV exports: `data/processed/min_defense_pairs_2025_26/{pairs,scorers,goals,stints,validation}.csv`. Raw and processed datasets are local, Git-ignored artifacts.']
    (ROOT / 'outputs/min_defense_pairs_2025_26/README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(coverage, indent=2))
    for r in summary[:10]:
        print(r)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--acquire', action='store_true')
    mode.add_argument('--snapshot', type=Path)
    args = parser.parse_args()
    analyze(acquire() if args.acquire else args.snapshot.resolve())
