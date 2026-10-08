"""Current NHL schedule context; never infer a player's participation from it."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import ssl
import unicodedata
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .per_game import TARGETS, require


def normalize_team(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value)).lower() if c.isalnum())


# espn-api 1.0.0 still emits the franchise's former name. Only use the alias
# when UTA actually appears in the authoritative schedule. No Arizona fallback.
LEGACY_TEAM_ALIASES = {"utahhockeyclub": "UTA"}


def refresh_schedule(season, root=Path("data/raw/nhl/snapshots")):
    import truststore
    started = datetime.now(timezone.utc)
    day = started.astimezone(ZoneInfo("America/New_York")).date()
    pages, sources, seen_dates = {}, [], set()
    for offset in [0, 7]:
        date = day + timedelta(days=offset)
        url = f"https://api-web.nhle.com/v1/schedule/{date.isoformat()}"
        request = Request(url, headers={"User-Agent": "Rink-Lab/0.1", "Accept": "application/json"})
        with urlopen(request, timeout=60, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)) as response:
            payload = response.read()
        data = json.loads(payload)
        require(isinstance(data.get("gameWeek"), list), "Malformed NHL schedule response")
        seen_dates.update(d["date"] for d in data["gameWeek"])
        filename = f"schedule_{date.isoformat()}.json"
        pages[filename] = payload
        sources.append(dict(file=filename, url=url, sha256=hashlib.sha256(payload).hexdigest(),
                            retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
    expected = {(day + timedelta(days=i)).isoformat() for i in range(8)}
    require(expected <= seen_dates, "Schedule response does not cover the seven-day horizon")
    target = root / f"schedule_{season}_{started.strftime('%Y%m%dT%H%M%SZ')}"
    target.mkdir(parents=True, exist_ok=False)
    for filename, payload in pages.items():
        (target / filename).write_bytes(payload)
    (target / "metadata.json").write_text(json.dumps(dict(
        season_id=season, cutoff_utc=started.isoformat(), horizon_days=7,
        retrieval_completed_at_utc=datetime.now(timezone.utc).isoformat(), sources=sources,
        dates_covered=sorted(seen_dates)), indent=2) + "\n")
    return target


def schedule_rows(snapshot):
    metadata = json.loads((snapshot / "metadata.json").read_text())
    cutoff = datetime.fromisoformat(metadata["cutoff_utc"])
    end = cutoff + timedelta(days=7)
    games, teams = {}, {}
    for source in metadata["sources"]:
        payload = (snapshot / source["file"]).read_bytes()
        require(hashlib.sha256(payload).hexdigest() == source["sha256"], "Schedule hash mismatch")
        for day in json.loads(payload)["gameWeek"]:
            for game in day["games"]:
                if game["id"] in games:
                    require(games[game["id"]] == game, "Schedule changed between pages")
                games[game["id"]] = game
                for side in ["homeTeam", "awayTeam"]:
                    team = game[side]
                    name = team.get("placeName", {}).get("default", "") + " " + team.get("commonName", {}).get("default", "")
                    for alias in [team["abbrev"], name]:
                        key = normalize_team(alias)
                        require(key not in teams or teams[key] == team["abbrev"], "Ambiguous NHL team name")
                        teams[key] = team["abbrev"]
    rows = []
    for game in games.values():
        start = datetime.fromisoformat(game["startTimeUTC"].replace("Z", "+00:00"))
        if not (game["season"] == metadata["season_id"] and game["gameType"] == 2 and cutoff <= start < end):
            continue
        if game.get("gameState") not in ("FUT", "PRE") or game.get("gameScheduleState") != "OK":
            continue
        for side, other in [("homeTeam", "awayTeam"), ("awayTeam", "homeTeam")]:
            rows.append(dict(game_id=game["id"], season_id=game["season"], start_time_utc=game["startTimeUTC"],
                             nhl_team_abbrev=game[side]["abbrev"], opponent=game[other]["abbrev"],
                             home_away="home" if side == "homeTeam" else "away"))
    for alias, abbrev in LEGACY_TEAM_ALIASES.items():
        if abbrev in teams.values():
            teams[alias] = abbrev
    return pd.DataFrame(rows, columns=["game_id", "season_id", "start_time_utc", "nhl_team_abbrev", "opponent", "home_away"]), teams, metadata


def export_schedule_reference(espn_csv, snapshot, output):
    schedule, teams, metadata = schedule_rows(snapshot)
    players = pd.read_csv(espn_csv)
    players = players[~players.primary_position.isin(["Goalie", "G"])].copy()
    players["nhl_team_abbrev"] = players.nhl_team.map(lambda x: teams.get(normalize_team(x)))
    players["team_mapping_status"] = np.where(players.nhl_team_abbrev.notna(), "matched", "unresolved")
    # A row in both scoring roster and waivers is retained in the pool export;
    # only one game forecast per ESPN player/game belongs in this derived table.
    players = players.sort_values("pool", ascending=False).drop_duplicates("espn_player_id")
    games = players[players.nhl_team_abbrev.notna()].merge(schedule, on="nhl_team_abbrev", how="inner", validate="many_to_many")
    require(not games.duplicated(["espn_player_id", "game_id"]).any(), "Duplicate player/game projection")
    games["forecast_cutoff_utc"] = metadata["cutoff_utc"]
    games["forecast_type"] = "conditional_if_plays_no_opponent_adjustment"
    for event in TARGETS:
        games = games.rename(columns={f"{event}_per_game": f"{event}_if_plays"})
        games[f"expected_{event}"] = np.nan
    games.to_csv(output / "scheduled_skater_game_forecasts.csv", index=False)
    counts = schedule.groupby("nhl_team_abbrev").size()
    players["scheduled_team_games"] = players.nhl_team_abbrev.map(counts).fillna(0)
    players.loc[players.team_mapping_status == "unresolved", "scheduled_team_games"] = np.nan
    for event in TARGETS:
        players[f"schedule_only_{event}"] = players[f"{event}_per_game"] * players.scheduled_team_games
    players["reference_assumption"] = "plays_every_scheduled_team_game_optimistic_not_availability_forecast"
    players["forecast_cutoff_utc"] = metadata["cutoff_utc"]
    players.to_csv(output / "seven_day_schedule_reference.csv", index=False)
    schedule.to_csv(output / "upcoming_team_games.csv", index=False)
    return dict(snapshot=str(snapshot), cutoff_utc=metadata["cutoff_utc"],
                games=int(schedule.game_id.nunique()), player_game_rows=len(games),
                unresolved_team_players=int((players.team_mapping_status == "unresolved").sum()))
