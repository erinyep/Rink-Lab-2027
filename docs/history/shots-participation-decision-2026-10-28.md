# Shots and lineup decision — October 28

The expanded evaluation does **not** justify changing the fantasy shots default or replacing the current lineup rule. Keep the existing fantasy ice-time update. Calibrated opponent shots remain a supported all-player challenger, with a smaller, uncertain benefit for fantasy rosters.

## Evidence and decision

All six saved complete daily slates were re-scored against the same October 28 actuals snapshot: October 10, 12, 20, 22, 24 and 27. There are 59 disjoint games, 2,121 forecast-covered skater appearances, and 423 saved fantasy-roster appearances. Missing forecast dates were not reconstructed. Historical model/input changes mean these results evaluate the saved forecasting policy, not one fixed fitted model.

| Population | Default shots MAE | Calibrated shots MAE | Paired change | Game-bootstrap 95% interval |
| --- | ---: | ---: | ---: | --- |
| All skaters | 1.040 | 1.023 | −0.017 | [−0.023, −0.012] |
| Saved fantasy rosters | 1.292 | 1.277 | −0.015 | [−0.033, +0.004] |

Calibrated shots improved 44/59 games for all skaters and 36/59 for fantasy. Removing any one date leaves a favorable point estimate in both populations. However, resampling whole dates also leaves the fantasy interval crossing zero (approximately −0.038 to +0.009). Six dates and exploratory comparisons do not establish a dependable fantasy improvement. Candidate shots are nearly tied with calibrated shots, so these results do not isolate a benefit from the opponent adjustment itself.

**Decision:** retain the fantasy shots default. Preserve calibrated shots as a challenger and reassess on additional frozen dates. Do not choose a player subgroup or blend based on these same errors.

## Participation test

The existing rule already prioritizes the previous team game's players, then baseline predicted TOI, with saved injury exclusions. We tested two fixed alternatives using each forecast's saved history strictly before its target date:

1. Rank by appearances in the last five **team** games, then baseline TOI.
2. Keep last-game priority and use five-game appearances as a tiebreaker before TOI.

All rules retain the original candidate population, saved injury labels, 12F/6D capacities, player means and unidentified replacement contribution. These are retrospective selection tests, not newly fitted or calibrated participation probabilities.

| Rule | Selected nonparticipants | Goal MAE per team | Shot MAE per team |
| --- | ---: | ---: | ---: |
| Saved lineup | 114 | 1.460 | 5.175 |
| Five-game frequency | 144 | 1.461 | 5.189 |
| Last game, then frequency | 116 | 1.460 | 5.162 |

The frequency rule adds 30 selected nonparticipants across 118 team-games; the paired game-bootstrap interval for the increase is +0.110 to +0.398 per team. The tiebreaker changes only six player swaps (12 candidate selection changes), adds two nonparticipants, and has no clear goal/shot error benefit. Three actual skater appearances lack candidate forecasts across the full sample and remain visible in coverage.

**Decision:** reject both lineup replacements. Recent appearance frequency alone is not the missing improvement. Keep both experiments reproducible without connecting them to production issuance.

Saved injury labels also need better timing/return-to-play evidence: 10 candidate appearances labeled INJURY_RESERVE and one labeled OUT subsequently played. These are candidate-game observations, not 11 unique players. ACTIVE likewise is not confirmation of playing. Do not remove injury exclusions wholesale based on these outcomes; preserve timestamped near-puck-drop status and lineup evidence for future testing.

## Goal overprediction

The original team model's pooled bias is +0.156 goals per team, versus +0.641 on October 27. Bias was negative on October 20, 22 and 24. This does not support a blanket correction based on yesterday. Neither participation challenger materially changes pooled goal error. This comparison concerns the original player-sum model; the new direct team model still has only its first prospective slate.

## Reproduce and inspect

[Full screen and source manifest](../../outputs/per_game_forecast/shots_participation_through_2026-10-27/README.md)

```sh
rink-lab.venv/bin/python scripts/screen_shots_and_participation.py \
  --previous_review outputs/per_game_forecast/season_through_2026-10-26 \
  --additional_bundle data/processed/forecasts/daily_2026-10-27_20261027T132258Z \
  --actuals data/processed/forecasts/fantasy_game_details_20261028T214830Z \
  --boxscores data/raw/nhl/snapshots/current_game_history_20262027_20261028T214822Z \
  --out outputs/per_game_forecast/shots_participation_reproduction
```

The output directory must be new. Frozen forecasts are hash-verified and never overwritten. The script exports paired game/date uncertainty, leave-one-date-out shots metrics, per-date participation results, every candidate's past-only features and selection, and each team's projected/actual totals.
