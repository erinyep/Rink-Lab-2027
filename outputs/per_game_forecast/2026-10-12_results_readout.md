# 2026-10-12 model results

Primary comparison: 2 games with forecasts issued before puck drop, 72 actual skater appearances. All five models cover the same appearances. Saved issue: 2026-10-12T22:53:14.302078+00:00.

| game_id | matchup | score |
| --- | --- | --- |
| 2026020088 | OTT @ NJD | 4–1 |
| 2026020089 | VGK @ MIN | 2–4 |

## Shot performance

| model | rows_scored | player_sog_mae | predicted_total | actual_total | team_sog_mae | fantasy_player_sog_mae |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 72 | 1.013 | 117.475 | 101.0 | 4.061 | 0.971 |
| candidate | 72 | 1.006 | 115.935 | 101.0 | 3.611 | 0.955 |
| default | 72 | 1.055 | 125.216 | 101.0 | 5.804 | 1.027 |
| opponent_form_sog_trial | 72 | 1.064 | 126.88 | 101.0 | 6.219 | 1.046 |
| usage_shot_context_trial | 72 | 1.028 | 115.4 | 101.0 | 4.315 | 1.054 |

MAE is average absolute error; lower is better. Player totals refer to actual appearances. Team projections use frozen assumed lineups and may differ from the player total. Candidate was best on all-player, team and fantasy-player SOG MAE for this slate. The opponent-only model increased error; adding it to candidate also hurt. The usage model improved on default for all players but did not beat candidate.

## Team shots projected versus actual

| game_id | team | opponent | actual_shots | calibrated_opponent_sog_trial | candidate | default | opponent_form_sog_trial | usage_shot_context_trial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026020088 | NJD | OTT | 30 | 33.173 | 32.191 | 34.768 | 35.829 | 32.725 |
| 2026020088 | OTT | NJD | 20 | 26.336 | 26.513 | 28.635 | 28.445 | 25.886 |
| 2026020089 | MIN | VGK | 28 | 27.652 | 27.783 | 30.007 | 29.866 | 25.991 |
| 2026020089 | VGK | MIN | 23 | 29.385 | 28.524 | 30.808 | 31.737 | 29.642 |

Whole-number exact team SOG guess rates (small samples):
| model | exact_guess_rows | exact_guess_rate |
| --- | --- | --- |
| calibrated_opponent_sog_trial | 4 | 0.0 |
| candidate | 4 | 0.0 |
| default | 4 | 0.0 |
| opponent_form_sog_trial | 4 | 0.0 |
| usage_shot_context_trial | 4 | 0.0 |

## Other categories

| model | category | rows_scored | mae | predicted_total | actual_total |
| --- | --- | --- | --- | --- | --- |
| candidate | assists | 72 | 0.357 | 21.892 | 17.0 |
| candidate | goals | 72 | 0.267 | 13.166 | 11.0 |
| candidate | hits | 72 | 0.828 | 82.012 | 69.0 |
| candidate | penalty_minutes | 72 | 0.726 | 33.105 | 37.0 |
| candidate | plus_minus | 72 | 0.784 | 0.683 | -2.0 |
| candidate | points | 72 | 0.459 | 35.058 | 28.0 |
| candidate | pp_points | 72 | 0.159 | 9.048 | 5.0 |
| candidate | toi_minutes | 72 | 2.278 | 1221.457 | 1179.0 |
| default | assists | 72 | 0.361 | 22.75 | 17.0 |
| default | goals | 72 | 0.267 | 13.166 | 11.0 |
| default | hits | 72 | 0.828 | 82.012 | 69.0 |
| default | penalty_minutes | 72 | 0.726 | 33.105 | 37.0 |
| default | plus_minus | 72 | 0.784 | 0.683 | -2.0 |
| default | points | 72 | 0.463 | 35.916 | 28.0 |
| default | pp_points | 72 | 0.159 | 9.048 | 5.0 |
| default | toi_minutes | 72 | 2.278 | 1221.457 | 1179.0 |
| usage_shot_context_trial | assists | 72 | 0.357 | 21.892 | 17.0 |
| usage_shot_context_trial | goals | 72 | 0.267 | 13.166 | 11.0 |
| usage_shot_context_trial | hits | 72 | 0.828 | 82.012 | 69.0 |
| usage_shot_context_trial | penalty_minutes | 72 | 0.726 | 33.105 | 37.0 |
| usage_shot_context_trial | plus_minus | 72 | 0.784 | 0.683 | -2.0 |
| usage_shot_context_trial | points | 72 | 0.459 | 35.058 | 28.0 |
| usage_shot_context_trial | pp_points | 72 | 0.159 | 9.048 | 5.0 |
| usage_shot_context_trial | toi_minutes | 72 | 2.066 | 1219.215 | 1179.0 |

Goals, hits, PIM, plus/minus and PPP means are shared across these models. Candidate changes assists and derived points. Usage changes shots and TOI. This is a small-slate diagnostic; aggregate overprediction does not justify fitting a new correction on these same outcomes.

## Goalies

| model | category | rows_scored | mae | predicted_total | actual_total |
| --- | --- | --- | --- | --- | --- |
| goalie_history_baseline | shots_against | 4 | 4.855 | 108.056 | 99.0 |
| goalie_opponent_context_trial | shots_against | 4 | 3.697 | 109.823 | 99.0 |
| goalie_history_baseline | saves | 4 | 5.076 | 97.154 | 90.0 |
| goalie_opponent_context_trial | saves | 4 | 4.041 | 98.735 | 90.0 |
| goalie_history_baseline | goals_against | 4 | 0.654 | 10.901 | 9.0 |
| goalie_opponent_context_trial | goals_against | 4 | 0.785 | 11.088 | 9.0 |

Goalie opponent context improves shot/save errors on these four starts, but goals-against error is slightly worse. These are full-60-minute conditional forecasts; actual starts may end early for empty-net play. Team shots and goals can include empty-net events and need not equal goalie-denominator totals. Starter probabilities remain provisional.

## Does this change the fantasy recommendation?

| model | appearances | mae |
| --- | --- | --- |
| calibrated_opponent_sog_trial | 96 | 1.326 |
| candidate | 96 | 1.325 |
| default | 96 | 1.311 |
| opponent_form_sog_trial | 96 | 1.313 |
| usage_shot_context_trial | 96 | 1.325 |

This combines the October 10 and October 12 prospective fantasy cohorts. Candidate wins the latest night, while default still has slightly lower combined error. Keep both visible; do not promote or retune a model based on two games. Test role/TOI-based calibration and isolate the usage model’s TOI, rate and context changes.

## Coverage and input limitations

| team | actual_skaters | actual_skaters_with_forecast | selected_lineup_actual_overlap | selected_identified_nonparticipants |
| --- | --- | --- | --- | --- |
| NJD | 18 | 18 | 18 | 0 |
| OTT | 18 | 18 | 18 | 0 |
| MIN | 18 | 18 | 17 | 1 |
| VGK | 18 | 18 | 17 | 1 |

Injury labels were retrieved at 2026-10-10T20:27:45.039563+00:00, approximately 50.4 hours before issuance. MoneyPuck inputs came from `data/raw/moneypuck/snapshots/team_games_20261010T201108Z` and lacked more recent game updates. NHL statistical inputs were cut off before the target date; no target-day outcomes were used.

Florida–Buffalo’s afternoon game was already final at issuance. Its late rows are retained in the evaluation files and excluded from every pregame table above. The separately saved goalie run and wide reading views are joined only in the evaluation output; frozen forecasts are preserved.

Before the next release, refresh ESPN injuries and MoneyPuck context, check starters and lineup coverage, then freeze the full skater/goalie bundle before first puck drop. Do not silently treat older availability data as freshly retrieved.

## Files

[Player-by-player results](../../data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z/player_projections.csv) · [Team results](../../data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z/team_projections.csv) · [Evaluation guide](../../data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z/README.md)

[Goalie results](../../data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z/goalie_projections.csv)

Evaluation: `data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z`. Frozen skaters: `data/processed/forecasts/daily_2026-10-12_20261012T225309Z`. Frozen goalies: `data/processed/forecasts/goalies_2026-10-12_20261012T225455Z`.

```sh
rink-lab.venv/bin/python scripts/write_daily_evaluation_readout.py \
  --evaluation data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z \
  --previous-evaluation data/processed/forecasts/daily_evaluation_2026-10-10_20261012T223430869565Z
```
