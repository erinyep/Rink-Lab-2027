#!/usr/bin/env python3
"""Validate NHL snapshots, evaluate baselines, and export conditional game means."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from src.fantasy.per_game import TARGETS, evaluate, forecast, latest_snapshot, load_season, require
from src.fantasy.schedule import export_schedule_reference


def relative_mae(metrics, reference, categories):
    a = metrics[(metrics.group == "all") & metrics.category.isin(categories)].set_index("category").mae
    b = reference[(reference.group == "all") & reference.category.isin(categories)].set_index("category").mae
    require((b > 0).all(), "Zero reference MAE; choose another selection metric explicitly")
    return float((a / b).mean())


def attach_espn(current, output, espn_root, processed_root, target_season):
    snapshots = sorted(espn_root.glob(f"espn_{target_season % 10000}_*"))
    if not snapshots:
        return {"status": "no_espn_snapshot"}
    snapshot = snapshots[-1]
    metadata = json.loads((snapshot / "metadata.json").read_text())
    require(all(metadata["validation"].values()), "ESPN recorded checks failed")
    require(not metadata["available_limit_reached"], "Available-player pool may be truncated")
    require(metadata["team_count"] == 6, "ESPN team count differs from Micro League configuration")
    for filename in ["rosters.csv", "available_players.csv"]:
        require(hashlib.sha256((snapshot / filename).read_bytes()).hexdigest() == metadata["files"][filename]["sha256"],
                f"ESPN hash mismatch: {filename}")
    roster = pd.read_csv(snapshot / "rosters.csv")
    roster["pool"] = "rostered"
    available = pd.read_csv(snapshot / "available_players.csv")
    available["pool"] = "available"
    pool = pd.concat([roster, available], ignore_index=True)
    crosswalk_file = processed_root / snapshot.name / "espn_nhl_crosswalk.csv"
    crosswalk = pd.read_csv(crosswalk_file)
    crosswalk_key = str(crosswalk_file.relative_to(ROOT)) if crosswalk_file.is_absolute() else str(crosswalk_file)
    require(hashlib.sha256(crosswalk_file.read_bytes()).hexdigest() == metadata["files"][crosswalk_key]["sha256"],
            "ESPN crosswalk hash mismatch")
    pool = pool.merge(crosswalk[["espn_player_id", "nhl_player_id", "match_status", "match_method"]],
                      on="espn_player_id", how="left", validate="many_to_one")
    pool = pool.merge(current, left_on="nhl_player_id", right_on="player_id", how="left", validate="many_to_one")
    pool["forecast_status"] = np.select(
        [pool.primary_position.isin(["Goalie", "G"]), pool.match_status != "matched", pool.goals_per_game.isna()],
        ["goalie_model_pending", "unresolved_nhl_identity", "no_recent_nhl_skater_history"],
        default="conditional_on_playing")
    pool["espn_retrieved_at_utc"] = metadata["retrieval_completed_at_utc"]
    # An ESPN injury label is context, not a calibrated probability or a confirmed lineup.
    pool["probability_of_playing"] = np.nan
    pool["availability_model_status"] = "not_fitted"
    pool["roster_transition_status"] = np.where(
        pool.espn_player_id.isin(metadata.get("pending_drop_overlap_ids", [])),
        "pending_drop_still_in_scoring_roster_review_required", "no_reported_overlap")
    pool.to_csv(output / "espn_player_forecasts.csv", index=False)
    return dict(snapshot=str(snapshot), retrieved_at_utc=metadata["retrieval_completed_at_utc"],
                rows=len(pool), rostered_status=pool[pool.pool == "rostered"].forecast_status.value_counts().to_dict(),
                status_counts=pool.forecast_status.value_counts().to_dict())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/per_game_forecast.json"))
    parser.add_argument("--snapshot-root", type=Path, default=Path("data/raw/nhl/snapshots"))
    parser.add_argument("--output-root", type=Path, default=Path("data/processed/forecasts"))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    require(config["development_season"] < config["validation_season"] < config["test_season"] < config["target_season"],
            "Development, validation, test and live seasons must be ordered")
    frames, sources, audits = [], [], []
    for season in config["history_seasons"] + [config["target_season"]]:
        frame, provenance, audit = load_season(latest_snapshot(args.snapshot_root, season), season)
        frames.append(frame)
        sources.extend(provenance)
        audits.extend(audit)
    panel = pd.concat(frames, ignore_index=True)
    require(not panel.duplicated(["player_id", "season_id"]).any(), "Duplicate player-season")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.output_root / f"per_game_{config['target_season']}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    panel.to_csv(out / "validated_player_seasons.csv", index=False)
    pd.DataFrame(audits).to_csv(out / "source_column_audit.csv", index=False)
    common = dict(lookback=config["lookback_seasons"], toi_prior_games=config["toi_prior_games"])
    validation = config["validation_season"]
    reference, _, _ = evaluate(forecast(panel, validation, method="last_season", **common), panel, validation)
    candidates = []
    for decay, event_prior, shot_prior in itertools.product(config["decay_grid"],
            config["event_prior_games_grid"], config["shooting_prior_shots_grid"]):
        params = dict(decay=decay, event_prior_games=event_prior, shooting_prior_shots=shot_prior)
        metrics, _, _ = evaluate(forecast(panel, validation, **common, **params), panel, validation)
        candidates.append(dict(method="process", **params,
                               score=relative_mae(metrics, reference, config["selection_categories"])))
    for decay in config["decay_grid"]:
        metrics, _, _ = evaluate(forecast(panel, validation, method="weighted", decay=decay, **common), panel, validation)
        candidates.append(dict(method="weighted", decay=decay, event_prior_games=0, shooting_prior_shots=0,
                               score=relative_mae(metrics, reference, config["selection_categories"])))
    candidates.append(dict(method="last_season", decay=1, event_prior_games=0, shooting_prior_shots=0, score=1.0))
    tuning = pd.DataFrame(candidates).sort_values("score", kind="stable")
    tuning.to_csv(out / "validation_model_selection.csv", index=False)
    chosen = tuning.iloc[0].to_dict()
    best_process = tuning[tuning.method == "process"].iloc[0].to_dict()
    best_weighted = tuning[tuning.method == "weighted"].iloc[0].to_dict()
    models = [dict(method="last_season", decay=1, event_prior_games=0, shooting_prior_shots=0),
              {k: v for k, v in best_weighted.items() if k != "score"},
              {k: v for k, v in best_process.items() if k != "score"}]
    all_metrics, coverage = [], []
    for season in [config["development_season"], validation, config["test_season"]]:
        for params in models:
            metrics, predictions, covered = evaluate(forecast(panel, season, **common, **params), panel, season)
            metrics["method"] = params["method"]
            metrics["split"] = {config["development_season"]: "development_diagnostic",
                                validation: "validation", config["test_season"]: "held_out_test"}[season]
            all_metrics.append(metrics)
            if params["method"] == "last_season":
                coverage.append(covered)
            if season == config["test_season"]:
                predictions.to_csv(out / f"held_out_{params['method']}_players.csv", index=False)
    metrics = pd.concat(all_metrics, ignore_index=True)
    metrics.to_csv(out / "evaluation_metrics.csv", index=False)
    pd.DataFrame(coverage).to_csv(out / "evaluation_population.csv", index=False)
    params = {k: v for k, v in chosen.items() if k != "score"}
    preseason = forecast(panel, config["target_season"], **common, **params)
    current = forecast(panel, config["target_season"], include_current=True, **common, **params)
    process_current = forecast(panel, config["target_season"], include_current=True, **common,
                               **{k: v for k, v in best_process.items() if k != "score"})
    # The validation cohort contains prior-known players, so it cannot justify
    # extrapolating an unshrunk few-game rate to a brand-new NHL player. Retain
    # them using a visibly provisional past-position shrinkage fallback.
    rookies = current.historical_gp == 0
    if rookies.any():
        process_index = process_current.set_index("player_id")
        for col in [f"{e}_per_game" for e in TARGETS]:
            current.loc[rookies, col] = current.loc[rookies, "player_id"].map(process_index[col])
        current.loc[rookies, "method"] = "process_rookie_fallback"
        current.loc[rookies, "fallback"] = "past_position_shrinkage_unvalidated_for_rookies"
    preseason.to_csv(out / "completed_history_forecast.csv", index=False)
    process_current.to_csv(out / "process_components_provisional.csv", index=False)
    current["forecast_scope"] = "season_aggregate_conditional_mean_not_opponent_specific"
    current["current_update_status"] = "provisional_not_validated_on_game_cutoffs"
    current.to_csv(out / "current_per_game_forecast.csv", index=False)
    panel[panel.season_id == config["target_season"]].to_csv(out / "current_observed_stats.csv", index=False)
    espn = attach_espn(current, out, Path("data/raw/espn/snapshots"), Path("data/processed/espn"), config["target_season"])
    schedules = sorted(args.snapshot_root.glob(f"schedule_{config['target_season']}_*"))
    schedule = {"status": "no_schedule_snapshot"}
    if schedules and (out / "espn_player_forecasts.csv").exists():
        schedule = export_schedule_reference(out / "espn_player_forecasts.csv", schedules[-1], out)
    manifest = dict(created_at_utc=datetime.now(timezone.utc).isoformat(), config=config,
                    selected_on_validation=chosen, best_process=best_process,
                    source_snapshots=sources, espn=espn, schedule=schedule, evaluation_population=coverage,
                    software=dict(python=sys.version.split()[0], pandas=pd.__version__, numpy=np.__version__),
                    limitations=["Historical source corrections were retrieved today; not historical as-of snapshots.",
                                 "Per-game evaluation uses season averages of returning players; no individual-game backtest.",
                                 "Players with no target appearance remain recorded with undefined per-game outcomes.",
                                 "Entrants absent from prior history are counted but not retrospectively predicted using future identities.",
                                 "Live current-season update and auxiliary categories are provisional.",
                                 "No fitted participation, goalie-start, injury, opponent, age or role adjustment.",
                                 "No calibrated intervals, GP forecast, fantasy rank, replacement value or lineup optimization."])
    manifest["files"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.csv"))}
    manifest["code_sha256"] = {
        str(p): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path("scripts/build_per_game_forecast.py"), Path("src/fantasy/per_game.py"),
                  Path("src/fantasy/schedule.py"), args.config]
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    test = metrics[(metrics.split == "held_out_test") & (metrics.group == "all") & metrics.category.isin(config["selection_categories"])]
    print("Forecast output:", out)
    print("Selected on validation:", chosen)
    print(test[["method", "category", "players", "mae", "bias", "gp_weighted_mae"]].to_string(index=False))
    print("ESPN roster coverage:", espn.get("rostered_status"))


if __name__ == "__main__":
    main()
