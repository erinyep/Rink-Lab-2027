#!/usr/bin/env python3
"""Save sanitized next-scoring-period roster to audit pending transactions."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.fantasy.espn_client import ESPNConfig, connect_espn
from src.fantasy.espn_snapshot import _roster_rows
import pandas as pd


def main():
    config=ESPNConfig.from_env(); league=connect_espn(config)
    original=league.current_week
    league.current_week=original+1
    rows=_roster_rows(league)
    out=ROOT/'data/raw/espn/snapshots'/('future_roster_2027_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    path=out/'rosters.csv';pd.DataFrame(rows).to_csv(path,index=False)
    metadata=dict(league_id=config.league_id,season_id=config.season_id,
        current_scoring_period=original,requested_scoring_period=original+1,
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        source='ESPN mRoster/mTeam; sanitized player and roster fields only',
        files={'rosters.csv':hashlib.sha256(path.read_bytes()).hexdigest()})
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('Future roster snapshot:',out.relative_to(ROOT))
    print('Next-period roster rows:',len(rows))


if __name__=='__main__':main()
