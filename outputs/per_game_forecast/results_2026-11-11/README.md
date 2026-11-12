# November 11 model results

All six pregame games were scored against official NHL boxscores and scoring summaries. The 216 actual skater appearances included 215 with forecast rows; the one missing participant remains listed separately. Twelve selected lineup players did not appear and were not scored as zeroes. Player counts below are conditional on playing.

## Winner probabilities

| Model | Brier (lower is better) | Correct most-likely team | Goal MAE per team |
| --- | ---: | ---: | ---: |
| Goal-history baseline | **0.206** | **6/6** | **1.174** |
| Calibrated team trial | 0.212 | 5/6 | 1.234 |
| Original player-sum | 0.219 | 5/6 | 1.216 |
| Direct team | 0.222 | 5/6 | 1.234 |
| 50/50 | 0.250 | — | — |

The goal-history baseline led this six-game slate. That is not enough evidence to replace the direct-team model or refit its probabilities; the raw direct-team probabilities remain the selected production output, with calibration still reported as a challenger. Winner outcomes include overtime and shootouts; player goal counts exclude shootout-deciding goals.

## Skater shots and fantasy-rostered players

| Population / model | Appearances | Shots MAE | Forecast bias |
| --- | ---: | ---: | ---: |
| All players — default | 215 | 1.045 | +0.034 |
| All players — calibrated-opponent | 215 | **1.033** | −0.088 |
| All players — candidate | 215 | 1.034 | −0.083 |
| Fantasy-rostered — default | 43 | 1.517 | −0.108 |
| Fantasy-rostered — calibrated-opponent | 43 | **1.496** | −0.291 |
| Fantasy-rostered — candidate | 43 | 1.502 | −0.286 |

The selected calibrated-opponent model had slightly lower shot error, but its total was low: 312 projected shots versus 331 actual across all players. On fantasy-rostered appearances, the apparent MAE difference was also small and the model underprojected shots. Keep fantasy shots on their separate default policy.

The isolated usage-TOI challenger reduced all-player TOI MAE from 2.393 to 2.189 minutes, while fantasy-rostered TOI MAE was 2.243 minutes for both default and usage-only. The PP-opportunity trial did not improve fantasy PP-point error (0.458 versus 0.443 for default). Neither result supports a fantasy-policy change.

## Other model checks

The direct-team model and goal-history baseline both predicted 37.8 total goals against 38 credited goals; their per-team goal MAEs were 1.234 and 1.174. The goalie opponent-context trial lowered goals-against MAE to 1.006 from 1.088 across six starts, but its saves MAE was worse (6.640 versus 6.217). These one-slate differences remain exploratory.

**Decision:** refresh tonight’s forecasts using the new official history, but keep coefficients and model selections unchanged. Nov. 11 adds only six team games and 215 player appearances; it does not justify a refit or promotion.

## Files and method

The evaluator verified the frozen release and official source hashes. Only forecasts issued before puck drop were scored. Started or late-issued rows, nonparticipants, and missing player forecasts are not treated as prospective observations.

[Winner scores](winner_scores.csv) · [Winner metrics](winner_metrics.csv) · [All-player category metrics](player_metrics.csv) · [Fantasy-rostered category metrics](fantasy_player_metrics.csv) · [Team metrics](team_metrics.csv) · [Goalie metrics](goalie_metrics.csv) · [Coverage](coverage.csv) · [Evaluation manifest](manifest.json)
