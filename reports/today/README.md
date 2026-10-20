# Today — Quinn Short for Quinnificent — October 20, 2026

[Interactive local report](2026-10-20_quinn_publishing_v2/index.html) · [Text summary](2026-10-20_quinn_publishing_v2/README.md) · [Published report](https://erinyep.github.io/Rink-Lab-2027/report/)

Today's report uses the October 20 frozen 11-game forecasts, ESPN roster/standings captured this morning, and refreshed league rules/next-period roster. The next-period roster has no additions or removals. One saved goalie start is recorded against a three-start minimum. An opponent GAA is unavailable because ESPN supplied a nonfinite rate; it is not treated as an advantage.

The report flags Gavin McKenna for an available Forward slot after benching off-day/injury-excluded players; confirm he dresses before acting. No lineup changes or transactions were performed. Streamers remain a watchlist, and remaining daily acquisition allowance is unverified.

Charts, category comparisons and the roster calendar are saved snapshots, not live updates. Historical October 17 pages are preserved under `docs/archive/2026-10-17/`.

## Rebuild

The league-aware runner `scripts/run_daily_forecasts.py` builds dated reports for the team in `config/fantasy_report.json`. Public-only runs skip the fantasy report. To publish a reviewed report:

```sh
rink-lab.venv/bin/python scripts/prepare_github_report.py \
  --report reports/today/2026-10-20_quinn_publishing_v2
```

Refresh inputs after roster changes; dated generated directories and private source data remain gitignored.
