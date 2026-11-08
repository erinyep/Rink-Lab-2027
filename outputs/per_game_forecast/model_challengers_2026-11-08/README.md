# Model challengers — 2026-11-08

These changes implement isolated usage-aware TOI, power-play opportunity and team probability calibration. Existing five-model means, primary calibrated SOG and fantasy policies remain unchanged. Automatic refresh and participation modeling are deferred.

## Player workload and PP opportunity

Retrospective challenger reconstruction on 1041 matched positive-TOI player-games / 29 games across 4 saved release dates. Only dates before each target enter historical features; same-day outcomes cannot change their prediction. Priors use completed 2023-24 through 2025-26 seasons with fixed half-life weights. Recent PP minutes are shrunk with ten prior games; PP event rates with 120 prior minutes. No parameter was selected by minimizing these evaluation errors. The original usage TOI model and calibrated SOG are retained and exposed together as `usage_toi_only_trial`; `pp_opportunity_trial` additionally replaces PPP with expected PP minutes × shrunk PPP/minute, capped at expected G+A. Shots, goals and assists are not scaled by TOI. Replacements without identity retain position priors.

| category | model | rows | mae | bias | predicted | actual |
| --- | --- | --- | --- | --- | --- | --- |
| toi | baseline_toi | 1041 | 2.203 | 0.043 | 17199.357 | 17155.0 |
| toi | usage_toi | 1041 | 2.062 | 0.071 | 17228.738 | 17155.0 |
| pp_points | baseline_pp_points | 1041 | 0.183 | -0.029 | 107.759 | 138.0 |
| pp_points | opportunity_pp_points | 1041 | 0.188 | -0.023 | 114.236 | 138.0 |
| pp_minutes | prior_pp_minutes | 1041 | 0.952 | -0.001 | 1406.841 | 1408.25 |
| pp_minutes | expected_pp_minutes | 1041 | 0.865 | 0.027 | 1436.216 | 1408.25 |

PPP count negative log likelihood and probability-of-at-least-one Brier are in player_metrics.csv, along with zero-mean positive outcomes. Sparse categories require these proper scores in addition to MAE. Any zero-minute or missing exposure conflicts stop the run; nonparticipants are not assigned zero conditional production. This audit measures projected player PP minutes, not a fitted team power-play opportunity or opponent-penalty model. There are no confirmed PP-unit assignments.

## Probability calibration

Only frozen direct-team probabilities from the same fitted model release are used, with official final winner labels and verified issuance/start times. No player-sum probabilities or market prices train calibration. A ridge-logistic intercept/slope is shrunk toward identity (intercept 0, slope 1), with nonnegative slope. Until at least 30 games, four dates and five of each outcome exist on earlier dates, calibration is identity.

Full rolling comparison, including identity fallback folds:

| model | games | brier | log_loss |
| --- | --- | --- | --- |
| calibration_trial | 43 | 0.221 | 0.633 |
| coin_flip | 43 | 0.25 | 0.693 |
| past_home_rate | 43 | 0.27 | 0.735 |
| raw | 43 | 0.221 | 0.634 |

Only games for which an earlier-date fitted calibrator was available:

| model | games | brier | log_loss |
| --- | --- | --- | --- |
| calibration_trial | 11 | 0.184 | 0.557 |
| coin_flip | 11 | 0.25 | 0.693 |
| past_home_rate | 11 | 0.25 | 0.693 |
| raw | 11 | 0.187 | 0.562 |

The next-date artifact uses 43 earlier games / 6 dates through 2026-11-07; intercept -0.08428, slope 1.08993. Reliability bins retain their sample sizes and empty bins. The limited fitted holdout cannot justify a promotion. Raw probabilities remain selected; upcoming releases can save calibrated challenger probabilities separately. No retrospective output is called an issued pregame forecast, and no profitability is inferred.

## Files and validation

[Player rows](player_challenger_rows.csv) · [Player metrics by date](player_metrics.csv) · [Rolling probability scores](probability_walk_forward_scores.csv) · [Fitted-fold metrics](probability_fitted_holdout_metrics.csv) · [Reliability](probability_reliability.csv) · [Next-date calibration](probability_calibration.json).

All 276 official final games / 9935 positive-TOI skater rows reconcile with the refreshed exposure source. Official boxscore/scoring-summary G/A/PPP identities and source hashes were validated. Historical releases are untouched; reconstructed challengers use today's corrected actuals vintage and remain retrospective. This is a small recent player-model evaluation, not a whole-season or fantasy-roster validation.
