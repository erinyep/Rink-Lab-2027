#!/usr/bin/env python3
"""Evaluate a frozen daily bundle in a new directory, separating issue timing.

Player predictions are conditional on playing: absent/zero-TOI observations
remain missing. Team SOG uses NHL boxscore totals; other categories sum skaters.
Goalie full-start errors are explicitly separated from relief and duration.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from src.fantasy.per_game import require

CATEGORIES = ["goals", "assists", "shots", "hits", "points", "pp_points",
              "penalty_minutes", "plus_minus", "toi_minutes"]


def digest(path, algorithm="sha256"):
    return hashlib.new(algorithm, Path(path).read_bytes()).hexdigest()


def verify_hash(path, expected, audit, algorithm="sha256"):
    observed = digest(path, algorithm)
    require(observed == expected, f"Source hash mismatch: {path}")
    audit.append(dict(file=str(path), algorithm=algorithm, expected=expected,
                      observed=observed, status="verified"))


def verify_manifest_files(folder, audit):
    manifest = json.loads((folder / "manifest.json").read_text())
    for name, value in manifest.get("files", {}).items():
        expected = value.get("sha256") if isinstance(value, dict) else value
        if expected:
            verify_hash(folder / name, expected, audit)
    return manifest


def verify_inputs(bundle, actuals, boxscores):
    """Verify all recorded data hashes; expose the known circular parent link.

    Historical code hashes identify issuance code and need not equal today's
    evaluator checkout. A goalie manifest recorded the parent manifest before
    its goalie fields were appended: that exact parent-only conflict is logged
    rather than pretending its historical bytes are still present.
    """
    audit = []
    manifest = verify_manifest_files(bundle, audit)
    inputs = Path(manifest["forecast"])
    verify_hash(inputs / "manifest.json", manifest["input_manifest_sha256"], audit)
    im = verify_manifest_files(inputs, audit)
    for source in im.get("source_snapshots", []):
        verify_hash(Path(source["file"]), source["md5"], audit, "md5")
    for source in manifest.get("sources", []):
        verify_hash(Path(manifest["raw_context"]) / source["file"], source["sha256"], audit)
    for file, expected in manifest.get("additional_sources", {}).items():
        verify_hash(Path(file), expected, audit)
    if manifest.get("moneypuck_sha256"):
        verify_hash(Path(manifest["moneypuck_snapshot"]) / "all_teams.csv",
                    manifest["moneypuck_sha256"], audit)
    history_dirs = {actuals, Path(manifest["game_history"])}
    for folder in history_dirs:
        source_manifest = verify_manifest_files(folder, audit)
        for source in source_manifest.get("sources", []):
            for field in ["boxscore", "landing"]:
                if source.get(field + "_sha256"):
                    verify_hash(Path(source[field]), source[field + "_sha256"], audit)
    bm = json.loads((boxscores / "metadata.json").read_text())
    for source in bm["sources"]:
        verify_hash(boxscores / source["file"], source["sha256"], audit)
    if manifest.get("goalie_source"):
        folder = Path(manifest["goalie_source"])
        verify_hash(folder / "manifest.json", manifest["goalie_manifest_sha256"], audit)
        gm = verify_manifest_files(folder, audit)
        for source in gm.get("sources", []):
            path = Path(source["file"])
            if path.resolve() == (bundle / "manifest.json").resolve() and digest(path) != source["sha256"]:
                audit.append(dict(file=str(path), algorithm="sha256", expected=source["sha256"],
                    observed=digest(path), status="historical_parent_manifest_back_reference_unavailable"))
            else:
                verify_hash(path, source["sha256"], audit)
    return manifest, pd.DataFrame(audit).drop_duplicates()


def validate_timing(frame):
    require(frame.issue_timing.isin(["pregame", "late_not_pregame"]).all(), "Unknown issue timing")
    if "issued_at_utc" in frame:
        issued = pd.to_datetime(frame.issued_at_utc, utc=True)
        starts = pd.to_datetime(frame.start_time_utc, utc=True)
        expected = np.where(issued < starts, "pregame", "late_not_pregame")
        require((frame.issue_timing == expected).all(), "Issue timing disagrees with issuance timestamps")


def add_errors(frame, mean_column):
    frame = frame.copy()
    frame["signed_error"] = frame[mean_column] - frame.actual
    frame["absolute_error"] = frame.signed_error.abs()
    frame["squared_error"] = frame.signed_error ** 2
    if "whole_number_guess" in frame:
        valid = frame.actual.notna() & frame.whole_number_guess.notna()
        frame["exact_guess_correct"] = np.where(valid, frame.whole_number_guess == frame.actual, np.nan)
    if "simulation_p10" in frame and "simulation_p90" in frame:
        valid = frame.actual.notna() & frame.simulation_p10.notna() & frame.simulation_p90.notna()
        frame["inside_p10_p90"] = np.where(valid,
            frame.actual.between(frame.simulation_p10, frame.simulation_p90), np.nan)
    return frame


def summarize_errors(frame, mean_column, groups=("issue_timing", "model", "category")):
    rows = []
    for key, group in frame.groupby(list(groups), dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        valid = group.actual.notna() & group[mean_column].notna()
        g = group[valid]
        error = g[mean_column] - g.actual
        exact = g["exact_guess_correct"].dropna() if "exact_guess_correct" in g else pd.Series(dtype=float)
        intervals = g["inside_p10_p90"].dropna() if "inside_p10_p90" in g else pd.Series(dtype=float)
        rows.append(dict(zip(groups, key), forecast_rows=len(group), rows_scored=len(g),
            games_scored=g.game_id.nunique(), predicted_total=g[mean_column].sum() if len(g) else np.nan,
            actual_total=g.actual.sum() if len(g) else np.nan, mae=error.abs().mean(),
            bias=error.mean(), rmse=np.sqrt((error ** 2).mean()), exact_guess_rows=len(exact),
            exact_guess_rate=exact.mean(), interval_rows=len(intervals),
            interval_p10_p90_coverage=intervals.mean()))
    return pd.DataFrame(rows)


def score_players(forecasts, skaters):
    require(not forecasts.duplicated(["game_id", "player_id", "model", "category"]).any(),
            "Duplicate player forecast")
    require(not skaters.duplicated(["game_id", "player_id"]).any(), "Duplicate actual skater")
    require(set(forecasts.category) <= set(CATEGORIES), "Unknown player category")
    validate_timing(forecasts)
    observed = skaters[skaters.toi_seconds > 0]
    actual = observed.melt(id_vars=["game_id", "player_id"], value_vars=CATEGORIES,
                           var_name="category", value_name="actual")
    result = forecasts.drop(columns=["actual", "absolute_error"], errors="ignore").merge(actual,
        on=["game_id", "player_id", "category"], how="left", validate="many_to_one")
    result = result.merge(observed[["game_id", "player_id", "toi_seconds"]].rename(
        columns={"toi_seconds": "actual_toi_seconds"}), on=["game_id", "player_id"],
        how="left", validate="many_to_one")
    result["actual_status"] = np.where(result.actual.notna(), "positive_toi_appearance",
                                      "no_positive_toi_appearance_not_scored")
    result = add_errors(result, "model_projection_if_plays")
    return result, summarize_errors(result, "model_projection_if_plays")


def score_teams(forecasts, skaters, boxes):
    validate_timing(forecasts)
    require(not forecasts.duplicated(["game_id", "team", "model", "category"]).any(),
            "Duplicate team forecast")
    observed = skaters[skaters.toi_seconds > 0]
    totals = observed.groupby(["game_id", "team"])[CATEGORIES].sum()
    result = forecasts.copy()
    result["actual_skater_sum"] = [totals.loc[(r.game_id, r.team), r.category]
                                   for r in result.itertuples()]
    official = {}
    for gid, box in boxes.items():
        for own, opp in [("homeTeam", "awayTeam"), ("awayTeam", "homeTeam")]:
            official[(gid, box[own]["abbrev"])] = dict(shots=box[own]["sog"],
                                                       shots_against=box[opp]["sog"])
    result["actual"] = [official[(r.game_id, r.team)]["shots"] if r.category == "shots"
                        else r.actual_skater_sum for r in result.itertuples()]
    result["actual_team_shots_against"] = [official[(r.game_id, r.team)]["shots_against"]
                                           for r in result.itertuples()]
    result["actual_population"] = np.where(result.category.eq("shots"), "official_nhl_team_sog",
        "all_positive_toi_skaters_including_unmodeled_excluding_shootout_deciding_goal")
    result = add_errors(result, "projection_mean")
    return result, summarize_errors(result, "projection_mean")


def score_goalies(forecasts, actuals):
    validate_timing(forecasts)
    require(not forecasts.duplicated(["game_id", "player_id", "model"]).any(), "Duplicate goalie forecast")
    require(not actuals.duplicated(["game_id", "player_id"]).any(), "Duplicate actual goalie")
    actual_columns = ["shots_against", "saves", "goals_against", "wins", "gaa", "save_percentage",
                      "starter", "toi_seconds", "count_identity_ok"]
    actual = actuals[["game_id", "player_id"] + actual_columns].rename(
        columns={c: "actual_" + c for c in actual_columns})
    result = forecasts.drop(columns=["actual_" + c for c in actual_columns], errors="ignore").merge(
        actual, on=["game_id", "player_id"], how="left", validate="many_to_one")
    known_starters = {}
    for key, group in actuals.groupby(["game_id", "team"]):
        starters = group[group.starter.eq(True)]
        require(len(starters) <= 1, "Multiple reported starting goalies for one team")
        if len(starters) == 1:
            known_starters[key] = int(starters.iloc[0].player_id)
    result["observed_in_boxscore"] = result.actual_toi_seconds.notna()
    # A known starter identifies every other candidate as a non-starter, even
    # when that candidate did not dress. Production remains missing for them.
    result["actual_starter"] = [float(int(r.player_id) == known_starters[(r.game_id, r.team)])
        if (r.game_id, r.team) in known_starters else np.nan for r in result.itertuples()]
    result["actual_toi_minutes"] = result.actual_toi_seconds / 60
    positive = result.actual_toi_seconds.gt(0)
    result["actual_role"] = np.select([result.actual_starter.eq(1), positive,
        result.observed_in_boxscore], ["starter", "relief", "unused_backup"], default="not_in_boxscore")
    result["eligible_for_conditional_count_scoring"] = positive & result.actual_count_identity_ok.eq(True)
    result["starter_55_to_65_minutes"] = (result.actual_starter.eq(1) &
        result.actual_toi_minutes.between(55, 65) & result.eligible_for_conditional_count_scoring)
    result["duration_comparison_status"] = "frozen_full_60_prediction_actual_duration_varies"
    metrics = []
    scopes = {
        "actual_starters": result.actual_starter.eq(1) & result.eligible_for_conditional_count_scoring,
        "starters_55_to_65_minutes": result.starter_55_to_65_minutes,
        "relief_appearances": result.actual_role.eq("relief") & result.eligible_for_conditional_count_scoring,
    }
    for category in ["shots_against", "saves", "goals_against"]:
        result[category + "_absolute_error"] = (result[category + "_if_full_start"] -
            result["actual_" + category]).abs().where(result.eligible_for_conditional_count_scoring)
        for scope, selected in scopes.items():
            g = result[selected].copy()
            if g.empty:
                continue
            g["category"] = category
            g["actual"] = g["actual_" + category]
            g["prediction"] = g[category + "_if_full_start"]
            g["simulation_p10"] = g[category + "_simulation_p10"]
            g["simulation_p90"] = g[category + "_simulation_p90"]
            scored = summarize_errors(add_errors(g, "prediction"), "prediction")
            scored["population"] = scope
            metrics.append(scored)
    start_rows = []
    for (timing, model, gid, team), g in result.groupby(["issue_timing", "model", "game_id", "team"]):
        starter = known_starters.get((gid, team))
        probs = g.start_share_provisional.to_numpy(dtype=float)
        complete = np.isfinite(probs).all() and np.isclose(probs.sum(), 1)
        target = g.player_id.eq(starter).to_numpy(dtype=float) if starter else None
        represented = starter is not None and starter in set(g.player_id)
        # Include a missing observed starter as an omitted class with forecast
        # probability zero. This penalizes roster coverage rather than dropping
        # the difficult team from the starter evaluation.
        omitted_loss = 0 if represented else 1
        row = dict(issue_timing=timing, model=model, game_id=gid, team=team,
                   candidates=len(g), actual_starter_id=starter,
                   actual_starter_in_candidates=represented,
                   probability_sum=float(probs.sum()) if complete else np.nan,
                   scoring_status="scored" if starter and complete else "unknown_starter_or_probability")
        if starter and complete:
            actual_prob = float(probs[target.astype(bool)][0]) if represented else 0.
            row.update(brier_score=float(np.square(probs - target).sum() + omitted_loss),
                       uniform_candidate_brier_score=float(np.square(1 / len(g) - target).sum() + omitted_loss),
                       actual_starter_probability=actual_prob,
                       log_loss=float(-np.log(actual_prob)) if actual_prob > 0 else np.inf)
        start_rows.append(row)
    return result, pd.concat(metrics, ignore_index=True) if metrics else pd.DataFrame(), pd.DataFrame(start_rows)


def coverage_table(source, wide, skaters, goalies):
    rows = []
    observed = skaters[skaters.toi_seconds > 0]
    for row in source.to_dict("records"):
        gid, team = row["game_id"], row["team"]
        actual = observed[(observed.game_id == gid) & (observed.team == team)]
        candidates = wide[(wide.game_id == gid) & (wide.team == team)]
        modeled_ids = set(candidates.player_id)
        selected_ids = set(candidates[candidates.selected_for_trial.eq(True)].player_id)
        actual_ids = set(actual.player_id)
        gs = goalies[(goalies.game_id == gid) & (goalies.team == team)]
        row.update(actual_skaters=len(actual_ids), actual_skaters_with_forecast=len(actual_ids & modeled_ids),
                   actual_skaters_without_forecast=len(actual_ids - modeled_ids),
                   missing_actual_skater_ids=";".join(map(str, sorted(actual_ids - modeled_ids))),
                   selected_lineup_actual_overlap=len(actual_ids & selected_ids),
                   selected_identified_nonparticipants=len(selected_ids - actual_ids),
                   modeled_nonparticipants=len(modeled_ids - actual_ids),
                   actual_goalie_appearances=gs[gs.actual_toi_seconds.gt(0)].player_id.nunique(),
                   forecast_goalies_observed_in_boxscore=gs[gs.observed_in_boxscore].player_id.nunique(),
                   goalie_count_exceptions=gs[gs.actual_toi_seconds.gt(0) &
                       ~gs.actual_count_identity_ok.eq(True)].player_id.nunique())
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate(bundle, actuals, boxscores, output_root):
    bundle, actuals, boxscores, output_root = map(Path, [bundle, actuals, boxscores, output_root])
    manifest, hash_audit = verify_inputs(bundle, actuals, boxscores)
    frozen_hash = digest(bundle / "manifest.json")
    player_forecasts = pd.read_csv(bundle / "simulation_summary.csv")
    ids = set(player_forecasts.game_id)
    require(len(ids) == manifest["games"], "Bundle game count mismatch")
    sk = pd.read_csv(actuals / "skater_game_stats.csv")
    gl = pd.read_csv(actuals / "goalie_game_stats.csv")
    require(ids <= set(sk.game_id) and ids <= set(gl.game_id), "Actuals do not cover all forecast games")
    sk, gl = sk[sk.game_id.isin(ids)].copy(), gl[gl.game_id.isin(ids)].copy()
    require(sk.game_date.eq(manifest["date"]).all() and gl.game_date.eq(manifest["date"]).all(),
            "Actual game dates disagree with forecast date")
    boxes = {int(gid): json.loads((boxscores / f"boxscore_{gid}.json").read_text()) for gid in ids}
    for gid, box in boxes.items():
        require(box["id"] == gid and box["gameType"] == 2 and box["gameState"] in ["OFF", "FINAL"],
                "Expected final regular-season boxscore")
        require(box["gameDate"] == manifest["date"] and box["season"] == int(str(gid)[:4] + str(int(str(gid)[:4]) + 1)),
                "Boxscore season/date mismatch")
        require(set(sk[sk.game_id.eq(gid)].team) == {box["homeTeam"]["abbrev"], box["awayTeam"]["abbrev"]},
                "Actual team coverage mismatch")
    players, pm = score_players(player_forecasts, sk)
    fantasy = players[players.fantasy_team_name.fillna("").astype(str).str.strip().ne("")]
    fantasy_metrics = summarize_errors(fantasy, "model_projection_if_plays")
    teams, tm = score_teams(pd.read_csv(bundle / "team_projected_vs_actual.csv"), sk, boxes)
    goalies, gm, starts = score_goalies(pd.read_csv(bundle / "goalie_projections.csv"), gl)
    wide = pd.read_csv(bundle / "player_projections.csv")
    actual_wide = sk[sk.toi_seconds > 0][["game_id", "player_id"] + CATEGORIES].rename(
        columns={c: "actual_" + c for c in CATEGORIES})
    wide = wide.merge(actual_wide, on=["game_id", "player_id"], how="left", validate="many_to_one")
    for category in CATEGORIES:
        wide[category + "_absolute_error"] = (wide["expected_" + category + "_if_plays"] - wide["actual_" + category]).abs()
    coverage = coverage_table(pd.read_csv(bundle / "game_team_coverage.csv"), wide, sk, goalies)
    modeled = players[["game_id", "player_id"]].drop_duplicates().assign(has_forecast=True)
    unmodeled = sk[sk.toi_seconds > 0].merge(modeled, on=["game_id", "player_id"], how="left", validate="one_to_one")
    unmodeled = unmodeled[unmodeled.has_forecast.isna()].drop(columns="has_forecast")
    game_timing = players[["game_id", "issue_timing"]].drop_duplicates()
    require(not game_timing.game_id.duplicated().any(), "Mixed skater timing within game")
    unmodeled = unmodeled.merge(game_timing, on="game_id", how="left", validate="many_to_one")
    team_wide = pd.read_csv(bundle / "team_projections.csv")
    values = teams.pivot(index=["game_id", "team", "model"], columns="category", values="actual").add_prefix("actual_").reset_index()
    team_wide = team_wide.merge(values, on=["game_id", "team", "model"], validate="one_to_one")
    for category in sorted(teams.category.unique()):
        team_wide[category + "_absolute_error"] = (team_wide["expected_" + category] - team_wide["actual_" + category]).abs()
    against = teams[["game_id", "team", "actual_team_shots_against"]].drop_duplicates()
    team_wide = team_wide.merge(against, on=["game_id", "team"], validate="many_to_one")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = output_root / f"daily_evaluation_{manifest['date']}_{stamp}"
    require(not out.resolve().is_relative_to(bundle.resolve()), "Evaluation output must be outside frozen bundle")
    out.mkdir(parents=True, exist_ok=False)
    frames = dict(simulation_summary=players, player_projections=wide, player_metrics=pm,
                  fantasy_player_metrics=fantasy_metrics,
                  team_projected_vs_actual=teams, team_projections=team_wide, team_metrics=tm,
                  goalie_projections=goalies, goalie_metrics=gm, goalie_starter_scores=starts,
                  game_team_coverage=coverage, unmodeled_actual_skaters=unmodeled, source_hash_audit=hash_audit)
    for name, frame in frames.items():
        frame.to_csv(out / (name + ".csv"), index=False)
    require(digest(bundle / "manifest.json") == frozen_hash, "Frozen bundle changed during evaluation")
    verify_manifest_files(bundle, [])
    evaluated = dict(evaluated_at_utc=datetime.now(timezone.utc).isoformat(), date=manifest["date"],
        frozen_bundle=str(bundle), frozen_bundle_manifest_sha256=frozen_hash,
        actuals=str(actuals), actuals_manifest_sha256=digest(actuals / "manifest.json"),
        boxscores=str(boxscores), boxscores_metadata_sha256=digest(boxscores / "metadata.json"),
        games=len(ids), game_issue_timing=game_timing.to_dict("records"),
        source_hash_exceptions=hash_audit[hash_audit.status.ne("verified")].to_dict("records"),
        scoring_notes=["Pregame and late rows scored separately; no pooled headline metrics.",
            "Player means scored only against positive-TOI appearances; absent players retain missing outcomes.",
            "Team SOG is official NHL boxscore SOG; other team categories sum all positive-TOI skaters.",
            "Goalie primary count metrics use actual starters with consistent counts, and include variable actual duration.",
            "55-65-minute starter and relief subsets are separate; unused backups retain observations but no count score.",
            "Starter Brier is the summed multiclass score per team-game; missing starters receive probability zero.",
            "Expected intervals remain uncalibrated; this evaluation does not tune or promote models."],
        files={p.name: digest(p) for p in out.glob("*.csv")},
        evaluation_code_sha256=digest(Path(__file__)))
    (out / "manifest.json").write_text(json.dumps(evaluated, indent=2) + "\n")
    (out / "README.md").write_text(f"# {manifest['date']} forecast results\n\n"
        "Start with player_projections.csv, team_projections.csv and goalie_projections.csv. "
        "Filter issue_timing=pregame for the prospective comparison; late_not_pregame is separate.\n\n"
        "Player/team metrics compare identical available observations across frozen models. "
        "Missing player actuals mean no positive-TOI appearance, not a scored zero. "
        "Check game_team_coverage.csv for missing players and lineup overlap. "
        "Goalie metrics separate actual starters, 55–65-minute starts and relief; full-60 assumptions remain provisional.\n\n"
        f"Frozen source: `{bundle}`. Actuals: `{actuals}`. "
        "Source hashes and any historical provenance exceptions are in source_hash_audit.csv and manifest.json.\n")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--actuals", type=Path, required=True)
    parser.add_argument("--boxscores", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("data/processed/forecasts"))
    args = parser.parse_args()
    out = evaluate(args.bundle, args.actuals, args.boxscores, args.output_root)
    print("Evaluated bundle:", out)
    metrics = pd.read_csv(out / "player_metrics.csv")
    print(metrics[metrics.category.eq("shots")][["issue_timing", "model", "rows_scored", "mae", "bias"]].to_string(index=False))


if __name__ == "__main__":
    main()
