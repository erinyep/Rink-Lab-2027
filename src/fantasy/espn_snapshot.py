"""Timestamped read-only ESPN Fantasy Hockey snapshot utilities.

The module intentionally persists normalized league data rather than raw ESPN
responses so that authentication cookies and private owner metadata are never
written to disk. Source data can be re-fetched from ESPN using the retrieval
timestamp and league/season identifiers recorded in metadata.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import platform
import re
import unicodedata
from typing import Any, Iterable

from espn_api.hockey.player import Player

from .espn_client import ESPNConfig, REPO_ROOT, connect_espn


DEFAULT_RAW_ROOT = REPO_ROOT / "data" / "raw" / "espn" / "snapshots"
DEFAULT_PROCESSED_ROOT = REPO_ROOT / "data" / "processed" / "espn"


@dataclass(frozen=True)
class SnapshotResult:
    raw_dir: Path
    processed_dir: Path
    metadata: dict[str, Any]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _team_id(team: Any) -> int | None:
    value = getattr(team, "team_id", None)
    return int(value) if value is not None else None


def _team_name(team: Any) -> str:
    value = getattr(team, "team_name", None)
    if value:
        return str(value)
    team_id = _team_id(team)
    return f"Team {team_id}" if team_id is not None else "Unknown team"


def _csv_value(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value if item not in (None, ""))
    return value


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> int:
    materialized = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in materialized:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})
    return len(materialized)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _player_row(player: Any) -> dict[str, Any]:
    return {
        "espn_player_id": getattr(player, "playerId", None),
        "player_name": getattr(player, "name", None),
        "primary_position": getattr(player, "position", None),
        "eligible_slots": getattr(player, "eligibleSlots", []) or [],
        "lineup_slot": getattr(player, "lineupSlot", None),
        "nhl_team": getattr(player, "proTeam", None),
        "injury_status": getattr(player, "injuryStatus", None),
        "injured": getattr(player, "injured", False),
        "acquisition_type": getattr(player, "acquisitionType", None),
    }


def _team_rows(league: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for team in league.teams:
        rows.append(
            {
                "team_id": _team_id(team),
                "team_abbrev": getattr(team, "team_abbrev", None),
                "team_name": _team_name(team),
                "division_id": getattr(team, "division_id", None),
                "division_name": getattr(team, "division_name", None),
                "wins": getattr(team, "wins", None),
                "losses": getattr(team, "losses", None),
                "ties": getattr(team, "ties", None),
                "standing": getattr(team, "standing", None),
                "final_standing": getattr(team, "final_standing", None),
                "roster_count": len(getattr(team, "roster", []) or []),
            }
        )
    return rows


def _roster_rows(league: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for team in league.teams:
        for player in getattr(team, "roster", []) or []:
            row = _player_row(player)
            row.update(
                {
                    "fantasy_team_id": _team_id(team),
                    "fantasy_team_name": _team_name(team),
                    "availability_status": "ROSTERED",
                }
            )
            rows.append(row)
    return rows


def _fetch_available_entries(league: Any, limit: int) -> list[dict[str, Any]]:
    """Fetch FREEAGENT and WAIVERS entries while preserving their status."""

    if limit < 1:
        raise ValueError("available-player limit must be >= 1")

    params = {
        "view": "kona_player_info",
        "scoringPeriodId": league.current_week,
    }
    filters = {
        "players": {
            "filterStatus": {"value": ["FREEAGENT", "WAIVERS"]},
            "filterSlotIds": {"value": []},
            "limit": limit,
            "sortPercOwned": {"sortPriority": 1, "sortAsc": False},
            "sortDraftRanks": {
                "sortPriority": 100,
                "sortAsc": True,
                "value": "STANDARD",
            },
        }
    }
    headers = {"x-fantasy-filter": json.dumps(filters)}
    data = league.espn_request.league_get(params=params, headers=headers)
    players = data.get("players", [])
    if not isinstance(players, list):
        raise RuntimeError("ESPN available-player response did not contain a player list")
    return players


def _available_rows(league: Any, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in _fetch_available_entries(league, limit):
        player = Player(entry)
        row = _player_row(player)

        pool = entry.get("playerPoolEntry", {}) if isinstance(entry, dict) else {}
        player_payload = pool.get("player", {}) if isinstance(pool, dict) else {}
        ownership = player_payload.get("ownership", {}) if isinstance(player_payload, dict) else {}

        row.update(
            {
                "availability_status": (
                    pool.get("status") if isinstance(pool, dict) else None
                )
                or (entry.get("status") if isinstance(entry, dict) else None)
                or "AVAILABLE",
                "percent_owned": ownership.get("percentOwned"),
                "percent_started": ownership.get("percentStarted"),
                "percent_change": ownership.get("percentChange"),
            }
        )
        rows.append(row)
    return rows


def _matchup_rows(league: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    matchups = league.scoreboard()
    summary_rows: list[dict[str, Any]] = []
    category_rows: list[dict[str, Any]] = []

    for index, matchup in enumerate(matchups, start=1):
        home = getattr(matchup, "home_team", None)
        away = getattr(matchup, "away_team", None)
        home_cats = getattr(matchup, "home_team_cats", None) or {}
        away_cats = getattr(matchup, "away_team_cats", None) or {}

        summary_rows.append(
            {
                "matchup_number": index,
                "matchup_period": getattr(league, "currentMatchupPeriod", None),
                "home_team_id": _team_id(home),
                "home_team_name": _team_name(home),
                "away_team_id": _team_id(away),
                "away_team_name": _team_name(away),
                "winner": getattr(matchup, "winner", None),
                "home_category_score": getattr(matchup, "home_team_live_score", None),
                "away_category_score": getattr(matchup, "away_team_live_score", None),
                "home_total_points": getattr(matchup, "home_final_score", None),
                "away_total_points": getattr(matchup, "away_final_score", None),
            }
        )

        for side, team, cats in (
            ("home", home, home_cats),
            ("away", away, away_cats),
        ):
            for category, payload in cats.items():
                details = payload if isinstance(payload, dict) else {}
                category_rows.append(
                    {
                        "matchup_number": index,
                        "matchup_period": getattr(league, "currentMatchupPeriod", None),
                        "side": side,
                        "team_id": _team_id(team),
                        "team_name": _team_name(team),
                        "category": category,
                        "score": details.get("score"),
                        "result": details.get("result"),
                    }
                )

    return summary_rows, category_rows


def _normalize_name(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("’", "'")
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def _first_present(row: dict[str, str], candidates: Iterable[str]) -> str | None:
    for candidate in candidates:
        value = row.get(candidate)
        if value not in (None, ""):
            return value
    return None


def _read_nhl_players(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _latest_file(pattern: str) -> Path | None:
    candidates = list((REPO_ROOT / "data" / "processed" / "fantasy").glob(pattern))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _nhl_index() -> tuple[dict[str, list[dict[str, str]]], list[str]]:
    source_files = [
        path
        for path in (
            _latest_file("*/historical_skaters.csv"),
            _latest_file("*/historical_goalies.csv"),
        )
        if path is not None
    ]
    index: dict[str, list[dict[str, str]]] = {}

    for path in source_files:
        for row in _read_nhl_players(path):
            name = _first_present(
                row,
                (
                    "skater_full_name",
                    "goalie_full_name",
                    "player_name",
                    "full_name",
                    "name",
                ),
            )
            player_id = _first_present(row, ("player_id", "playerId", "id"))
            team = _first_present(
                row,
                ("team_abbrevs", "team_abbrev", "team", "team_code"),
            )
            if not name or not player_id:
                continue
            candidate = {
                "nhl_player_id": player_id,
                "nhl_name": name,
                "nhl_team": team or "",
                "source_file": str(path.relative_to(REPO_ROOT)),
            }
            index.setdefault(_normalize_name(name), []).append(candidate)

    return index, [str(path.relative_to(REPO_ROOT)) for path in source_files]


def _team_matches(espn_team: str | None, nhl_team_value: str | None) -> bool:
    if not espn_team or not nhl_team_value:
        return False
    espn = espn_team.upper()
    tokens = {
        token.strip().upper()
        for token in re.split(r"[,/|;\s]+", nhl_team_value)
        if token.strip()
    }
    return espn in tokens


def _crosswalk_rows(
    roster_rows: list[dict[str, Any]],
    available_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    player_map: dict[int, dict[str, Any]] = {}
    for row in roster_rows + available_rows:
        player_id = row.get("espn_player_id")
        if player_id in (None, ""):
            continue
        player_map.setdefault(int(player_id), row)

    nhl_index, source_files = _nhl_index()
    rows: list[dict[str, Any]] = []

    for espn_id in sorted(player_map):
        player = player_map[espn_id]
        candidates = nhl_index.get(_normalize_name(player.get("player_name")), [])

        chosen: dict[str, str] | None = None
        method = ""
        status = "unmatched"

        if len(candidates) == 1:
            chosen = candidates[0]
            method = "exact_normalized_name"
            status = "matched"
        elif len(candidates) > 1:
            team_candidates = [
                candidate
                for candidate in candidates
                if _team_matches(player.get("nhl_team"), candidate.get("nhl_team"))
            ]
            if len(team_candidates) == 1:
                chosen = team_candidates[0]
                method = "exact_normalized_name_and_team"
                status = "matched"
            else:
                status = "ambiguous"
        elif not source_files:
            status = "nhl_source_not_found"

        rows.append(
            {
                "espn_player_id": espn_id,
                "player_name": player.get("player_name"),
                "espn_team": player.get("nhl_team"),
                "primary_position": player.get("primary_position"),
                "nhl_player_id": chosen.get("nhl_player_id") if chosen else None,
                "nhl_name": chosen.get("nhl_name") if chosen else None,
                "nhl_team": chosen.get("nhl_team") if chosen else None,
                "match_status": status,
                "match_method": method,
                "source_file": chosen.get("source_file") if chosen else None,
            }
        )

    return rows, source_files


def _validate(
    teams: list[dict[str, Any]],
    rosters: list[dict[str, Any]],
    available: list[dict[str, Any]],
) -> dict[str, Any]:
    team_ids = [row["team_id"] for row in teams]
    roster_ids = [row["espn_player_id"] for row in rosters]
    available_ids = [row["espn_player_id"] for row in available]

    checks = {
        "team_count_positive": len(teams) > 0,
        "team_ids_unique": len(team_ids) == len(set(team_ids)),
        "roster_player_ids_present": all(value not in (None, "") for value in roster_ids),
        "roster_player_ids_unique": len(roster_ids) == len(set(roster_ids)),
        "available_player_ids_present": all(
            value not in (None, "") for value in available_ids
        ),
        "available_player_ids_unique": len(available_ids) == len(set(available_ids)),
        "rostered_and_available_disjoint": not (set(roster_ids) & set(available_ids)),
    }

    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("ESPN snapshot validation failed: " + ", ".join(failed))
    return checks


def create_espn_snapshot(
    config: ESPNConfig | None = None,
    *,
    available_limit: int = 2000,
    raw_root: Path = DEFAULT_RAW_ROOT,
    processed_root: Path = DEFAULT_PROCESSED_ROOT,
) -> SnapshotResult:
    """Fetch and persist a timestamped read-only ESPN league snapshot."""

    started = _utc_now()
    resolved = config or ESPNConfig.from_env()
    league = connect_espn(resolved)

    teams = _team_rows(league)
    rosters = _roster_rows(league)
    available = _available_rows(league, available_limit)
    matchups, categories = _matchup_rows(league)
    validations = _validate(teams, rosters, available)
    crosswalk, crosswalk_sources = _crosswalk_rows(rosters, available)

    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    snapshot_name = f"espn_{resolved.season_id}_{stamp}"
    raw_dir = Path(raw_root) / snapshot_name
    processed_dir = Path(processed_root) / snapshot_name

    if raw_dir.exists() or processed_dir.exists():
        raise FileExistsError(f"Snapshot already exists: {snapshot_name}")

    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)

    outputs: dict[str, int] = {}
    outputs["teams.csv"] = _write_csv(
        raw_dir / "teams.csv",
        teams,
        [
            "team_id",
            "team_abbrev",
            "team_name",
            "division_id",
            "division_name",
            "wins",
            "losses",
            "ties",
            "standing",
            "final_standing",
            "roster_count",
        ],
    )
    outputs["rosters.csv"] = _write_csv(
        raw_dir / "rosters.csv",
        rosters,
        [
            "fantasy_team_id",
            "fantasy_team_name",
            "espn_player_id",
            "player_name",
            "primary_position",
            "eligible_slots",
            "lineup_slot",
            "nhl_team",
            "injury_status",
            "injured",
            "acquisition_type",
            "availability_status",
        ],
    )
    outputs["available_players.csv"] = _write_csv(
        raw_dir / "available_players.csv",
        available,
        [
            "espn_player_id",
            "player_name",
            "primary_position",
            "eligible_slots",
            "nhl_team",
            "injury_status",
            "injured",
            "acquisition_type",
            "availability_status",
            "percent_owned",
            "percent_started",
            "percent_change",
        ],
    )
    outputs["matchups.csv"] = _write_csv(
        raw_dir / "matchups.csv",
        matchups,
        [
            "matchup_number",
            "matchup_period",
            "home_team_id",
            "home_team_name",
            "away_team_id",
            "away_team_name",
            "winner",
            "home_category_score",
            "away_category_score",
            "home_total_points",
            "away_total_points",
        ],
    )
    outputs["matchup_categories.csv"] = _write_csv(
        raw_dir / "matchup_categories.csv",
        categories,
        [
            "matchup_number",
            "matchup_period",
            "side",
            "team_id",
            "team_name",
            "category",
            "score",
            "result",
        ],
    )
    outputs["espn_nhl_crosswalk.csv"] = _write_csv(
        processed_dir / "espn_nhl_crosswalk.csv",
        crosswalk,
        [
            "espn_player_id",
            "player_name",
            "espn_team",
            "primary_position",
            "nhl_player_id",
            "nhl_name",
            "nhl_team",
            "match_status",
            "match_method",
            "source_file",
        ],
    )

    completed = _utc_now()
    files = {}
    for path in sorted(raw_dir.glob("*.csv")):
        files[path.name] = {
            "rows": outputs[path.name],
            "sha256": _sha256(path),
        }
    crosswalk_path = processed_dir / "espn_nhl_crosswalk.csv"
    files[str(crosswalk_path.relative_to(REPO_ROOT))] = {
        "rows": outputs["espn_nhl_crosswalk.csv"],
        "sha256": _sha256(crosswalk_path),
    }

    crosswalk_counts: dict[str, int] = {}
    for row in crosswalk:
        status = str(row["match_status"])
        crosswalk_counts[status] = crosswalk_counts.get(status, 0) + 1

    settings = getattr(league, "settings", None)
    metadata: dict[str, Any] = {
        "source": "ESPN Fantasy Hockey private league API via espn-api",
        "retrieval_started_at_utc": started.isoformat(),
        "retrieval_completed_at_utc": completed.isoformat(),
        "league_id": resolved.league_id,
        "season_id": resolved.season_id,
        "league_name": getattr(settings, "name", None),
        "current_scoring_period": getattr(league, "current_week", None),
        "current_matchup_period": getattr(league, "currentMatchupPeriod", None),
        "team_count": len(teams),
        "rostered_player_count": len(rosters),
        "available_player_count": len(available),
        "available_player_limit": available_limit,
        "available_limit_reached": len(available) >= available_limit,
        "matchup_count": len(matchups),
        "matchup_category_rows": len(categories),
        "crosswalk_status_counts": crosswalk_counts,
        "crosswalk_nhl_sources": crosswalk_sources,
        "validation": validations,
        "privacy": {
            "authentication_cookies_persisted": False,
            "owner_metadata_persisted": False,
            "raw_api_response_persisted": False,
        },
        "software": {
            "python": platform.python_version(),
            "espn-api": _package_version("espn-api"),
            "python-dotenv": _package_version("python-dotenv"),
            "truststore": _package_version("truststore"),
        },
        "files": files,
    }
    _write_json(raw_dir / "metadata.json", metadata)

    return SnapshotResult(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        metadata=metadata,
    )
