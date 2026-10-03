#!/usr/bin/env python3
"""Create a timestamped read-only ESPN Fantasy Hockey league snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.fantasy.espn_client import ESPNConfig
from src.fantasy.espn_snapshot import create_espn_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch current ESPN Fantasy Hockey league state into local snapshots."
    )
    parser.add_argument(
        "--available-limit",
        type=int,
        default=2000,
        help="Maximum FREEAGENT/WAIVERS players to retrieve (default: 2000).",
    )
    args = parser.parse_args()

    try:
        config = ESPNConfig.from_env()
        print("Rink Lab ESPN Fantasy Hockey snapshot")
        print(f"League ID: {config.league_id}")
        print(f"ESPN season: {config.season_id}")
        print("Fetching read-only league state ...")

        result = create_espn_snapshot(
            config,
            available_limit=args.available_limit,
        )
    except Exception as exc:
        print(f"SNAPSHOT FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    metadata = result.metadata
    print("SNAPSHOT SUCCESSFUL")
    print(f"Raw snapshot: {result.raw_dir.relative_to(REPO_ROOT)}")
    print(f"Processed crosswalk: {result.processed_dir.relative_to(REPO_ROOT)}")
    print(f"Teams: {metadata['team_count']}")
    print(f"Rostered players: {metadata['rostered_player_count']}")
    print(f"Available players: {metadata['available_player_count']}")
    print(f"Current matchups: {metadata['matchup_count']}")
    print(f"Category rows: {metadata['matchup_category_rows']}")
    print(f"Crosswalk: {metadata['crosswalk_status_counts']}")
    if metadata["available_limit_reached"]:
        print(
            "WARNING: available-player result hit the configured limit; "
            "rerun with a larger --available-limit."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
