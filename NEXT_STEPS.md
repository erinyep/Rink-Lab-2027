# Rink Lab — Next Steps

## Feature evidence completed before October 20 games

[Report and per-player/team contribution tables](outputs/per_game_forecast/feature_evidence_2026-10-20/README.md) · [Published searchable evidence](https://erinyep.github.io/Rink-Lab-2027/evidence/).

- Existing usage-trial SOG accounting reconciles 498 candidate players, 395 selected players and 22 team means (one unidentified Colorado replacement). TOI/rate/calibration/matchup contributions are ordered forecast movements, not causal or independent importance.
- Saved October 10/12 cohort: 468 appearances across 13 games. Calibration contributes the clearest overall SOG improvement (-0.018 MAE); fantasy subgroup instead worsens +0.022 at this ordered stage. Recent rate and matchup changes do not show a reliable aggregate gain. No per-player predictive importance established.
- Fixed-design retrospective screen: train October 5–12 (50 games), hold out October 13–19 (51 games). Team SOG MAE: bias control 4.621, PBP D 4.634, shot quality 4.823, both 4.813. All incremental benefit intervals cross zero. Quarantines preserved; missing features use training-only imputation. Corrected current downloads are not historical as-of vintages.
- Four experimental team-volume variants refitted through October 19 and frozen before puck drop for all 11 October 20 games, with coefficient/sample-size/contribution tables. No replacement of main models. Config: `config/pregame_feature_audit.json`; producer: `scripts/publish_feature_evidence.py`.
- After acquiring final actuals, score without refitting: `scripts/evaluate_feature_evidence.py --evidence outputs/per_game_forecast/feature_evidence_2026-10-20 --actuals <refreshed-actuals> --out <new-evaluation-directory>`. It rejects late trials and scores identical completed games for every variant; missing finals stay unscored.
- Next: accumulate prospective performance, archive daily source vintages, inspect fantasy/role subgroups, and acquire shift-based deployment before D-pair/PP claims. These tests address SOG, not all categories or goalie performance.


October 20 publication refresh: GitHub Pages matchup and fantasy views now use today's 11-game frozen bundle. Root links/date labels and category SVG were refreshed; October 17 pages are archived under `docs/archive/2026-10-17/`. Fantasy report handles nonfinite ESPN goalie rates as unavailable; no transactions performed.

Latest completed milestone: [October 20 season audit and issuance](#season-to-date-audit-pregame-release-and-defense-events--2026-10-20). All 140 finals acquired; 11-game pregame bundle issued. The October 17 reports below are preserved historical context.

## Active plan — 2026-10-17

Make the next phase answer: **Which start/sit, add/drop or streaming decision
improves our actual fantasy matchup?** Keep the hockey research foundation;
connect forecasts to league scoring, usable starts and concise recommendations.
This checklist supersedes the priorities in the historical notes below.

### Working local baseline — October 17

Python 3.12 environment and six NHL season snapshots rebuilt on this machine.
[Today's public-data forecasts](outputs/per_game_forecast/2026-10-17_daily_2026-10-17_20261017T171641Z_pregame_readout.md)
cover 13 games pregame and one late game; all 120 final games through October 16
and 4,319 positive-TOI appearances validated. Five skater models and two goalie
scenarios are finalized. The one-command runner passed an end-to-end public-mode
run; 49 unit tests pass. Issued bundles are retained separately.

Completed: standalone MoneyPuck acquisition, date-aware finalizer, explicit
public-only mode, ESPN freshness gate, and refresh/build/finalize orchestration.
Fixed positive-TOI coverage validation without discarding zero-minute source rows.

**ESPN connected — October 17, 1:30 p.m. Eastern:** local credentials verified;
read-only refresh returned six teams, 134 rostered and 1,572 available players.
[New league-aware bundle](outputs/per_game_forecast/2026-10-17_daily_2026-10-17_20261017T173051Z_pregame_readout.md)
issued for 13 pregame games and one late game. The full refresh/build/finalize/
validation runner passed with fresh ownership, injuries and an ESPN benchmark.
Earlier public-only bundles remain frozen. Lineups/starters remain provisional;
optimized start/sit and transaction recommendations are still pending.
Transfer historical `data/raw/` and `data/processed/` from the other machine to
retain older prospective evaluations. See [local setup](docs/LOCAL_SETUP.md).
Remaining priorities: release validation/freshness automation, permanent
scoreboard, exact scoring and usable-start value. No unattended schedule enabled.

### Daily category report working — October 17

[Quinn’s report and interactive charts](reports/today/README.md) now combine the
frozen default forecasts with verified H2H category scoring, roster eligibility,
individual-game lineup locks and a next-period roster audit. Charts show saved
category gaps, selectable conditional skater means, and the roster schedule;
streamers sort by category with one-start active-slot feasibility. SVG export,
CSV downloads and source hashes are included. 54 unit tests pass; Chrome checks
passed for charts, controls, mobile overflow and SVG downloads.

User-reported Byram → Pionk move is reflected accurately: ESPN retains Byram as
FUTURE_DROP today and includes Pionk in scoring period 20. Today's saved roster
has no unlocked benched skater with a game. Do not assume Pionk can start today.
The calendar uses the next-period roster for later dates as a static scenario.

There is no fantasy-points objective in this category league. Compare category
tradeoffs, keeping ATOI, GAA and SV% exposure-weighted. The daily runner now
builds the report for team 5 via `config/fantasy_report.json`; public-only mode
skips it. Reports are timestamped local artifacts, not live dashboards.
Remaining work: verify effective transaction dates and daily acquisition usage,
extend slot feasibility to future days and attainable replacement/drop choices,
then log prospective decisions and outcomes in the permanent scoreboard. No
category-win probabilities or automatic transaction recommendations are issued.

### GitHub report packaging — October 17

A reviewed static report is packaged under `docs/report/` with a README SVG
preview. Enable Pages once from `main` → `/docs`; see
[GitHub Pages setup](docs/GITHUB_PAGES.md). Credentials, raw source snapshots
and local generated datasets remain ignored. Today’s acquisition lock now
sets new-add usable starts to zero after the first scheduled game.

### All-NHL matchup reading view — October 17

[All 14 NHL game predictions](docs/games/README.md) now pair the existing frozen
team forecasts against official away/home identities. Each card compares goal
means, provisional goal/shot ranges, scoring edge, assumed shot leaders and
separate full-start goalie scenarios. All five skater models and both goalie
variants remain selectable. Thirteen pregame games show by default; late-issued
NJD–WSH is separately labeled. No model refit or new win-probability claim.

The live report is at `https://erinyep.github.io/Rink-Lab-2027/games/`; GitHub
Pages is enabled. The daily runner also generates an NHL view inside each local
bundle. Regenerate the reviewed Pages copy explicitly with
`scripts/build_nhl_outlook.py --bundle <issued-bundle>` before committing it.
59 unit tests and Chrome model/filter/chart/goalie/mobile checks pass.
Goal models still need fitted opponent/goalie adjustments and prospective
calibration; current scoring leans are comparisons of conditional means.

### 1. Make daily forecasts reliable

- [x] Finish standalone MoneyPuck acquisition and the date-aware daily finalizer.
- [ ] Generalize date-specific postgame evaluation/readout text.
- [x] Run refresh → skater/goalie forecasts → finalization → coverage checks in
  one command with an explicit target date. Record source cutoffs, freshness,
  hashes, game IDs and issuance times; label late games separately.
- [ ] Address missing players using official rosters and recent participants.
  Keep probability of playing separate from production conditional on playing;
  keep goalie starts, relief and expected duration distinct.
- [ ] Add scheduled execution, retries and alerts after the credential-free
  runner and freshness gates are reliable.

### 2. Build one permanent prospective scoreboard

- [ ] Create an append-only prediction/result history and derived
  `model_scoreboard.csv` (Parquet if useful). Preserve issued predictions and
  version actuals/source corrections rather than rewriting history.
- [ ] Key records by model/version, issuance, game and player/team; retain input
  cutoffs, forecast timing, ownership snapshot and coverage/missingness flags.
- [ ] Report MAE, RMSE, bias, coverage and probability calibration for the season
  and rolling 7/30-day windows. Compare matched pregame samples with paired
  game-cluster uncertainty.
- [ ] Break out forwards, defensemen, goalies, fantasy-rostered players, waiver
  candidates and shot-volume groups. Keep aged baseline and late forecasts
  distinct from fresh prospective comparisons.

Evidence to carry forward: in the October 10/12 trial (13 games, 468 matched
skater appearances), candidate/default SOG MAE was 1.0445/1.0646 and team MAE
3.4791/4.0672. Default retained a small, uncertain fantasy-subgroup edge
(1.3108/1.3253). Keep default as baseline and candidate as challenger; these
results do not justify promotion or blanket corrections.

### 3. Define fantasy value and ship a concise daily view

- [x] Validate exact category scoring, roster slots/eligibility and saved
  roster/waiver/schedule inputs; do not invent a points total for H2H categories.
- [ ] Resolve daily acquisition usage and effective transaction dates; evaluate
  category-aware decision gains in the scoreboard.
- [ ] Estimate replacement value by eligible slot and **usable** starts under
  lineup constraints. Rank start/sit and streamer choices by incremental matchup
  points, accounting for the displaced player and transaction limits.
- [x] Create `reports/today/` with roster/availability actions, category charts,
  streamer slot fit and downloads. Label conditional forecasts and source times.
- [ ] Add validated incremental category value and concise start/sit tradeoffs
  when feasible alternatives exist; keep transaction gates explicit.
- [ ] Keep detailed diagnostics in `reports/model_health/`, reviewed weekly.
  Log recommendations and alternatives as issued, then evaluate realized
  decision gains against the saved baseline choice.

### 4. Improve opportunity and role before adding model complexity

- [ ] Model EV/PP/SH minutes, PP role and participation explicitly, using
  past-only rolling usage and shrunk player-rate estimates.
- [ ] Acquire and validate NHL play-by-play: attempts, strength-state exposure,
  shot locations and defensible rush/rebound or sequence features. Use ixG only
  from a documented source/model; do not treat current D production proxies as
  measured chance creation.
- [ ] Test position × role interactions and fitted team/opponent, rest and
  home/away effects. Check player totals against expected team opportunity.
  Saved context fields are not evidence of fitted predictive value.
- [ ] Freeze TOI-only, rate-only and context-only ablations on unseen games;
  assess fantasy and position subgroups before adopting changes.

### 5. Add challengers, distributions and matchup simulation

- [ ] After the feature pipeline is validated, compare one boosted-tree
  challenger with the interpretable baseline using chronological holdouts and
  prospective issuance. Test count models such as Poisson/negative binomial.
- [ ] Calibrate count probabilities and predictive ranges; evaluate goalie
  shot-volume and goals-allowed effects separately. Existing simulation ranges
  remain provisional until validated.
- [ ] Once joint forecasts and roster constraints are credible, simulate the
  remaining matchup and compare legal transactions by expected points or win
  probability under the league's actual scoring format. Account for shared
  game/team uncertainty rather than assuming independent player outcomes.

### Defer

More manual calibration constants, elaborate defense proxies, bespoke long
postmortems, conclusions from tiny model shootouts, and marginal all-NHL MAE
optimization without fantasy benefit. NCAA translation, player similarity and
exotic tracking features remain longer-term research tracks.

## Historical milestones and reference plans

Retained for provenance and commands. Dates and unfinished checklists below are
historical; use the active plan above to choose new work.

## Project Goal

Build a reproducible hockey analytics research environment using R and Python
to investigate player talent, repeatability, predictive value, and
NCAA-to-NHL translation.

The central research question is:

> Which measurable player actions represent repeatable talent, which contribute
> meaningful value, and which predict future NHL performance?

---

## Season-to-date audit, pregame release and defense events — 2026-10-20

Read [season results through October 19](outputs/per_game_forecast/season_through_2026-10-19/README.md)
and [source quality/shot-quality chart](outputs/per_game_forecast/season_through_2026-10-19/source_quality.md).
All 140 final regular-season games acquired and validated: 5,039 positive-TOI
skater appearances. Saved season-rate baselines cover 2,422 appearances in 69
games; 71 games lack a saved baseline. The prospective five-model daily sample
remains 13 October 10/12 games, not 140. Older October 9 issued simulations,
opponent SOG and goalie trials are re-evaluated separately; postgame reconstructions
remain excluded. Baseline SOG MAE over covered appearances is 1.043, bias +0.092.
This selects the latest saved pregame snapshot per whole game and represents a
changing issuance policy, not a fixed-version full-season backtest.

Daily trial candidate/default player SOG MAE remains 1.044/1.065 and team MAE
3.479/4.067. Default retains the saved fantasy-player edge, 1.311/1.325.
Opponent goalie saves improve 4.188→3.949 but GA worsens 1.231→1.264.
Additional October 17 published exports provide 12 publication-safe team/goalie games: team SOG MAE candidate/default 4.200/4.392; goalie saves trial/baseline 4.298/4.249 (earlier advantage reverses), GA 1.334/1.366. Full player forecasts remain unavailable locally; transfer the original bundle for complete evaluation. Continue comparison without promotion or new blanket calibration.

Completed now:

- Acquired official NHL PBP for 140 games: 16,025 attempts, no missing shooter
  positions/coordinates. Two team-game SOG disagreements quarantine both games.
  New all-strength/5v5 inputs include D attempts, unblocked attempts, SOG,
  near-net attempts, D scoring involvement and 10-second teammate followups.
  Followups are temporal associations, not passes, possession chains or causal
  creation. No D-pair or on-ice rate claim without shifts.
- Standalone MoneyPuck team refresh covers all 140 games. Acquired published
  shot data: 11,613 unblocked events, 124 original fields. Forty-nine games have
  an official SOG disagreement and are quarantined for shot-quality summaries.
  Derived missing-position fallback uses same-game NHL boxscores (164 missing
  raw positions, zero unresolved). Credit MoneyPuck.com; raw files unchanged.
- Future daily builds save lagged PBP and optional D xG/expected-rebound context,
  with explicit cutoff/quarantine/sample sizes. No coefficients fitted.
- Public read-only Kalshi snapshot across seven requested NHL series assesses
  coverage/spreads/volume. Quotes remain unmapped and unused by forecasts; this
  cannot reconstruct historical pregame markets. No orders/account access.
- Fixed issuance's zero-TOI population mismatch, replaced hard-coded October 10
  finalization text, added full-release timing/freshness/coverage/category/count
  checks, preserved immutable goalie parent provenance, and enabled repeated
  dated releases without overwriting prior bundles.

Latest [October 20 pregame release](outputs/per_game_forecast/2026-10-20_20261020T125723Z_pregame_readout.md):
11 games, 22 teams, 2,490 player/model rows, 110 team/model rows and 102
goalie/model rows, released 12:57:39.690935 UTC (8:57 AM EDT; consult manifest for exact
completion). All five skater/two goalie models are present. Colorado has one
unidentified lineup replacement; other lineups and all starter shares remain
provisional. Original forecasts/actual fields preserved. Earlier October 20
release checks are retained as separate artifacts; use this latest bundle:
`data/processed/forecasts/daily_2026-10-20_20261020T125723Z/`.

The integrated `scripts/run_daily_forecasts.py` also supports the PBP/shot-quality inputs and publishes matchup/category views. The projection-only command below is useful when those personal report views are unnecessary.

Single-command future issuance (set target date explicitly):

```sh
rink-lab.venv/bin/python scripts/issue_daily_forecasts.py \
  --date 2026-10-21 \
  --template-forecast data/processed/forecasts/per_game_20262027_20261009T195052Z
```

This refreshes official finals, scoring, TOI, ESPN, MoneyPuck teams/shots and
PBP, builds skaters and goalies, then finalizes only if every scheduled game is
still at least ten minutes away, retrievals/injuries are at most six hours old,
and preceding-day history is complete. MoneyPuck lag requires an explicit
`--allow-context-lag` exception and remains visible. `--prepared-inputs <JSON>`
reuses freshly acquired input paths; that build/finalize path was exercised end
to end, with the refresh subcommands also run individually. No scheduler enabled.
Morning issuance does not verify evening lineups; run again nearer puck drop.

Next experiments, in order:

1. Resolve MoneyPuck/NHL shot revisions before depending on broader xG features;
   retain quarantines and test coverage bias from missing games/teams.
2. Acquire/validate NHL shifts for D-pair minutes, linemates and PP deployment.
   No event-level passing/entry claim from standard PBP alone.
3. Freeze TOI-only, rate-only, matchup-only and D-context-only variants on unseen
   games. Use paired game uncertainty, role/fantasy subgroups and calibration;
   test shot quality/rebound inputs only after source and exposure checks.
4. Map Kalshi contracts/rules to NHL IDs, collect actual pregame quote histories,
   depth and last-trade times, and evaluate market-only versus model-only before
   blending. Do not equate winner probability with expected SOG.
5. Schedule the runner on an available host with retries, idempotence, secret
   handling and failure alerts. Keep personal ESPN credentials/snapshots local.

Full source recommendations and official links: [data-source strategy](docs/DATA_SOURCE_STRATEGY.md).

## Weekly review and defense opportunity inputs — 2026-10-16

Read [October 12–15 weekly review](outputs/per_game_forecast/week_2026-10-12/README.md).
All 32 final games and 1,151 positive-TOI appearances reviewed; 1,119 have older
October 9 baseline forecasts and 32 are missing. Only two games this week have
issued five-model and goalie trials. All nine skater/team categories and three
goalie count categories are exported; missing challenger forecasts are never
reconstructed. Official boxscores and scoring summaries refreshed through
October 15: 118 season games. All frozen daily trials re-evaluated using those
actuals, preserving prior evaluations and predictions.

Source corrections since October 14: October 13 shots changed for Zach Benson
1→0, Dylan Cozens 1→2, Brady Skjei 2→3. Covered actual SOG becomes 863 instead
of 862; baseline MAE becomes 1.015. Earlier readouts remain archived snapshots.

Published two charts, all-team defense proxies and player/team SOG contribution
tables. Biggest mean absolute forecast movement in the scored October 10/12
usage trial comes from calibration (0.120 SOG), recent shot rate (0.111), matchup
(0.068), then TOI (0.036). These are sequential accounting effects, not causal
importance or independently validated feature gains. Signed realized player
error changes are included. Rest, PP/EV context and ESPN benchmarks currently
have no fitted forecast effect. Candidate remains the leading overall SOG
challenger; preserve default and the fantasy subgroup comparison.

`src/fantasy/diagnostics.py` now computes date-exclusive D shots/game, team shot
share, assist credits/game and shots/60 summed D-player minutes. Future daily
builds save `defense_opportunity_context.csv`; no D coefficient is fitted or
applied yet. This is direct defensemen production, not measured chance creation
or pair effects. Next, acquire NHL play-by-play for D attempts, strength-specific
exposure and D-involved sequences leading to shots/chances. Define distinct
opportunities explicitly before modeling them; use past-only shrinkage and
future-game D-only ablations alongside TOI-only/rate-only/context-only trials.

Postgame automation: `scripts/update_weekly_review.py` runs official acquisition,
scoring validation, re-evaluation of specified frozen bundles, tables and charts
in one command. It stops on errors and requires a new output directory. Example:

```sh
rink-lab.venv/bin/python scripts/update_weekly_review.py \
  --start 2026-10-12 --end 2026-10-15 \
  --baseline data/processed/forecasts/per_game_20262027_20261009T195052Z \
  --evaluations \
    data/processed/forecasts/daily_evaluation_2026-10-10_20261016T172526291855Z \
    data/processed/forecasts/daily_evaluation_2026-10-12_20261016T172526055112Z \
  --out outputs/per_game_forecast/week_2026-10-12_next_refresh
```

Priorities: (1) finish fresh, complete pregame issuance and date-aware finalizer;
(2) define/acquire stronger D opportunity measures; (3) freeze component ablations
on unseen games with game-cluster uncertainty and role/fantasy checks; (4) add
scheduled execution, retries, freshness gates and alerts once the runner is
credential-free and reliable. No unattended schedule is enabled in this update.

## October 13 review completed — 2026-10-14

Read [October 13 results and recommendations](outputs/per_game_forecast/2026-10-13_results_readout.md).
All 16 final games, scoring summaries and goalie actuals are acquired. The
October 13 daily run was never issued in this workspace: only the default
forecasts saved October 9 cover this date. No challenger, goalie or team
simulation was recreated after results. Keep these aged baseline results
separate from the October 10/12 five-model prospective comparison.

Coverage: 575 positive-TOI skater appearances, 558 covered, 17 missing and one
additional zero-TOI boxscore row. All nine conditional means are present for
covered appearances. Default SOG MAE 1.0135; predicted 896.51 versus 862 actual.
Goals 99.46/109, assists 166.07/192, PPP 58.26/59. Defensemen account for 31.26
of the 34.51 excess predicted shots; forwards are close in aggregate. Treat
position/role differences as a new hypothesis, not fitted correction factors.
Saved fantasy cohort: 105 appearances, SOG MAE 1.2575; Quinn's 17 players total
39.36 predicted/33 actual. Saved ownership and injuries are from October 9.

Earlier prospective trial evidence is now pooled: 13 October 10/12 games,
468 matched skater appearances, 26 team observations and 96 fantasy appearances.
Candidate/default shot MAE 1.0445/1.0646; team MAE 3.4791/4.0672. Candidate
improves 11/13 games; paired game-bootstrap delta -0.0201, exploratory 95%
interval [-0.0314, -0.0086]. Default retains a small fantasy MAE edge
(1.3108/1.3253); that difference is uncertain. Usage improves TOI MAE from
2.2681 to 2.1078. Opponent-only adds no clear benefit. Across 26 goalie starts,
opponent saves MAE 3.949 versus baseline 4.188, but GA MAE worsens 1.231 to
1.264. October 13 has 32 starter/34 active goalie actuals but no forecasts.

Next session, in order:

1. Finish the standalone MoneyPuck acquisition and date-aware finalizer, then
   orchestrate refresh, skaters, goalies, finalization and coverage checks in one
   command. Require/record injury freshness, actual source cutoff and all game
   IDs. Set the next target date explicitly; the October 13 commands below are
   archived templates and must not be reused as a purported pregame issuance.
2. Use official rosters plus recent participants and flagged position priors to
   address the missing-player audit. Keep participation separate from conditional
   rates; do not sum every ESPN-pool player as a playing lineup.
3. Keep default as the baseline and candidate as the leading all-player/team
   challenger. No new blanket shot cut or stronger opponent factor. Isolate
   TOI-only, shot-rate-only and context-only variants on future unseen games;
   test EV/PP exposure and position/role calibration with shrinkage.
4. Improve goalie starter and duration modeling. Keep full-start forecasts,
   actual starts, relief and empty-net time distinct. Validate shot-volume and
   GA effects separately rather than promoting the entire goalie trial.
5. Continue paired chronological evaluations with MAE, RMSE, bias, game-cluster
   uncertainty and discrete probability calibration. Player shot intervals
   currently cover 92–93%; discreteness prevents interpreting this alone as
   proof of excessive dispersion. October 13 exact-count accuracy is unavailable
   because no saved integer guesses were issued.

Readout generator: `scripts/write_october_13_review.py`; artifact bundle:
`data/processed/forecasts/october_13_review_20261014T135613Z/`.
NHL actuals: `data/processed/forecasts/fantasy_game_details_20261014T135057Z/`.
Team sums in this review condition on actual participants and are diagnostics,
not frozen pregame team forecasts. Forecast data/settings were preserved.

## Archived plan: October 13 Frozen Frenzy projections (not executed)

**Paused before issuance at the owner's request. No October 13 projections or
input refreshes were run as part of this handoff.** Confirm the official NHL
October 13 schedule and earliest start when resuming; do not assume a game count
or that every game starts in the evening. Use NHL game dates across midnight UTC.

### Findings to carry forward

- Read [October 12 results](outputs/per_game_forecast/2026-10-12_results_readout.md)
  and [October 10/11 review](outputs/per_game_forecast/recent_results_2026-10-12.md).
  October 12's prospective sample is only two games: candidate SOG MAE 1.006
  versus default 1.055 per player, and 3.611 versus 5.805 per team. All models
  missed the exact team SOG count in all four team observations.
- Keep **default as baseline**, candidate as the leading all-player/team SOG
  challenger, and all five existing skater models for comparison. On 96 combined
  October 10/12 fantasy-player appearances, default still leads candidate
  (SOG MAE 1.311 versus 1.325). Do not apply another blanket shot reduction or
  increase opponent-factor strength based on these outcomes.
- Usage improved October 12 TOI MAE from 2.278 to 2.066 minutes, but its shot
  forecasts did not beat candidate. Later isolate TOI-only, rate-only and
  context-only changes, plus position/PP-role calibration, on future holdouts.
  Fantasy ownership is an evaluation subgroup, not a hockey skill feature.
- Keep both goalie models. Opponent context improved saves MAE from 5.076 to
  4.041 on four starters, but worsened GA error. Start shares are provisional;
  full-60-minute forecasts do not model pulls/empty-net time. Evaluate goalie
  outcomes separately from team totals.
- The immediate problem is input freshness and lineup assumptions: October 12
  injuries were about 50 hours old and MoneyPuck lacked recent games. All 72
  evening skater appearances had forecasts, but assumed named lineups matched
  only 70. Refresh inputs before drawing conclusions about stronger adjustments.
  NHL fitting history ended October 11; no October 12 outcomes entered fitting.

### Ordered checklist for the next session

1. **Finish small release prerequisites first.** Extract the existing MoneyPuck
   download logic in `scripts/evaluate_october_9.py` into a standalone acquisition
   command; do not run the old evaluation merely to download data. Save a new
   immutable snapshot with URL, retrieval timestamp and hash. Generalize
   `scripts/finalize_daily_bundle.py`: its date, game counts, history counts and
   Montreal/Philadelphia replacement text still describe October 10. Derive
   them from the new manifest/coverage tables. Run the relevant tests after fixes.
2. **Refresh availability and statistical inputs.** Run the commands below in
   order, recording each printed output path. Refresh ESPN injuries/ownership
   close to issuance and check lineup/starter information. Acquire every final
   game through October 12, complete fantasy/goalie scoring details, and refresh
   EV/PP/SH TOI and the ESPN projection benchmark. The history script supports
   `--reuse`, but a full fetch also picks up source corrections. Never edit raw
   snapshots manually or substitute current season totals containing target-day
   results for cutoff-safe game history.
3. **Refresh and validate MoneyPuck separately.** The official source already
   used is `https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv`.
   Inspect each team's latest eligible game, paired rows, missingness and NHL
   shot-count disagreements; retain the existing quarantine/neutral-fallback
   flags. A new download timestamp alone does not establish current coverage.
   If publication lags, document the actual cutoff and affected teams. Do not
   silently reuse `team_games_20261010T201108Z` as a fresh input.
4. **Build and finalize together, before puck drop.** Use the existing frozen
   model settings in `config/daily_forecast_trial.json` and the commands below.
   Build all five skater models and both goalie models, then finalize the three
   reader tables. Do not refit or promote a model while issuing this comparison.
5. **Check the release.** Match every official scheduled game ID and both teams;
   inspect missing players, fallback/replacement labels, injury exclusions and
   provisional starter shares. Check duplicate IDs, missing means, all model
   populations, goalie SA = saves + GA, and team SF = opponent SA. Confirm
   statistical inputs are strictly before October 13, injury timestamps are
   current, and every claimed pregame forecast was actually issued before that
   game's start. Keep already-started games explicitly late. Record source
   hashes, leave outcomes blank, and preserve the final issued bundle unchanged.
6. **Publish the local handoff.** Link `player_projections.csv`,
   `team_projections.csv`, `goalie_projections.csv` and the dated readout from
   `outputs/per_game_forecast/README.md`; document any source lag. Keep generated
   datasets local under the existing ignore rules. Update this checklist with
   actual issuance time, paths and coverage once the run is complete.

Commands for later, from repository root. Set the uppercase path variables to
the outputs of the preceding steps; these are templates, not an unattended
runner. `MONEYPUCK_SNAPSHOT` requires the standalone refresh step above.

```sh
rink-lab.venv/bin/python scripts/refresh_forecast_inputs.py --seasons 20262027
rink-lab.venv/bin/python scripts/acquire_current_game_history.py --through 2026-10-12
# Set BOXSCORE_HISTORY to the newly printed raw history directory.
rink-lab.venv/bin/python scripts/complete_fantasy_game_stats.py \
  --boxscore-snapshots "${BOXSCORE_HISTORY:?set refreshed raw history path}"
# Set GAME_HISTORY to the newly printed enriched fantasy history directory.
rink-lab.venv/bin/python scripts/acquire_game_toi.py --before 2026-10-13 \
  --season 20262027 --boxscore-snapshot "$BOXSCORE_HISTORY"
# Set GAME_TOI to the new player_game_toi.csv; ESPN_SNAPSHOT to fresh ESPN raw data.
rink-lab.venv/bin/python scripts/export_espn_projection_benchmark.py \
  --espn-snapshot "${ESPN_SNAPSHOT:?set refreshed ESPN path}" \
  --out "${ESPN_BENCHMARK:?set a new processed benchmark CSV path}"

rink-lab.venv/bin/python scripts/build_daily_forecasts.py --date 2026-10-13 \
  --template-forecast data/processed/forecasts/per_game_20262027_20261009T195052Z \
  --game-history "${GAME_HISTORY:?set enriched history path}" \
  --boxscore-history "$BOXSCORE_HISTORY" \
  --moneypuck-snapshot "${MONEYPUCK_SNAPSHOT:?set refreshed MoneyPuck path}" \
  --game-toi "${GAME_TOI:?set refreshed TOI CSV path}" \
  --espn-benchmark "$ESPN_BENCHMARK"
# Set DAILY_BUNDLE to the newly printed daily_2026-10-13_* directory.
rink-lab.venv/bin/python scripts/build_goalie_game_forecasts.py \
  --simulation "${DAILY_BUNDLE:?set new daily bundle path}" \
  --injury-context "$DAILY_BUNDLE/inputs/pregame_injury_context.csv" \
  --game-history "$GAME_HISTORY" --boxscore-history "$BOXSCORE_HISTORY" \
  --output-root "$DAILY_BUNDLE/inputs"
# Set GOALIE_BUNDLE to that command's output; fix finalizer wording before use.
rink-lab.venv/bin/python scripts/finalize_daily_bundle.py \
  --bundle "$DAILY_BUNDLE" --goalies "${GOALIE_BUNDLE:?set new goalie bundle path}"
```

After games finish, acquire final boxscores/fantasy details and use
`scripts/evaluate_daily_forecasts.py --bundle <issued-bundle> --actuals
<enriched-actuals> --boxscores <raw-boxscores>` to create a separate evaluation.
The evaluator now supports missing wide views and an explicit `--goalie-source`
for separately issued goalies, without rewriting frozen forecasts. Generalize
the October 12-specific narrative in `scripts/write_daily_evaluation_readout.py`
before reusing it for a later date. Compare common positive-TOI appearances,
fantasy subsets and goalie starters separately; report pregame-only headline
errors, bias, count accuracy and interval coverage with game-level uncertainty.

Resume prompt: **“Run the October 13 Frozen Frenzy checklist in NEXT_STEPS;
refresh inputs, freeze all games before their starts, finalize all five skater
and both goalie models, and link the player/team/goalie projections.”**

## October 12 night evaluation — 2026-10-13

Read `outputs/per_game_forecast/2026-10-12_results_readout.md`. Discovered and
verified the subsequently issued skater run `daily_2026-10-12_20261012T225309Z`
and separate goalie run `goalies_2026-10-12_20261012T225455Z`. Both preceded the
two evening games. Florida–Buffalo was already final and remains a late-only
diagnostic. This supersedes the earlier review's statement that no new October
12 run had yet been issued.

Primary sample: 72/72 skater appearances, four teams, four goalies. SOG MAE:
default 1.0554, candidate 1.0061, opponent 1.0643, combined 1.0128, usage 1.0281.
Team SOG MAE: 5.8045, 3.6113, 6.2190, 4.0605, 4.3153 respectively. Candidate
also wins the 18 fantasy-rostered appearances (0.9547 vs default 1.0273), but
default remains slightly better over the combined 96 October 10/12 fantasy
appearances (1.3108 vs 1.3253). Continue comparison; no promotion from two games.
Usage TOI MAE improves 2.278 to 2.066 minutes. Goalies: opponent saves MAE
4.041 vs baseline 5.076, but GA error slightly worse. Four starts are too few
to validate an across-the-board goalie change.

Evaluation output: `data/processed/forecasts/daily_evaluation_2026-10-12_20261013T125524789050Z/`.
Wide tables derived from frozen long tables because the original bundle was
not finalized. Evaluator now accepts explicit `--goalie-source` and supports
missing wide views or absent goalie forecasts without inventing projections.
All recorded source hashes verified. Original forecasts remain immutable.

Input problem: injuries were from October 10 (~50 hours old); MoneyPuck also
lacked the more recent updates. Before another daily issuance, refresh these
sources and enforce/document freshness, confirm available lineup/starter info,
and finalize the skater/goalie bundle together. Statistical inputs themselves
ended October 11 and contained no target-day outcomes. Named lineup overlap
was 70/72. Readout generator: `scripts/write_daily_evaluation_readout.py`.

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
