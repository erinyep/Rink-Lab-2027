# Today — Quinn Short for Quinnificent

[Open the interactive report](2026-10-17_quinn_publishing/index.html)
(open the HTML file in a browser if your editor shows source).
[Text summary](2026-10-17_quinn_publishing/README.md).

The report includes category-gap comparisons, a category-selectable skater chart,
a streamer table with active-slot fit, goalie scenarios, and a roster calendar.
Charts can be saved as SVG. Data, CSVs and the provenance manifest are linked
inside the report. It is a local snapshot; it does not update automatically.

The refreshed ESPN source records Byram as today's `FUTURE_DROP` and Pionk in
the next scoring period's roster. The calendar uses today's roster for today,
then holds the next-period roster constant as a schedule scenario.

No unlocked benched skater has a game today. The saved matchup has PPP tied,
assists +2 and SOG +39. Five saved goalie starts satisfy the three-start minimum;
GAA and SV% trail. These are current category standings, not win probabilities.
Today’s add/drop window has closed. Further acquisitions are future planning
only; remaining daily allowance is unverified. No roster transactions were performed by this report.

## Rebuild

The league-aware daily runner now also builds the report for the team in
`config/fantasy_report.json`. Use `--report-team-id` to override it.
Public-only runs skip the fantasy report.

To rebuild from the current saved inputs into a new, unused directory:

```sh
rink-lab.venv/bin/python scripts/build_today_report.py \
  --bundle data/processed/forecasts/daily_2026-10-17_20261017T173552Z \
  --rules data/raw/espn/snapshots/rules_2027_20261017T173603569187Z \
  --future-roster data/raw/espn/snapshots/future_roster_2027_20261017T173632652100Z \
  --team-id 5 \
  --out reports/today/2026-10-17_quinn_new
```

Refresh the sources after transactions or before relying on a later slate.
Dated generated report directories are local and gitignored, as are source data.

## Useful visuals to add later

In `reports/model_health/`, add weekly error/bias trends by model and fantasy
subgroup, plus probability calibration after the permanent scoreboard exists.
Those charts should use prospective history rather than reconstructed forecasts.
The older machine's frozen history is still needed for the previous trials.
