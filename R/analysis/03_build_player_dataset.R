library(tidyverse)

if (!exists("raw_dir", inherits = FALSE)) raw_dir <- "data/raw/nhl"
if (!exists("output_dir", inherits = FALSE)) output_dir <- "data/processed"

# -------------------------------------------------------------------------
# 1. Load raw data snapshots
# -------------------------------------------------------------------------

nhl_summary <- read_csv(
  file.path(raw_dir, "nhl_skaters_2025_26.csv"),
  show_col_types = FALSE
)

nhl_toi <- read_csv(
  file.path(raw_dir, "nhl_skaters_toi_2025_26.csv"),
  show_col_types = FALSE
)

# Fail before saving if either snapshot has invalid keys or incompatible data.
# game_type is absent from these CSVs; regular season is the retrieval default,
# not an independently verified property of the saved snapshots.
check <- function(ok, message) {
  if (!isTRUE(ok)) stop(message, call. = FALSE)
}
for (report in list(nhl_summary, nhl_toi)) {
  check(nrow(report) > 0, "Empty raw report")
  check(!anyNA(report$player_id) && !anyDuplicated(report$player_id),
        "Missing or duplicate player_id in raw report")
  check(all(report$season_id == 20252026), "Unexpected or missing season_id")
  check(all(report$position_code %in% c("C", "L", "R", "D")),
        "Unexpected skater position")
  check(all(is.finite(report$games_played) & report$games_played >= 1 &
              report$games_played == floor(report$games_played)), "Invalid GP")
}
check(all(nhl_summary$points == nhl_summary$goals + nhl_summary$assists),
      "Points do not equal goals plus assists")
for (field in c("goals", "assists", "points", "shots")) {
  check(all(is.finite(nhl_summary[[field]]) & nhl_summary[[field]] >= 0),
        paste("Invalid", field))
}
for (field in c("time_on_ice", "ev_time_on_ice", "pp_time_on_ice",
                "sh_time_on_ice", "ot_time_on_ice")) {
  check(all(is.finite(nhl_toi[[field]]) & nhl_toi[[field]] >= 0),
        paste("Invalid", field))
}
check(all(nhl_toi$time_on_ice > 0), "Nonpositive total TOI")
check(all(abs(nhl_toi$time_on_ice - nhl_toi$ev_time_on_ice -
                nhl_toi$pp_time_on_ice - nhl_toi$sh_time_on_ice) < 0.01),
      "Total TOI does not equal EV + PP + SH (OT overlaps these buckets)")
matched <- inner_join(nhl_summary, nhl_toi,
                      by = c("player_id", "season_id"), suffix = c(".summary", ".toi"),
                      relationship = "one-to-one")
check(all(matched$games_played.summary == matched$games_played.toi),
      "Reports disagree on GP; refresh aligned snapshots")
# API averages are rounded: allow 0.01 seconds, not exact floating equality.
check(all(abs(matched$time_on_ice_per_game.summary -
                matched$time_on_ice / matched$games_played.toi) < 0.01),
      "Summary TOI/game disagrees with total TOI / GP")
check(all(abs(nhl_toi$time_on_ice_per_game -
                nhl_toi$time_on_ice / nhl_toi$games_played) < 0.01),
      "TOI report average disagrees with total TOI / GP")

# -------------------------------------------------------------------------
# 2. Data-quality checks before building the analysis dataset
# -------------------------------------------------------------------------

cat("Summary rows:", nrow(nhl_summary), "\n")
cat("Summary unique player_id:", n_distinct(nhl_summary$player_id), "\n")
cat("Summary missing player_id:", sum(is.na(nhl_summary$player_id)), "\n")

cat("TOI rows:", nrow(nhl_toi), "\n")
cat("TOI unique player_id:", n_distinct(nhl_toi$player_id), "\n")
cat("TOI missing player_id:", sum(is.na(nhl_toi$player_id)), "\n")

summary_only <- nhl_summary |>
  anti_join(nhl_toi, by = "player_id")

toi_only <- nhl_toi |>
  anti_join(nhl_summary, by = "player_id")

cat("Summary-only players:", nrow(summary_only), "\n")
cat("TOI-only players:", nrow(toi_only), "\n")

# Show the players missing from the TOI report so they are not silently dropped.
summary_only |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    position_code,
    games_played,
    goals,
    assists,
    points
  ) |>
  arrange(games_played) |>
  print(n = 20)

# -------------------------------------------------------------------------
# 3. Build analysis-ready player-season dataset
# -------------------------------------------------------------------------

# Keep the full season summary population. Match useful TOI fields to the
# summary report without dropping summary players who do not appear in the TOI
# report. The resulting merged table is intentionally a left join so the raw
# player population is preserved.

toi_features <- nhl_toi |>
  transmute(
    player_id,
    season_id,
    toi_seconds = time_on_ice,
    toi_minutes = time_on_ice / 60,
    ev_toi_seconds = ev_time_on_ice,
    ev_toi_minutes = ev_time_on_ice / 60,
    pp_toi_seconds = pp_time_on_ice,
    pp_toi_minutes = pp_time_on_ice / 60,
    sh_toi_seconds = sh_time_on_ice,
    sh_toi_minutes = sh_time_on_ice / 60,
    ot_toi_seconds = ot_time_on_ice,
    ot_toi_minutes = ot_time_on_ice / 60,
    shifts,
    shifts_per_game,
    time_on_ice_per_shift,
    time_on_ice_per_game_seconds = time_on_ice_per_game,
    time_on_ice_per_game_minutes = time_on_ice_per_game / 60
  )

player_season <- nhl_summary |>
  left_join(toi_features, by = c("player_id", "season_id"),
            relationship = "one-to-one") |>
  mutate(
    goals_per_game = if_else(games_played > 0, goals / games_played, NA_real_),
    assists_per_game = if_else(games_played > 0, assists / games_played, NA_real_),
    points_per_game = if_else(games_played > 0, points / games_played, NA_real_),
    shots_per_game = if_else(games_played > 0, shots / games_played, NA_real_),
    goals_per_60 = if_else(toi_minutes > 0, goals / toi_minutes * 60, NA_real_),
    assists_per_60 = if_else(toi_minutes > 0, assists / toi_minutes * 60, NA_real_),
    points_per_60 = if_else(toi_minutes > 0, points / toi_minutes * 60, NA_real_),
    shots_per_60 = if_else(toi_minutes > 0, shots / toi_minutes * 60, NA_real_),
    toi_minutes_per_game = if_else(games_played > 0, toi_minutes / games_played, NA_real_)
  )

# -------------------------------------------------------------------------
# 4. Final validation and output
# -------------------------------------------------------------------------

cat("Player-season rows:", nrow(player_season), "\n")
cat("Player-season unique player_id:", n_distinct(player_season$player_id), "\n")
cat("Missing TOI rows:", sum(is.na(player_season$toi_minutes)), "\n")
cat("Missing shooting_pct rows:", sum(is.na(player_season$shooting_pct)), "\n")

player_season |>
  summarise(
    min_games_played = min(games_played, na.rm = TRUE),
    median_games_played = median(games_played, na.rm = TRUE),
    max_games_played = max(games_played, na.rm = TRUE),
    avg_toi_minutes = mean(toi_minutes, na.rm = TRUE),
    median_toi_minutes = median(toi_minutes, na.rm = TRUE)
  )

check(nrow(player_season) == nrow(nhl_summary), "Join changed summary population")
check(!anyDuplicated(player_season$player_id), "Duplicate processed player_id")
rate_fields <- c("goals_per_game", "assists_per_game", "points_per_game",
                 "shots_per_game", "goals_per_60", "assists_per_60",
                 "points_per_60", "shots_per_60")
check(all(vapply(player_season[rate_fields],
                 function(x) all(is.na(x) | is.finite(x)), logical(1))),
      "Nonfinite rate in processed dataset")

# Save the processed dataset for later analyses.
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
write_csv(
  player_season,
  file.path(output_dir, "nhl_player_season_2025_26.csv")
)

message("Processed dataset saved to ", output_dir)
