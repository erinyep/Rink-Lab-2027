# Broader model development — through 2026-10-25

Question: does lagged expected-goal history improve next-game goal and winner forecasts, and what do defense production and saved injury labels add?

## More games, with distinct evidence

| season | model | games | team_rows | mae |
| --- | --- | --- | --- | --- |
| 2025 | equal_blend | 1312 | 2624 | 1.36 |
| 2025 | lagged_goals | 1312 | 2624 | 1.364 |
| 2025 | lagged_xg | 1312 | 2624 | 1.365 |
| 2026 | equal_blend | 167 | 334 | 1.383 |
| 2026 | lagged_goals | 167 | 334 | 1.384 |
| 2026 | lagged_xg | 167 | 334 | 1.387 |

2025 means the 2025–26 season; 2026 means 2026–27. Rolling features exclude the entire target date.
Each team's last 20 current-season games are combined with a fixed 20-game previous-season team prior;
missing prior teams use the previous-season league mean. Own offense and opponent defense receive equal weight.
Goal history, xG history and a fixed 50/50 blend were specified together; no fitted coefficients or winner promotion.
All 17 current-season team-file discrepancy games are excluded from features/scoring and retained in the audit.
Historical seasons have internal pair checks, not independent official boxscore reconciliation.
Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Corrected downloads are not historical pregame vintages;
MoneyPuck's current xG model was trained on 2023–26 shots. Older-season results are development evidence,
not a clean test of the upstream xG model. [Paired uncertainty](goal_uncertainty.csv).

## Current-season team probabilities

| model | games | brier |
| --- | --- | --- |
| equal_blend | 167 | 0.239 |
| lagged_goals | 167 | 0.238 |
| lagged_xg | 167 | 0.24 |

Official final winners include shootouts; goal-count targets exclude shootout deciding goals.
Independent Poisson counts and equally split ties are an uncalibrated approximation. No home advantage or
confirmed starter feature. [Paired Brier deltas](probability_uncertainty.csv). These reconstructed probabilities
are retrospective development results, separate from the 36-game frozen-main-model comparison.

## Defense scoring and expected versus actual goals

| role | appearances | players | goals | assists | shots | pp_points | toi_minutes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D | 2244 | 250 | 165 | 581 | 2727 | 141 | 42711.483 |
| F | 4379 | 474 | 981 | 1341 | 7346 | 593 | 66571.033 |

These are defensemen's offensive contributions, not a score of defensive prevention. Assists/PPP can involve
multiple players on the same goal and must not be added to goals as distinct scoring events.

| role | games | goals | xg | shots |
| --- | --- | --- | --- | --- |
| D | 115 | 104 | 100.785 | 1658 |
| F | 115 | 615 | 622.062 | 4568 |

Shot-level xG uses only 115 fully reconciled games; 69 games remain quarantined
for SOG or goal discrepancies. [Every player, with no GP threshold](player_goals_vs_xg.csv) includes goals minus xG
on the SAME usable games. This residual mixes finishing, sampling variation and model error; it is not established
repeatable finishing talent. Split PP/5v5, shrink toward longer history and test future games before adding effects.

## Frozen defense/quality trials: 3 prospective dates

| model | games | mae |
| --- | --- | --- |
| bias_control | 35 | 5.339 |
| defense_and_quality | 35 | 5.378 |
| pbp_defense | 35 | 5.41 |
| shot_quality | 35 | 5.341 |

[Paired uncertainty](prospective_feature_uncertainty.csv). These 35 games test team shots, not defenseman goal
scoring or team win probabilities. They cannot validate a defense scoring coefficient for a different target.

## Injuries and opportunity

[Saved injury labels versus subsequent participation](injury_participation_by_date.csv) and
[actual lineup overlap](lineup_coverage.csv) retain each original date. ACTIVE means an availability label,
not confirmed dressing; absence can be scratch, demotion or injury. Current injury labels never backfill old games.
Next test: separate probability of dressing from conditional EV/PP minutes and production; redistribute missing
players' opportunity to actual replacement roles. Effects require saved lineups/PP units and starter/rest history.
