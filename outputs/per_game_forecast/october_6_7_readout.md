# October 6–7 forecast readout and October 8 preparation

The frozen model overpredicted assists and shots in this small sample; goals were close in aggregate. This is a first game-level diagnostic, not evidence that the model is calibrated or that a parameter change is justified.

## Fair comparison and coverage

The evaluated forecast artifact was created at **2026-10-06T23:50:39.326692+00:00** (7:50 PM EDT October 6). Six October 6 games had already started and have no saved pregame scheduled forecasts. The three later October 6 games and all three October 7 games are eligible. Newly refreshed statistics are never used to recreate those predictions.

| game_date | matchup | score | saved_pregame_schedule_coverage |
| --- | --- | --- | --- |
| 2026-10-06 | NSH @ TOR | 4-5 | False |
| 2026-10-06 | CAR @ MTL | 6-4 | False |
| 2026-10-06 | OTT @ DET | 3-5 | False |
| 2026-10-06 | UTA @ NJD | 5-3 | False |
| 2026-10-06 | MIN @ BUF | 2-3 | False |
| 2026-10-06 | NYI @ NYR | 2-5 | False |
| 2026-10-06 | STL @ CHI | 2-4 | True |
| 2026-10-06 | VGK @ SEA | 6-2 | True |
| 2026-10-06 | FLA @ LAK | 2-1 | True |
| 2026-10-07 | PIT @ WSH | 3-5 | True |
| 2026-10-07 | COL @ WPG | 2-3 | True |
| 2026-10-07 | EDM @ ANA | 5-2 | True |

All 12 final boxscores were acquired: 432 unique skater/game rows. The six covered games have 216 skater appearances; 213 have saved usable predictions. The saved schedule pool contains 517 rows for these games, including 114 unresolved NHL identities, 24 rows without recent skater history, and 166 resolved players absent from the game boxscore. These absent rows are retained but excluded from conditional-production metrics; they are not assigned zero outcomes. Historical players attached to teams in ESPN are not necessarily current NHL roster members.

## Production if the player plays

| category | player_games | predicted_total | actual_total | mae | bias |
| --- | --- | --- | --- | --- | --- |
| goals | 213 | 38.837 | 37.000 | 0.277 | 0.009 |
| assists | 213 | 66.033 | 56.000 | 0.407 | 0.047 |
| shots | 213 | 351.907 | 311.000 | 0.962 | 0.192 |

MAE is average absolute error per player appearance. Bias is prediction minus actual; positive means overprediction. Predicted totals sum conditional means only across evaluated appearances. They are not unconditional team forecasts.

By date (same saved-pool appearance population):

| date | category | player_games | predicted_total | actual_total | mae | bias |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-06 | goals | 107 | 18.683 | 17.000 | 0.265 | 0.016 |
| 2026-10-06 | assists | 107 | 31.965 | 25.000 | 0.390 | 0.065 |
| 2026-10-06 | shots | 107 | 174.716 | 152.000 | 0.963 | 0.212 |
| 2026-10-07 | goals | 106 | 20.154 | 20.000 | 0.289 | 0.001 |
| 2026-10-07 | assists | 106 | 34.068 | 31.000 | 0.425 | 0.029 |
| 2026-10-07 | shots | 106 | 177.191 | 159.000 | 0.960 | 0.172 |

### Saved ESPN scoring-roster players

| category | player_games | predicted_total | actual_total | mae | bias |
| --- | --- | --- | --- | --- | --- |
| goals | 35 | 12.009 | 11.000 | 0.479 | 0.029 |
| assists | 35 | 20.045 | 18.000 | 0.739 | 0.058 |
| shots | 35 | 91.788 | 81.000 | 1.446 | 0.308 |

This covers all six fantasy teams, not specifically your team. Ownership is from the October 6 snapshot. 35 rostered players appeared; Connor Bedard and Zach Hyman had saved forecasts but no boxscore appearance. Their saved injury labels were INJURY_RESERVE and OUT. No participation probabilities were fitted.

Largest point misses among saved scoring-roster appearances:

| player_name | game_date | points_if_plays | points | shots_if_plays | shots |
| --- | --- | --- | --- | --- | --- |
| Jack Eichel | 2026-10-06 | 1.219 | 4.000 | 3.444 | 2.000 |
| Leon Draisaitl | 2026-10-07 | 1.467 | 4.000 | 3.040 | 2.000 |
| Tom Wilson | 2026-10-07 | 0.784 | 3.000 | 2.118 | 2.000 |
| Evan Bouchard | 2026-10-07 | 1.074 | 3.000 | 2.773 | 4.000 |
| Nathan MacKinnon | 2026-10-07 | 1.585 | 0.000 | 4.389 | 1.000 |
| Connor McDavid | 2026-10-07 | 1.673 | 3.000 | 3.467 | 1.000 |
| Beckett Sennecke | 2026-10-07 | 0.738 | 2.000 | 2.393 | 7.000 |
| Leo Carlsson | 2026-10-07 | 0.822 | 2.000 | 2.248 | 0.000 |

A mean such as 1.2 points is not a prediction that the player will score exactly one point. Burst scoring and scoreless games are expected; calibrated distributions are still missing.

## Source checks and limitations

Game IDs, season, regular-season type, final status, unique player/game keys, and G+A=P passed. Player goals reconcile with final team scores (allowing a shootout deciding goal). Florida’s October 6 skater shots total 29 while its team boxscore reports 30. This source exception is retained in source_exceptions.csv; player-level metrics use reported player SOG. The cause is unresolved. All other team-shot checks passed. No PPP game evaluation is claimed because the boxscore supplies PP goals but not player PP assists.

Two dates cannot establish stable superiority, statistical significance, or new tuning settings. Individual-game MAE is not comparable with the earlier season-average MAE because outcomes differ. Missing lineup history still prevents an availability backtest.

## Refreshed October 8 inputs and baseline forecasts

Forecast build: **2026-10-08T20:30:42.051092+00:00**. NHL reports and schedule were refreshed at **2026-10-08T20:30:30.724248+00:00** (schedule cutoff); ESPN completed at **2026-10-08T20:30:33.505129+00:00**. Game dates are Eastern time; source timestamps shown here are UTC. This is a saved snapshot through source-reported totals at retrieval, not a continuously updating feed.

The current reports contain 630 skaters and 56 goalies. Skater validation passed; one goalie SA≠SV+GA exception remains flagged. The league has 134 scoring-roster entries: 116 skaters receive conditional forecasts and 18 goalies remain unmodeled.

Today’s export covers **10 games**, **884 saved-pool rows**, and **74 scoring-roster skater rows**. The selected model remains weighted history with decay 0.5 and the existing provisional current-season update. No model settings were edited.

Highest conditional point means among all six teams’ scoring-roster skaters (not a lineup recommendation):

| player_name | nhl_team_abbrev | opponent | goals_if_plays | assists_if_plays | shots_if_plays | injury_status |
| --- | --- | --- | --- | --- | --- | --- |
| Nikita Kucherov | TBL | MIN | 0.539 | 1.128 | 3.219 | ACTIVE |
| Nathan MacKinnon | COL | CGY | 0.586 | 0.988 | 4.365 | ACTIVE |
| David Pastrnak | BOS | UTA | 0.437 | 0.844 | 3.726 | ACTIVE |
| Macklin Celebrini | SJS | STL | 0.483 | 0.790 | 3.479 | DAY_TO_DAY |
| Jack Eichel | VGK | TOR | 0.384 | 0.856 | 3.433 | ACTIVE |
| Kirill Kaprizov | MIN | TBL | 0.599 | 0.599 | 3.491 | ACTIVE |
| Nick Suzuki | MTL | NSH | 0.370 | 0.795 | 2.206 | ACTIVE |
| Mikko Rantanen | DAL | BUF | 0.387 | 0.777 | 2.498 | ACTIVE |
| William Nylander | TOR | VGK | 0.502 | 0.659 | 2.839 | ACTIVE |
| Martin Necas | COL | CGY | 0.426 | 0.710 | 2.660 | ACTIVE |
| Cale Makar | COL | CGY | 0.301 | 0.796 | 2.825 | ACTIVE |
| Clayton Keller | UTA | BOS | 0.344 | 0.745 | 2.753 | ACTIVE |

Celebrini is DAY_TO_DAY in the refreshed ESPN snapshot; his values apply only if he plays. Injuries, scratches, goalie starts, opponent effects and fantasy lineup feasibility are still unmodeled.

[All today’s player/game forecasts](../../data/processed/forecasts/per_game_20262027_20261008T203040Z/today_skater_game_forecasts.csv) · [Updated observed skater stats](../../data/processed/forecasts/per_game_20262027_20261008T203040Z/current_observed_stats.csv) · [Refreshed ESPN player forecasts](../../data/processed/forecasts/per_game_20262027_20261008T203040Z/espn_player_forecasts.csv)

## What to investigate before editing the model

1. Extend the chronological game-level sample and compare weighted, last-season and process forecasts on identical appearances with frozen pregame inputs. Keep October 6–7 as a recorded diagnostic.
2. Investigate shot overprediction through observed TOI versus predicted TOI and SOG per minute; avoid reducing all players’ rates based on six games.
3. Acquire historical eligible-roster observations to distinguish scratches/injuries from players outside the NHL population, then evaluate participation and rolling TOI.
4. Evaluate current-season update weights and rookie shrinkage in chronological validation windows before adopting a change. Goalies remain a separate baseline.

## Reproduce and inspect

Frozen forecast: `data/processed/forecasts/per_game_20262027_20261006T235037Z`. Review data: `data/processed/forecasts/game_review_20261008T203106Z`. Raw source snapshot: `data/raw/nhl/snapshots/game_review_20261008T172206Z`.

[Player-by-player comparison](../../data/processed/forecasts/game_review_20261008T203106Z/frozen_forecast_vs_actual.csv) · [Metrics](../../data/processed/forecasts/game_review_20261008T203106Z/game_metrics.csv) · [Coverage](../../data/processed/forecasts/game_review_20261008T203106Z/game_coverage.csv) · [Source exceptions](../../data/processed/forecasts/game_review_20261008T203106Z/source_exceptions.csv)

```sh
rink-lab.venv/bin/python scripts/evaluate_recent_games.py \
  --forecast data/processed/forecasts/per_game_20262027_20261006T235037Z \
  --dates 2026-10-06 2026-10-07 \
  --raw-snapshot data/raw/nhl/snapshots/game_review_20261008T172206Z \
  --current-forecast data/processed/forecasts/per_game_20262027_20261008T203040Z
```
