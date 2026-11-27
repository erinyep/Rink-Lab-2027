# November 27 pregame refresh

All **15 games** were issued pregame at **12:39 p.m. Eastern**. The frozen public release contains **4,837 player-model rows, 210 player-sum team-model rows and 136 goalie scenarios**. Direct team win probabilities were issued separately at 12:31 p.m.; the Kalshi comparison covers 30 contracts across all 15 games sampled at 12:31–12:32 p.m. Both remain separate from player projections.

[Game outlook](../../games/) · [Direct team probabilities](../../team-model/) · [Fantasy report](../../report/) · [Kalshi comparison](../kalshi_benchmark_2026-11-27_1732/) · [Frozen forecasts](../../../outputs/per_game_forecast/frozen/daily_2026-11-27_20261127T173735Z/)

## Data and availability

- Acquired official history through November 26: 399 finals, no unfinished games. November 26 had no games, so the latest statistical game date is November 25. All 14,363 positive-TOI player-game rows reconcile with the boxscores, with zero component or identity discrepancies.
- MoneyPuck team history covers through November 25. The play-by-play audit retains six team-game shot discrepancies; the MoneyPuck shot-quality audit quarantines 163 games. Source values were not manually changed and no new model coefficients were fit.
- NHL lineup articles were available for 22 of 30 teams; complete matched 12F/6D lineups were applied to 16. Six other available articles failed full-match/coverage requirements, six teams lacked articles, and two teams had ambiguous names/statuses. Those teams retain prior-game lineup scenarios. [Coverage](coverage.csv) · [Parsed source rows](projected_lineups.csv) · [Source provenance](lineup_manifest.json).
- Vancouver lists two players named Elias Pettersson; Anaheim lists Beckett Sennecke both in the projected lineup and as injured. The importer now quarantines the entire ambiguous team scenario while preserving usable opponent and other-team sources. It does not guess availability or drop the whole day's import. All 110 tests pass, including regressions for the duplicate-name/status case.
- The public NHL bundle has UNKNOWN ESPN injury labels and no fantasy ownership. Published lineups and goalie ordering remain projected, not confirmed. The separate authenticated ESPN fantasy report refreshed at **12:26 p.m. Eastern**, covering **16/16 eligible roster skaters and 3/3 goalies**. Consult that report for the refreshed fantasy availability labels.

## Model policy and follow-up

Existing calibrated-opponent all-player SOG and usage-only conditional ATOI remain selected. Fantasy SOG retains its separate default policy. Raw direct-team probabilities remain selected, with calibration retained as a challenger. No refit or policy promotion was performed.

The hosted refresh and Pages deployment succeeded. Yesterday's failed roster lookup was an empty Thanksgiving slate, not an ESPN authentication failure. Follow-up: handle no-game dates as an explicit successful skip. The existing scheduled workflow publishes the fantasy report only; public NHL game and team pages were refreshed separately in this release.
