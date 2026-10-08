#!/usr/bin/env python3
"""Save the current official NHL schedule covering the next seven days."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.fantasy.schedule import refresh_schedule

if __name__ == "__main__":
    config = json.loads((ROOT / "config/per_game_forecast.json").read_text())
    print("Schedule snapshot:", refresh_schedule(config["target_season"]))
