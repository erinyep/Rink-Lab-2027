# October 9 postgame readout

All four final regular-season games, eight teams. Frozen means are unchanged. Refreshed-lineup team totals were derived after puck drop from frozen pregame inputs, not independently issued pregame forecasts.

Conditional player comparison covers 143 modeled appearances out of 144 observed positive-TOI skaters. Unobserved roster members remain missing and are not scored as zero.

## Player results

| model | category | appearances | predicted_total | actual_total | mae | bias | rmse | interval_p10_p90_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate | assists | 143 | 39.819 | 36.0 | 0.385 | 0.027 | 0.521 | 0.944 |
| candidate | goals | 143 | 25.29 | 22.0 | 0.27 | 0.023 | 0.389 | 0.958 |
| candidate | hits | 143 | 168.377 | 167.0 | 0.992 | 0.01 | 1.332 | 0.902 |
| candidate | points | 143 | 65.109 | 58.0 | 0.521 | 0.05 | 0.683 | 0.93 |
| candidate | pp_points | 143 | 14.774 | 9.0 | 0.137 | 0.04 | 0.236 | 1.0 |
| candidate | shots | 143 | 207.955 | 213.0 | 1.048 | -0.035 | 1.363 | 0.86 |
| default | assists | 143 | 41.38 | 36.0 | 0.39 | 0.038 | 0.523 | 0.944 |
| default | goals | 143 | 25.29 | 22.0 | 0.27 | 0.023 | 0.389 | 0.958 |
| default | hits | 143 | 168.377 | 167.0 | 0.992 | 0.01 | 1.332 | 0.902 |
| default | points | 143 | 66.669 | 58.0 | 0.525 | 0.061 | 0.685 | 0.93 |
| default | pp_points | 143 | 14.774 | 9.0 | 0.137 | 0.04 | 0.236 | 1.0 |
| default | shots | 143 | 224.602 | 213.0 | 1.058 | 0.081 | 1.377 | 0.867 |
| opponent_form_sog_trial | assists | 143 | 41.38 | 36.0 | 0.39 | 0.038 | 0.523 | 0.944 |
| opponent_form_sog_trial | goals | 143 | 25.29 | 22.0 | 0.27 | 0.023 | 0.389 | 0.958 |
| opponent_form_sog_trial | hits | 143 | 168.377 | 167.0 | 0.992 | 0.01 | 1.332 | 0.902 |
| opponent_form_sog_trial | points | 143 | 66.669 | 58.0 | 0.525 | 0.061 | 0.685 | 0.93 |
| opponent_form_sog_trial | pp_points | 143 | 14.774 | 9.0 | 0.137 | 0.04 | 0.236 | 1.0 |
| opponent_form_sog_trial | shots | 143 | 224.621 | 213.0 | 1.059 | 0.081 | 1.379 | 0.867 |

## Team shots and chance context

| game_id | team | opponent | actual | candidate | default | opponent_form_sog_trial | xOnGoalFor | xOnGoalAgainst | xGoalsFor | xGoalsAgainst |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026020066 | DET | SEA | 40 | 25.785 | 27.849 | 28.223 | 44.086 | 30.903 | 3.852 | 3.437 |
| 2026020066 | SEA | DET | 24 | 25.342 | 27.371 | 27.15 | 30.903 | 44.086 | 3.437 | 3.852 |
| 2026020067 | NYR | WSH | 22 | 25.931 | 28.007 | 27.873 | 25.741 | 32.372 | 2.887 | 4.525 |
| 2026020067 | WSH | NYR | 27 | 29.388 | 31.74 | 31.184 | 32.372 | 25.741 | 4.525 | 2.887 |
| 2026020068 | CBJ | PIT | 47 | 26.61 | 28.74 | 28.402 | 45.709 | 25.716 | 5.244 | 3.186 |
| 2026020068 | PIT | CBJ | 22 | 27.064 | 29.231 | 29.773 | 25.716 | 45.709 | 3.186 | 5.244 |
| 2026020069 | ANA | WPG | 17 | 24.978 | 26.977 | 27.228 | 22.435 | 23.491 | 3.757 | 2.342 |
| 2026020069 | WPG | ANA | 17 | 24.276 | 26.219 | 26.317 | 23.491 | 22.435 | 2.342 | 3.757 |

The three model columns are pregame shot-on-goal expectations. xOnGoalFor/Against are MoneyPuck postgame chance-context measures: expected on-target outcomes of observed unblocked attempts, assuming average shooting talent. xGoalsFor/Against measure expected goals instead. They are not forecasts of the game that were available beforehand. Team shot outcomes use official NHL boxscores; player outcomes use individual NHL skater stats.

MoneyPuck/NHL shot-feed audit (discrepancies retained):
| team | shotsOnGoalFor | nhl_shots_for | shotsOnGoalAgainst | nhl_shots_against |
| --- | --- | --- | --- | --- |
| NYR | 22.0 | 22.0 | 27.0 | 27.0 |
| PIT | 22.0 | 22.0 | 45.0 | 47.0 |
| WPG | 16.0 | 17.0 | 17.0 | 17.0 |
| ANA | 17.0 | 17.0 | 16.0 | 17.0 |
| SEA | 24.0 | 24.0 | 40.0 | 40.0 |
| WSH | 27.0 | 27.0 | 22.0 | 22.0 |
| CBJ | 45.0 | 47.0 | 22.0 | 22.0 |
| DET | 40.0 | 40.0 | 24.0 | 24.0 |

## Goalies

| model | shots_against_absolute_error | saves_absolute_error | goals_against_absolute_error |
| --- | --- | --- | --- |
| goalie_history_baseline | 13.105 | 12.547 | 1.425 |
| goalie_opponent_context_trial | 12.096 | 11.634 | 1.341 |

Actual starters only (eight per model; includes shortened starts and overtime):
| model | shots_against_absolute_error | saves_absolute_error | goals_against_absolute_error |
| --- | --- | --- | --- |
| goalie_history_baseline | 11.786 | 11.514 | 1.355 |
| goalie_opponent_context_trial | 11.139 | 10.928 | 1.31 |

Errors above cover positive-TOI, internally consistent goalie observations; backups are excluded from conditional count scoring. Full-60 projections are imperfect comparisons for partial starts, pulls and relief. Check actual_starter and actual_toi_seconds in the consolidated goalie table. Win probabilities remain provisional team-win proxies.

## Coverage and lineup assumptions

| team | actual_skaters | actual_skaters_with_forecast | refreshed_lineup_actual_overlap |
| --- | --- | --- | --- |
| DET | 18 | 18 | 17 |
| SEA | 18 | 18 | 17 |
| WSH | 18 | 18 | 18 |
| NYR | 18 | 18 | 18 |
| CBJ | 18 | 17 | 17 |
| PIT | 18 | 18 | 18 |
| WPG | 18 | 18 | 17 |
| ANA | 18 | 18 | 17 |

## Next decisions

Keep the default baseline while accumulating chronological evidence. Compare the SOG trial on identical appearances and lineup versions; four games cannot validate an opponent model. Prioritize actual lineup/TOI prediction and rookie shrinkage before stronger opponent adjustments. Acquire historical MoneyPuck team game data for lagged, strength-specific shot volume and xOnGoal rates, with prior-season shrinkage and cutoff checks. Compare lagged raw SOG, unblocked attempts, xOnGoal and xGoals in held-out games before using any as a feature. Never use this game’s postgame chance metrics to predict this same game.

MoneyPuck data: [published downloads](https://moneypuck.com/data.htm) and [data dictionary](https://peter-tanner.com/moneypuck/downloads/MoneyPuckDataDictionaryForPlayers.csv). Non-commercial research use; credit MoneyPuck.

Sources: `data/processed/forecasts/fantasy_game_details_20261010T200934Z`, `data/raw/nhl/snapshots/game_review_20261010T200920Z`, `data/raw/moneypuck/snapshots/team_games_20261010T201108Z`. Convenience view: `data/processed/forecasts/october_9_review/`.

Reproduce after restoring the archived pre-evaluation convenience view:
```sh
rink-lab.venv/bin/python scripts/evaluate_october_9.py \
  --actuals data/processed/forecasts/fantasy_game_details_20261010T200934Z \
  --boxscores data/raw/nhl/snapshots/game_review_20261010T200920Z \
  --moneypuck-snapshot data/raw/moneypuck/snapshots/team_games_20261010T201108Z
```

## Fourth model: retrospective combined trial

| model | appearances | player_mae | player_rmse | team_mae |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 143 | 1.05 | 1.365 | 7.816 |
| candidate | 143 | 1.048 | 1.363 | 7.823 |
| default | 143 | 1.058 | 1.377 | 8.87 |
| opponent_form_sog_trial | 143 | 1.059 | 1.379 | 8.862 |

The hybrid combines fixed October 6–7 shot/assist calibration with the frozen opponent/form SOG factor. Other categories follow candidate. It is exploratory after observing October 9, not an issued pregame success. Missing context falls back to a flagged neutral factor. Jake O’Brien now has a SOG-only past-position prior; he is not assumed to play. Damon Severson was absent from the saved NHL roster context and remains an uncovered actual appearance; adding him using the postgame lineup would misstate pregame coverage. Source shot-feed discrepancies remain flagged, without manufactured corrections.
