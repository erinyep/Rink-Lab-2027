# October 13 results and model recommendations

## What was actually issued

All 16 final regular-season games were acquired from the [official NHL schedule](https://api-web.nhle.com/v1/schedule/2026-10-13), with boxscores and scoring summaries. The latest saved default covering them was issued **2026-10-09T19:50:54.720471+00:00** (October 9, 3:50 PM Eastern), over four days before the games. The October 13 daily run remained pending; no five-model slate, goalie predictions, team simulations or exact-count guesses for this date were located. No missing predictions were reconstructed after seeing results.

The boxscores contain 576 skater rows, including one zero-TOI row (Z. L’Heureux, Colorado), leaving 575 appearances. The saved ESPN pool covers **558**, with **17 unmodeled appearances** retained in an audit. All covered appearances have all nine conditional means. Fantasy ownership/injuries reflect October 9, not game-day rosters. Do not score missing/unused players as zeros.

## October 13: default projected versus actual

| population | category | rows | predicted_total | actual_total | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_covered | goals | 558 | 99.463 | 109.0 | 0.291 | -0.017 | 0.463 |
| all_covered | assists | 558 | 166.073 | 192.0 | 0.423 | -0.046 | 0.585 |
| all_covered | shots | 558 | 896.507 | 862.0 | 1.014 | 0.062 | 1.297 |
| all_covered | hits | 558 | 642.874 | 658.0 | 0.889 | -0.027 | 1.189 |
| all_covered | points | 558 | 265.536 | 301.0 | 0.565 | -0.064 | 0.738 |
| all_covered | pp_points | 558 | 58.263 | 59.0 | 0.169 | -0.001 | 0.358 |
| all_covered | penalty_minutes | 558 | 265.585 | 295.0 | 0.791 | -0.053 | 1.42 |
| all_covered | plus_minus | 558 | 0.932 | -6.0 | 1.014 | 0.012 | 1.341 |
| all_covered | toi_minutes | 558 | 9310.324 | 9268.017 | 2.242 | 0.076 | 2.89 |
| saved_fantasy_roster | goals | 105 | 34.037 | 40.0 | 0.488 | -0.057 | 0.626 |
| saved_fantasy_roster | assists | 105 | 56.52 | 75.0 | 0.654 | -0.176 | 0.879 |
| saved_fantasy_roster | shots | 105 | 265.971 | 248.0 | 1.257 | 0.171 | 1.567 |
| saved_fantasy_roster | hits | 105 | 99.071 | 92.0 | 0.814 | 0.067 | 1.064 |
| saved_fantasy_roster | points | 105 | 90.556 | 115.0 | 0.818 | -0.233 | 1.071 |
| saved_fantasy_roster | pp_points | 105 | 28.519 | 37.0 | 0.47 | -0.081 | 0.7 |
| saved_fantasy_roster | penalty_minutes | 105 | 52.659 | 60.0 | 0.821 | -0.07 | 1.204 |
| saved_fantasy_roster | plus_minus | 105 | 4.019 | 25.0 | 1.186 | -0.2 | 1.485 |
| saved_fantasy_roster | toi_minutes | 105 | 2112.477 | 2153.45 | 2.129 | -0.39 | 2.624 |

MAE is average absolute error per appearance; lower is better. Bias is predicted minus actual. Totals use identical covered players. TOI is in minutes. PPP is completed from NHL scoring summaries. `expected_*_if_plays` is the conditional prediction; absent unconditional `expected_*` values in older sources do not mean these conditional predictions are missing.

## Where the shot error came from

| stratum | value | rows | predicted_total | actual_total | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| position_group | D | 192 | 250.262 | 219.0 | 0.896 | 0.163 | 1.121 |
| position_group | F | 366 | 646.244 | 643.0 | 1.075 | 0.009 | 1.381 |
| shot_tier | [0.0, 1.0) | 106 | 83.972 | 91.0 | 0.689 | -0.066 | 0.891 |
| shot_tier | [1.0, 2.0) | 306 | 440.254 | 441.0 | 1.016 | -0.002 | 1.296 |
| shot_tier | [2.0, 3.0) | 119 | 281.21 | 245.0 | 1.224 | 0.304 | 1.48 |
| shot_tier | [3.0, inf) | 27 | 91.071 | 85.0 | 1.333 | 0.225 | 1.725 |

The league-wide excess is concentrated among defensemen in this sample; forwards are close in aggregate. Players projected below two shots are also close as a group, while the two-to-three-shot group is high. This motivates testing position/role-specific calibration, not fitting new correction factors to this one night. Aggregate agreement can hide substantial individual errors.

## Fantasy teams at the saved ownership snapshot

| fantasy_team_name | rows | predicted_total | actual_total | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- |
| Bedardians of the Galaxy | 16 | 40.592 | 40.0 | 0.964 | 0.037 | 1.162 |
| Geekie Squad | 18 | 47.19 | 39.0 | 1.04 | 0.455 | 1.272 |
| Judge, Juraj and Executioner | 18 | 41.464 | 42.0 | 1.02 | -0.03 | 1.197 |
| Le Tang Clan | 18 | 47.47 | 44.0 | 1.502 | 0.193 | 1.767 |
| Parker's Perfect Team | 18 | 49.893 | 50.0 | 1.686 | -0.006 | 2.192 |
| Quinn Short for Quinnificent | 17 | 39.361 | 33.0 | 1.302 | 0.374 | 1.509 |

These are shot results for players who appeared, using saved scoring-roster membership; they are not current ESPN lineup totals or fantasy-point scores. Quinn’s cohort is overpredicted on this night, unlike the earlier concern about underprediction. Ownership itself should not drive hockey-rate adjustments.

## All games: matched-player shot diagnostics

These sums select actual participants after the games. They diagnose player-forecast errors, **not pregame team-total forecast accuracy**. Missing players explain any gap between matched actual shots and official team SOG. Final score includes shootout decisions, where applicable; player goals exclude shootout deciding goals.

| game_id | team | opponent | final_goals | official_shots | actual_positive_toi_skaters | covered_skaters | matched_player_expected_shots | matched_player_actual_shots | mae | bias |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026020090 | NJD | DET | 5 | 37 | 18 | 18 | 34.57 | 37.0 | 1.221 | -0.135 |
| 2026020090 | DET | NJD | 4 | 27 | 18 | 18 | 26.923 | 27.0 | 1.09 | -0.004 |
| 2026020091 | FLA | CBJ | 7 | 28 | 18 | 18 | 31.177 | 28.0 | 1.098 | 0.176 |
| 2026020091 | CBJ | FLA | 3 | 27 | 18 | 18 | 29.318 | 27.0 | 0.899 | 0.129 |
| 2026020092 | BUF | MTL | 3 | 17 | 18 | 18 | 26.595 | 17.0 | 0.951 | 0.533 |
| 2026020092 | MTL | BUF | 4 | 38 | 18 | 17 | 25.453 | 37.0 | 1.247 | -0.679 |
| 2026020093 | WSH | CAR | 2 | 22 | 18 | 18 | 31.596 | 22.0 | 0.859 | 0.533 |
| 2026020093 | CAR | WSH | 4 | 35 | 18 | 18 | 30.717 | 35.0 | 1.28 | -0.238 |
| 2026020094 | SEA | PHI | 3 | 31 | 18 | 16 | 25.136 | 29.0 | 0.673 | -0.242 |
| 2026020094 | PHI | SEA | 2 | 26 | 18 | 16 | 24.568 | 25.0 | 1.149 | -0.027 |
| 2026020095 | TBL | NYR | 1 | 26 | 18 | 16 | 27.365 | 25.0 | 1.055 | 0.148 |
| 2026020095 | NYR | TBL | 4 | 23 | 18 | 18 | 27.876 | 23.0 | 0.972 | 0.271 |
| 2026020096 | STL | OTT | 7 | 26 | 18 | 17 | 25.875 | 26.0 | 1.171 | -0.007 |
| 2026020096 | OTT | STL | 2 | 17 | 18 | 18 | 28.559 | 17.0 | 0.974 | 0.642 |
| 2026020097 | VAN | NYI | 2 | 26 | 18 | 17 | 23.023 | 26.0 | 0.537 | -0.175 |
| 2026020097 | NYI | VAN | 3 | 38 | 18 | 18 | 28.286 | 38.0 | 1.406 | -0.54 |
| 2026020098 | PIT | CHI | 3 | 27 | 18 | 18 | 29.864 | 27.0 | 0.875 | 0.159 |
| 2026020098 | CHI | PIT | 5 | 20 | 18 | 18 | 26.758 | 20.0 | 1.16 | 0.375 |
| 2026020099 | MIN | WPG | 2 | 21 | 18 | 17 | 28.205 | 20.0 | 0.976 | 0.483 |
| 2026020099 | WPG | MIN | 5 | 25 | 18 | 18 | 26.949 | 25.0 | 1.075 | 0.108 |
| 2026020100 | COL | DAL | 3 | 25 | 17 | 17 | 33.49 | 25.0 | 1.123 | 0.499 |
| 2026020100 | DAL | COL | 2 | 26 | 18 | 18 | 25.208 | 26.0 | 1.143 | -0.044 |
| 2026020101 | VGK | NSH | 5 | 25 | 18 | 18 | 30.697 | 25.0 | 0.716 | 0.317 |
| 2026020101 | NSH | VGK | 2 | 27 | 18 | 16 | 26.025 | 24.0 | 0.868 | 0.127 |
| 2026020102 | TOR | UTA | 4 | 26 | 18 | 18 | 31.644 | 26.0 | 0.693 | 0.314 |
| 2026020102 | UTA | TOR | 5 | 28 | 18 | 18 | 30.601 | 28.0 | 0.719 | 0.144 |
| 2026020103 | CGY | ANA | 4 | 36 | 18 | 16 | 24.47 | 34.0 | 1.103 | -0.596 |
| 2026020103 | ANA | CGY | 2 | 25 | 18 | 16 | 23.507 | 23.0 | 0.856 | 0.032 |
| 2026020104 | EDM | LAK | 4 | 17 | 18 | 18 | 27.068 | 17.0 | 0.953 | 0.559 |
| 2026020104 | LAK | EDM | 1 | 40 | 18 | 18 | 28.848 | 40.0 | 1.258 | -0.62 |
| 2026020105 | BOS | SJS | 6 | 26 | 18 | 17 | 26.601 | 25.0 | 1.082 | 0.094 |
| 2026020105 | SJS | BOS | 3 | 38 | 18 | 18 | 29.537 | 38.0 | 1.214 | -0.47 |

## How the five models are performing: earlier prospective evidence

This comparison is **October 10 and 12 only**: 13 games, 468 matched appearances, 26 team observations and 96 fantasy-rostered appearances. It excludes late forecasts, retrospective October 9 hybrid results, and October 13’s aged baseline.

| model | rows | predicted_total | actual_total | mae | bias | rmse | team_sog_mae | fantasy_sog_mae | exact_player_rate | interval_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 468 | 710.024 | 694.0 | 1.046 | 0.034 | 1.336 | 3.612 | 1.326 | 0.323 | 0.925 |
| candidate | 468 | 708.484 | 694.0 | 1.044 | 0.031 | 1.335 | 3.479 | 1.325 | 0.321 | 0.927 |
| default | 468 | 765.2 | 694.0 | 1.065 | 0.152 | 1.343 | 4.067 | 1.311 | 0.327 | 0.929 |
| opponent_form_sog_trial | 468 | 766.863 | 694.0 | 1.066 | 0.156 | 1.344 | 4.141 | 1.313 | 0.327 | 0.927 |
| usage_shot_context_trial | 468 | 703.922 | 694.0 | 1.05 | 0.021 | 1.336 | 3.645 | 1.325 | 0.323 | 0.921 |

Candidate has the lowest player/team SOG MAE and reduces positive bias. Its advantage is modest. Default remains slightly better on the saved fantasy cohort. The opponent-only effect does not improve the baseline, and combining it with candidate has no demonstrated incremental gain. Model ranking depends on the population and objective; include RMSE and mean bias alongside MAE when evaluating expected counts.

Paired game-cluster bootstrap: 20,000 resamples with appearance-weighted errors. Negative differences favor the challenger. These are exploratory intervals over only 13 game clusters, not guarantees of future performance.

| population | model | games | appearances | mae_delta_vs_default | lower_95 | upper_95 | games_improved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_players | calibrated_opponent_sog_trial | 13 | 468 | -0.019 | -0.03 | -0.008 | 11 |
| all_players | candidate | 13 | 468 | -0.02 | -0.031 | -0.009 | 11 |
| all_players | default | 13 | 468 | 0.0 | 0.0 | 0.0 | 0 |
| all_players | opponent_form_sog_trial | 13 | 468 | 0.002 | -0.001 | 0.004 | 6 |
| all_players | usage_shot_context_trial | 13 | 468 | -0.014 | -0.036 | 0.006 | 6 |
| saved_fantasy_roster | calibrated_opponent_sog_trial | 13 | 96 | 0.016 | -0.031 | 0.058 | 5 |
| saved_fantasy_roster | candidate | 13 | 96 | 0.015 | -0.034 | 0.058 | 6 |
| saved_fantasy_roster | default | 13 | 96 | 0.0 | 0.0 | 0.0 | 0 |
| saved_fantasy_roster | opponent_form_sog_trial | 13 | 96 | 0.002 | -0.006 | 0.009 | 5 |
| saved_fantasy_roster | usage_shot_context_trial | 13 | 96 | 0.015 | -0.046 | 0.074 | 6 |

Player shot p10–p90 ranges contain about 92–93% of outcomes. Discrete count quantiles can cover more than 80% even for a correct model; this does not establish overdispersion or justify mechanically narrowing intervals. Check discrete probability calibration, proper scores and conditional coverage over a larger holdout. Exact player counts are correct about 32% of the time and should be a secondary metric to the forecast distribution.

## Usage and goalies

| model | rows | mae | bias | rmse |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 468 | 2.268 | 0.162 | 3.039 |
| candidate | 468 | 2.268 | 0.162 | 3.039 |
| default | 468 | 2.268 | 0.162 | 3.039 |
| opponent_form_sog_trial | 468 | 2.268 | 0.162 | 3.039 |
| usage_shot_context_trial | 468 | 2.108 | 0.112 | 2.879 |

The usage model improves TOI errors, but its shot result remains behind candidate. Test TOI-only, rate-only and opponent-context changes separately rather than assuming the whole combined model is better.

Earlier October 10/12 actual-starter goalie comparison:
| model | category | rows | predicted_total | actual_total | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| goalie_history_baseline | shots_against | 26 | 712.48 | 688.0 | 3.826 | 0.942 | 4.774 |
| goalie_history_baseline | saves | 26 | 639.249 | 626.0 | 4.188 | 0.51 | 4.953 |
| goalie_history_baseline | goals_against | 26 | 73.231 | 62.0 | 1.231 | 0.432 | 1.475 |
| goalie_opponent_context_trial | shots_against | 26 | 703.401 | 688.0 | 3.687 | 0.592 | 4.543 |
| goalie_opponent_context_trial | saves | 26 | 631.061 | 626.0 | 3.949 | 0.195 | 4.674 |
| goalie_opponent_context_trial | goals_against | 26 | 72.34 | 62.0 | 1.264 | 0.398 | 1.502 |

October 13 goalie actuals are saved: 32 starters and 34 positive-TOI appearances; all active goalie rows satisfy SA = saves + GA. There are no saved October 13 goalie predictions to score. Earlier full-60-minute projections have mixed results across SA, saves and GA; actual pulls/empty-net time matter. Start probabilities remain provisional.

## Recommended next changes, in order

1. **Make daily issuance reliable.** Finish the MoneyPuck refresh command and date-aware finalizer, then use one orchestrated refresh/build/goalie/finalize/check command. Require current injury timestamps, declare source publication lag, cover every official game, and record issue times and immutable hashes. October 13 missed the intended experiment because no daily challenger bundle was issued.

2. **Repair player and lineup coverage.** Use the current official roster plus recent participants, stable NHL IDs and explicit position priors for missing history. Review the 17 unmodeled October 13 appearances. Model probability of dressing separately from conditional production; do not sum the entire ESPN pool as a team lineup.

3. **Retain default and candidate.** Candidate is the leading all-player/team challenger; default remains the fantasy baseline until more prospective evidence accumulates. Do not make another global SOG cut, strengthen the opponent factor, or claim an October 13 challenger win.

4. **Test deployment before added complexity.** Isolate the usage model’s TOI improvement; then test EV/PP exposure times shot rate, with shrinkage for sparse histories and neutral fallbacks. Evaluate position and pregame shot-rate strata on later games. The October 13 defense/forward split is a hypothesis to validate, not a fitted fix.

5. **Improve goalie participation/duration.** Timestamp confirmed starters where available, otherwise retain provisional probabilities; score starting probability and conditional shot/save/GA counts separately. Test duration/pull effects and opponent shot volume without assuming all components improve together.

6. **Continue chronological validation.** Keep a predeclared holdout, paired model populations, game-cluster uncertainty, MAE/RMSE/bias and discrete calibration. Keep fantasy and league-wide cohorts separate. These outcomes are now development evidence; newly tuned changes need later unseen games.

## Files and reproduction

[Player projected versus actual](../../data/processed/forecasts/october_13_review_20261014T135613Z/player_projected_vs_actual.csv) · [Team diagnostics](../../data/processed/forecasts/october_13_review_20261014T135613Z/team_matched_player_diagnostics.csv) · [Missing-player audit](../../data/processed/forecasts/october_13_review_20261014T135613Z/unmodeled_actual_skaters.csv) · [Goalie actuals, no forecasts](../../data/processed/forecasts/fantasy_game_details_20261014T135057Z/goalie_game_stats.csv)

Saved baseline: `data/processed/forecasts/per_game_20262027_20261009T195052Z`. Evaluated output: `data/processed/forecasts/october_13_review_20261014T135613Z`. Frozen data, acquired actual-file hashes and earlier evaluation files used here were verified. The October 10 evaluation retains its documented unavailable historical parent-manifest back-reference; this is not a changed forecast-data hash and is preserved in this review manifest. Statistical settings and frozen predictions were unchanged.

```sh
rink-lab.venv/bin/python scripts/write_october_13_review.py \
  --review data/processed/forecasts/game_review_20261014T135018Z \
  --actuals data/processed/forecasts/fantasy_game_details_20261014T135057Z \
  --evaluations data/processed/forecasts/daily_evaluation_2026-10-10_20261012T223430869565Z data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z
```
