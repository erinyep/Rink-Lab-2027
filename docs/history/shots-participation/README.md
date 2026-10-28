# Shots and participation screen through October 27

59 disjoint games across 6 saved dates; 2121 observed skater appearances.
All canonical bundles re-scored against one actuals vintage; no missing-date forecasts reconstructed.

## Shots

| population | model | rows_scored | mae | bias |
| --- | --- | --- | --- | --- |
| all_players | calibrated_opponent_sog_trial | 2121 | 1.023 | -0.05 |
| all_players | candidate | 2121 | 1.023 | -0.052 |
| all_players | default | 2121 | 1.04 | 0.068 |
| all_players | opponent_form_sog_trial | 2121 | 1.04 | 0.07 |
| all_players | usage_shot_context_trial | 2121 | 1.027 | -0.063 |
| fantasy | calibrated_opponent_sog_trial | 423 | 1.277 | -0.125 |
| fantasy | candidate | 423 | 1.278 | -0.138 |
| fantasy | default | 423 | 1.292 | 0.05 |
| fantasy | opponent_form_sog_trial | 423 | 1.292 | 0.063 |
| fantasy | usage_shot_context_trial | 423 | 1.287 | -0.128 |

| population | model | games | appearances | mae_delta_vs_default | lower_95 | upper_95 | games_improved |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_players | calibrated_opponent_sog_trial | 59 | 2121 | -0.017 | -0.023 | -0.012 | 44 |
| all_players | candidate | 59 | 2121 | -0.017 | -0.023 | -0.012 | 43 |
| all_players | default | 59 | 2121 | 0.0 | 0.0 | 0.0 | 0 |
| all_players | opponent_form_sog_trial | 59 | 2121 | -0.0 | -0.002 | 0.002 | 27 |
| all_players | usage_shot_context_trial | 59 | 2121 | -0.013 | -0.023 | -0.003 | 36 |
| fantasy | calibrated_opponent_sog_trial | 59 | 423 | -0.015 | -0.033 | 0.004 | 36 |
| fantasy | candidate | 59 | 423 | -0.014 | -0.033 | 0.006 | 36 |
| fantasy | default | 59 | 423 | 0.0 | 0.0 | 0.0 | 0 |
| fantasy | opponent_form_sog_trial | 59 | 423 | 0.0 | -0.005 | 0.006 | 31 |
| fantasy | usage_shot_context_trial | 59 | 423 | -0.005 | -0.031 | 0.022 | 33 |

Date-cluster sensitivity (only six dates, exploratory):

| population | model | delta | lower_95 | upper_95 |
| --- | --- | --- | --- | --- |
| all_players | calibrated_opponent_sog_trial | -0.017 | -0.021 | -0.015 |
| all_players | candidate | -0.017 | -0.023 | -0.014 |
| all_players | default | 0.0 | 0.0 | 0.0 |
| all_players | opponent_form_sog_trial | -0.0 | -0.002 | 0.002 |
| all_players | usage_shot_context_trial | -0.013 | -0.016 | -0.011 |
| fantasy | calibrated_opponent_sog_trial | -0.015 | -0.038 | 0.009 |
| fantasy | candidate | -0.014 | -0.041 | 0.012 |
| fantasy | default | 0.0 | 0.0 | 0.0 |
| fantasy | opponent_form_sog_trial | 0.0 | -0.004 | 0.006 |
| fantasy | usage_shot_context_trial | -0.005 | -0.029 | 0.014 |

## Participation screen

| variant | team_games | nonparticipants | missed_actual | unmodeled_actual | swaps | goals_mae | goals_bias | shots_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| last_then_recent_five | 118 | 116 | 115 | 3 | 12 | 1.46 | 0.152 | 5.162 |
| recent_five | 118 | 144 | 143 | 3 | 186 | 1.461 | 0.154 | 5.189 |
| saved_lineup | 118 | 114 | 113 | 3 | 0 | 1.46 | 0.156 | 5.175 |

| date | variant | nonparticipants | goals_mae | shots_mae |
| --- | --- | --- | --- | --- |
| 2026-10-10 | last_then_recent_five | 19 | 1.498 | 3.68 |
| 2026-10-10 | recent_five | 19 | 1.489 | 3.713 |
| 2026-10-10 | saved_lineup | 18 | 1.502 | 3.751 |
| 2026-10-12 | last_then_recent_five | 2 | 1.331 | 5.804 |
| 2026-10-12 | recent_five | 4 | 1.38 | 5.821 |
| 2026-10-12 | saved_lineup | 2 | 1.331 | 5.804 |
| 2026-10-20 | last_then_recent_five | 27 | 1.112 | 4.92 |
| 2026-10-20 | recent_five | 26 | 1.126 | 4.986 |
| 2026-10-20 | saved_lineup | 26 | 1.116 | 4.898 |
| 2026-10-22 | last_then_recent_five | 22 | 1.529 | 6.08 |
| 2026-10-22 | recent_five | 30 | 1.55 | 6.092 |
| 2026-10-22 | saved_lineup | 22 | 1.522 | 6.103 |
| 2026-10-24 | last_then_recent_five | 25 | 1.551 | 4.855 |
| 2026-10-24 | recent_five | 38 | 1.557 | 4.853 |
| 2026-10-24 | saved_lineup | 25 | 1.551 | 4.855 |
| 2026-10-27 | last_then_recent_five | 21 | 1.617 | 6.099 |
| 2026-10-27 | recent_five | 27 | 1.582 | 6.134 |
| 2026-10-27 | saved_lineup | 21 | 1.617 | 6.099 |

| metric | variant | delta_per_team | lower_95 | upper_95 |
| --- | --- | --- | --- | --- |
| nonparticipants | last_then_recent_five | 0.017 | 0.0 | 0.042 |
| nonparticipants | recent_five | 0.254 | 0.11 | 0.398 |
| nonparticipants | saved_lineup | 0.0 | 0.0 | 0.0 |
| goals_error | last_then_recent_five | -0.0 | -0.004 | 0.003 |
| goals_error | recent_five | 0.001 | -0.017 | 0.02 |
| goals_error | saved_lineup | 0.0 | 0.0 | 0.0 |
| shots_error | last_then_recent_five | -0.014 | -0.041 | 0.008 |
| shots_error | recent_five | 0.014 | -0.103 | 0.124 |
| shots_error | saved_lineup | 0.0 | 0.0 | 0.0 |

Two fixed last-five-team-game ranking rules, neither fitted nor tuned on outcomes. Preserve 12F/6D, saved injury exclusions,
candidate populations, baseline player means and unidentified replacement contributions. Use each issuance's saved history,
strictly before target date. Missing history retains the candidate. Injury labels are snapshots, not confirmed scratches.
These new rankings are retrospective development screens, not previously issued predictions or calibrated participation probabilities.
Actual positive-TOI appearances define participation. No unseen roster players added after outcomes. Unmodeled actuals stay visible.
Team errors assess lineup swaps only; player forecasts remain conditional on playing. Shot targets here sum skater SOG (goalie shots excluded).
Do not claim production improvement from this screen without a future frozen trial.

[Leave-one-date-out](shots_leave_one_date_out.csv) · [Every team](participation_team_games.csv) · [Every candidate](https://github.com/erinyep/Rink-Lab-2027/blob/main/outputs/per_game_forecast/shots_participation_through_2026-10-27/participation_player_audit.csv)
