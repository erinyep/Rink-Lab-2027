#!/usr/bin/env python3
"""Export hash-verified daily projections without private fantasy ownership."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_daily_bundle import validate


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--out-root', type=Path, default=Path('outputs/per_game_forecast/frozen'))
    args = parser.parse_args()
    bundle = args.bundle
    validation = validate(bundle)
    source = json.loads((bundle / 'manifest.json').read_text())
    if not source.get('finalized_at_utc') or not source.get('release_validation'):
        raise ValueError('Only finalized and release-validated bundles can be exported')
    release = source['release_validation']

    stamp = bundle.name.rsplit('_', 1)[-1]
    out = args.out_root / f"daily_{source['date']}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    private_fields = {'fantasy_team_name', 'fantasy_team_id', 'espn_player_id'}
    source_files = {}
    rows = {}
    for name in ['player_projections.csv', 'team_projections.csv', 'goalie_projections.csv', 'game_team_coverage.csv']:
        frame = pd.read_csv(bundle / name)
        source_files[name] = sha(bundle / name)
        frame = frame.drop(columns=[c for c in private_fields if c in frame], errors='ignore')
        frame.to_csv(out / name, index=False)
        rows[name] = len(frame)

    model_config = json.loads((ROOT / 'config/daily_forecast_trial.json').read_text())
    raw_schedule = Path(source['raw_context']) / 'schedule.json'
    schedule = json.loads(raw_schedule.read_text())
    games = [g for day in schedule['gameWeek'] if day['date'] == source['date']
             for g in day['games'] if g['season'] == 20262027 and g['gameType'] == 2]
    late_ids = set()
    for filename in ['player_projections.csv', 'team_projections.csv', 'goalie_projections.csv']:
        late_ids.update(pd.read_csv(bundle / filename).loc[
            lambda f: f.issue_timing.eq('late_not_pregame'), 'game_id'].unique())
    late_games = [dict(game_id=g['id'], away=g['awayTeam']['abbrev'], home=g['homeTeam']['abbrev'])
                  for g in games if g['id'] in late_ids]
    late_matchups = ', '.join(f"{g['away']} at {g['home']}" for g in late_games) or 'none'
    mp = json.loads((Path(source['moneypuck_snapshot']) / 'metadata.json').read_text())
    boxscores = json.loads((Path(source['boxscore_history']) / 'metadata.json').read_text())
    mp_last = mp['latest_game_date_by_season'].get('2026') or mp['latest_game_date_by_season'].get(2026)
    if mp_last:
        mp_last = str(mp_last)
        mp_last = f'{mp_last[:4]}-{mp_last[4:6]}-{mp_last[6:8]}'
    guide = f"""# Frozen daily projections — {source['date']}

Issued {source['created_at_utc']}. Official statistical history ends {source['statistical_history_last_game_date']} ({boxscores['final_games']} completed games). The slate contains {release['pregame_games']} pregame game forecasts and {release['late_games']} late-issued game scenario(s).

Start with `player_projections.csv`, `team_projections.csv`, and `goalie_projections.csv`. Player means are conditional on playing; assumed lineups and goalie start shares are not confirmed. The calibrated-opponent SOG model is selected for all-player NHL shots; fantasy category policy remains separate. Alternative rows are preserved for comparison.

Late-issued scenario(s), excluded from prospective scoring: {late_matchups}.

Availability comes from a timestamped ESPN snapshot and does not confirm participation. MoneyPuck team-game data covered through {mp_last}; this is lagged relative to the NHL history cutoff. That context lag was accepted explicitly and is recorded in the release validation. The complete local issue bundle contains private fantasy ownership and API context; this export omits fantasy team names and ESPN player IDs.
"""
    (out / 'README.md').write_text(guide)
    manifest = dict(
        date=source['date'],
        released_at_utc=source['finalized_at_utc'],
        statistical_history_last_game_date=source['statistical_history_last_game_date'],
        games=validation['games'],
        pregame_games=release['pregame_games'],
        late_games=late_games,
        models=source['config']['models'],
        primary_sog_model=model_config['primary_sog_model'],
        availability=source.get('availability_status'),
        injuries_as_of_utc=source.get('injuries_as_of_utc'),
        moneypuck_latest_game_date=mp_last,
        moneypuck_retrieved_at_utc=mp.get('retrieved_at_utc'),
        moneypuck_context_lag_explicitly_accepted=source['release_validation']['context_lag_explicitly_accepted'],
        source_bundle_manifest_sha256=sha(bundle / 'manifest.json'),
        source_files_sha256=source_files,
        privacy_note='Public projection files omit fantasy-team names and ESPN player IDs. Raw snapshots, credentials and league ownership remain local.',
        rows=rows,
        files={p.name: sha(p) for p in out.iterdir() if p.is_file() and p.name != 'manifest.json'},
    )
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Public frozen release:', out)
    print('Games:', validation['games'], 'Pregame:', release['pregame_games'], 'Late:', release['late_games'])
    print('Player rows:', rows['player_projections.csv'], 'Team rows:', rows['team_projections.csv'],
          'Goalie rows:', rows['goalie_projections.csv'])


if __name__ == '__main__':
    main()
