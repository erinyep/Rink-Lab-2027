# Rink Lab — Next Steps

## Project Goal

Build a reproducible hockey analytics research environment using R and Python
to investigate player talent, repeatability, predictive value, and
NCAA-to-NHL translation.

The central research question is:

> Which measurable player actions represent repeatable talent, which contribute
> meaningful value, and which predict future NHL performance?

---

## Latest validated snapshot — 2026-09-17

The current saved summary and TOI files each contain **940 unique skaters**,
with no unmatched IDs. Earlier 935/927 counts below are historical findings,
not the current population. No raw files were changed during this review.

Completed in this milestone:
- [x] Build and save the player-season dataset with season-aware one-to-one joins
- [x] Stop the build on invalid IDs, seasons, GP, scoring identities or TOI totals
- [x] Verify GP and TOI/game agreement between reports
- [x] Derive per-game and all-strength per-60 rates, retaining all summary players
- [x] Describe GP, TOI, scoring and rate distributions by position
- [x] Compare GP and TOI thresholds without choosing a universal eligibility rule
- [x] Save distribution plots, missingness, extreme-rate and exposure tables

Run from the repository root:
```sh
Rscript R/analysis/03_build_player_dataset.R
Rscript R/analysis/04_descriptive_player_season.R
```

Results and interpretation: `outputs/descriptive_2025_26/README.md`.

### Immediate next steps, in order

**First priority: review all guides and Markdown documents generated or updated
on 2026-09-17 before starting more analysis or ingestion work.**

1. [ ] Review the [descriptive results and interpretation](outputs/descriptive_2025_26/README.md):
   validation findings, position summaries, GP/TOI threshold sensitivity, and
   limitations of observed scoring rates.
2. [ ] Review the [NHL acquisition guide](docs/NHL_ACQUISITION.md):
   refresh commands, pagination checks, metadata, snapshot locations, and how
   to build from an accepted snapshot.
3. [ ] Review the [expected-opportunity specification](docs/EXPECTED_OPPORTUNITY.md):
   proposed seven-day games-played and TOI targets, required historical inputs,
   baseline assumptions, and evaluation design. Confirm the intended meaning
   of “expected plays” before implementing the model.
4. [ ] Review this updated [research roadmap](NEXT_STEPS.md), including the latest
   milestone and the distinction between current findings and historical notes.
   Record questions or corrections from the document review before continuing.
5. [ ] Compare totals, per-game and per-60 results within position, including
   threshold sensitivity. Choose eligibility based on the research question,
   not a cutoff that happens to produce attractive results.
6. [ ] After reviewing the opportunity specification, acquire game-level history
   and as-of roster data for a held-out baseline. Season aggregates alone cannot
   validate availability or future opportunity predictions.
7. [ ] Add timestamped injury/lineup data only after selecting a documented source.
   Schedule, availability, and player impact are distinct quantities; neither
   schedule counts nor descriptive scoring rates establish player impact.

### Acquisition milestone completed — 2026-09-17

Direct requests now preserve API total and errors; pagination checks reject
duplicates, truncated pages and changing totals. Script
`00_refresh_nhl_snapshots.R` saves paired timestamped snapshots with JSON metadata
and CSV hashes. Older flat CSVs still lack provenance; new snapshots do not
overwrite them. Live verification passed: 940 unique skaters and 10 pages per
report, with matching API totals, passing build validation and verified saved
file hashes.

The sections below retain the original research roadmap and historical notes;
the milestone above supersedes their older population counts and open build tasks.

---

## Current Status

### Project Setup

- [x] Create Rink Lab GitHub repository
- [x] Configure VS Code
- [x] Configure Python virtual environment
- [x] Configure R
- [x] Confirm existing R package library is available
- [x] Install / confirm tidyverse
- [x] Upgrade fastRhockey to 1.0.0
- [x] Connect successfully to NHL Stats API
- [x] Create `AGENTS.md`
- [x] Create `NEXT_STEPS.md`
- [ ] Document Python dependencies
- [ ] Document R dependencies
- [ ] Review `.gitignore`

### NHL Data Acquisition

- [x] Identify NHL season format (`20252026`)
- [x] Retrieve NHL skater summary statistics
- [x] Identify NHL Stats API pagination behavior
- [x] Create reusable `get_all_nhl_skaters()` function
- [x] Improve pagination to stop automatically
- [x] Retrieve complete 2025-26 skater population
- [x] Retrieve 935 unique skaters
- [x] Save raw NHL skater dataset as:
      `data/raw/nhl/nhl_skaters_2025_26.csv`
- [ ] Add retrieval metadata / source documentation

---

# Phase 1 — NHL Player Landscape

## 1. Initial Data Quality

Completed checks:

- [x] Confirm dataset dimensions: 935 rows × 26 columns
- [x] Confirm 935 unique player IDs
- [x] Confirm no duplicate player IDs
- [x] Confirm no missing player IDs
- [x] Profile missing values across variables
- [x] Inspect position distribution
- [x] Inspect games-played distribution
- [x] Inspect low-GP players
- [x] Investigate missing shooting percentage
- [x] Investigate missing faceoff percentage
- [x] Compare player counts across common GP thresholds

Known population:

- Centers: 296
- Defensemen: 324
- Left wings: 163
- Right wings: 152
- Total skaters: 935

Games played:

- Minimum: 1
- 25th percentile: 23
- Median: 61
- Mean: 50.33
- 75th percentile: 77
- Maximum: 83

GP threshold populations:

- 1+ GP: 935
- 10+ GP: 776
- 20+ GP: 713
- 40+ GP: 610
- 60+ GP: 486

Remaining data-quality questions:

- [x] Check impossible or suspicious values
- [x] Investigate players with 83 games played
- [x] Inspect team abbreviation values
- [x] Identify players associated with multiple teams
- [x] Understand how NHL summary data represents traded players
- [ ] Confirm position coding against NHL source data
- [ ] Create concise data-quality summary

---

## 2. Define Analytical Populations

Do not remove low-GP players from raw data.

Eligibility rules should be applied only to analysis datasets.

Already evaluated:

- [x] All players with at least 1 GP
- [x] 10+ GP
- [x] 20+ GP
- [x] 40+ GP
- [x] 60+ GP
- [x] Compare population size across GP thresholds

Next:

- [x] Acquire total time-on-ice data
- [ ] Examine total TOI distribution
- [ ] Evaluate TOI-based eligibility thresholds
- [ ] Compare GP-based vs. TOI-based eligibility
- [ ] Determine appropriate eligibility rules by research question

Research question:

> How does the definition of an "NHL player" change our statistical conclusions?

---

## 3. Expand Time-on-Ice Data

Use the NHL Stats `timeonice` report.

Completed:

- [x] Retrieve complete 2025-26 `timeonice` report
- [x] Inspect available TOI variables
- [x] Validate player IDs and report coverage
- [x] Compare player coverage with summary dataset
- [x] Identify total TOI
- [x] Identify even-strength TOI
- [x] Identify power-play TOI
- [x] Identify shorthanded / penalty-kill TOI
- [x] Confirm TOI values are stored in seconds
- [x] Validate that `time_on_ice = ev_time_on_ice + pp_time_on_ice + sh_time_on_ice`
- [x] Confirm `ot_time_on_ice` is not an additional mutually exclusive TOI bucket
- [x] Document that NHL Stats report populations are not identical

Coverage findings:

- Summary report: 935 unique skaters
- Time-on-ice report: 927 unique skaters
- Summary-only: 13 skaters
- Time-on-ice-only: 5 skaters
- Do not assume separate NHL Stats reports contain identical player populations.
- Preserve the 935-player summary population when building the initial processed dataset.
- Do not use an `inner_join()` that silently removes summary players without TOI matches.

Next:

- [ ] Save raw TOI report as `data/raw/nhl/nhl_skaters_toi_2025_26.csv`
- [ ] Examine total TOI distribution
- [ ] Select useful TOI variables for the player-season dataset
- [ ] Join useful TOI variables to summary data by `player_id`
- [ ] Convert seconds to clearly named minute-based analysis variables
- [ ] Validate joined dataset and missing TOI values
- [ ] Save processed player-season dataset

---

## 4. Descriptive Statistics

Explore the distribution of NHL player performance.

Variables:

- [ ] Games played
- [ ] Goals
- [ ] Assists
- [ ] Points
- [ ] Shots
- [ ] Shooting percentage
- [ ] Plus/minus
- [ ] Penalty minutes
- [ ] Power-play production
- [ ] Shorthanded production
- [ ] Time on ice

For useful variables calculate:

- [ ] Mean
- [ ] Median
- [ ] Standard deviation
- [ ] Quartiles
- [ ] Percentiles
- [ ] Distribution shape
- [ ] Outliers

Visualize important distributions rather than relying only on summary tables.

---

## 5. Rate Statistics

Create:

- [ ] Goals/game
- [ ] Assists/game
- [ ] Points/game
- [ ] Shots/game
- [ ] Goals/60
- [ ] Assists/60
- [ ] Points/60
- [ ] Shots/60

Compare:

- [ ] Raw totals
- [ ] Per-game rates
- [ ] Per-60 rates

Research question:

> How different are player evaluations based on totals, per-game rates,
> and playing-time-adjusted rates?

Investigate players whose apparent performance changes substantially depending
on the denominator used.

---

## 6. Position Differences

Compare:

- [ ] Centers
- [ ] Left wings
- [ ] Right wings
- [ ] Defensemen
- [ ] All forwards
- [ ] Forwards vs. defensemen

Research questions:

> How much of the distribution of common hockey statistics is driven by position?

> Should player percentiles and comparisons be position-specific?

---

# Phase 2 — Expand the Player Feature Set

The NHL Stats API exposes multiple skater reports beyond `summary`.

Potential reports include:

- [ ] `scoringRates`
- [x] `timeonice`
- [ ] `percentages`
- [ ] `shottype`
- [ ] `puckPossessions`
- [ ] `realtime`
- [ ] `powerplay`
- [ ] `penaltykill`
- [ ] `summaryshooting`
- [ ] `goalsForAgainst`

For each new report:

1. Retrieve complete population
2. Inspect variables
3. Validate player coverage
4. Identify useful features
5. Join using `player_id`
6. Document definitions
7. Avoid retaining variables simply because they are available

Goal:

> Build a richer player-season table describing how players create value,
> rather than simply how many points they accumulated.

---

# Phase 3 — NHL EDGE

Explore tracking-derived player measures.

Potential features:

- [ ] Skating speed
- [ ] Speed bursts
- [ ] Skating distance
- [ ] Shot speed
- [ ] Shot location
- [ ] Offensive-zone time
- [ ] Other available EDGE measures

Research questions:

> Which physical or tracking characteristics distinguish elite players?

> Do EDGE metrics contain information that traditional statistics miss?

> Do EDGE metrics improve prediction of future performance?

---

# Phase 4 — Talent vs. Outcomes

Begin separating repeatable player characteristics from noisy outcomes.

## Repeatability

Possible approaches:

- First-half vs. second-half
- Season-to-season
- Rolling windows

Test stability of:

- [ ] Shooting percentage
- [ ] Goals/60
- [ ] Assists/60
- [ ] Points/60
- [ ] Shots/60
- [ ] Expected goals
- [ ] Shot characteristics
- [ ] Puck possession measures
- [ ] EDGE metrics

Research question:

> Which NHL statistics behave like repeatable player characteristics?

---

## Regression to the Mean

- [ ] Identify high-variance statistics
- [ ] Measure regression toward league average
- [ ] Compare goals with shot generation
- [ ] Compare shooting percentage with underlying shot quality
- [ ] Examine whether extreme performances persist

Research question:

> Which impressive-looking results are likely to persist, and which are
> largely driven by variance?

---

# Phase 5 — Predictive Value

Start with interpretable baselines.

Example progression:

1. Future goals ~ previous goals
2. Future goals ~ previous shots
3. Future goals ~ previous xG
4. Future goals ~ shots + xG + shooting percentage
5. Add TOI and contextual variables
6. Add EDGE features

Potential outcomes:

- Future goals
- Future assists
- Future points
- Future shots
- Future xG
- Future TOI
- Probability of remaining an NHL regular

Evaluation:

- [ ] Define train/test periods correctly
- [ ] Avoid temporal leakage
- [ ] Establish naive baselines
- [ ] Evaluate out-of-sample performance
- [ ] Compare incremental predictive value of feature groups

Potential models:

- [ ] Linear regression
- [ ] Regularized regression
- [ ] Random forest
- [ ] Gradient boosting

Do not introduce complex models until they outperform meaningful baselines.

Primary question:

> What information actually helps us predict what a player will do next?

---

# Phase 6 — Player Styles and Archetypes

Explore player similarity without initially imposing labels.

- [ ] Select appropriate features
- [ ] Standardize metrics
- [ ] Correlation analysis
- [ ] PCA
- [ ] Clustering
- [ ] Player similarity scores
- [ ] Interpret discovered clusters
- [ ] Compare archetypes by position

Potential concepts to investigate:

- Shooters
- Playmakers
- Transition players
- Offensive defensemen
- Defensive defensemen
- High-volume / low-efficiency scorers
- Low-volume / high-efficiency scorers

Labels should follow statistical results rather than being imposed beforehand.

Research question:

> Can players with very different point totals possess similar underlying
> skill profiles?

---

# Phase 7 — Play-by-Play and Shift Analysis

Move below the player-season level.

Potential data:

- [ ] Game-level player boxscores
- [ ] Play-by-play
- [ ] Shift data
- [ ] Shot events
- [ ] Scoring events
- [ ] Penalties
- [ ] Game states

Research questions:

> What happens before valuable offensive events?

> Which players consistently improve the state of play while they are on the ice?

> Which actions have predictive value beyond goals and assists?

---

# Phase 8 — NCAA Men's Hockey

Build a 2025-26 NCAA men's player dataset.

- [ ] Identify reliable NCAA data sources
- [ ] Acquire complete NCAA player population
- [ ] Standardize player names and identifiers
- [ ] Collect age
- [ ] Position
- [ ] Team
- [ ] Conference
- [ ] GP
- [ ] Goals
- [ ] Assists
- [ ] Points
- [ ] Shots
- [ ] Special-teams production
- [ ] Other available talent measures

Preserve the raw NCAA population before identifying NHL-bound players.

---

# Phase 9 — NCAA → NHL Translation

Identify NCAA players entering the NHL/pro pipeline for 2026-27.

Build historical NCAA → NHL transitions to provide training data.

Potential features:

- Age
- Position
- Conference
- NCAA scoring rate
- Shot generation
- Share of team offense
- Power-play production
- Age-adjusted production

Potential NHL outcomes:

- NHL games played
- NHL P/60
- NHL G/60
- NHL xG/60
- NHL TOI
- Probability of becoming an NHL regular

Primary question:

> Which NCAA statistics and player characteristics actually translate to
> NHL success?

---

# Phase 10 — 2026-27 NHL Rookie Research

Apply NCAA-to-NHL findings to players entering the NHL.

- [ ] Define rookie-eligible population
- [ ] Identify NCAA players entering NHL organizations
- [ ] Build rookie player profiles
- [ ] Compare prospects to historical NCAA players
- [ ] Estimate expected NHL opportunity
- [ ] Estimate expected NHL performance
- [ ] Track actual 2026-27 results
- [ ] Evaluate predictions

Goal:

> Use the upcoming rookie class as a real-world test of the research framework.

---

# Long-Term Research Questions

- What valuable hockey actions are poorly captured by points?
- What happens immediately before high-danger chances?
- What is the value of maintaining offensive-zone possession?
- What is the value of a successful zone entry?
- What is the value of recovering a loose puck?
- Can we measure pre-assist creation?
- How valuable are turnovers and takeaways?
- Which players consistently improve the quality of the next event?
- Can possession sequences be assigned expected value?
- Can we measure how players affect teammates?
- Can we separate individual contribution from team/context effects?
- Can we construct an interpretable all-around player-value metric?
- Which metrics contain genuinely new information versus repackaging
  existing statistics?

---

# Research Rules

1. Start with the hockey question before selecting the statistical method.
2. Never manually modify raw source data.
3. Preserve all players in raw datasets.
4. Apply eligibility thresholds only at the analysis stage.
5. Validate API results before trusting them.
6. Keep player identifiers wherever possible.
7. Document definitions of unfamiliar metrics.
8. Distinguish descriptive relationships from predictive relationships.
9. Distinguish repeatability from value.
10. Distinguish player talent from opportunity and team context.
11. Avoid treating correlation as evidence of causation.
12. Establish simple statistical baselines before using machine learning.
13. Test predictive models on future or held-out data.
14. Prefer interpretable results when predictive performance is comparable.
15. Document surprising results, failed hypotheses, and methodological decisions.
16. Do not add complexity simply because additional data or modeling methods
    are available.