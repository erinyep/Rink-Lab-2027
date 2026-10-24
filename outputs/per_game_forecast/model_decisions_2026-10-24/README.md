# Model decision evidence through 2026-10-23

Research question: do saved forecasts justify changing fantasy category projections or introducing team win probabilities?

36 games across 4 saved dates. All original forecasts remain unchanged.
Saved fantasy ownership defines the fantasy population; no current-roster relabeling.

## Fantasy shots

| model | rows_scored | mae | bias | interval_p10_p90_coverage |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 262 | 1.325 | -0.289 | 0.866 |
| candidate | 262 | 1.329 | -0.302 | 0.866 |
| default | 262 | 1.326 | -0.113 | 0.87 |
| opponent_form_sog_trial | 262 | 1.323 | -0.1 | 0.866 |
| usage_shot_context_trial | 262 | 1.334 | -0.289 | 0.87 |

[Paired game-bootstrap uncertainty, all categories and roles](paired_uncertainty.csv).
[Leave-one-date-out sensitivity](leave_one_date_out.csv). These are exploratory comparisons;
four dates do not establish stable subgroup improvement. Do not tune corrections on the same evaluation sample.

## Team win-probability development screen

| model | games | brier | log_loss | delta_vs_even | lower_95 | upper_95 |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 36 | 0.238 | 0.669 | -0.012 | -0.033 | 0.01 |
| candidate | 36 | 0.238 | 0.669 | -0.012 | -0.032 | 0.01 |
| default | 36 | 0.238 | 0.669 | -0.012 | -0.032 | 0.01 |
| opponent_form_sog_trial | 36 | 0.238 | 0.669 | -0.012 | -0.033 | 0.009 |
| usage_shot_context_trial | 36 | 0.238 | 0.669 | -0.012 | -0.032 | 0.009 |

Independent Poisson counts from frozen team goal means; tied counts split 50/50.
Official final scores determine winners, including overtime/shootouts. Saved means cover full-game
scoring, so this is an approximate scoring-count model, not regulation/OT decomposition.
This transformation was introduced after outcomes: its historical scores are a retrospective
development screen, NOT previously issued probability forecasts. No fitted calibration or home-ice
adjustment. Compare with the 50/50 baseline (Brier .25, log loss .6931).
Intervals resample games and do not resolve within-date dependence or multiple comparisons.
[Reliability bins](team_probability_reliability.csv) expose the small sample. Keep any new probabilities
as a separately frozen experimental release until future calibration and accuracy are assessed.

Goalie interval coverage and starter scores retain their own populations and dates in the CSVs.
No goalie interval widening or fantasy model promotion is automated by this script.
