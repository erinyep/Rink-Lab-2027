# Run from repository root. Both reports are staged and validated before a
# new timestamped snapshot directory is published; existing raw files stay intact.
source("R/functions/get_nhl_skaters.R")
args <- commandArgs(trailingOnly = TRUE)
season <- if (length(args)) args[[1]] else "20252026"
summary <- get_all_nhl_skaters(season, "summary", game_type = 2)
toi <- get_all_nhl_skaters(season, "timeonice", game_type = 2)
suffix <- paste0(substr(season, 1, 4), "_", substr(season, 7, 8))
parent <- "data/raw/nhl/snapshots"
dir.create(parent, recursive = TRUE, showWarnings = FALSE)
staging <- tempfile(".staging-", tmpdir = parent)
dir.create(staging)
for (report in c("summary", "timeonice")) {
  data <- if (report == "summary") summary else toi
  name <- paste0("nhl_skaters_", if (report == "timeonice") "toi_" else "", suffix, ".csv")
  path <- file.path(staging, name)
  readr::write_csv(data, path)
  metadata <- attr(data, "retrieval_metadata")
  metadata$file <- name
  metadata$md5 <- unname(tools::md5sum(path))
  jsonlite::write_json(metadata, paste0(path, ".metadata.json"), pretty = TRUE, auto_unbox = TRUE)
}
# The current build targets 2025-26. Validate that season with the same production
# checks, directing its processed output into staging instead of overwriting it.
if (season == "20252026") {
  local({
    raw_dir <- staging
    output_dir <- file.path(staging, "validation")
    source("R/analysis/03_build_player_dataset.R", local = TRUE)
  })
}
final <- file.path(parent, paste0(season, "_", format(Sys.time(), tz = "UTC", "%Y%m%dT%H%M%SZ")))
if (dir.exists(final) || !file.rename(staging, final)) stop("Cannot publish snapshot: ", staging)
message("Snapshot saved: ", final)
message("Metadata records request game type, retrieval times, page counts and file hashes.")
