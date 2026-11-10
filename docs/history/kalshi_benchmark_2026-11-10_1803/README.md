# Kalshi winner benchmark — 2026-11-10

Mapped 14 contracts to all 7 official NHL games using exact dates,
team aliases and two-team fixture identities. Quotes were sampled at 1:03 p.m. Eastern,
before each official game start. The model probabilities were issued at 8:12 a.m. Eastern,
so this is a later pregame quote snapshot, not a synchronized comparison.
[Matched quotes and model probabilities](winner_benchmark.csv) · [All open markets acquired](open_markets.csv) · [Series coverage](series_coverage.csv).

The full public acquisition returned 94 open winner contracts with two-sided quotes (median spread $0.02; median reported volume 133.24), plus totals, team totals and player markets. No contracts were returned for saves or any-goal series. The mapped seven-game subset has a $0.01 median spread. Market data were read-only and never entered the forecasts. The [acquisition manifest](acquisition_manifest.json) records its timestamp, series and source hashes.

Contracts settle on official final winners, with postponement/cancellation provisions retained per row.
This benchmark assumes a normally completed fixture; void/fair-price resolutions must be excluded from
ordinary win/loss scoring. Raw contract text remains authoritative. Home/away quoted midpoints need not
sum to one. Midpoints are quoted prices, not calibrated probabilities or executable prices.
The model and market snapshots are 4 hours 51 minutes apart. Order-book depth and last-trade
time are unavailable in this snapshot; market update time is not a trade timestamp. No blended forecast,
betting recommendation or historical pregame claim. Evaluate future model-only and market-only scores
on identical settled games before testing a blend with chronological training.

[Kalshi historical data documentation](https://docs.kalshi.com/getting_started/historical_data)
describes live/archive cutoffs. Backfill must use candles ending before an explicitly fixed NHL pregame
cutoff; final settlement prices cannot substitute for pregame probabilities.
