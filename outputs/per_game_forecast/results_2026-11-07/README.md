# Model performance review — November 7, 2026

Research question: how well did the saved pregame forecasts predict winners, scoring, player production and goalie workload, and which changes merit the next prospective test?

**Assessment:** calibrated player shots remain the clearest demonstrated incremental improvement, although the absolute gain is small. Direct team probabilities had a good night on proper probability scores but fewer correct favorite picks than the original model. Usage-aware ice time and confirmed participation/starter inputs deserve priority; the evidence does not justify replacing every category with one model.

## Evaluation population and provenance

- NHL date: November 7, 2026, interpreted in America/New_York. Twelve final games; **11 eligible pregame games**. Florida–Washington finished 3–4 but was already underway at issuance and is excluded from every reported prospective metric.
- Official schedule, boxscores and scoring summaries were retrieved November 8 and saved with source URLs and SHA-256 hashes. Goals, assists and power-play scoring were reconciled between boxscore and scoring summary. Regular season 2026-27 only; unique game/player keys checked.
- 396 positive-TOI skater appearances, **395 modeled**, one omitted player (Artyom Duda, UTA: 2 shots, 14.15 minutes). Conditional means are scored only for actual participants. Missing or absent participants are never converted to zero production.
- Candidate coverage: 499 player-games. The assumed 396-player lineup selected 375 who appeared and **21 who did not**; 20 other modeled participants were outside the selected lineup. Thus lineup precision and coverage are both 94.7%, a separate question from conditional-stat accuracy.
- Team shots use official totals: 608, versus 606 across covered participants. Goal counts include overtime but exclude artificial shootout winner goals. Winner outcomes include overtime/shootouts.
- Direct team coefficients were frozen through October 26. November 7 used NHL history through November 6 and MoneyPuck xG through November 5. No coefficients or policies were refit for this review.
- Public exports omit fantasy ownership. These results cannot establish accuracy for the current fantasy roster, actual start/sit decisions, or lineup transactions.

## Games: winner probability and goal means

| model | games | favorite_accuracy | brier | log_loss | goal_mae | predicted_goals | actual_goals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| coin_flip | 11 | nan | 0.25 | 0.693 | nan | nan | 74 |
| direct_team | 11 | 0.727 | 0.187 | 0.562 | 1.1 | 68.704 | 74 |
| goal_history_baseline | 11 | 0.818 | 0.202 | 0.595 | 1.139 | 68.787 | 74 |
| original_player_sum | 11 | 0.909 | 0.199 | 0.588 | 1.09 | 69.734 | 74 |

Favorite accuracy counts correct favored teams. Brier score averages squared probability error; log loss penalizes confident mistakes. Lower is better for Brier, log loss and goal MAE; goal MAE is per team. The original-model probabilities are the existing independent-Poisson/tie-split transform applied to frozen player-sum goal means; they are not a newly fitted model or independently timestamped probability release.

The original model picked **10/11** winners, direct team **8/11**, and goal-history baseline **9/11**. Direct-team Brier was **0.1871**, versus original **0.1987**, history **0.2021** and 50/50 **0.2500**. Direct log loss was also lower. A model can win fewer binary picks while giving better probabilities: moving a near-50/50 matchup across 50% changes the pick dramatically but barely changes its probability score. The direct model gave stronger, successful favorites to Carolina, Dallas and Edmonton; Seattle, Toronto and Los Angeles were its losing favorites, all at only 50–53%.

| Matchup | Final (away–home) | Direct pick | Original pick | Direct goal means (away–home) |
| --- | --- | --- | --- | --- |
| STL at NSH | 1–3 | NSH 53.4% | NSH 50.7% | 2.90–3.12 |
| NYR at SEA | 4–3 | SEA 50.9% | NYR 52.0% | 3.01–3.07 |
| MTL at TOR | 4–2 | TOR 50.4% | MTL 53.6% | 3.38–3.41 |
| UTA at OTT | 2–4 | OTT 54.0% | UTA 56.8% | 2.97–3.23 |
| NJD at NYI | 5–4 OT | NJD 55.0% | NJD 56.5% | 3.15–2.84 |
| CHI at CAR | 2–9 | CAR 73.8% | CAR 62.2% | 2.34–3.96 |
| SJS at DAL | 3–4 | DAL 69.2% | DAL 56.0% | 2.38–3.63 |
| TBL at MIN | 4–3 OT | TBL 52.3% | TBL 59.6% | 3.15–3.00 |
| DET at COL | 0–4 | COL 61.6% | COL 71.4% | 2.74–3.49 |
| PIT at LAK | 5–2 | LAK 53.1% | PIT 50.9% | 3.04–3.24 |
| VAN at EDM | 2–4 | EDM 69.5% | EDM 59.8% | 2.66–3.99 |

Carolina's nine goals were the largest obvious scoring miss: direct predicted 3.96 and original 3.57. Both recognized Carolina as favored, but neither point mean anticipates every blowout. Direct predicted 68.70 total goals versus 74 actual; original predicted 69.73. Original goal MAE was marginally better, **1.090 versus 1.100**. One night is insufficient evidence to raise all scoring rates or add a blowout correction.

### Broader direct-team record

| model | games | brier | log_loss | accuracy |
| --- | --- | --- | --- | --- |
| coin_flip | 43 | 0.25 | 0.693 | nan |
| direct_team | 43 | 0.221 | 0.634 | 0.535 |
| original_player_sum | 43 | 0.238 | 0.669 | 0.651 |

This combines saved comparisons from October 27, 29, 30 and November 4, 6, 7: **43 games across six dates**. Direct favorite accuracy is **23/43 (53.5%)**, original **28/43 (65.1%)**. Direct Brier is **0.2215 versus 0.2381**. Paired whole-game-bootstrap direct-minus-original Brier difference is **−0.0167**, with 95% interval **[−0.0394, +0.0065]**: superiority remains unresolved. Dates and teams share conditions, so even this interval should not be treated as independent season-long proof. The history baseline lacks a saved November 4 score in this aggregation and is deliberately excluded from the 43-game table.

November 6 adds three games: original 3/3, direct 2/3, but direct Brier 0.1825 versus original 0.2143. The same distinction between favorite picks and probability quality applies.

There is no matched November 7 market snapshot scored here. Earlier matched market reports are distinct cohorts. These results do not establish a market edge or betting returns.

## Player shots: the best-supported current selection

| model | rows | games | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 395 | 11 | 0.984 | -0.046 | 1.296 |
| candidate | 395 | 11 | 0.987 | -0.049 | 1.301 |
| default | 395 | 11 | 1.006 | 0.069 | 1.3 |
| opponent_form_sog_trial | 395 | 11 | 1.004 | 0.073 | 1.295 |
| usage_shot_context_trial | 395 | 11 | 1.004 | -0.072 | 1.317 |

Calibrated-opponent SOG averaged **0.984 shots absolute error**, default **1.006**: a **2.2% reduction**, or 0.022 shots per player. It had lower game-level MAE in **9/11 games**. Paired game-bootstrap MAE difference: **−0.0223**, 95% interval **[−0.0324, −0.0115]**. This estimates a comparison within this slate, not stability across future slates. RMSE improved only slightly (1.296 versus 1.300), so the gain is mostly in typical absolute error rather than elimination of large misses.

Role splits also favored calibrated shots: defensemen **0.900 versus 0.916**, forwards **1.026 versus 1.051**. Keep subgroup findings exploratory.

### Larger saved forecast cohort

| model | rows | games | mae | bias |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 3662 | 102 | 1.016 | -0.056 |
| candidate | 3662 | 102 | 1.016 | -0.057 |
| default | 3662 | 102 | 1.032 | 0.061 |
| opponent_form_sog_trial | 3662 | 102 | 1.032 | 0.063 |
| usage_shot_context_trial | 3662 | 102 | 1.021 | -0.072 |

Across **3,662 matched player-games / 102 games / 12 dates**, calibrated MAE is **1.0157 versus 1.0321**: **1.59% lower**, with lower game-level error in **79/102 games** and lower date-level MAE on every saved date. Whole-game-bootstrap difference: **−0.0164**, 95% interval **[−0.0204, −0.0123]**. A date-cluster sensitivity interval is **[−0.0193, −0.0139]**, but only 12 dates are available and repeated teams/players remain dependent.

Actuals-vintage limitation: October–November 5 rows come from the existing validated through-November-5 review; November 6–7 rows use the November 8 acquisition. This is an extension of saved evaluation vintages, **not a full historical re-score on one newly refreshed actuals vintage**. All models within each game share the same observations. The separate past-only replay remains retrospective and is not pooled here. Forecasts were not saved for every season game, so coverage should not be interpreted as the entire season.

### Player examples

Highest projected shooters, saved calibrated means versus actual shots:

| player_name | team | expected_shots_if_plays | actual_shots |
| --- | --- | --- | --- |
| Nathan MacKinnon | COL | 4.004 | 4.0 |
| Jack Hughes | NJD | 3.719 | 5.0 |
| Auston Matthews | TOR | 3.599 | 3.0 |
| Kirill Kaprizov | MIN | 3.213 | 5.0 |
| Connor McDavid | EDM | 3.209 | 3.0 |
| Timo Meier | NJD | 3.194 | 8.0 |
| Matt Boldy | MIN | 3.174 | 2.0 |
| Macklin Celebrini | SJS | 3.149 | 6.0 |

Largest absolute misses:

| player_name | team | expected_shots_if_plays | actual_shots | shot_error |
| --- | --- | --- | --- | --- |
| Nikita Kucherov | TBL | 2.972 | 9.0 | -6.028 |
| Timo Meier | NJD | 3.194 | 8.0 | -4.806 |
| Alex Laferriere | LAK | 2.28 | 7.0 | -4.72 |
| Jake Guentzel | TBL | 2.595 | 7.0 | -4.405 |
| Leon Draisaitl | EDM | 2.897 | 7.0 | -4.103 |
| Vince Dunn | SEA | 1.951 | 6.0 | -4.049 |
| John Leonard | DET | 0.985 | 5.0 | -4.015 |
| Arseny Gritsyuk | NJD | 2.201 | 6.0 | -3.799 |

Kucherov's 9 shots versus 2.97 expected and Meier's 8 versus 3.19 are tail outcomes to investigate with uncertainty and workload features. They do not imply that their expected means should have been 9 and 8. The ten players projected above 3 shots averaged 3.34 predicted versus 4.10 actual; that tiny, one-night subgroup is a diagnostic, not grounds for a fitted correction.

## Ice time and other player categories

| model | category | rows | mae | bias | predicted_total | actual_total |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | assists | 395 | 0.399 | -0.053 | 111.967 | 133.0 |
| calibrated_opponent_sog_trial | goals | 395 | 0.278 | -0.009 | 70.415 | 74.0 |
| calibrated_opponent_sog_trial | points | 395 | 0.519 | -0.062 | 182.382 | 207.0 |
| calibrated_opponent_sog_trial | pp_points | 395 | 0.205 | -0.061 | 41.971 | 66.0 |
| calibrated_opponent_sog_trial | toi_minutes | 395 | 2.055 | 0.037 | 6520.664 | 6506.233 |
| default | assists | 395 | 0.402 | -0.042 | 116.355 | 133.0 |
| default | goals | 395 | 0.278 | -0.009 | 70.415 | 74.0 |
| default | points | 395 | 0.52 | -0.051 | 186.77 | 207.0 |
| default | pp_points | 395 | 0.205 | -0.061 | 41.974 | 66.0 |
| default | toi_minutes | 395 | 2.055 | 0.037 | 6520.664 | 6506.233 |
| usage_shot_context_trial | assists | 395 | 0.399 | -0.053 | 111.967 | 133.0 |
| usage_shot_context_trial | goals | 395 | 0.278 | -0.009 | 70.415 | 74.0 |
| usage_shot_context_trial | points | 395 | 0.519 | -0.062 | 182.382 | 207.0 |
| usage_shot_context_trial | pp_points | 395 | 0.205 | -0.061 | 41.971 | 66.0 |
| usage_shot_context_trial | toi_minutes | 395 | 1.935 | 0.071 | 6534.461 | 6506.233 |

Usage-trial conditional TOI MAE was **1.935 minutes versus 2.055**, a **5.9% improvement**. Both roles benefited: defense 2.171 versus 2.343 minutes; forwards 1.818 versus 1.912. November 6 also favored usage TOI (2.317 versus 2.533). This supports continued category-specific validation of opportunity modeling. Usage-shot MAE remained worse than calibrated shots yesterday (1.004 versus 0.984), so a TOI improvement does not automatically transfer to shot-rate forecasts.

Goals were close in aggregate: 70.4 predicted versus 74 actual, with 0.278 MAE. Assists and special teams were underpredicted: default assists 116.4 versus 133; default points 186.8 versus 207; power-play points **42.0 versus 66**. Calibrated assists and points were slightly better on player MAE but lower in aggregate, showing that mean bias and absolute error measure different properties. One slate cannot distinguish a temporary high-PP night from a persistent deployment problem.

Sparse-category caution: predicting zero goals for every covered player would score **74/395 = 0.187 MAE**, better than 0.278, while offering no useful scoring discrimination. Therefore low goal/PPP MAE alone cannot establish model skill. For these targets, add scorer probabilities and proper probability scores, ranking/lift and calibration alongside count MAE; compare with simple past-only baselines. Do not interpret a fractional expected count as an exact count prediction.

## Teams and goalies

Calibrated team-shot MAE was **3.529 per team**, default **3.757**, usage **3.636**. Calibrated predicted 586.8 shots versus 608 actual; default 632.3. This one-night team result favors calibrated, but default beat these variants on November 5. Player-level and lineup-summed team-level performance require separate decisions.

For **22 actual starting goalies**, opponent context improved shots-against MAE **5.441 → 4.904** and saves **5.581 → 5.075**. Goals-against MAE was slightly worse, **1.014 → 1.021**. In the **20 starters with 55–65 minutes**, saves MAE improved **4.406 → 3.871**. This sensitivity check matters because fixed-60-minute predictions overstate workload after a goalie is pulled: Seattle's starter played 13.9 minutes and Chicago's 30.6. Relief scenarios are preserved separately and are not evidence for full-start accuracy.

Goalie-start selection itself needs work: provisional starter-share multiclass Brier was **0.585**, versus **0.564** for uniform shares among candidates (lower is better). Both goalie count variants share the same starter shares. Opponent context can improve saves conditional on the right starter while leaving starter selection unresolved. The mean probability assigned to the actual starter was only 49.1%. Do not call these confirmed-start predictions.

## Recommended next experiments, in order

1. **Separate participation, workload and event rate.** Acquire timestamped lineup and starter observations from a documented source before issuance, retaining an explicit unknown state. Track selected-lineup precision/recall and starter proper scores. Test a duration/pull model separately from conditional full-start counts. The 21 assumed-lineup nonparticipants and poor starter-share score identify concrete gaps.
2. **Retain calibrated all-player SOG and validate usage TOI separately.** Keep existing fantasy category policy. Freeze a prospectively defined challenger using improved expected EV/PP minutes, then evaluate whether event rates remain calibrated within role and opportunity bands. Require consistent multi-date gain and paired intervals before promotion. Do not stack adjustments merely because each looks useful in isolation.
3. **Audit power-play deployment before changing scoring coefficients.** Decompose PP points into expected PP minutes, team PP opportunities and individual per-minute production. Check missing PP-unit or role-change information and persistent date/role bias with past-only inputs. Yesterday's 42 versus 66 deserves investigation, not an immediate global uplift.
4. **Evaluate team probabilities as probabilities.** Keep the direct model experimental. Maintain matched game cohorts, Brier/log loss and reliability plots, with goal-history/home-ice baselines and separately saved market quotes when available. Collect more future slates before fitting any recalibration; if tested, fit only on earlier data and reserve later dates for evaluation. Explicit regulation/OT/shootout handling and confirmed-goalie effects are candidate features, not assumed improvements.
5. **Make the daily audit reproducible.** Run source refresh → validation → frozen-release scoring → coverage checks → versioned report after each completed slate. Re-score the full historical cohort on one current official actuals vintage before a policy decision. Preserve late-game exclusions, source lag, quarantine flags, forecasts and alternative models. Add proper probabilistic scoring and empirical interval coverage by role/volume; test overdispersion before adopting a different shot-count distribution.

No model was refit, promoted, committed or pushed. The new reusable public-release evaluator verifies hashes and timing and uses the existing goalie scorer. Two complete slates passed end-to-end evaluation; nine existing evaluation/probability tests passed. The local project environment now has SciPy and Matplotlib, and dependency compatibility/import checks pass.

## Reproduce and inspect

Run from the repository root using `rink-lab.venv/bin/python`:

```sh
rink-lab.venv/bin/python scripts/evaluate_public_daily.py \
  --bundle outputs/per_game_forecast/frozen/daily_2026-11-07_20261107T174425Z \
  --team outputs/per_game_forecast/team_context_daily_2026-11-07_20261107T174829Z \
  --actuals data/processed/forecasts/fantasy_game_details_20261108T140716Z \
  --boxscores data/raw/nhl/snapshots/results_nov6_7_20261108T140655Z \
  --out outputs/per_game_forecast/results_2026-11-07_rerun
```

Raw snapshots and processed actuals remain local/ignored; transfer them privately or reacquire a separately labeled actuals vintage to reproduce elsewhere. Supplemental cumulative calculations are preserved as CSVs with source manifest hashes in `review_manifest.json`.

[Game results](team_games.csv) · [Winner scores](winner_metrics.csv) · [Player metrics](player_metrics.csv) · [Scored players](player_projections_scored.csv) · [Team totals](team_metrics.csv) · [Goalie metrics](goalie_metrics.csv) · [Lineup coverage](coverage.csv) · [Cumulative shots](cumulative_shots_metrics.csv) · [Shot uncertainty](shots_uncertainty.csv) · [Cumulative winner scores](cumulative_winner_metrics.csv) · [Winner uncertainty](winner_uncertainty.csv).
