# Season-to-date review through 2026-10-20

[Start with the multi-date comparison](multi_date.md): 24 full-comparison games, plus 12 additional team/goalie export games. The new feature trial has only 11 prospective games.

151 final regular-season games, 5,435 positive-TOI skater appearances; 2,422 have saved baseline means. 82 games have no saved baseline forecast. Daily challenger comparison covers 24 pregame games. No missing predictions are reconstructed.

## Coverage

![Season coverage](season_coverage.png)

[Every game and missing-player count](game_coverage.csv). The baseline selects the most recently created saved pregame season-rate snapshot for each entire game, before examining errors. This is a changing forecast policy, not one fixed model/version or a complete season backtest. It does not fill missing players from older runs. No-appearance forecasts are not scored as zeros. Skaters and goalies remain separate.

## Baseline, all covered appearances

| population | category | rows | games | predicted_total | actual_total | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_covered | goals | 2422 | 69 | 432.592 | 417.0 | 0.277 | 0.006 | 0.434 |
| all_covered | assists | 2422 | 69 | 722.701 | 703.0 | 0.404 | 0.008 | 0.545 |
| all_covered | shots | 2422 | 69 | 3907.036 | 3684.0 | 1.043 | 0.092 | 1.337 |
| all_covered | hits | 2422 | 69 | 2809.202 | 2834.0 | 0.877 | -0.01 | 1.172 |
| all_covered | points | 2422 | 69 | 1155.293 | 1120.0 | 0.533 | 0.015 | 0.692 |
| all_covered | pp_points | 2422 | 69 | 253.677 | 256.0 | 0.168 | -0.001 | 0.338 |
| all_covered | penalty_minutes | 2422 | 69 | 1149.664 | 1273.0 | 0.793 | -0.051 | 1.414 |
| all_covered | plus_minus | 2422 | 69 | -0.257 | -23.0 | 0.87 | 0.009 | 1.197 |
| all_covered | toi_minutes | 2422 | 69 | 40479.383 | 40214.8 | 2.23 | 0.109 | 2.942 |

## Issued daily trial comparison

| level | model | rows | games | mae | bias |
| --- | --- | --- | --- | --- | --- |
| player | calibrated_opponent_sog_trial | 864 | 24 | 1.042 | -0.026 |
| player | candidate | 864 | 24 | 1.043 | -0.03 |
| player | default | 864 | 24 | 1.058 | 0.09 |
| player | opponent_form_sog_trial | 864 | 24 | 1.058 | 0.095 |
| player | usage_shot_context_trial | 864 | 24 | 1.045 | -0.043 |
| team | calibrated_opponent_sog_trial | 48 | 24 | 4.249 | -0.442 |
| team | candidate | 48 | 24 | 4.227 | -0.524 |
| team | default | 48 | 24 | 4.448 | 1.649 |
| team | opponent_form_sog_trial | 48 | 24 | 4.432 | 1.737 |
| team | usage_shot_context_trial | 48 | 24 | 4.262 | -0.717 |
| saved_fantasy_player | calibrated_opponent_sog_trial | 179 | 24 | 1.361 | -0.355 |
| saved_fantasy_player | candidate | 179 | 24 | 1.364 | -0.367 |
| saved_fantasy_player | default | 179 | 24 | 1.35 | -0.177 |
| saved_fantasy_player | opponent_form_sog_trial | 179 | 24 | 1.348 | -0.164 |
| saved_fantasy_player | usage_shot_context_trial | 179 | 24 | 1.366 | -0.348 |

[All categories, fantasy subgroup, RMSE and bias](model_metrics.csv). Same saved games/positive-TOI appearances per model; team errors use issued lineup scenarios, not postgame participant sums. [Paired game-bootstrap deltas](game_cluster_uncertainty.csv) are exploratory; player rows are not independent games. The full-player comparative dates and frozen sources are recorded in the manifest; missing dates are not reconstructed. The October 9 issued simulation cohort is exported separately; retrospective October 8 calibration reconstructions and October 9 combined-model reconstructions are excluded from prospective comparisons. Independently issued October 9 trials are refreshed against the same official actuals in [opponent SOG metrics](archived_opponent_metrics.csv) and [goalie metrics](archived_goalie_metrics.csv). Keep these older input/format cohorts separate from the daily trial.

## Goalies

| model | category | rows | games | mae | bias |
| --- | --- | --- | --- | --- | --- |
| goalie_history_baseline | shots_against | 48 | 24 | 4.881 | 0.171 |
| goalie_opponent_context_trial | shots_against | 48 | 24 | 4.662 | -0.27 |
| goalie_history_baseline | saves | 48 | 24 | 5.221 | 0.079 |
| goalie_opponent_context_trial | saves | 48 | 24 | 4.959 | -0.318 |
| goalie_history_baseline | goals_against | 48 | 24 | 1.085 | 0.092 |
| goalie_opponent_context_trial | goals_against | 48 | 24 | 1.093 | 0.049 |

Eligible actual starts only; full-start means do not model pulls or empty-net duration. Keep saves and GA conclusions separate.

## Defense chance-creation data

[Past-only team context](defense_context.csv): all-strength and 5v5 D attempts, unblocked attempts, SOG, near-net attempts, assist credits, goals involving a D shooter/assistant, and short same-team followups after a D attempt. Near-net uses a 25-foot attacking-net distance, not a learned xG definition. Followups are within 10 seconds, stop at whistles/period changes/opponent shot attempts or recorded puck actions, and are temporal associations rather than passes or verified possessions. PBP/boxscore disagreements quarantine both teams of the affected games. Counts per game are not per-60 on-ice rates. This source snapshot ends on 2026-10-19; no missing PBP dates are inferred. No D feature coefficient is applied in the main forecasts. See [source strategy](../DATA_SOURCE_STRATEGY.md).

## Release fixes

A single command now refreshes inputs, builds all five skater/two goalie models and finalizes reader views. Publication checks require prior-day history, fresh injury/context retrievals, official game/team coverage, finite means, goalie count identities, no outcomes and at least ten minutes before every start. Late builds fail instead of becoming an issued pregame bundle. See NEXT_STEPS.md for the command and limits.

## Newer repository evidence

[October 17 published team and goalie evaluation](published_october_17.md) adds evidence beyond the locally restored bundles.
