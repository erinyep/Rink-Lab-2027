# Results through 2026-10-25

17 finals in this update; 12 have saved daily-model forecasts. Season history contains 184 finals. Full model comparisons cover 48 games.

[Interactive results](index.html) · [Every final score](game_results.csv).

| game_id | date | away | home | away_score | home_score | final_period_type | saved_daily_forecast |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026020168 | 2026-10-24 | ANA | PHI | 5 | 4 | REG | True |
| 2026020169 | 2026-10-24 | LAK | NJD | 1 | 3 | REG | True |
| 2026020170 | 2026-10-24 | SJS | BOS | 4 | 6 | REG | True |
| 2026020171 | 2026-10-24 | NYR | OTT | 4 | 7 | REG | True |
| 2026020172 | 2026-10-24 | NSH | PIT | 2 | 3 | OT | True |
| 2026020173 | 2026-10-24 | BUF | WSH | 3 | 4 | OT | True |
| 2026020174 | 2026-10-24 | VGK | CBJ | 1 | 2 | OT | True |
| 2026020175 | 2026-10-24 | CAR | STL | 4 | 0 | REG | True |
| 2026020176 | 2026-10-24 | TOR | EDM | 7 | 2 | REG | True |
| 2026020177 | 2026-10-24 | TBL | UTA | 4 | 5 | OT | True |
| 2026020178 | 2026-10-24 | DET | CGY | 1 | 4 | REG | True |
| 2026020179 | 2026-10-24 | MIN | SEA | 5 | 1 | REG | True |
| 2026020180 | 2026-10-25 | FLA | CHI | 3 | 2 | REG | False |
| 2026020181 | 2026-10-25 | NYI | DAL | 3 | 6 | REG | False |
| 2026020182 | 2026-10-25 | MTL | WPG | 2 | 1 | REG | False |
| 2026020183 | 2026-10-25 | COL | NSH | 2 | 6 | REG | False |
| 2026020184 | 2026-10-25 | MIN | VAN | 4 | 2 | REG | False |

Frozen forecasts are preserved. Official scoring excludes shootout deciding goals from player/team scoring counts;
final game winners include overtime and shootouts. No forecast is reconstructed for uncovered dates.
Every daily evaluation uses the same actuals vintage as the season review. Missing participants are not scored as
zero conditional production. Fantasy roster labels reflect the saved issue, not current ownership.

## Probability benchmark

| model | games | brier | log_loss | favorite_accuracy |
| --- | --- | --- | --- | --- |
| even_baseline | 12 | 0.25 | 0.693 | nan |
| kalshi_home_midpoint | 12 | 0.226 | 0.644 | 0.667 |
| team_probability_trial | 12 | 0.25 | 0.692 | 0.5 |

One binary home outcome per game; the complementary away contract is not another sample.
These are official NHL-outcome probability scores, not exchange settlement verification or P&L.
No model promotion from one slate. The broader historical probability screen remains separate.

## Fantasy shots uncertainty

| population | model | games | appearances | mae_delta_vs_default | lower_95 | upper_95 | games_improved | category |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| saved_fantasy_roster | calibrated_opponent_sog_trial | 48 | 347 | -0.008 | -0.028 | 0.013 | 28 | shots |
| saved_fantasy_roster | candidate | 48 | 347 | -0.006 | -0.027 | 0.016 | 27 | shots |
| saved_fantasy_roster | default | 48 | 347 | 0.0 | 0.0 | 0.0 | 0 | shots |
| saved_fantasy_roster | opponent_form_sog_trial | 48 | 347 | -0.001 | -0.008 | 0.005 | 26 | shots |
| saved_fantasy_roster | usage_shot_context_trial | 48 | 347 | -0.007 | -0.036 | 0.022 | 27 | shots |

## Missing forecasts on 2026-10-24

| game_id | game_date | player_id | name | team | position | goals | assists | points | shots | hits | penalty_minutes | plus_minus | pp_goals | pp_assists | pp_points | toi_seconds | toi_minutes | issue_timing |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026020168 | 2026-10-24 | 8484262 | T. Mitchell | ANA | D | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1206 | 20.1 | pregame |
| 2026020172 | 2026-10-24 | 8482993 | A. Hayes | PIT | R | 0 | 0 | 0 | 5 | 3 | 0 | 0 | 0 | 0 | 0 | 763 | 12.717 | pregame |

The saved fantasy skater CSV, when supplied, uses original active/bench labels and is not an audit of final ESPN lineup changes.

## Source discrepancies and feature results

October 24 goalie counts are scored on 22 eligible starts. Tristan Jarry (30 shots against, 25 saves, 6 goals against) and Karel Vejmelka (32, 29, 4) fail the shots = saves + goals identity in the official source. Their rows remain in the audit; no count correction is invented.

[October 24 frozen feature scores](feature_results_2026-10-24/metrics.csv) · [Paired feature uncertainty](feature_results_2026-10-24/paired_uncertainty.csv).
