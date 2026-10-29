# Frozen feature experiment — 2026-10-29

11 games, four variants: bias control, defense, shot quality and both.
Issued 2026-10-29T14:06:40.130055+00:00. Uses the exact October 20 fitted parameters with fresh
past-only inputs through 2026-10-28; no refit, tuning or model promotion.
Source disagreements retain their existing quarantines and training-time imputation.

[Frozen predictions](tonight_experimental_team_forecasts.csv) · [Player SOG accounting](player_contributions.csv).
These separate team-volume experiments do not change the main five models.
Player contributions are ordered changes in the usage trial, not causal importance.
Completed feature evaluations are reported separately in the latest model review;
this release does not fix the historical evidence count to its original issue date.

Score after finals using `scripts/evaluate_feature_evidence.py`; preserve this release.
