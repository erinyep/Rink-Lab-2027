# Model decisions — October 24, 2026

Keep the default fantasy model. Add separately labeled team probability and Kalshi
benchmarks; neither is a promoted replacement. All issued forecasts remain frozen.

| Question | Evidence | Decision / next test |
| --- | --- | --- |
| More than October 22? | Full saved forecasts: 36 games over four dates, 1,295 positive-TOI appearances, 262 fantasy appearances and 72 goalie starts. Broader goal/xG development: 1,312 prior-season games plus 155 reconciled current-season games. | Keep prospective and reconstructed evidence separate. Missing saved forecasts cannot be recreated as prospective predictions. |
| Improve fantasy shots? | Opponent-only MAE 1.3226 versus default 1.3259; paired delta −0.0033, exploratory 95% interval [−0.0101,+0.0030]. Calibrated all-player MAE improves 1.0435→1.0263, but its fantasy delta is only −0.0004. | Retain default for fantasy. Continue category-specific trials; do not transfer all-player gains to a roster subgroup. |
| Opportunity and injuries? | 68 selected identified skaters did not appear across the saved dates. ACTIVE candidates appeared 1,259/1,398 times; DTD 9/22. Saved IR labels include four appearances. Usage trial improves fantasy TOI MAE by 0.162 minutes, but does not improve fantasy shots. | Highest-priority player test: probability of dressing, conditional EV/PP minutes, and replacement-role allocation. Availability labels are not confirmed lineups. Injuries are not the only cause of absence; do not infer causal injury effects from these rates. |
| Goalie improvements? | Opponent context saves MAE 5.309 versus 5.529; nominal p10–p90 saves intervals cover 69.4% versus 65.3% for baseline across 72 starts. GA error is essentially tied. | Test starter/rest features, start/relief and duration separately, then dispersion. Do not widen intervals by a multiplier fitted to this same evaluation sample. |
| Defense scoring ability? | Across 167 games: defensemen 147 goals, 525 assists and 125 PPP. On 105 reconciled shot-data games: 95 goals versus 90.0 xG. | Descriptive production, not proof of finishing talent. Compare D goals/xG, PP opportunity, rebounds and secondary chance creation separately. Goals plus assists double-count scoring events. Shift/pair/PP-unit exposure is needed for on-ice offense or prevention. |
| Do existing D features help? | Both frozen slates together: 23 games. D-only team SOG MAE 5.630 versus control 5.717; paired delta −0.088 [−0.436,+0.261]. Shot quality alone 5.734. | No promotion. These are team-shot tests, not tests of defenseman goals or team wins. Continue the frozen design. |
| Add MoneyPuck xG? | Simple lagged xG did not beat goal history reliably. Prior-season blend MAE 1.360 versus 1.364; current-season blend 1.382 versus 1.382. Current Brier: goals 0.2394, xG 0.2404, blend 0.2395. All paired gain intervals include zero. | Test special-teams opportunity, goalie quality, score/venue-adjusted 5v5 xG and shrunk finishing jointly against interpretable baselines. Preserve source/model vintages. |
| Trust all MoneyPuck rows? | 12 current team-file games fail goals/SOG reconciliation; 62 shot-file games fail SOG reconciliation. Shot-quality description retains 105 games. | Keep both teams quarantined in affected games and export discrepancies. Do not silently overwrite NHL counts or discard raw source rows. |
| Add Kalshi? | 24 winner contracts mapped to all 12 October 24 games; median spread $0.01. Broad prop series often have zero median volume; queried save series returned no contracts. | Save a market-only pregame benchmark first. Current snapshots cannot backfill historical pregame quotes. Depth and last-trade time remain unavailable. No market blend or betting recommendation. |

The new probability transform of saved team goal means has development Brier 0.238
versus 0.250 for 50/50 on 36 games; its paired interval includes no improvement.
The five existing models share goal means, so identical probability results are
one signal, not five independent confirmations. October 24 is its first separate
timestamped prospective release. It assumes independent Poisson scoring counts
and splits tied counts equally; it has no fitted home-ice, starter, or OT model.

[Broader goal/xG, defense and injury evidence](broader_model_review_2026-10-24/README.md)
· [Fantasy/role uncertainty](model_decisions_2026-10-24_v2/README.md)
· [New probability trial](team_probability_2026-10-24/README.md)
· [Kalshi benchmark](kalshi_benchmark_2026-10-24/README.md).

MoneyPuck provides documented team/shot downloads and rebuilt its xG model using
2023–26 shots. Older-season screens on current corrected xG are development work,
not independent validation of that upstream model. Credit [MoneyPuck.com](https://moneypuck.com/data.htm)
and [model documentation](https://moneypuck.com/about.htm). Kalshi backfill must follow
[live/archive cutoffs](https://docs.kalshi.com/getting_started/historical_data) and use
candles ending before the chosen NHL pregame timestamp, never settlement prices.
