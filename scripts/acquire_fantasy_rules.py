#!/usr/bin/env python3
"""Read-only acquisition of league rules, excluding credentials and owner data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.fantasy.espn_client import ESPNConfig, connect_espn


def main():
    config = ESPNConfig.from_env()
    league = connect_espn(config)
    data = league.espn_request.league_get(params={'view': 'mSettings'})
    settings = data['settings']
    selected = {key: settings.get(key) for key in
                ['scoringSettings', 'rosterSettings', 'acquisitionSettings', 'scheduleSettings']}
    teams = league.espn_request.league_get(params={'view':'mTeam'})
    selected['team_transaction_counters'] = [dict(team_id=t['id'],transaction_counter=t.get('transactionCounter',{})) for t in teams.get('teams',[])]
    selected['current_scoring_period'] = league.current_week
    selected['current_matchup_period'] = league.currentMatchupPeriod
    selected['league_id'] = config.league_id
    selected['season_id'] = config.season_id
    selected['retrieved_at_utc'] = datetime.now(timezone.utc).isoformat()
    out = ROOT/'data/raw/espn/snapshots'/('rules_2027_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    path = out/'rules.json'
    path.write_text(json.dumps(selected, indent=2)+'\n')
    (out/'metadata.json').write_text(json.dumps(dict(source='ESPN mSettings, whitelisted rule groups only',
        retrieved_at_utc=selected['retrieved_at_utc'], files={'rules.json':hashlib.sha256(path.read_bytes()).hexdigest()}),indent=2)+'\n')
    print('Rules snapshot:', out.relative_to(ROOT))
    print('Scoring:', selected['scoringSettings']['scoringType'])
    print('Team transaction counters:', json.dumps(selected['team_transaction_counters']))


if __name__ == '__main__':
    main()
