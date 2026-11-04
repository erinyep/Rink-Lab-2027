# Model decision evidence through 2026-11-03

Research question: do saved forecasts justify changing fantasy category projections or introducing team win probabilities?

73 games across 8 saved dates. All original forecasts remain unchanged.
Saved fantasy ownership defines the fantasy population; no current-roster relabeling.

## Fantasy shots

| model | rows_scored | mae | bias | interval_p10_p90_coverage |
| --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 518 | 1.27 | -0.14 | 0.884 |
| candidate | 518 | 1.272 | -0.153 | 0.882 |
| default | 518 | 1.284 | 0.034 | 0.88 |
| opponent_form_sog_trial | 518 | 1.282 | 0.047 | 0.876 |
| usage_shot_context_trial | 518 | 1.279 | -0.148 | 0.888 |

[Paired game-bootstrap uncertainty, all categories and roles](paired_uncertainty.csv).
[Leave-one-date-out sensitivity](leave_one_date_out.csv). These are exploratory comparisons;
8 dates do not establish stable subgroup improvement. Do not tune corrections on the same evaluation sample.

## Team win-probability development screen

| model | games | brier | log_loss | delta_vs_even | lower_95 | upper_95 |
| --- | --- | --- | --- | --- | --- | --- |
| calibrated_opponent_sog_trial | 73 | 0.246 | 0.684 | -0.004 | -0.017 | 0.009 |
| candidate | 73 | 0.246 | 0.684 | -0.004 | -0.017 | 0.009 |
| default | 73 | 0.246 | 0.684 | -0.004 | -0.017 | 0.009 |
| opponent_form_sog_trial | 73 | 0.246 | 0.684 | -0.004 | -0.017 | 0.009 |
| usage_shot_context_trial | 73 | 0.246 | 0.684 | -0.004 | -0.017 | 0.009 |

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
