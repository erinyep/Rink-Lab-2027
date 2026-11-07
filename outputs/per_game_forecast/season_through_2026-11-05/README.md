# All saved daily-model results through November 5, 2026

All available frozen five-model daily forecasts were scored against one refreshed official NHL actuals vintage through November 5. The 88 games below are the games with saved prospective five-model releases; the other 173 of 261 finals have no saved release and are not reconstructed in this prospective review. A separate [past-only replay](../rolling_replay_through_2026-11-05/README.md) rebuilds conditional shots means for all 261 game dates from inputs cut off before each date; it is clearly labeled as retrospective and is not pooled with the saved releases. Player errors here are conditional on playing; only positive-TOI actuals are included.

## All-player shots

| model | player-games | games | SOG MAE | bias |
| --- | ---: | ---: | ---: | ---: |
| calibrated_opponent_sog_trial | 3,159 | 88 | 1.0205 | -0.0567 |
| candidate | 3,159 | 88 | 1.0210 | -0.0581 |
| usage_shot_context_trial | 3,159 | 88 | 1.0239 | -0.0727 |
| default | 3,159 | 88 | 1.0362 | +0.0607 |
| opponent_form_sog_trial | 3,159 | 88 | 1.0362 | +0.0622 |

Calibrated-opponent minus default MAE is **-0.0157 shots** (95% paired whole-game bootstrap interval -0.0201 to -0.0113); calibrated-opponent had lower SOG error in 67 of 88 games. That is a **1.5% lower MAE** than default (about 0.016 shots per appearance). The game-level bootstrap interval excludes zero, though the absolute gain is small. Calibrated-opponent also had lower date-level SOG MAE on 10 of 10 saved forecast dates. This is a conditional SOG comparison, not lineup-selection or fantasy-category performance. The interval treats games as clusters; forecast dates can still share slate-level conditions.

## Other player categories

See [all category metrics](player_metrics.csv). All five variants share the same scored player-game populations. Category differences are descriptive; the calibrated-opponent change is intended for NHL SOG only.

## Coverage and files

- Official results: 261 completed games through November 5; matched saved five-model forecasts: 88 games and 3,159 distinct player-game appearances across the scored participant population.
- [SOG forecast and actual rows for all five models](shots_scored_all_games.csv) · [SOG results by forecast date](shots_by_date.csv) · [date-level comparison](shots_date_comparison.csv) · [paired game differences](shots_paired_games.csv) · [bootstrap interval](shots_paired_uncertainty.csv).
- Source snapshots and hashes, saved review manifest hashes, excluded nonparticipants, and calculation details are in `manifest.json`.
- November 6 has not been evaluated because those games were not completed when this review was made.
