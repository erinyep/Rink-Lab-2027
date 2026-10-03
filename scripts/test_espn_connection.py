#!/usr/bin/env python3
"""Smoke-test the read-only ESPN Fantasy Hockey connection.

Run from the repository root:
    python scripts/test_espn_connection.py

The script never prints ESPN_S2 or ESPN_SWID.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.fantasy.espn_client import ESPNConfig, connect_espn, summarize_league


def main() -> int:
    print("Rink Lab ESPN Fantasy Hockey connection test")
    print("Loading configuration from environment / .env ...")

    try:
        config = ESPNConfig.from_env()
    except RuntimeError as exc:
        print(f"CONFIG ERROR: {exc}")
        print("See docs/ESPN_CONNECTION.md and .env.example.")
        return 2

    # Safe identifiers only; credentials are intentionally never displayed.
    print(f"League ID: {config.league_id}")
    print(f"ESPN season: {config.season_id}")
    print("Connecting to ESPN ...")

    try:
        league = connect_espn(config)
    except Exception as exc:  # Library exception classes can vary by release.
        print(f"CONNECTION FAILED: {type(exc).__name__}: {exc}")
        print(
            "If the IDs are correct, refresh ESPN_S2 and ESPN_SWID from a "
            "currently logged-in ESPN browser session and try again."
        )
        return 1

    summary = summarize_league(league)
    print("CONNECTION SUCCESSFUL")
    print(f"League: {summary['league_name']}")
    print(f"Teams returned: {summary['team_count']}")
    if summary["current_week"] is not None:
        print(f"Current ESPN scoring period/week: {summary['current_week']}")

    if summary["team_names"]:
        print("Teams:")
        for name in summary["team_names"]:
            print(f"  - {name}")
    else:
        print("WARNING: ESPN returned no teams; treat this as an incomplete test.")
        return 1

    print("\nRead-only league access is working. No roster data was written to disk.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
