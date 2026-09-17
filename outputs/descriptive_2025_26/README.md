# Player-season descriptive review

Question: How do position and eligibility definitions change the observed
opportunity and scoring distributions in the saved 2025-26 NHL skater snapshots?
This is descriptive research, not evidence of repeatable talent or prediction.

## Validation

Both raw reports contain 940 unique player IDs for season 20252026, with no
missing IDs or unmatched players. GP agrees across reports; total TOI equals
EV + PP + SH for every player. OT overlaps those buckets and is not added.
The processed dataset retains all 940 players and has no missing total TOI.
Positions: C 298, D 325, L 165, R 152. GP ranges from 1 to 83; median 61.
A player exceeding 82 GP is flagged for inspection, not automatically excluded.
Shooting percentage is missing for 28 players; faceoff percentage for 370.
Missing percentages are retained, not replaced by zero.

Season is present in each CSV. Regular-season game type is the retrieval helper's
default, but the CSVs have no game-type or retrieval metadata. Matching populations
do not independently prove pagination completion. The source is the NHL Stats API
via fastRhockey::nhl_stats_skaters, as documented in the existing acquisition code.
Retrieval dates are unknown; this review did not refresh or edit raw data.

## Findings and interpretation

| Eligibility scenario | Players |
| --- | ---: |
| All skaters | 940 |
| 10+ GP | 778 |
| 20+ GP | 715 |
| 40+ GP | 612 |
| 60+ GP | 488 |
| 250+ TOI minutes | 708 |
| 500+ TOI minutes | 616 |
| 1000+ TOI minutes | 408 |
| 40+ GP and 500+ TOI minutes | 595 |

40+ GP and 500+ minutes yield similar counts but different populations:
17 meet only the GP rule and 21 meet only the TOI rule. These illustrative
thresholds measure different aspects of exposure; none is a validated skill
or reliability threshold. Keep the full population and report sensitivity.

All rates combine all strength states and therefore reflect deployment as well
as outcomes. The mean player rate weights each skater equally; the pooled rate
weights by TOI. Neither adjusts for teammates, opponents, or role. Low exposure
can produce extreme per-60 values; inspect the denominator before interpreting.
Position groups C/L/R/D, F, and All skaters overlap and should not be summed.
Shooting percentage uses the source's fractional scale (0.10 means 10%).

## Reproduce and inspect

Run scripts 03 then 04 from the repository root (commands in NEXT_STEPS.md).
Requires tidyverse; tested with tidyverse 2.0.0, dplyr 1.1.4, readr 2.1.5,
and ggplot2 4.0.0. Full runtime versions are saved in session_info.txt.

- eligibility_summary.csv: retained counts, exposure and mean/pooled scoring rates
- position_distributions.csv: observed/missing counts, mean, SD and quantiles
- gp_toi_overlap.csv: membership differences by position
- missingness.csv: processed column missingness
- exposure_edge_cases.csv: low-GP and above-82-GP records with player IDs
- highest_observed_points_rates.csv: extreme rates with exposure denominators
- distributions.png: distributions for all skaters, colored by position

Next: acquisition provenance and explicit pagination validation, then denominator
and position comparisons. Define the forecast outcome before schedule modeling;
injury status and predictive player impact are not available in this dataset.
