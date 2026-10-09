# October 9 simulations and exact model status

Simulation artifact created at **2026-10-09T19:51:20.131895+00:00**, before first puck drop. All **4** October 9 regular-season games are verified against the official schedule. 178 official-roster skater/game entries receive draws for both models; 1 entries without model history remain explicitly listed.

## October 8: what the default actually did

| model | category | player_games | projected | actual | mae | bias | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | goals | 351 | 62.605 | 61.000 | 0.285 | 0.005 | 0.454 |
| baseline | assists | 351 | 104.797 | 106.000 | 0.418 | -0.003 | 0.567 |
| baseline | shots | 351 | 563.911 | 542.000 | 1.109 | 0.062 | 1.430 |
| candidate | goals | 351 | 62.605 | 61.000 | 0.285 | 0.005 | 0.454 |
| candidate | assists | 351 | 100.845 | 106.000 | 0.414 | -0.015 | 0.567 |
| candidate | shots | 351 | 522.114 | 542.000 | 1.091 | -0.057 | 1.429 |

The default was close on aggregate goals and assists, and overpredicted shots by 21.9. The candidate reduced shots MAE 1.65% and assists MAE 1.05%, but undershot their totals and worsened assist bias. Its October 8 predictions were reconstructed afterward from saved pregame inputs using factors frozen before reading outcomes. This was not a forecast issued pregame.

[Readable October 8 player comparison](../../data/processed/forecasts/october_8_comparison_20261009T193905Z/player_comparison_readable.csv) · [Full October 8 readout](october_8_readout.md)

## Default and new test model

Default: GP-exposure-weighted history with completed-season recency weights 1, 0.5, 0.25, the existing provisional current-season update and rookie shrinkage fallback. Candidate: the same means with SOG×0.92588 and assists×0.96229, fitted only on October 6–7 with 200 pseudo expected events. Goals stay unchanged and points=G+A. No promotion or refitting occurred.

Both now have a seeded simulation layer: 10,000 draws per skater/game/model, seed 20261009. SOG is Poisson; goals are binomial conditional on SOG; assists and hits are Poisson; points=G+A; PPP is binomial conditional on points. Whole-number draws preserve goals≤SOG and PPP≤points. Assists/hits and players are otherwise independent; opponent, role and team dependence are not modeled. PIM, plus/minus, TOI and goalie outcomes are not simulated.

A 2.7-shot mean stays 2.7. Individual simulated outcomes can be 0, 1, 2, 3 or higher. Simulation p10/p90 and event probabilities apply **if the player plays** and are provisional distribution summaries, not calibrated predictive intervals or appearance probabilities.

## Every October 9 game and team

| game_id | team | opponent | official_roster_skaters | simulated_skaters | missing_model_history | goalie_rows_retained_not_simulated |
| --- | --- | --- | --- | --- | --- | --- |
| 2026020066 | DET | SEA | 24 | 24 | 0 | 2 |
| 2026020066 | SEA | DET | 23 | 22 | 1 | 2 |
| 2026020067 | WSH | NYR | 21 | 21 | 0 | 2 |
| 2026020067 | NYR | WSH | 23 | 23 | 0 | 3 |
| 2026020068 | CBJ | PIT | 21 | 21 | 0 | 2 |
| 2026020068 | PIT | CBJ | 23 | 23 | 0 | 2 |
| 2026020069 | WPG | ANA | 21 | 21 | 0 | 3 |
| 2026020069 | ANA | WPG | 23 | 23 | 0 | 2 |

Official rosters include players who may not dress and injured players. Injury labels remain visible and missing history remains listed. Game coverage is complete; confirmed lineup and player forecast coverage are separate questions. No fantasy roster is used as the NHL population.

## Distribution diagnostics and what they imply

| model | category | appearances | mean_nll | zero_mean_positive_actual | positive_mean_nll | at_least_one_brier | positive_mean_pearson_second_moment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| default | goals | 351 | 0.474 | 0 | 0.485 | 0.119 | 1.206 |
| default | assists | 351 | inf | 1 | 0.674 | 0.179 | 1.154 |
| default | shots | 351 | inf | 1 | 1.592 | 0.196 | 1.182 |
| default | hits | 351 | inf | 1 | 1.319 | 0.200 | 1.215 |
| candidate | goals | 351 | 0.474 | 0 | 0.485 | 0.119 | 1.206 |
| candidate | assists | 351 | inf | 1 | 0.675 | 0.178 | 1.199 |
| candidate | shots | 351 | inf | 1 | 1.592 | 0.195 | 1.276 |
| candidate | hits | 351 | inf | 1 | 1.319 | 0.200 | 1.215 |

Lower negative log likelihood (NLL) and Brier score are better. A positive-mean Pearson residual second moment around 1 is consistent with Poisson variance; values around 1.15–1.28 suggest checking extra variability, but mean error also affects this measure. Infinite full NLL means a zero-mean forecast assigned no probability to a positive observed count. These cases are counted, not excluded. The positive-mean diagnostics are explicitly a subset and do not rescue the complete distribution. No dispersion parameter was selected from October 8.

## Stored data and freshness

Forecast: `data/processed/forecasts/per_game_20262027_20261009T195052Z`. Schedule cutoff: **2026-10-09T19:45:25.099952+00:00**. ESPN completed: **2026-10-09T19:49:44.015913+00:00**. Source timestamps are UTC; game dates are Eastern.

All 65 completed regular-season games September 29–October 8 are archived: 2,340 skater/game rows, 260 separate goalie/game rows (including backups), PPP reconstructed from official scoring summaries. All 642 skaters reconcile with season reports across ten categories. One goalie count exception remains flagged. ESPN ATOI=TTOI seconds/GP, GAA=GA×3600/goalie seconds and SV%=SV/SA passed for all six teams; minimum goalie starts and historical lineup eligibility are not established by those ratio checks.

## Next steps, in order

1. Freeze this October 9 run and evaluate means and distributions after all four games finish. Compare default/candidate on identical appearances; preserve absent/unmapped rows. Do not tune factors after outcomes and call October 9 untouched.
2. Prioritize position-prior shrinkage for sparse/zero-count histories in a separately versioned candidate: zero means produced impossible-count failures. Define and select the prior using chronological development/validation windows, not the already-observed October 8 night.
3. Extend prior-season game and historical eligible-roster coverage. Evaluate rolling TOI, current-season update strength and rookie fallbacks using ordered, non-overlapping windows before fitting participation. Current-season logs are complete, but historical eligibility cannot be reconstructed from today’s ESPN roster.
4. Compare Poisson with a negative-binomial candidate using validation-selected dispersion; check probability/interval coverage and log scores by game/date, not independent player rows. The present quantiles remain provisional until those checks pass.
5. Add goalie starts/rates after count exceptions and league minimum-start rules are resolved; then calibrated joint scenarios, feasible replacement and lineup decisions. These gates remain unfinished rather than being marked complete merely because simulations exist.

## Reproduce and inspect

```sh
rink-lab.venv/bin/python scripts/simulate_game_date.py --date 2026-10-09 \
  --forecast data/processed/forecasts/per_game_20262027_20261009T195052Z --draws 10000 --seed 20261009 \
  --raw-snapshot data/raw/nhl/snapshots/simulation_context_20261009T194825Z
```

The pregame checks intentionally block replay after puck drop; preserve the run and its manifest for evaluation instead of issuing it again as a new pregame forecast.

[Simulation summaries](../../data/processed/forecasts/simulation_2026-10-09_20261009T195119Z/simulation_summary.csv) · [Whole-number example draws](../../data/processed/forecasts/simulation_2026-10-09_20261009T195119Z/integer_simulation_examples.csv) · [All-game coverage](../../data/processed/forecasts/simulation_2026-10-09_20261009T195119Z/game_team_coverage.csv) · [Unmodeled roster skaters](../../data/processed/forecasts/simulation_2026-10-09_20261009T195119Z/players_without_model_history.csv) · [Manifest](../../data/processed/forecasts/simulation_2026-10-09_20261009T195119Z/manifest.json)
