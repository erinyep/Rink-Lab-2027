# October 6–7 diagnosis and candidate changes

The six eligible games suggest marginal shot and assist means were high. They
do not establish a new player skill estimate or support changing individual
players after a big scoring night. October 8 outcomes have not been read.

## Interpretation

Across 213 appearances, goals were 38.84 predicted versus 37 observed (+5.0%),
assists 66.03 versus 56 (+17.9%), and shots 351.91 versus 311 (+13.2%). Close
aggregate goals can hide offsetting individual errors; goals MAE was 0.277,
assists 0.407 and shots 0.962 per appearance. These differ from season-average
errors and must not be compared directly with that earlier evaluation.

Shot error decomposes exactly as:

`predicted_rate × (predicted_TOI − actual_TOI) + (predicted_rate × actual_TOI − actual_shots)`

| Population | Excess predicted shots | TOI component | Rate residual |
| --- | ---: | ---: | ---: |
| All evaluated appearances | 40.91 | 10.45 | 30.45 |
| Saved fantasy scoring-roster appearances | 10.79 | -1.32 | 12.11 |

About 26% of the full-population excess aligns with ice-time error; 74% remains
after substituting actual ice time. This is an accounting decomposition, not a
causal finding: the residual includes shooting variance, game context and model
misspecification. Fantasy players' TOI was slightly underpredicted, so reducing
their ice time globally would address the wrong part of the error.

Fantasy-rostered players also had larger shot MAE (1.446), reflecting a different
population and higher event volume. Their October 7 totals were much closer than
October 6. That argues against a separate correction fitted to 35 appearances.
Eichel/Draisaitl four-point games and MacKinnon's scoreless game do not justify
individual boosts or penalties; conditional means cannot predict every burst.

The 166 resolved forecast rows without boxscore appearances expose an eligibility
problem. They include historical players attached to teams, not just verified
scratches. Keep conditional forecasts, show injury review flags, and acquire roster
history before fitting participation. Never turn all those absences into zeros.
Florida's one-shot source discrepancy remains flagged; it cannot explain a
40.91-shot aggregate excess. PPP, goalies and ratio-category decisions remain
outside this diagnostic.

## Implemented experimental candidate

Retain the original weighted-history model as the reference. Add one pooled
correction for SOG and one for assists, using all 213 eligible appearances:

`multiplier = (observed_events + 200) / (predicted_events + 200)`

The 200 pseudo expected events anchor the ratio toward 1. This is an explicit,
conservative initial assumption, not a validated or optimized prior. It gives
SOG multiplier **0.92588** (−7.41%) and assist multiplier **0.96229** (−3.77%).
Unshrunk ratios would cut shots 11.62% and assists 15.19%; the candidate deliberately
does not chase those complete two-day corrections.

Goals, TOI and auxiliary categories are unchanged; points are recomputed as G+A.
The candidate preserves original means and missing forecasts, adds a model version,
and flags non-ACTIVE or unknown injury labels for lineup review without inventing
appearance probabilities. Goals and shots remain separate marginal means; no
coherent joint count distribution or calibrated intervals are claimed.

Frozen settings: [candidate config](../../config/game_calibration_candidate.json).
Implementation: `src/fantasy/game_calibration.py` and
`scripts/build_game_calibration_candidate.py`. The candidate is separate from
the live default so its quality can be judged before promotion.

Candidate run:
`data/processed/forecasts/calibration_candidate_20261009T192106Z/`.
Its October 8 candidate forecasts use the saved October 8 pregame baseline and
only October 6–7 calibration outcomes. They were generated on October 9, so this
is a retrospective reconstruction with frozen features, not a forecast issued
before those games. Original October 8 forecasts remain preserved.

## Next evaluation, before further edits

1. Compare the frozen baseline and candidate on identical October 8 appearances.
   Report MAE, bias, RMSE and coverage for G/A/SOG, plus fantasy-roster strata.
   Do not change the two multipliers after reading those results and still call
   October 8 an untouched evaluation.
2. Extend the game sample and use chronological development/validation/test
   windows. Six games do not give 213 independent trials; summarize game-level
   errors and eventually uncertainty by game or date rather than independent rows.
3. Acquire game logs and historical roster eligibility, then evaluate rolling TOI,
   current-season update strength and rookie shrinkage. Investigate role and
   opponent effects only against these interpretable baselines.
4. Promote the candidate only if subsequent chronological evidence supports it.
   A single October 8 night can challenge the correction but cannot prove it works.

No October 8 boxscores were acquired or inspected during this change.
