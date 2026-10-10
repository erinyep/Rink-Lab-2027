#!/usr/bin/env python3
"""Freeze ESPN season projections as a separate, timestamped shot benchmark.

Only projected season totals (source 1, split 0) are accepted. Current actual
totals may contain live games and are deliberately not persisted or consumed.
The existing ESPN/NHL crosswalk defines the requested population, including
unmatched players and goalies. This benchmark never changes model coefficients.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def projection_entry(player: dict, season: int) -> dict:
    """Select by metadata, never by array order or the ambiguous stat ID alone."""
    entries = [
        stat for stat in player.get("stats", [])
        if stat.get("seasonId") == season
        and stat.get("statSourceId") == 1
        and stat.get("statSplitTypeId") == 0
        and stat.get("scoringPeriodId", 0) == 0
    ]
    distinct = {json.dumps(entry.get("stats", {}), sort_keys=True) for entry in entries}
    if len(distinct) > 1:
        raise ValueError(f"Conflicting season projections for ESPN player {player.get('id')}")
    return {
        "espn_player_id": player.get("id"),
        "espn_player_name_at_retrieval": player.get("fullName"),
        "injury_status_at_projection_retrieval": player.get("injuryStatus"),
        "season_id": season,
        "stat_source_id": 1,
        "stat_split_type_id": 0,
        "projection_entry_count": len(entries),
        "stats": entries[0].get("stats", {}) if entries else {},
    }


def acquire_projection_snapshot(season: int, target_ids: set[int]) -> Path:
    from src.fantasy.espn_client import ESPNConfig, connect_espn

    config = ESPNConfig.from_env()
    if config.season_id != season:
        raise ValueError("Configured ESPN season differs from supplied saved snapshot")
    started = datetime.now(timezone.utc)
    league = connect_espn(config)
    # Request the whole pool once, then retain the saved crosswalk's population.
    # An explicit limit and requested-ID audit prevent silent partial coverage.
    limit = max(5000, 2 * len(target_ids))
    filters = {"players": {"limit": limit, "sortPercOwned": {
        "sortPriority": 1, "sortAsc": False,
    }}}
    data = league.espn_request.league_get(
        params={"view": "kona_player_info", "scoringPeriodId": league.current_week},
        headers={"x-fantasy-filter": json.dumps(filters)},
    )
    entries = data.get("players")
    if not isinstance(entries, list) or len(entries) >= limit:
        raise ValueError("ESPN pool response missing or reached the retrieval limit")
    rows = []
    for entry in entries:
        player = entry.get("playerPoolEntry", entry).get("player", {})
        if player.get("id") in target_ids:
            rows.append(projection_entry(player, season))
    ids = [row["espn_player_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("ESPN response contains duplicate player entries")
    completed = datetime.now(timezone.utc)
    raw = ROOT / "data/raw/espn/snapshots" / (
        f"espn_projections_{season}_{completed.strftime('%Y%m%dT%H%M%SZ')}"
    )
    raw.mkdir(parents=True, exist_ok=False)
    payload = raw / "season_projections.json"
    payload.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    metadata = {
        "source": "ESPN Fantasy Hockey read-only kona_player_info view",
        "source_url": "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/",
        "method": "espn-api authenticated GET; normalized projected numeric fields only",
        "season_id": season,
        "retrieval_started_at_utc": started.isoformat(),
        "retrieval_completed_at_utc": completed.isoformat(),
        "requested_player_count": len(target_ids),
        "returned_pool_count": len(entries),
        "returned_requested_player_count": len(rows),
        "missing_requested_espn_ids": sorted(target_ids - set(ids)),
        "request_limit": limit,
        "sha256": {payload.name: sha256(payload)},
        "privacy": "Authentication cookies and private owner/team metadata omitted",
        "projection_definition": "seasonId matches; statSourceId=1; statSplitTypeId=0; scoringPeriodId=0",
    }
    (raw / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--espn-snapshot", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--projection-snapshot", type=Path,
                        help="Reuse an immutable normalized projection snapshot")
    args = parser.parse_args()
    saved = args.espn_snapshot.resolve()
    saved_meta = json.loads((saved / "metadata.json").read_text())
    season = int(saved_meta["season_id"])
    crosswalk = ROOT / "data/processed/espn" / saved.name / "espn_nhl_crosswalk.csv"
    frame = pd.read_csv(crosswalk)
    if frame.espn_player_id.isna().any() or frame.espn_player_id.duplicated().any():
        raise ValueError("Saved crosswalk must have one row per valid ESPN identifier")
    ids = set(frame.espn_player_id.astype(int))
    raw = args.projection_snapshot or acquire_projection_snapshot(season, ids)
    metadata = json.loads((raw / "metadata.json").read_text())
    source = raw / "season_projections.json"
    if metadata["season_id"] != season or metadata["sha256"][source.name] != sha256(source):
        raise ValueError("Projection snapshot season/hash validation failed")
    entries = json.loads(source.read_text())
    rows = []
    for entry in entries:
        if (entry["season_id"], entry["stat_source_id"], entry["stat_split_type_id"]) != (season, 1, 0):
            raise ValueError("Snapshot includes a nonmatching projection stat entry")
        stats = entry.pop("stats")
        entry.update({
            "espn_projected_season_sog": stats.get("29"),
            "espn_projected_season_games": stats.get("34"),
            "espn_projected_season_toi_seconds": stats.get("26"),
            "espn_projected_atoi_seconds": stats.get("27"),
        })
        rows.append(entry)
    projections = pd.DataFrame(rows)
    if projections.empty or projections.espn_player_id.duplicated().any():
        raise ValueError("Empty or duplicated normalized projection population")
    frame = frame.merge(projections, on="espn_player_id", how="left", validate="one_to_one")
    gp = pd.to_numeric(frame.espn_projected_season_games, errors="coerce")
    shots = pd.to_numeric(frame.espn_projected_season_sog, errors="coerce")
    valid = gp.gt(0) & shots.ge(0)
    frame["espn_projected_sog_per_game"] = (shots / gp).where(valid)
    frame["espn_projected_toi_minutes_per_game"] = (
        pd.to_numeric(frame.espn_projected_season_toi_seconds, errors="coerce") / gp / 60
    ).where(gp.gt(0))
    frame["projection_status"] = "missing_sog_or_positive_gp"
    frame.loc[valid, "projection_status"] = "available_season_average_benchmark"
    frame.loc[frame.primary_position.eq("Goalie"), "projection_status"] = "goalie_separate_population"
    frame["projection_retrieved_at_utc"] = metadata["retrieval_completed_at_utc"]
    frame["crosswalk_snapshot"] = saved.name
    frame["benchmark_scope"] = "season_average_not_matchup_adjusted_or_calibrated_participation"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    provenance = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "projection_snapshot": relative(raw),
        "projection_retrieved_at_utc": metadata["retrieval_completed_at_utc"],
        "crosswalk": relative(crosswalk),
        "source_sha256": {relative(source): sha256(source), relative(crosswalk): sha256(crosswalk)},
        "output_sha256": sha256(args.out),
        "rows": len(frame),
        "unmatched_nhl_players": int(frame.nhl_player_id.isna().sum()),
        "status_counts": frame.projection_status.value_counts().to_dict(),
        "timing": "Use only for games beginning after projection_retrieved_at_utc; never reconstruct an earlier issue",
        "stat_mapping": {"29": "season SOG", "34": "season GP", "26": "total TOI seconds", "27": "ATOI seconds"},
    }
    args.out.with_suffix(".metadata.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
