# Rink Lab — Next Steps

## Project Goal

Build a reproducible hockey analytics research environment using R and Python
to investigate player talent, repeatability, predictive value, and
NCAA-to-NHL translation.

The central research question is:

> Which measurable player actions represent repeatable talent, which contribute
> meaningful value, and which predict future NHL performance?

---

## Recent-results review before October 12 evening games — 2026-10-12

Read `outputs/per_game_forecast/recent_results_2026-10-12.md`. Retrieved all
86 completed regular-season games through October 11 plus the final October 12
Florida–Buffalo game in a separate recent-game snapshot. All 18 newly completed
games October 10–12 have an older saved default forecast; October 11 lacks a
newly issued multi-model/goalie run. Evaluate that baseline with its October 9
issue date, not as reconstructed new-model performance.

Primary five-model comparison: October 10's eleven pregame games, 396/396 skater
appearances, 22 teams and 22 starters. SOG MAE: default 1.0662, candidate 1.0514,
opponent 1.0664, combined 1.0516, usage 1.0543. Team SOG MAE: 3.751, 3.455,
3.763, 3.531 and 3.523 respectively. Candidate improves 9/11 games; usage 5/11.
Game-cluster bootstrap accompanies the readout; separate late-game metrics.

Important subgroup reversal: on 78 saved fantasy-rostered appearances, default
shot MAE is 1.376 versus candidate 1.411; default predicted 199.11/216 actual
shots, candidate 184.35/216. Do not strengthen blanket SOG calibration or
promote candidate for fantasy decisions based on pooled league performance.
Test pregame shot-rate, TOI/PP-role and position calibration strata using future
holdouts, not fantasy ownership as a hockey mechanism. Usage TOI MAE improves
2.266 to 2.115 minutes; isolate TOI/rate/context effects in future experiments.
Goalie opponent trial has mixed results: starter saves MAE 3.932 versus 4.027,
but slightly worse SA and GA. No broad goalie-model promotion.

Reusable `scripts/evaluate_daily_forecasts.py` writes separate evaluated
artifacts and preserves frozen forecasts. `scripts/write_recent_model_readout.py`
reproduces the readout. Older evaluator supports `--completed-only` and records
unfinished game IDs. A display-only rookie fallback-label bug was corrected for
future daily runs; the frozen underlying rates already used position shrinkage.

Before the next release: refresh availability/starter information, retain default
and candidate comparison, and improve lineup assumptions. Only 377/395 named
skaters in the pregame lineup scenarios appeared, although player forecasting
coverage was complete. October 12 predictions have not been newly issued by
this evaluation task; first remaining game starts 7 PM Eastern.

## October 10 daily release — 2026-10-10

Primary readout: `outputs/per_game_forecast/2026-10-10_pregame_readout.md`.
Reader bundle: `data/processed/forecasts/daily_2026-10-10_20261010T203436Z/`.
Use the wide `player_projections.csv`, `team_projections.csv`, and
`goalie_projections.csv`; detailed simulations/audits remain in the same folder.

Refreshed NHL season reports, schedule, rosters, ESPN league availability,
69-game history through October 9, complete fantasy scoring/goalie details,
2,484 game-level strength-specific TOI rows, and ESPN season projection benchmark.
Current season reports include October 10 activity, so model current rates are
rebuilt from games strictly before October 10. Fourteen games are retained;
three already-started games are explicitly late, eleven are pregame.

Five skater models issued: default, candidate, opponent_form_sog_trial,
calibrated_opponent_sog_trial, and usage_shot_context_trial. The fifth uses
last-five-game TOI/rate with fixed completed-history priors and team context
combining prior-season SOG and lagged 5v5 xOnGoal. No settings were optimized on
October 9. Nine NHL/MoneyPuck shot-disputed games are quarantined from current
chance updates. Original opponent/hybrid formulas remain separate comparisons.

Roster candidates now include prior-game players absent from the current roster,
with explicit review labels; missing player history receives completed-season
position priors. Montreal and Philadelphia team scenarios each require one
unidentified defense replacement; production is included transparently without
an invented NHL ID. Player and team coverage remains visible. Sparse count
constraints PPP<=G+A and goals<=shots are applied with before/after audit fields.

Goalie pipeline now uses supplied cutoff-safe game history for current rates,
separate completed-season priors, injury exclusions, and per-game issue timing.
Full-60 projections remain conditional; starts/duration/pulls are not calibrated.

Next: score the eleven prospective games on matching populations; test PP/EV
deployment and rest features, which are currently contextual columns. Validate
calibration, usage, raw opponent and xOnGoal effects separately over later games.
Current EDGE aggregates are excluded because a prior-date cutoff is unavailable.
Confirmed lineups/starters, calibrated participation and goalie-duration models
remain research tasks. No baseline promotion. Thirty-eight Python tests pass.

## Combined calibration/opponent trial — 2026-10-10

Added `calibrated_opponent_sog_trial` to the consolidated player/team tables
with `scripts/build_hybrid_trial.py`. Candidate shot and assist calibration is
retained; SOG also receives the frozen opponent/form factor. Goals and other
means remain candidate values. This fourth model was created after observing
October 9: retrospective exploratory results, never an issued pregame forecast.
Shot MAE on 143 common appearances: candidate 1.048, hybrid 1.050, default
1.058, opponent 1.059. Team MAE on identical refreshed lineup scenarios:
hybrid 7.816, candidate 7.823, opponent 8.862, default 8.870. No promotion.

Missing context receives a flagged neutral factor; a missing player SOG mean
requires a documented pregame prior. Jake O’Brien now has a SOG-only prior from
the frozen process model's past-position prior. Other categories/participation
remain unknown. Actual CBJ skater Damon Severson was absent from the saved
official roster context; repair roster acquisition/coverage prospectively,
without inserting postgame participants into a claimed pregame lineup.
Valid zero-rate estimates are preserved; sparse-history shrinkage remains a
separate validation question. Source shot-count disagreements remain flags.

Feature/source priorities: `docs/SHOT_FORECAST_FEATURES.md`. Next validation
should isolate calibration, opponent context, TOI/participation and strength
state features through chronological ablations with game-cluster uncertainty.

## October 9 evaluation and expected-shot acquisition — 2026-10-10

Completed all four final games with NHL boxscores and scoring summaries. Filled
the four consolidated tables; preserved frozen forecasts and a pre-evaluation
archive. Read `outputs/per_game_forecast/october_9_results_readout.md`.
143/144 positive-TOI skaters have simulation forecasts. Candidate shot MAE was
1.048 versus default 1.058; opponent trial 1.059. Keep default until a larger
chronological comparison supports promotion. Team lineup overlap is 139/144;
address lineups, TOI and rookie fallback before increasing opponent strength.

Acquired MoneyPuck's published team game history and October 9 xOnGoalFor,
xOnGoalAgainst, xGoalsFor and xGoalsAgainst. These describe observed chances,
not pregame predictions. Source shot counts differ from NHL for CBJ (45/47)
and WPG (16/17); discrepancies are retained and official NHL team SOG is scored.
Player shot outcomes use individual skater stats, which need not sum to the
official team totals. New script: `scripts/evaluate_october_9.py`.

Next: build cutoff-safe lagged MoneyPuck features by strength state with
prior-season shrinkage. Compare raw SOG, unblocked attempts, xOnGoal and xGoals
in chronological held-out windows. Reconcile source gaps before interpreting
chance rates. Improve goalie starter probabilities, duration/pull assumptions
and team/goalie shot reconciliation; evaluate starter and relief roles separately.
Do not feed October 9 postgame chance measures into October 9 predictions.

## Consolidated October 9 reading view — 2026-10-09

Primary reader-facing folder: `data/processed/forecasts/october_9_review/`.
Four tables: `simulation_summary.csv`, `team_projected_vs_actual.csv`,
`goalie_projected_vs_actual.csv`, and `game_team_coverage.csv`, with README and
provenance manifest. All models share one player table; goalie simulations and
rate projections share one goalie table. Latest injury labels are explicit,
without overwriting original issue labels or frozen source runs.

Team rows distinguish original and refreshed-injury lineup scenarios. Added
refreshed-lineup aggregates derive from frozen pregame means and lineup rules;
their consolidation time is not a new pregame issue time. Compare models within
the same lineup version. Actual fields remain blank until evaluation. Regenerate
with `scripts/consolidate_october_9.py`; it blocks overwriting populated actuals.
Use this consolidated view for the next postgame comparison rather than editing
the many frozen source folders. All prior research gates remain outstanding.

## Late October 9 pregame opponent SOG trial and injury correction — 2026-10-09

Frozen around 6:55 PM EDT before first puck drop. Refreshed ESPN status completed
at 22:53:52 UTC. Added a separate SOG trial for all four games, 178 modeled official
roster skaters, and a refreshed 18-skater team scenario for every team:
`data/processed/forecasts/opponent_sog_trial_2026-10-09_20261009T225456Z/`.
Formula: baseline SOG × sqrt(shrunken own SF/league SF × shrunken opponent
SA/league SF), with 20 league-average pseudo-games for each team rate. Adjustment
range: −1.75% to +1.86%. Fixed unvalidated assumptions, no prior-season team
priors or schedule-strength correction. Own-team form can double-count historical
player context; test incremental value. Other player means remain unchanged.

Injury audit: individual conditional-if-plays means correctly retain unavailable
players, but they are not unconditional forecasts. Team scenarios block saved
OUT/IR/SUSPENSION statuses. Previously goalie start shares did not block these
labels; fixed with a shared normalized status rule and renormalization. Fresh
IR labels set Hellebuyck and Korpisalo start shares to zero. If every candidate
is blocked, shares remain unknown rather than inventing a starter. DTD/UNKNOWN
and ACTIVE are not confirmed dressed lineups; roster-membership and participation
models remain incomplete. Original frozen artifacts are preserved.

Revised goalie artifact:
`data/processed/forecasts/goalies_2026-10-09_20261009T225533Z/`.
Twenty-one Python tests pass, including injury exclusion and all-blocked unknowns.
For evaluation use the explicitly versioned late trials alongside the original
models; do not silently substitute a new lineup while attributing all error changes
to the rate adjustment. Next: confirmed starter/lineup vintages, sparse-history
shrinkage, prior-season attack/defense priors and schedule-adjusted chronological
validation. No calibrated participation probabilities or injury recovery model.

## Added October 9 pregame goalie baseline — 2026-10-09

See the [goalie readout](outputs/per_game_forecast/october_9_goalie_readout.md).
New artifact: `data/processed/forecasts/goalies_2026-10-09_20261009T224516Z/`.
All four games/eight teams/18 official-roster goalies have separate historical
and opponent-context full-60-minute forecasts, SA/SV/GA simulations, provisional
start shares and team-win support proxies. All ESPN-rostered goalie rates are
exported even for teams not scheduled tonight. Fixed initial priors: 200 shots,
600 goalie minutes, ten team-context games and one start pseudo-count per goalie.

Excluded inconsistent player-season goalie rows from event-rate fitting, retained
all source values in an audit, and used valid completed-season league priors for
missing history. This is an explicit provisional alternative to source repair,
not resolution of the goalie data exceptions. Starts are used as separate role
observations. Twenty Python tests pass, including save-count identities and
exception exclusion. Original skater and team-scenario artifacts remain frozen.

Next: evaluate goalie SA/SV/GA conditional errors and start-share Brier scores
after tonight's final games; separate relief/partial starts from the full-60
scenario. Acquire confirmed starter vintages and prior-season role coverage,
validate prior strength and team/opponent effects chronologically, resolve count
exceptions and implement goalie decision/OT/pull logic. Start shares and win
proxies are uncalibrated. Historical save percentage is not opponent-adjusted
shot-quality talent. Add skater opponent effects as a separate future candidate.

## Current resume point: October 9 pregame simulations — 2026-10-09

Completed the [October 9 simulation/status readout](outputs/per_game_forecast/october_9_simulation_readout.md),
which also explains default October 8 performance, the candidate and improvement
priorities. All four games (SEA–DET, NYR–WSH, PIT–CBJ, ANA–WPG) and all eight
official roster lists are verified. Simulated 178 of 179 roster skater/game
entries; one lacks history and is explicitly retained. Official roster inclusion
does not establish that a player dresses. No GP or TOI threshold was applied.

- Refreshed NHL season reports and schedule around 3:45 PM EDT; refreshed ESPN
  completed before final forecast/simulation creation around 3:51 PM EDT. Exact
  UTC retrieval/build times are in manifests and the readout. Data remain 642
  observed skaters and 60 appeared goalies; 134 fantasy roster entries and 1,570
  available entries. Cumulative game/season reconciliation passed again.
- Default and frozen candidate receive 10,000 seeded conditional simulations
  per player/game. SOG/assists/hits are Poisson; goals are binomial conditional
  on shots, points=G+A, PPP is binomial conditional on points. Preserved
  conditional means, injury labels, count identities and missing model coverage.
- Stored summary quantiles/probabilities and 100 whole-number example draws per
  player/model. These are provisional, not calibrated predictive intervals.
  PIM, +/−, TOI, participation and goalie outcomes are not simulated.
- Scored fixed Poisson assumptions on all 351 October 8 appearances. One each
  of assists/SOG/HIT had positive actuals with zero forecast means, yielding
  infinite full NLL. Failures are reported, not excluded. Positive-mean residual
  diagnostics suggest checking extra variance but cannot select dispersion here.
- Latest frozen run:
  `data/processed/forecasts/simulation_2026-10-09_20261009T195119Z/`.
  Forecast inputs: `data/processed/forecasts/per_game_20262027_20261009T195052Z/`.
  Raw roster/schedule context:
  `data/raw/nhl/snapshots/simulation_context_20261009T194825Z/`.
- Seventeen Python tests and existing R pagination/population tests passed;
  simulation count identities, expected means, reproducibility and impossible
  outcome diagnostics are tested. Source/output hashes are recorded.

### Active next tasks (older dated entries below are historical)

October 9 team-total trial added before puck drop:
`data/processed/forecasts/team_trial_2026-10-09_20261009T201330Z/`.
All eight teams/four games have default and candidate totals for G/A/SOG/HIT/
points/PPP, decimal means, an analytical modal whole-number guess, simulated
exact-total probabilities and provisional ranges. Actual/error/exact-match fields
remain blank until final games. The scenario assumes 12F/6D: eligible last-game
appearances first, then predicted baseline TOI; saved OUT/IR/SUSPENSION labels
excluded, DTD/UNKNOWN retained. Every roster player and selection reason is
retained in a lineup audit. This is an unconfirmed lineup scenario, not a valid
unconditional team forecast. It does not replace the frozen individual run.

Implementation: `scripts/build_team_total_trial.py`; 18 Python tests pass.
Team goals exclude shootout deciding goals and goalie scoring contributions.
No cross-player dependence or team goal/assist accounting constraint is fitted.

Full team implementation remains a separate next step: acquire timestamped
announced/projected lineups and scratches; model correlated participation, allow
11F/7D as well as 12F/6D, cover no-history players, incorporate role/opponent
context and team/player scoring dependence. Validate means, exact-count
probabilities and intervals chronologically. Compare non-shootout team goals
and official player-summed hits, with lineup error separated from rate error.

1. [ ] Evaluate the frozen October 9 run only after all four games are final,
   comparing identical appearances, probabilities, log scores and interval
   coverage. Preserve unavailable/absent rows and game/date clustering.
2. [ ] Add and chronologically validate position-prior shrinkage for sparse and
   zero-count histories as a separate candidate; the current multiplicative
   correction cannot fix zero-mean support failures. Do not refit on October 8
   and still call it untouched.
3. [ ] Acquire prior-season game logs and historical roster eligibility. Current
   season logs are complete, but participation and rolling TOI are not fitted.
   Establish non-overlapping game train/validation/test windows before tuning
   current-season updates, TOI response and rookie priors.
4. [ ] Fit a negative-binomial alternative using training/validation only, then
   assess held-out probabilities/interval coverage. Add joint category/team
   dependence only after marginal distributions pass checks.
5. [ ] Resolve goalie count exceptions and minimum-start rules, chronologically
   validate the new provisional goalie start/rate and opponent-context baselines,
   then feasible replacement and lineup decisions.

These are unresolved research gates, not completed merely by producing draws.

## October 8 evaluation and full current-season game archive — 2026-10-09

Completed the [October 8 readout](outputs/per_game_forecast/october_8_readout.md)
without refitting the October 6–7 calibration candidate. Ten games, 351 matched
appearances and 68 scoring-roster appearances. Baseline/candidate SOG MAE:
1.1092/1.0908; assists MAE: 0.4185/0.4141. Candidate totals undershot both
categories and assist bias worsened. Keep weighted history as the live default;
one-night gains do not establish stable superiority.

- Refreshed NHL season reports, schedule and ESPN around 3:25 PM EDT. Current
  observations: 642 skaters, 60 appeared goalies (one source-count exception),
  134 scoring-roster entries, 1,570 available entries; 116 skaters forecasted,
  18 goalies remain unmodeled.
- Acquired all 65 final current-season regular-season boxscores through October
  8 (four October 9 games still pending). Stored 2,340 skater/game rows and 260
  goalie/game rows, including unused backups. Official scoring summaries fill
  PP assists and PPP; skater G/A and PP goals reconcile with boxscores.
- All 642 cumulative skater IDs match latest season reports across GP, G, A,
  points, SOG, HIT, PIM, +/−, PPP and TOI. Preserved one game-level goalie
  SA=SV+GA exception and undefined zero-TOI backup ratios.
- All 18 ESPN snapshot ratio checks passed: ATOI=TTOI seconds/GP,
  GAA=GA×3600/goalie TOI seconds, SV%=SV/SA. This settles the observed snapshot
  arithmetic, not historical eligibility or unknown minimum goalie starts.
- Detected duplicate ESPN identities for Legault and Agozzino. Retained alias
  rows in audits, checked forecast agreement, and counted each NHL player/game
  once during evaluation. No October 8 skater team-shot exceptions.

Next: acquire prior-season game and roster-eligibility history, define chronological
train/validation/test windows, evaluate rolling TOI and participation, and assess
calibration over more dates. October 8 is now observed evaluation data; do not
retune using it and still label it untouched. Frozen factors remain unchanged.

## October 6–7 model diagnosis and experimental calibration — 2026-10-09

Completed the [diagnosis and recommendations](outputs/per_game_forecast/october_6_7_model_recommendations.md)
before reading October 8 outcomes. Shot overprediction decomposed into 10.45
shots associated with TOI error and 30.45 remaining rate residual. Fantasy
roster TOI was slightly low, so a blanket ice-time reduction is unsupported.

Added a separate, unvalidated pooled SOG/assist calibration candidate with
200 pseudo expected events anchored at ratio 1: SOG ×0.92588, assists ×0.96229.
Goals remain unchanged; points are recomputed. Preserved baseline columns,
unknown participation, and injury review flags. Settings and calibration dates
are frozen in `config/game_calibration_candidate.json`. October 8 candidate
forecasts are a retrospective reconstruction from saved pregame features,
not a forecast issued before the games. Live baseline remains unchanged.

Next: evaluate unchanged baseline and frozen candidate on identical October 8
appearances before further tuning. Extend chronological evaluation and eligibility
coverage before promotion; do not interpret six games as 213 independent trials.

## October 6–7 game review and refreshed forecasts — 2026-10-08

Completed the first frozen game-level diagnostic; see the
[readout](outputs/per_game_forecast/october_6_7_readout.md). Acquired all 12
regular-season final boxscores (432 skater/game rows). Only six games had saved
pregame scheduled forecasts: the October 6 artifact was created after six games
had started. Never reconstruct those earlier predictions with refreshed totals.

- Evaluated 213 appearances: predicted/actual G 38.84/37, A 66.03/56,
  SOG 351.91/311. This is a small conditional-production diagnostic, not tuning
  evidence or proof of game-level calibration. Retained absent and unresolved rows.
- Flagged Florida's October 6 sum of skater SOG (29) versus team SOG (30);
  preserved source counts and reported the exception. Cause remains unresolved.
- Refreshed current-season NHL summary/TOI/realtime and separate goalie reports,
  schedule and ESPN at approximately 4:30 PM EDT. Skater validation passed:
  630 skaters; 56 goalies with one count exception. ESPN: 134 scoring-roster
  entries, 116 forecasted skaters and 18 unmodeled goalies; 1,568 available entries.
- Rebuilt unchanged baseline and exported October 8 forecasts for ten games,
  with conditional means and preserved injury labels. Exact snapshots, coverage,
  and rerun commands are in the readout. Generated data remain Git-ignored.
- Existing 11 Python tests and R pagination/population checks passed; the
  review also ran successfully offline from preserved boxscores.

Next: extend frozen chronological game-level comparisons; investigate predicted
versus observed TOI and SOG/minute before adjusting shot rates. The participation,
rolling-TOI and chronological update-validation tasks below remain outstanding.

## Per-game forecast baseline — 2026-10-06

Implemented the first ELWAY-inspired rate comparison; see
[methodology and commands](docs/PER_GAME_FORECAST.md) and
[results](outputs/per_game_forecast/README.md). This supersedes older statements
below that no historical forecast or ESPN snapshot exists. It does not mark the
full opportunity/goalie/replacement pipeline complete.

- Refreshed official NHL summary, TOI, realtime and separate goalie reports for
  2021–22 through 2026–27. The current season contains 617 reported skaters and
  53 goalies; one current goalie source-count identity exception remains flagged.
- Validated all six skater seasons, retaining every player. Frozen split:
  development 2023–24, selection 2024–25, held-out evaluation 2025–26.
- Compared last-completed-season rates, recency-weighted history, and a visible
  minutes × event-rate model with shooting-conversion shrinkage. Validation
  narrowly selected the weighted baseline; preserve the process model as a
  candidate rather than choosing it after inspecting test results.
- Held-out evaluation includes 820 returning skaters. The selected model's
  goals/assists MAE is approximately 5% lower than the last-season baseline;
  shots MAE is effectively unchanged. These are season-average per-game errors,
  not evidence of individual-game accuracy, calibrated intervals, or causal skill.
- Refreshed ESPN: six teams, 134 scoring-roster entries, 1,566 available entries.
  All 117 rostered skaters receive conditional forecasts; 17 goalies remain
  unmodeled. Preserve the documented pending-drop roster/waiver overlap.
- Added current-season updates and rookie shrinkage fallbacks, both provisional
  until evaluated at game cutoffs. Exported upcoming skater/game conditional means
  and the seven-day schedule-only reference. Participation probabilities and
  unconditional game expectations remain unknown.

### Next implementation tasks, in order

1. [ ] Acquire game-level skater events/TOI and historical roster eligibility with
   source coverage checks. Distinguish missed appearances from missing coverage;
   today's ESPN roster cannot reconstruct historical eligibility.
2. [ ] Implement and evaluate the existing
   [participation and rolling-TOI specification](docs/EXPECTED_OPPORTUNITY.md),
   using non-overlapping chronological train/validation/test game windows.
3. [ ] Evaluate the current-season updating rule and no-history fallback at those
   cutoffs, then multiply calibrated appearance probability by conditional event
   means. Add opponent/role effects only against this baseline.
4. [ ] Resolve goalie count exceptions and verify ESPN ATOI/category aggregation,
   then fit separate goalie-start and goalie-rate baselines.
5. [ ] Add uncertainty, feasible replacement and matchup decisions only after the
   preceding gates; retain all roster/identity/data limitations in exports.

---

## ESPN Fantasy connection milestone — 2026-10-03

A read-only connection to the private ESPN Micro League is now working through
`espn-api`, with credentials kept only in the local `.env`. The connector uses
the macOS system trust store via `truststore` so Homebrew Python can validate
ESPN's HTTPS certificate chain without disabling SSL verification.

The first timestamped league snapshot completed successfully:

- Raw snapshot: `data/raw/espn/snapshots/espn_2027_20261003T160748Z`
- Processed crosswalk: `data/processed/espn/espn_2027_20261003T160748Z`
- Teams: 6
- Rostered players: 132
- Available players: 1,560
- Current matchups: 3
- Matchup/category rows: 108
- ESPN→NHL crosswalk: 1,017 matched, 674 unmatched, 1 ambiguous

Current ESPN tooling:

- `src/fantasy/espn_client.py`: authenticated read-only league connection
- `src/fantasy/espn_snapshot.py`: normalized timestamped snapshot pipeline
- `scripts/test_espn_connection.py`: connection smoke test
- `scripts/refresh_espn_snapshot.py`: live league refresh command
- `docs/ESPN_CONNECTION.md`: credentials, setup, and snapshot documentation
- `requirements-espn.txt`: isolated connector dependencies

### Resume here when ESPN/fantasy work restarts

1. [ ] Build a latest-snapshot report that automatically selects the newest ESPN
   snapshot and prints all six team rosters plus ESPN position eligibility.
2. [ ] Measure ESPN→NHL crosswalk coverage specifically for the 132 rostered
   players, list every unmatched or ambiguous rostered player, and fix high-value
   crosswalk gaps before broad free-agent cleanup. Never force an ambiguous match.
3. [ ] Identify the user's fantasy team in the snapshot and produce a concise
   current-roster view with lineup slot, eligibility, NHL team, injury status,
   and NHL player ID where matched.
4. [ ] Validate current H2H category extraction, including category names,
   directionality, ratio handling, and ESPN's ATOI aggregation behavior.
5. [ ] Filter the available-player pool to NHL-matched, fantasy-relevant players
   and build the first waiver/add-drop candidate report. Keep performance
   projection separate from current ESPN totals and ownership context.
6. [ ] Add league-aware replacement value/FVAR only after the projection baseline
   is validated; then use matchup state, remaining schedule, roster eligibility,
   and the seven-acquisition limit for weekly streaming decisions.

This is intentionally paused after establishing reliable live data acquisition.
The next ESPN milestone is analysis of the latest snapshot, not more connection
or authentication work.

---

## Minnesota defense-pair ad hoc analysis — 2026-09-29

Completed a descriptive 2025–26 regular-season study: how often did each Wild
defense pair appear together, and what share of team goals occurred with them?
See [full pair/scorer report](outputs/min_defense_pairs_2025_26/README.md) and
`src/analysis/min_defense_pairs.py` for reproducible acquisition and analysis.
All 82 games, 247 source files, 14 defensemen and 67 observed combinations are
included without usage thresholds. The denominator is 268 non-shootout goals;
205 had two defensemen, 59 had one, two had three, and two had none. Three-D
goals credit every co-present pair, so pair shares are not a partition.
Showings mean continuous shared shift intervals; games and minutes are also
reported. Official HTML on-ice lists determine goal attribution independently
of shift boundaries. All game scores reconciled with API goal events and HTML
reports; shift totals and source hashes passed validation. Three exact duplicate
defense shift intervals were deduplicated for usage, preserving raw sources.

Local source snapshot: `data/raw/nhl/snapshots/min_pairs_20252026_20260929T192759Z`.
Five processed CSVs and coverage metadata are in
`data/processed/min_defense_pairs_2025_26/`. These generated datasets are ignored
by Git. The report and script are retained. Goal shares reflect exposure and
all-strength context; they do not establish pair skill. A follow-up question
is whether differences persist after separating five-on-five usage from special
teams and accounting for shared minutes and teammate/opponent context.

## Fantasy strategy review — 2026-09-28

Reviewed the [draft strategy](docs/FANTASY_DRAFT_STRATEGY.md),
[variable dictionary](docs/FANTASY_VARIABLE_DICTIONARY.md), and
[league template](config/fantasy_league.example.yml). These are design documents;
no fantasy forecasts, backtests, or rankings have been implemented. The existing
processed dataset is a single 2025–26 skater season, not a historical evaluation
panel. The broader research roadmap below remains applicable.

Research question for the first fantasy milestone:

> Do multi-season, exposure-weighted skater rates improve held-out season event
> forecasts over last-season totals and a simple rate × projected-GP baseline?

### Review findings to resolve

- Preserve the separation of opportunity, event forecasts, league scoring,
  replacement, and market price. The proposed full board is a long-term output,
  not the acceptance criterion for the first baseline.
- Historical facts retrieved today are not historical as-of snapshots. Record
  retrieval time separately from event time; document retrospective corrections
  and unavailable roster/injury/eligibility history. Do not claim a strict as-of
  backtest when the necessary vintages are absent.
- The template uses null for unknown settings. Before a validator is implemented,
  distinguish unknown, explicitly unlimited, and not applicable; zero slots or
  an explicitly empty keeper list must remain valid when confirmed.
- The pick-urgency expression is illustrative. Its cliff and opportunity-cost
  terms need the same utility units, and can overlap with replacement value.
  Test a candidate-now/alternative-next comparison before adopting this score.
  Auction drafts require budget and nomination rules, not next-pick survival.
- Define allowed positions for UTIL/FLEX and the scope of limits (per player,
  roster, week, or season). Slot names and numeric caps alone are insufficient
  to verify a feasible lineup.

### Next implementation steps

1. [ ] Capture actual league settings and draft deadline in a working config.
   Confirm scoring, slots, eligibility, lineup locks, limits, keeper rules and
   draft type. Keep the example unconfigured; do not infer platform defaults.
2. [ ] Build a source/coverage inventory for the scored events, opportunity,
   goalie outcomes, platform eligibility and ADP. Identify which historical
   cutoffs are reconstructible. League-independent historical work can proceed
   while settings are pending; league valuation cannot.
3. [ ] Acquire and validate a small multi-season regular-season panel with
   explicit provenance. Choose training, tuning and held-out target seasons
   before modeling; every target season needs earlier feature history. Preserve
   players without next-season appearances and distinguish verified zero GP
   from missing coverage. Report rookies and sparse-history fallbacks separately.
4. [ ] Implement `R/analysis/05_fantasy_projection_baseline.R` for a limited
   skater event forecast comparison. Start with G, A and SOG, deriving P=G+A;
   add actual scored categories as their inputs pass validation. An aggregate
   baseline is a research deliverable, not fulfillment of the final board gates.
   Use all-strength rates until matching strength-level counts and TOI exist.
5. [ ] Save held-out GP/event MAE and bias, population/missingness reports and
   baseline comparisons by position and history. Fit shrinkage and choose
   history weights using training/validation data only. Do not report predictive
   quantiles until their construction and coverage have been evaluated.
6. [ ] Add separate goalie baselines if the league includes goalies, then test
   exact league scoring and feasible replacement using hand-worked examples.
   Keep ADP survival, joint scenarios and draft updates as subsequent milestones.

### League settings received — 2026-09-28

The user supplied the ESPN Micro League settings PDF. Transcribed settings are
in [config/fantasy_league.micro.yml](config/fantasy_league.micro.yml), marked
partial because unprinted rules remain unknown. Six teams; H2H each category;
snake draft September 28 at 8:30 PM EDT, order randomized at 7:30 PM EDT.
Active slots: 9 F, 5 D, 1 UTIL, 2 G; five bench spots, one IR, maximum four
rostered goalies. Daily individual game-time locks; seven acquisitions per
seven-day matchup; no skater/goalie games-played maximum.

Skater categories: G, A, +/-, PIM, PPP, ATOI, SOG, HIT.
Goalie categories: W, GAA, SV%. No keepers for 2027 or 2028.

Before the fantasy refresh, the saved processed CSV was inspected: 940 rows and unique player IDs for
20252026. Seven of eight skater category inputs are present with no missing
values; hits are absent. This is a coverage check, not a new full validation.
Goalie forecasts and platform eligibility are not provided by this skater table.
ATOI is an average and needs verified ESPN aggregation, not summed player rates.

Tonight's next deliverable is a clearly labeled historical category worksheet,
with hits/goalie coverage resolved or flagged before any complete draft board.
Draft position can be added when available. Confirm goalie minimum starts,
ATOI aggregation and UTIL eligibility; the PDF does not settle those details.

### Fantasy acquisition completed — 2026-09-28

Extended the existing pagination pipeline to support separate goalie reports.
Run `Rscript R/analysis/00_refresh_fantasy_snapshots.R 20252026` to reproduce
summary, TOI, realtime (hits), and goalie acquisitions. The live snapshot is
`data/raw/nhl/snapshots/fantasy_20252026_20260928T145951Z`;
historical worksheets are in the matching `data/processed/fantasy/` directory.
All three skater reports contain 940 matching IDs and GP; the existing full
skater build validation passed. All eight skater category inputs are now present.
The goalie report contains 98 unique IDs, but 22 rows fail SA=SV+GA. Preserve
these source values and block affected rows from valuation pending investigation;
see `goalie_validation_exceptions.csv`. SV% and GAA denominator checks passed.
Pagination tests (including goalie-specific coverage) passed; source file hashes
were independently verified. Existing raw snapshots were preserved.
Compared with the September 17 summary snapshot, four player rows changed;
no player IDs were added or removed. The reason for those source changes has
not been established.

Saved work and handoff:
- `config/fantasy_league.micro.yml`: transcribed league rules and unresolved inputs.
- `R/functions/get_nhl_skaters.R`: shared skater/goalie retrieval with compatible skater calls.
- `R/analysis/00_refresh_fantasy_snapshots.R`: reproducible four-report refresh and exports.
- `R/tests/test_nhl_pagination.R`: existing pagination cases plus goalie population checks.
- `docs/NHL_ACQUISITION.md`: commands, validation behavior and goalie exceptions.
- `data/processed/fantasy/fantasy_20252026_20260928T145951Z/`: local
  `historical_skaters.csv`, `historical_goalies.csv`, and
  `goalie_validation_exceptions.csv`. These and the raw timestamped snapshot
  are intentionally Git-ignored generated data, saved locally but not committed.
  Re-running acquisition can reflect later source corrections; preserve the
  local snapshot separately if the exact retrieved version is needed elsewhere.

Next: investigate the goalie count discrepancy, verify ESPN ATOI aggregation,
and build the historical category worksheet. Current injuries, ESPN eligibility,
and draft-market information remain separate inputs. Additional historical
seasons are still needed for a backtested projection model; this acquisition
does not establish a forecast.

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
