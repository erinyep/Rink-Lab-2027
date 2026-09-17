# NHL snapshot acquisition

From the repository root:

```sh
Rscript R/tests/test_nhl_pagination.R
Rscript R/analysis/00_refresh_nhl_snapshots.R 20252026
```

Dependencies: httr2, jsonlite, janitor, dplyr, readr, and tidyverse for build
validation. The helper returns a data frame, preserving existing callers, with
retrieval_metadata attached. The refresh script persists that metadata as JSON.

The direct NHL Stats API request records season, game type (2: regular season),
season-level aggregation flags, playerId ascending sort, page offsets, API total,
retrieval times, package versions, and a hash of each saved CSV. Request failures
raise errors. Empty/malformed pages, duplicate or unordered IDs, changing totals,
and unexpected seasons stop retrieval. A run finishes only when retrieved rows
match the stable API total; no deduplication conceals errors. A stable count does
not guarantee that every underlying statistic stayed unchanged during retrieval.

Both reports are fetched before writing. A new timestamped directory under
`data/raw/nhl/snapshots/` contains CSVs and metadata. For 2025-26 the player-season
build runs against the staged pair before publication; its validation output is
stored in the snapshot's `validation/` directory. A failed validation may leave
an unpublished `.staging-*` directory for diagnosis. Other seasons currently
receive retrieval checks only; the build still targets 2025-26.

Existing raw CSVs and processed outputs are not replaced. To build from an
accepted 2025-26 snapshot, run in R from the repository root:

```r
raw_dir <- "data/raw/nhl/snapshots/REPLACE_WITH_SNAPSHOT_DIRECTORY"
output_dir <- "data/processed"
source("R/analysis/03_build_player_dataset.R")
source("R/analysis/04_descriptive_player_season.R")
```

The chosen snapshot's JSON establishes provenance; older flat CSVs have no
retroactively inferred metadata. Legacy exploratory scripts 01/02 still write
the old flat paths and do not save metadata; use script 00 for new acquisition.
Generated snapshots are ignored by Git. Preserve them separately if archiving
exact source responses is required; rerunning the API can reflect corrections.

## Verified run

Live retrieval completed on 2026-09-17 UTC:
`data/raw/nhl/snapshots/20252026_20260917T235510Z`.
Each report returned 940 unique players over 10 pages, matching its API total.
The staged player-season validation passed with zero unmatched players and zero
missing total TOI. Saved metadata and CSV hashes were checked after publication.
Offline tests cover partial and exact-multiple final pages plus eight invalid
response scenarios. The existing flat snapshots were left unchanged.
