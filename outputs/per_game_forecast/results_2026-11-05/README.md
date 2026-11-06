# November 5 frozen forecast results

The 11-game November 5 release was issued before puck drop and scored against the refreshed official NHL boxscores and player stats. No predictions were reconstructed after games or refit on these outcomes. Player and goalie forecasts are conditional scenarios; nonparticipants are not assigned zero production.

## All-player shots

| model | rows_scored | games_scored | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 395 | 11 | 1.011 | -0.131 |
| candidate | 395 | 11 | 1.013 | -0.126 |
| default | 395 | 11 | 1.022 | -0.008 |
| opponent_form_sog_trial | 395 | 11 | 1.022 | -0.013 |
| usage_shot_context_trial | 395 | 11 | 1.018 | -0.151 |

## Conditional ice time

| model | rows_scored | mae | bias |
| --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 395 | 2.334 | 0.113 |
| candidate | 395 | 2.334 | 0.113 |
| default | 395 | 2.334 | 0.113 |
| opponent_form_sog_trial | 395 | 2.334 | 0.113 |
| usage_shot_context_trial | 395 | 2.177 | 0.133 |

The daily trial comparison is one slate. Compare it with the saved November 4 results and the earlier season-wide evidence before changing policy. Calibrated-opponent SOG remains the NHL-wide selected model based on prior multi-date evidence; fantasy SOG policy remains separate.

The updated [all-date review through November 5](../season_through_2026-11-05/README.md) combines 88 saved forecast games and re-scores their player outcomes against one current official actuals vintage.

Across the two latest saved slates (November 4–5; 15 games), player shots MAE was 1.007 for calibrated-opponent, 1.009 for candidate, 1.010 for usage-shot-context, 1.018 for default, and 1.019 for opponent-form. On this short two-date cohort, calibrated-opponent was closer than default for 293 of 538 player-games. Defense and forward breakouts are in [the two-date table](two_date_shots_metrics.csv). This small cohort supports keeping the established policy under review; it does not support another promotion.

## Team totals and goalie scenarios

Official NHL team shots against the saved team projections:

| model | games | team_rows | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 11 | 22 | 4.400 | -2.497 |
| candidate | 11 | 22 | 4.265 | -2.421 |
| default | 11 | 22 | 3.646 | -0.316 |
| opponent_form_sog_trial | 11 | 22 | 3.755 | -0.397 |
| usage_shot_context_trial | 11 | 22 | 5.033 | -2.949 |

Goalie MAE is against the goalies recorded as starters. The full-start prediction is a 60-minute scenario, so use `goalie_metrics.csv` rows ending in `_55_65_min` for the duration sensitivity view. Starts and 11-game samples do not establish better goalie selection.

## Coverage

| games | forecast_player_ids | forecast_model_rows | players_with_positive_toi | modeled_positive_toi_players | unmodeled_actual_players | selected_scenario_players | selected_scenario_appeared | selected_scenario_nonparticipants |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 485 | 2425 | 396 | 395 | 1 | 395 | 380 | 15 |

## Model and data update notes

The November 6 player forecast uses results through November 5 (261 final games, 9,395 positive-TOI player/game rows; all forecasted game-history keys reconciled with the refreshed TOI snapshot). The retrospective 2025-26 validation selected the weighted season-rate method (score 0.944 versus 1.000 for last-season-only on the configured G/A/SOG selection metric); on the held-out 2025-26 population, its shots MAE is 0.333 versus 0.333 for last-season-only and ice-time MAE 1.596 versus 1.590. These are retrospective season-level results, not evidence to replace the current daily category policies.

NHL PBP has four team-game SOG disagreements flagged; MoneyPuck shot inputs quarantined 103 games. Three goalie source rows failed the saves identity check in the refreshed season snapshot and remain excluded from valuation. None were silently corrected.

- [Complete November 5 frozen projections](../frozen/daily_2026-11-05_20261105T204849Z/README.md)
- [Player metrics](player_metrics.csv) · [scored player projections](player_projections_scored.csv)
- [Team metrics](team_metrics.csv) · [game/team scores](team_games.csv)
- [Goalie metrics](goalie_metrics.csv) · [confirmed-starter scores](goalie_starter_scores.csv)
- [Two-date shots comparison](two_date_shots_metrics.csv) · [coverage](coverage.csv)

No separate direct team win-probability forecast was saved for November 5, so none is reconstructed here. The new November 6 direct-team issue will be evaluated after those games finish.
