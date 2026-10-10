#!/usr/bin/env python3
"""Acquire cutoff-safe NHL per-game even-strength, PP and PK player exposure."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests
import truststore

ROOT = Path(__file__).resolve().parents[1]
URL = "https://api.nhle.com/stats/rest/en/skater/timeonice"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=date.fromisoformat,
                        help="Exclusive NHL game-date cutoff")
    parser.add_argument("--season", type=int, default=20262027)
    parser.add_argument("--raw-snapshot", type=Path, help="Reprocess saved source without network")
    parser.add_argument("--boxscore-snapshot", type=Path,
                        help="Cross-check positive-TOI player/game keys against saved NHL boxscores")
    args = parser.parse_args()
    cutoff = args.before.isoformat()
    if args.raw_snapshot:
        raw = args.raw_snapshot.resolve()
        metadata = json.loads((raw / "metadata.json").read_text())
        if metadata["season_id"] != args.season or metadata["before_game_date"] != cutoff:
            raise ValueError("Saved source season/cutoff mismatch")
        pages = []
        for name, expected in metadata["source_sha256"].items():
            path = raw / name
            if digest(path) != expected:
                raise ValueError(f"Source hash mismatch: {name}")
            pages.append(json.loads(path.read_text()))
    else:
        truststore.inject_into_ssl()
        started = datetime.now(timezone.utc)
        params = {
            "isAggregate": "false", "isGame": "true", "limit": 100,
            "sort": json.dumps([{"property": "gameId", "direction": "ASC"},
                                {"property": "playerId", "direction": "ASC"}]),
            "cayenneExp": f'seasonId={args.season} and gameTypeId=2 and gameDate<"{cutoff}"',
        }

        def fetch(offset: int) -> dict:
            response = requests.get(URL, params={**params, "start": offset}, timeout=60,
                                    headers={"User-Agent": "Rink-Lab/0.1 research"})
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload.get("data"), list) or "total" not in payload:
                raise ValueError("Invalid NHL time-on-ice response")
            return payload

        first = fetch(0)
        offsets = list(range(0, first["total"], 100))
        with ThreadPoolExecutor(max_workers=4) as pool:
            pages = [first, *pool.map(fetch, offsets[1:])]
        if any(page["total"] != first["total"] for page in pages):
            raise ValueError("NHL pagination total changed during acquisition")
        completed = datetime.now(timezone.utc)
        label = f"game_toi_{args.season}_{completed.strftime('%Y%m%dT%H%M%SZ')}"
        raw = ROOT / "data/raw/nhl/snapshots" / label
        raw.mkdir(parents=True, exist_ok=False)
        hashes = {}
        for offset, page in zip(offsets, pages):
            path = raw / f"page_{offset:06d}.json"
            path.write_text(json.dumps(page, indent=2, sort_keys=True) + "\n")
            hashes[path.name] = digest(path)
        metadata = {
            "source_url": URL, "request_parameters": params,
            "season_id": args.season, "game_type": 2, "before_game_date": cutoff,
            "retrieval_started_at_utc": started.isoformat(),
            "retrieval_completed_at_utc": completed.isoformat(),
            "api_total": first["total"], "pages": len(pages), "source_sha256": hashes,
            "method": "NHL Stats API JSON, stable gameId/playerId ordering, pages of 100",
        }
        (raw / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    rows = [row for page in pages for row in page["data"]]
    source = pd.DataFrame(rows)
    if len(source) != metadata["api_total"] or source.empty:
        raise ValueError("Incomplete or empty NHL pagination")
    rename = {
        "playerId": "player_id", "gameId": "game_id", "gameDate": "game_date",
        "skaterFullName": "player_name", "teamAbbrev": "team",
        "opponentTeamAbbrev": "opponent", "homeRoad": "home_road",
        "positionCode": "position", "timeOnIce": "toi_seconds",
        "evTimeOnIce": "ev_toi_seconds", "ppTimeOnIce": "pp_toi_seconds",
        "shTimeOnIce": "sh_toi_seconds", "otTimeOnIce": "ot_toi_seconds", "shifts": "shifts",
    }
    frame = source[list(rename)].rename(columns=rename)
    frame["season_id"] = args.season
    if frame[["game_id", "player_id", "game_date"]].isna().any().any():
        raise ValueError("Missing player/game/date key")
    if frame.duplicated(["game_id", "player_id"]).any():
        raise ValueError("Duplicate player/game exposure rows")
    if (frame.game_date >= cutoff).any() or not frame.game_id.astype(str).str.startswith(str(args.season)[:4] + "02").all():
        raise ValueError("Game dates or IDs violate season/type/cutoff")
    time_cols = [column for column in frame if column.endswith("_seconds")]
    if frame[time_cols].isna().any().any() or frame[time_cols].lt(0).any().any():
        raise ValueError("Missing or negative player exposure")
    frame["toi_components_agree"] = frame.toi_seconds.eq(
        frame.ev_toi_seconds + frame.pp_toi_seconds + frame.sh_toi_seconds
    )
    validation = {
        "rows": len(frame), "games": int(frame.game_id.nunique()),
        "players": int(frame.player_id.nunique()), "first_game_date": frame.game_date.min(),
        "last_game_date": frame.game_date.max(),
        "toi_component_disagreements": int((~frame.toi_components_agree).sum()),
        "max_toi_minutes": float(frame.toi_seconds.max() / 60),
        "zero_toi_rows": int(frame.toi_seconds.eq(0).sum()),
        "boxscore_comparison": "not_requested",
    }
    if args.boxscore_snapshot:
        observed = set()
        for path in args.boxscore_snapshot.glob("boxscore_*.json"):
            box = json.loads(path.read_text())
            if (box.get("season") != args.season or box.get("gameType") != 2
                    or box.get("gameDate", cutoff) >= cutoff
                    or box.get("gameState") not in {"OFF", "FINAL"}):
                continue
            for side in ("awayTeam", "homeTeam"):
                players = box.get("playerByGameStats", {}).get(side, {})
                for group in ("forwards", "defense"):
                    for player in players.get(group, []):
                        if player.get("toi", "00:00") not in {"00:00", "0:00"}:
                            observed.add((box["id"], player["playerId"]))
        keys = set(frame.loc[frame.toi_seconds.gt(0), ["game_id", "player_id"]].itertuples(index=False, name=None))
        validation["boxscore_comparison"] = {
            "observed_keys": len(observed), "toi_keys": len(keys),
            "missing_from_toi": sorted(observed - keys),
            "absent_from_boxscores": sorted(keys - observed),
        }
        if keys != observed:
            raise ValueError(f"Player/game exposure coverage differs from boxscores: {validation['boxscore_comparison']}")
    out = ROOT / "data/processed/nhl" / raw.name
    out.mkdir(parents=True, exist_ok=True)
    path = out / "player_game_toi.csv"
    frame.sort_values(["game_id", "player_id"]).to_csv(path, index=False)
    report = {**metadata, "raw_snapshot": str(raw.relative_to(ROOT)),
              "processed_csv": str(path.relative_to(ROOT)), "output_sha256": digest(path),
              "validation": validation,
              "units": "All time columns are seconds. OT overlaps EV/PP/SH; do not add OT to components."}
    (out / "manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(path.relative_to(ROOT)), "validation": validation}, indent=2))


if __name__ == "__main__":
    main()
