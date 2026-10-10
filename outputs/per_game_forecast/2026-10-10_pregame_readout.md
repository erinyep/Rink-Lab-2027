# October 10 projections

Bundle: `data/processed/forecasts/daily_2026-10-10_20261010T203436Z`. Issued 2026-10-10T20:34:49.440842+00:00. All 14 games retained: 11 pregame, 3 late. Statistical inputs end October 9; current availability is timestamped at retrieval.

[Player projections](../../data/processed/forecasts/daily_2026-10-10_20261010T203436Z/player_projections.csv) · [Team projections](../../data/processed/forecasts/daily_2026-10-10_20261010T203436Z/team_projections.csv) · [Goalies](../../data/processed/forecasts/daily_2026-10-10_20261010T203436Z/goalie_projections.csv) · [Reading guide](../../data/processed/forecasts/daily_2026-10-10_20261010T203436Z/README.md)

## Tonight’s team shots

| team | opponent | unidentified_replacement_skaters | calibrated_opponent_sog_trial | candidate | default | opponent_form_sog_trial | usage_shot_context_trial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ANA | CGY | 0 | 24.111 | 24.363 | 26.313 | 26.042 | 25.831 |
| BUF | UTA | 0 | 26.222 | 26.703 | 28.841 | 28.321 | 25.844 |
| CAR | CHI | 0 | 29.717 | 29.138 | 31.471 | 32.096 | 32.826 |
| CBJ | STL | 0 | 27.475 | 27.281 | 29.465 | 29.675 | 27.8 |
| CGY | ANA | 0 | 24.489 | 24.645 | 26.618 | 26.45 | 25.847 |
| CHI | CAR | 0 | 22.146 | 23.269 | 25.131 | 23.919 | 19.015 |
| COL | TOR | 0 | 34.006 | 33.154 | 35.808 | 36.728 | 37.09 |
| DAL | PIT | 0 | 25.324 | 25.171 | 27.186 | 27.351 | 23.291 |
| DET | MTL | 0 | 27.431 | 26.838 | 28.986 | 29.627 | 27.208 |
| FLA | MIN | 0 | 28.518 | 28.498 | 30.78 | 30.801 | 28.109 |
| LAK | VGK | 0 | 26.662 | 26.919 | 29.074 | 28.797 | 25.628 |
| MIN | FLA | 0 | 27.354 | 27.64 | 29.853 | 29.544 | 26.649 |
| MTL | DET | 1 | 25.904 | 26.25 | 28.352 | 27.977 | 24.957 |
| NSH | OTT | 0 | 26.127 | 26.378 | 28.489 | 28.219 | 23.5 |
| NYI | TBL | 0 | 25.909 | 26.359 | 28.469 | 27.983 | 24.732 |
| OTT | NSH | 0 | 27.116 | 26.752 | 28.893 | 29.286 | 27.748 |
| PIT | DAL | 0 | 26.919 | 27.007 | 29.169 | 29.074 | 26.817 |
| STL | CBJ | 0 | 24.532 | 24.669 | 26.644 | 26.496 | 23.953 |
| TBL | NYI | 0 | 28.195 | 27.792 | 30.017 | 30.452 | 28.715 |
| TOR | COL | 0 | 27.931 | 27.814 | 30.041 | 30.167 | 26.054 |
| UTA | BUF | 0 | 28.84 | 29.029 | 31.353 | 31.149 | 29.858 |
| VGK | LAK | 0 | 28.846 | 28.14 | 30.393 | 31.155 | 28.617 |

Montreal uses one unidentified defense replacement with a past-position prior. All lineups remain scenarios. The fifth model uses recent shot rate and TOI shrunk toward completed-season rates plus conservative team/chance factors. PP/EV usage, rest and ESPN projections are exposed as context; their coefficients have not been fitted.

## Data and remaining validation

Refreshed NHL current season reports, ESPN rosters/injuries, all 69 completed games through October 9, game scoring/goalie stats, 2,484 player-game EV/PP/SH TOI rows, and ESPN projected SOG/GP. MoneyPuck team history retrieved October 10 supplies completed prior-season and lagged current-season context. Nine current games have shot-count disagreements and are excluded from chance updates, retaining official NHL SOG.

Current NHL EDGE aggregates lack a reliable prior-date cutoff and are not used. Confirmed lineups/starters, calibrated participation, goalie duration/pulls, and chronological testing remain open. No model is promoted based on October 9. Sparse zero-rate means are preserved unless the separately labeled usage/shrinkage model changes them. Simulation feasibility constraints cap PPP at G+A and enforce goals ≤ shots, with original means and flags retained.
