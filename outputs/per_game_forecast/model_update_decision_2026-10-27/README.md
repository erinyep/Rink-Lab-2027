# Two concrete model changes — October 27

## 1. Fantasy ATOI: adopt the recent-usage TOI model

Saved fantasy evaluation: 347 appearances across 48 games/five dates. TOI MAE falls from 2.1644 to 2.0145 minutes
(6.9%). Paired delta −0.1499 minutes, exploratory game-bootstrap 95% [−0.2127,−0.0826]; 37/48 games improve.
The advantage persists leaving out each date. The category policy now uses usage-trial TOI for ATOI and preserves
default means for every other skater category. This is an actual selection change in `build_today_report.py`,
effective October 27, with original means and source-model lineage retained. It does not claim a shots improvement.
No historical roster report is rewritten under the new policy. Conditional TOI still assumes participation.

## 2. Team goals and wins: fit home/rest and team-strength effects

Trained on 2,624 games (2023–24 and 2024–25), selected on 1,312 games (2025–26), evaluated on 187 current-season
games including all three October 26 games. Selected `goal_xg_home_rest` improves recent goal MAE 1.4175→1.4048
and Brier 0.2425→0.2350 versus the simple goal-history baseline. Paired Brier delta −0.00749, 95% [−0.01485,+0.00011].
Improvement is promising, not statistically established at that threshold. Historical corrected xG has upstream
training overlap; these are chronological development results, not forecasts issued before those games.

The model is fitted and enabled in daily issuance, with a separate frozen forecast for October 27's 11 games.
Production coefficients include official outcomes through October 26. MoneyPuck currently ends October 25;
missing yesterday xG is excluded rather than fabricated. The simple baseline remains beside each updated prediction.
This updates direct team goals and derived win probabilities, not individual player means or confirmed-goalie effects.

## Compare against the old saved-forecast probability approach too

| games | old_brier | new_brier | delta | lower_95 | upper_95 |
| --- | --- | --- | --- | --- | --- |
| 48 | 0.241 | 0.242 | 0.001 | -0.02 | 0.022 |

On the 48 shared games, the new model is slightly worse than the transform of old saved team means.
That prevents a claim that it has already beaten the existing model. The new retrospective predictions and old
saved-input transform have different source-vintage provenance; compare prospectively from October 27 onward.
Only the original October 24 probability release had actual pregame probability issuance before this update.
The new team model is an enabled challenger, with old baselines preserved, not an established replacement winner.

## Learned effects

| feature | coefficient_native |
| --- | --- |
| log_own_goal_rate | 0.294 |
| log_opponent_goals_against | 0.239 |
| is_home | 0.062 |
| own_back_to_back | -0.062 |
| opponent_back_to_back | 0.029 |
| rest_advantage | 0.066 |
| log_own_xg_rate | 0.394 |
| log_opponent_xg_against | 0.548 |

Coefficients are on the log expected-goals scale in native feature units, conditional on the other inputs.
Home coefficient implies approximately 6.4% higher goal expectation;
back-to-back coefficient implies approximately -6.0% change,
other features held fixed. These are predictive associations, not causal effects. Correlated goal/xG coefficients
must not be interpreted as independent player talent. [Recent reliability bins](recent_probability_reliability.csv)
are descriptive checks, not a fitted probability calibration layer.
