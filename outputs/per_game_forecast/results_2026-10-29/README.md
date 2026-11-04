# Frozen model results — 2026-10-29

All 11 games scored against official NHL finals. No refitting.

| model | games | brier | log_loss | favorite_accuracy | goal_mae | predicted_goals | actual_goals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| coin_flip | 11 | 0.25 | 0.693 | nan | nan | nan | 82 |
| goal_history_baseline | 11 | 0.236 | 0.666 | 0.636 | 1.4 | 67.444 | 82 |
| new_team | 11 | 0.239 | 0.669 | 0.364 | 1.423 | 68.482 | 82 |
| original_player_sum | 11 | 0.24 | 0.672 | 0.636 | 1.343 | 69.639 | 82 |

Brier and goal MAE: lower is better. Goal MAE is per team; excludes shootout bonus goals.
Winner scores include overtime/shootouts, one home outcome per game.
Original-model probabilities are the existing Poisson/tie-split transform of saved pregame goal means.
New-minus-original Brier delta: -0.0008; paired game-bootstrap 95% interval [-0.0483, 0.0498].
One slate cannot establish lasting superiority. No market benchmark is scored in this report.

## Game results and home win probabilities

| away | home | away_score | home_score | new_home_probability | original_home_probability |
| --- | --- | --- | --- | --- | --- |
| WPG | TBL | 4 | 6 | 0.668 | 0.595 |
| UTA | PIT | 4 | 3 | 0.524 | 0.439 |
| CBJ | CAR | 2 | 3 | 0.667 | 0.532 |
| CHI | DET | 1 | 4 | 0.63 | 0.513 |
| BOS | STL | 1 | 4 | 0.485 | 0.432 |
| WSH | NSH | 4 | 3 | 0.539 | 0.39 |
| MTL | DAL | 5 | 2 | 0.583 | 0.561 |
| NYI | MIN | 4 | 3 | 0.626 | 0.523 |
| BUF | ANA | 7 | 6 | 0.505 | 0.458 |
| OTT | LAK | 5 | 6 | 0.463 | 0.427 |
| VAN | SJS | 2 | 3 | 0.597 | 0.531 |

## Player shots and fantasy ice time

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | shots | 393 | 1.037 | -0.041 |
| candidate | shots | 393 | 1.037 | -0.038 |
| default | shots | 393 | 1.049 | 0.079 |
| opponent_form_sog_trial | shots | 393 | 1.048 | 0.076 |
| usage_shot_context_trial | shots | 393 | 1.036 | -0.055 |

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | shots | 76 | 1.221 | -0.366 |
| calibrated_opponent_sog_trial | toi_minutes | 76 | 2.211 | -0.507 |
| candidate | shots | 76 | 1.228 | -0.378 |
| candidate | toi_minutes | 76 | 2.211 | -0.507 |
| default | shots | 76 | 1.211 | -0.198 |
| default | toi_minutes | 76 | 2.211 | -0.507 |
| opponent_form_sog_trial | shots | 76 | 1.201 | -0.184 |
| opponent_form_sog_trial | toi_minutes | 76 | 2.211 | -0.507 |
| usage_shot_context_trial | shots | 76 | 1.227 | -0.374 |
| usage_shot_context_trial | toi_minutes | 76 | 2.075 | -0.374 |

These fantasy metrics cover all saved league rosters, not only Quinn. The deployed fantasy policy changes TOI only;
other usage-trial categories remain experimental. MAE is average absolute error; bias is prediction minus actual.

## Goalie counts

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| goalie_history_baseline | shots_against | 22 | 5.113 | 2.309 |
| goalie_opponent_context_trial | shots_against | 22 | 4.827 | 1.754 |
| goalie_history_baseline | saves | 22 | 5.348 | 2.943 |
| goalie_opponent_context_trial | saves | 22 | 4.895 | 2.444 |
| goalie_history_baseline | goals_against | 22 | 1.192 | -0.634 |
| goalie_opponent_context_trial | goals_against | 22 | 1.198 | -0.69 |

Full-start predictions compared with actual starters; 55–65 minute sensitivity is in goalie_metrics.csv.
All 396 actual skater appearances covered;
24 selected lineup players did not appear.
Goalie count identity exceptions: 0.

## Saved fantasy roster ice time

14 observed skaters; old TOI MAE 1.982 minutes; new 1.742 minutes.
Includes saved active and bench skaters who played, not inferred final lineup decisions.
Absent/zero-TOI skaters remain unscored rather than assigned zero production.

[Game-by-game](team_games.csv) · [Fantasy roster](fantasy_toi_comparison.csv)

Daily player/category, team, goalie, coverage and source-hash diagnostics: `data/processed/forecasts/daily_evaluation_2026-10-29_20261104T152602419479Z`.
Actuals: `data/processed/forecasts/fantasy_game_details_20261104T152452Z`. Official source snapshot: `data/raw/nhl/snapshots/current_game_history_20262027_20261104T152427Z`.
