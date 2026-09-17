# Expected opportunity: proposed first baseline

Research question: Given information available at a forecast cutoff, how many
NHL games and all-strength minutes will a skater play over the next seven days?

This is a proposed working definition of “expected plays,” not a settled choice
of outcome. Games and TOI describe opportunity; shots or other actions would
require a separate event-rate model. No predictive model is fitted yet.

## Unit and timing

One row per player_id and forecast cutoff (UTC), with season_id explicit.
Forecast window: [cutoff, cutoff + 7 days). Use only games completed and roster,
schedule, or availability records known before the cutoff. Historical snapshots
must reflect what was known then; today's injuries or revised schedule cannot
be used as historical features.

## Required inputs

- Game schedule: game_id, season_id, game type, teams, start time, status,
  retrieved_at_utc; retain revisions and distinguish postponed/cancelled games.
- Game-level skater participation and TOI, including zero appearances against
  the eligible roster population; an absent boxscore row alone is not enough to
  distinguish a scratch, injury, transaction, or missing data.
- As-of roster/team membership keyed by player_id, including transactions.
  Season team_abbrevs is not an as-of team assignment for traded players.
- Optional timestamped injury/lineup observations from a documented source.
  Missing status means unknown, not healthy.

## Interpretable baselines

1. Schedule-only reference: each eligible roster player participates in every
   scheduled team game. Explicitly optimistic; no injury information assumed.
2. Participation baseline: scheduled games multiplied by the player's appearance
   fraction over the team's prior 10 completed games while roster-eligible.
3. Expected TOI: sum of game appearance probabilities multiplied by prior mean
   TOI conditional on playing. For insufficient history, use a position-level
   baseline fitted only on past data and flag the fallback.

The 10-game history and seven-day horizon are initial design choices to evaluate,
not evidence-backed reliability thresholds. Retain low-history players and report
results separately rather than silently excluding them.

## Evaluation before expansion

Use chronological train/validation/test cutoffs and prevent overlapping target
windows across splits. Report MAE for games and minutes, prediction bias, and
results by position, history length, and known availability. Compare against the
schedule-only baseline. Fit or tune fallback rates on training history only.
Treat future transactions and unanticipated injuries as forecast uncertainty.

Only after this baseline is evaluated should event counts be estimated from
opportunity and lagged event rates. Neither expected TOI nor points/60 establishes
causal player impact or repeatable talent.
