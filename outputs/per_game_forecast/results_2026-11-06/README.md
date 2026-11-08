# November 6 forecast evaluation

Three saved pregame games scored against official finals acquired November 8. All 108 participating skaters were covered; six assumed-lineup selections did not appear. Nonparticipants are excluded from conditional production errors.

| model | games | brier | log_loss | favorite_accuracy | goal_mae | predicted_goals | actual_goals |
| --- | --- | --- | --- | --- | --- | --- | --- |
| coin_flip | 3 | 0.25 | 0.693 | nan | nan | nan | 20 |
| direct_team | 3 | 0.182 | 0.553 | 0.667 | 1.061 | 18.846 | 20 |
| goal_history_baseline | 3 | 0.194 | 0.581 | 1.0 | 1.139 | 18.609 | 20 |
| original_player_sum | 3 | 0.214 | 0.621 | 1.0 | 1.351 | 18.227 | 20 |

Full interpretation is in the [November 7 model review](../results_2026-11-07/README.md). The player, team, goalie and coverage CSVs and input hashes are preserved in this directory.
