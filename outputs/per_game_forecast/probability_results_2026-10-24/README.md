# First prospective probability comparison — 2026-10-24

| model | games | brier | log_loss | favorite_accuracy |
| --- | --- | --- | --- | --- |
| even_baseline | 12 | 0.25 | 0.693 | nan |
| kalshi_home_midpoint | 12 | 0.226 | 0.644 | 0.667 |
| team_probability_trial | 12 | 0.25 | 0.692 | 0.5 |

[Every game and forecast](scored_predictions.csv) · [Paired game-bootstrap differences](paired_uncertainty.csv).
All scores use the exact separately frozen pregame probabilities and quotes, with one HOME outcome per game.
The market uses the home contract midpoint directly, not an after-the-fact normalized or blended estimate.
Official final winners include overtime/shootouts. No source forecast is refitted or overwritten.
12 games scored; 0 remain unscored.
This is a single slate, too small for promotion or stable calibration conclusions.

These are NHL-outcome probability scores, not exchange settlement/P&L validation: no fees, execution,
depth or actual trade prices. Rescheduled starts fail closed for rules review. The same-game complementary
away contract is validated but does not count as another independent game. Tied 50/50 predictions have
no favorite-accuracy score. Original contract rules and quote timestamps remain in the benchmark.
The earlier retrospective probability-development screen is not pooled into this prospective sample.
