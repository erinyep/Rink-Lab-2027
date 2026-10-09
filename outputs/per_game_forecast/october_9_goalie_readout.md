# October 9 goalie baseline and opponent-context trial

Later correction before puck drop: [revised goalie forecasts with fresh injury exclusions](../../data/processed/forecasts/goalies_2026-10-09_20261009T225533Z/goalie_game_forecasts.csv).
ESPN statuses refreshed at 22:53:52 UTC. Saved IR labels now exclude Hellebuyck
and Korpisalo from trial start shares. The original artifacts and table below
describe the earlier model, whose start-share rule did not apply injury exclusions.
Use the revised artifact for the late pregame trial; conditional rates stay available.

Created **2026-10-09T22:45:16.048013+00:00**, before first puck drop. All four games/eight teams and 18 official-roster goalies are retained. Original skater and team-trial artifacts remain frozen.

## What was implemented

Separate goalie history and opponent-context models. Save probability uses three completed seasons plus valid current-season observations, weights 1/0.5/0.25 for completed history and 1 for current data, and 200 prior shots from valid completed-season league history. Shot exposure per 60 minutes uses a 600-minute prior. Missing history receives the past league prior. These prior strengths are fixed initial assumptions, not tuned settings.

51 player-season rows with invalid count identities or valuation flags are excluded from event-rate fitting and preserved in an audit. Source values are never repaired. Starts are role observations independent of event-count validity.

Start share is (observed starts for this current-team goalie + 1) / (starts summed across current roster goalies + number of roster goalies). Shares sum to one, but are **not confirmed starters or calibrated probabilities**. Rest, back-to-backs, injuries, call-ups and coaching choices are not fitted.

Conditional forecasts assume **a full 60-minute start**. SOG against is Poisson and saves are binomial given SOG; GA=SA−SV. GAA equals expected GA for that 60-minute scenario. Saves/GA/SA simulation quantiles are provisional. Win support is a proxy from independent team goals-for and goalie goals-allowed draws, splitting ties equally. It does not model goalie win credit, overtime, shootouts, pulls or relief.

## Opponent-context trial

Expected SA is the average of own team SA/game and opponent SOG/game, each shrunk with ten league-average pseudo-games from the 65 completed games. The rate baseline uses goalie historical SA/60 instead. This is a visible early-season opponent-volume candidate; it does not identify goalie talent, defensive skill or shot quality. GAA and save outcomes change with the opponent volume; SV probability remains the historical shrunken estimate.

| team | opponent | player_name | start_share_provisional | saves_if_full_start | gaa_if_full_60 | save_percentage_projection |
| --- | --- | --- | --- | --- | --- | --- |
| DET | SEA | John Gibson | 0.800 | 23.935 | 2.697 | 0.899 |
| DET | SEA | Daniil Tarasov | 0.200 | 23.821 | 2.812 | 0.894 |
| SEA | DET | Joey Daccord | 0.667 | 25.133 | 2.521 | 0.909 |
| SEA | DET | Philipp Grubauer | 0.333 | 24.862 | 2.792 | 0.899 |
| WSH | NYR | Charlie Lindgren | 0.400 | 23.961 | 2.879 | 0.893 |
| WSH | NYR | Logan Thompson | 0.600 | 24.428 | 2.411 | 0.910 |
| NYR | WSH | Dylan Garand | 0.250 | 24.091 | 2.123 | 0.919 |
| NYR | WSH | Joonas Korpisalo | 0.125 | 23.416 | 2.798 | 0.893 |
| NYR | WSH | Igor Shesterkin | 0.625 | 23.817 | 2.396 | 0.909 |
| CBJ | PIT | Jet Greaves | 0.750 | 25.329 | 2.557 | 0.908 |
| CBJ | PIT | Cam Talbot | 0.250 | 24.705 | 3.182 | 0.886 |
| PIT | CBJ | Sergei Murashov | 0.333 | 23.747 | 2.693 | 0.898 |
| PIT | CBJ | Arturs Silovs | 0.667 | 23.240 | 3.201 | 0.879 |
| WPG | ANA | Connor Hellebuyck | 0.143 | 24.904 | 2.545 | 0.907 |
| WPG | ANA | Stuart Skinner | 0.571 | 24.549 | 2.899 | 0.894 |
| WPG | ANA | Clay Stevenson | 0.286 | 24.848 | 2.600 | 0.905 |
| ANA | WPG | Lukas Dostal | 0.800 | 24.302 | 2.885 | 0.894 |
| ANA | WPG | Ville Husso | 0.200 | 24.157 | 3.030 | 0.889 |

## Artifacts

[Game forecasts for both models](../../data/processed/forecasts/goalies_2026-10-09_20261009T224516Z/goalie_game_forecasts.csv) · [Goalie simulations](../../data/processed/forecasts/goalies_2026-10-09_20261009T224516Z/goalie_simulation_summary.csv) · [All ESPN-rostered goalie rates](../../data/processed/forecasts/goalies_2026-10-09_20261009T224516Z/espn_rostered_goalie_rates.csv) · [Opponent inputs](../../data/processed/forecasts/goalies_2026-10-09_20261009T224516Z/opponent_context.csv) · [Excluded source rows](../../data/processed/forecasts/goalies_2026-10-09_20261009T224516Z/excluded_goalie_source_rows.csv)

The ESPN rate file includes goalies whose teams do not play October 9; rate availability is not a scheduled start forecast. Do not sum goalie GAA or SV%. Fantasy ratios must be calculated from aggregate GA/TOI and SV/SA.

## Relation to ELWAY and other projection systems

Our [ELWAY-inspired plan](../../docs/ELWAY_ADAPTATION_PLAN.md) already calls for team offensive environment, goalie shots against, team win support, tandem uncertainty and distinct current-context projections. Opposing fantasy rosters mentioned there are a separate matchup-decision concept. Our existing skater baseline records the NHL opponent but makes no statistical opponent adjustment.

[MoneyPuck’s published methodology](https://www.moneypuck.com/about.htm) explicitly combines team scoring chances, goaltending, home/away and rest for game predictions, and models starter probabilities separately. This supports the architecture of separating goalie skill, team environment and opportunity; it does not validate our new coefficients or assumptions.

## Next gates

1. Evaluate the frozen goalie baseline and opponent trial after October 9 final results, with start-share Brier scores and conditional SA/SV/GA errors. Treat partial starts/relief separately from the full-60 scenario.
2. Acquire timestamped confirmed starter sources and historical starter/roster coverage. Validate start shares, role priors, rest and injury effects chronologically.
3. Resolve source-count discrepancies. Validate prior shots/minutes, then opponent-volume effects versus the history baseline on prior-season chronological windows.
4. Add shot-quality-adjusted opponent scoring and goalie effects, strength splits, team dependencies and win-credit logic only against the simpler baselines. Add skater opponent adjustments as separate candidates, not changes to today’s frozen skater predictions.

Twenty Python tests pass. Data, code and source provenance are retained. Both goalie models remain provisional and unvalidated; the default skater model is unchanged.
