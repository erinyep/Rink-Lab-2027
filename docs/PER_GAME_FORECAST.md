# Per-game forecast baseline

Implemented October 6, 2026, following the sequence in the
[ELWAY adaptation](ELWAY_ADAPTATION_PLAN.md): validate history, compare interpretable
baselines, expose opportunity and event-rate components, then add current context.

Research question: **Do recency-weighted history and exposure-based shrinkage
predict next-season production per game better than the last completed season?**

This is a first predictive baseline. A conditional per-game mean is available;
participation probabilities, goalie starts, opponent adjustments, and calibrated
game-level uncertainty are not yet fitted. A season-average rate is not a direct
measurement of player talent.

## Reproduce

From the repository root, with the Rink Lab virtual environment active:

```sh
# Only needed when these dependencies are missing:
python -m pip install -r requirements-forecast.txt -r requirements-espn.txt

# First acquisition: all configured historical seasons, current season, schedule,
# and read-only ESPN league state. Existing snapshots are preserved.
python scripts/refresh_forecast_inputs.py

# Later updates need only the in-progress season and current context:
python scripts/refresh_forecast_inputs.py --seasons 20262027

# Build and evaluate using the latest saved snapshot of each configured season:
python scripts/build_per_game_forecast.py

# Use the exact output directory printed by the previous command:
Rscript R/analysis/05_fantasy_projection_baseline.R data/processed/forecasts/REPLACE_WITH_RUN

python -m unittest discover -s tests -v
Rscript R/tests/test_nhl_pagination.R
```

`--skip-espn` on the refresh command allows NHL acquisition when ESPN credentials
are unavailable. The forecast manifest always identifies the ESPN and schedule
snapshots actually used; it must not be described as fully fresh when either is
older. Refreshing sources and building forecasts are separate operations.

R handles the existing acquisition pipeline and the evaluation visualization.
Python holds the reusable forecast, validation, and league joins. This preserves
both language workflows without duplicating the fitted model.

## Source and population contract

- Official NHL Stats API `summary`, `timeonice`, and `realtime`, game type 2
  (regular season). Goalies are acquired separately and never mixed into skater
  priors. The NHL schedule uses `api-web.nhle.com/v1/schedule/<date>`.
- Five completed seasons, 2021–22 through 2025–26; 2026–27 is an in-progress
  observation set, not a completed-season training target.
- The builder rechecks file hashes, recorded pagination totals, season IDs,
  report populations, unique player IDs, GP agreement, G+A=P, G<=SOG, PPP<=P,
  positive TOI, EV+PP+SH totals, and TOI/GP agreement for **every season**.
  Missingness and numeric extremes are exported before modeling.
- No GP/TOI population threshold is applied. The forecast cohort includes
  everyone observed within the three-season lookback, plus current-season
  debutants for the live output. Historical presence does not establish current
  NHL roster membership; use the ESPN-enriched file for league context.
- Source retrieval times are distinct from event times. These are statistics
  retrieved today, including possible source corrections, not historical
  preseason vintages. In-progress season reports are source-reported totals;
  they are not guaranteed atomic across requests or free from live corrections.

Raw snapshots are immutable and Git-ignored. Processed outputs are reproducible
and Git-ignored. Preserve a run's source snapshots if exact reproduction is
needed after upstream corrections; the manifest names and hashes the inputs.

## Baselines and exposed components

1. **Last completed-season rate:** events / GP in the most recent completed
   season observed within the lookback. This is explicitly a stale fallback for
   players absent from the immediately preceding season.
2. **Recency-weighted rate:** sum(weight × events) / sum(weight × GP), with
   up to three seasons of history. The selected decay of 0.5 assigns historical
   weights 1, 0.5, and 0.25 from newest to oldest, with GP determining exposure.
3. **Opportunity × rate with shrinkage:** estimate minutes/game, SOG/minute,
   shooting conversion, and A/minute separately. Pool past observations by
   forward/defense position for priors, never by future position or future stats.

For weighted historical counts C, minutes M, GP N, position mean minutes/game m,
and pseudo-exposure k:

```text
conditional minutes/game = (M + k_toi × m) / (N + k_toi)
event rate/minute = (C + k_event × m × position event rate/minute)
                    / (M + k_event × m)
shooting conversion = (G + k_shots × position shooting conversion)
                      / (SOG + k_shots)
shots/game = conditional minutes/game × shots/minute
goals/game = shots/game × shooting conversion
assists/game = conditional minutes/game × assists/minute
points/game = goals/game + assists/game
```

The process-component export includes past position priors and observed-data
weights. It is an all-strength baseline; it does not infer PP1/PP2 or age effects.
These are regularized baseline estimates, not a claim of identified intrinsic skill.

## Evaluation design

The split and candidate grid live in `config/per_game_forecast.json`:

- Development target: 2023–24. Its reported results are diagnostic because final
  settings are subsequently selected on the later validation season.
- Validation target: 2024–25. Search decay {0.5, 0.75, 1}, event prior exposure
  {5, 20, 60} games, and shooting prior {50, 200, 800} shots. TOI prior exposure
  is fixed at 10 games as an initial modeling assumption.
- Untouched selection holdout: 2025–26. Features and position priors use only
  seasons strictly before each target. The test never selects the method or
  hyperparameters. Its season can become history for the later live forecast.
- Select the smallest mean relative MAE across G, A, and SOG on validation,
  each divided by the validation last-season baseline MAE. Do not select by
  looking at which candidate wins the test season.

Every metric reports returning-player count, GP, equal-player MAE, signed bias,
and GP-weighted MAE. Position and sparse-history strata are reported separately.
The 40-GP sparse-history label is a reporting convention, not an eligibility cut.

Players with no reported appearance in the fully retrieved target-season table
stay in the evaluation population with target GP=0 and **undefined** event/GP
outcomes. They are not assigned zero goals/game. New target-season entrants absent
from the pre-target cohort are counted separately, not given hindsight identities
and called preseason forecasts. This first evaluation does not validate a GP
model, rookie model, or roster-availability model.

The target is each player's **season-average production per game played**.
Errors must not be described as individual-game forecast accuracy. A chronological
game-log backtest with eligible roster observations is the next required step.

## Current-season update and scheduled games

Current-season observations receive weight 1 while completed-season weights
remain 1, 0.5, 0.25 under the selected decay. That online update rule is
**provisional**, pending evaluation at historical game cutoffs. A player with no
completed-season history receives the past-position shrinkage fallback even when
the default is the weighted model; this fallback is labeled and unvalidated for
rookies. It avoids treating a few NHL appearances as a stable unshrunk rate.

ESPN contributes current team, fantasy ownership, eligibility, and injury labels.
An injury label is preserved, not converted into an invented playing probability.
Goalies remain present with `goalie_model_pending`; unmatched players are retained
with an explicit reason and blank forecasts. The known goalie source-count
exceptions remain flagged rather than repaired.

The schedule export covers `[schedule retrieval cutoff, cutoff + 7 days)`.
Only scheduled regular-season games with normal schedule status and future start
times are eligible; games already underway and postponed games are excluded.
Each skater/game row contains `*_if_plays` values. `probability_of_playing` and
unconditional `expected_*` values remain missing. Home/away and opponent are
context columns, not fitted adjustments.

The seven-day **schedule-only reference** multiplies conditional rates by team
scheduled games and explicitly assumes the player plays every one. This is the
optimistic reference in `EXPECTED_OPPORTUNITY.md`, not a weekly availability
forecast or feasible fantasy lineup. Unknown team assignment stays unknown,
not zero games. ESPN's legacy “Utah Hockey Club” label maps to UTA after the
[official Utah Mammoth name change](https://www.nhl.com/news/mammoth-unveiled-as-utah-nickname).
No Arizona-to-Utah inference is made for unattached historical players.

## Output guide

Each run writes `data/processed/forecasts/per_game_<season>_<UTC timestamp>/`:

| File | Meaning |
| --- | --- |
| `manifest.json` | Configuration, selected model, versions, exact sources, hashes, limits |
| `current_observed_stats.csv` | Current-season NHL skater observations, not forecasts |
| `validated_player_seasons.csv` | Complete accepted multi-season skater panel |
| `source_column_audit.csv` | Counts, missingness, numeric extremes by source and season |
| `completed_history_forecast.csv` | Default conditional mean using completed history only |
| `current_per_game_forecast.csv` | Default with provisional current-season update |
| `process_components_provisional.csv` | Inspectable ELWAY-inspired shrinkage candidate |
| `espn_player_forecasts.csv` | All roster/available records with identity and forecast status |
| `scheduled_skater_game_forecasts.csv` | Conditional skater/game means with unknown participation |
| `today_skater_game_forecasts.csv` | Scheduled rows for the build date in America/New_York |
| `seven_day_schedule_reference.csv` | Optimistic schedule-only totals, no lineup constraints |
| `validation_model_selection.csv` | All candidate scores on validation only |
| `evaluation_metrics.csv` | Development, validation, test metrics and strata |
| `evaluation_population.csv` | Returners, no-appearance players, and excluded target entrants |
| `held_out_*_players.csv` | All pre-target cohort players, predictions, and observed outcomes |
| `held_out_per_game_error.png` | R-generated held-out comparison after running script 05 |

HIT, PIM, PPP, +/−, points and conditional TOI are also exported and evaluated,
but only G/A/SOG determine model selection. Treat auxiliary-category estimates
as exploratory. ESPN roster ATOI aggregation is still unresolved: do not sum
player average TOI to manufacture a valid fantasy category score.

Next: acquire validated skater game logs and as-of eligibility/roster history,
build the documented participation and rolling-TOI baseline, evaluate current
updates at chronological game cutoffs, then connect event rates to participation.
Goalies, calibrated uncertainty, strength-specific roles, replacement value, and
lineup optimization retain their later milestones in the ELWAY plan.

## Frozen October 6–7 game diagnostic

See the [October 8 readout](../outputs/per_game_forecast/october_6_7_readout.md)
for exact reproduction commands and refreshed forecast links.
`scripts/evaluate_recent_games.py` acquires official final boxscores, preserves
raw payloads and hashes, validates identities/scoring, flags team-shot exceptions,
and joins the frozen scheduled forecasts. `--raw-snapshot` supports offline reuse
without overwriting source payloads. Metrics exclude absent players and blank
forecasts because the model estimates production conditional on playing.
Artifact creation must precede puck drop; schedule cutoff alone is insufficient.
This diagnostic does not choose new settings or establish availability accuracy.

## October 8 comparison and current game history

See [October 8 results](../outputs/per_game_forecast/october_8_readout.md).
`evaluate_recent_games.py --no-readout` exports generic date-specific diagnostics.
ESPN aliases with identical forecasts are retained in an audit and deduplicated
by NHL player/game for evaluation. Conflicting alias forecasts block evaluation.
`compare_october_8_models.py` verifies the frozen candidate hashes, joins the
original October 8 forecasts and actuals on identical appearances, adds
last-season/process comparators from the original pregame panel, and audits
current ESPN ratio denominators. It never refits the calibration factors.

`acquire_current_game_history.py --through 2026-10-09 --reuse <snapshots>`
validates complete schedule date coverage and acquires every final regular-season
boxscore. `complete_fantasy_game_stats.py --boxscore-snapshots <snapshot>` acquires
official scoring summaries and reconciles scoring before deriving PP assists and
PPP. It preserves separate goalie start/win/SA/SV/GA/TOI rows and count exceptions.
`audit_current_game_history.py --fantasy-games <directory> --forecast <directory>`
reconciles aggregated games with current season observations without repairing
source discrepancies. Prior-season game history and historical roster eligibility
remain missing. Raw data and generated exports remain Git-ignored.

## Integer conditional simulations

`scripts/simulate_game_date.py --date 2026-10-09 --forecast <run>` verifies
every regular-season game on the requested NHL schedule date and acquires all
eight teams' official current rosters. It blocks a claimed complete pregame run
if any game has started, is postponed or lacks normal schedule status. A second
cutoff check ensures the run finishes before first puck drop. Skaters lacking
model history are retained in a coverage export rather than dropped.

The simulator draws 10,000 outcomes per modeled player/game for both the default
and frozen calibration candidate, using seed 20261009 and stable player/game keys.
SOG is Poisson; goals are binomial conditional on SOG; assists and hits are Poisson;
points=G+A; PPP is binomial conditional on points. This preserves basic count
identities but does not fit team dependence, roles, overdispersion or correlated
fantasy categories. Poisson NLL, at-least-one Brier scores and residual diagnostics
on October 8 are reported without fitting new dispersion parameters.

Mean projections remain decimals. The summary exports integer simulation
quantiles, marginal at-least-one probabilities conditional on playing and a
100-draw sample export. Quantiles are provisional distribution summaries, not
calibrated predictive intervals. Participation remains unknown; goalie outcomes,
PIM, plus/minus and continuous TOI are outside this simulation. The manifest
records inputs, hashes, cutoffs, seed, draw count and model assumptions.
