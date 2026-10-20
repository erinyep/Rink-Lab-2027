#!/usr/bin/env python3
"""Refresh, build skaters/goalies, and validate one complete pregame release.

Requires network access and local ESPN credentials. --prepared-inputs accepts a
JSON of paths from already refreshed sources for reproducible build-only runs.
No outcomes or fitted parameters are changed; no external publication occurs.
"""
import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import subprocess
import sys


def run(script, args, marker=None):
    result=subprocess.run([sys.executable,str(Path('scripts')/script),*map(str,args)],
        text=True,stdout=subprocess.PIPE,check=True)
    print(result.stdout,end='',flush=True)
    if marker:
        paths=[line.split(marker,1)[1].strip() for line in result.stdout.splitlines() if line.startswith(marker)]
        if len(paths)!=1 or not Path(paths[0]).is_dir(): raise ValueError('Invalid acquisition path')
        return paths[0]
    return result.stdout


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--date',type=date.fromisoformat,required=True)
    ap.add_argument('--template-forecast',type=Path,required=True)
    ap.add_argument('--prepared-inputs',type=Path)
    ap.add_argument('--allow-context-lag',action='store_true')
    a=ap.parse_args(); target=str(a.date)
    if a.prepared_inputs:
        inputs=json.loads(a.prepared_inputs.read_text())
    else:
        boxes=run('acquire_current_game_history.py',['--through',str(a.date-timedelta(days=1))],'Current history snapshot:')
        actuals=run('complete_fantasy_game_stats.py',['--boxscore-snapshots',boxes],'Fantasy game output:')
        toi=json.loads(run('acquire_game_toi.py',['--before',target,'--boxscore-snapshot',boxes]))['output']
        espn=run('refresh_espn_snapshot.py',[],'Raw snapshot:')
        # Each projection export is immutable and paired with this crosswalk.
        benchmark=Path(actuals)/'espn_benchmark.csv'
        run('export_espn_projection_benchmark.py',['--espn-snapshot',espn,'--out',benchmark])
        mp=run('refresh_moneypuck.py',[],'MoneyPuck snapshot:')
        pbp=run('acquire_defense_play_by_play.py',['--boxscores',boxes],'Defense PBP output:')
        shots=run('acquire_moneypuck_shots.py',['--boxscores',boxes],'MoneyPuck shots output:')
        inputs=dict(boxscore_history=boxes,game_history=actuals,game_toi=toi,espn_benchmark=str(benchmark),
            moneypuck_snapshot=mp,defense_pbp=pbp,moneypuck_shots=shots)
    args=['--date',target,'--template-forecast',a.template_forecast]
    for key in ['game_history','boxscore_history','game_toi','espn_benchmark','moneypuck_snapshot','defense_pbp']:
        args += ['--'+key.replace('_','-'),inputs[key]]
    if inputs.get('moneypuck_shots'): args += ['--moneypuck-shots',inputs['moneypuck_shots']]
    bundle=run('build_daily_forecasts.py',args,'Daily bundle:')
    goalie=run('build_goalie_game_forecasts.py',['--simulation',bundle,
        '--injury-context',str(Path(bundle)/'inputs/pregame_injury_context.csv'),
        '--game-history',inputs['game_history'],'--boxscore-history',inputs['boxscore_history'],
        '--output-root',str(Path(bundle)/'inputs')],'Goalie output:')
    flags=['--allow-context-lag'] if a.allow_context_lag else []
    run('finalize_daily_bundle.py',['--bundle',bundle,'--goalies',goalie,*flags])
    print('Issued bundle:',bundle)


if __name__=='__main__': main()
