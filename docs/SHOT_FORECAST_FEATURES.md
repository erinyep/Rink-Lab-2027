# Shot forecast features and source priorities

Question: which pregame information improves player SOG and team shots
for/against beyond historical player rates, without using future game events?

## Current comparison

October 10 implementation: `scripts/build_daily_forecasts.py` now issues the
four comparison models plus `usage_shot_context_trial`. That fifth trial uses
recent shot rate and TOI, completed-season player priors, prior-season team
SOG priors and lagged 5v5 xOnGoal. Source-disputed current games are excluded
from chance updates. `scripts/acquire_game_toi.py` supplies strength-specific
TOI context; `scripts/export_espn_projection_benchmark.py` supplies ESPN SOG/GP
benchmarks. Neither PP usage nor ESPN benchmarks currently receives a fitted
forecast coefficient. See the [October 10 readout](../outputs/per_game_forecast/2026-10-10_pregame_readout.md).

Daily sequence: refresh current sources; acquire completed games through the
previous date; complete fantasy game stats and game TOI; build daily forecasts
with explicit template/history/MoneyPuck/benchmark paths; run goalie forecasts
with the same histories; finalize the wide reading views. Each command has
`--help`; source paths and hashes are stored in the resulting manifests.
Current season-summary reports are retained for auditing but are replaced by
past-only game aggregates when producing date-specific player rates.

October 9, 143 identical positive-TOI modeled appearances; lower MAE is better.
Team MAE uses eight official NHL team SOG outcomes and identical refreshed
lineup scenarios. Player counts use individual NHL skater SOG and need not sum
to official team counts. Assumed lineups are not confirmed starting lineups.

| Model | Player shot MAE | Player shot RMSE | Team shot MAE |
| --- | ---: | ---: | ---: |
| default | 1.058 | 1.377 | 8.870 |
| opponent_form_sog_trial | 1.059 | 1.379 | 8.862 |
| candidate | 1.048 | 1.363 | 7.823 |
| calibrated_opponent_sog_trial | 1.050 | 1.365 | 7.816 |

Candidate lowers SOG and assists using fixed October 6–7 calibration.
Opponent trial changes SOG only with a conservative team/opponent factor.
Hybrid combines those operations; it does not blend predictions using weights
chosen on October 9. Other means follow candidate, including points = G + A.
The hybrid was constructed after seeing October 9 and is exploratory.
Default remains the baseline; four games do not justify promotion.

Reproduce hybrid: `rink-lab.venv/bin/python scripts/build_hybrid_trial.py`.
All four models are in the existing consolidated files; hybrid team rows use
`lineup_version=refreshed_injury_trial`. The additional Jake O’Brien row is
SOG-only. Injury and appearance probabilities are not inferred from a prior.

## Source and feature choices

| Priority | Source | Features to test | Reason and limits |
| --- | --- | --- | --- |
| 1 | Official NHL boxscores, play-by-play, schedules and rosters | Recent player SOG/minute; rolling TOI; PP/EV role; shot attempts for/against; rest days, home/away, back-to-backs | Separates shot opportunity from shooting rate. State-specific TOI may require shift data or suitable summary reports; do not infer exact player exposure from team events alone. |
| 2 | MoneyPuck published team/player game and shot downloads | Lagged 5v5 and PP/PK SOG, attempts, xOnGoal/60, xGoals/60, player on-ice opportunities | Already acquired team history. Shot-volume measures are more directly aligned with SOG than goal-quality measures. Validate both rather than assume xGoals improves shots. |
| 3 | NHL EDGE | Offensive-zone time, shot-location mix | Candidate context features. Check historical/as-of access before integration; a current season summary cannot recreate an earlier cutoff. Public access does not guarantee a documented bulk API. |
| 4 | ESPN saved league/player snapshots and projections | Timestamped injury status, eligibility, fantasy roster; projected SOG/GP and TOI if supplied | Useful availability/context and independent benchmark. Current local exports have injury/eligibility/ownership fields, not ESPN shot projections. Verify projection season, actual versus projected stat source and GP denominator before comparing. |

Official NHL EDGE describes shot location and puck-zone time:
[NHL introduction](https://www.nhl.com/news/nhl-edge-launches-website-for-puck-and-player-tracking-data).
MoneyPuck publishes team/player game data and unblocked shot-event files:
[downloads](https://moneypuck.com/data.htm). Credit MoneyPuck for its data;
published use is non-commercial. Blocked shots are absent from the event files,
so use appropriate team totals or NHL events for all-attempt measures.
ESPN provides [fantasy projections](https://fantasy.espn.com/hockey/players/projections);
availability in our authenticated feed must be inspected before acquisition.

ESPN percent owned and percent started reflect fantasy-manager decisions;
they are not calibrated probabilities of NHL participation. Keep them out of
the initial shot-rate model. Fantasy points combine outcomes and add little
information beyond their components. Prioritize PP TOI, total TOI, recent
deployment, availability and schedule over popularity metrics.

## Missing-data rules

- Missing opponent context: neutral multiplier 1, visible status flag.
- Missing player history: documented pregame position prior for SOG; retain
  missingness in unsupported categories. Do not silently drop the player.
- True observed zero: preserve it. A separately tested sparse-history shrinkage
  rule may soften zeros; do not replace them just because an outcome was positive.
- Missing roster entries: check current NHL rosters against player-history and
  saved prior-game populations before issuance. A history-only candidate must be
  labeled uncertain; known injuries still apply. Severson is an uncovered
  October 9 appearance, not a retroactively added pregame selection.
- Conflicting shot totals: retain both and a source-agreement flag. NHL official
  boxscores define team SOG scoring. Do not manufacture chance-level events to
  make MoneyPuck totals match: CBJ 45 versus NHL 47, WPG 16 versus NHL 17.
- Missing postgame appearance: do not score a conditional forecast as zero.
  Participation models need a separately defined eligible roster population.

## Validation sequence

1. Build reproducible lagged player rates/exposure and team rates from games
   strictly preceding each forecast cutoff. Use prior-season shrinkage because
   early-season head-to-head samples are too small.
2. Compare baseline, calibration only, opponent only and combined model on
   identical appearances. Evaluate roster/participation separately.
3. Add TOI/PP role and lagged attempt/xOnGoal features one family at a time.
   Fit weights on training/calibration windows, assess later untouched games.
4. Report player/team bias, MAE, RMSE and probabilistic scores, interval coverage,
   source completeness and lineup error. Estimate uncertainty by game, since
   players share a common game environment.
5. Issue the fourth model prospectively before puck drop. October 9 is a
   diagnostic, and cannot validate a model designed after inspecting its results.
