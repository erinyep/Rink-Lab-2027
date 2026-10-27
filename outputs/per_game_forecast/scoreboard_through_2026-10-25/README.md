# Prediction history — through 2026-10-25

[Season and rolling 7/30-day scoreboard](model_scoreboard.csv) · [Source registry](source_registry.csv).

Immutable, content-addressed copies of issued forecasts, official actuals and evaluations
are stored locally under `data/processed/prediction_history/`. Repeating registration
verifies hashes; corrected actuals receive a new version. Issuance, input cutoffs,
ownership labels and original manifests are retained. Registered forecasts are scored only
when matching actuals exist in the review. No missing forecast is reconstructed; absent conditional outcomes are not zero.

The derived scoreboard uses the review's canonical forecast per date and one actuals
vintage, so revisions and repeated issuances are not double-counted. Separate player,
fantasy, team and eligible goalie-start populations are shown. The October 17 export-only
cohort and older October 9 trials remain in their separate research reports. This first
scoreboard covers full daily bundles only. Rates are not pooled across goalie exposures.
Probability calibration, interval coverage and paired uncertainty remain in the detailed
evaluation reports; this CSV summarizes count errors, not proof of a model improvement.
