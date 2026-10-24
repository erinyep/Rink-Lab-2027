#!/usr/bin/env python3
"""Freeze an experimental team probability transform before games start."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate_daily_forecasts import verify_manifest_files, digest
from scripts.validate_daily_bundle import validate
from src.fantasy.team_probability import scoring_win_probability


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists(): raise ValueError('Preserve issued probabilities')
    validate(a.bundle)
    m = verify_manifest_files(a.bundle, [])
    schedule_path = Path(m['raw_context'])/'schedule.json'
    expected = next(s['sha256'] for s in m['sources'] if s['file']=='schedule.json')
    if digest(schedule_path) != expected: raise ValueError('Changed schedule')
    games = [g for d in json.loads(schedule_path.read_text())['gameWeek'] if d['date']==m['date']
             for g in d['games'] if g['gameType']==2 and g['season']==20262027]
    t = pd.read_csv(a.bundle/'team_projections.csv')
    t = t[t.model.eq('default')]
    now = datetime.now(timezone.utc)
    if set(t.game_id) != {g['id'] for g in games}: raise ValueError('Incomplete schedule')
    rows = []
    for g in games:
        if pd.Timestamp(g['startTimeUTC']) <= pd.Timestamp(now)+pd.Timedelta(minutes=10):
            raise ValueError('Insufficient pregame lead')
        z = t[t.game_id.eq(g['id'])].set_index('team')
        h, away = g['homeTeam']['abbrev'], g['awayTeam']['abbrev']
        if len(z)!=2 or set(z.index)!={h,away}: raise ValueError('Invalid team pair')
        prob = scoring_win_probability(z.loc[h,'expected_goals'], z.loc[away,'expected_goals'])
        rows.append(dict(game_id=g['id'], date=m['date'], start_time_utc=g['startTimeUTC'], home=h, away=away,
            home_goal_mean=z.loc[h,'expected_goals'], away_goal_mean=z.loc[away,'expected_goals'],
            home_win_probability=prob, away_win_probability=1-prob, issued_at_utc=now.isoformat(),
            model='independent_poisson_tie_split_v1', status='experimental_uncalibrated', actual_home_win=None))
    a.out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(a.out/'team_win_probabilities.csv', index=False)
    (a.out/'README.md').write_text(f'''# Experimental team win probabilities — {m['date']}

[Frozen probabilities for all {len(rows)} games](team_win_probabilities.csv).

Independent Poisson scoring counts from the default frozen team goal means, with tied
counts split equally. Away probability is exactly one minus home probability. No fitted
calibration, home-ice effect, confirmed-goalie adjustment or explicit OT/shootout model.
Full-game scoring means are an approximation for this purpose. These probabilities are
experimental and do not replace the main team outlook or fantasy goalie win scenarios.

Development screen: 36 saved games, Brier 0.238 versus 0.250 for 50/50; the paired interval
includes no improvement. That screen transformed old means after outcomes were known;
this is the first separately timestamped prospective probability release. Score future
official final winners, including overtime/shootouts, without refitting or choosing runs.
''')
    (a.out/'manifest.json').write_text(json.dumps(dict(created_at_utc=now.isoformat(),date=m['date'],
        bundle=str(a.bundle), bundle_sha256=digest(a.bundle/'manifest.json'),
        method='independent_poisson_tie_split_v1', code_sha256=digest(Path('src/fantasy/team_probability.py')),
        files={p.name:digest(p) for p in a.out.iterdir() if p.is_file()}),indent=2)+'\n')
    print('Probability trial:',a.out)


if __name__=='__main__': main()
