# ELWAY-Inspired Rink Lab Modeling Plan

Status: **implementation roadmap**  
Target season: **2026-27**  
Prepared: **2026-10-03**

## Purpose

Adapt the most useful modeling ideas from Nate Silver and Joseph George's 2026 ELWAY NFL forecast to Rink Lab without copying NFL-specific assumptions.

The goal is not to create a single opaque player score. The goal is to improve Rink Lab's ability to separate repeatable hockey skill from noisy outcomes, translate that into league-specific fantasy value, and eventually make roster decisions under uncertainty.

This plan should be read alongside:

- `docs/FANTASY_DRAFT_STRATEGY.md`
- `docs/FANTASY_VARIABLE_DICTIONARY.md`
- `docs/EXPECTED_OPPORTUNITY.md`
- `NEXT_STEPS.md`
- `config/fantasy_league.micro.yml`

## Current starting point

Rink Lab already has:

- validated 2025-26 NHL skater summary and TOI data;
- fantasy-category acquisition for skaters and goalies;
- league settings captured for the ESPN Micro League;
- a fantasy decision specification emphasizing opportunity, event rates, uncertainty, replacement value, and market context;
- no fitted multi-season fantasy forecast yet;
- no production ESPN Fantasy integration yet.

The current fantasy work is therefore a strong design specification, but the forecast, backtest, replacement-value engine, and live league-state layer still need to be implemented.

---

# Guiding principles adapted from ELWAY

## 1. Predict the process, not just the observed outcome

Goals, assists, wins, save percentage, and fantasy category totals are outcomes. Rink Lab should increasingly model the underlying processes that generate them.

For skaters, prioritize repeatable opportunity and event-generation variables such as:

- expected games played;
- EV, PP, and SH TOI;
- PP1/PP2 role probability;
- shot attempts and shots on goal;
- individual expected goals or shot quality when validated;
- primary assist / chance-creation signals when available;
- team offensive environment;
- hits, blocks, and PIM as their own action processes.

For goalies, model:

- probability of starting;
- expected starts;
- shots against;
- saves and goals allowed;
- team win support;
- role/tandem uncertainty.

Actual fantasy categories remain the prediction targets, but the model should prefer repeatable inputs over noisy realized results when those inputs validate better out of sample.

## 2. Shrink noisy rates toward appropriate baselines

High-impact events can still be poor predictors when they occur infrequently or fluctuate heavily.

Candidate variables for explicit shrinkage include:

- shooting percentage;
- secondary-assist rate;
- on-ice shooting percentage;
- short-handed scoring;
- power-play conversion rates;
- goalie save percentage in small samples;
- shutouts;
- plus/minus;
- unusually high or low team finishing rates.

Shrinkage strength should depend on exposure and historical reliability rather than a universal rule.

Deliverable: every fitted event-rate model should report how much observed performance is retained versus regressed toward a prior or league/position baseline.

## 3. Separate baseline talent from current context

Create distinct player views rather than one mutable ranking.

### A. Underlying projection

Best estimate of repeatable player ability based on historical performance, age, usage, and shrinkage.

### B. Full-role projection

Underlying projection assuming the player's expected normal/healthy NHL role.

### C. Current-context projection

Full-role projection adjusted for current team, line, PP unit, injury/availability, schedule, and role uncertainty.

### D. Fantasy-league value

Current-context projection translated through the exact ESPN league categories, roster constraints, replacement level, and available-player pool.

This structure should make it obvious whether a player's value changed because the model learned something about talent or because the player's opportunity changed.

## 4. Use value above replacement rather than raw projected production

Create a Fantasy Value Above Replacement metric (`FVAR`) after the underlying category projections are trustworthy.

Conceptually:

`FVAR = projected fantasy contribution - best feasible replacement contribution`

Replacement must be league-specific and roster-aware.

For this league, replacement should account for:

- six teams;
- 9 F, 5 D, 1 UTIL, and 2 G active slots;
- five bench spots;
- maximum four rostered goalies;
- daily lineup changes;
- seven acquisitions per matchup;
- ESPN position eligibility;
- the actual available-player pool.

Do not use a fixed percentile of all NHL players as the final replacement definition. A percentile can be a temporary baseline, but the eventual replacement frontier should reflect feasible roster construction and waiver availability.

## 5. Keep important component ratings visible

Do not collapse all information into one unexplained Rink score.

Recommended player-level output columns:

- projected category totals;
- projected category rates;
- expected GP / starts;
- expected TOI / PP TOI;
- underlying talent estimate;
- current-role adjustment;
- sustainability / regression flag;
- availability risk;
- FVAR;
- positional scarcity;
- current-roster marginal value;
- uncertainty interval;
- evidence/data-quality flag.

A composite rank or tier can exist for convenience, but the components must remain inspectable.

## 6. Simulate dynamic fantasy outcomes eventually

The long-term system should simulate future games/weeks rather than assume one fixed season projection.

Within each simulation branch, allow events such as:

- missed games / injury absences;
- role expansion or contraction;
- PP1/PP2 changes;
- goalie starter/tandem changes;
- roster transactions;
- schedule density and lineup congestion;
- replacement-player production while a rostered player is unavailable.

This is a later-stage feature. Do not build the simulation layer before simpler baselines validate out of sample.

---

# Workstream A — ESPN Fantasy connection

## Why it is still needed

Yes: the ESPN connection still needs to be built.

The repo currently has ESPN league settings captured manually, but ESPN eligibility and live league state are still treated as separate inputs. The current Python dependency file also does not include a dedicated ESPN Fantasy client.

Because the draft has already occurred, the ESPN connection is now most valuable for **in-season roster management**, not just draft preparation.

## What the ESPN connection should provide

Minimum useful scope:

1. League metadata
   - league ID / season ID;
   - teams and team IDs;
   - scoring settings when available;
   - roster rules;
   - matchup periods.

2. Current roster state
   - user's roster;
   - opponent rosters;
   - lineup slots;
   - bench / IR state;
   - player fantasy eligibility.

3. Player pool
   - free agents / waiver players;
   - rostered vs available status;
   - ESPN player IDs;
   - fantasy position eligibility.

4. Matchup state
   - current category totals;
   - remaining scheduled games;
   - category deficits / surpluses;
   - transaction limit remaining.

5. Transactions / market context when accessible
   - recent adds/drops;
   - waiver status;
   - ownership / roster percentage if available;
   - acquisition timestamps.

## Authentication and security requirements

The league is private, so the integration may require authenticated ESPN session information.

Rules:

- never commit ESPN cookies, session tokens, `espn_s2`, `SWID`, passwords, or other credentials;
- store credentials only in local environment variables or another ignored local secret file;
- document required environment-variable names in an example file without values;
- fail clearly when credentials are unavailable rather than silently returning an empty league.

## Proposed files

Future implementation may use:

- `src/fantasy/espn_client.py` — authenticated ESPN retrieval wrapper;
- `src/fantasy/espn_normalize.py` — normalize ESPN IDs/positions/rosters;
- `config/espn.example.yml` — non-secret league metadata only;
- `data/raw/espn/snapshots/` — timestamped generated snapshots, Git-ignored;
- `docs/ESPN_FANTASY_CONNECTION.md` — setup, authentication, fields, and validation;
- tests for roster counts, player IDs, duplicate players, and eligibility parsing.

Python is a good fit for this integration because the repo already reserves Python for pipelines and reusable predictive tooling.

## ESPN validation gates

Before using ESPN data in recommendations:

- team count matches the league configuration;
- roster size and lineup-slot counts reconcile;
- each rostered fantasy player has a stable ESPN ID;
- NHL-player crosswalk coverage is reported;
- duplicate roster assignments are rejected;
- position eligibility is preserved exactly as ESPN reports it;
- unavailable or unknown fields remain explicit rather than being inferred;
- snapshot retrieval timestamp is saved.

## ESPN dependency on other work

The ESPN connection should be built **in parallel** with the hockey projection work.

It is required for:

- live roster-aware recommendations;
- waiver comparisons;
- true position eligibility;
- current matchup optimization;
- acquisition-limit-aware streaming decisions;
- actual league replacement value.

It is **not required** to begin:

- multi-season NHL data acquisition;
- shrinkage research;
- event-rate forecasting;
- held-out model evaluation;
- underlying talent estimation.

---

# Workstream B — Multi-season modeling panel

## Goal

Create the historical panel needed to evaluate whether ELWAY-style signal extraction actually improves prediction.

## Required seasons

Use multiple completed seasons, with at least one full held-out target season.

For each target season, features must be constructed only from information available before that target period.

## Minimum skater inputs

- NHL player ID;
- age / experience;
- team and position;
- GP;
- TOI and TOI/game;
- EV/PP/SH TOI if available;
- G, A, SOG;
- PPP;
- HIT;
- PIM;
- plus/minus if modeled;
- historical shooting percentage;
- team offensive context.

Later additions can include xG, shot attempts, primary/secondary assists, line/pair context, and NHL EDGE variables only after the baseline is established.

## Minimum goalie inputs

Keep goalies separate from skaters.

- starts and appearances;
- TOI;
- shots against;
- saves;
- goals against;
- wins;
- SV%;
- GAA;
- team context.

First resolve the current goalie validation exceptions before using goalie data for model fitting.

---

# Workstream C — Projection baselines

## Baseline 1: naive historical production

For each category, compare against simple benchmarks such as:

- prior-season total;
- prior-season per-game rate × conservative GP projection;
- multi-season exposure-weighted rate × projected GP.

## Baseline 2: shrunken event rates

Estimate category-specific rates with exposure-aware regression toward appropriate priors.

Examples:

- SOG/60 should require less shrinkage than shooting percentage;
- shooting percentage should receive stronger shrinkage at low shot volumes;
- goalie SV% should depend heavily on shot volume and multi-season history;
- secondary assists should be treated more cautiously than primary creation metrics if the data support that distinction.

## Baseline 3: opportunity × rate

Estimate:

`Projected event count = expected opportunity × expected event rate`

Where opportunity may include:

- probability of playing;
- expected games;
- expected TOI;
- expected PP TOI;
- expected goalie starts.

This should become the core interpretable projection architecture.

## Evaluation

Use held-out seasons and report:

- MAE;
- bias;
- calibration where probabilistic forecasts exist;
- performance by position;
- performance by experience / sample size;
- performance for role changers and traded players;
- performance relative to simple baselines.

Do not advance to a more complex model unless it materially improves held-out performance or adds decision-useful uncertainty.

---

# Workstream D — Sustainability and regression signals

Create a separate diagnostic layer rather than embedding all regression effects invisibly in the rank.

Potential labels:

- `sustainability_signal = stable / mild_regression / strong_regression / insufficient_data`
- `role_signal = expanding / stable / contracting / uncertain`
- `availability_signal = low / moderate / high uncertainty`

Examples of possible regression flags:

- shooting percentage far above multi-season expectation;
- point totals driven disproportionately by secondary assists;
- very high on-ice shooting percentage;
- unusually high PP scoring rate without corresponding PP opportunity;
- goalie SV% unsupported by longer-run shot-stopping history.

All thresholds should eventually be derived from historical predictive performance rather than hand-set permanently.

---

# Workstream E — FVAR and replacement value

Do this only after league-category projections and ESPN eligibility are reliable.

## Stage 1: transparent approximation

Estimate replacement pools by eligible roster role:

- F;
- D;
- G;
- UTIL-compatible players.

Use the league's roster depth and current available pool to define a provisional replacement frontier.

## Stage 2: feasible replacement

Build a lineup-aware replacement calculation that considers:

- multi-position eligibility;
- daily schedules;
- overlapping game times;
- bench capacity;
- goalie roster cap;
- available free agents;
- transaction limits.

## Stage 3: current-roster marginal value

Calculate value relative to **this team's** roster, not just league-average replacement.

A player can have positive league FVAR but little marginal value if the roster already dominates the categories he improves or cannot start his games efficiently.

---

# Workstream F — In-season decision engine

Once ESPN ingestion, projections, and replacement value exist, Rink Lab can answer practical questions such as:

- Who is the best add for the next matchup?
- Is a free agent actually better than the player I would drop?
- Which category is most realistically swingable this week?
- Is a goalie stream worth using one of the seven acquisitions?
- Which available player creates the most expected category win probability?
- Should a player be benched because of schedule congestion?

The recommendation layer should show its components rather than only output a name.

Recommended output:

- candidate player;
- player to drop, if applicable;
- projected category deltas;
- games/start opportunity;
- FVAR change;
- matchup win-probability change when supported;
- acquisition cost / remaining moves;
- role and injury uncertainty;
- explanation.

---

# Workstream G — Simulation layer

Add only after the deterministic and probabilistic baselines are validated.

## Weekly simulation

Simulate:

- player availability;
- games played;
- TOI / starts;
- category outcomes;
- lineup feasibility;
- opponent production;
- roster substitutions.

Output category win probabilities for a matchup.

## Season simulation

Eventually simulate:

- weekly matchups;
- injuries / missed time;
- changing roles;
- goalie tandems;
- acquisitions;
- playoff qualification and playoff matchups.

Do not let simulated future results recursively change a player's intrinsic talent estimate without an explicit modeled reason. Role and availability can change dynamically; underlying talent should update only when new performance information is introduced.

---

# Recommended implementation order

## Milestone 1 — ESPN read-only connection

- [ ] Build authenticated read-only ESPN retrieval.
- [ ] Save a timestamped league snapshot locally.
- [ ] Validate six teams and roster counts.
- [ ] Pull the user's current roster and free-agent pool.
- [ ] Preserve ESPN eligibility.
- [ ] Create ESPN-to-NHL player-ID crosswalk coverage report.
- [ ] Document credentials and setup without committing secrets.

**Acceptance criterion:** Rink Lab can reproducibly identify who is on each team, who is available, and each player's ESPN eligibility from a timestamped snapshot.

## Milestone 2 — Multi-season skater baseline

- [ ] Acquire multiple historical seasons.
- [ ] Predefine training/validation/test seasons.
- [ ] Build naive prior-season baseline.
- [ ] Build multi-season exposure-weighted baseline.
- [ ] Add shrinkage.
- [ ] Compare held-out G, A, SOG and GP forecasts.

**Acceptance criterion:** at least one shrunken or multi-season baseline is compared honestly with naive alternatives on a held-out season.

## Milestone 3 — Opportunity model

- [ ] Forecast GP.
- [ ] Forecast TOI and PP opportunity.
- [ ] Separate talent rate from opportunity.
- [ ] Evaluate whether opportunity × rate improves held-out category forecasts.

**Acceptance criterion:** Rink Lab can explain whether a forecast moved because of skill/rate or expected opportunity.

## Milestone 4 — Complete league categories and goalies

- [ ] Resolve goalie validation exceptions.
- [ ] Add goalie projection baseline.
- [ ] Add HIT, PIM, PPP, +/-, and ATOI handling.
- [ ] Verify exact ESPN ATOI aggregation and category directions.

**Acceptance criterion:** every scored league category has a documented, validated calculation path or an explicit unsupported status.

## Milestone 5 — FVAR

- [ ] Build provisional replacement values.
- [ ] Use ESPN available-player pool and eligibility.
- [ ] Add schedule and lineup feasibility.
- [ ] Calculate current-roster marginal value.

**Acceptance criterion:** player value can differ correctly from raw fantasy production because replacement scarcity is incorporated.

## Milestone 6 — Weekly matchup optimizer

- [ ] Project next-week category totals.
- [ ] Incorporate opponent roster.
- [ ] Incorporate remaining acquisition limit.
- [ ] Rank candidate add/drop moves by marginal matchup value.
- [ ] Display uncertainty and reasons.

**Acceptance criterion:** recommendations can be traced from source data → projection → replacement/roster effect → matchup effect.

## Milestone 7 — Dynamic simulations

- [ ] Add correlated outcome simulations.
- [ ] Add role and availability scenarios.
- [ ] Validate interval coverage.
- [ ] Add season/playoff simulation only if weekly simulation is trustworthy.

---

# Near-term priority

The next two tracks should proceed in parallel:

1. **ESPN integration for live league state** — because the league is now active and this unlocks roster, waiver, eligibility, and matchup-aware analysis.
2. **Multi-season baseline modeling** — because live ESPN data alone cannot tell us which NHL performance signals are actually predictive.

Do not pause the modeling work while waiting for a perfect ESPN integration, and do not build live recommendations that simply repackage current fantasy points without a validated projection layer.

# Conceptual source

This roadmap adapts modeling ideas discussed in Nate Silver and Joseph George's 2026 description of the ELWAY NFL forecasting system, especially its separation of underlying team/player quality from current adjustments, shrinkage of noisy events, value-above-replacement thinking, and dynamic simulation philosophy. The hockey implementation must be validated independently using NHL and fantasy-hockey data.