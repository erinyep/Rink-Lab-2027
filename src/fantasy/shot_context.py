"""Past-only team shot context for explicitly experimental pregame forecasts.

Raw NHL SOG and MoneyPuck xOnGoal are distinct measurements. The latter is a
description of observed unblocked attempts; only lagged aggregates are used.
No weights here were selected using October 9 outcomes. Missing context is
visible and has a neutral effect on a forecast.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .per_game import require

TEAM_ALIASES = {"T.B": "TBL", "L.A": "LAK", "S.J": "SJS", "N.J": "NJD"}
CHANCE_METRICS = {
    "xongoal_for": "xOnGoalFor", "xongoal_against": "xOnGoalAgainst",
    "attempts_for": "shotAttemptsFor", "attempts_against": "shotAttemptsAgainst",
    "unblocked_for": "unblockedShotAttemptsFor",
    "unblocked_against": "unblockedShotAttemptsAgainst",
    "xgoals_for": "xGoalsFor", "xgoals_against": "xGoalsAgainst",
}


def load_nhl_team_games(snapshot_paths):
    """Read final regular-season boxscores and verify available source hashes.

    Overlapping snapshots are allowed only when the team totals agree. The
    caller records source paths/hashes in its forecast manifest. This helper
    does not claim that a schedule archive is complete merely from its rows.
    """
    rows = []
    if isinstance(snapshot_paths, (str, Path)):
        snapshot_paths = [snapshot_paths]
    for root in map(Path, snapshot_paths):
        metadata = json.loads((root / "metadata.json").read_text())
        sources = metadata.get("sources", [])
        for source in sources:
            if not source["file"].startswith("boxscore_"):
                continue
            payload = (root / source["file"]).read_bytes()
            require(hashlib.sha256(payload).hexdigest() == source["sha256"],
                    "NHL team-context boxscore hash mismatch")
            box = json.loads(payload)
            if box["gameType"] != 2 or box["gameState"] not in {"OFF", "FINAL"}:
                continue
            for own, opposing in [("homeTeam", "awayTeam"), ("awayTeam", "homeTeam")]:
                rows.append(dict(game_id=box["id"], game_date=box["gameDate"],
                                 season_id=box["season"], team=box[own]["abbrev"],
                                 opponent=box[opposing]["abbrev"], sf=box[own]["sog"],
                                 sa=box[opposing]["sog"]))
    columns = ["game_id", "game_date", "season_id", "team", "opponent", "sf", "sa"]
    frame = pd.DataFrame(rows, columns=columns).drop_duplicates()
    require(not frame.duplicated(["game_id", "team"]).any(),
            "Conflicting overlapping NHL boxscores")
    return frame


def _validate_pairs(frame, *, label, sf=None, sa=None):
    require(not frame.duplicated(["game_id", "team"]).any(), f"Duplicate {label} team-game")
    if frame.empty:
        return
    require(frame.groupby("game_id").size().eq(2).all(), f"Incomplete {label} game pairs")
    require(frame.groupby("game_id").game_date.nunique().eq(1).all(),
            f"Conflicting {label} game dates")
    reverse = frame.rename(columns={"team": "opponent", "opponent": "team"})
    paired = frame.merge(reverse, on=["game_id", "team", "opponent"],
                         suffixes=("", "_opponent"), validate="one_to_one")
    require(len(paired) == len(frame) and (frame.team != frame.opponent).all(),
            f"Invalid {label} opponents")
    if sf and sa:
        require(np.allclose(paired[sf], paired[sa + "_opponent"], atol=.002, rtol=0),
                f"Inconsistent {label} for/against pairs")


def _prepare_moneypuck(frame, cutoff, start_year):
    required = {"team", "opposingTeam", "season", "gameId", "gameDate", "situation",
                "playoffGame", "iceTime", "shotsOnGoalFor", "shotsOnGoalAgainst"}
    require(required <= set(frame), "Missing MoneyPuck team-game columns")
    result = frame.copy()
    result["game_date"] = pd.to_datetime(result.gameDate.astype(str), format="%Y%m%d")
    result = result[(result.game_date < cutoff) & result.season.isin([start_year - 1, start_year])
                    & result.playoffGame.eq(0) & result.situation.isin(["all", "5on5"])].copy()
    result = result.rename(columns={"gameId": "game_id", "opposingTeam": "opponent"})
    for col in ["team", "opponent"]:
        result[col] = result[col].replace(TEAM_ALIASES)
    require((result.game_id // 1000000 == result.season).all(), "MoneyPuck season mismatch")
    require(((result.game_id // 10000) % 100 == 2).all(), "MoneyPuck non-regular-season ID")
    require(not result.duplicated(["game_id", "team", "situation"]).any(),
            "Duplicate MoneyPuck team-game situation")
    for situation, group in result.groupby("situation"):
        _validate_pairs(group, label=f"MoneyPuck {situation}",
                        sf="shotsOnGoalFor", sa="shotsOnGoalAgainst")
    numeric = ["iceTime", "shotsOnGoalFor", "shotsOnGoalAgainst"]
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="raise")
        require(np.isfinite(result[column]).all() and result[column].ge(0).all(),
                f"Invalid MoneyPuck {column}")
    # Some source versions omit chance fields. Preserve that missingness instead
    # of claiming a zero count or silently substituting raw shots.
    for column in CHANCE_METRICS.values():
        if column not in result:
            result[column] = np.nan
        result[column] = pd.to_numeric(result[column], errors="raise")
        require((result[column].isna() | (np.isfinite(result[column]) & result[column].ge(0))).all(),
                f"Invalid MoneyPuck {column}")
    return result


def build_shot_context(nhl_games, moneypuck_games, target_date, season_id,
                       teams=None, prior_games=20):
    """Return per-team lagged rates, exposure counts and source-quality flags.

    A fixed twenty-game prior uses previous-season team SOG per game, and
    previous-season team 5v5 chance rates per 60 minutes. Its 5v5 exposure is
    twenty previous-season *league-average* 5v5 game durations. A missing team
    prior falls back to the previous-season league. Current MoneyPuck games
    without NHL corroboration or with shot-count disagreement are excluded
    from chance features as whole games, with counts retained in the output.

    This date cutoff deliberately excludes all target-date games, including
    earlier games on that day. Actual issue/source times remain caller duties.
    """
    require(np.isfinite(prior_games) and prior_games > 0, "Invalid context prior games")
    cutoff = pd.Timestamp(date.fromisoformat(str(target_date)))
    start_year = int(season_id) // 10000
    require(int(season_id) == start_year * 10000 + start_year + 1, "Invalid NHL season ID")
    nhl = nhl_games.copy()
    nhl["game_date"] = pd.to_datetime(nhl.game_date)
    nhl = nhl[(nhl.game_date < cutoff) & nhl.season_id.eq(season_id)].copy()
    require((nhl.game_id // 1000000 == start_year).all(), "NHL game season mismatch")
    require(((nhl.game_id // 10000) % 100 == 2).all(), "NHL non-regular-season ID")
    for column in ["sf", "sa"]:
        nhl[column] = pd.to_numeric(nhl[column], errors="raise")
        require(np.isfinite(nhl[column]).all() and nhl[column].ge(0).all()
                and nhl[column].mod(1).eq(0).all(), f"Invalid NHL {column}")
    _validate_pairs(nhl, label="NHL", sf="sf", sa="sa")
    mp = _prepare_moneypuck(moneypuck_games, cutoff, start_year)
    prior = mp[mp.season.eq(start_year - 1)]
    prior_all = prior[prior.situation.eq("all")]
    prior_five = prior[prior.situation.eq("5on5") & prior.iceTime.gt(0)]
    current_all = mp[mp.season.eq(start_year) & mp.situation.eq("all")]
    audit = current_all.merge(nhl[["game_id", "team", "sf", "sa"]],
                              on=["game_id", "team"], how="left", validate="one_to_one")
    audit["nhl_missing"] = audit.sf.isna()
    audit["shot_discrepancy"] = (~audit.nhl_missing &
        ((audit.shotsOnGoalFor != audit.sf) | (audit.shotsOnGoalAgainst != audit.sa)))
    excluded_ids = set(audit.loc[audit.nhl_missing | audit.shot_discrepancy, "game_id"])
    allowed_ids = set(audit.game_id) - excluded_ids
    current_five = mp[mp.season.eq(start_year) & mp.situation.eq("5on5")
                      & mp.game_id.isin(allowed_ids) & mp.iceTime.gt(0)]
    league_sog = float(nhl.sf.mean()) if len(nhl) else np.nan
    prior_league_sog = float(prior_all.shotsOnGoalFor.mean()) if len(prior_all) else league_sog
    five_prior_seconds = prior_games * prior_five.iceTime.mean() if len(prior_five) else 0.
    # Prefer a stable past-season denominator; unavailable data yield NaN and
    # are handled explicitly by matchup_shot_factors.
    prior_rates = {}
    for name, source in CHANCE_METRICS.items():
        valid = prior_five[prior_five[source].notna()]
        prior_rates[name] = 3600 * valid[source].sum() / valid.iceTime.sum() if len(valid) else np.nan
    population = sorted(set(teams) if teams is not None else set(nhl.team) | set(mp.team))
    rows = []
    for team in population:
        current = nhl[nhl.team.eq(team)]
        past = prior_all[prior_all.team.eq(team)]
        chance = current_five[current_five.team.eq(team)]
        old_chance = prior_five[prior_five.team.eq(team)]
        check = audit[audit.team.eq(team)]
        latest = current.game_date.max() if len(current) else pd.NaT
        row = dict(team=team, season_id=season_id, target_date=str(target_date),
                   history_cutoff_exclusive=str(target_date), nhl_games=len(current),
                   latest_nhl_game_date=latest.strftime("%Y-%m-%d") if pd.notna(latest) else None,
                   days_since_last_game=(cutoff - latest).days if pd.notna(latest) else np.nan,
                   back_to_back=(cutoff - latest).days == 1 if pd.notna(latest) else None,
                   prior_games=prior_games, prior_season_team_games=len(past),
                   prior_sog_source=("moneypuck_previous_regular_season" if len(past) else
                       "moneypuck_previous_regular_season_league_fallback" if len(prior_all) else
                       "nhl_current_league_fallback"),
                   prior_sog_not_nhl_reconciled=bool(len(prior_all)),
                   current_league_sog=league_sog, prior_league_sog=prior_league_sog,
                   missing_nhl_context=not len(current), missing_prior_team_context=not len(past),
                   moneypuck_current_games=len(check), moneypuck_5v5_games_used=len(chance),
                   moneypuck_shot_discrepancy_games=int(check.shot_discrepancy.sum()),
                   moneypuck_nhl_unmatched_games=int(check.nhl_missing.sum()),
                   moneypuck_missing_nhl_games=len(set(current.game_id) - set(check.game_id)),
                   moneypuck_excluded_current_game_ids=";".join(map(str, sorted(set(check.game_id) & excluded_ids))),
                   missing_current_5v5_context=not len(chance),
                   moneypuck_current_5v5_seconds=float(chance.iceTime.sum()),
                   prior_5v5_seconds=float(five_prior_seconds))
        for direction, source in [("sf", "shotsOnGoalFor"), ("sa", "shotsOnGoalAgainst")]:
            row[f"original_current_{direction}"] = ((current[direction].sum() + prior_games * league_sog)
                                                       / (len(current) + prior_games))
            prior_mean = past[source].mean() if len(past) else prior_league_sog
            row[f"prior_{direction}"] = prior_mean
            row[f"shrunken_{direction}"] = ((current[direction].sum() + prior_games * prior_mean)
                                              / (len(current) + prior_games))
        for name, source in CHANCE_METRICS.items():
            available_prior = old_chance[old_chance[source].notna()]
            prior_rate = (3600 * available_prior[source].sum() / available_prior.iceTime.sum()
                          if len(available_prior) else prior_rates[name])
            available = chance[chance[source].notna()]
            seconds = available.iceTime.sum()
            if np.isfinite(prior_rate) and five_prior_seconds > 0:
                rate = ((3600 * available[source].sum() + five_prior_seconds * prior_rate)
                        / (seconds + five_prior_seconds))
            else:
                rate = 3600 * available[source].sum() / seconds if seconds > 0 else np.nan
            row[f"{name}_5v5_per60"] = rate
            row[f"{name}_5v5_league_per60"] = prior_rates[name]
            row[f"{name}_current_games_used"] = len(available)
        rows.append(row)
    return pd.DataFrame(rows)


def matchup_shot_factors(context, team, opponent):
    """Return separate raw-SOG, xOnGoal and fixed 50/50 geometric trial factors.

    The original factor retains the October 9 NHL/current-season formula.
    The new raw factor uses previous-season team priors. The chance experiment
    blends this raw factor with a 5v5 xOnGoal factor. It is deliberately small
    and unvalidated; it does not assert that 5v5 equals all-strength behavior.
    """
    require(not context.team.duplicated().any(), "Duplicate team context")
    lookup = context.set_index("team")
    own = lookup.loc[team] if team in lookup.index else None
    other = lookup.loc[opponent] if opponent in lookup.index else None

    def factor(sf, sa, denominator, require_current=False):
        if own is None or other is None:
            return 1., True
        if require_current and (own.missing_nhl_context or other.missing_nhl_context):
            return 1., True
        values = [own.get(sf, np.nan), other.get(sa, np.nan), own.get(denominator, np.nan)]
        if not all(np.isfinite(v) and v > 0 for v in values):
            return 1., True
        return float(np.sqrt(values[0] * values[1]) / values[2]), False

    original, old_missing = factor("original_current_sf", "original_current_sa", "current_league_sog", True)
    raw, raw_missing = factor("shrunken_sf", "shrunken_sa", "prior_league_sog")
    chance, chance_missing = factor("xongoal_for_5v5_per60", "xongoal_against_5v5_per60",
                                     "xongoal_for_5v5_league_per60")
    # A missing chance source contributes neutral multiplicative evidence.
    # The blend therefore damps the raw factor when its second component is
    # missing; both statuses remain explicit for later ablation evaluation.
    blend = float(np.sqrt(raw * chance))
    return dict(original_current_sog_factor=original, prior_season_sog_factor=raw,
                xongoal_factor=chance, blended_sog_factor=blend,
                original_context_missing=old_missing, prior_context_missing=raw_missing,
                xongoal_context_missing=chance_missing,
                factor_status="experimental_fixed_weights_not_validated")
