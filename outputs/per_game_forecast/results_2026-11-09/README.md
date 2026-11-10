# November 9 forecasts — results

Scored November 10 against official NHL boxscores and scoring summaries. All three saved forecasts were issued before puck drop. NHL history now contains 285 completed games through November 9.

## Game results and winner forecasts

| Game | Final | Direct team home win probability | Original player-sum home win probability |
|---|---:|---:|---:|
| NYR at EDM | EDM 3–1 | 58.4% (EDM) ✓ | 56.8% (EDM) ✓ |
| PHI at VAN | PHI 3–1 | 51.4% (VAN) ✗ | 40.4% (PHI) ✓ |
| NYI at SJS | SJS 3–2, SO | 49.2% (NYI favored) ✗ | 50.6% (SJS) ✓ |

| Probability model | Brier, lower is better | Correct favorite | Goal MAE per team |
|---|---:|---:|---:|
| Direct team | 0.232 | 1/3 | **1.115** |
| Original player-sum | **0.198** | **3/3** | 1.151 |
| Goal-history baseline | 0.230 | 2/3 | 1.122 |
| Calibrated team trial | 0.236 | 2/3 | **1.115** |
| 50/50 | 0.250 | — | — |

The direct model was slightly better on goal-count error, while the original player-sum probabilities did better on winners and Brier score. The shootout decision is included for the game winner; the shootout goal is excluded from player goal totals and goal-count errors. The six teams scored 12 credited goals.

## Player models

Metrics below are conditional on playing: **108 actual skaters across three games**, with 108 player-game rows scored for each model. No actual participant was missing from the forecast candidate set. Five players marked selected did not appear. Lower MAE is better; bias is projected minus actual.

| Metric/model | MAE | Bias | Projected total | Actual |
|---|---:|---:|---:|---:|
| Shots — default | 1.121 | +0.087 | 165.4 | 156 |
| Shots — selected calibrated-opponent model | 1.105 | −0.042 | 151.5 | 156 |
| Shots — usage shot-context trial | **1.079** | −0.073 | 148.1 | 156 |
| TOI — default | 2.698 min | +0.003 min | 1,786.0 min | 1,785.7 min |
| TOI — usage challenger | **2.483 min** | +0.022 min | 1,788.1 min | 1,785.7 min |
| Assists — default | 0.336 | +0.124 | 30.4 | 17 |
| Assists — candidate/usage variants | **0.330** | +0.114 | 29.3 | 17 |

The selected shots model reduced MAE by 1.4% versus default; the usage shot-context trial was 3.7% lower, but underprojected the slate by nearly eight shots. The TOI challenger reduced player-level MAE by 8.0% while total projected TOI was close. Goal MAE was 0.228 for all variants (18.7 projected versus 12 actual). The PP-opportunity trial did not improve PP-point MAE (0.163 versus 0.159 for the default variants).

## Goalies

The six actual starters were all represented in the forecast. The opponent-context trial had saves MAE **7.50** versus **7.59** for the history baseline, and goals-against MAE **1.11** versus **1.26**. The two models used identical starter probabilities: mean multiclass Brier was 0.328 across six team starts, compared with 0.583 for uniform candidate probabilities.

## Interpretation

This is a three-game sample. The winner-probability comparison favored the original player-sum baseline, while the selected shots model and usage TOI challenger had lower player-level errors than their baselines. Keep the existing policy and challenger labels; these results alone do not support a promotion or refit.

Detailed files: [player metrics](player_metrics.csv), [team games and probabilities](team_games.csv), [goalie metrics](goalie_metrics.csv), [coverage](coverage.csv), [all scored player categories](player_category_scores.csv), and [evaluation manifest](manifest.json).
