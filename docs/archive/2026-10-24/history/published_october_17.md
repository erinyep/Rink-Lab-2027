# Additional October 17 evidence from the newer repository

The published export declares issuance at 2026-10-17T17:36:04.427312+00:00; the view was created at 2026-10-17T19:48:34.711496+00:00. It has 13 declared pregame games, of which 12 were still future when the exported view was created. One earlier game is explicitly late and excluded. The full raw October 17 bundle remains on the other machine; its source-manifest hash is recorded in the published manifest. The exported prediction CSV hashes verify, but we cannot independently inspect the absent bundle or recover every player forecast.

## Team shots

| scope | model | rows | games | mae | bias |
| --- | --- | --- | --- | --- | --- |
| declared_pregame | calibrated_opponent_sog_trial | 26 | 13 | 4.205 | -0.885 |
| declared_pregame | candidate | 26 | 13 | 4.315 | -0.843 |
| declared_pregame | default | 26 | 13 | 4.484 | 1.245 |
| declared_pregame | opponent_form_sog_trial | 26 | 13 | 4.398 | 1.199 |
| declared_pregame | usage_shot_context_trial | 26 | 13 | 4.14 | -1.508 |
| publication_safe | calibrated_opponent_sog_trial | 24 | 12 | 4.147 | -0.597 |
| publication_safe | candidate | 24 | 12 | 4.2 | -0.545 |
| publication_safe | default | 24 | 12 | 4.392 | 1.546 |
| publication_safe | opponent_form_sog_trial | 24 | 12 | 4.369 | 1.49 |
| publication_safe | usage_shot_context_trial | 24 | 12 | 4.147 | -1.296 |

Use publication_safe for conservative comparative evidence; declared_pregame depends on the saved issuance claim. Do not merge these exported team observations into the full-player sample. All six exported team categories are scored in [metrics](published_october_17_metrics.csv).

## Goalies

| scope | model | category | rows | games | mae | bias |
| --- | --- | --- | --- | --- | --- | --- |
| declared_pregame | goalie_history_baseline | saves | 26 | 13 | 4.355 | 0.897 |
| declared_pregame | goalie_opponent_context_trial | saves | 26 | 13 | 4.383 | 0.362 |
| declared_pregame | goalie_history_baseline | goals_against | 26 | 13 | 1.286 | 0.054 |
| declared_pregame | goalie_opponent_context_trial | goals_against | 26 | 13 | 1.254 | -0.003 |
| publication_safe | goalie_history_baseline | saves | 24 | 12 | 4.249 | 1.303 |
| publication_safe | goalie_opponent_context_trial | saves | 24 | 12 | 4.298 | 0.645 |
| publication_safe | goalie_history_baseline | goals_against | 24 | 12 | 1.366 | 0.052 |
| publication_safe | goalie_opponent_context_trial | goals_against | 24 | 12 | 1.334 | -0.019 |

14 goalie/model rows remain unresolved. IDs use exact normalized full names on the official same-game NHL PBP goalie roster. [Mapping and observed roles](published_october_17_goalie_mapping.csv) retain every candidate; headline counts use actual starters with valid count identities only. The public export contains saves and GA means, so no unexported per-player/SA forecast is invented.

Next: transfer the immutable raw and processed October 17 forecast bundle to enable full player evaluation, fantasy subgroups and issue-time/source verification. The existing interactive matchup and category-report work is preserved.
