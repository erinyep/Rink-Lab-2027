# Updated team model — 2026-10-29

[Interactive forecasts](index.html) · [Goal and win forecasts](team_win_probabilities.csv) · [Lagged model inputs](team_goal_forecasts.csv).

11 games, all issued before puck drop. Model `goal_xg_home_rest` fit through 2026-10-26.
Learned home ice, rest/back-to-back, own scoring and opposing goals allowed, plus lagged xG where applicable.
The simple baseline is preserved alongside every updated prediction. Player/fantasy conditional means are unchanged;
these are direct team forecasts, not a redistribution of player goals. No confirmed-goalie or injury effect is claimed.
Winner probabilities use independent Poisson scoring and equal tie splitting; intervals are not calibrated.
Model choice used the prior full season. Coefficients remain frozen through 2026-10-26;
today's lagged feature inputs include official history through 2026-10-28, without refitting coefficients.
Future performance must be scored against this frozen release. Credit MoneyPuck.com for lagged xG data; absent or
disagreeing xG rows remain excluded from rate updates, with official goals and schedule retained.
