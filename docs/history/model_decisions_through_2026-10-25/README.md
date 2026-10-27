# Model decision evidence through 2026-10-25

Research question: do saved forecasts justify changing fantasy category projections or introducing team win probabilities?

48 games across 5 saved dates. All original forecasts remain unchanged.
Saved fantasy ownership defines the fantasy population; no current-roster relabeling.

## Fantasy shots

| model | rows_scored | mae | bias | interval_p10_p90_coverage |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 347 | 1.309 | -0.212 | 0.867 |
| candidate | 347 | 1.312 | -0.227 | 0.87 |
| default | 347 | 1.317 | -0.039 | 0.867 |
| opponent_form_sog_trial | 347 | 1.316 | -0.023 | 0.867 |
| usage_shot_context_trial | 347 | 1.31 | -0.215 | 0.876 |

[Paired game-bootstrap uncertainty, all categories and roles](paired_uncertainty.csv).
[Leave-one-date-out sensitivity](leave_one_date_out.csv). These are exploratory comparisons;
5 dates do not establish stable subgroup improvement. Do not tune corrections on the same evaluation sample.

## Team win-probability development screen

| model | games | brier | log_loss | delta_vs_even | lower_95 | upper_95 |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 48 | 0.241 | 0.675 | -0.009 | -0.026 | 0.009 |
| candidate | 48 | 0.241 | 0.675 | -0.009 | -0.026 | 0.009 |
| default | 48 | 0.241 | 0.675 | -0.009 | -0.026 | 0.009 |
| opponent_form_sog_trial | 48 | 0.241 | 0.675 | -0.009 | -0.026 | 0.009 |
| usage_shot_context_trial | 48 | 0.241 | 0.675 | -0.009 | -0.026 | 0.009 |

Independent Poisson counts from frozen team goal means; tied counts split 50/50.
Official final scores determine winners, including overtime/shootouts. Saved means cover full-game
scoring, so this is an approximate scoring-count model, not regulation/OT decomposition.
This pooled table applies the transform to all saved means and is a development screen.
Only separately timestamped probability releases qualify for prospective probability scoring;
evaluate those releases separately rather than labeling this entire pool prospective. No fitted calibration or home-ice
adjustment. Compare with the 50/50 baseline (Brier .25, log loss .6931).
Intervals resample games and do not resolve within-date dependence or multiple comparisons.
[Reliability bins](team_probability_reliability.csv) expose the small sample. Keep any new probabilities
as a separately frozen experimental release until future calibration and accuracy are assessed.

Goalie interval coverage and starter scores retain their own populations and dates in the CSVs.
No goalie interval widening or fantasy model promotion is automated by this script.
