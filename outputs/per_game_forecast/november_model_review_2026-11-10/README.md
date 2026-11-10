# November daily model review through 2026-11-09

## Recommendation

**Keep calibrated-opponent shots selected for the NHL-wide all-player SOG view.** Across 33 eligible games from the six saved Nov. 4–9 releases (1,185 player-games), its pooled MAE was 1.008 versus 1.023 for default (1.5% lower). The paired game-cluster bootstrap for the MAE difference was -0.015 shots, 95% interval [-0.022, -0.009]. This is continuation evidence for the existing selection, not a case for another promotion.

Keep fantasy shots on their separate default policy. **Show the usage-aware ATOI result on today's reporting page as a challenger:** it scored 2.098 versus 2.246 minutes MAE (6.6% lower) and improved on 6/6 dates. This 33-game variant changes both usage context and shots; the isolated usage-TOI challenger has only 4 games so far. Display it as evidence, but keep default ATOI production policy until the isolated forecast accumulates more prospective games.

The broader saved-forecast review through Nov. 5 also favored calibrated-opponent SOG: **1.0205 vs. 1.0362** for default across 88 games (67/88 games lower; game-cluster 95% interval −0.0201 to −0.0113). That earlier set overlaps Nov. 4–5 in this report, so it is supporting context and is not added to the 33-game count.

Do not promote assist changes: candidate MAE was 0.399 versus 0.403, while the selected/candidate-style forecast totaled 329.9 assists against 368 actual. Keep the PP-opportunity variant labeled experimental (only 4 games) and leave calibrated team probabilities separate (four games). November 1–3 have no saved frozen daily releases in the repository, so their results cannot be included without reconstructing forecasts after the fact.

## Population and provenance

The review includes every saved frozen daily release from Nov. 4 through Nov. 9. It scores conditional player forecasts only for skaters with positive official time on ice; no-shows are not treated as zero-stat performances. All dates use the same refreshed official actuals/boxscore vintage through Nov. 9. The Nov. 8 release contributes its one prospective game; its five late-issued scenarios are excluded. Missing actual participant coverage is listed separately. There are separate direct-team probability results only for dates with a frozen team-model release; Nov. 5 has player/team-category forecasts but no independent daily team-probability file.

## All-player conditional metrics

See [pooled categories](player_metrics.csv), [date-level results](player_metrics_by_date.csv), and [paired SOG intervals](paired_shots_vs_default.csv). Lower MAE and RMSE are better; bias is predicted minus actual.

## Game probabilities

The direct-team/original player-sum comparison uses the matched subset with a separate frozen direct-team release (22 games). It is not a full-November comparison because the Nov. 5 slate has no separate daily team-probability artifact. See [metrics](winner_metrics.csv), [games](team_games.csv), and [per-game scores](winner_scores.csv).

## Coverage

See [coverage by date](coverage_by_date.csv) and [actual participants missing from forecasts](unmodeled_actual_skaters.csv). The official schedule and boxscores were reconciled through 2026-11-09; all source manifests and file hashes are captured in `manifest.json`.
