#!/usr/bin/env python3
"""Build a past-only replay of the NHL conditional shots models.

This does not recreate missing forecasts as-issued. It applies the current
weighted-rate baseline and the frozen October 6-7 calibration plus NHL SOG
opponent factor to each historical game date, using only earlier outcomes.
The replay scores actual participants and does not evaluate roster selection
or availability.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import argparse
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_per_game_forecast import latest_snapshot
from src.fantasy.daily import current_from_games
from src.fantasy.per_game import TARGETS, forecast, load_season, require
from src.fantasy.shot_context import load_nhl_team_games


SEASON = 20262027
THROUGH = "2026-11-05"
SEASON_DIR = Path("outputs/per_game_forecast/season_through_2026-11-05")
ACTUALS_DIR = Path("data/processed/forecasts/fantasy_game_details_20261106T213413Z")
BOXSCORE_DIR = Path("data/raw/nhl/snapshots/current_game_history_20262027_20261106T213140Z")
TEMPLATE_DIR = Path("data/processed/forecasts/per_game_20262027_20261006T233936Z")
CALIBRATION_FILE = Path("config/game_calibration_candidate.json")
CONFIG_FILE = Path("config/daily_forecast_trial.json")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prior_position_means(panel: pd.DataFrame) -> pd.DataFrame:
    past = panel[(panel.season_id < SEASON) & (panel.season_id >= 20232024)].copy()
    past["weight"] = 0.5 ** (2025 - past.season_id // 10000)
    totals = past[TARGETS + ["games_played"]].mul(past.weight, axis=0).groupby(past.position_group).sum()
    return totals[TARGETS].div(totals.games_played, axis=0)


def rates_for_date(history: pd.DataFrame, panel: pd.DataFrame, date: str,
                   params: dict, process_params: dict, common: dict) -> pd.DataFrame:
    """Return conditional rates at the date cutoff, matching the daily pipeline."""
    past = history[history.game_date < date]
    if past.empty:
        combined = panel[panel.season_id < SEASON].copy()
        rates = forecast(combined, SEASON, include_current=False, **common, **params)
        process = forecast(combined, SEASON, include_current=False, **common, **process_params)
    else:
        current = current_from_games(past, date, SEASON)
        combined = pd.concat([panel[panel.season_id < SEASON], current], ignore_index=True)
        rates = forecast(combined, SEASON, include_current=True, **common, **params)
        process = forecast(combined, SEASON, include_current=True, **common, **process_params)

    rates = rates.set_index("player_id")
    process = process.set_index("player_id")
    rookies = rates.historical_gp.eq(0)
    if rookies.any():
        for event in TARGETS:
            col = f"{event}_per_game"
            rates.loc[rookies, col] = process[col].reindex(rates.index[rookies])
    rates = rates.reset_index()
    return rates[["player_id", "position_group", "shots_per_game", "goals_per_game"]]


def team_context_for_date(team_games: pd.DataFrame, date: str, prior_games: int = 20):
    """Reproduce the daily raw-NHL SOG context factor with a strict date cutoff."""
    current = team_games[(team_games.game_date < date) & team_games.season_id.eq(SEASON)].copy()
    if current.empty:
        return {}, np.nan
    league = float(current.sf.mean())
    context = {}
    for team, group in current.groupby("team"):
        context[team] = dict(
            sf=(float(group.sf.sum()) + prior_games * league) / (len(group) + prior_games),
            sa=(float(group.sa.sum()) + prior_games * league) / (len(group) + prior_games),
            games=len(group),
        )
    return context, league


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
        default=Path("outputs/per_game_forecast/rolling_replay_through_2026-11-05"),
        help="new output directory; existing outputs are preserved")
    args = parser.parse_args()
    out = args.out
    require(not out.exists(), f"Preserve existing review; choose a new output folder: {out}")

    actual_manifest = json.loads((ACTUALS_DIR / "manifest.json").read_text())
    for name, digest in actual_manifest["files"].items():
        require(sha(ACTUALS_DIR / name) == digest, f"Actuals hash mismatch: {name}")
    actual = pd.read_csv(ACTUALS_DIR / "skater_game_stats.csv")
    actual["game_id"] = actual.game_id.astype(str)
    actual["player_id"] = pd.to_numeric(actual.player_id, errors="raise").astype("int64")
    actual["game_date"] = actual.game_date.astype(str)
    actual = actual[(actual.toi_seconds > 0) & (actual.game_date <= THROUGH)].copy()
    require(actual.game_date.max() == THROUGH, "Actuals do not reach requested cutoff")
    require(not actual.duplicated(["game_id", "player_id"]).any(), "Duplicate actual player-game")

    box_meta = json.loads((BOXSCORE_DIR / "metadata.json").read_text())
    require(box_meta["final_games"] == 261 and box_meta["through_eastern_date"] == THROUGH,
            "Unexpected official NHL boxscore snapshot")
    team_games = load_nhl_team_games(BOXSCORE_DIR)
    team_games["game_id"] = team_games.game_id.astype(str)
    team_games["game_date"] = team_games.game_date.astype(str)
    require(team_games.game_id.nunique() == actual.game_id.nunique(), "Game coverage mismatch")
    require(team_games.groupby("game_id").size().eq(2).all(), "Incomplete NHL team-game pairs")

    template = json.loads((TEMPLATE_DIR / "manifest.json").read_text())
    config = template["config"]
    require(template["selected_on_validation"]["method"] == "weighted", "Unexpected rate method")
    params = {k: v for k, v in template["selected_on_validation"].items() if k != "score"}
    process_params = {k: v for k, v in template["best_process"].items() if k != "score"}
    common = dict(lookback=config["lookback_seasons"], toi_prior_games=config["toi_prior_games"])
    panel_frames, season_sources = [], []
    snapshot_root = Path("data/raw/nhl/snapshots")
    for season in config["history_seasons"]:
        folder = latest_snapshot(snapshot_root, season)
        frame, provenance, _ = load_season(folder, season)
        panel_frames.append(frame)
        season_sources.extend(provenance)
    panel = pd.concat(panel_frames, ignore_index=True)
    require(not panel.duplicated(["player_id", "season_id"]).any(), "Duplicate prior-season player rows")
    priors = prior_position_means(panel)

    calibration = json.loads(CALIBRATION_FILE.read_text())
    multiplier = float(calibration["factors"]["shots"]["multiplier"])
    trained_through = max(calibration["calibration_dates"])
    require(trained_through == "2026-10-07", "Unexpected calibration window")

    opponent_map = (team_games[["game_id", "team", "opponent"]]
                    .rename(columns={"opponent": "opponent_team"}))
    target = actual.merge(opponent_map, on=["game_id", "team"], how="left", validate="many_to_one")
    require(target.opponent_team.notna().all(), "Missing target-team opponent")
    target_dates = sorted(target.game_date.unique())
    output = []
    coverage = []
    factors_by_date = {}
    rates_by_date = {}

    for date in target_dates:
        rates = rates_for_date(actual, panel, date, params, process_params, common).copy()
        rates_by_date[date] = rates.set_index("player_id")
        context, league = team_context_for_date(team_games, date)
        factors = {}
        # Build the factor from the target slate's team-opponent pairs.
        slate = target.loc[target.game_date.eq(date), ["game_id", "team", "opponent_team"]].drop_duplicates()
        for row in slate.itertuples(index=False):
            if np.isfinite(league) and row.team in context and row.opponent_team in context:
                factors[(row.game_id, row.team)] = float(
                    np.sqrt(context[row.team]["sf"] * context[row.opponent_team]["sa"]) / league)
            else:
                factors[(row.game_id, row.team)] = 1.0
        factors_by_date[date] = factors
        day = target[target.game_date.eq(date)]
        for row in day.itertuples(index=False):
            rate = rates_by_date[date].loc[row.player_id] if row.player_id in rates_by_date[date].index else None
            if rate is None:
                group = "D" if row.position == "D" else "F"
                base_shots = float(priors.loc[group, "shots"])
                base_goals = float(priors.loc[group, "goals"])
                source = "past_position_prior_no_player_history"
            else:
                base_shots = float(rate.shots_per_game)
                base_goals = float(rate.goals_per_game)
                source = "past_player_seasons_plus_current_season_through_prior_date"
            opponent_factor = factors[(row.game_id, row.team)]
            # Match the daily feasibility rule that projected shots cannot be
            # below projected goals; other event means do not affect this score.
            default_shots = max(base_shots, base_goals)
            calibrated_shots = max(base_shots * multiplier * opponent_factor, base_goals)
            challenger_eligible = date > trained_through
            output.append(dict(
                date=date, game_id=row.game_id, player_id=row.player_id,
                player_name=row.name, team=row.team, opponent=row.opponent_team,
                position_group="D" if row.position == "D" else "F",
                actual_shots=float(row.shots), default_forecast=default_shots,
                calibrated_opponent_forecast=(calibrated_shots if challenger_eligible else np.nan),
                base_rate_shots=base_shots, base_rate_goals=base_goals,
                calibration_multiplier=multiplier, opponent_factor=opponent_factor,
                forecast_rate_source=source, challenger_eligible=challenger_eligible,
                history_cutoff_exclusive=date,
            ))
        for game_id, game in day.groupby("game_id"):
            coverage.append(dict(date=date, game_id=game_id,
                actual_positive_toi_players=len(game),
                default_predictions=len(game),
                calibrated_opponent_predictions=len(game) if date > trained_through else 0,
                history_cutoff_exclusive=date,
                forecast_policy="fixed_weighted_rate_plus_historical_NHL_SOG_context"))

    scored = pd.DataFrame(output)
    require(not scored.duplicated(["game_id", "player_id"]).any(), "Duplicate replay player-game")
    require(scored.game_id.nunique() == 261, "Replay does not cover all 261 completed games")
    post = scored[scored.challenger_eligible].copy()
    require(post.game_id.nunique() > 200, "Unexpectedly small post-calibration sample")

    rows = []
    for window, frame in [("all_261_games_default", scored),
                          ("post_calibration_paired", post)]:
        model_cols = [("default", "default_forecast")]
        if window == "post_calibration_paired":
            model_cols.append(("calibrated_opponent_sog_trial", "calibrated_opponent_forecast"))
        for model, column in model_cols:
            err = frame[column] - frame.actual_shots
            rows.append(dict(window=window, model=model, player_games=len(frame),
                games=frame.game_id.nunique(), dates=frame.date.nunique(),
                forecast_total=frame[column].sum(), actual_total=frame.actual_shots.sum(),
                mae=err.abs().mean(), rmse=np.sqrt((err ** 2).mean()), bias=err.mean()))
    metrics = pd.DataFrame(rows)

    paired = post.assign(default_ae=(post.default_forecast-post.actual_shots).abs(),
        calibrated_ae=(post.calibrated_opponent_forecast-post.actual_shots).abs())
    game_metrics = paired.groupby(["date", "game_id"], as_index=False).agg(
        player_games=("player_id", "size"), default_mae=("default_ae", "mean"),
        calibrated_opponent_mae=("calibrated_ae", "mean"))
    game_metrics["calibrated_minus_default_mae"] = (
        game_metrics.calibrated_opponent_mae-game_metrics.default_mae)
    game_metrics["calibrated_lower_error"] = game_metrics.calibrated_minus_default_mae.lt(-1e-12)

    rng = np.random.default_rng(20261106)
    game_sums = paired.groupby("game_id")[["default_ae", "calibrated_ae"]].sum()
    game_counts = paired.groupby("game_id").size().reindex(game_sums.index).to_numpy()
    sums = game_sums.to_numpy()
    draws = np.empty(20000)
    for i in range(len(draws)):
        idx = rng.integers(0, len(game_sums), len(game_sums))
        draws[i] = (sums[idx, 1].sum()-sums[idx, 0].sum())/game_counts[idx].sum()
    delta = (paired.calibrated_ae.sum()-paired.default_ae.sum())/len(paired)
    uncertainty = pd.DataFrame([dict(
        comparison="calibrated_opponent_sog_trial - default", games=len(game_sums),
        player_games=len(paired), observed_mae_delta=delta,
        interval_95_low=np.quantile(draws, .025), interval_95_high=np.quantile(draws, .975),
        calibrated_lower_error_games=int(game_metrics.calibrated_lower_error.sum()),
        seed=20261106, resamples=len(draws),
        interval_method="paired bootstrap resampling whole games")])

    by_date = []
    for date, group in scored.groupby("date"):
        default_error = group.default_forecast-group.actual_shots
        row = dict(date=date, games=group.game_id.nunique(), player_games=len(group),
            default_mae=default_error.abs().mean(), default_bias=default_error.mean(),
            challenger_eligible=bool(group.challenger_eligible.all()))
        if group.challenger_eligible.all():
            error = group.calibrated_opponent_forecast-group.actual_shots
            row.update(calibrated_opponent_mae=error.abs().mean(), calibrated_opponent_bias=error.mean())
        by_date.append(row)
    by_date = pd.DataFrame(by_date)

    # Compare the replay with archived prospective means on their shared
    # player-games. This is a reproducibility diagnostic, not part of the score.
    saved_path = SEASON_DIR / "shots_scored_all_games.csv"
    saved = pd.read_csv(saved_path)
    saved = saved[saved.model.isin(["default", "calibrated_opponent_sog_trial"])]
    saved = saved[["date", "game_id", "player_id", "model", "forecast"]].copy()
    saved["game_id"] = saved.game_id.astype(str)
    saved["player_id"] = saved.player_id.astype(str)
    replay_join = scored[["date", "game_id", "player_id", "default_forecast",
                          "calibrated_opponent_forecast"]].copy()
    replay_join["player_id"] = replay_join.player_id.astype(str)
    replay_join = replay_join.melt(id_vars=["date", "game_id", "player_id"],
        value_vars=["default_forecast", "calibrated_opponent_forecast"],
        var_name="replay_model", value_name="replay_forecast")
    replay_join["model"] = replay_join.replay_model.map({
        "default_forecast": "default",
        "calibrated_opponent_forecast": "calibrated_opponent_sog_trial"})
    replay_join = replay_join.dropna(subset=["replay_forecast"])
    overlap = saved.merge(replay_join[["date", "game_id", "player_id", "model", "replay_forecast"]],
        on=["date", "game_id", "player_id", "model"], how="inner", validate="one_to_one")
    overlap["forecast_difference"] = overlap.replay_forecast-overlap.forecast
    agreement = []
    for model, group in overlap.groupby("model"):
        agreement.append(dict(model=model, overlap_player_games=len(group),
            games=group.game_id.nunique(),
            mean_absolute_forecast_difference=group.forecast_difference.abs().mean(),
            mean_signed_forecast_difference=group.forecast_difference.mean(),
            correlation=group[["forecast", "replay_forecast"]].corr().iloc[0, 1]))
    agreement = pd.DataFrame(agreement)

    out.mkdir(parents=True)
    scored.sort_values(["date", "game_id", "team", "player_name"]).to_csv(out/"shots_replay_all_games.csv", index=False)
    pd.DataFrame(coverage).to_csv(out/"game_coverage.csv", index=False)
    metrics.to_csv(out/"model_metrics.csv", index=False)
    by_date.to_csv(out/"metrics_by_date.csv", index=False)
    game_metrics.to_csv(out/"paired_game_metrics.csv", index=False)
    uncertainty.to_csv(out/"paired_uncertainty.csv", index=False)
    overlap.to_csv(out/"replay_vs_saved_forecasts.csv", index=False)
    agreement.to_csv(out/"replay_agreement_summary.csv", index=False)

    post_metrics = metrics[metrics.window.eq("post_calibration_paired")].set_index("model")
    default_mae = float(post_metrics.loc["default", "mae"])
    trial_mae = float(post_metrics.loc["calibrated_opponent_sog_trial", "mae"])
    percent = 100*(default_mae-trial_mae)/default_mae
    bootstrap = uncertainty.iloc[0]
    summary = [
        "# Past-only shots replay through November 5, 2026", "",
        "This is a retrospective, date-cutoff replay, not recovery of the missing original forecasts. "
        "It applies the selected weighted player-rate baseline and the frozen calibrated-opponent SOG "
        "formula to each completed game date, rebuilding each forecast from official outcomes dated "
        "before that entire date. It uses one current official actuals vintage.", "",
        "## Results", "",
        f"The baseline replay covers **{scored.game_id.nunique()} games and {len(scored):,} positive-TOI player-games** "
        f"from {scored.date.min()} through {scored.date.max()}. Its all-game conditional SOG MAE is "
        f"**{metrics.iloc[0].mae:.4f} shots**. The calibrated-opponent comparison excludes the "
        f"{scored.loc[~scored.challenger_eligible, 'game_id'].nunique()} calibration-training games and covers "
        f"**{post.game_id.nunique()} games and {len(post):,} paired player-games** after {trained_through}.", "",
        f"On that shared post-calibration cohort, default MAE is **{default_mae:.4f}** and "
        f"calibrated-opponent MAE is **{trial_mae:.4f}**, **{percent:.1f}% lower**. The paired game-cluster "
        f"95% interval for calibrated minus default is **{bootstrap.interval_95_low:+.4f} to "
        f"{bootstrap.interval_95_high:+.4f} shots**; the trial was lower-error in "
        f"{int(bootstrap.calibrated_lower_error_games)} of {int(bootstrap.games)} games. These replay estimates "
        "are conditional on having played; the results do not evaluate whether the daily roster or lineup "
        "selection found the player.", "",
        "## Interpretation limits", "",
        "- The NHL and MoneyPuck APIs provide historical outcomes and team inputs, not Rink Lab's missing saved forecast releases. "
        "The exact issued predictions for unarchived dates cannot be recovered.",
        "- The replay uses the current weighted-rate method, current frozen multiplier and strict past-game cutoffs. "
        "It does not represent the model versions, candidate pool, status snapshot, or lineup known on every historical date.",
        "- The multiplier was calibrated on October 6-7; only later dates are used for the paired challenger comparison. "
        "Earlier games contribute only to the default's full-period descriptive score.",
        "- The player set is defined by postgame positive TOI and is forecast conditionally on playing. "
        "This isolates conditional SOG means and cannot measure availability, lineup selection, or unmodeled call-ups.",
        "- The replay is checked against saved prospective default and calibrated-opponent forecasts on overlapping rows in "
        "[the agreement diagnostic](replay_agreement_summary.csv); source corrections can still change historical features.",
        "- The separate [original frozen-release evaluation](../season_through_2026-11-05/README.md) remains the clean prospective result. "
        "Do not pool its rows with this replay as if every prediction had been issued live.", "",
        "## Files", "",
        "[All replay forecast and outcome rows](shots_replay_all_games.csv) · [coverage by game](game_coverage.csv) · "
        "[metrics by model](model_metrics.csv) · [metrics by date](metrics_by_date.csv) · "
        "[paired game results](paired_game_metrics.csv) · [paired uncertainty](paired_uncertainty.csv) · "
        "[replay versus saved forecast rows](replay_vs_saved_forecasts.csv).", "",
        f"Reproduction: `python3 scripts/review_walk_forward_sog.py --out outputs/per_game_forecast/rolling_replay_through_2026-11-05_rerun`. Actuals cutoff: {THROUGH}; "
        f"the calibration freeze was dated through {trained_through}.",
    ]
    (out/"README.md").write_text("\n".join(summary)+"\n")

    sources = dict(actuals_manifest_sha256=sha(ACTUALS_DIR/"manifest.json"),
        actuals_file_sha256=sha(ACTUALS_DIR/"skater_game_stats.csv"),
        boxscore_metadata_sha256=sha(BOXSCORE_DIR/"metadata.json"),
        calibration_sha256=sha(CALIBRATION_FILE), config_sha256=sha(CONFIG_FILE),
        template_forecast_manifest_sha256=sha(TEMPLATE_DIR/"manifest.json"),
        saved_review_manifest_sha256=sha(SEASON_DIR/"manifest.json"),
        prior_season_sources=season_sources)
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), through=THROUGH,
        games=int(scored.game_id.nunique()), player_games=int(len(scored)),
        calibrated_games=int(post.game_id.nunique()), calibrated_player_games=int(len(post)),
        calibration_training_dates=calibration["calibration_dates"],
        replay_scope="conditional positive-TOI player SOG means; not availability or lineup selection",
        history_cutoff="strictly before each complete game date", sources=sources,
        code_sha256=sha(Path(__file__)),
        files={p.name: sha(p) for p in out.iterdir() if p.is_file()})
    (out/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(metrics.to_string(index=False))
    print(uncertainty.to_string(index=False))
    print(agreement.to_string(index=False))
    print("Review:", out)


if __name__ == "__main__":
    main()
