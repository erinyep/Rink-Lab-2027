# Frozen model results — 2026-10-27

All 11 games scored against official NHL finals. No refitting.

| model | games | brier | log_loss | favorite_accuracy | goal_mae | predicted_goals | actual_goals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| coin_flip | 11 | 0.25 | 0.693 | nan | nan | nan | 55 |
| goal_history_baseline | 11 | 0.257 | 0.708 | 0.727 | 1.555 | 67.247 | 55 |
| new_team | 11 | 0.261 | 0.717 | 0.273 | 1.523 | 67.37 | 55 |
| original_player_sum | 11 | 0.268 | 0.73 | 0.364 | 1.617 | 69.094 | 55 |

Brier and goal MAE: lower is better. Goal MAE is per team; excludes shootout bonus goals.
Winner scores include overtime/shootouts, one home outcome per game.
Original-model probabilities are the existing Poisson/tie-split transform of saved pregame goal means.
New-minus-original Brier delta: -0.0070; paired game-bootstrap 95% interval [-0.0484, 0.0338].
One slate cannot establish lasting superiority. No market benchmark is scored in this report.

## Game results and home win probabilities

| away | home | away_score | home_score | new_home_probability | original_home_probability |
| --- | --- | --- | --- | --- | --- |
| CBJ | PHI | 4 | 3 | 0.508 | 0.465 |
| BOS | CAR | 1 | 2 | 0.62 | 0.451 |
| LAK | CHI | 1 | 2 | 0.5 | 0.462 |
| MTL | STL | 2 | 0 | 0.519 | 0.491 |
| NYI | NSH | 4 | 3 | 0.52 | 0.532 |
| NJD | DAL | 5 | 1 | 0.548 | 0.538 |
| FLA | WPG | 5 | 1 | 0.5 | 0.484 |
| MIN | UTA | 3 | 1 | 0.516 | 0.556 |
| OTT | VGK | 1 | 4 | 0.546 | 0.483 |
| VAN | ANA | 6 | 5 | 0.657 | 0.543 |
| BUF | SJS | 2 | 0 | 0.477 | 0.475 |

## Player shots and fantasy ice time

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | shots | 396 | 1.01 | -0.017 |
| candidate | shots | 396 | 1.007 | -0.012 |
| default | shots | 396 | 1.03 | 0.106 |
| opponent_form_sog_trial | shots | 396 | 1.031 | 0.101 |
| usage_shot_context_trial | shots | 396 | 1.021 | -0.03 |

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | shots | 76 | 1.131 | 0.271 |
| calibrated_opponent_sog_trial | toi_minutes | 76 | 2.232 | -0.783 |
| candidate | shots | 76 | 1.125 | 0.268 |
| candidate | toi_minutes | 76 | 2.232 | -0.783 |
| default | shots | 76 | 1.176 | 0.452 |
| default | toi_minutes | 76 | 2.232 | -0.783 |
| opponent_form_sog_trial | shots | 76 | 1.183 | 0.455 |
| opponent_form_sog_trial | toi_minutes | 76 | 2.232 | -0.783 |
| usage_shot_context_trial | shots | 76 | 1.18 | 0.268 |
| usage_shot_context_trial | toi_minutes | 76 | 2.064 | -0.697 |

These fantasy metrics cover all saved league rosters, not only Quinn. The deployed fantasy policy changes TOI only;
other usage-trial categories remain experimental. MAE is average absolute error; bias is prediction minus actual.

## Goalie counts

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| goalie_history_baseline | shots_against | 22 | 4.968 | 0.907 |
| goalie_opponent_context_trial | shots_against | 22 | 5.097 | 0.566 |
| goalie_history_baseline | saves | 22 | 5.169 | 0.457 |
| goalie_opponent_context_trial | saves | 22 | 5.219 | 0.153 |
| goalie_history_baseline | goals_against | 22 | 1.494 | 0.451 |
| goalie_opponent_context_trial | goals_against | 22 | 1.497 | 0.413 |

Full-start predictions compared with actual starters; 55–65 minute sensitivity is in goalie_metrics.csv.
All 396 actual skater appearances covered;
21 selected lineup players did not appear.
Goalie count identity exceptions: 0.

## Saved fantasy roster ice time

15 observed skaters; old TOI MAE 2.167 minutes; new 2.045 minutes.
Includes saved active and bench skaters who played, not inferred final lineup decisions.
Absent/zero-TOI skaters remain unscored rather than assigned zero production.

[Game-by-game](team_games.csv) · [Fantasy roster](fantasy_toi_comparison.csv)

Daily player/category, team, goalie, coverage and source-hash diagnostics: `data/processed/forecasts/daily_evaluation_2026-10-27_20261028T214857181958Z`.
Actuals: `data/processed/forecasts/fantasy_game_details_20261028T214830Z`. Official source snapshot: `data/raw/nhl/snapshots/current_game_history_20262027_20261028T214822Z`.
