s# Initial per-game forecast results — October 6, 2026

The first baseline is implemented and evaluated. **Recency-weighted historical
rates are the default**, selected on 2024–25 validation. The more structured
ELWAY-inspired opportunity × rate model remains available with its shrinkage
components exposed. No goalie-start or skater participation model is claimed.

Methodology and rerun commands: [forecast guide](../../docs/PER_GAME_FORECAST.md).

## Latest accepted inputs

Current NHL reports, schedule, and ESPN league state were refreshed at approximately
**7:47 PM EDT on October 6, 2026** (23:47 UTC). This is a saved snapshot, not a
continuously updating feed. NHL source corrections and in-progress games can
change subsequent pulls.

| NHL regular season | Skaters | Goalies | Goalies flagged for SA ≠ SV + GA |
| --- | ---: | ---: | ---: |
| 2021–22 | 1,004 | 119 | 0 |
| 2022–23 | 951 | 107 | 15 |
| 2023–24 | 924 | 98 | 10 |
| 2024–25 | 920 | 103 | 18 |
| 2025–26 | 940 | 98 | 22 |
| 2026–27, in progress | 617 | 53 | 1 |

All skater seasons passed the expanded model-input validation, including report
coverage/GP agreement, scoring identities, TOI identities, source hashes, and
pagination totals. Goalies remain a separate population; source exceptions are
retained and flagged, not repaired or fitted.

ESPN snapshot: six teams, **134 scoring-roster entries**, **1,566 available
entries**, and **1,699 distinct players**. The difference is Owen Tippett's
explicit pending-drop overlap. All **117 rostered skaters** receive conditional
forecasts and have a resolved schedule-team mapping; **17 rostered goalies** have
`goalie_model_pending`. Barkov, McKenna, Stenberg, and the center Elias Pettersson
now have resolved NHL identities.

The seven-day schedule snapshot contains **48 upcoming regular-season games**.
The export contains **4,218 skater/game rows**, including players with explicitly
missing forecasts; **337** rows concern rostered skaters. There are **109 skaters
with an unknown ESPN NHL team**, all outside the scoring-roster skater population.
Their game counts remain missing rather than zero. Matching does not imply every
available player has recent NHL history or a usable forecast.

## Held-out result

Target: **2025–26 season-average production per game played**. Equal-player MAE
is shown below; a lower number is better. This is not individual-game accuracy.

| Model | Goals/game MAE | Assists/game MAE | SOG/game MAE |
| --- | ---: | ---: | ---: |
| Last completed-season rate | 0.07569 | 0.09750 | 0.33323 |
| Recency-weighted, selected default | 0.07192 | 0.09222 | 0.33278 |
| Opportunity × rate with shrinkage | 0.06666 | 0.09393 | 0.33947 |

The default reduces MAE by about **5.0% for goals** and **5.4% for assists**;
the **0.1% shot improvement is effectively unchanged**. The process model has
the strongest held-out goals result but worse equal-player SOG error. We did not
change the selected method after seeing those test results.

Validation scores were close: weighted **0.943850**, process **0.944089**, versus
1.0 for the reference. This is not evidence of a decisive or statistically
significant superiority. The process model's chosen settings were decay 0.5,
5 pseudo-games of event exposure, 50 prior shots for finishing, and the fixed
10-game TOI prior. The weighted default uses historical weights 1, 0.5, 0.25.

The default's test bias is **+0.00717 G/game**, **+0.00435 A/game**, and
**+0.11792 SOG/game**. Its GP-weighted SOG MAE is **0.29210**, versus **0.28893**
for the last-season baseline, so the equal-player result does not imply improved
shot forecasts for heavily used players. The full metric export includes position,
history strata, and GP-weighted errors for every supported category.

The pre-target cohort contains **1,210 players**: 820 appeared in the target
season, while 390 had no reported appearance and retain undefined per-game
outcomes. Another 120 target-season entrants had no prior history in the cohort
and are reported outside the evaluation. This limits claims about rookies and
future availability. Historical corrections retrieved today also prevent a
strict historical as-of claim.

## Current output and limits

The NHL forecast table retains **1,212 skaters** with recent history or current
appearances. This is a research population, not a claim that all are currently
rostered in the NHL. The live update adds observed current-season exposure and
uses a labeled position-shrinkage fallback for 16 current-season players without
completed-season history. Neither update has yet been validated at game cutoffs.

Every scheduled-game row distinguishes production **if the player plays** from
unconditional expectations. Playing probabilities and `expected_*` fields are
missing. The seven-day schedule reference assumes every team game is played and
does not adjust for injuries, scratches, opponent strength, lineup congestion,
or goalie starts. Auxiliary HIT/PIM/PPP/+−/TOI estimates are exploratory; roster
ATOI aggregation is not established.

Latest local run (generated files are Git-ignored):

`data/processed/forecasts/per_game_20262027_20261006T235037Z/`

- [Scheduled skater/game rows](../../data/processed/forecasts/per_game_20262027_20261006T235037Z/scheduled_skater_game_forecasts.csv)
- [ESPN-enriched player forecasts](../../data/processed/forecasts/per_game_20262027_20261006T235037Z/espn_player_forecasts.csv)
- [Process components and shrinkage](../../data/processed/forecasts/per_game_20262027_20261006T235037Z/process_components_provisional.csv)
- [Held-out comparison plot](../../data/processed/forecasts/per_game_20262027_20261006T235037Z/held_out_per_game_error.png)
- [Provenance and output hashes](../../data/processed/forecasts/per_game_20262027_20261006T235037Z/manifest.json)

Validation completed: 11 focused Python tests, existing R pagination/population
tests, full live pipeline execution, source/output hash checks, and visual review
of the R comparison plot. The next milestone remains the documented game-level
participation and rolling-TOI baseline, followed by goalie forecasts and the later
ELWAY uncertainty/replacement layers.
