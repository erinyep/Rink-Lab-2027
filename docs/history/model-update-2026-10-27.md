# Model update — October 27, 2026

Two actual changes are enabled:

1. **Fantasy ATOI:** recent-usage TOI replaces default TOI only. Error falls 2.1644→2.0145 minutes on 347 saved fantasy appearances/48 games (6.9%); paired 95% interval for the change is [-0.2127,-0.0826] minutes. Improvement survives leaving out each date. All other skater category means retain default.
2. **Team goals and derived win probabilities:** a fitted Poisson model uses own scoring, opponent goals allowed, xG/xGA, home ice and schedule rest. Trained on 2,624 games, selected on a separate 1,312-game season, and tested on all 187 current-season games through October 26. Recent goal MAE 1.4175→1.4048; Brier 0.2425→0.2350 versus the simple goal-history baseline. Production coefficients are refit through yesterday, and daily issuance now generates the updated team model alongside the original forecasts.

The team model is an **enabled challenger**, not a proven winner. The recent Brier interval narrowly includes no improvement. On the 48 games shared with the old saved-forecast probability approach it is slightly worse (0.2421 vs 0.2409). Preserve both and score future frozen forecasts; do not count the reconstructed training/test predictions as prospective releases. Historical xG uses a corrected upstream model trained on 2023–26 shots.

[Today’s updated team forecasts](../team-model/) · [Today’s fantasy report](../report/) · [Full validation and fitted coefficients](team_model_update_through_2026-10-26/README.md) · [Selection details, shared-old-model comparison and reliability](model_update_decision_2026-10-27/README.md).

The training snapshot lacked October 26 xG, so official goals/schedule still contributed without invented xG. The fresh daily issuance snapshot subsequently reached all 187 games and updates usable lagged xG inputs. Disagreements remain quarantined. Today’s 11-game release uses fresh ESPN injuries; lineup and goalie starts remain provisional. The new team model does not claim an injury or confirmed-goalie effect.

The latest complete pregame team-context vintage is `team_context_daily_2026-10-27_20261027T132258Z`, chosen by issuance time, not outcomes. The earlier standalone release is preserved separately. Only one canonical version per game should enter the primary prospective scoreboard.
