#!/usr/bin/env python3
"""Apply a previously frozen feature experiment to a new, strictly pregame slate."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.evaluate_daily_forecasts import verify_manifest_files, digest
from scripts.publish_feature_evidence import accounting
from src.fantasy.feature_screen import lagged_team_rows, apply_residual
from src.fantasy.per_game import require


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ['bundle', 'evidence', 'actuals', 'pbp', 'quality', 'out']:
        ap.add_argument('--' + key, type=Path, required=True)
    a = ap.parse_args()
    require(not a.out.exists(), 'Preserve previous releases')
    manifests = {key: verify_manifest_files(getattr(a, key), [])
                 for key in ['bundle', 'evidence', 'actuals', 'pbp', 'quality']}
    target = manifests['bundle']['date']
    require(target > manifests['evidence']['target_date'], 'Require a later prospective slate')
    team = pd.read_csv(a.bundle / 'team_projections.csv')
    team = team[team.model.eq('default')]
    actual = pd.read_csv(a.actuals / 'skater_game_stats.csv')
    require(actual.game_date.lt(target).all(), 'Target-day outcomes in inputs')
    require(not actual.duplicated(['game_id', 'player_id']).any(), 'Duplicate actuals')
    history = actual[actual.toi_seconds.gt(0)].groupby(['game_id', 'game_date', 'team']).shots.sum().reset_index()
    require(history.groupby('game_id').size().eq(2).all(), 'Incomplete team pairs')
    opponents = history[['game_id', 'team', 'shots']].rename(columns={'team': 'opponent', 'shots': 'shots_against'})
    history = history.merge(opponents, on='game_id')
    history = history[history.team.ne(history.opponent)]
    fixtures = team[['game_id', 'team', 'opponent']].assign(game_date=target)
    features = lagged_team_rows(history, fixtures,
        pd.read_csv(a.pbp / 'defense_team_games.csv'), pd.read_csv(a.pbp / 'source_audit.csv'),
        pd.read_csv(a.quality / 'defense_shot_quality_team_games.csv'),
        manifests['evidence']['config']['team_prior_games'])
    features = features.merge(team[['game_id', 'team', 'start_time_utc']], on=['game_id', 'team'], validate='one_to_one')
    models = json.loads((a.evidence / 'fitted_models.json').read_text())['tonight_refit']
    now = datetime.now(timezone.utc)
    require((pd.to_datetime(features.start_time_utc, utc=True) > pd.Timestamp(now) + pd.Timedelta(minutes=10)).all(), 'Too late to issue')
    rows = []
    for name, model in models.items():
        pred, effects = apply_residual(features, model)
        z = features.assign(model=name, experimental_team_sog=pred,
            intercept_contribution=model['intercept'], issued_at_utc=now.isoformat(),
            status='separate_research_trial_not_used_by_main_forecasts')
        for column in effects:
            z[column + '_contribution'] = effects[column]
        rows.append(z)
    player, _ = accounting(a.bundle)
    a.out.mkdir(parents=True)
    pd.concat(rows).to_csv(a.out / 'tonight_experimental_team_forecasts.csv', index=False)
    player.to_csv(a.out / 'player_contributions.csv', index=False)
    (a.out / 'fitted_models.json').write_text(json.dumps({'tonight_refit': models}, indent=2) + '\n')
    (a.out / 'README.md').write_text(f'''# Frozen feature experiment — {target}

{len(team)//2} games, four variants: bias control, defense, shot quality and both.
Issued {now.isoformat()}. Uses the exact October 20 fitted parameters with fresh
past-only inputs through {actual.game_date.max()}; no refit, tuning or model promotion.
Source disagreements retain their existing quarantines and training-time imputation.

[Frozen predictions](tonight_experimental_team_forecasts.csv) · [Player SOG accounting](player_contributions.csv).
These separate team-volume experiments do not change the main five models.
Player contributions are ordered changes in the usage trial, not causal importance.
Completed feature evaluations are reported separately in the latest model review;
this release does not fix the historical evidence count to its original issue date.

Score after finals using `scripts/evaluate_feature_evidence.py`; preserve this release.
''')
    table = pd.concat(rows)[['game_id', 'team', 'opponent', 'model', 'experimental_team_sog']].round(3).to_html(index=False)
    (a.out / 'index.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Feature trials — {target}</title><style>body{{font:16px system-ui;margin:24px;color:#172c38}}main{{overflow:auto}}td,th{{padding:8px;text-align:left}}p{{max-width:900px}}</style><h1>Feature trials — {target}</h1><p><a href="../games/">Matchups</a> · <a href="../report/">Fantasy</a> · <a href="../results/">Completed model results</a> · <a href="../archive/2026-10-20/evidence/">Original feature research</a></p><p>Four frozen variants on {len(team)//2} new games. Exact October 20 coefficients; fresh past-only context. No refit or promotion. Predictions remain separate from the main models.</p><p><a href="README.md">Method and limits</a> · <a href="tonight_experimental_team_forecasts.csv">Forecast CSV</a> · <a href="player_contributions.csv">Player contributions CSV</a></p><main>{table}</main></html>''')
    manifest = dict(created_at_utc=now.isoformat(), target_date=target, config=manifests['evidence']['config'],
        status='frozen_parameters_new_prospective_slate',
        source_manifests={str(getattr(a, key) / 'manifest.json'): digest(getattr(a, key) / 'manifest.json') for key in manifests},
        files={p.name: digest(p) for p in a.out.iterdir() if p.is_file()})
    (a.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Frozen feature release:', a.out)


if __name__ == '__main__':
    main()
