# PuckSignal

Finding the signal in hockey performance.

A hockey analytics research project using R and Python to explore player talent,
repeatability, predictive value, NHL performance, and NCAA-to-NHL translation.

## Research Goals

- Explore NHL player performance through descriptive statistics
- Identify which player metrics represent repeatable skills
- Determine which metrics have predictive value
- Explore player archetypes and similarities
- Study NCAA-to-NHL player translation
- Develop better measures of player contribution beyond traditional box scores

## Current forecast work

October 13: [October 12 night results](outputs/per_game_forecast/2026-10-12_results_readout.md).
Candidate led the two-game shot comparison; default still edges it over the
combined fantasy-rostered sample. Frozen sources and evaluated reading views
are linked in the report, including separately issued goalie forecasts.

October 12: [latest model results and adjustments](outputs/per_game_forecast/recent_results_2026-10-12.md).
The 11-game prospective comparison favors candidate overall, while default
performs better on fantasy-rostered players. All recent completed games and
forecast timing limitations are documented.

October 10: [today's projections and reading guide](outputs/per_game_forecast/README.md).
Five skater models and two goalie scenarios cover all 14 games, with 11 issued
before puck drop and three explicitly labeled late. Stats are cut off before
October 10; availability is timestamped at retrieval.

For October 9, start with the [consolidated results guide](data/processed/forecasts/october_9_review/README.md)
or [forecast status](outputs/per_game_forecast/README.md). The derived reading
folder groups players, team totals and goalies while preserving frozen source runs.

The conditional per-game skater baseline, frozen game comparisons, and seeded
integer simulations are implemented. The live default remains recency-weighted
history; the pooled shot/assist calibration remains experimental. All 65 completed
current-season games through October 8 are archived and reconciled with season
reports. See the
[forecast guide](docs/PER_GAME_FORECAST.md),
[current status and readouts](outputs/per_game_forecast/README.md), and
[next tasks](NEXT_STEPS.md). Separate provisional goalie rates/start shares and
an opponent-shot-volume trial now exist; confirmed starters, chronological goalie
validation, participation and fantasy lineup optimization remain later milestones.
Simulation ranges are provisional, not
calibrated predictive intervals; the October 9 readout records every covered game.
