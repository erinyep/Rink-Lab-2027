# ESPN Fantasy Hockey connection

Rink Lab uses a **read-only local connection** to ESPN Fantasy Hockey. ESPN does not expose a normal public API key for private leagues, so the connection uses the `espn_s2` and `SWID` browser cookies from a currently logged-in ESPN session.

Connection status: **verified locally on 2026-10-03**.

## Security

- Keep `.env` local only.
- Never commit `ESPN_S2` or `ESPN_SWID`.
- The repository `.gitignore` ignores `.env` and `.env.*` while allowing `.env.example`.
- The smoke-test and snapshot scripts never print either credential.
- ESPN session cookies can expire; refresh them locally if authentication later fails.
- The snapshot pipeline does **not** persist raw ESPN responses or fantasy-owner metadata.

## Expected environment variables

```text
ESPN_LEAGUE_ID=745879168
ESPN_SEASON_ID=2027
ESPN_S2=<private cookie value>
ESPN_SWID={private-swid-value}
```

`SWID` may be entered with or without braces; the connector normalizes it before connecting.

The connector also accepts `LEAGUE_ID` as an alias for `ESPN_LEAGUE_ID`, `ESPN_YEAR` for `ESPN_SEASON_ID`, and `SWID` for `ESPN_SWID`.

## Install ESPN dependencies

From the repository root and inside the Rink Lab virtual environment:

```sh
python -m pip install -r requirements-espn.txt
```

Use `requirements-espn.txt` for the connector rather than reinstalling the full frozen `requirements.txt`. The general requirements snapshot contains older environment pins that may not be installable under the current Python version.

On macOS, the connector uses `truststore` so `requests`/`urllib3` validate ESPN HTTPS certificates against the operating-system trust store rather than only the static Certifi bundle.

## Test the connection

From the repository root:

```sh
python scripts/test_espn_connection.py
```

A successful result prints:

- `CONNECTION SUCCESSFUL`
- the ESPN league name
- the number of teams
- the returned team names

No roster or player data is written by this test.

## Create a live league snapshot

After the connection test passes:

```sh
python scripts/refresh_espn_snapshot.py
```

The default available-player retrieval limit is 2,000. If ESPN returns exactly that many records, the script warns that the result may be truncated. Rerun with a larger limit:

```sh
python scripts/refresh_espn_snapshot.py --available-limit 3000
```

Each run creates a timestamped local directory under:

```text
data/raw/espn/snapshots/espn_<season>_<UTC timestamp>/
```

with:

- `teams.csv` — fantasy-team IDs, names, standings/record fields, roster counts;
- `rosters.csv` — every rostered ESPN player, current lineup slot, eligibility, NHL team, injury status, and acquisition type;
- `available_players.csv` — players ESPN returns as FREEAGENT or WAIVERS, including eligibility and ownership fields where supplied;
- `matchups.csv` — current matchup summary;
- `matchup_categories.csv` — current H2H category scores/results when ESPN supplies cumulative category data;
- `metadata.json` — retrieval timestamps, counts, validations, package versions, file hashes, and privacy flags.

Generated ESPN snapshots are Git-ignored because roster, waiver, injury, and matchup state are time-varying league data.

## ESPN-to-NHL player crosswalk

The refresh script also writes:

```text
data/processed/espn/espn_<season>_<UTC timestamp>/espn_nhl_crosswalk.csv
```

It uses the most recent local `historical_skaters.csv` and `historical_goalies.csv` under `data/processed/fantasy/` when those files exist.

The first-pass match is conservative:

1. exact normalized player name;
2. if the name maps to multiple NHL IDs, exact team is used as a tiebreaker;
3. ambiguous and unmatched rows remain explicitly flagged rather than guessed.

Review unresolved rows before using the crosswalk for modeling.

## Snapshot validation

A snapshot is rejected if:

- fantasy-team IDs are duplicated;
- rostered ESPN player IDs are missing or duplicated;
- available-player ESPN IDs are missing or duplicated;
- the same ESPN player appears both rostered and available.

The metadata records whether the available-player query reached its configured limit.

## Current scope

This first connector milestone is intentionally read-only. It does **not**:

- add/drop players;
- change lineups;
- submit waiver claims;
- infer missing league rules;
- treat ESPN eligibility or waiver status as historical backtest data.

The live ESPN state is a current operational input to Rink Lab, separate from the historical NHL model-training data.

## Troubleshooting

### Missing environment variables

If a script reports a configuration error, confirm `.env` is in the repository root and the four variables above are populated.

### Access denied / authentication failure

Confirm the league and season IDs first. If they are correct, refresh `ESPN_S2` and `ESPN_SWID` from a browser session currently logged into the ESPN account with access to the league.

### Certificate verification failure on macOS

Install the ESPN requirements and rerun:

```sh
python -m pip install -r requirements-espn.txt
```

The connector injects the macOS system trust store before importing the ESPN HTTP client. Do not disable TLS verification with `verify=False`.

### Package/import error

Run:

```sh
python -m pip install -r requirements-espn.txt
```

and confirm the script is running with the same Python interpreter / virtual environment used for Rink Lab.
