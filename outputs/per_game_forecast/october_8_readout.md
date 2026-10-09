# October 8 projected versus actual

The candidate was frozen using October 6–7 only and evaluated without retuning. Its October 8 predictions were reconstructed on October 9 from saved pregame features; the baseline was genuinely saved before puck drop. Do not call the candidate a forecast issued pregame.

## Matched appearances

| model | category | player_games | projected | actual | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | goals | 351 | 62.605 | 61.000 | 0.285 | 0.005 | 0.454 |
| baseline | assists | 351 | 104.797 | 106.000 | 0.418 | -0.003 | 0.567 |
| baseline | shots | 351 | 563.911 | 542.000 | 1.109 | 0.062 | 1.430 |
| candidate | goals | 351 | 62.605 | 61.000 | 0.285 | 0.005 | 0.454 |
| candidate | assists | 351 | 100.845 | 106.000 | 0.414 | -0.015 | 0.567 |
| candidate | shots | 351 | 522.114 | 542.000 | 1.091 | -0.057 | 1.429 |

Results concern production conditional on playing. Only actual appearances with baseline and candidate means enter these metrics. Absent/unknown players remain in the all-rows export; no zero production or appearance probability is invented. PPP comes from validated official scoring summaries.

## Saved scoring-roster players across all six fantasy teams

| model | category | player_games | projected | actual | mae | bias |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | goals | 68 | 21.493 | 18.000 | 0.448 | 0.051 |
| baseline | assists | 68 | 36.156 | 42.000 | 0.639 | -0.086 |
| baseline | shots | 68 | 166.936 | 158.000 | 1.464 | 0.131 |
| baseline | points | 68 | 57.650 | 60.000 | 0.780 | -0.035 |
| baseline | hits | 68 | 63.241 | 67.000 | 0.880 | -0.055 |
| baseline | penalty_minutes | 68 | 32.717 | 20.000 | 0.639 | 0.187 |
| baseline | plus_minus | 68 | 4.425 | 0.000 | 0.950 | 0.065 |
| baseline | toi_minutes | 68 | 1369.239 | 1344.433 | 2.426 | 0.365 |
| baseline | pp_points | 68 | 18.122 | 23.000 | 0.443 | -0.072 |
| candidate | goals | 68 | 21.493 | 18.000 | 0.448 | 0.051 |
| candidate | assists | 68 | 34.793 | 42.000 | 0.638 | -0.106 |
| candidate | shots | 68 | 154.563 | 158.000 | 1.429 | -0.051 |
| candidate | points | 68 | 56.286 | 60.000 | 0.777 | -0.055 |
| candidate | hits | 68 | 63.241 | 67.000 | 0.880 | -0.055 |
| candidate | penalty_minutes | 68 | 32.717 | 20.000 | 0.639 | 0.187 |
| candidate | plus_minus | 68 | 4.425 | 0.000 | 0.950 | 0.065 |
| candidate | toi_minutes | 68 | 1369.239 | 1344.433 | 2.426 | 0.365 |
| candidate | pp_points | 68 | 18.122 | 23.000 | 0.443 | -0.072 |

## Additional frozen-input comparators

| model | category | player_games | projected | actual | mae | bias |
| --- | --- | --- | --- | --- | --- | --- |
| last_season | goals | 351 | 62.818 | 61.000 | 0.282 | 0.005 |
| last_season | assists | 351 | 105.821 | 106.000 | 0.422 | -0.001 |
| last_season | shots | 351 | 555.566 | 542.000 | 1.105 | 0.039 |
| process | goals | 351 | 63.201 | 61.000 | 0.287 | 0.006 |
| process | assists | 351 | 105.517 | 106.000 | 0.421 | -0.001 |
| process | shots | 351 | 566.969 | 542.000 | 1.109 | 0.071 |

These diagnostic comparators use the same original October 8 panel and preselected parameters. Do not choose a new winner from this single night.

## Coverage and stored sources

| game_date | matchup | score | actual_skater_rows |
| --- | --- | --- | --- |
| 2026-10-08 | UTA @ BOS | 1-6 | 36 |
| 2026-10-08 | DAL @ BUF | 4-0 | 36 |
| 2026-10-08 | NSH @ MTL | 5-2 | 36 |
| 2026-10-08 | PHI @ OTT | 1-2 | 36 |
| 2026-10-08 | MIN @ TBL | 2-3 | 36 |
| 2026-10-08 | VAN @ CAR | 2-7 | 36 |
| 2026-10-08 | CHI @ NYI | 1-4 | 36 |
| 2026-10-08 | SJS @ STL | 3-2 | 36 |
| 2026-10-08 | COL @ CGY | 7-3 | 36 |
| 2026-10-08 | TOR @ VGK | 3-4 | 36 |

Evaluated 351 player appearances and 68 scoring-roster appearances. Preserved 882 forecast rows. ESPN aliases are retained in `data/processed/forecasts/game_review_20261009T192557Z/espn_alias_rows.csv` and deduplicated by NHL player/game for evaluation only. Forecast values for aliases agreed.

## Latest stats and fantasy coverage

New forecast build: `data/processed/forecasts/per_game_20262027_20261009T192558Z`. ESPN source: `data/raw/espn/snapshots/espn_2027_20261009T192520Z`. Official current-season skater summary/TOI/realtime and separate goalie summary were refreshed; all historical season inputs were validated during the rebuild. NHL schedule and ESPN ownership, eligibility, injuries, current matchups and scored categories are refreshed.

ESPN ratio checks passed: 18/18. In this snapshot ATOI equals total skater TOI seconds divided by GP; GAA equals GA×3600/goalie TOI seconds; SV% equals SV/SA. ATOI is a ratio, not summed player average TOI. These empirical identities do not establish historical lineup eligibility or the unknown minimum goalie starts.

PPP coverage is filled by goal/assist attribution using official strength labels; all skater G/A and PP goals must reconcile with boxscores. Separate goalie game rows preserve SA, SV, GA, TOI, wins and start flags. Unused backups have undefined ratios. Source-count exceptions remain flagged.

The full current-season archive covers all **65 completed regular-season games**, September 29 through October 8: **2,340 skater/game rows** and **260 goalie/game rows**, including unused backups. All ten cumulative skater categories reconcile for all **642 skaters** with latest NHL season reports (TOI within 0.02 minutes). The current goalie summary contains 60 appeared goalies and one SA=SV+GA exception; one game-level goalie count exception is also retained. Four October 9 games are not final and were excluded from actuals.

## Decision and next work

On the full matched population, candidate SOG MAE fell 1.65% and assist MAE fell 1.05%. SOG bias changed from +0.062 to −0.057 per appearance; assist bias worsened from −0.003 to −0.015. Assist RMSE was essentially unchanged and slightly higher. Among scoring-roster players, SOG MAE improved 2.37%; assist MAE improved only 0.12% while underprediction increased. This mixed, small one-night result does not justify replacing the default.

Keep the baseline as the live default. Compare changes in MAE as well as bias; lower totals alone do not prove better predictions. Preserve these candidate factors as tested, and collect more chronological games before considering promotion. Extend prior-season game logs and historical roster eligibility before fitting participation or rolling TOI. No opponent or goalie forecasting model has been fitted. October 8 is now observed evaluation data, not an untouched future tuning holdout.

## Exports

[Readable player comparison](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/player_comparison_readable.csv) · [Readable evaluated appearances](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/evaluated_player_comparison_readable.csv) · [Full technical export](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/projected_vs_actual_all_rows.csv) · [Evaluated player appearances](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/evaluated_player_appearances.csv) · [Model metrics](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/model_metrics.csv) · [Per-game metrics](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/by_game_metrics.csv) · [ESPN ratio audit](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/espn_ratio_audit.csv) · [Latest future-game candidate forecasts](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/latest_scheduled_candidate_forecasts.csv)

[Full current-season skater game stats](../../data/processed/forecasts/fantasy_game_details_20261009T192950Z/skater_game_stats.csv) · [Separate goalie game stats](../../data/processed/forecasts/fantasy_game_details_20261009T192950Z/goalie_game_stats.csv) · [Game/season reconciliation](../../data/processed/forecasts/fantasy_game_details_20261009T192950Z/cumulative_category_audit.csv)

Game review: `data/processed/forecasts/game_review_20261009T192557Z`. Enriched fantasy games: `data/processed/forecasts/fantasy_game_details_20261009T192950Z`. Frozen candidate: `data/processed/forecasts/calibration_candidate_20261009T192106Z`.

The readable comparison groups original projection if plays, candidate projection if plays, and actual for each category. It preserves absent players and missing forecasts with status labels. Actuals for players without matched boxscore rows stay missing, not zero. Participation-adjusted `expected_*` fields remain in the technical export and are undefined until a participation model is fitted.
