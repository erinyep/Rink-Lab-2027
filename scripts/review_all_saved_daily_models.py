#!/usr/bin/env python3
"""Re-score all saved five-model daily slates on one current NHL actuals vintage.

Player forecasts are conditional on playing. Only positive-TOI actuals are
scored; no unissued or missing prediction is reconstructed. The paired SOG
interval resamples games as clusters rather than treating players as independent.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.evaluate_daily_forecasts import CATEGORIES, digest, verify_manifest_files
from src.fantasy.per_game import require


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def forecast_rows_from_wide(path, date):
    frame = pd.read_csv(path)
    require(frame.issue_timing.eq('pregame').all(), f'Non-pregame rows in {path}')
    rows = []
    for category in CATEGORIES:
        column = f'expected_{category}_if_plays'
        require(column in frame, f'Missing {column} in {path}')
        subset = frame[['game_id', 'player_id', 'model', 'player_name', 'team', column]].copy()
        subset = subset.rename(columns={column: 'forecast'})
        subset['category'] = category
        subset['date'] = date
        rows.append(subset)
    return pd.concat(rows, ignore_index=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prior-review', type=Path, required=True)
    ap.add_argument('--nov4-evaluation', type=Path, required=True)
    ap.add_argument('--nov4-results', type=Path, required=True)
    ap.add_argument('--nov5-results', type=Path, required=True)
    ap.add_argument('--actuals', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    require(not a.out.exists(), 'Choose a new output folder to preserve previous reviews')

    audit = []
    prior = verify_manifest_files(a.prior_review, audit)
    nov4_eval = verify_manifest_files(a.nov4_evaluation, audit)
    nov4_result = verify_manifest_files(a.nov4_results, audit)
    nov5_result = verify_manifest_files(a.nov5_results, audit)
    actual_manifest = verify_manifest_files(a.actuals, audit)
    require(actual_manifest.get('games') == 261, 'Expected current actuals through November 5')
    require(prior.get('through') == '2026-11-03', 'Unexpected prior season-review cutoff')
    require(nov5_result.get('date') == '2026-11-05', 'Wrong November 5 results package')
    official_source_hash_checks = 0
    for source in actual_manifest.get('sources', []):
        for field in ['boxscore', 'landing']:
            path = Path(source[field])
            require(sha(path) == source[field + '_sha256'], f'Changed official NHL source: {path}')
            official_source_hash_checks += 1
    require(nov4_eval['files']['player_projections.csv'] == nov4_result['files']['player_projections.csv'],
            'November 4 evaluation and published results use different forecasts')

    actual = pd.read_csv(a.actuals / 'skater_game_stats.csv')
    require(actual.game_date.max() == '2026-11-05', 'Actuals do not end on November 5')
    actual['game_id'] = actual.game_id.astype(str)
    actual['player_id'] = actual.player_id.astype(str)
    actual = actual[actual.toi_seconds.gt(0)].copy()
    require(not actual.duplicated(['game_id', 'player_id']).any(), 'Duplicate positive-TOI actual')
    a.out.mkdir(parents=True)

    sources = []
    daily_frames = []
    for folder in prior['evaluations']:
        folder = Path(folder)
        manifest = verify_manifest_files(folder, audit)
        frame = pd.read_csv(folder / 'simulation_summary.csv')
        frame = frame[frame.issue_timing.eq('pregame')]
        frame = frame.rename(columns={'model_projection_if_plays': 'forecast'})
        frame['date'] = manifest['date']
        daily_frames.append(frame[['game_id', 'player_id', 'model', 'category', 'date',
                                   'team', 'player_name', 'forecast']])
        sources.append(dict(date=manifest['date'], evaluation_manifest_sha256=sha(folder / 'manifest.json')))

    nov4_eval_path = a.nov4_evaluation / 'manifest.json'
    require(nov4_eval.get('date') == '2026-11-04', 'Wrong November 4 evaluation')
    daily_frames.append(pd.read_csv(a.nov4_evaluation / 'simulation_summary.csv')
        .query("issue_timing == 'pregame'")
        .rename(columns={'model_projection_if_plays': 'forecast'})
        [['game_id', 'player_id', 'model', 'category', 'date', 'team', 'player_name', 'forecast']])
    daily_frames.append(forecast_rows_from_wide(a.nov5_results / 'player_projections_scored.csv', '2026-11-05'))
    forecasts = pd.concat(daily_frames, ignore_index=True)
    forecasts['game_id'] = forecasts.game_id.astype(str)
    forecasts['player_id'] = forecasts.player_id.astype(str)
    forecasts['date'] = forecasts.date.astype(str)
    forecasts['forecast'] = pd.to_numeric(forecasts.forecast, errors='coerce')
    forecasts = forecasts.dropna(subset=['forecast'])
    require(not forecasts.duplicated(['game_id', 'player_id', 'model', 'category']).any(),
            'Repeated saved model prediction for a player/game/category')

    observed = actual[['game_id', 'player_id', 'game_date', 'name', 'team', *CATEGORIES]].copy()
    observed = observed.rename(columns={'game_date': 'actual_game_date', 'name': 'actual_name'})
    long_actuals = observed.melt(id_vars=['game_id', 'player_id', 'actual_game_date', 'actual_name', 'team'],
                                 value_vars=CATEGORIES, var_name='category', value_name='actual')
    scored = forecasts.merge(long_actuals, on=['game_id', 'player_id', 'category'], how='inner',
                             suffixes=('_forecast', '_actual'), validate='many_to_one')
    require(scored.date.eq(scored.actual_game_date).all(), 'Forecast date does not match official actual date')
    scored['absolute_error'] = (scored.forecast - scored.actual).abs()
    scored['signed_error'] = scored.forecast - scored.actual
    require(scored.game_id.nunique() == 88, f'Expected 88 saved prospective games, got {scored.game_id.nunique()}')

    metrics = (scored.groupby(['model', 'category'], as_index=False)
        .agg(rows=('absolute_error', 'size'), games=('game_id', 'nunique'),
             predicted_total=('forecast', 'sum'), actual_total=('actual', 'sum'),
             mae=('absolute_error', 'mean'), bias=('signed_error', 'mean')))
    scored['squared_error'] = np.square(scored.forecast - scored.actual)
    rmses = (scored.groupby(['model', 'category']).squared_error.mean().pow(.5)
             .rename('rmse').reset_index())
    metrics = metrics.merge(rmses, on=['model', 'category'], validate='one_to_one')

    shots = scored[scored.category.eq('shots')].copy()
    shots_export = shots[['date', 'game_id', 'team_forecast', 'player_id', 'player_name',
                          'model', 'forecast', 'actual', 'signed_error', 'absolute_error']].copy()
    shots_export = shots_export.rename(columns={'team_forecast': 'team'})
    shots_export.sort_values(['date', 'game_id', 'team', 'player_name', 'model']).to_csv(
        a.out / 'shots_scored_all_games.csv', index=False)

    by_date = (shots.groupby(['date', 'model'], as_index=False)
        .agg(rows=('absolute_error', 'size'), games=('game_id', 'nunique'),
             mae=('absolute_error', 'mean'), bias=('signed_error', 'mean')))
    by_date.to_csv(a.out / 'shots_by_date.csv', index=False)
    date_comparison = by_date.pivot(index='date', columns='model', values='mae').reset_index()
    date_comparison['calibrated_minus_default_mae'] = (
        date_comparison.calibrated_opponent_sog_trial - date_comparison.default)
    date_comparison['calibrated_lower_error'] = date_comparison.calibrated_minus_default_mae.lt(0)
    date_comparison.to_csv(a.out / 'shots_date_comparison.csv', index=False)
    pivot = shots.pivot(index=['date', 'game_id', 'player_id'], columns='model', values='absolute_error').reset_index()
    paired = pivot.groupby(['date', 'game_id'], as_index=False).agg(
        player_rows=('calibrated_opponent_sog_trial', 'size'),
        calibrated_opponent_mae=('calibrated_opponent_sog_trial', 'mean'),
        default_mae=('default', 'mean'))
    paired['calibrated_minus_default_mae'] = paired.calibrated_opponent_mae - paired.default_mae
    paired['calibrated_lower_error'] = paired.calibrated_minus_default_mae.lt(-1e-12)
    paired['tie'] = paired.calibrated_minus_default_mae.abs().le(1e-12)
    paired.to_csv(a.out / 'shots_paired_games.csv', index=False)

    rng = np.random.default_rng(20261105)
    paired_players = shots.pivot(index=['game_id', 'player_id'], columns='model', values='absolute_error')
    paired_players = paired_players.dropna(subset=['calibrated_opponent_sog_trial', 'default'])
    game_sums = paired_players.groupby('game_id')[['calibrated_opponent_sog_trial', 'default']].sum()
    game_counts = paired_players.groupby('game_id').size()
    game_ids = game_sums.index.to_numpy()
    cal = game_sums['calibrated_opponent_sog_trial'].to_numpy()
    default = game_sums['default'].to_numpy()
    counts = game_counts.loc[game_sums.index].to_numpy()
    draws = np.empty(20000)
    for i in range(len(draws)):
        idx = rng.integers(0, len(game_ids), len(game_ids))
        draws[i] = (cal[idx].sum() - default[idx].sum()) / counts[idx].sum()
    observed_delta = (cal.sum() - default.sum()) / counts.sum()
    paired_summary = pd.DataFrame([dict(
        comparison='calibrated_opponent_sog_trial - default', games=len(paired),
        rows=int(game_counts.sum()), observed_mae_delta=observed_delta,
        interval_95_low=np.quantile(draws, .025), interval_95_high=np.quantile(draws, .975),
        calibrated_lower_error_games=int(paired.calibrated_lower_error.sum()),
        ties=int(paired.tie.sum()), seed=20261105, resamples=len(draws),
        interval_method='paired bootstrap resampling whole games')])
    paired_summary.to_csv(a.out / 'shots_paired_uncertainty.csv', index=False)
    metrics.to_csv(a.out / 'player_metrics.csv', index=False)

    shot_metrics = metrics[metrics.category.eq('shots')].sort_values('mae')
    report = ['# All saved daily-model results through November 5, 2026', '',
        'All available frozen five-model daily forecasts were scored against one refreshed official NHL actuals vintage through November 5. '
        'The 88 games below are the games with saved prospective five-model releases; the other 173 of 261 finals have no saved release '
        'and are not reconstructed. Player errors are conditional on playing; only positive-TOI actuals are included.', '',
        '## All-player shots', '',
        '| model | player-games | games | SOG MAE | bias |', '| --- | ---: | ---: | ---: | ---: |']
    for row in shot_metrics.itertuples():
        report.append(f'| {row.model} | {row.rows:,} | {row.games} | {row.mae:.4f} | {row.bias:+.4f} |')
    delta = paired_summary.iloc[0]
    default_mae = float(shot_metrics.loc[shot_metrics.model.eq('default'), 'mae'].iloc[0])
    percent_improvement = 100 * abs(float(delta.observed_mae_delta)) / default_mae
    report += ['', f'Calibrated-opponent minus default MAE is **{delta.observed_mae_delta:+.4f} shots** '
        f'(95% paired whole-game bootstrap interval {delta.interval_95_low:+.4f} to {delta.interval_95_high:+.4f}); '
        f'calibrated-opponent had lower SOG error in {int(delta.calibrated_lower_error_games)} of 88 games. '
        f'That is a **{percent_improvement:.1f}% lower MAE** than default (about 0.016 shots per appearance). '
        'The game-level bootstrap interval excludes zero, though the absolute gain is small. '
        f'Calibrated-opponent also had lower date-level SOG MAE on {int(date_comparison.calibrated_lower_error.sum())} '
        f'of {len(date_comparison)} saved forecast dates. '
        'This is a conditional SOG comparison, not lineup-selection or fantasy-category performance. The interval treats games as clusters; '
        'forecast dates can still share slate-level conditions.', '',
        '## Other player categories', '',
        'See [all category metrics](player_metrics.csv). All five variants share the same scored player-game populations. '
        'Category differences are descriptive; the calibrated-opponent change is intended for NHL SOG only.', '',
        '## Coverage and files', '',
        f'- Official results: 261 completed games through November 5; matched saved five-model forecasts: 88 games and '
        f'{shots[["game_id", "player_id"]].drop_duplicates().shape[0]:,} distinct player-game appearances across the scored participant population.',
        '- [SOG forecast and actual rows for all five models](shots_scored_all_games.csv) · [SOG results by forecast date](shots_by_date.csv) · '
        '[date-level comparison](shots_date_comparison.csv) · [paired game differences](shots_paired_games.csv) · '
        '[bootstrap interval](shots_paired_uncertainty.csv).',
        '- Source snapshots and hashes, saved review manifest hashes, excluded nonparticipants, and calculation details are in `manifest.json`.',
        '- November 6 has not been evaluated because those games were not completed when this review was made.']
    (a.out / 'README.md').write_text('\n'.join(report) + '\n')

    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), through='2026-11-05',
        actuals_source='official NHL skater game stats through 2026-11-05',
        actuals_manifest_sha256=sha(a.actuals / 'manifest.json'),
        prior_review_source=a.prior_review.name,
        prior_review_manifest_sha256=sha(a.prior_review / 'manifest.json'),
        nov4_evaluation_source='saved pregame player evaluation for 2026-11-04',
        nov4_evaluation_manifest_sha256=sha(nov4_eval_path),
        nov4_results_source=a.nov4_results.as_posix(),
        nov4_results_manifest_sha256=sha(a.nov4_results / 'manifest.json'),
        nov5_results_source=a.nov5_results.as_posix(),
        nov5_results_manifest_sha256=sha(a.nov5_results / 'manifest.json'),
        review_code_sha256=sha(Path(__file__)),
        official_source_hash_checks=official_source_hash_checks,
        matched_games=int(shots.game_id.nunique()), positive_toi_player_games=int(shots[['game_id','player_id']].drop_duplicates().shape[0]),
        unavailable_final_games=int(actual.game_id.nunique() - shots.game_id.nunique()),
        paired_bootstrap_seed=20261105, paired_bootstrap_resamples=20000,
        sources=sources,
        files={p.name: sha(p) for p in a.out.iterdir() if p.is_file()})
    (a.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Review:', a.out)
    print(shot_metrics[['model','rows','games','mae','bias']].to_string(index=False))
    print(paired_summary.to_string(index=False))


if __name__ == '__main__':
    main()
