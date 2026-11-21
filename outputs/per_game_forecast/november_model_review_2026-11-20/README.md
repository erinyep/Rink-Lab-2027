# November daily model review through 2026-11-19

## Results at a glance

Saved prospective releases cover 14 dates (2026-11-04–2026-11-19), 96 games and 3,443 matched positive-TOI player-games. November 1–3 have no saved frozen releases, so they are not reconstructed.

**Keep calibrated-opponent SOG for NHL-wide shots.** Across 96 games, it scored 1.003 MAE versus 1.020 for default (1.6% lower). The paired whole-game bootstrap difference was -0.016 shots (95% interval [-0.020, -0.012]); it won on 77/96 games. The candidate model's pooled MAE was 1.003, effectively tied with the selected variant, so there is no reason to retune the shot policy.

**Keep the isolated usage-aware ATOI model as the NHL-wide conditional ice-time selection.** `usage_toi_only_trial` scored 2.054 vs. 2.200 minutes MAE for default on 67 games (6.6% lower); the paired game-cluster interval for the difference was [-0.168, -0.122], with lower error in 64/67 games. This isolates the TOI change, unlike `usage_shot_context_trial`, which also changes SOG. It is already the NHL-wide selection, and the fantasy category policy also uses usage-aware TOI. Across 27 fantasy-rostered games, 192 appearances and 5 dates with saved evaluations, usage-only MAE was 2.074 vs. 2.254 for default; paired interval [-0.247, -0.119].

**Keep fantasy shots on default.** This review scores the public NHL-wide population; the saved public bundles do not retain fantasy ownership. Do not transfer the all-player SOG result to fantasy until a paired fantasy evaluation is available.

**Keep the direct-team probabilities and goal-history baseline side by side; do not promote calibration.** Across the matched 74-game subset, Brier was 0.236 for goal history, 0.240 for player-sum, and 0.244 for direct team. The calibrated trial scored 0.257 on its 56-game subset. This sample gives no support for a calibration promotion.

The PP-opportunity trial did not improve PP-point MAE (0.168 vs. 0.163 default on the same 27 games); keep it experimental. Assist MAE differences are negligible (0.398 candidate vs. 0.403 default), so retain current rates.

**Keep goalie opponent context as a challenger.** Across the November release cohort, opponent context scored 4.70 saves MAE versus 4.77 for the history baseline on actual starters. Starter probabilities scored multiclass Brier 0.523 versus 0.523; keep both unchanged while improving starter identification and duration handling.

## Population and provenance

Only pregame forecasts are scored. Conditional player predictions are scored for positive-TOI participants; nonparticipants remain unscored. When a date has multiple frozen releases, this review uses the latest pregame release. On 2026-11-19, 12 games had 430 matched player appearances; 2 actual skaters were missing forecasts. Late-issued SEA–CAR is excluded. Earlier Nov. 8 late scenarios are likewise excluded. Team win probabilities appear only on dates with a separately frozen direct-team release.

For 2026-11-19, calibrated-opponent SOG MAE was 0.957 vs. 0.976 default. Usage-only TOI MAE was 2.034 vs. 2.171 minutes. Goalie count scores use actual starters with consistent boxscore counts and compare frozen full-start scenarios against actual duration; starter probabilities are scored as team-level multiclass outcomes. See [goalie metrics](goalie_metrics.csv), [starter scores](goalie_starter_scores.csv), and [starter summary](goalie_starter_metrics.csv).

## All-player conditional metrics

See [pooled categories](player_metrics.csv), [date-level results](player_metrics_by_date.csv), and [paired SOG intervals](paired_shots_vs_default.csv). Lower MAE and RMSE are better; bias is predicted minus actual.

## Game probabilities

The direct-team/original player-sum comparison uses the matched subset with a separate frozen direct-team release. See [metrics](winner_metrics.csv), [games](team_games.csv), and [per-game scores](winner_scores.csv).

## Coverage

See [coverage by date](coverage_by_date.csv) and [actual participants missing from forecasts](unmodeled_actual_skaters.csv). The official schedule and boxscores were reconciled through 2026-11-19; all source manifests and file hashes are captured in `manifest.json`.
