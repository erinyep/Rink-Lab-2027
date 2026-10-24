# Kalshi winner benchmark — 2026-10-24

Mapped 24 contracts to 12 official NHL games using exact dates,
team aliases and two-team fixture identities. Quotes were sampled before official game starts.
[Quotes, model probabilities, contract rules and source timestamps](winner_benchmark.csv).

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
