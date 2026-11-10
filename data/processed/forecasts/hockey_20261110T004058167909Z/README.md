# Kalshi public NHL market snapshot

Captured at `2026-11-10T00:40:58Z` (November 9 at 7:40 p.m. Eastern) from Kalshi's public open-markets endpoint. Pagination completed for all seven requested series. The exact API responses and their checksums are in `data/raw/kalshi/snapshots/hockey_20261110T004058167909Z/`.

The capture contains 609 open contracts across five series. No open NHL saves or anytime-goal contracts were returned. See `series_coverage.csv` for per-series counts, two-sided quote coverage, and median spreads; `markets.csv` contains each quote and timestamp.

This is a current market snapshot, not a historical pregame capture for the November 9 slate. Contracts are intentionally unmapped to NHL games or players and are not forecast inputs. Quoted midpoints are not validated probabilities, and no trading endpoints or account data were used.
