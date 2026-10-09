#!/usr/bin/env python3
"""Freeze an October 6–7 candidate before examining October 8 outcomes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.fantasy.game_calibration import fit_calibration, apply_calibration, shot_error_components
from src.fantasy.per_game import require


def main():
    review = Path('data/processed/forecasts/game_review_20261008T203106Z')
    baseline = Path('data/processed/forecasts/per_game_20262027_20261008T203040Z')
    source = review / 'frozen_forecast_vs_actual.csv'
    rows = pd.read_csv(source)
    dates = set(rows.loc[rows.appeared == True, 'game_date'])
    require(dates == {'2026-10-06', '2026-10-07'}, 'Calibration dates must remain frozen')
    factors = fit_calibration(rows, prior_expected_events=200)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = Path('data/processed/forecasts') / f'calibration_candidate_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    parts = shot_error_components(rows)
    parts.to_csv(out / 'shot_error_components.csv', index=False)
    diagnostics = []
    for name, frame in [('all_saved_pool', parts), ('saved_scoring_roster', parts[parts.pool == 'rostered'])]:
        diagnostics.append(dict(group=name, player_games=len(frame),
            total_shot_error=(frame.shots_if_plays-frame.shots).sum(),
            toi_component=frame.shot_error_toi_component.sum(),
            rate_residual=frame.shot_error_rate_residual.sum()))
    pd.DataFrame(diagnostics).to_csv(out / 'shot_error_summary.csv', index=False)
    config = dict(version='pooled_calibration_v1_experimental', calibration_dates=sorted(dates),
        factors=factors, prior_rationale='Fixed conservative 200 pseudo expected events anchored at ratio 1; not tuned.',
        untouched_categories=['goals','hits','penalty_minutes','pp_points','plus_minus','toi_minutes'],
        evaluation_date='2026-10-08', status='frozen_before_inspecting_october_8_results',
        limitations=['Six games share team/game context; 213 appearances are not independent games.',
                     'Corrections fit on October 6–7 are not out-of-sample improvements.',
                     'October 8 candidate is reconstructed retrospectively from saved pregame features, not issued pregame.',
                     'Multipliers calibrate marginal means; no coherent joint goals/shots distribution is fitted.'])
    Path('config/game_calibration_candidate.json').write_text(json.dumps(config, indent=2) + '\n')
    scheduled_file = baseline / 'today_skater_game_forecasts.csv'
    scheduled = pd.read_csv(scheduled_file)
    manifest = json.loads((baseline / 'manifest.json').read_text())
    require(hashlib.sha256(scheduled_file.read_bytes()).hexdigest() == manifest['files'][scheduled_file.name],
            'Frozen October 8 baseline hash mismatch')
    require((pd.to_datetime(scheduled.start_time_utc, utc=True).dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d') == '2026-10-08').all(),
            'Unexpected evaluation schedule date')
    apply_calibration(scheduled, factors).to_csv(out / 'october_8_candidate_conditional_forecasts.csv', index=False)
    # Deliberately never acquire or load October 8 actual outcomes here.
    (out / 'manifest.json').write_text(json.dumps(dict(config=config,
        created_at_utc=datetime.now(timezone.utc).isoformat(), calibration_source=str(source), baseline_source=str(baseline),
        calibration_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        baseline_sha256=hashlib.sha256(scheduled_file.read_bytes()).hexdigest(),
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}), indent=2)+'\n')
    print('Candidate output:', out)
    print(json.dumps(factors, indent=2))
    print(pd.DataFrame(diagnostics).to_string(index=False))


if __name__ == '__main__':
    main()
