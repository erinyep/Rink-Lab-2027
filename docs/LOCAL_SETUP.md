# Set up a second machine

Use Python 3.12 or newer. The system Python on this Mac is too old for the
project's HTTPS trust-store support. The local `rink-lab.venv` has now been
created and populated; R and the required acquisition packages are available.
Run commands from the repository root.

ESPN read-only access to Micro League (six teams) was refreshed on November 25.
Keep the local `.env` file out of chat and Git when moving between machines.

## What to transfer privately

Copy `.env` from the working machine to this repository's root. It contains
ESPN league settings and session cookies; keep it out of chat and Git. Use
`.env.example` as the field reference if recreating it. Then check the connection:

```sh
rink-lab.venv/bin/python scripts/test_espn_connection.py
```

Optionally transfer `data/raw/` and `data/processed/` from the other machine to
retain frozen forecasts, past evaluations and source snapshots. Git intentionally
does not carry these. Preserve existing timestamped directories; avoid replacing
this machine's newly acquired snapshots. The new machine can rebuild public data,
but cannot recreate old pregame issuances after the games.

## Daily forecasts on this machine

The November 25 refresh acquired official final game/scoring/TOI/PBP history and
MoneyPuck data through November 24, refreshed the eight-day NHL schedule, and
validated 13,859 positive-TOI rows against 385 official finals. The current
player-season template on this machine is:

`data/processed/forecasts/per_game_20262027_20261125T161648Z`

After `.env` is transferred, this command refreshes ESPN, final games, ice time,
MoneyPuck, schedule and rosters, then issues skaters, goalies and reading tables:

```sh
rink-lab.venv/bin/python scripts/run_daily_forecasts.py \
  --date 2026-11-26 \
  --template-forecast data/processed/forecasts/per_game_20262027_20261125T161648Z
```

Set the target date explicitly for future slates. Each run stops on failure and
creates new timestamped outputs; same-day reports receive versioned names.
The ESPN build rejects injury snapshots older than six hours. Reused inputs can
be supplied explicitly with `--boxscore-history`, `--game-history`, `--game-toi`
and `--moneypuck-snapshot`; their cutoffs and coverage must suit the target date.

Without ESPN, add `--without-espn`. This produces public hockey scenarios only:
injuries are `UNKNOWN`, fantasy ownership is absent, and lineups/starter shares
are unconfirmed. Do not interpret these as league-specific start/sit advice.
Today's available outputs are linked from [forecast status](../outputs/per_game_forecast/README.md).

No unattended schedule or ESPN roster transactions are enabled.

## Rebuild from a fresh checkout

With `uv` installed:

```sh
uv venv --python 3.12 rink-lab.venv
uv pip install --python rink-lab.venv/bin/python \
  -r requirements-forecast.txt -r requirements-espn.txt
```

Run `Rscript R/analysis/00_refresh_fantasy_snapshots.R <season>` for each season
in `config/per_game_forecast.json` (20212022 through 20262027), then:

```sh
rink-lab.venv/bin/python scripts/build_per_game_forecast.py
rink-lab.venv/bin/python -m unittest discover -s tests
```

Use the newly printed template path when invoking the daily runner. Rebuilding
uses current source corrections; it does not restore the other machine's issued
forecast history. See [ESPN connection](ESPN_CONNECTION.md) and
[NHL acquisition](NHL_ACQUISITION.md) for source and validation details.

Both issuance runners now register finalized predictions in the append-only local
`data/processed/prediction_history/` archive. After evaluating a new actuals vintage,
run `scripts/update_prediction_history.py --review <season-review> --bundle <latest-issued-bundle> --out <new-scoreboard-directory>`.
This preserves previous result vintages and produces season/7-day/30-day count-error metrics.
