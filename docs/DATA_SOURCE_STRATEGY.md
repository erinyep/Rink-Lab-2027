# Forecast data priorities — October 20, 2026

The research question is whether defense-generated offense, player opportunity
and independent game expectations improve **future** player SOG, scoring and
goalie forecasts beyond our existing history/usage baselines.

Add sources in the order below. Availability of a field does not establish its
predictive value. Save snapshots before games, retain IDs/source cutoffs, and
compare one feature group at a time on later games.

| Priority/source | Useful inputs | Current evidence and action |
| --- | --- | --- |
| 1. Official NHL schedule, boxscores, rosters and game TOI | Actual participation, current team, recent minutes, EV/PP/PK role, rest, opponent, home/away | Refreshed all 140 finals through October 19 and 5,039 positive-TOI skater exposures. These establish population, outcomes and opportunity; keep them authoritative. Freshness/coverage matters more immediately than another complex model. |
| 2. Official NHL play-by-play | D attempts including blocks, strength, location, D scoring involvement, short same-team followups | Acquired 16,025 attempts for 140 games. Two team-game SOG discrepancies; quarantine both games for derived context. No missing shooter positions or shot coordinates. Context-only in today's release. |
| 3. MoneyPuck team and shot downloads | Team 5v5 xOnGoal/xG, individual D shot quality, expected rebound generation, shot location/type and rush/rebound context | Team file covers 140 games. New shot file has 11,613 unblocked events and 124 original fields across all 140 games. 49 games disagree with at least one official team SOG total and are quarantined for shot-quality aggregates. Resolve source-version differences before trusting broad xG comparisons. |
| 4. NHL shifts and deployment | Which D pair was on ice, player-pair exposure, PP units, linemates and changes in role | Acquire shift-level coverage next. Without it, we cannot attribute on-ice team chances to a D pair or use true pair minutes as a denominator. Boxscore D shots are not pair creation. |
| 5. ESPN Fantasy | Timestamped injuries, eligibility, ownership/waivers, projected season benchmarks, roster decisions | Refreshed read-only league state and projections. Only 327 skater entries currently have usable projected SOG/positive GP; preserve missing benchmark values. Ownership describes decision context, not hockey ability. Do not use current roster/ownership to label historical fantasy cohorts. |
| 6. Kalshi public markets | External win/total/points/assist/save probability benchmarks, pregame changes, disagreement with model | Took an unauthenticated read-only snapshot of seven requested NHL series. Current prices remain unmapped and unused in forecasts. First build an independent benchmark; consider features only after coverage/timing and incremental value are validated. |
| 7. NHL EDGE | Offensive-zone time, shot-location profiles, skating/shot traits | Useful hypotheses for role/style; start saving dated snapshots. Current cumulative aggregates cannot recreate old as-of features. Prioritize zone/shot exposure ahead of speed leaderboards for the current forecasting targets. |

MoneyPuck's [published downloads](https://moneypuck.com/data.htm) support this
research use with attribution. Credit **MoneyPuck.com** in outputs that use its
data. Its shot download contains unblocked events; NHL PBP supplies blocks.
The site's [model explanation](https://moneypuck.com/about.htm) distinguishes
shot-quality scores from observed goals. Keep model-derived xG separate from
official outcomes. No unlisted website scraping is needed.

## What the defense measures mean

- **Direct production:** D attempts, unblocked attempts, SOG and shot share.
- **Shot quality:** sum of MoneyPuck D xG and expected rebounds, with source
  reconciliation flags. These are model scores, not goals a defenseman caused.
- **Scoring involvement:** distinct goals with a D shooter or assistant;
  assist credits are separate because two D can assist the same goal.
- **Temporal followups:** another teammate's attempt within 10 seconds after a
  D attempt, without an intervening whistle/period boundary or recorded opponent
  attempt/puck action. Each following attempt gets at most one most-recent D
  anchor. This is neither a recorded pass nor a verified possession sequence.
- **Not yet measured:** exits, controlled entries, pre-shot passes, possession
  value and pair-specific creation. Standard PBP does not establish these.

Export all-strength and 5v5 counts separately. A 5v5 followup means the following
attempt was 5v5; its anchor can have a different strength state. Per-game counts
are not on-ice per-60 rates. Use shifts/state-specific exposure before claiming
pair or on-ice rates. Retain low-exposure teams/players with sample sizes and
shrink estimates rather than silently deleting them.

MoneyPuck shot positions are missing on 164 raw events. The processed quality
table uses the same game's official NHL boxscore position only for those
missing values, preserving the raw snapshot and recording the fallback. Never
classify missing position as forward. `shotID` is unique jointly with game ID,
not globally in this download; NHL game IDs are reconstructed from the season
start year and MoneyPuck's game suffix and checked against official games.

## Kalshi: benchmark first

[Public market data](https://docs.kalshi.com/getting_started/quick_start_market_data)
can be read without an account or API key. The acquisition script only calls
public GET market endpoints; it makes no orders or account requests.

The October 20 snapshot queried KXNHLGAME, KXNHLTOTAL, KXNHLTEAMTOTAL,
KXNHLSAVES, KXNHLAST, KXNHLPTS and KXNHLANYGOAL. It found respectively
94, 225, 130, 0, 209, 261 and 0 open markets. Empty queried series do not prove
that no equivalent contracts exist under another series. For example, inspect
the separate KXNHLSAVE/KXNHLGOAL series before concluding save/goal coverage
is absent. No current SOG series was identified in the inspected series catalog.

Among two-sided quotes, median spread was $0.02 for game winners versus $0.24
for game totals. Median reported volume was zero for totals, team totals, assists
and points. These observations argue against treating every posted midpoint as
a reliable independent consensus.

Before joining a market to a forecast:

1. Map the exact NHL game ID and, for a player prop, NHL player ID and contract
   threshold. Inspect settlement rules, overtime/shootout treatment and void rules.
2. Save quotes, bid/ask sizes, depth, last-trade timestamp, volume, contract rules
   and retrieval timestamp **before the official NHL start**. Contract close time
   is not game start; current quotes can already contain live information.
3. Reject crossed, missing or one-sided quotes; report spreads and stale/low-volume
   observations. A quoted midpoint is not itself a calibrated probability.
4. Evaluate Brier/log loss and calibration for matching binary events. Winner
   probability is not expected SOG; player threshold contracts compare with the
   model's probability of exceeding the same threshold, not its mean count.
5. Separate model-only, market-only and combined forecasts on identical future
   games. Test whether market data adds signal beyond injuries/starters already
   represented in our inputs. Do not promote a blend from these exploratory quotes.

Kalshi's [historical API documentation](https://docs.kalshi.com/getting_started/historical_data)
separates live and archived markets/candles. Backfill must follow the published
cutoffs and pagination. Use candles whose end is at or before our issue cutoff;
closing/settlement prices cannot stand in for earlier pregame prices.

## Additional NHL/ESPN features worth testing

The existing official TOI endpoint is
`https://api.nhle.com/stats/rest/en/skater/timeonice`; PBP is
`https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play`.
Keep report pagination, complete game IDs and raw hashes. Public endpoint
schemas should be treated as subject to change, with validation before joins.

Next feature families:

1. **Opportunity and availability:** recent EV/PP minutes, change versus prior
   role, team PP opportunities, recent participation and goalie rest/start history.
   Do not conflate a conditional player mean with the probability of dressing.
2. **Team game state:** lagged score-state shot rates, PP/PK opportunity and
   opponent strength; test whether adjustments duplicate information already
   in individual histories or MoneyPuck context.
3. **Deployment:** shift-based pair/linemate exposure and PP-unit continuity.
4. **ESPN benchmark gaps:** audit identity/projection coverage for actual NHL
   participants and fantasy rosters before adding more league-facing fields.
5. **EDGE snapshots:** NHL describes its zone-time and shot-location measures on
   [NHL EDGE](https://www.nhl.com/nhl-edge/teams/). Freeze future observations;
   do not backfill historical cutoffs using today's cumulative values.

## Validation and experiment order

Keep the existing default/candidate comparison unchanged. On the next unseen
games, freeze TOI-only, shot-rate-only, matchup-only and D-context-only variants.
Use fixed pre-declared shrinkage and a common participant population. Evaluate
player SOG MAE/RMSE/bias and discrete calibration; report team and fantasy/role
subgroups separately, with paired game-cluster uncertainty. Evaluate goalie
saves and GA independently. More features are justified only by stable coverage
and incremental out-of-sample benefit.

Finish scheduled execution after the one-command runner has a reliable local
runtime, secret handling, idempotence, retries, freshness gates and failure alerts.
No unattended job or external trade execution is enabled here.

## First incremental-value screen completed

[October 20 feature evidence](../outputs/per_game_forecast/feature_evidence_2026-10-20/README.md) trains through October 12 and tests 51 October 13–19 games. D and shot-quality inputs do not improve team SOG MAE against a bias-adjusted control in this specified screen. This is a corrected-data retrospective test, not evidence that the sources never help. All variants are frozen separately for tonight; main forecasts remain unchanged. Archive source vintages and score future games before promotion.

## October 24 validation update

[Broader review](history/broader_model_review_2026-10-24/README.md) supersedes older coverage counts: 167 official games, 155 reconciled MoneyPuck team games for the new goal/xG screen, and 105 reconciled shot-quality games. Twelve team-file games and 62 shot-file games have discrepancies; no raw values overwritten. Credit MoneyPuck.com. Current xG was rebuilt using 2023–26 shots, so older-season screens cannot independently validate the upstream model.

[Kalshi benchmark](history/kalshi_benchmark_2026-10-24/README.md): 24 winner contracts mapped to 12 official October 24 games, before puck drop, with contract rules retained. Median spread $0.01. Quoted midpoint remains a benchmark, not a calibrated probability or model input. Depth and last-trade timestamps are not captured. Extra series query found no KXNHLSAVE contracts and 127 KXNHLGOAL contracts (92 two-sided; median volume zero). Historical pregame backfill remains separate work.

## Results through October 25

184 NHL finals and 6,623 positive-TOI appearances validated. The refreshed MoneyPuck goal/xG screen retains 167 current-season games (17 team-file discrepancies); shot-quality comparison retains 115 games (69 shot-file discrepancies). All source rows preserved. Official goalie count exceptions for October 24 Jarry and Vejmelka remain excluded from conditional count scoring. [Updated evidence](history/broader_model_review_through_2026-10-25/README.md).

The October 24 Kalshi comparison uses saved pregame quotes and official NHL final winners, one home outcome per game. It does not claim exchange settlement verification, trade execution or P&L. [First prospective probability scores](history/probability_results_2026-10-24/README.md).
