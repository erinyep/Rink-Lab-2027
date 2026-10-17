#!/usr/bin/env python3
"""Read-only release checks for finalized daily forecasts."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate(bundle):
    manifest = json.loads((bundle / 'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        require(hashlib.sha256((bundle / name).read_bytes()).hexdigest() == expected,
                f'Bundle hash mismatch: {name}')
    raw = Path(manifest['raw_context'])
    schedule = json.loads((raw / 'schedule.json').read_text())
    expected = {g['id'] for day in schedule['gameWeek'] if day['date'] == manifest['date']
                for g in day['games'] if g['gameType'] == 2 and g['season'] == 20262027}
    players = pd.read_csv(bundle / 'player_projections.csv')
    teams = pd.read_csv(bundle / 'team_projections.csv')
    goalies = pd.read_csv(bundle / 'goalie_projections.csv')
    coverage = pd.read_csv(bundle / 'game_team_coverage.csv')
    for frame, keys in [(players, ['game_id','player_id','model']),
                        (teams, ['game_id','team','model']),
                        (goalies, ['game_id','player_id','model'])]:
        require(not frame.duplicated(keys).any(), f'Duplicate identity: {keys}')
        require(set(frame.game_id) == expected, 'Official schedule game coverage differs')
        require(frame.filter(regex='^actual').isna().all().all(), 'Actuals populated in issued forecast')
        pregame = frame.issue_timing.eq('pregame')
        starts = pd.to_datetime(frame.loc[pregame,'start_time_utc'],utc=True)
        issued = (pd.to_datetime(frame.loc[pregame,'issued_at_utc'],utc=True)
                  if 'issued_at_utc' in frame else pd.Timestamp(manifest['created_at_utc']))
        require((starts > issued).all(), 'Pregame label after start')
    models = set(manifest['config']['models'])
    require(set(teams.model) == models and set(players.model) == models, 'Missing skater model')
    require(teams.groupby(['game_id','model']).size().eq(2).all(), 'Missing team/model')
    require(players.groupby(['game_id','player_id']).model.nunique().eq(len(models)).all(), 'Unequal model populations')
    expected_means = ['expected_'+c+'_if_plays' for c in
        ['goals','assists','shots','hits','points','pp_points','penalty_minutes','plus_minus','toi_minutes']]
    require(np.isfinite(players[expected_means]).all().all(), 'Missing/nonfinite player means')
    require(set(zip(coverage.game_id,coverage.team)) == set(zip(teams.game_id,teams.team)), 'Team coverage differs')
    lookup = teams.set_index(['game_id','team','model']).expected_shots
    for row in teams.itertuples():
        require(np.isclose(row.expected_shots_against, lookup.loc[(row.game_id,row.opponent,row.model)]), 'Team SF/opponent SA mismatch')
    require(np.allclose(goalies.shots_against_if_full_start,
                        goalies.saves_if_full_start+goalies.goals_against_if_full_start), 'Goalie SA != saves + GA')
    require(goalies.groupby(['game_id','player_id']).model.nunique().eq(2).all(), 'Missing goalie model')
    require(np.allclose(goalies.groupby(['game_id','team','model']).start_share_provisional.sum(),1), 'Goalie start shares do not sum to one')
    if manifest['availability_status'] == 'disabled_public_data_only':
        require(players.injury_status.eq('UNKNOWN').all() and goalies.injury_status.eq('UNKNOWN').all(), 'Public-mode availability mislabeled')
    return dict(date=manifest['date'], games=len(expected), player_rows=len(players),
                team_rows=len(teams), goalie_rows=len(goalies), availability=manifest['availability_status'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.bundle), indent=2))


if __name__ == '__main__':
    main()
