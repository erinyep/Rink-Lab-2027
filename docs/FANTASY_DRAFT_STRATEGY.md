# Fantasy Hockey Draft Lab — modeling and draft strategy

Status: **design specification, not a fitted model or player ranking**  
Target season: 2026–27 | Prepared: 2026-09-28

## Objective

Make a draft pick that maximizes expected **incremental fantasy roster value**, rather than selecting the NHL skater with the most projected points. A player can have strong intrinsic production yet be a poor pick if an almost equivalent replacement will be available several rounds later. Conversely, a defenseman or peripheral-category contributor may be valuable despite lower point totals.

Rink Lab's research into player talent and predictive value remains independent of fantasy scoring. The fantasy layer translates projected hockey outcomes into league-specific decisions. Keep observed facts, modeled projections, and draft preferences separate and traceable.

The current repo contains 2025–26 skater summary and time-on-ice descriptive research. Its validated population is 940 unique skaters, but that **does not establish a 2026–27 forecast**. Before building a board, acquire multiple seasons of game/strength-level information, relevant current/as-of context, fantasy league settings, platform eligibility, goalie data, and ADP. See NEXT_STEPS.md, docs/EXPECTED_OPPORTUNITY.md, and outputs/descriptive_2025_26/README.md.

## 1. Decision pipeline

1. **Data and as-of snapshot:** player IDs, past games/TOI/events, team/roster history, fantasy eligibility, schedule, injury/role observations, ADP. Record source, timestamp, game type, units and quality checks.
2. **Opportunity:** probability of playing each game; conditional even-strength, power-play and shorthanded minutes; PP1/PP2 and lineup role probabilities.
3. **Event rates:** separate conditional rates for G, A, shots, PPP, hits, blocks, PIM, faceoffs and other *scored* statistics. Estimate uncertainty and regression to the mean.
4. **Season/weekly joint forecasts:** sum events across probable appearances and strength states; simulate correlated outcomes and role scenarios.
5. **Fantasy translation:** actual league scoring rules, category directions, goalie start minima, lineup caps and ratio aggregation.
6. **Scarcity and replacement:** marginal gain over a feasible C/LW/RW/D/G/UTIL replacement, with multi-position eligibility and available waiver talent.
7. **Market and pick decision:** ADP distribution, likely next-pick availability, opponent drafting, existing roster strengths, trade-offs and personal risk preference.
8. **Output:** tiered draft board with projected categories, upside/downside, role risk, positional cliffs, ADP gap, next-pick availability and plain-English reasons. Recalculate during the draft.

Do not merge these layers into an unexplained universal composite rating. Each intermediate table and each final rationale should make its assumptions auditable.

## 2. Opportunity is the denominator of value

For player i and future game g, project appearance probability a_ig. Given appearance, project minutes m_igs for strength state s. Baseline projected count for event k:

    E[Y_ik] = sum_g sum_s a_ig * E[m_igs | plays] * r_iks / 60

Here r_iks is an as-of estimate of events/60 for that state. This is an **interpretable baseline**: in a richer simulation, role, TOI and event rates are jointly sampled rather than assumed independent.

Distinguish team scheduled games from NHL games played; as-of team assignment from a player's end-of-season team; missing injury status from healthy; and scratches from missing boxscore data. Conditional total TOI must agree with the chosen mutually exclusive EV+PP+SH buckets; do not double-count OT. For season forecasts include remaining games as of the draft and account for projected missed games, rather than scaling a rate by 82 automatically.

Important inputs: lagged GP/team GP; healthy/eligible games observable at cutoff; rolling TOI; EV/PP/SH TOI shares; likely line/pair; PP1 vs PP2 probability; role persistence; coach/team usage; team shot environment; team PP opportunities; timestamped injury/transaction uncertainty. Exclude future lineup news when training past preseason cutoffs.

## 3. Predict events, not just points

### Skater production
- Goals: shots and shot attempts, individual xG/shot quality if reliably sourced, location, shot volume/60, shooting conversion, PP opportunities and expected minutes. Regress unusually high/low conversion toward context-appropriate priors; do not mistake all residual for luck.
- Assists: primary/secondary assist rates, individual and on-ice chance creation, teammate finishing, team style, PP deployment. Separate role effects from repeatable creation.
- Shots: shot generation rate times available ice time; role/lineup and team pace. Shots can provide a more stable fantasy floor than realized goals, subject to evaluation.
- Power-play points: modeled PP TOI, team power plays, unit/role probabilities and PP event rates; PPP is a subset of points and must not exceed P.
- Hits, blocks and PIM: distinct action-rate processes with position, usage and scorer/source effects. Do not infer these from scoring points. Consider short samples and recording inconsistencies.
- Faceoffs: attempts from center deployment/TOI, then win probability conditional on attempts. If league counts faceoff wins, wins cannot exceed attempts.
- Plus/minus or special categories: separate noisy/team-dependent outcome models if actually counted, with explicit limitations.

Estimate per-game, per-minute, and conditional event counts with exposure-weighted historical data, age/role adjustments and shrinkage for low exposure. Compare simple lagged baselines before adding xG, NHL EDGE or complex ML. If a source/metric is unavailable, omit or label its substitute rather than inventing it.

**Correlation matters:** goals and shots, PPP and points, TOI and blocked shots, G/A/PPP, and availability across categories move together. Report coherent joint outcome simulations; do not add independent z-score intervals or double-count P as a separate independent outcome when G and A already define it.

### Goalies are a separate population
Project probability of start per scheduled game, projected starts, team win support, shots against, saves, goals against, expected SV%, GAA, and shutout probability if counted. Track goalie tandem/role changes, back-to-backs, rest, current roster availability and start minimums. A goalie with strong SV% but few starts can have limited counting-category value. Compute roster SV% as total saves / total shots against; GAA as 60 × goals against / goalie minutes. Never average goalie percentages without denominator weighting.

## 4. Forecast uncertainty and scenarios

Return mean or median plus P10/P50/P90 from **joint** simulations, along with interpretable sensitivities to GP, PP1 assignment, TOI, rate regression and goalie starts. Sample realistic correlations where possible. An upside scenario should have a reason (e.g., added PP time and higher shots) rather than an arbitrary +15% bonus.

Candidate scenarios: missed time, stable role, expansion, lost PP unit, transition/new team, tandem-to-starter. Estimate their probabilities from historical evidence; when evidence is absent, label the probabilities subjective and show sensitivity. Avoid an arbitrary universal "injury-prone", "clutch", "breakout" or "risk" score. Keep risk appetite a **decision preference**, not disguised as a skill projection.

## 5. Fantasy translation, category leverage and replacement

**Points league:** forecast each scored event, multiply by the platform's exact rules, include bonuses/penalties, and apply position/roster constraints. A points total is only valid for that specific scoring system.

**Rotisserie/categories:** score the contribution to each category separately. An initial reference-standardized difference is (projected total - reference mean)/reference SD for higher-is-better categories. Select reference populations that reflect draftable players and roster needs, not 940 equally weighted NHL skaters. A z-score is a descriptive standardization, **not** a validated chance of winning.

**Weekly head-to-head:** better decision value is the change in the probability of winning each category after feasible starters and opposing team distributions are simulated. Marginal value can be nonlinear: ten extra hits might be decisive in a close matchup and useless in an already secure one. Do not declare category weights equal until the platform rules are known.

For ratio categories (SV%, GAA, shooting %, if counted), aggregate projected numerators/denominators at the **team** level and evaluate the *marginal* change from adding a player; individual percentage z-scores cannot simply be summed.

**Replacement level:** define the best feasible attainable alternative given league size, active position slots, bench, FLEX/UTIL, dual eligibility, games/start caps, waiver supply and schedule overlap. An approximate initial positional replacement cutoff is acceptable if explicitly labeled; later use a feasible-lineup optimizer. Treat the replacement frontier as roster-dependent. Position scarcity is about the alternatives that disappear before subsequent picks—not an automatic premium for any defenseman.

Outputs to distinguish:
- intrinsic projected fantasy contribution;
- contribution above league-level replacement (VORP-style);
- incremental **current-roster** utility;
- expected next-pick scarcity/opportunity cost;
- market surplus relative to acquisition price.

Don't treat a surplus in one category as globally valuable without examining team needs and the actual contest format.

## 6. ADP and draft economics

Bring in platform-specific ADP with retrieval date, format, pool, sample size and ideally the distribution of picks, not merely a single overall rank. ADP forecasts market behavior and availability; it is not hockey performance.

Track model rank, ADP, rank/pick gap and hypothetical next-pick availability separately. **Do not subtract ADP rank from category z-score**: those units are incomparable. Convert both to a common estimated utility/pick opportunity cost through simulations or keep them as two columns.

At pick t, compare drafting player i now against the best feasible combination of taking someone else now and potentially selecting i or another alternative next round. Initial transparent heuristic:

    pick_urgency(i,t) =
      marginal_roster_utility(i)
      × P(i unavailable at our next pick)
      + relative position/category cliff
      - foregone utility of other candidates now

This is a decision heuristic, not a fitted formula; calibrate or replace it through mock drafts. Expected availability comes from historical drafts/ADP uncertainty and should be stress-tested, especially in small samples. A high intrinsic player may be worth waiting for if survival is plausible, but never assume certainty.

During the draft, remove drafted players, update eligibility and roster needs, estimate feasible starter games, recompute replacement and remaining category variance, and compare candidate-specific next-pick alternatives. Display **draft now**, **likely wait**, **category/position fit**, and **evidence quality** as explanation fields rather than an unexplained one-number recommendation.

## 7. Schedule, bench and postseason optimization

Season-long production and realized starts are different. Include games by scoring week, off-night frequency, lineup-slot overlap, maximum games/starts, bench capacity and streaming flexibility. A sixth forward's projected points are less useful if many games are blocked by fully occupied lineups. For H2H playoffs, track exact weeks and known team games; evaluate whether those weeks deserve additional emphasis based on actual league rules and advancement objective. Schedule-only games played is not a skill variable.

## 8. Model evaluation (before trusting rankings)

Use rolling historical preseason/as-of cutoffs and only facts available at each cutoff. Hold out entire later seasons and prevent the same target games from leaking across train/test windows. Compare the following **in order**:

1. Last-season totals and rate × conservative GP baseline.
2. Multi-season/shrunk event rates plus forecast GP.
3. Strength-state TOI/role model.
4. Additional shot-quality, chance and teammate features.
5. Correlated outcome scenarios.
6. League/category/ratio translation and positional replacement.
7. ADP-aware and roster-aware recommendations.

Measure GP/TOI MAE and bias, probabilistic coverage, event MAE/deviance/calibration, count/rate identities, category-total calibration and rank/tier stability. Critically, test whether each layer improves **out-of-sample fantasy decision value**, not merely NHL points RMSE. Compare repeated simulated/mock drafts using identical draft scenarios; evaluate roster feasibility and category outcomes. Report by position, exposure, age/experience, role stability, traded players and goalie tandem. Maintain fallback behavior and missingness diagnostics.

## 9. Proposed repo structure and gates

The existing validated data and research scripts remain unchanged.

| Proposed path | Purpose |
|---|---|
| docs/FANTASY_DRAFT_STRATEGY.md | This methodological and decision specification |
| docs/FANTASY_VARIABLE_DICTIONARY.md | Feature/target definitions and validation |
| config/fantasy_league.example.yml | Explicit yet unfilled league configuration |
| R/analysis/05_fantasy_projection_baseline.R | Future interpretable backtested skater baseline |
| src/fantasy/ | Future utilities and pick/lineup optimizer if justified |
| data/processed/fantasy/ | Generated joined feature/forecast tables |
| outputs/fantasy_2026_27/ | Generated draft board, scenario results, model card |

**Gate A — league rules:** obtain format, categories/weights, teams, slots, eligibility, limits, draft order and playoffs. **Gate B — data:** source historical game/strength data, player positions and as-of roster/injuries, goalie stats and draft ADP. Validate IDs/coverage/timestamps. **Gate C — forecasts:** build and backtest transparent opportunity × rate baselines. **Gate D — fantasy valuation:** verify scoring math and feasible replacement against hand-worked rosters. **Gate E — market/draft:** add ADP, next-pick simulations and roster-aware updates. Do not publish a "final draft list" before these gates.

### Final board specification

At minimum: NHL player ID, name, age, team-as-of, fantasy eligibility, expected GP/starts, EV+PP+SH TOI, PP role confidence, separate projected scored categories, mean/P10/P50/P90 value, position replacement surplus, marginal current-roster value, ADP/source/date, projected next-pick availability (if supported), pick urgency, tier, data quality/confidence and concise reasons. Preserve enough component columns to explain any surprising ranking.

### Open decisions

League platform; H2H categories vs roto vs points; exact categories/weights; number of teams; C/LW/RW/D/G/UTIL/bench/IR slots; daily or weekly moves; limits and goalie minima; keeper/dynasty settings; draft order/type; playoff weeks; projection horizon; acceptable outside data/ADP sources. None of these are assumed.
