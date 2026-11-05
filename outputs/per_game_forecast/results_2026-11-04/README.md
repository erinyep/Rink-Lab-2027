# November 4 frozen forecast results

The four pregame forecasts were issued before puck drop and scored against the official NHL box scores acquired November 5. No model was refit. Predictions and actuals are kept as separate files.

## Game winners and goal means

| away | home | final | new model pick | original model pick |
| --- | --- | --- | --- | --- |
| OTT | BUF | 2–1 | OTT (50.7%) | BUF (54.0%) |
| CHI | FLA | 3–5 | FLA (64.2%) | FLA (54.9%) |
| SJS | LAK | 2–7 | LAK (60.1%) | SJS (55.2%) |
| CGY | SEA | 1–2 | SEA (57.5%) | SEA (50.6%) |

| model | games | brier | favorite_correct | favorite_accuracy | goal_mae_per_team |
| --- | --- | --- | --- | --- | --- |
| new_team_model | 4 | 0.178 | 4 | 100% | 1.56 |
| original_model | 4 | 0.261 | 2 | 50% | 1.63 |

Brier and per-team absolute goal error are lower-is-better. New model picks were correct in 4/4 games; original model picks were correct in 2/4. The Brier point-score difference was -0.083. Four games do not establish calibration or durable superiority, so no uncertainty interval is inferred from this slate. Scores use official final box-score goals.

## Player shots

| model | rows_scored | mae | bias |
| --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 143 | 0.996 | -0.030 |
| candidate | 143 | 0.996 | -0.040 |
| default | 143 | 1.008 | 0.078 |
| opponent_form_sog_trial | 143 | 1.011 | 0.089 |
| usage_shot_context_trial | 143 | 0.988 | -0.057 |

All models were issued pregame. These are conditional player means scored only for players with positive time on ice. The main calibrated-opponent model is distinct from the usage-shot-context trial. Across the 143 forecasted participants, the usage trial's shot MAE was 0.988 versus 1.008 for baseline. It was better for 80 players, worse for 63, and tied for 0.

## Usage trial by position

| group | players | baseline_shots_mae | usage_trial_shots_mae | change | trial_better | baseline_better |
| --- | --- | --- | --- | --- | --- | --- |
| all | 143 | 1.008 | 0.988 | -0.019 | 80 | 63 |
| D | 48 | 0.906 | 0.837 | -0.069 | 34 | 14 |
| F | 95 | 1.059 | 1.065 | 0.006 | 46 | 49 |

## Lineup coverage

The issued lineup scenario selected 144 players; 132 appeared, and 12 selected players did not appear. 11 other forecasted players played. 1 actual participant was not present in the archived forecast rows. Conditional shot/ice-time scoring excludes nonparticipants.

## Files

- [Complete November 4 frozen projection package](../frozen/daily_2026-11-04_20261104T153917Z/README.md)
- [Team-game scores and probabilities](team_games.csv) · [team metrics](team_metrics.csv)
- [Player shot metrics](player_shot_metrics.csv) · [all player category metrics](player_metrics.csv)
- [Scored player rows](player_projections.csv) · [lineup coverage](game_team_coverage.csv)
- [Usage trial by position](usage_trial_by_group.csv) · [scored usage trial player rows](usage_trial_player_scores.csv)
- [Experimental team SOG feature metrics](experimental_team_sog_metrics.csv)

The team SOG variants and usage trial are exploratory one-slate comparisons. They do not alter the frozen policy. The fantasy report could not be refreshed from the saved November 4 roster because that file lacks game and NHL player identifiers; no fantasy roster score is claimed here.
