# November daily model review through 2026-11-12

## Results at a glance

Saved prospective releases cover 9 dates (2026-11-04–2026-11-12), 56 games and 2,007 matched positive-TOI player-games. November 1–3 have no saved frozen releases, so they are not reconstructed.

**Keep calibrated-opponent SOG for NHL-wide shots.** Across 56 games, it scored 1.018 MAE versus 1.032 for default (1.4% lower). The paired whole-game bootstrap difference was -0.014 shots (95% interval [-0.020, -0.009]); it won on 44/56 games. The candidate model's pooled MAE was 1.017, effectively tied with the selected variant, so there is no reason to retune the shot policy.

**Promote the isolated usage-aware ATOI model for NHL-wide conditional ice time.** `usage_toi_only_trial` scored 2.112 vs. 2.232 minutes MAE for default on 27 games (5.4% lower); the paired game-cluster interval for the difference was [-0.181, -0.121], with lower error in 26/27 games. This isolates the TOI change, unlike `usage_shot_context_trial`, which also changes SOG. The separate fantasy category policy already uses usage-aware TOI. Across 27 fantasy-rostered games, 192 appearances and 5 dates with saved evaluations, usage-only MAE was 2.074 vs. 2.254 for default; paired interval [-0.247, -0.119]. On Nov. 12 alone, fantasy-rostered MAE was 2.518 vs. 2.629 minutes.

**Keep fantasy shots on default pending a paired multi-date review.** Yesterday's 73 fantasy-rostered appearances favored candidate (1.168 MAE) and calibrated-opponent (1.172) over default (1.191), but one slate is not enough to change the separate fantasy SOG policy.

**Keep the direct-team win probabilities and goal-history baseline side by side; do not promote calibration.** Across the matched 45-game probability subset, direct-team Brier was 0.222, compared with 0.227 for goal history and 0.227 for player-sum. Original player-sum picked more winners (75.6% vs. 62.2%), while direct-team probabilities were better under Brier. Calibration trial Brier was 0.242 on its 27-game subset.

The PP-opportunity trial did not improve PP-point MAE (0.172 vs. 0.167 default on the same 27 games); keep it experimental. Assist MAE differences are negligible (0.400 candidate vs. 0.404 default), so retain current rates.

## Population and provenance

Only pregame forecasts are scored. Conditional player predictions are scored for positive-TOI participants; nonparticipants remain unscored. On 2026-11-12, 10 games had 356 matched player appearances; four actual skaters were missing forecasts. Late-issued SEA–CAR is excluded. Earlier Nov. 8 late scenarios are likewise excluded. Team win probabilities appear only on dates with a separately frozen direct-team release.

For 2026-11-12, calibrated-opponent SOG MAE was 0.993 vs. 1.007 default. Usage-only TOI MAE was 2.258 vs. 2.379 minutes. Full model and category details are in the CSVs below. Daily goalie and fantasy evaluations remain in local processed-data outputs and are not included in this review bundle.

## All-player conditional metrics

See [pooled categories](player_metrics.csv), [date-level results](player_metrics_by_date.csv), and [paired SOG intervals](paired_shots_vs_default.csv). Lower MAE and RMSE are better; bias is predicted minus actual.

## Game probabilities

The direct-team/original player-sum comparison uses the matched subset with a separate frozen direct-team release. See [metrics](winner_metrics.csv), [games](team_games.csv), and [per-game scores](winner_scores.csv).

## Coverage

See [coverage by date](coverage_by_date.csv) and [actual participants missing from forecasts](unmodeled_actual_skaters.csv). The official schedule and boxscores were reconciled through 2026-11-12; all source manifests and file hashes are captured in `manifest.json`.
