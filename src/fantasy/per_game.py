"""Interpretable skater forecasts: opportunity x event rate, with visible shrinkage.

Season aggregates support a conditional per-game mean, not game-specific
availability, opponent effects, or a calibrated predictive distribution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

EVENTS = ["goals", "assists", "shots", "hits", "penalty_minutes", "pp_points", "plus_minus"]
TARGETS = EVENTS + ["points", "toi_minutes"]
COUNTS = ["games_played", "goals", "assists", "points", "shots", "hits", "penalty_minutes", "pp_points"]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def latest_snapshot(root: Path, season: int) -> Path:
    paths = sorted(root.glob(f"fantasy_{season}_*"))
    require(bool(paths), f"No fantasy NHL snapshot for {season}; run the R refresh first")
    return paths[-1]


def load_season(path: Path, season: int):
    """Verify provenance and full source populations before any model filtering."""
    suffix = f"{str(season)[:4]}_{str(season)[6:]}"
    frames, provenance, audits = {}, [], []
    for report, stem in [("summary", "nhl_skaters"), ("toi", "nhl_skaters_toi"),
                         ("realtime", "nhl_skaters_realtime")]:
        file = path / f"{stem}_{suffix}.csv"
        metadata = json.loads(Path(str(file) + ".metadata.json").read_text())
        require(hashlib.md5(file.read_bytes()).hexdigest() == metadata["md5"], f"Hash mismatch: {file}")
        require(int(metadata["season_id"]) == season and metadata["game_type"] == 2,
                f"Unexpected season/game type: {file}")
        require(metadata["population"] == "skater" and not metadata["isGame"], "Unexpected population")
        x = pd.read_csv(file)
        require(len(x) == metadata["api_total"] == metadata["rows"], f"Incomplete population: {file}")
        require(sum(page["rows"] for page in metadata["pages"]) == len(x), "Incomplete pagination log")
        require(not x.player_id.isna().any() and not x.player_id.duplicated().any(), "Invalid player IDs")
        require((x.player_id > 0).all() and (x.player_id % 1 == 0).all(), "Invalid player ID values")
        require((x.season_id == season).all(), "Mixed seasons")
        require(x.position_code.isin(["C", "L", "R", "D"]).all(), "Invalid skater position")
        require(np.isfinite(x.games_played).all() and (x.games_played >= 1).all()
                and (x.games_played % 1 == 0).all(), "Invalid GP")
        for col in x:
            numeric = pd.api.types.is_numeric_dtype(x[col])
            audits.append(dict(season_id=season, report=report, column=col, rows=len(x),
                               missing=int(x[col].isna().sum()),
                               minimum=x[col].min() if numeric else None,
                               maximum=x[col].max() if numeric else None))
        frames[report] = x.set_index("player_id")
        provenance.append(dict(file=str(file), md5=metadata["md5"], rows=len(x),
                               retrieved_at_utc=metadata["completed_at_utc"], season_id=season,
                               game_type=2, source=metadata["source"]))
    s, t, r = (frames[k] for k in ["summary", "toi", "realtime"])
    for other in [t, r]:
        require(set(s.index) == set(other.index), "Report populations disagree; do not silently drop players")
        require((s.games_played == other.reindex(s.index).games_played).all(), "Report GP disagree")
    t, r = t.reindex(s.index), r.reindex(s.index)
    for col in COUNTS:
        values = r[col] if col == "hits" else s[col]
        require(np.isfinite(values).all() and (values >= 0).all() and (values % 1 == 0).all(),
                f"Invalid count: {col}")
    require((s.points == s.goals + s.assists).all(), "G+A != P")
    require((s.goals <= s.shots).all(), "Goals exceed shots")
    require((s.pp_points <= s.points).all(), "PPP exceed points")
    require(np.isfinite(s.plus_minus).all(), "Missing/nonfinite plus-minus")
    for col in ["time_on_ice", "ev_time_on_ice", "pp_time_on_ice", "sh_time_on_ice"]:
        require(np.isfinite(t[col]).all() and (t[col] >= 0).all(), f"Invalid {col}")
    require((t.time_on_ice > 0).all(), "Zero TOI")
    require(np.allclose(t.time_on_ice, t.ev_time_on_ice + t.pp_time_on_ice + t.sh_time_on_ice,
                        atol=.01, rtol=0), "TOI components disagree")
    for average in [s.time_on_ice_per_game, t.time_on_ice_per_game]:
        require(np.allclose(average, t.time_on_ice / s.games_played, atol=.01, rtol=0), "TOI/GP mismatch")
    s = s.copy()
    s["hits"] = r.hits
    s["toi_minutes"] = t.time_on_ice / 60
    s["pp_toi_minutes"] = t.pp_time_on_ice / 60
    s["position_group"] = np.where(s.position_code == "D", "D", "F")
    s["source_snapshot"] = str(path)
    return s.reset_index(), provenance, audits


def forecast(panel, target_season, *, method="process", decay=.75, event_prior_games=20,
             shooting_prior_shots=200, toi_prior_games=10, lookback=3, include_current=False):
    """Only seasons strictly before target train priors, even with a live update.

No age/injury/role effects are invented. Retain every player with history in the
window. A player with only current-season history receives past position priors.
    """
    year = target_season // 10000
    start_year = panel.season_id // 10000
    hist = panel[(start_year >= year - lookback) & (panel.season_id < target_season)].copy()
    require(not hist.empty, "No pre-target history")
    hist["weight"] = decay ** (year - 1 - hist.season_id // 10000)
    obs = hist.copy()
    if include_current:
        current = panel[panel.season_id == target_season].copy()
        current["weight"] = 1.0
        obs = pd.concat([obs, current], ignore_index=True)
    latest = obs.sort_values("season_id").drop_duplicates("player_id", keep="last").set_index("player_id")
    out = latest[["skater_full_name", "position_code", "position_group", "team_abbrevs", "season_id"]].copy()
    out = out.rename(columns={"season_id": "last_observed_season", "team_abbrevs": "last_observed_teams"})
    out["forecast_season"] = target_season
    out["history_seasons"] = hist.groupby("player_id").size().reindex(out.index).fillna(0).astype(int)
    out["historical_gp"] = hist.groupby("player_id").games_played.sum().reindex(out.index).fillna(0)
    out["current_gp"] = obs[obs.season_id == target_season].set_index("player_id").games_played.reindex(out.index).fillna(0)
    out["evidence"] = np.select([out.historical_gp == 0, out.historical_gp < 40],
                                 ["no_completed_season_history", "sparse_history"], default="established_history")
    # These labels describe coverage; 40 GP is only a reporting stratum, never an exclusion.
    values = ["games_played", "toi_minutes"] + EVENTS
    weighted = obs[values].mul(obs.weight, axis=0).groupby(obs.player_id).sum().reindex(out.index)
    prior_totals = hist[values].mul(hist.weight, axis=0).groupby(hist.position_group).sum()
    priors = prior_totals.reindex(out.position_group).set_axis(out.index)
    require(not priors.isna().any().any(), "Position prior unavailable")
    prior_toi = priors.toi_minutes / priors.games_played
    prior_shots = priors.shots / priors.games_played
    out["weighted_gp"] = weighted.games_played
    out["weighted_toi_minutes"] = weighted.toi_minutes
    if method == "last_season":
        # Use the most recent *completed* season. Old history is an explicit stale fallback.
        previous = hist.sort_values("season_id").drop_duplicates("player_id", keep="last").set_index("player_id")
        previous = previous.reindex(out.index)
        for event in EVENTS + ["toi_minutes"]:
            out[f"{event}_per_game"] = (previous[event] / previous.games_played).fillna(priors[event] / priors.games_played)
        out["fallback"] = np.where(previous.games_played.isna(), "past_position_prior", "most_recent_completed_season")
    elif method == "weighted":
        for event in EVENTS + ["toi_minutes"]:
            out[f"{event}_per_game"] = weighted[event] / weighted.games_played
        out["fallback"] = "none"
    else:
        require(method == "process", f"Unknown method {method}")
        # Pseudo-exposure encodes how strongly to regress toward past F/D averages.
        pseudo_minutes = event_prior_games * prior_toi
        minutes = (weighted.toi_minutes + toi_prior_games * prior_toi) / (weighted.games_played + toi_prior_games)
        out["toi_minutes_per_game"] = minutes
        out["toi_observed_weight"] = weighted.games_played / (weighted.games_played + toi_prior_games)
        out["event_observed_weight"] = weighted.toi_minutes / (weighted.toi_minutes + pseudo_minutes)
        for event in EVENTS:
            if event == "goals":
                continue
            prior_rate = priors[event] / priors.toi_minutes
            rate = (weighted[event] + pseudo_minutes * prior_rate) / (weighted.toi_minutes + pseudo_minutes)
            out[f"{event}_per_60"] = 60 * rate
            out[f"{event}_per_game"] = rate * minutes
        prior_conversion = priors.goals / priors.shots
        denom = weighted.shots + shooting_prior_shots
        conversion = ((weighted.goals + shooting_prior_shots * prior_conversion) / denom).where(denom > 0, prior_conversion)
        out["shooting_probability"] = conversion
        out["shooting_observed_weight"] = (weighted.shots / denom).where(denom > 0, 0)
        out["goals_per_game"] = out.shots_per_game * conversion
        out["goals_per_60"] = out.shots_per_60 * conversion
        out["position_prior_toi_per_game"] = prior_toi
        out["position_prior_shots_per_game"] = prior_shots
        out["position_prior_shooting_probability"] = prior_conversion
        out["fallback"] = "past_position_shrinkage"
    out["points_per_game"] = out.goals_per_game + out.assists_per_game
    out["method"] = method
    out["includes_current_season"] = include_current
    require(np.isfinite(out[[f"{e}_per_game" for e in TARGETS]]).all().all(), "Nonfinite forecast")
    return out.reset_index()


def evaluate(prediction, panel, target_season):
    """Preserve nonreturners; per-game targets are undefined when target GP is zero.

Absence means no reported appearance in a fully retrieved regular-season table,
not proof of retirement or a retrospectively known preseason roster.
    """
    actual = panel[panel.season_id == target_season][["player_id", "games_played"] + TARGETS]
    scored = prediction.merge(actual, on="player_id", how="left", validate="one_to_one")
    scored["target_appearance_status"] = np.where(scored.games_played.isna(), "no_reported_appearance", "appeared")
    scored["target_gp"] = scored.games_played.fillna(0)
    coverage = dict(target_season=target_season, prior_known_players=len(prediction),
                    appeared=int(scored.games_played.notna().sum()),
                    no_reported_appearance=int(scored.games_played.isna().sum()),
                    entrants_without_history=int((~actual.player_id.isin(prediction.player_id)).sum()))
    rows = []
    groups = [("all", scored)]
    groups += [(f"position_{key}", group) for key, group in scored.groupby("position_group")]
    groups += [(str(key), group) for key, group in scored.groupby("evidence")]
    for group_name, group in groups:
        group = group[group.games_played.notna()]
        if group.empty:
            continue
        for event in TARGETS:
            error = group[f"{event}_per_game"] - group[event] / group.games_played
            rows.append(dict(target_season=target_season, group=group_name, category=event,
                             players=len(group), games=int(group.games_played.sum()),
                             mae=float(error.abs().mean()), bias=float(error.mean()),
                             gp_weighted_mae=float(np.average(error.abs(), weights=group.games_played))))
    return pd.DataFrame(rows), scored, coverage
