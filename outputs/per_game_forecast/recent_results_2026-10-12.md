# Recent model results — October 12, 2026

Decision: keep default for fantasy-rostered player decisions tonight; retain candidate as the leading all-skater/team challenger. Avoid a stronger global shot reduction. Candidate improves the full population but worsens the saved fantasy-rostered cohort. The opponent effect has no clear incremental benefit. The new usage model improves TOI but has not established a shot-accuracy advantage over candidate.

## Coverage and timing

All 18 completed games from October 10 through the October 12 Florida–Buffalo matinee have an older October 9-issued default projection available. The five-model prospective test is limited to 11 October 10 games: 396/396 observed skaters, 22 teams and 22 starters. Three early October 10 daily projections were issued late and are excluded from the primary model comparison. October 11 has three saved default forecasts but no newly issued five-model or goalie slate; October 12’s matinee likewise uses the older default.

Tonight: Ottawa–New Jersey at 7:00 PM Eastern; Vegas–Minnesota at 8:00 PM Eastern. Florida–Buffalo is already final. Schedule checked against the [official NHL feed](https://api-web.nhle.com/v1/schedule/2026-10-12). This report does not issue new October 12 predictions.

## October 10: identical pregame populations

| model | appearances | player_mae | predicted_shots | actual_shots | team_mae | team_exact_guesses |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 396 | 1.052 | 592.548 | 593.0 | 3.531 | 1 |
| candidate | 396 | 1.051 | 592.549 | 593.0 | 3.455 | 2 |
| default | 396 | 1.066 | 639.985 | 593.0 | 3.751 | 2 |
| opponent_form_sog_trial | 396 | 1.066 | 639.983 | 593.0 | 3.763 | 2 |
| usage_shot_context_trial | 396 | 1.054 | 588.522 | 593.0 | 3.523 | 0 |

Player MAE measures absolute error per appearance. Team MAE uses official NHL SOG and the same assumed lineup for every model; shots-against mirrors are not counted as extra samples. Exact guesses are out of 22 team outcomes. Candidate improves player SOG MAE about 1.4% and team SOG MAE about 7.9% versus default. Its total being close to actual does not imply accurate player allocation.

## Fantasy-rostered players: the recommendation changes

| model | appearances | mae | predicted_shots | actual_shots |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 78 | 1.409 | 184.685 | 216.0 |
| candidate | 78 | 1.411 | 184.352 | 216.0 |
| default | 78 | 1.376 | 199.11 | 216.0 |
| opponent_form_sog_trial | 78 | 1.374 | 199.469 | 216.0 |
| usage_shot_context_trial | 78 | 1.388 | 184.943 | 216.0 |

These 78 appearances are identified using the saved pregame fantasy ownership, not current ownership or outcomes. Default underpredicted their combined shots by 16.89; candidate underpredicted by 31.65. Candidate was worse in player MAE for each of the six fantasy teams. Do not calibrate directly to fantasy ownership; test prior projected shot rate, position and TOI/PP role as hockey-relevant strata in later untouched games.

| fantasy_team_name | model | appearances | mae | predicted_shots | actual_shots |
| --- | --- | --- | --- | --- | --- |
| Bedardians of the Galaxy | candidate | 16 | 1.354 | 37.034 | 38.0 |
| Bedardians of the Galaxy | default | 16 | 1.346 | 39.998 | 38.0 |
| Geekie Squad | candidate | 10 | 1.145 | 26.991 | 34.0 |
| Geekie Squad | default | 10 | 1.079 | 29.152 | 34.0 |
| Judge, Juraj and Executioner | candidate | 11 | 1.706 | 22.604 | 36.0 |
| Judge, Juraj and Executioner | default | 11 | 1.622 | 24.413 | 36.0 |
| Le Tang Clan | candidate | 15 | 1.336 | 34.764 | 39.0 |
| Le Tang Clan | default | 15 | 1.324 | 37.547 | 39.0 |
| Parker's Perfect Team | candidate | 15 | 1.516 | 36.902 | 43.0 |
| Parker's Perfect Team | default | 15 | 1.486 | 39.856 | 43.0 |
| Quinn Short for Quinnificent | candidate | 11 | 1.399 | 26.057 | 26.0 |
| Quinn Short for Quinnificent | default | 11 | 1.365 | 28.143 | 26.0 |

Quinn Short for Quinnificent illustrates the difference: candidate’s aggregate total is close to 26 actual shots, but default has lower individual-player error. Totals can cancel errors across players.

## Other categories and goalies

| model | category | appearances | mae | bias | predicted_total | actual_total |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | assists | 396 | 0.362 | 0.048 | 112.979 | 94.0 |
| calibrated_opponent_sog_trial | goals | 396 | 0.254 | 0.032 | 69.547 | 57.0 |
| calibrated_opponent_sog_trial | hits | 396 | 0.851 | 0.01 | 463.076 | 459.0 |
| calibrated_opponent_sog_trial | penalty_minutes | 396 | 0.806 | -0.115 | 192.652 | 238.0 |
| calibrated_opponent_sog_trial | plus_minus | 396 | 0.642 | 0.014 | 2.569 | -3.0 |
| calibrated_opponent_sog_trial | points | 396 | 0.488 | 0.08 | 182.526 | 151.0 |
| calibrated_opponent_sog_trial | pp_points | 396 | 0.161 | -0.002 | 40.179 | 41.0 |
| calibrated_opponent_sog_trial | toi_minutes | 396 | 2.266 | 0.084 | 6622.949 | 6589.583 |
| candidate | assists | 396 | 0.362 | 0.048 | 112.979 | 94.0 |
| candidate | goals | 396 | 0.254 | 0.032 | 69.547 | 57.0 |
| candidate | hits | 396 | 0.851 | 0.01 | 463.076 | 459.0 |
| candidate | penalty_minutes | 396 | 0.806 | -0.115 | 192.652 | 238.0 |
| candidate | plus_minus | 396 | 0.642 | 0.014 | 2.569 | -3.0 |
| candidate | points | 396 | 0.488 | 0.08 | 182.526 | 151.0 |
| candidate | pp_points | 396 | 0.161 | -0.002 | 40.179 | 41.0 |
| candidate | toi_minutes | 396 | 2.266 | 0.084 | 6622.949 | 6589.583 |
| default | assists | 396 | 0.367 | 0.059 | 117.407 | 94.0 |
| default | goals | 396 | 0.254 | 0.032 | 69.547 | 57.0 |
| default | hits | 396 | 0.851 | 0.01 | 463.076 | 459.0 |
| default | penalty_minutes | 396 | 0.806 | -0.115 | 192.652 | 238.0 |
| default | plus_minus | 396 | 0.642 | 0.014 | 2.569 | -3.0 |
| default | points | 396 | 0.492 | 0.091 | 186.954 | 151.0 |
| default | pp_points | 396 | 0.161 | -0.002 | 40.179 | 41.0 |
| default | toi_minutes | 396 | 2.266 | 0.084 | 6622.949 | 6589.583 |
| opponent_form_sog_trial | assists | 396 | 0.367 | 0.059 | 117.407 | 94.0 |
| opponent_form_sog_trial | goals | 396 | 0.254 | 0.032 | 69.547 | 57.0 |
| opponent_form_sog_trial | hits | 396 | 0.851 | 0.01 | 463.076 | 459.0 |
| opponent_form_sog_trial | penalty_minutes | 396 | 0.806 | -0.115 | 192.652 | 238.0 |
| opponent_form_sog_trial | plus_minus | 396 | 0.642 | 0.014 | 2.569 | -3.0 |
| opponent_form_sog_trial | points | 396 | 0.492 | 0.091 | 186.954 | 151.0 |
| opponent_form_sog_trial | pp_points | 396 | 0.161 | -0.002 | 40.179 | 41.0 |
| opponent_form_sog_trial | toi_minutes | 396 | 2.266 | 0.084 | 6622.949 | 6589.583 |
| usage_shot_context_trial | assists | 396 | 0.362 | 0.048 | 112.979 | 94.0 |
| usage_shot_context_trial | goals | 396 | 0.254 | 0.032 | 69.547 | 57.0 |
| usage_shot_context_trial | hits | 396 | 0.851 | 0.01 | 463.076 | 459.0 |
| usage_shot_context_trial | penalty_minutes | 396 | 0.806 | -0.115 | 192.652 | 238.0 |
| usage_shot_context_trial | plus_minus | 396 | 0.642 | 0.014 | 2.569 | -3.0 |
| usage_shot_context_trial | points | 396 | 0.488 | 0.08 | 182.526 | 151.0 |
| usage_shot_context_trial | pp_points | 396 | 0.161 | -0.002 | 40.179 | 41.0 |
| usage_shot_context_trial | toi_minutes | 396 | 2.115 | 0.031 | 6601.96 | 6589.583 |

Usage-model TOI MAE fell from 2.266 to 2.115 minutes (about 6.7%); its SOG MAE is still slightly worse than candidate. All models predicted 69.55 goals versus 57 across these appearances. Assists remained high after calibration (112.98 versus 94); hits and PPP totals were much closer. PIM was underestimated. These are diagnostics, not new fitted correction factors.

| model | starters | shots_against_mae | saves_mae | goals_against_mae |
| --- | --- | --- | --- | --- |
| goalie_history_baseline | 22 | 3.638 | 4.027 | 1.336 |
| goalie_opponent_context_trial | 22 | 3.685 | 3.932 | 1.351 |

All 22 scored starters played between 55 and 65 minutes. The opponent goalie trial improves saves slightly but worsens shots-against and goals-against errors slightly. There is no broad goalie winner. Starting probabilities, relief and duration remain separate evaluation targets in the detailed artifact.

## Strength of evidence

| model | mae_difference_vs_default | bootstrap_95_lower | bootstrap_95_upper | games_improved |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | -0.015 | -0.025 | -0.004 | 9 |
| candidate | -0.015 | -0.025 | -0.004 | 9 |
| default | 0.0 | 0.0 | 0.0 | 0 |
| opponent_form_sog_trial | 0.0 | -0.002 | 0.002 | 6 |
| usage_shot_context_trial | -0.012 | -0.037 | 0.01 | 5 |

Approximate 95% intervals resample 11 games, 20,000 times with seed 20261012, using equal-game mean paired errors. Negative values favor the trial. This small-sample exploratory bootstrap does not account for all model-selection comparisons. Candidate improves 9/11 games; usage improves 5/11 and its interval includes no improvement.

## Independent ESPN benchmark

| model | appearances | mae |
| --- | --- | --- |
| calibrated_opponent_sog_trial | 200 | 1.218 |
| candidate | 200 | 1.217 |
| default | 200 | 1.224 |
| opponent_form_sog_trial | 200 | 1.226 |
| usage_shot_context_trial | 200 | 1.222 |
| ESPN_season_average_benchmark | 200 | 1.225 |

These are the same 200 appearances with an available frozen ESPN season-average projection. Do not compare these MAEs directly with the 396-player table. ESPN is competitive but provides no clear improvement, and is not matchup-adjusted here.

## October 11 and today’s completed matinee

| date | category | player_games | predicted_total | actual_total | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-10-11 | goals | 104 | 19.467 | 19.0 | 0.286 | 0.004 | 0.429 |
| 2026-10-11 | assists | 104 | 30.517 | 36.0 | 0.442 | -0.053 | 0.557 |
| 2026-10-11 | shots | 104 | 164.392 | 152.0 | 0.984 | 0.119 | 1.28 |
| 2026-10-12 | goals | 36 | 6.289 | 8.0 | 0.28 | -0.048 | 0.425 |
| 2026-10-12 | assists | 36 | 10.193 | 15.0 | 0.476 | -0.134 | 0.666 |
| 2026-10-12 | shots | 36 | 59.274 | 55.0 | 1.071 | 0.119 | 1.34 |

October 11 coverage is 104/108 actual skaters; today’s matinee is 36/36. These are older, previously issued default conditional forecasts, not reconstructed versions of the new models. Retain their age and population distinction.

## Lineups and large misses

Of 395 named skaters selected in the eleven pregame lineup scenarios, 377 appeared. Montreal’s team scenario also included an unidentified defense replacement. Actual player forecasts cover all 396 appearances even when the lineup selection was wrong. Team lineup error and player rate error are distinct.

| team | opponent | projection_mean | shots | ae |
| --- | --- | --- | --- | --- |
| NSH | OTT | 28.489 | 18 | 10.489 |
| OTT | NSH | 28.893 | 20 | 8.893 |
| PIT | DAL | 29.169 | 21 | 8.169 |
| CAR | CHI | 31.471 | 39 | 7.529 |
| TOR | COL | 30.041 | 23 | 7.041 |
| CBJ | STL | 29.465 | 23 | 6.465 |
| NYI | TBL | 28.469 | 23 | 5.469 |
| BUF | UTA | 28.841 | 24 | 4.841 |

## Adjustments to prioritize before the next release

1. Keep default visible for fantasy-rostered decisions and retain candidate as the all-skater/team challenger; do not strengthen the global calibration multiplier.
2. Refresh tonight’s eligible rosters, injury labels and goalie starter information before issuance; preserve all timing labels.
3. Split the next usage experiment into TOI-only, shot-rate-only and context-only versions. Keep the same lineup and evaluate paired outcomes.
4. Evaluate calibration by pregame shot/TOI/position strata; current ownership reversal suggests a blanket multiplier is too coarse. Fit on past games and test later games, rather than tuning tonight’s factors to these results.
5. Investigate goal and assist overprediction separately from SOG; save shares and goalie duration need their own validation.
6. Maintain frozen sources and write evaluations to separate folders. A display-only fallback-label bug was corrected prospectively; original rookie rates already used shrinkage, and frozen forecasts remain unchanged.

## Inspect and reproduce

Frozen daily bundle: `data/processed/forecasts/daily_2026-10-10_20261010T203436Z`. Final enriched observations: `data/processed/forecasts/fantasy_game_details_20261012T221953Z`. Older baseline evaluation: `data/processed/forecasts/game_review_20261012T222022Z`.

[All recent game results](../../data/processed/forecasts/game_review_20261012T222022Z/game_coverage.csv) · [Older default player comparisons](../../data/processed/forecasts/game_review_20261012T222022Z/frozen_forecast_vs_actual.csv)

```sh
rink-lab.venv/bin/python scripts/write_recent_model_readout.py \
  --bundle data/processed/forecasts/daily_2026-10-10_20261010T203436Z \
  --actuals data/processed/forecasts/fantasy_game_details_20261012T221953Z \
  --boxscores data/raw/nhl/snapshots/current_game_history_20262027_20261012T221922Z \
  --older-review data/processed/forecasts/game_review_20261012T222022Z
```
