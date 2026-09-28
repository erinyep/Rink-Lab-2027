# Run from repository root. Independent timestamped snapshots; no legacy overwrite.
source("R/functions/get_nhl_skaters.R")
args <- commandArgs(trailingOnly = TRUE)
season <- if (length(args)) args[[1]] else "20252026"
reports <- list(
  summary = get_all_nhl_skaters(season, "summary"),
  timeonice = get_all_nhl_skaters(season, "timeonice"),
  realtime = get_all_nhl_skaters(season, "realtime"),
  goalies = get_all_nhl_players(season, "summary", population = "goalie")
)
check <- function(ok, msg) if (!isTRUE(ok)) stop(msg)
counts <- function(x, fields) {
  check(all(fields %in% names(x)), "Missing required count columns")
  for (field in fields) check(all(is.finite(x[[field]]) & x[[field]] >= 0 &
                                  x[[field]] == floor(x[[field]])),
                              paste("Invalid count:", field))
}
s <- reports$summary
t <- reports$timeonice
r <- reports$realtime
g <- reports$goalies
counts(r, c("hits", "blocked_shots"))
counts(g, c("games_played", "games_started", "wins", "saves", "shots_against",
            "goals_against", "shutouts"))
# Preserve source inconsistencies; never repair raw counts or silently drop players.
# Retrieval completeness is distinct from analytical acceptance of goalie records.
goalie_identity_ok <- g$saves + g$goals_against == g$shots_against
if (any(!goalie_identity_ok)) warning(sum(!goalie_identity_ok),
  " goalie rows fail SA=SV+GA; flagged and ineligible for valuation pending investigation")
check(all(g$games_started <= g$games_played & g$wins <= g$games_played &
            g$shutouts <= g$games_played), "Invalid goalie workload")
check(all(is.finite(g$time_on_ice) & g$time_on_ice > 0), "Invalid goalie TOI")
sa <- g$shots_against > 0
check(all(abs(g$save_pct[sa] - g$saves[sa] / g$shots_against[sa]) < 0.00002),
      "Goalie save percentage disagrees with counts")
check(all(abs(g$goals_against_average - 3600 * g$goals_against / g$time_on_ice) < 0.00002),
      "Goalie GAA disagrees with counts and seconds")
for (other in list(t, r)) {
  check(setequal(s$player_id, other$player_id), "Skater report coverage differs; inspect before joining")
  check(all(s$games_played == other$games_played[match(s$player_id, other$player_id)]),
        "Skater GP differs across reports")
}
parent <- "data/raw/nhl/snapshots"
dir.create(parent, recursive = TRUE, showWarnings = FALSE)
staging <- tempfile(".staging-fantasy-", tmpdir = parent)
dir.create(staging)
suffix <- paste0(substr(season, 1, 4), "_", substr(season, 7, 8))
files <- c(summary = paste0("nhl_skaters_", suffix, ".csv"),
           timeonice = paste0("nhl_skaters_toi_", suffix, ".csv"),
           realtime = paste0("nhl_skaters_realtime_", suffix, ".csv"),
           goalies = paste0("nhl_goalies_", suffix, ".csv"))
for (name in names(reports)) {
  path <- file.path(staging, files[[name]])
  readr::write_csv(reports[[name]], path)
  metadata <- attr(reports[[name]], "retrieval_metadata")
  metadata$file <- files[[name]]
  metadata$md5 <- unname(tools::md5sum(path))
  jsonlite::write_json(metadata, paste0(path, ".metadata.json"), pretty = TRUE, auto_unbox = TRUE)
}
if (season == "20252026") {
  local({
    raw_dir <- staging
    output_dir <- file.path(staging, "validation")
    source("R/analysis/03_build_player_dataset.R", local = TRUE)
  })
}
# Record missingness and extremes rather than silently removing low-GP players.
audit <- dplyr::bind_rows(lapply(names(reports), function(name) {
  x <- reports[[name]]
  dplyr::bind_rows(lapply(names(x), function(field) data.frame(
    report = name, column = field, rows = nrow(x), missing = sum(is.na(x[[field]])),
    minimum = if (is.numeric(x[[field]]) && any(!is.na(x[[field]]))) min(x[[field]], na.rm = TRUE) else NA_real_,
    maximum = if (is.numeric(x[[field]]) && any(!is.na(x[[field]]))) max(x[[field]], na.rm = TRUE) else NA_real_
  )))
}))
readr::write_csv(audit, file.path(staging, "column_audit.csv"))
final <- file.path(parent, paste0("fantasy_", season, "_", format(Sys.time(), tz = "UTC", "%Y%m%dT%H%M%SZ")))
check(!dir.exists(final) && file.rename(staging, final), "Cannot publish staged snapshot")
# Processed historical worksheet: observed stats only, no forecast or fantasy rank.
out <- file.path("data/processed/fantasy", basename(final))
dir.create(out, recursive = TRUE, showWarnings = FALSE)
skaters <- dplyr::left_join(s, dplyr::select(r, player_id, season_id, hits, blocked_shots),
                           by = c("player_id", "season_id"), relationship = "one-to-one")
skaters$source_snapshot <- final
g$source_snapshot <- final
g$save_identity_ok <- goalie_identity_ok
g$eligible_for_valuation <- goalie_identity_ok
g$source_count_residual <- g$saves + g$goals_against - g$shots_against
readr::write_csv(skaters, file.path(out, "historical_skaters.csv"))
readr::write_csv(g, file.path(out, "historical_goalies.csv"))
readr::write_csv(g[!goalie_identity_ok, ], file.path(out, "goalie_validation_exceptions.csv"))
message("Snapshot: ", final)
message("Historical worksheets: ", out)
