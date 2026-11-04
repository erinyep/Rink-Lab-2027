# Frozen model results — 2026-10-30

All 3 games scored against official NHL finals. No refitting.

| model | games | brier | log_loss | favorite_accuracy | goal_mae | predicted_goals | actual_goals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| coin_flip | 3 | 0.25 | 0.693 | nan | nan | nan | 22 |
| goal_history_baseline | 3 | 0.275 | 0.744 | 0.333 | 1.741 | 18.219 | 22 |
| new_team | 3 | 0.236 | 0.663 | 0.667 | 1.595 | 18.013 | 22 |
| original_player_sum | 3 | 0.26 | 0.714 | 0.667 | 1.689 | 18.073 | 22 |

Brier and goal MAE: lower is better. Goal MAE is per team; excludes shootout bonus goals.
Winner scores include overtime/shootouts, one home outcome per game.
Original-model probabilities are the existing Poisson/tie-split transform of saved pregame goal means.
New-minus-original Brier delta: -0.0246; paired game-bootstrap 95% interval [-0.0846, 0.0851].
One slate cannot establish lasting superiority. No market benchmark is scored in this report.

## Game results and home win probabilities

| away | home | away_score | home_score | new_home_probability | original_home_probability |
| --- | --- | --- | --- | --- | --- |
| NJD | VGK | 5 | 2 | 0.57 | 0.49 |
| WPG | FLA | 2 | 5 | 0.635 | 0.533 |
| SEA | CGY | 2 | 6 | 0.501 | 0.432 |

## Player shots and fantasy ice time

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | shots | 107 | 1.015 | -0.006 |
| candidate | shots | 107 | 1.011 | -0.021 |
| default | shots | 107 | 1.036 | 0.1 |
| opponent_form_sog_trial | shots | 107 | 1.041 | 0.116 |
| usage_shot_context_trial | shots | 107 | 1.009 | -0.054 |

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | shots | 19 | 1.309 | 0.429 |
| calibrated_opponent_sog_trial | toi_minutes | 19 | 2.104 | 1.186 |
| candidate | shots | 19 | 1.313 | 0.406 |
| candidate | toi_minutes | 19 | 2.104 | 1.186 |
| default | shots | 19 | 1.393 | 0.603 |
| default | toi_minutes | 19 | 2.104 | 1.186 |
| opponent_form_sog_trial | shots | 19 | 1.392 | 0.628 |
| opponent_form_sog_trial | toi_minutes | 19 | 2.104 | 1.186 |
| usage_shot_context_trial | shots | 19 | 1.312 | 0.326 |
| usage_shot_context_trial | toi_minutes | 19 | 1.76 | 0.844 |

These fantasy metrics cover all saved league rosters, not only Quinn. The deployed fantasy policy changes TOI only;
other usage-trial categories remain experimental. MAE is average absolute error; bias is prediction minus actual.

## Goalie counts

| model | category | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| goalie_history_baseline | shots_against | 6 | 7.395 | 2.424 |
| goalie_opponent_context_trial | shots_against | 6 | 6.804 | 2.879 |
| goalie_history_baseline | saves | 6 | 6.79 | 2.654 |
| goalie_opponent_context_trial | saves | 6 | 6.26 | 3.062 |
| goalie_history_baseline | goals_against | 6 | 0.976 | -0.231 |
| goalie_opponent_context_trial | goals_against | 6 | 0.906 | -0.182 |

Full-start predictions compared with actual starters; 55–65 minute sensitivity is in goalie_metrics.csv.
All 108 actual skater appearances covered;
5 selected lineup players did not appear.
Goalie count identity exceptions: 0.

## Saved fantasy roster ice time

2 observed skaters; old TOI MAE 2.135 minutes; new 1.696 minutes.
Includes saved active and bench skaters who played, not inferred final lineup decisions.
Absent/zero-TOI skaters remain unscored rather than assigned zero production.

[Game-by-game](team_games.csv) · [Fantasy roster](fantasy_toi_comparison.csv)

Daily player/category, team, goalie, coverage and source-hash diagnostics: `data/processed/forecasts/daily_evaluation_2026-10-30_20261104T152603618420Z`.
Actuals: `data/processed/forecasts/fantasy_game_details_20261104T152452Z`. Official source snapshot: `data/raw/nhl/snapshots/current_game_history_20262027_20261104T152427Z`.
