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

The conditional per-game skater baseline, frozen game comparisons, and seeded
integer simulations are implemented. The live default remains recency-weighted
history; the pooled shot/assist calibration remains experimental. All 65 completed
current-season games through October 8 are archived and reconciled with season
reports. See the
[forecast guide](docs/PER_GAME_FORECAST.md),
[current status and readouts](outputs/per_game_forecast/README.md), and
[next tasks](NEXT_STEPS.md). Participation, goalie starts, and fantasy lineup
optimization remain later milestones. Simulation ranges are provisional, not
calibrated predictive intervals; the October 9 readout records every covered game.
