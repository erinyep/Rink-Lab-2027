#!/usr/bin/env python3
"""Publish a compact, attributed MoneyPuck snapshot for NHL team models.

The full all_teams.csv download is too large for a normal GitHub file. This
release preserves every source column for regular-season Team Level rows from
seasons 2022-2026, the seasons used by the current team-model history loader.
The current-season shot archive is copied byte-for-byte with its provenance.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


TEAM_URL = "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"
SEASONS = {"2022", "2023", "2024", "2025", "2026"}
TEAM_FOLDER = Path("data/processed/moneypuck/team_context_20261106")
SHOT_FOLDER = Path("data/raw/moneypuck/published/shots_2026_20261106")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-snapshot", type=Path, required=True,
                        help="Complete team_games_* snapshot directory")
    parser.add_argument("--shots-snapshot", type=Path, required=True,
                        help="Validated shots_2026_* snapshot directory")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.repo_root.resolve()
    team_source = args.team_snapshot.resolve()
    shots_source = args.shots_snapshot.resolve()
    team_out = root / TEAM_FOLDER
    shots_out = root / SHOT_FOLDER
    if team_out.exists() or shots_out.exists():
        raise FileExistsError("Refusing to overwrite an existing MoneyPuck release")

    source_csv = team_source / "all_teams.csv"
    source_meta_path = team_source / "metadata.json"
    source_meta = json.loads(source_meta_path.read_text())
    if sha256(source_csv) != source_meta.get("sha256"):
        raise ValueError("Team snapshot checksum does not match its metadata")
    if source_meta.get("url") != TEAM_URL:
        raise ValueError("Unexpected MoneyPuck team-games source URL")

    team_out.mkdir(parents=True)
    rows_by_season: Counter[str] = Counter()
    rows_by_situation: Counter[str] = Counter()
    dates_by_season: dict[str, list[str]] = defaultdict(list)
    identities: set[tuple[str, str, str, str]] = set()
    games: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    with source_csv.open(newline="", encoding="utf-8") as source, \
            (team_out / "all_teams.csv").open("w", newline="", encoding="utf-8") as target:
        reader = csv.DictReader(source)
        required = {"season", "gameId", "gameDate", "team", "opposingTeam",
                    "position", "situation", "playoffGame", "home_or_away",
                    "goalsFor", "goalsAgainst", "xGoalsFor", "xGoalsAgainst",
                    "shotsOnGoalFor", "shotsOnGoalAgainst", "xOnGoalFor",
                    "xOnGoalAgainst", "iceTime", "shotAttemptsFor",
                    "shotAttemptsAgainst", "unblockedShotAttemptsFor",
                    "unblockedShotAttemptsAgainst"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Team source is missing required columns: " + ", ".join(sorted(missing)))
        writer = csv.DictWriter(target, fieldnames=reader.fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in reader:
            if (row["season"] not in SEASONS or row["position"] != "Team Level"
                    or row["playoffGame"] != "0"):
                continue
            identity = (row["season"], row["gameId"], row["team"], row["situation"])
            if identity in identities:
                raise ValueError(f"Duplicate selected team-game row: {identity}")
            identities.add(identity)
            games[(row["season"], row["gameId"], row["situation"])].add(row["team"])
            writer.writerow(row)
            rows_by_season[row["season"]] += 1
            rows_by_situation[row["situation"]] += 1
            dates_by_season[row["season"]].append(row["gameDate"])

    if not rows_by_season or set(rows_by_season) != SEASONS:
        raise ValueError("The selected source does not cover all five requested seasons")
    if any(len(teams) != 2 for teams in games.values()):
        raise ValueError("A selected game/situation is missing its opposing team row")
    if set(rows_by_situation) != {"all", "5on5", "4on5", "5on4", "other"}:
        raise ValueError("Unexpected MoneyPuck situation coverage")

    metadata = {
        "source": "MoneyPuck published game-by-game team download",
        "url": TEAM_URL,
        "retrieved_at_utc": source_meta["retrieved_at_utc"],
        "license": "Non-commercial research with MoneyPuck attribution; see https://moneypuck.com/data.htm",
        "source_sha256": source_meta["sha256"],
        "source_rows": source_meta["rows"],
        "sha256": sha256(team_out / "all_teams.csv"),
        "rows": sum(rows_by_season.values()),
        "seasons": sorted(SEASONS, key=int),
        "regular_season_only": True,
        "position": "Team Level",
        "situations": sorted(rows_by_situation),
        "rows_by_season": dict(sorted(rows_by_season.items())),
        "rows_by_situation": dict(sorted(rows_by_situation.items())),
        "latest_game_date_by_season": {
            season: max(dates) for season, dates in sorted(dates_by_season.items())
        },
        "field_scope": "All original MoneyPuck columns are retained for selected rows.",
        "filter": "season in 2022-2026; position == Team Level; playoffGame == 0",
        "purpose": "Compact team-game context for model training and current-season lagged forecasts. This is a filtered source release, not the full MoneyPuck download.",
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (team_out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (team_out / "README.md").write_text(
        "# MoneyPuck team-game context\n\n"
        "This compact release retains the original source columns for regular-season "
        "Team Level rows from 2022-23 through 2026-27, across all five published "
        "situations. It is suitable for the current direct team-goal and lagged "
        "5-on-5 shot-context workflows. The full upstream download is much larger; "
        "this file is a documented row-filtered subset.\n\n"
        "MoneyPuck source: [published team-game data](https://moneypuck.com/data.htm). "
        "Non-commercial research use; please credit MoneyPuck.com. The source "
        "retrieval time, original file hash, filters, row counts, and published "
        "file hash are in `metadata.json`.\n\n"
        "Coverage ends on the per-season dates in the manifest. MoneyPuck may revise "
        "historical values in later downloads; this is the frozen November 6, 2026 "
        "vintage, not a historical as-of series.\n"
    )

    shot_zip = shots_source / "shots.zip"
    shot_meta_path = shots_source / "metadata.json"
    shot_meta = json.loads(shot_meta_path.read_text())
    if sha256(shot_zip) != shot_meta.get("sha256"):
        raise ValueError("Shot archive checksum does not match its metadata")
    shots_out.mkdir(parents=True)
    published_zip = shots_out / "shots_2026.zip"
    shutil.copyfile(shot_zip, published_zip)
    public_shot_meta = {key: value for key, value in shot_meta.items()
                        if key not in {"raw_snapshot", "boxscores"}}
    public_shot_meta.update({
        "filename": published_zip.name,
        "sha256": sha256(published_zip),
        "note": "Original MoneyPuck ZIP copied byte-for-byte; local acquisition and NHL boxscore paths omitted.",
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    (shots_out / "metadata.json").write_text(json.dumps(public_shot_meta, indent=2) + "\n")
    (shots_out / "README.md").write_text(
        "# MoneyPuck 2026-27 unblocked shots\n\n"
        "`shots_2026.zip` is the original MoneyPuck download copied byte-for-byte. "
        "It contains 21,775 shot events in the November 6, 2026 vintage. Validation "
        "coverage, checksum, source URL, license, and reconciliation notes are in "
        "`metadata.json`.\n\n"
        "Source: [MoneyPuck published downloads](https://moneypuck.com/data.htm). "
        "Non-commercial research use; credit MoneyPuck.com. The ZIP is event-level "
        "input data; blocked attempts are absent and downloaded xG is not a historical "
        "as-of model score.\n"
    )
    print(f"Team context: {team_out} ({metadata['rows']} rows, {metadata['sha256']})")
    print(f"Shot archive: {shots_out} ({shot_meta['rows']} events, {public_shot_meta['sha256']})")


if __name__ == "__main__":
    main()
