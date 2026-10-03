# ESPN Fantasy Hockey connection

Rink Lab uses a **read-only local connection** to ESPN Fantasy Hockey. ESPN does not expose a normal public API key for private leagues, so the connection uses the `espn_s2` and `SWID` browser cookies from a currently logged-in ESPN session.

## Security

- Keep `.env` local only.
- Never commit `ESPN_S2` or `ESPN_SWID`.
- The repository `.gitignore` already ignores `.env` and `.env.*` while allowing `.env.example`.
- The smoke-test script never prints either credential.
- ESPN session cookies can expire; refresh them locally if authentication later fails.

## Expected environment variables

```text
ESPN_LEAGUE_ID=745879168
ESPN_SEASON_ID=2027
ESPN_S2=<private cookie value>
ESPN_SWID={private-swid-value}
```

`SWID` may be entered with or without braces; the connector normalizes it before connecting.

The connector also accepts `LEAGUE_ID` as an alias for `ESPN_LEAGUE_ID`, `ESPN_YEAR` for `ESPN_SEASON_ID`, and `SWID` for `ESPN_SWID`.

## Install dependencies

From the repository root and inside the Rink Lab virtual environment:

```sh
python -m pip install -r requirements.txt
```

The ESPN connector uses `espn-api` for Fantasy Hockey and `python-dotenv` to read the local `.env` file.

## Test the connection

From the repository root:

```sh
python scripts/test_espn_connection.py
```

A successful result should print:

- `CONNECTION SUCCESSFUL`
- the ESPN league name
- the number of teams
- the returned team names

No roster or player data is written by this test.

## First live-data milestone

After the smoke test passes, build a timestamped read-only ESPN snapshot containing:

1. league/team metadata;
2. all current rosters;
3. ESPN player IDs and fantasy-position eligibility;
4. free-agent / waiver pool data;
5. current matchup/category state where supported;
6. an ESPN-player-ID to NHL-player-ID crosswalk.

Keep raw ESPN snapshots separate from NHL source data and record retrieval time because league rosters, eligibility, and waiver availability change during the season.

## Troubleshooting

### Missing environment variables

If the script reports a configuration error, confirm `.env` is in the repository root and the four variables above are populated.

### Access denied / authentication failure

Confirm the league and season IDs first. If they are correct, refresh `ESPN_S2` and `ESPN_SWID` from a browser session that is currently logged into the ESPN account with access to the league.

### Package/import error

Re-run:

```sh
python -m pip install -r requirements.txt
```

and confirm the script is being run with the same Python interpreter / virtual environment used for Rink Lab.
