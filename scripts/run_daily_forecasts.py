#!/usr/bin/env python3
"""Refresh, issue and finalize a daily bundle; stop immediately on failed stages."""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(script, *arguments):
    subprocess.run([sys.executable, str(ROOT / 'scripts' / script), *map(str, arguments)],
                   cwd=ROOT, check=True)


def new_output(script, parent, pattern, *arguments):
    before = set(parent.glob(pattern))
    run(script, *arguments)
    created = set(parent.glob(pattern)) - before
    if len(created) != 1:
        raise RuntimeError(f'{script}: expected one new output, found {len(created)}')
    return created.pop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', required=True, type=date.fromisoformat)
    parser.add_argument('--template-forecast', required=True, type=Path)
    parser.add_argument('--report-team-id',type=int,help='Override configured team for the category report')
    parser.add_argument('--without-espn', action='store_true',
                        help='Issue public-only scenarios with unknown injuries and ownership')
    parser.add_argument('--boxscore-history', type=Path)
    parser.add_argument('--game-history', type=Path)
    parser.add_argument('--game-toi', type=Path)
    parser.add_argument('--moneypuck-snapshot', type=Path)
    args = parser.parse_args()
    # Resolve repository-relative paths consistently even when invoked elsewhere.
    import os
    os.chdir(ROOT)
    if not (args.template_forecast / 'manifest.json').exists():
        parser.error('Template missing: restore prior data or run build_per_game_forecast.py after NHL season acquisition')
    if not args.without_espn:
        # Validate private configuration before potentially expensive acquisition.
        sys.path.insert(0, str(ROOT))
        from src.fantasy.espn_client import ESPNConfig
        ESPNConfig.from_env()
        espn = new_output('refresh_espn_snapshot.py', Path('data/raw/espn/snapshots'), 'espn_*')
        benchmark = Path('data/processed/espn') / espn.name / 'projection_benchmark.csv'
        run('export_espn_projection_benchmark.py', '--espn-snapshot', espn, '--out', benchmark)
    else:
        benchmark = None
    boxes = args.boxscore_history or new_output('acquire_current_game_history.py',
        Path('data/raw/nhl/snapshots'), 'current_game_history_*', '--through', args.date - timedelta(days=1))
    games = args.game_history or new_output('complete_fantasy_game_stats.py',
        Path('data/processed/forecasts'), 'fantasy_game_details_*', '--boxscore-snapshots', boxes)
    toi = args.game_toi
    if toi is None:
        toi = new_output('acquire_game_toi.py', Path('data/processed/nhl'), 'game_toi_*',
                         '--before', args.date, '--boxscore-snapshot', boxes) / 'player_game_toi.csv'
    mp = args.moneypuck_snapshot or new_output('acquire_moneypuck_team_games.py',
        Path('data/raw/moneypuck/snapshots'), 'team_games_*')
    extra = ['--without-espn'] if args.without_espn else ['--espn-benchmark', benchmark]
    bundle = new_output('build_daily_forecasts.py', Path('data/processed/forecasts'), f'daily_{args.date}_*',
        '--date', args.date, '--template-forecast', args.template_forecast,
        '--game-history', games, '--boxscore-history', boxes,
        '--moneypuck-snapshot', mp, '--game-toi', toi, *extra)
    goalies = new_output('build_goalie_game_forecasts.py', bundle / 'inputs', f'goalies_{args.date}_*',
        '--simulation', bundle, '--injury-context', bundle / 'inputs/pregame_injury_context.csv',
        '--game-history', games, '--boxscore-history', boxes, '--output-root', bundle / 'inputs')
    run('finalize_daily_bundle.py', '--bundle', bundle, '--goalies', goalies)
    run('validate_daily_bundle.py', '--bundle', bundle)
    report_config=ROOT/'config/fantasy_report.json'
    report_team=args.report_team_id
    if report_team is None and report_config.exists():
        report_team=json.loads(report_config.read_text()).get('team_id')
    if report_team is not None and not args.without_espn:
        rules=new_output('acquire_fantasy_rules.py',Path('data/raw/espn/snapshots'),'rules_*')
        future=new_output('acquire_future_roster.py',Path('data/raw/espn/snapshots'),'future_roster_*')
        report_out=Path('reports/today')/f'{args.date}_team_{report_team}_{bundle.name}'
        run('build_today_report.py','--bundle',bundle,'--rules',rules,'--future-roster',future,
            '--team-id',report_team,'--out',report_out)
    print('Completed daily bundle:', bundle)
    print('Availability:', json.loads((bundle / 'manifest.json').read_text())['availability_status'])


if __name__ == '__main__':
    main()
