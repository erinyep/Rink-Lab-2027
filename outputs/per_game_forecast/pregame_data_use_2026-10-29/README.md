# Pregame preparation and data use — 2026-10-29

Research question: do the current ice-time, shots and direct team-model policies improve on their frozen baselines on new games, and how do their winner probabilities compare with independently observed pregame market quotes?

## Release

11 games issued at 10:06 AM ET; 498 candidate skaters across five models and 51 goalie candidates across two models. All games passed strict pregame, freshness, coverage, finite-value, source-hash and count-identity checks. Official history covers 202 final games through 2026-10-28. No missing historical forecast dates are reconstructed.

[Game outlook](../../../docs/games/index.html) · [Fantasy report](../../../reports/today/2026-10-29_quinn/index.html) · [Direct team model](../team_context_daily_2026-10-29_20261029T140615Z/README.md) · [Frozen feature trial](../feature_evidence_2026-10-29/README.md)

## How today's data is used

- **MoneyPuck team games:** 202 current-season games downloaded. Previous-season SOG supplies team priors; lagged 5v5 xOnGoal supplies the usage-shot context challenger. The original opponent-shot factor remains based on NHL SOG. Today's main-context audit excludes 9 distinct games involving today's teams from MoneyPuck chance features because of source discrepancies. Previous-season priors are not reconciled game by game against current-season NHL snapshots.
- **Separate direct team model:** uses lagged MoneyPuck xG/xGA alongside official goals, home ice and rest. 191/202 current games pass its goals/SOG reconciliation; 11 games are excluded from xG updates while their official goals and schedule remain. Coefficients stay frozen through 2026-10-26; fresh features end before today. Team goals are not redistributed into player forecasts.
- **MoneyPuck shot file:** 16,880 raw events, 202 official games represented, 77 games quarantined and 125 usable. Missing official games: 0. Lagged defense shot quality and expected rebounds enter the separate four-variant feature trial using the October 20 coefficients. These do not change the five main player models.
- **Fantasy:** the adopted policy uses usage-based TOI only; shots and other categories keep the default. Neither new MoneyPuck xG nor Kalshi prices change fantasy goal/shot means. Saved active/bench labels and category scores come from refreshed ESPN data.
- **Kalshi:** 22 winner contracts mapped to all 11 games by exact date, team aliases and fixture identity, with rules and pregame timestamps retained. Median bid/ask spread is $0.01. Quotes benchmark both probability models; they do not train or adjust either model. Player props/totals are preserved for coverage inspection only and have not been mapped or validated as forecasting features.

Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Whole target-date outcomes are excluded from every forecasting feature. Downloaded xG may contain retrospective source corrections; it is not an archived historical as-of score.

## Today's games and market comparison

Goal means belong to the separate fitted team model. All probability columns refer to the home team; differences are percentage points, not betting edges. Quoted midpoints are not calibrated or guaranteed executable probabilities. Model and market observation times differ.

| away | home | start_ET | away_goal_mean | home_goal_mean | team_model_home_% | original_home_% | Kalshi_home_% | model_minus_market_pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WPG | TBL | 7:00 PM | 2.56 | 3.66 | 66.84 | 59.51 | 68.5 | -1.66 |
| UTA | PIT | 7:00 PM | 3.18 | 3.34 | 52.38 | 43.95 | 45.5 | 6.88 |
| CBJ | CAR | 7:00 PM | 2.6 | 3.7 | 66.68 | 53.18 | 69.5 | -2.82 |
| CHI | DET | 7:30 PM | 2.55 | 3.37 | 62.99 | 51.28 | 62.5 | 0.49 |
| BOS | STL | 8:00 PM | 3.04 | 2.95 | 48.48 | 43.18 | 50.5 | -2.02 |
| WSH | NSH | 8:00 PM | 3.05 | 3.3 | 53.93 | 39.05 | 50.5 | 3.43 |
| MTL | DAL | 8:00 PM | 2.76 | 3.28 | 58.3 | 56.09 | 59.5 | -1.2 |
| NYI | MIN | 8:00 PM | 2.65 | 3.45 | 62.55 | 52.34 | 64.5 | -1.95 |
| BUF | ANA | 10:00 PM | 3.31 | 3.35 | 50.55 | 45.8 | 43.5 | 7.05 |
| OTT | LAK | 10:00 PM | 3.0 | 2.77 | 46.32 | 42.74 | 48.5 | -2.18 |
| VAN | SJS | 10:00 PM | 3.0 | 3.64 | 59.67 | 53.1 | 62.5 | -2.83 |

[Full comparison and timestamps](game_comparison.csv) · [Contract rules and original bid/ask quotes](../kalshi_benchmark_2026-10-29/winner_benchmark.csv) · [Depth and trade recency](../kalshi_liquidity_2026-10-29/winner_liquidity.csv)

Depth was available for 22/22 contracts. Trade pagination completed for 22/22. Median age of most recent available live-API trade at the later observation: 0.9 minutes. Depth, trades and original quotes are separate sequential observations. A recent trade does not establish sufficient liquidity for an arbitrary order size.

### Today's broader Kalshi coverage

Date-filtered contract counts below are discovery counts; only winner contracts have verified NHL mappings and rules for today's benchmark. Zero-volume or absent markets are not imputed.

| series | contracts | two_sided | median_volume | median_spread |
| --- | --- | --- | --- | --- |
| KXNHLGAME | 22 | 22 | 2613.8 | 0.01 |
| KXNHLTOTAL | 99 | 99 | 20.0 | 0.01 |
| KXNHLTEAMTOTAL | 110 | 110 | 0.0 | 0.02 |
| KXNHLSAVES | 0 | 0 | — | — |
| KXNHLSAVE | 0 | 0 | — | — |
| KXNHLAST | 219 | 219 | 0.0 | 0.04 |
| KXNHLPTS | 290 | 286 | 0.0 | 0.04 |
| KXNHLANYGOAL | 0 | 0 | — | — |
| KXNHLGOAL | 506 | 505 | 0.0 | 0.02 |

## Participation and fantasy status

Preserved official roster candidates, last-game participation and timestamped ESPN injury labels for every candidate. No lineup-selection replacement or fitted participation probability was promoted. Conditional player means assume dressing; goalie means assume a full start. No starter is certified by these inputs.

[Every candidate and selection reason](participation_candidates.csv) · [Team participation audit](participation_summary.csv) · [MoneyPuck coverage by team](moneypuck_team_context.csv)

13 selected candidates have a non-ACTIVE label: {'UNKNOWN': 9, 'DAY_TO_DAY': 4}. [Review names and statuses](selected_status_review.csv). These labels require follow-up; ACTIVE itself also does not confirm dressing. Official roster and ESPN snapshots are morning observations, not evening lineup confirmations.

- Next scoring period 32: added none; removed none. Today retains the current-period roster until ESPN makes the change effective.
- No unlocked benched skater has a game today in the saved roster; no additional rostered start is available.
- Matchup goalie starts: 4 of 3 minimum recorded. Minimum already met. You have 2 active goalie slots at a time; the minimum accumulates across the matchup. Upcoming active goalies: Jesper Wallstedt, Pyotr Kochetkov. Starts remain unconfirmed. Benched with a game: Juuse Saros; bench starts do not count toward your matchup.

## Next prospective checks

Preserve this morning release. Before evening puck drop, acquire a new timestamped roster/injury/starter and market observation; any new forecast must be issued separately before the ten-minute cutoff. After finals, score the frozen player, fantasy TOI, goalie, direct-team and feature releases separately, and compare each probability model with the same home-side Kalshi benchmark on matched completed games. Exclude void/cancelled/fair-price contract resolutions from ordinary winner scoring. No model promotion, coefficient tuning, lineup transactions or market trades occurred in this preparation.

[Source paths, timestamps and usage](source_usage.csv) · [Report manifest](manifest.json)
