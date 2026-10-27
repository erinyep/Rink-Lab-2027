# PuckSignal

Finding the signal in hockey performance.

A hockey analytics research project using R and Python to explore player talent,
repeatability, predictive value, NHL performance, and NCAA-to-NHL translation.

## Models updated — October 27

[Updated team goals/win probabilities](https://erinyep.github.io/Rink-Lab-2027/team-model/) · [Fantasy report with updated ATOI](https://erinyep.github.io/Rink-Lab-2027/report/) · [Model changes and validation](docs/history/model-update-2026-10-27.md).

Fantasy TOI error improves 6.9% on 347 saved fantasy appearances; the new category policy changes ATOI only. A fitted team model now includes team strength, home/rest and lagged xG, trained/validated on full seasons and tested on all 187 current-season games through yesterday. Recent Brier improves 0.2425→0.2350 against a simple goal-history baseline, but not the old model on their smaller shared cohort; it remains an enabled challenger with baselines preserved. Both changes are applied to fresh October 27 forecasts.

## Latest update — results through October 25

[October 24–25 results](https://erinyep.github.io/Rink-Lab-2027/results/) · [Model history](https://erinyep.github.io/Rink-Lab-2027/history/) · [Full local results](outputs/per_game_forecast/results_through_2026-10-25/README.md) · [Probability vs Kalshi](outputs/per_game_forecast/probability_results_2026-10-24/README.md).

184 official finals validated; all 17 October 24–25 games acquired. Main model comparisons now cover 48 saved games. October 25 has no saved daily forecast, so its five games update season data without adding retrospective predictions. Fantasy default retained; no defense/xG promotion. First prospective probability slate: model Brier 0.2496 vs Kalshi midpoint 0.2255 across 12 games. Too little evidence for promotion.

October 24 forecasts below are historical snapshots. [Refreshed broader xG, defense and injury review](outputs/per_game_forecast/broader_model_review_through_2026-10-25/README.md) · [Rolling scoreboard](outputs/per_game_forecast/scoreboard_through_2026-10-25/README.md).

## Model review — October 24

[Model decisions](docs/history/model-priorities-2026-10-24.md) · [Broader goal/xG, defense and injury review](outputs/per_game_forecast/broader_model_review_2026-10-24/README.md) · [Season review](outputs/per_game_forecast/season_through_2026-10-23/README.md) · [Rolling scoreboard](outputs/per_game_forecast/scoreboard_2026-10-24/README.md).

167 official finals audited. Full saved comparisons cover 36 games across October 10, 12, 20 and 22, with 1,295 positive-TOI appearances and 262 fantasy appearances. Default retained for fantasy: the small opponent-only advantage has uncertainty crossing zero. All-player calibrated SOG improves MAE 1.0435→1.0263; do not transfer that gain to every category or subgroup.

The broader chronological development screen covers all 1,312 games in 2025–26 plus 155 reconciled current-season games. Simple goal/xG blends did not establish a reliable improvement. Both prospective defense-feature slates now total 23 games; no feature promotion. Corrected historical sources are separate from saved pregame forecasts.

[Experimental team probabilities](outputs/per_game_forecast/team_probability_2026-10-24/README.md) · [Kalshi benchmark: 24 contracts, 12 games](outputs/per_game_forecast/kalshi_benchmark_2026-10-24/README.md). These are separate pregame research releases, not fantasy-model changes.

## Research Goals

- Explore NHL player performance through descriptive statistics
- Identify which player metrics represent repeatable skills
- Determine which metrics have predictive value
- Explore player archetypes and similarities
- Study NCAA-to-NHL player translation
- Develop better measures of player contribution beyond traditional box scores

## Local setup

[Second-machine setup and daily forecast command](docs/LOCAL_SETUP.md).

## Latest saved NHL predictions — October 24

[Saturday, October 24 NHL matchups](https://erinyep.github.io/Rink-Lab-2027/games/) —
projected goals, shots, scoring leans and goalie scenarios for all 24 teams.
[Reading guide](docs/games/README.md).

## What is driving the forecasts?

[Feature evidence, player/team contributions and tonight’s frozen experiments](https://erinyep.github.io/Rink-Lab-2027/evidence/). Four separate research variants use the exact October 20 coefficients with fresh past-only inputs for October 24. No model promotion; completed evidence remains linked from the trial page.

## Latest saved fantasy report — October 24

[Quinn’s local report and roster alerts](reports/today/README.md).

[Interactive browser report](https://erinyep.github.io/Rink-Lab-2027/report/)
(requires the [one-time Pages setup](docs/GITHUB_PAGES.md)).

![October 24 category comparison](docs/report/category-gaps.svg)

## Current forecast work

October 24: [12-game frozen release](outputs/per_game_forecast/2026-10-24_20261024T110008Z_pregame_readout.md), fresh inputs through October 23, [continued feature trials](outputs/per_game_forecast/feature_evidence_2026-10-24_v2/README.md), and updated local game/fantasy reports. The broader review prioritizes participation/EV-PP opportunity, goalie start/duration and calibrated uncertainty. Local reports are prepared; remote publication has not been performed.

October 22: [All 12 games issued pregame](outputs/per_game_forecast/2026-10-22_20261022T204633Z_pregame_readout.md), with fresh ESPN roster/category data and history through October 21. [Frozen feature trials](outputs/per_game_forecast/feature_evidence_2026-10-22/README.md) continue without refitting. The append-only local archive now preserves predictions and actuals versions; the derived scoreboard reports season and rolling 7/30-day errors. All starters remain provisional.

October 20: [Season-to-date model review](outputs/per_game_forecast/season_through_2026-10-19/README.md)
covers 140 final games with explicit saved-forecast gaps. New official PBP,
MoneyPuck shot-quality and public Kalshi source audits support the
[data-source strategy](docs/DATA_SOURCE_STRATEGY.md). A complete
[October 20 pregame slate](outputs/per_game_forecast/2026-10-20_20261020T125723Z_pregame_readout.md)
was issued through the new validated skater/goalie runner. No D-context
coefficient or market blend is promoted.

October 16: [Weekly model performance, player/team inputs and visuals](outputs/per_game_forecast/week_2026-10-12/README.md).
Review covers 32 final October 12–15 games with explicit forecast coverage,
all-category metrics, player/team SOG contribution tables and defense opportunity
proxies. A single command now acquires actuals, re-evaluates issued models and
publishes the review. See [next steps](NEXT_STEPS.md) for pregame automation and
prospective feature-validation priorities.

October 14: [October 13 results and model recommendations](outputs/per_game_forecast/2026-10-13_results_readout.md).
All 16 games checked against October 9-issued default forecasts; 558/575 skater
appearances covered. No October 13 challenger/goalie slate was issued. The
readout separates this evaluation from the pooled October 10/12 five-model
comparison and prioritizes daily issuance, roster coverage and role/usage tests.

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
