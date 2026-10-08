#!/usr/bin/env python3
"""Refresh official NHL reports and read-only ESPN state, preserving old snapshots."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", nargs="+", type=int, help="Default: all seasons in forecast config")
    parser.add_argument("--skip-espn", action="store_true")
    args = parser.parse_args()
    config = json.loads((ROOT / "config/per_game_forecast.json").read_text())
    seasons = args.seasons or config["history_seasons"] + [config["target_season"]]
    for season in seasons:
        subprocess.run(["Rscript", "R/analysis/00_refresh_fantasy_snapshots.R", str(season)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/refresh_nhl_schedule.py"], cwd=ROOT, check=True)
    if not args.skip_espn:
        subprocess.run([sys.executable, "scripts/refresh_espn_snapshot.py"], cwd=ROOT, check=True)
    print("Refresh complete. Run python scripts/build_per_game_forecast.py next.")


if __name__ == "__main__":
    main()
