# Past-only shots replay through November 5, 2026

This is a retrospective, date-cutoff replay, not recovery of the missing original forecasts. It applies the selected weighted player-rate baseline and the frozen calibrated-opponent SOG formula to each completed game date, rebuilding each forecast from official outcomes dated before that entire date. It uses one current official actuals vintage.

## Results

The baseline replay covers **261 games and 9,395 positive-TOI player-games** from 2026-09-29 through 2026-11-05. Its all-game conditional SOG MAE is **1.0230 shots**. The calibrated-opponent comparison excludes the 55 calibration-training games and covers **206 games and 7,415 paired player-games** after 2026-10-07.

On that shared post-calibration cohort, default MAE is **1.0295** and calibrated-opponent MAE is **1.0122**, **1.7% lower**. The paired game-cluster 95% interval for calibrated minus default is **-0.0203 to -0.0143 shots**; the trial was lower-error in 159 of 206 games. These replay estimates are conditional on having played; the results do not evaluate whether the daily roster or lineup selection found the player.

## Interpretation limits

- The NHL and MoneyPuck APIs provide historical outcomes and team inputs, not Rink Lab's missing saved forecast releases. The exact issued predictions for unarchived dates cannot be recovered.
- The replay uses the current weighted-rate method, current frozen multiplier and strict past-game cutoffs. It does not represent the model versions, candidate pool, status snapshot, or lineup known on every historical date.
- The multiplier was calibrated on October 6-7; only later dates are used for the paired challenger comparison. Earlier games contribute only to the default's full-period descriptive score.
- The player set is defined by postgame positive TOI and is forecast conditionally on playing. This isolates conditional SOG means and cannot measure availability, lineup selection, or unmodeled call-ups.
- The replay is checked against saved prospective default and calibrated-opponent forecasts on overlapping rows in [the agreement diagnostic](replay_agreement_summary.csv); source corrections can still change historical features.
- The separate [original frozen-release evaluation](../season_through_2026-11-05/README.md) remains the clean prospective result. Do not pool its rows with this replay as if every prediction had been issued live.

## Files

[All replay forecast and outcome rows](shots_replay_all_games.csv) · [coverage by game](game_coverage.csv) · [metrics by model](model_metrics.csv) · [metrics by date](metrics_by_date.csv) · [paired game results](paired_game_metrics.csv) · [paired uncertainty](paired_uncertainty.csv) · [replay versus saved forecast rows](replay_vs_saved_forecasts.csv).

Reproduction: `python3 scripts/review_walk_forward_sog.py --out outputs/per_game_forecast/rolling_replay_through_2026-11-05_rerun`. Actuals cutoff: 2026-11-05; the calibration freeze was dated through 2026-10-07.
