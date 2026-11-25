#!/usr/bin/env python3
"""Acquire official NHL rosters for the target-date crosswalk."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import ssl
from urllib.request import Request, urlopen

import pandas as pd
import truststore


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Rink-Lab/0.1", "Accept": "application/json"})
    with urlopen(request, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=60) as response:
        return response.read()


def default_text(value) -> str:
    if isinstance(value, dict):
        return str(value.get("default") or "").strip()
    return str(value or "").strip()


def acquire(target: date) -> tuple[Path, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = Path("data/raw/nhl/snapshots") / f"roster_identity_{target}_{stamp}"
    processed = Path("data/processed/nhl") / f"roster_identity_{target}_{stamp}"
    raw.mkdir(parents=True, exist_ok=False)

    schedule_url = f"https://api-web.nhle.com/v1/schedule/{target.isoformat()}"
    schedule_bytes = download(schedule_url)
    (raw / "schedule.json").write_bytes(schedule_bytes)
    schedule = json.loads(schedule_bytes)
    days = [day for day in schedule.get("gameWeek", []) if day.get("date") == target.isoformat()]
    if len(days) != 1:
        raise ValueError("Official NHL schedule did not contain exactly one target date")
    games = [game for game in days[0].get("games", [])
             if game.get("season") == 20262027 and game.get("gameType") == 2]
    if not games:
        raise ValueError("No 2026-27 regular-season NHL games on target date")

    teams = sorted({game[side]["abbrev"] for game in games for side in ("awayTeam", "homeTeam")})
    sources = [dict(file="schedule.json", url=schedule_url, sha256=digest(raw / "schedule.json"))]

    def acquire_roster(team: str):
        url = f"https://api-web.nhle.com/v1/roster/{team}/current"
        payload = download(url)
        roster = json.loads(payload)
        name = f"roster_{team}.json"
        (raw / name).write_bytes(payload)
        rows = []
        for group, fallback_position in (("forwards", "F"), ("defensemen", "D"), ("goalies", "G")):
            for player in roster.get(group, []):
                player_id = player.get("id")
                player_name = " ".join(filter(None, (
                    default_text(player.get("firstName")),
                    default_text(player.get("lastName")),
                )))
                if player_id is None or not player_name:
                    raise ValueError(f"Incomplete NHL identity in {team} roster")
                rows.append(dict(
                    player_id=int(player_id),
                    player_name=player_name,
                    team_abbrev=team,
                    position_code=player.get("positionCode") or fallback_position,
                ))
        if not rows:
            raise ValueError(f"Official NHL roster was empty for {team}")
        return name, url, rows

    with ThreadPoolExecutor(max_workers=6) as pool:
        roster_results = list(pool.map(acquire_roster, teams))

    identities = []
    for name, url, rows in roster_results:
        identities.extend(rows)
        sources.append(dict(file=name, url=url, sha256=digest(raw / name)))

    identity = pd.DataFrame(identities)
    duplicate_ids = identity.loc[identity.player_id.duplicated(keep=False), "player_id"].unique()
    if len(duplicate_ids):
        raise ValueError("A player ID appeared on multiple target-date team rosters")

    raw_metadata = dict(
        source="NHL public API current rosters",
        date=target.isoformat(),
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
        teams=teams,
        sources=sources,
    )
    (raw / "metadata.json").write_text(json.dumps(raw_metadata, indent=2) + "\n")

    processed.mkdir(parents=True, exist_ok=False)
    identity_path = processed / "identity.csv"
    identity.sort_values(["team_abbrev", "player_id"]).to_csv(identity_path, index=False)
    processed_metadata = dict(
        source=raw_metadata["source"],
        date=target.isoformat(),
        raw_snapshot=str(raw),
        teams=teams,
        player_count=len(identity),
        sources=sources,
        files={"identity.csv": digest(identity_path)},
    )
    (processed / "manifest.json").write_text(json.dumps(processed_metadata, indent=2) + "\n")
    return raw, processed


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    raw, processed = acquire(args.date)
    print(f"NHL identity raw snapshot: {raw}")
    print(f"NHL identity snapshot: {processed}")


if __name__ == "__main__":
    main()
