# Pregame preparation and data use — 2026-10-30

Research question: do the current ice-time, shots and direct team-model policies improve on their frozen baselines on new games, and how do their winner probabilities compare with independently observed pregame market quotes?

## Release

3 games issued at 12:13 PM ET; 133 candidate skaters across five models and 16 goalie candidates across two models. All games passed strict pregame, freshness, coverage, finite-value, source-hash and count-identity checks. Official history covers 213 final games through 2026-10-29. No missing historical forecast dates are reconstructed.

[Game outlook](../../../docs/games/index.html) · [Fantasy report](../../../reports/today/2026-10-30_quinn/index.html) · [Direct team model](../team_context_daily_2026-10-30_20261030T161300Z/README.md) · [Frozen feature trial](../feature_evidence_2026-10-30/README.md)

## How today's data is used

- **MoneyPuck team games:** 213 current-season games downloaded. Previous-season SOG supplies team priors; lagged 5v5 xOnGoal supplies the usage-shot context challenger. The original opponent-shot factor remains based on NHL SOG. Today's main-context audit excludes 3 distinct games involving today's teams from MoneyPuck chance features because of source discrepancies. Previous-season priors are not reconciled game by game against current-season NHL snapshots.
- **Separate direct team model:** uses lagged MoneyPuck xG/xGA alongside official goals, home ice and rest. 200/213 current games pass its goals/SOG reconciliation; 13 games are excluded from xG updates while their official goals and schedule remain. Coefficients stay frozen through 2026-10-26; fresh features end before today. Team goals are not redistributed into player forecasts.
- **MoneyPuck shot file:** 17,780 raw events, 213 official games represented, 80 games quarantined and 133 usable. Missing official games: 0. Lagged defense shot quality and expected rebounds enter the separate four-variant feature trial using the October 20 coefficients. These do not change the five main player models.
- **Fantasy:** the adopted policy uses usage-based TOI only; shots and other categories keep the default. Neither new MoneyPuck xG nor Kalshi prices change fantasy goal/shot means. Saved active/bench labels and category scores come from refreshed ESPN data.
- **Kalshi:** 6 winner contracts mapped to all 3 games by exact date, team aliases and fixture identity, with rules and pregame timestamps retained. Median bid/ask spread is $0.01. Quotes benchmark both probability models; they do not train or adjust either model. Player props/totals are preserved for coverage inspection only and have not been mapped or validated as forecasting features.

Credit [MoneyPuck.com](https://moneypuck.com/data.htm). Whole target-date outcomes are excluded from every forecasting feature. Downloaded xG may contain retrospective source corrections; it is not an archived historical as-of score.

## Today's games and market comparison

Goal means belong to the separate fitted team model. All probability columns refer to the home team; differences are percentage points, not betting edges. Quoted midpoints are not calibrated or guaranteed executable probabilities. Model and market observation times differ.

| away | home | start_ET | away_goal_mean | home_goal_mean | team_model_home_% | original_home_% | Kalshi_home_% | model_minus_market_pp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NJD | VGK | 6:00 PM | 2.74 | 3.18 | 57.05 | 49.02 | 50.5 | 6.55 |
| WPG | FLA | 7:00 PM | 2.61 | 3.47 | 63.46 | 53.3 | 67.5 | -4.04 |
| SEA | CGY | 8:00 PM | 3.01 | 3.02 | 50.14 | 43.18 | 48.5 | 1.64 |

[Full comparison and timestamps](game_comparison.csv) · [Contract rules and original bid/ask quotes](../kalshi_benchmark_2026-10-30/winner_benchmark.csv) · [Depth and trade recency](../kalshi_liquidity_2026-10-29/winner_liquidity.csv)

Depth was available for 22/22 contracts. Trade pagination completed for 22/22. Median age of most recent available live-API trade at the later observation: 0.9 minutes. Depth, trades and original quotes are separate sequential observations. A recent trade does not establish sufficient liquidity for an arbitrary order size.

### Today's broader Kalshi coverage

Date-filtered contract counts below are discovery counts; only winner contracts have verified NHL mappings and rules for today's benchmark. Zero-volume or absent markets are not imputed.

| series | contracts | two_sided | median_volume | median_spread |
| --- | --- | --- | --- | --- |
| KXNHLGAME | 6 | 6 | 14656.91 | 0.01 |
| KXNHLTOTAL | 27 | 27 | 56.66 | 0.01 |
| KXNHLTEAMTOTAL | 30 | 30 | 1.0 | 0.02 |
| KXNHLSAVES | 0 | 0 | — | — |
| KXNHLSAVE | 2 | 2 | 823.41 | 0.045 |
| KX | 0 | 0 | — | — |
| NHL | 0 | 0 | — | — |

## Participation and fantasy status

Preserved official roster candidates, last-game participation and timestamped ESPN injury labels for every candidate. No lineup-selection replacement or fitted participation probability was promoted. Conditional player means assume dressing; goalie means assume a full start. No starter is certified by these inputs.

[Every candidate and selection reason](participation_candidates.csv) · [Team participation audit](participation_summary.csv) · [MoneyPuck coverage by team](moneypuck_team_context.csv)

4 selected candidates have a non-ACTIVE label: {'UNKNOWN': 3, 'DAY_TO_DAY': 1}. [Review names and statuses](selected_status_review.csv). These labels require follow-up; ACTIVE itself also does not confirm dressing. Official roster and ESPN snapshots are morning observations, not evening lineup confirmations.

- No unlocked benched skater has a game today in the saved roster; no additional rostered start is available.
- Matchup goalie starts: 6 of 3 minimum recorded. Minimum already met. You have 2 active goalie slots at a time; the minimum accumulates across the matchup.

## Next prospective checks

Preserve this morning release. Before evening puck drop, acquire a new timestamped roster/injury/starter and market observation; any new forecast must be issued separately before the ten-minute cutoff. After finals, score the frozen player, fantasy TOI, goalie, direct-team and feature releases separately, and compare each probability model with the same home-side Kalshi benchmark on matched completed games. Exclude void/cancelled/fair-price contract resolutions from ordinary winner scoring. No model promotion, coefficient tuning, lineup transactions or market trades occurred in this preparation.

[Source paths, timestamps and usage](source_usage.csv) · [Report manifest](manifest.json)
