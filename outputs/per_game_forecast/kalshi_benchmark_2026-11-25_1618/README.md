# Kalshi winner benchmark — 2026-11-25

Mapped 28 contracts to 14 official NHL games using exact dates,
team aliases and two-team fixture identities. Quotes were sampled before official game starts.
[Quotes, model probabilities, contract rules and source timestamps](winner_benchmark.csv).

This snapshot maps 14 games and 28 two-sided team contracts. Median quoted spread is 0.010. Quotes were sampled a median of 7.3 minutes after the team-model issue and at least 461.7 minutes before puck drop. Each row records its own sample time. The market-minus-model column is quoted midpoint minus the raw direct-team probability in percentage points; no de-vigging or blending is applied.

The quote snapshot postdates the forecast issue, so it was not available to the model and is a separate pregame benchmark. It does not alter player forecasts or the selected raw direct-team probabilities.

Contracts settle on official final winners, with postponement/cancellation provisions retained per row.
This benchmark assumes a normally completed fixture; void/fair-price resolutions must be excluded from
ordinary win/loss scoring. Raw contract text remains authoritative. Home/away quoted midpoints need not
sum to one. Midpoints are quoted prices, not calibrated probabilities or executable prices.
The model and market snapshots are close in time but not simultaneous. Order-book depth and last-trade
time are unavailable in this snapshot; market update time is not a trade timestamp. No blended forecast,
betting recommendation or historical pregame claim. Evaluate future model-only and market-only scores
on identical settled games before testing a blend with chronological training.

[Kalshi historical data documentation](https://docs.kalshi.com/getting_started/historical_data)
describes live/archive cutoffs. Backfill must use candles ending before an explicitly fixed NHL pregame
cutoff; final settlement prices cannot substitute for pregame probabilities.
