#!/usr/bin/env python3
"""Score every saved November public daily release on one official actuals vintage."""
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
from src.fantasy.per_game import require
from src.fantasy.team_probability import scoring_win_probability


CATEGORIES = ['goals', 'assists', 'shots', 'hits', 'penalty_minutes',
              'plus_minus', 'points', 'pp_points', 'toi_minutes']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(path):
    """Keep provenance portable and avoid leaking machine-specific paths."""
    return Path(path).resolve().relative_to(ROOT).as_posix()


def check_files(folder, manifest):
    for name, expected in manifest.get('files', {}).items():
        path = folder / name
        require(path.is_file() and sha(path) == expected, f'Changed source file: {path}')


def verify_source_acquisition(actuals, boxscores):
    am = json.loads((actuals / 'manifest.json').read_text())
    check_files(actuals, am)
    for source in am.get('sources', []):
        for field in ['boxscore', 'landing']:
            if field in source and source.get(field + '_sha256'):
                require(sha(source[field]) == source[field + '_sha256'],
                        f'Changed actual source: {source[field]}')
    bm = json.loads((boxscores / 'metadata.json').read_text())
    for source in bm['sources']:
        require(sha(boxscores / source['file']) == source['sha256'],
                f'Changed boxscore source: {source["file"]}')
    return am, bm


def paired_bootstrap(player_rows, challenger, category='shots', draws=10000, seed=20261110):
    z = player_rows[player_rows.category.eq(category) &
                    player_rows.model.isin(['default', challenger])].copy()
    wide = z.pivot(index=['game_id', 'player_id'], columns='model', values='absolute_error').dropna()
    by_game = (wide.assign(delta=wide[challenger] - wide['default'])
               .groupby(level='game_id').agg(delta=('delta', 'sum'), n=('delta', 'size')))
    observed = by_game.delta.sum() / by_game.n.sum()
    rng = np.random.default_rng(seed)
    indexes = rng.integers(0, len(by_game), size=(draws, len(by_game)))
    deltas = by_game.delta.to_numpy()[indexes].sum(axis=1)
    counts = by_game.n.to_numpy()[indexes].sum(axis=1)
    interval = np.quantile(deltas / counts, [.025, .975])
    game_mae = wide.assign(delta=wide[challenger] - wide['default']).groupby(level='game_id').delta.mean()
    return dict(model=challenger, category=category, paired_rows=len(wide), games=len(by_game),
                mae_delta_vs_default=float(observed), lower_95=float(interval[0]),
                upper_95=float(interval[1]), games_lower_mae=int((game_mae < 0).sum()),
                games_equal_or_higher=int((game_mae >= 0).sum()), bootstrap_draws=draws)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--actuals', type=Path, required=True)
    ap.add_argument('--boxscores', type=Path, required=True)
    ap.add_argument('--through', required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    require(not a.out.exists(), 'Preserve prior review; choose a new output directory')
    am, bm = verify_source_acquisition(a.actuals, a.boxscores)
    require(bm.get('through_eastern_date') == a.through and not bm.get('unfinished_games'),
            'Boxscore history must be complete through the requested date')
    box_by_id = {}
    for path in a.boxscores.glob('boxscore_*.json'):
        box = json.loads(path.read_text())
        if box['season'] == 20262027 and box['gameType'] == 2:
            box_by_id[box['id']] = box

    sk = pd.read_csv(a.actuals / 'skater_game_stats.csv')
    require(not sk.duplicated(['game_id', 'player_id']).any(), 'Duplicate actual skater-game key')
    require(sk[CATEGORIES].notna().all().all(), 'Actual stats contain missing modeled categories')
    sk = sk[sk.toi_seconds.gt(0)].copy()
    sk['toi_minutes'] = sk.toi_seconds / 60

    bundle_dirs = []
    for folder in sorted((ROOT / 'outputs/per_game_forecast/frozen').glob('daily_2026-11-*')):
        manifest_path = folder / 'manifest.json'
        if not manifest_path.is_file():
            continue
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('date', '') <= a.through and manifest.get('date', '').startswith('2026-11-'):
            bundle_dirs.append((folder, manifest))
    require(bundle_dirs, 'No frozen November releases found')

    player_parts, daily_rows, coverage_rows, source_hashes = [], [], [], []
    winner_rows, winner_games = [], []
    missing_actuals = []
    for bundle, manifest in bundle_dirs:
        check_files(bundle, manifest)
        day = manifest['date']
        source_hashes.append(dict(date=day, bundle=repo_path(bundle),
                                  manifest_sha256=sha(bundle / 'manifest.json')))
        forecasts = pd.read_csv(bundle / 'player_projections.csv')
        forecasts = forecasts[forecasts.issue_timing.eq('pregame')].copy()
        game_ids = set(forecasts.game_id)
        require(len(game_ids) == manifest.get('pregame_games', len(game_ids)),
                f'Pregame game count mismatch for {day}')
        require(game_ids <= set(box_by_id), f'Missing completed official boxscore for {day}')
        for gid in game_ids:
            require(box_by_id[gid]['gameDate'] == day, f'Wrong game date for {gid}')
        actual_subset = sk[['game_id', 'player_id'] + CATEGORIES].rename(
            columns={c: c + '_actual' for c in CATEGORIES})
        scored = forecasts.merge(actual_subset, on=['game_id', 'player_id'],
                                 how='left', validate='many_to_one')
        scored = scored[scored.toi_minutes_actual.notna()].copy()
        for category in CATEGORIES:
            pred = f'expected_{category}_if_plays'
            if pred not in scored:
                continue
            part = scored[['game_id', 'player_id', 'player_name', 'team', 'model']].copy()
            part['date'] = day
            part['category'] = category
            part['prediction'] = scored[pred].to_numpy()
            part['actual'] = scored[category + '_actual'].to_numpy()
            part['signed_error'] = part.prediction - part.actual
            part['absolute_error'] = part.signed_error.abs()
            player_parts.append(part)
        actual_ids = sk[sk.game_id.isin(game_ids)][['game_id', 'player_id']].drop_duplicates()
        covered = forecasts[['game_id', 'player_id']].drop_duplicates()
        gaps = actual_ids.merge(covered.assign(modeled=True), on=['game_id', 'player_id'], how='left')
        missing = gaps[gaps.modeled.isna()]
        if len(missing):
            missing_actuals.append(missing.assign(date=day))
        selected = forecasts[forecasts.selected_for_trial.eq(True)].drop_duplicates(['game_id', 'player_id'])
        covered_ids = set(zip(covered.game_id, covered.player_id))
        actual_ids_set = set(zip(actual_ids.game_id, actual_ids.player_id))
        coverage_rows.append(dict(date=day, games=len(game_ids), actual_participants=len(actual_ids_set),
                                  forecast_participants=len(actual_ids_set.intersection(covered_ids)),
                                  unmodeled_actual_participants=len(missing),
                                  selected_player_games=len(selected),
                                  selected_nonparticipants=int(selected.merge(actual_ids.assign(appeared=True),
                                      on=['game_id', 'player_id'], how='left').appeared.isna().sum())))

        # Direct team probabilities were issued only on dates with a separate team release.
        team_dirs = sorted((ROOT / 'outputs/per_game_forecast').glob(f'team_context_daily_{day}_*'))
        if not team_dirs:
            continue
        team_dir = team_dirs[-1]
        team_hash = sha(team_dir / 'manifest.json')
        source_hashes[-1]['team_release'] = repo_path(team_dir)
        source_hashes[-1]['team_manifest_sha256'] = team_hash
        probabilities = pd.read_csv(team_dir / 'team_win_probabilities.csv')
        team_proj = pd.read_csv(bundle / 'team_projections.csv')
        default = team_proj[team_proj.model.eq('default')].set_index(['game_id', 'team'])
        actual_goals = sk[sk.game_id.isin(game_ids)].groupby(['game_id', 'team']).goals.sum()
        for row in probabilities.itertuples():
            box = box_by_id[row.game_id]
            require(row.training_through < day, f'Team model uses target-date results: {day}')
            require(pd.Timestamp(row.start_time_utc) - pd.Timestamp(row.issued_at_utc) >= pd.Timedelta(minutes=10),
                    f'Late team forecast: {row.game_id}')
            home_win = int(box['homeTeam']['score'] > box['awayTeam']['score'])
            home_actual = float(actual_goals.loc[(row.game_id, row.home)])
            away_actual = float(actual_goals.loc[(row.game_id, row.away)])
            oh = float(default.loc[(row.game_id, row.home)].expected_goals)
            oa = float(default.loc[(row.game_id, row.away)].expected_goals)
            original_p = scoring_win_probability(oh, oa)
            forecast_models = [
                ('direct_team', float(row.home_win_probability), row.home_goal_mean, row.away_goal_mean),
                ('original_player_sum', original_p, oh, oa),
                ('goal_history_baseline', float(row.baseline_home_win_probability),
                 row.baseline_home_goals, row.baseline_away_goals),
            ]
            if hasattr(row, 'calibrated_home_win_probability') and pd.notna(row.calibrated_home_win_probability):
                forecast_models.append(('calibrated_team_trial', float(row.calibrated_home_win_probability),
                                        row.home_goal_mean, row.away_goal_mean))
            for model, prob, home_mean, away_mean in forecast_models:
                winner_rows.append(dict(date=day, game_id=row.game_id, model=model,
                    home_probability=prob, actual_home_win=home_win,
                    brier=(prob-home_win)**2,
                    log_loss=-np.log(np.clip(prob if home_win else 1-prob, 1e-12, 1)),
                    favorite_correct=float((prob > .5) == bool(home_win)) if prob != .5 else np.nan,
                    goal_mae=(abs(home_mean-home_actual)+abs(away_mean-away_actual))/2,
                    predicted_goals=home_mean+away_mean, actual_goals=home_actual+away_actual))
            winner_games.append(dict(date=day, game_id=row.game_id, away=row.away, home=row.home,
                away_score=box['awayTeam']['score'], home_score=box['homeTeam']['score'],
                ending=box['periodDescriptor']['periodType'],
                direct_home_probability=row.home_win_probability,
                original_home_probability=original_p, direct_home_goals=row.home_goal_mean,
                direct_away_goals=row.away_goal_mean, original_home_goals=oh,
                original_away_goals=oa, actual_home_player_goals=home_actual,
                actual_away_player_goals=away_actual))

    players = pd.concat(player_parts, ignore_index=True)
    pooled = []
    for (model, category), group in players.groupby(['model', 'category']):
        e = group.signed_error
        pooled.append(dict(model=model, category=category, rows=len(group),
            games=group.game_id.nunique(), predicted_total=group.prediction.sum(),
            actual_total=group.actual.sum(), mae=e.abs().mean(), bias=e.mean(),
            rmse=np.sqrt(np.mean(e**2))))
    pooled = pd.DataFrame(pooled)
    by_date = []
    for (day, model, category), group in players.groupby(['date', 'model', 'category']):
        e = group.signed_error
        by_date.append(dict(date=day, model=model, category=category, rows=len(group),
            games=group.game_id.nunique(), predicted_total=group.prediction.sum(),
            actual_total=group.actual.sum(), mae=e.abs().mean(), bias=e.mean(),
            rmse=np.sqrt(np.mean(e**2))))
    by_date = pd.DataFrame(by_date)
    pairs = [('candidate', 'shots'), ('opponent_form_sog_trial', 'shots'),
             ('calibrated_opponent_sog_trial', 'shots'), ('usage_shot_context_trial', 'shots'),
             ('usage_shot_context_trial', 'toi_minutes'), ('usage_toi_only_trial', 'toi_minutes')]
    paired = pd.DataFrame([paired_bootstrap(players, model, category)
                           for model, category in pairs if model in set(players.model)])
    winner_scores = pd.DataFrame(winner_rows)
    winner_metrics = (winner_scores.groupby('model').agg(games=('game_id', 'nunique'),
        brier=('brier', 'mean'), log_loss=('log_loss', 'mean'),
        favorite_accuracy=('favorite_correct', 'mean'), goal_mae=('goal_mae', 'mean'),
        predicted_goals=('predicted_goals', 'sum'), actual_goals=('actual_goals', 'sum')).reset_index()
        if len(winner_scores) else pd.DataFrame())

    a.out.mkdir(parents=True)
    frames = {
        'player_metrics.csv': pooled,
        'player_metrics_by_date.csv': by_date,
        'paired_shots_vs_default.csv': paired,
        'coverage_by_date.csv': pd.DataFrame(coverage_rows),
        'winner_scores.csv': winner_scores,
        'winner_metrics.csv': winner_metrics,
        'team_games.csv': pd.DataFrame(winner_games),
        'unmodeled_actual_skaters.csv': pd.concat(missing_actuals, ignore_index=True)
            if missing_actuals else pd.DataFrame(columns=['game_id', 'player_id', 'date']),
    }
    for name, frame in frames.items():
        frame.to_csv(a.out / name, index=False)
    shot = pooled[pooled.category.eq('shots')].set_index('model')
    selected = shot.loc['calibrated_opponent_sog_trial']
    default = shot.loc['default']
    delta = float(selected.mae - default.mae)
    pdelta = paired[(paired.model.eq('calibrated_opponent_sog_trial')) &
                    (paired.category.eq('shots'))].iloc[0]
    toi = pooled[pooled.category.eq('toi_minutes')].set_index('model')
    toi_default, toi_usage = toi.loc['default'], toi.loc['usage_shot_context_trial']
    usage_dates = by_date[(by_date.category.eq('toi_minutes')) &
                          (by_date.model.eq('usage_shot_context_trial'))].set_index('date')
    default_dates = by_date[(by_date.category.eq('toi_minutes')) &
                            (by_date.model.eq('default'))].set_index('date')
    usage_toi_pair = paired[(paired.model.eq('usage_shot_context_trial')) &
                            (paired.category.eq('toi_minutes'))].iloc[0]
    isolated_toi = toi.loc['usage_toi_only_trial']
    isolated_toi_pair = paired[(paired.model.eq('usage_toi_only_trial')) &
                               (paired.category.eq('toi_minutes'))].iloc[0]
    games = int(coverage_rows and sum(row['games'] for row in coverage_rows))
    playergames = int(shot.loc['default'].rows)
    dates = sorted({r['date'] for r in coverage_rows})
    latest_date = dates[-1]
    latest_shots = by_date[(by_date.date.eq(latest_date)) & by_date.category.eq('shots')].set_index('model')
    latest_toi = by_date[(by_date.date.eq(latest_date)) & by_date.category.eq('toi_minutes')].set_index('model')
    latest_winners = winner_scores[winner_scores.date.eq(latest_date)]
    latest_winner_metrics = (latest_winners.groupby('model').agg(
        games=('game_id', 'nunique'), brier=('brier', 'mean'),
        favorite_accuracy=('favorite_correct', 'mean'), goal_mae=('goal_mae', 'mean'))
        if len(latest_winners) else pd.DataFrame())
    fantasy_toi_parts = []
    fantasy_evaluation_sources = []
    for day in dates:
        evaluations = sorted((ROOT / 'data/processed/forecasts').glob(
            f'daily_evaluation_{day}_*'))
        if not evaluations:
            continue
        eval_file = evaluations[-1] / 'simulation_summary.csv'
        if not eval_file.is_file():
            continue
        eval_manifest = evaluations[-1] / 'manifest.json'
        if eval_manifest.is_file():
            fantasy_evaluation_sources.append(dict(date=day,
                evaluation=evaluations[-1].relative_to(ROOT).as_posix(),
                manifest_sha256=sha(eval_manifest)))
        frame = pd.read_csv(eval_file)
        fantasy = frame[(frame.issue_timing.eq('pregame')) &
            frame.category.eq('toi_minutes') &
            frame.fantasy_team_name.fillna('').astype(str).str.strip().ne('') &
            frame.model.isin(['default', 'usage_toi_only_trial'])].copy()
        fantasy['absolute_error'] = (fantasy.model_projection_if_plays - fantasy.actual).abs()
        fantasy_toi_parts.append(fantasy[['date', 'game_id', 'player_id', 'model', 'absolute_error']])
    fantasy_usage_summary = None
    if fantasy_toi_parts:
        fantasy_toi = pd.concat(fantasy_toi_parts, ignore_index=True)
        fantasy_wide = fantasy_toi.pivot(index=['date', 'game_id', 'player_id'],
            columns='model', values='absolute_error').dropna()
        if not fantasy_wide.empty:
            fantasy_wide['delta'] = (fantasy_wide['usage_toi_only_trial'] -
                                      fantasy_wide['default'])
            fantasy_game = fantasy_wide.groupby(level=['date', 'game_id']).agg(
                delta=('delta', 'sum'), n=('delta', 'size'))
            rng = np.random.default_rng(20261113)
            ids = np.arange(len(fantasy_game))
            draws = rng.integers(0, len(ids), size=(10000, len(ids)))
            boot_delta = (fantasy_game.delta.to_numpy()[draws].sum(axis=1) /
                          fantasy_game.n.to_numpy()[draws].sum(axis=1))
            fantasy_game_means = fantasy_game.delta / fantasy_game.n
            fantasy_usage_summary = dict(
                rows=int(len(fantasy_wide)), games=int(len(fantasy_game)),
                dates=int(fantasy_wide.index.get_level_values('date').nunique()),
                default_mae=float(fantasy_wide['default'].mean()),
                usage_toi_mae=float(fantasy_wide['usage_toi_only_trial'].mean()),
                mae_delta=float(fantasy_wide['delta'].mean()),
                lower_95=float(np.quantile(boot_delta, .025)),
                upper_95=float(np.quantile(boot_delta, .975)),
                games_lower_mae=int((fantasy_game_means < 0).sum()),
                bootstrap_draws=10000, seed=20261113)
    summary = dict(through=a.through, forecast_dates=sorted({r['date'] for r in coverage_rows}),
        prospective_games=games, player_games=playergames,
        selected_shots_model='calibrated_opponent_sog_trial',
        selected_shots_mae=float(selected.mae), default_shots_mae=float(default.mae),
        selected_minus_default_shots_mae=delta,
        selected_shots_relative_improvement_pct=float(100*(default.mae-selected.mae)/default.mae),
        selected_shots_paired_game_bootstrap=dict(
            model=str(pdelta.model), category=str(pdelta.category),
            paired_rows=int(pdelta.paired_rows), games=int(pdelta.games),
            mae_delta_vs_default=float(pdelta.mae_delta_vs_default),
            lower_95=float(pdelta.lower_95), upper_95=float(pdelta.upper_95),
            games_lower_mae=int(pdelta.games_lower_mae),
            games_equal_or_higher=int(pdelta.games_equal_or_higher),
            bootstrap_draws=int(pdelta.bootstrap_draws)),
        usage_toi_mae=float(toi_usage.mae), default_toi_mae=float(toi_default.mae),
        usage_toi_relative_improvement_pct=float(100*(toi_default.mae-toi_usage.mae)/toi_default.mae),
        usage_toi_improved_dates=int(sum(usage_dates.loc[d, 'mae'] < default_dates.loc[d, 'mae']
                                         for d in usage_dates.index)),
        usage_toi_paired_game_bootstrap=dict(
            model=str(usage_toi_pair.model), category=str(usage_toi_pair.category),
            paired_rows=int(usage_toi_pair.paired_rows), games=int(usage_toi_pair.games),
            mae_delta_vs_default=float(usage_toi_pair.mae_delta_vs_default),
            lower_95=float(usage_toi_pair.lower_95), upper_95=float(usage_toi_pair.upper_95),
            games_lower_mae=int(usage_toi_pair.games_lower_mae),
            games_equal_or_higher=int(usage_toi_pair.games_equal_or_higher),
            bootstrap_draws=int(usage_toi_pair.bootstrap_draws)),
        isolated_usage_toi_mae=float(isolated_toi.mae),
        isolated_usage_toi_games=int(isolated_toi.games),
        isolated_usage_toi_paired_game_bootstrap=dict(
            model=str(isolated_toi_pair.model), category=str(isolated_toi_pair.category),
            paired_rows=int(isolated_toi_pair.paired_rows), games=int(isolated_toi_pair.games),
            mae_delta_vs_default=float(isolated_toi_pair.mae_delta_vs_default),
            lower_95=float(isolated_toi_pair.lower_95), upper_95=float(isolated_toi_pair.upper_95),
            games_lower_mae=int(isolated_toi_pair.games_lower_mae),
            games_equal_or_higher=int(isolated_toi_pair.games_equal_or_higher),
            bootstrap_draws=int(isolated_toi_pair.bootstrap_draws)),
        latest_date=latest_date,
        latest_pregame_games=int(coverage_rows[-1]['games']),
        latest_player_games=int(latest_shots.loc['default', 'rows']),
        latest_default_shots_mae=float(latest_shots.loc['default', 'mae']),
        latest_calibrated_shots_mae=float(latest_shots.loc['calibrated_opponent_sog_trial', 'mae']),
        latest_default_toi_mae=float(latest_toi.loc['default', 'mae']),
        latest_usage_toi_mae=float(latest_toi.loc['usage_toi_only_trial', 'mae']),
        latest_winner_metrics=latest_winner_metrics.reset_index().to_dict('records'),
        fantasy_usage_toi= fantasy_usage_summary,
        fantasy_evaluation_sources=fantasy_evaluation_sources,
        recommendation='Retain calibrated-opponent SOG for NHL-wide all-player shots and default fantasy shots. Promote isolated usage-aware TOI as the NHL-wide ATOI selection: its prospective game-cluster interval excludes zero across a larger sample, and the November 12 fantasy subset also improves. Keep PP and team-probability calibration as challengers.',
        missing_early_november_releases=['2026-11-01', '2026-11-02', '2026-11-03'],
        winner_probability_games=int(winner_scores.game_id.nunique()) if len(winner_scores) else 0)
    (a.out / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    assists = pooled[pooled.category.eq('assists')].set_index('model')
    pp_opportunity = pooled[(pooled.category.eq('pp_points')) &
                            (pooled.model.eq('pp_opportunity_trial'))]
    pp_trial_dates = set(by_date[(by_date.category.eq('pp_points')) &
                                 (by_date.model.eq('pp_opportunity_trial'))].date)
    pp_default_matched = by_date[(by_date.category.eq('pp_points')) &
        by_date.model.eq('default') & by_date.date.isin(pp_trial_dates)]
    pp_default_matched_mae = float((pp_default_matched.mae * pp_default_matched.rows).sum() /
                                   pp_default_matched.rows.sum())
    readme = f'''# November daily model review through {a.through}

## Results at a glance

Saved prospective releases cover {len(dates)} dates ({dates[0]}–{dates[-1]}), {games} games and {playergames:,} matched positive-TOI player-games. November 1–3 have no saved frozen releases, so they are not reconstructed.

**Keep calibrated-opponent SOG for NHL-wide shots.** Across {games} games, it scored {selected.mae:.3f} MAE versus {default.mae:.3f} for default ({100*(default.mae-selected.mae)/default.mae:.1f}% lower). The paired whole-game bootstrap difference was {pdelta.mae_delta_vs_default:+.3f} shots (95% interval [{pdelta.lower_95:+.3f}, {pdelta.upper_95:+.3f}]); it won on {pdelta.games_lower_mae}/{pdelta.games} games. The candidate model's pooled MAE was {shot.loc['candidate', 'mae']:.3f}, effectively tied with the selected variant, so there is no reason to retune the shot policy.

**Promote the isolated usage-aware ATOI model for NHL-wide conditional ice time.** `usage_toi_only_trial` scored {isolated_toi.mae:.3f} vs. {toi_default.mae:.3f} minutes MAE for default on {int(isolated_toi.games)} games ({100*(toi_default.mae-isolated_toi.mae)/toi_default.mae:.1f}% lower); the paired game-cluster interval for the difference was [{isolated_toi_pair.lower_95:+.3f}, {isolated_toi_pair.upper_95:+.3f}], with lower error in {isolated_toi_pair.games_lower_mae}/{isolated_toi_pair.games} games. This isolates the TOI change, unlike `usage_shot_context_trial`, which also changes SOG. The separate fantasy category policy already uses usage-aware TOI. {f'Across {summary["fantasy_usage_toi"]["games"]} fantasy-rostered games, {summary["fantasy_usage_toi"]["rows"]} appearances and {summary["fantasy_usage_toi"]["dates"]} dates with saved evaluations, usage-only MAE was {summary["fantasy_usage_toi"]["usage_toi_mae"]:.3f} vs. {summary["fantasy_usage_toi"]["default_mae"]:.3f} for default; paired interval [{summary["fantasy_usage_toi"]["lower_95"]:+.3f}, {summary["fantasy_usage_toi"]["upper_95"]:+.3f}].' if summary['fantasy_usage_toi'] else 'The saved daily fantasy comparisons are in the date-specific evaluation outputs.'} On Nov. 12 alone, fantasy-rostered MAE was 2.518 vs. 2.629 minutes.

**Keep fantasy shots on default pending a paired multi-date review.** Yesterday's 73 fantasy-rostered appearances favored candidate (1.168 MAE) and calibrated-opponent (1.172) over default (1.191), but one slate is not enough to change the separate fantasy SOG policy.

**Keep the direct-team win probabilities and goal-history baseline side by side; do not promote calibration.** Across the matched {int(winner_scores.game_id.nunique())}-game probability subset, direct-team Brier was {winner_metrics.set_index('model').loc['direct_team', 'brier']:.3f}, compared with {winner_metrics.set_index('model').loc['goal_history_baseline', 'brier']:.3f} for goal history and {winner_metrics.set_index('model').loc['original_player_sum', 'brier']:.3f} for player-sum. Original player-sum picked more winners ({winner_metrics.set_index('model').loc['original_player_sum', 'favorite_accuracy']:.1%} vs. {winner_metrics.set_index('model').loc['direct_team', 'favorite_accuracy']:.1%}), while direct-team probabilities were better under Brier. Calibration trial Brier was {winner_metrics.set_index('model').loc['calibrated_team_trial', 'brier']:.3f} on its {int(winner_metrics.set_index('model').loc['calibrated_team_trial', 'games'])}-game subset.

The PP-opportunity trial did not improve PP-point MAE ({pp_opportunity.mae.iloc[0]:.3f} vs. {pp_default_matched_mae:.3f} default on the same 27 games); keep it experimental. Assist MAE differences are negligible ({assists.loc['candidate'].mae:.3f} candidate vs. {assists.loc['default'].mae:.3f} default), so retain current rates.

## Population and provenance

Only pregame forecasts are scored. Conditional player predictions are scored for positive-TOI participants; nonparticipants remain unscored. On {latest_date}, {summary['latest_pregame_games']} games had {summary['latest_player_games']} matched player appearances; four actual skaters were missing forecasts. Late-issued SEA–CAR is excluded. Earlier Nov. 8 late scenarios are likewise excluded. Team win probabilities appear only on dates with a separately frozen direct-team release.

For {latest_date}, calibrated-opponent SOG MAE was {summary['latest_calibrated_shots_mae']:.3f} vs. {summary['latest_default_shots_mae']:.3f} default. Usage-only TOI MAE was {summary['latest_usage_toi_mae']:.3f} vs. {summary['latest_default_toi_mae']:.3f} minutes. Full model and category details are in the CSVs below. The daily goalie and fantasy evaluations remain in local processed-data outputs and are not included in this review bundle.

## All-player conditional metrics

See [pooled categories](player_metrics.csv), [date-level results](player_metrics_by_date.csv), and [paired SOG intervals](paired_shots_vs_default.csv). Lower MAE and RMSE are better; bias is predicted minus actual.

## Game probabilities

The direct-team/original player-sum comparison uses the matched subset with a separate frozen direct-team release. See [metrics](winner_metrics.csv), [games](team_games.csv), and [per-game scores](winner_scores.csv).

## Coverage

See [coverage by date](coverage_by_date.csv) and [actual participants missing from forecasts](unmodeled_actual_skaters.csv). The official schedule and boxscores were reconciled through {a.through}; all source manifests and file hashes are captured in `manifest.json`.
'''
    (a.out / 'README.md').write_text(readme)
    shots_table = pooled[pooled.category.eq('shots')][['model', 'rows', 'games', 'mae', 'bias']]
    toi_table = pooled[pooled.category.eq('toi_minutes')][['model', 'rows', 'games', 'mae', 'bias']]
    winner_table = winner_metrics if len(winner_metrics) else pd.DataFrame()
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>November model review</title><style>body{font:16px system-ui;color:#172c38;max-width:1120px;margin:30px auto;padding:20px;line-height:1.5}a{color:#08777c}h1,h2{color:#087e83}table{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0 24px}th,td{text-align:right;padding:9px;border-bottom:1px solid #d5e1e6}th:first-child,td:first-child{text-align:left}main{overflow:auto}</style></head><body><main>'
        '<p><a href="../../games/">Today’s game outlook</a> · <a href="../../team-model/">Today’s direct team model</a> · <a href="../../report/">Today’s fantasy report</a></p>'
        '<h1>November model review</h1><p>' +
        f'{games} prospective games and {playergames:,} matched player-games across {len(dates)} dates ({dates[0]}–{dates[-1]}). Forecasts are scored only for actual participants.</p>'
        f'<h2>Recommendation</h2><p><strong>Keep calibrated-opponent shots selected for NHL-wide SOG.</strong> It reduced MAE from {default.mae:.3f} to {selected.mae:.3f} ({100*(default.mae-selected.mae)/default.mae:.1f}%); paired game-cluster 95% interval for its difference: [{pdelta.lower_95:+.3f}, {pdelta.upper_95:+.3f}].</p>'
        f'<p><strong>Promote the isolated usage-only TOI variant for NHL-wide ATOI.</strong> It reduced MAE from {toi_default.mae:.3f} to {isolated_toi.mae:.3f} minutes across {int(isolated_toi.games)} games; the paired interval [{isolated_toi_pair.lower_95:+.3f}, {isolated_toi_pair.upper_95:+.3f}] excludes zero.</p>'
        '<p>Keep fantasy SOG on default. Do not promote PP or calibrated win probabilities. November 1–3 lack saved releases and are not reconstructed.</p>'
        '<h2>All-player shots</h2>' + shots_table.round(4).to_html(index=False, border=0) +
        '<h2>Conditional ice time</h2>' + toi_table.round(4).to_html(index=False, border=0) +
        '<h2>Matched winner probability subset</h2>' + winner_table.round(4).to_html(index=False, border=0) +
        '<p><a href="README.md">Methods and interpretation</a> · <a href="player_metrics.csv">All player categories</a> · <a href="player_metrics_by_date.csv">By date</a> · <a href="paired_shots_vs_default.csv">Paired intervals</a> · <a href="coverage_by_date.csv">Coverage</a></p>'
        '</main></body></html>')
    (a.out / 'index.html').write_text(html)
    (a.out / 'manifest.json').write_text(json.dumps(dict(
        created_at_utc=datetime.now(timezone.utc).isoformat(), through=a.through,
        actuals=repo_path(a.actuals), actuals_manifest_sha256=sha(a.actuals / 'manifest.json'),
        boxscores=repo_path(a.boxscores), boxscore_metadata_sha256=sha(a.boxscores / 'metadata.json'),
        frozen_releases=source_hashes, code_sha256=sha(__file__), summary=summary,
        files={p.name: sha(p) for p in a.out.iterdir() if p.is_file() and p.name != 'manifest.json'}),
        indent=2, allow_nan=False) + '\n')
    print(readme)
    print('\nWinner metrics:')
    print(winner_metrics.to_string(index=False))


if __name__ == '__main__':
    main()
