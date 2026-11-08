# Usage, power-play and probability challengers

The November 8 update adds two player alternatives to the existing five-model
daily bundle. The selected all-player shots model and fantasy category policy
remain unchanged. Automatic refresh is a separate next task.

| New player model | Conditional TOI | Shots, goals and assists | Power-play points |
| --- | --- | --- | --- |
| `usage_toi_only_trial` | Existing recent-usage estimate | Existing calibrated-opponent means | Existing calibrated-opponent mean |
| `pp_opportunity_trial` | Existing recent-usage estimate | Existing calibrated-opponent means | Expected PP minutes × shrunk PPP/minute, capped at G+A |

This isolates workload changes from shot-rate changes. PP deployment uses five
previous appearances, shrunk toward completed-season player PP minutes with ten
prior games. The event rate uses 120 prior PP minutes. Completed-season player
rates are themselves shrunk toward the position rate; rookies use position
priors. These are fixed research assumptions, not coefficients tuned to the
November 7 results. Player IDs, positive-TOI participation, exposure identities,
dates and missingness are validated. No confirmed PP unit or opponent-penalty
effect is inferred.

The direct team issuer additionally saves `calibrated_home_win_probability` and
`calibrated_away_win_probability`. Its original probability columns remain the
selected output. Calibration uses a regularized logistic intercept/slope on
earlier independently issued probabilities from the same team-model release.
It preserves raw probabilities until at least 30 earlier games, four dates and
five observations of each outcome exist. The coefficient prior is identity;
calibration is an experimental alternative, not an improvement claim.

Both daily runners include the configured team model and optional calibrator.
The calibrator's cutoff and raw-model manifest hash must match the new issue.
The public evaluator scores the additional probability columns when present.
Existing finalized forecasts are never rewritten. Replaying a date before a
calibrator's target date is rejected; explicitly choose an earlier release or
omit the optional calibration argument for historical work.

## Evidence and limitations

The [November 8 review](../outputs/per_game_forecast/model_challengers_2026-11-08/README.md)
covers 1,041 matched appearances in 29 games across November 4–7. Usage TOI MAE
is 2.062 versus 2.203 minutes; PP minute MAE is 0.865 versus a completed-season
prior's 0.952. PPP Brier improves slightly, 0.07837 to 0.07744, while count MAE
worsens, 0.18337 to 0.18802. Keep PPP experimental.

On November 7, projected PP minutes were already above actuals (550.7 versus
496.2 across the covered players), while projected PPP remained below actuals
(44.2 versus 66). Extra PP volume alone therefore does not explain that night's
miss. Investigate deployment mix and PPP/minute variation across more dates
before increasing scoring rates.

Only eleven games have a fitted earlier-date calibration holdout: Brier 0.18427
versus raw 0.18710. This small retrospective check does not justify selecting the
calibrator. The next-date artifact is trained on all 43 earlier issued games.
Keep prospective scores distinct from reconstructed player challengers.

## Repeat the analysis

Use the existing `rink-lab.venv` with `requirements-forecast.txt` and
`requirements-espn.txt`. Acquire official actuals with
`acquire_current_game_history.py`, `complete_fantasy_game_stats.py` and
`acquire_game_toi.py`, then run:

```sh
rink-lab.venv/bin/python scripts/update_model_challengers.py \
  --actuals <validated-fantasy-game-details-directory> \
  --exposure <validated-player-game-toi.csv> \
  --panel <validated-player-seasons.csv> \
  --target-date YYYY-MM-DD \
  --out <new-review-directory>
```

The output records source hashes, reconstructed player means, per-date and pooled
metrics, proper PPP scores, rolling probability folds, reliability bins, and the
next-date calibration artifact. Use a new directory each time. To adopt a newly
reviewed calibration artifact for future side-by-side issuance, update
`probability_calibration_release` in `config/team_goal_model_active.json`.
