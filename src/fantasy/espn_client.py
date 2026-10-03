"""Read-only ESPN Fantasy Hockey connection helpers.

Credentials are loaded from environment variables or a repository-root `.env`
file. Secret values are never logged or returned by the helper functions.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv
from espn_api.hockey import League


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"


_ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "league_id": ("ESPN_LEAGUE_ID", "LEAGUE_ID"),
    "season_id": ("ESPN_SEASON_ID", "ESPN_YEAR", "YEAR"),
    "espn_s2": ("ESPN_S2", "espn_s2"),
    "swid": ("ESPN_SWID", "SWID", "swid"),
}


def _first_env(names: Iterable[str]) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip() != "":
            return value.strip()
    return None


def _normalize_swid(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    return "{" + stripped.strip("{}") + "}"


@dataclass(frozen=True)
class ESPNConfig:
    """Connection settings for one ESPN Fantasy Hockey league."""

    league_id: int
    season_id: int
    espn_s2: str
    swid: str

    @classmethod
    def from_env(cls, env_file: str | Path | None = None) -> "ESPNConfig":
        """Load ESPN credentials without exposing them in code or logs."""

        dotenv_path = Path(env_file) if env_file is not None else DEFAULT_ENV_FILE
        if dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path, override=False)
        else:
            # Still allow callers to supply credentials through shell/CI variables.
            load_dotenv(override=False)

        values = {
            key: _first_env(aliases)
            for key, aliases in _ENV_ALIASES.items()
        }
        missing = [
            _ENV_ALIASES[key][0]
            for key, value in values.items()
            if value is None
        ]
        if missing:
            raise RuntimeError(
                "Missing ESPN environment variable(s): " + ", ".join(missing)
            )

        try:
            league_id = int(values["league_id"])  # type: ignore[arg-type]
            season_id = int(values["season_id"])  # type: ignore[arg-type]
        except ValueError as exc:
            raise RuntimeError(
                "ESPN_LEAGUE_ID and ESPN_SEASON_ID must be integers."
            ) from exc

        return cls(
            league_id=league_id,
            season_id=season_id,
            espn_s2=values["espn_s2"],  # type: ignore[arg-type]
            swid=_normalize_swid(values["swid"]),  # type: ignore[arg-type]
        )


def connect_espn(config: ESPNConfig | None = None) -> League:
    """Create a read-only ESPN Fantasy Hockey League client."""

    resolved = config or ESPNConfig.from_env()
    return League(
        league_id=resolved.league_id,
        year=resolved.season_id,
        espn_s2=resolved.espn_s2,
        swid=resolved.swid,
    )


def _team_name(team: Any) -> str:
    for attr in ("team_name", "team_abbrev", "name"):
        value = getattr(team, attr, None)
        if value:
            return str(value)
    team_id = getattr(team, "team_id", None)
    return f"Team {team_id}" if team_id is not None else "Unknown team"


def summarize_league(league: League) -> dict[str, Any]:
    """Return a non-secret summary suitable for a smoke-test or log message."""

    settings = getattr(league, "settings", None)
    league_name = getattr(settings, "name", None) or "Unknown league"
    teams = list(getattr(league, "teams", []) or [])

    return {
        "league_name": league_name,
        "team_count": len(teams),
        "team_names": [_team_name(team) for team in teams],
        "current_week": getattr(league, "current_week", None),
    }
