# Team goal model update — through 2026-10-26

Selected specification: **goal_xg_home_rest**, chosen solely on 2025–26 Poisson goal likelihood.
Training: 2624 games from 2023–24 and 2024–25. Validation: 1312 games
from 2025–26. Recent test: **187 games** from 2026–27, including all games through 2026-10-26.
No games-played threshold. Both teams, same fixtures for every model. No new per-slate correction.

The model learns team offense and opponent goals-against effects, home ice, back-to-backs and rest difference.
A second declared candidate adds lagged own xG and opponent xGA. Both use training-only standardization and
fixed ridge penalty 20. The simple baseline averages shrunk own scoring and opponent goals allowed.
Rates use the last 20 current-season games plus a fixed 20-game prior from the previous season.
Every feature excludes the entire target date. Goals are official NHL counts in the recent test; discrepancies
in downloaded xG are quarantined while retaining official goal and schedule observations.

## Full-season validation

| model | games | mae | poisson_nll |
| --- | --- | --- | --- |
| goal_strength_home_rest | 1312 | 1.366 | 1.928 |
| goal_xg_home_rest | 1312 | 1.363 | 1.926 |
| lagged_goals_baseline | 1312 | 1.364 | 1.927 |

## Recent goal forecasts

| model | games | mae | poisson_nll |
| --- | --- | --- | --- |
| goal_strength_home_rest | 187 | 1.412 | 1.937 |
| goal_xg_home_rest | 187 | 1.405 | 1.935 |
| lagged_goals_baseline | 187 | 1.417 | 1.94 |

## Recent win-probability forecasts

| model | games | brier | log_loss |
| --- | --- | --- | --- |
| goal_strength_home_rest | 187 | 0.237 | 0.666 |
| goal_xg_home_rest | 187 | 0.235 | 0.663 |
| lagged_goals_baseline | 187 | 0.242 | 0.678 |

[Paired game-bootstrap differences](paired_uncertainty.csv) · [Every recent date](recent_metrics_by_date.csv)
· [Goal predictions](recent_predictions.csv) · [Win probabilities](recent_probabilities.csv).

Poisson likelihood is the model-selection target, not MAE or a hand-picked winning slate. Winner probabilities
use independent Poisson scores and equal tie splitting; there is no fitted overtime model. These historical
predictions are a chronological development test, NOT original issued probabilities. Current-season results
do not enter the specification choice. The final deployed coefficients are refit through 2026-10-26; they
must only be used for later dates and their future scores tracked separately.

Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Historical sources are corrected downloads rather than
as-of snapshots; the upstream xG model used 2023–26 training shots. Therefore xG candidate validation is
development evidence with upstream overlap, not an independent validation of MoneyPuck. Historical goal
counts have internal checks; recent targets are reconciled against official NHL finals. Rest excludes travel
distance and timezone changes. Missing confirmed starters/lineups remain an improvement opportunity.

[Production parameters](fitted_model.json) · [Frozen pre-test parameters](historical_test_models.json).
