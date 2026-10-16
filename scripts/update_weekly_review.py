#!/usr/bin/env python3
"""Acquire official finals, validate scoring details, and publish a weekly review.

Uses explicit frozen evaluation directories; never fits or fabricates forecasts.
Stops immediately on acquisition/validation errors. No ESPN credentials needed.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def run(script, args, marker=None):
    result = subprocess.run([sys.executable, str(Path('scripts')/script), *map(str,args)],
                            text=True, stdout=subprocess.PIPE, check=True)
    print(result.stdout, end='', flush=True)
    if marker:
        paths = [line.split(marker, 1)[1].strip() for line in result.stdout.splitlines() if line.startswith(marker)]
        if len(paths) != 1 or not Path(paths[0]).is_dir():
            raise ValueError('Missing or ambiguous acquisition output path')
        return paths[0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start', required=True)
    p.add_argument('--end', required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--evaluations', type=Path, nargs='+', required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('Choose a new output directory to preserve previous reports')
    boxes = run('acquire_current_game_history.py', ['--through', a.end], 'Current history snapshot:')
    actuals = run('complete_fantasy_game_stats.py', ['--boxscore-snapshots', boxes], 'Fantasy game output:')
    evaluations = []
    for source in a.evaluations:
        old = json.loads((source/'manifest.json').read_text())
        args = ['--bundle', old['frozen_bundle'], '--actuals', actuals, '--boxscores', boxes]
        if old.get('external_goalie_source'):
            args += ['--goalie-source', old['external_goalie_source']]
        evaluations.append(run('evaluate_daily_forecasts.py', args, 'Evaluated bundle:'))
    run('review_forecast_week.py', ['--start', a.start, '--end', a.end, '--baseline', a.baseline,
        '--actuals', actuals, '--out', a.out, '--evaluations', *evaluations])


if __name__ == '__main__':
    main()
