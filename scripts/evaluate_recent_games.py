#!/usr/bin/env python3
"""Audit frozen pregame conditional forecasts against official final boxscores."""
import argparse
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
    parser.add_argument('--forecast', type=Path, required=True)
    parser.add_argument('--dates', nargs='+', required=True)
    parser.add_argument('--raw-snapshot', type=Path, help='Resume/read an existing acquisition without overwriting source files')
    parser.add_argument('--current-forecast', type=Path, help='Include refreshed forecasts in the Markdown readout')
    parser.add_argument('--no-readout', action='store_true', help='Export generic game diagnostics without the October 6–7 report')
    parser.add_argument('--completed-only', action='store_true', help='Skip scheduled/live games, recording them in acquisition metadata')
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    raw = args.raw_snapshot or Path('data/raw/nhl/snapshots') / f'game_review_{stamp}'
    raw.mkdir(parents=True, exist_ok=args.raw_snapshot is not None)
    sources = []
    exceptions = []
    def fetch(endpoint, filename):
        url = 'https://api-web.nhle.com/v1/' + endpoint
        path = raw / filename
        if path.exists():
            payload = path.read_bytes()
        else:
            request = Request(url, headers={'User-Agent': 'Rink-Lab/0.1', 'Accept': 'application/json'})
            with urlopen(request, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=60) as response:
                payload = response.read()
            path.write_bytes(payload)
        sources.append(dict(url=url, file=filename, sha256=hashlib.sha256(payload).hexdigest(),
                            saved_file_time_utc=datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()))
        return json.loads(payload)
    schedule = fetch('schedule/' + min(args.dates), 'schedule.json')
    games = [g for d in schedule['gameWeek'] if d['date'] in args.dates for g in d['games']
             if g['gameType'] == 2]
    unfinished = [g['id'] for g in games if g['gameState'] not in ['OFF','FINAL']]
    if args.completed_only:
        games = [g for g in games if g['gameState'] in ['OFF','FINAL']]
    require(games, 'No games available for evaluation')
    require(set(args.dates) <= {d['date'] for d in schedule['gameWeek']}, 'Incomplete date coverage')
    observed, coverage = [], []
    for game in games:
        box = fetch(f"gamecenter/{game['id']}/boxscore", f"boxscore_{game['id']}.json")
        require(box['gameState'] in ['OFF', 'FINAL'], 'Game not final')
        require(box['id'] == game['id'] and box['season'] == 20262027 and box['gameType'] == 2,
                'Wrong game/season/type')
        game_rows = []
        for side in ['homeTeam', 'awayTeam']:
            players = box['playerByGameStats'][side]
            skaters = players['forwards'] + players['defense']
            require(len({p['playerId'] for p in skaters}) == len(skaters), 'Duplicate skater')
            shot_total = sum(p['sog'] for p in skaters)
            if shot_total != box[side]['sog']:
                exceptions.append(dict(game_id=box['id'], team=box[side]['abbrev'],
                    check='sum_skater_sog_equals_team_sog', skater_sum=shot_total, team_total=box[side]['sog']))
            # Shootout deciding goals are excluded from player scoring totals.
            deciding = box.get('gameOutcome', {}).get('lastPeriodType') == 'SO'
            total_goals = sum(p['goals'] for p in skaters)
            require(total_goals == box[side]['score'] or (deciding and total_goals == box[side]['score'] - 1),
                    'Team goals do not reconcile')
            for p in skaters:
                require(p['points'] == p['goals'] + p['assists'], 'Scoring identity failed')
                minutes, seconds = map(int, p['toi'].split(':'))
                game_rows.append(dict(game_id=box['id'], game_date=box['gameDate'], player_id=p['playerId'],
                    actual_name=p['name']['default'], actual_team=box[side]['abbrev'],
                    goals=p['goals'], assists=p['assists'], shots=p['sog'], points=p['points'],
                    hits=p['hits'], penalty_minutes=p['pim'], plus_minus=p['plusMinus'],
                    toi_minutes=minutes + seconds / 60, appeared=minutes * 60 + seconds > 0))
        observed.extend(game_rows)
        coverage.append(dict(game_id=box['id'], game_date=box['gameDate'], start_time_utc=box['startTimeUTC'],
            matchup=box['awayTeam']['abbrev'] + ' @ ' + box['homeTeam']['abbrev'],
            score=f"{box['awayTeam']['score']}-{box['homeTeam']['score']}", actual_skater_rows=len(game_rows)))
    if not (raw / 'metadata.json').exists():
        (raw / 'metadata.json').write_text(json.dumps(dict(sources=sources, dates=args.dates,
            completed_only=args.completed_only, unfinished_game_ids=unfinished), indent=2) + '\n')
    out = Path('data/processed/forecasts') / f'game_review_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    actual = pd.DataFrame(observed)
    require(not actual.duplicated(['game_id', 'player_id']).any(), 'Duplicate player/game')
    actual.to_csv(out / 'actual_skater_games.csv', index=False)
    pd.DataFrame(exceptions, columns=['game_id','team','check','skater_sum','team_total']).to_csv(out / 'source_exceptions.csv', index=False)
    manifest = json.loads((args.forecast / 'manifest.json').read_text())
    filename = 'scheduled_skater_game_forecasts.csv'
    require(hashlib.sha256((args.forecast / filename).read_bytes()).hexdigest() == manifest['files'][filename],
            'Frozen forecast hash mismatch')
    predictions = pd.read_csv(args.forecast / filename)
    predictions = predictions[predictions.game_id.isin(actual.game_id.unique())].copy()
    # Actual artifact creation time is the conservative availability cutoff.
    require((pd.to_datetime(predictions.start_time_utc, utc=True) > pd.Timestamp(manifest['created_at_utc'])).all(),
            'Forecast artifact was created after game start')
    alias_rows = predictions[predictions.player_id.notna() & predictions.duplicated(['game_id','player_id'], keep=False)]
    alias_rows.to_csv(out / 'espn_alias_rows.csv', index=False)
    for _, aliases in alias_rows.groupby(['game_id','player_id']):
        for event in ['goals','assists','shots','points','toi_minutes']:
            require(aliases[f'{event}_if_plays'].nunique(dropna=False) == 1, 'Conflicting forecasts for ESPN aliases')
    # Preserve aliases in an audit, evaluate one NHL appearance once, prefer scoring ownership.
    resolved = predictions[predictions.player_id.notna()].sort_values('pool', ascending=False).drop_duplicates(['game_id','player_id'])
    predictions = pd.concat([resolved, predictions[predictions.player_id.isna()]], ignore_index=True)
    joined = predictions.merge(actual, on=['game_id', 'player_id'], how='left', validate='many_to_one', indicator=True)
    joined['appearance_status'] = joined['_merge'].map({'both':'boxscore_row', 'left_only':'no_boxscore_row', 'right_only':'unexpected'})
    joined.to_csv(out / 'frozen_forecast_vs_actual.csv', index=False)
    metrics = []
    for group, frame in [('all_saved_pool', joined), ('saved_scoring_roster', joined[joined.pool == 'rostered'])]:
        for date in ['combined'] + args.dates:
            subset = frame if date == 'combined' else frame[frame.game_date == date]
            for event in ['goals', 'assists', 'shots', 'points', 'hits', 'penalty_minutes', 'plus_minus', 'toi_minutes']:
                valid = subset[(subset.appeared == True) & subset[f'{event}_if_plays'].notna()].copy()
                if valid.empty:
                    continue
                error = valid[f'{event}_if_plays'] - valid[event]
                metrics.append(dict(group=group, date=date, category=event, player_games=len(valid),
                    predicted_total=valid[f'{event}_if_plays'].sum(), actual_total=valid[event].sum(),
                    mae=error.abs().mean(), bias=error.mean(), rmse=(error.pow(2).mean()) ** .5))
    pd.DataFrame(metrics).to_csv(out / 'game_metrics.csv', index=False)
    covered_ids = set(predictions.game_id)
    for row in coverage:
        row['saved_pregame_schedule_coverage'] = row['game_id'] in covered_ids
        row['saved_forecast_rows'] = int((predictions.game_id == row['game_id']).sum())
    pd.DataFrame(coverage).to_csv(out / 'game_coverage.csv', index=False)
    (out / 'manifest.json').write_text(json.dumps(dict(raw_snapshot=str(raw), frozen_forecast=str(args.forecast),
        frozen_created_at_utc=manifest['created_at_utc'], sources=sources,
        forecast_rows=len(joined), no_boxscore_rows=int((joined['_merge'] == 'left_only').sum()),
        source_exceptions=exceptions,
        limitations=['Conditional means evaluated only among boxscore appearances with positive TOI.',
                     'No boxscore row is not a verified scratch or a zero event forecast.',
                     'Saved ESPN pool is not the entire NHL population; saved ownership is not current ownership.',
                     'Two dates are a diagnostic, not model selection or calibrated game-level validation.']), indent=2) + '\n')
    if args.no_readout:
        print('Review output:', out)
        print(pd.DataFrame(metrics).query("date == 'combined'").to_string(index=False))
        return
    def table(frame):
        def cell(value):
            return f'{value:.3f}' if isinstance(value, float) else str(value)
        return '\n'.join(['| ' + ' | '.join(frame.columns) + ' |',
            '| ' + ' | '.join(['---'] * len(frame.columns)) + ' |'] +
            ['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in frame.itertuples(index=False, name=None)])
    m = pd.DataFrame(metrics)
    main_metrics = m[(m.group == 'all_saved_pool') & (m.date == 'combined') & m.category.isin(['goals','assists','shots'])]
    roster_metrics = m[(m.group == 'saved_scoring_roster') & (m.date == 'combined') & m.category.isin(['goals','assists','shots'])]
    columns = ['category','player_games','predicted_total','actual_total','mae','bias']
    report = [
        '# October 6–7 forecast readout and October 8 preparation',
        '\nThe frozen model overpredicted assists and shots in this small sample; goals were close in aggregate. '
        'This is a first game-level diagnostic, not evidence that the model is calibrated or that a parameter change is justified.',
        '\n## Fair comparison and coverage',
        f'\nThe evaluated forecast artifact was created at **{manifest["created_at_utc"]}** '
        '(7:50 PM EDT October 6). Six October 6 games had already started and have no saved pregame scheduled forecasts. '
        'The three later October 6 games and all three October 7 games are eligible. '
        'Newly refreshed statistics are never used to recreate those predictions.',
        '\n' + table(pd.DataFrame(coverage)[['game_date','matchup','score','saved_pregame_schedule_coverage']]),
        f'\nAll 12 final boxscores were acquired: {len(actual)} unique skater/game rows. '
        f'The six covered games have 216 skater appearances; 213 have saved usable predictions. '
        f'The saved schedule pool contains {len(joined)} rows for these games, including '
        f'{int((joined.forecast_status == "unresolved_nhl_identity").sum())} unresolved NHL identities, '
        f'{int((joined.forecast_status == "no_recent_nhl_skater_history").sum())} rows without recent skater history, and '
        f'{int(((joined.player_id.notna()) & joined.appeared.isna()).sum())} resolved players absent from the game boxscore. '
        'These absent rows are retained but excluded from conditional-production metrics; they are not assigned zero outcomes. '
        'Historical players attached to teams in ESPN are not necessarily current NHL roster members.',
        '\n## Production if the player plays',
        '\n' + table(main_metrics[columns]),
        '\nMAE is average absolute error per player appearance. Bias is prediction minus actual; positive means overprediction. '
        'Predicted totals sum conditional means only across evaluated appearances. They are not unconditional team forecasts.',
        '\nBy date (same saved-pool appearance population):',
        '\n' + table(m[(m.group == 'all_saved_pool') & (m.date != 'combined') & m.category.isin(['goals','assists','shots'])][['date'] + columns]),
        '\n### Saved ESPN scoring-roster players',
        '\n' + table(roster_metrics[columns]),
        '\nThis covers all six fantasy teams, not specifically your team. Ownership is from the October 6 snapshot. '
        '35 rostered players appeared; Connor Bedard and Zach Hyman had saved forecasts but no boxscore appearance. '
        'Their saved injury labels were INJURY_RESERVE and OUT. No participation probabilities were fitted.',
    ]
    misses = joined[(joined.pool == 'rostered') & (joined.appeared == True)].copy()
    misses['points_error'] = misses.points_if_plays - misses.points
    report += ['\nLargest point misses among saved scoring-roster appearances:', '\n' + table(
        misses.sort_values('points_error', key=abs, ascending=False)[['player_name','game_date','points_if_plays','points','shots_if_plays','shots']].head(8)),
        '\nA mean such as 1.2 points is not a prediction that the player will score exactly one point. '
        'Burst scoring and scoreless games are expected; calibrated distributions are still missing.',
        '\n## Source checks and limitations',
        '\nGame IDs, season, regular-season type, final status, unique player/game keys, and G+A=P passed. '
        'Player goals reconcile with final team scores (allowing a shootout deciding goal). '
        'Florida’s October 6 skater shots total 29 while its team boxscore reports 30. '
        'This source exception is retained in source_exceptions.csv; player-level metrics use reported player SOG. '
        'The cause is unresolved. All other team-shot checks passed. No PPP game evaluation is claimed because the '
        'boxscore supplies PP goals but not player PP assists.',
        '\nTwo dates cannot establish stable superiority, statistical significance, or new tuning settings. '
        'Individual-game MAE is not comparable with the earlier season-average MAE because outcomes differ. '
        'Missing lineup history still prevents an availability backtest.',
    ]
    if args.current_forecast:
        current_manifest = json.loads((args.current_forecast / 'manifest.json').read_text())
        today_rows = pd.read_csv(args.current_forecast / 'today_skater_game_forecasts.csv')
        roster_today = today_rows[today_rows.pool == 'rostered'].copy()
        tomorrow = args.current_forecast
        report += ['\n## Refreshed October 8 inputs and baseline forecasts',
            f'\nForecast build: **{current_manifest["created_at_utc"]}**. NHL reports and schedule were refreshed '
            f'at **{current_manifest["schedule"]["cutoff_utc"]}** (schedule cutoff); ESPN completed at '
            f'**{current_manifest["espn"]["retrieved_at_utc"]}**. Game dates are Eastern time; source timestamps shown here are UTC. '
            'This is a saved snapshot through source-reported totals at retrieval, not a continuously updating feed.',
            '\nThe current reports contain 630 skaters and 56 goalies. Skater validation passed; one goalie '
            'SA≠SV+GA exception remains flagged. The league has 134 scoring-roster entries: '
            '116 skaters receive conditional forecasts and 18 goalies remain unmodeled.',
            f'\nToday’s export covers **{today_rows.game_id.nunique()} games**, **{len(today_rows)} saved-pool rows**, '
            f'and **{len(roster_today)} scoring-roster skater rows**. The selected model remains weighted history '
            'with decay 0.5 and the existing provisional current-season update. No model settings were edited.',
            '\nHighest conditional point means among all six teams’ scoring-roster skaters (not a lineup recommendation):',
            '\n' + table(roster_today.sort_values('points_if_plays', ascending=False)[[
                'player_name','nhl_team_abbrev','opponent','goals_if_plays','assists_if_plays','shots_if_plays','injury_status']].head(12)),
            '\nCelebrini is DAY_TO_DAY in the refreshed ESPN snapshot; his values apply only if he plays. '
            'Injuries, scratches, goalie starts, opponent effects and fantasy lineup feasibility are still unmodeled.',
            f'\n[All today’s player/game forecasts](../../{tomorrow}/today_skater_game_forecasts.csv) · '
            f'[Updated observed skater stats](../../{tomorrow}/current_observed_stats.csv) · '
            f'[Refreshed ESPN player forecasts](../../{tomorrow}/espn_player_forecasts.csv)',
        ]
    report += ['\n## What to investigate before editing the model',
        '\n1. Extend the chronological game-level sample and compare weighted, last-season and process forecasts '
        'on identical appearances with frozen pregame inputs. Keep October 6–7 as a recorded diagnostic.',
        '2. Investigate shot overprediction through observed TOI versus predicted TOI and SOG per minute; '
        'avoid reducing all players’ rates based on six games.',
        '3. Acquire historical eligible-roster observations to distinguish scratches/injuries from players '
        'outside the NHL population, then evaluate participation and rolling TOI.',
        '4. Evaluate current-season update weights and rookie shrinkage in chronological validation windows '
        'before adopting a change. Goalies remain a separate baseline.',
        '\n## Reproduce and inspect',
        f'\nFrozen forecast: `{args.forecast}`. Review data: `{out}`. Raw source snapshot: `{raw}`.',
        f'\n[Player-by-player comparison](../../{out}/frozen_forecast_vs_actual.csv) · '
        f'[Metrics](../../{out}/game_metrics.csv) · [Coverage](../../{out}/game_coverage.csv) · '
        f'[Source exceptions](../../{out}/source_exceptions.csv)',
        '\n```sh\nrink-lab.venv/bin/python scripts/evaluate_recent_games.py \\\n'
        f'  --forecast {args.forecast} \\\n  --dates {" ".join(args.dates)} \\\n  --raw-snapshot {raw}' +
        (f' \\\n  --current-forecast {args.current_forecast}' if args.current_forecast else '') + '\n```',
    ]
    report_path = Path('outputs/per_game_forecast/october_6_7_readout.md')
    report_path.write_text('\n'.join(report) + '\n')
    print('Readout:', report_path)
    print('Review output:', out)
    print(pd.DataFrame(metrics).query("date == 'combined' and category in ['goals','assists','shots']").to_string(index=False))


if __name__ == '__main__':
    main()
