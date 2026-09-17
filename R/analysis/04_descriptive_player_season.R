# Question: How do position and eligibility definitions change the observed
# distributions of opportunity and scoring? Descriptive, not a talent estimate.
# Run from repository root after 03_build_player_dataset.R.
library(tidyverse)

players <- read_csv("data/processed/nhl_player_season_2025_26.csv",
                    show_col_types = FALSE)
stopifnot(nrow(players) > 0, !anyNA(players$player_id),
          !anyDuplicated(players$player_id), all(players$season_id == 20252026))
out <- "outputs/descriptive_2025_26"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
save_table <- function(x, name) write_csv(x, file.path(out, paste0(name, ".csv")))

# These are sensitivity scenarios, not recommended eligibility cutoffs.
# All players remain in the processed dataset. Missing TOI fails TOI eligibility.
scenarios <- tribble(
  ~population, ~min_gp, ~min_toi,
  "All skaters", 1, 0,
  "GP >= 10", 10, 0,
  "GP >= 20", 20, 0,
  "GP >= 40", 40, 0,
  "GP >= 60", 60, 0,
  "TOI >= 250 min", 1, 250,
  "TOI >= 500 min", 1, 500,
  "TOI >= 1000 min", 1, 1000,
  "GP >= 40 and TOI >= 500 min", 40, 500
)
cohorts <- pmap_dfr(scenarios, function(population, min_gp, min_toi) {
  players |>
    filter(games_played >= min_gp,
           min_toi == 0 | (!is.na(toi_minutes) & toi_minutes >= min_toi)) |>
    mutate(population = population)
})
coverage <- cohorts |>
  group_by(population) |>
  summarise(players = n(), share_of_all_players = n() / nrow(.env$players),
            median_gp = median(games_played),
            median_toi_minutes = median(toi_minutes, na.rm = TRUE),
            mean_player_points_per_60 = mean(points_per_60, na.rm = TRUE),
            # Pooled rate uses the same complete cases for numerator/denominator.
            pooled_points_per_60 = 60 * sum(points[!is.na(toi_minutes)]) /
              sum(toi_minutes, na.rm = TRUE), .groups = "drop")
save_table(coverage, "eligibility_summary")

# Include all skaters, individual positions, and forwards as separate groups.
# These groups overlap and must not be summed together.
groups <- bind_rows(
  cohorts |> mutate(position_group = position_code),
  cohorts |> mutate(position_group = "All skaters"),
  cohorts |> filter(position_code != "D") |> mutate(position_group = "F")
)
metrics <- c("games_played", "toi_minutes", "toi_minutes_per_game", "goals",
             "assists", "points", "shots", "shooting_pct", "plus_minus",
             "penalty_minutes", "pp_points", "sh_points", "points_per_game",
             "goals_per_60", "assists_per_60", "points_per_60", "shots_per_60")
# Guard empty/all-missing groups rather than reporting Inf extrema.
stat <- function(x, f, ...) if (all(is.na(x))) NA_real_ else f(x, ..., na.rm = TRUE)
descriptive <- groups |>
  select(population, position_group, all_of(metrics)) |>
  pivot_longer(all_of(metrics), names_to = "metric", values_to = "value") |>
  group_by(population, position_group, metric) |>
  summarise(players = n(), observed = sum(!is.na(value)), missing = sum(is.na(value)),
            mean = stat(value, mean), sd = stat(value, sd),
            min = stat(value, min), p25 = stat(value, quantile, probs = .25),
            median = stat(value, median), p75 = stat(value, quantile, probs = .75),
            p90 = stat(value, quantile, probs = .9), max = stat(value, max),
            .groups = "drop")
save_table(descriptive, "position_distributions")
save_table(players |> summarise(across(everything(), ~sum(is.na(.x)))) |>
             pivot_longer(everything(), names_to = "variable", values_to = "missing"),
           "missingness")
save_table(players |> filter(games_played > 82 | games_played < 10) |>
             select(player_id, skater_full_name, team_abbrevs, position_code,
                    games_played, toi_minutes, points, points_per_60), "exposure_edge_cases")
# Show largest observed rates with denominators; no automatic outlier removal.
save_table(players |> arrange(desc(points_per_60)) |>
             select(player_id, skater_full_name, position_code, games_played,
                    toi_minutes, points, points_per_60) |> slice_head(n = 20),
           "highest_observed_points_rates")
save_table(players |>
             mutate(gp_40 = games_played >= 40,
                    toi_500 = !is.na(toi_minutes) & toi_minutes >= 500) |>
             count(position_code, gp_40, toi_500), "gp_toi_overlap")

plot <- players |>
  select(position_code, games_played, toi_minutes, points_per_60, shots_per_60) |>
  pivot_longer(-position_code, names_to = "metric", values_to = "value") |>
  ggplot(aes(value, fill = position_code)) +
  geom_histogram(bins = 30, position = "stack", na.rm = TRUE) +
  facet_wrap(~metric, scales = "free", ncol = 2) +
  labs(title = "Opportunity and observed scoring rates",
       subtitle = paste("2025-26 saved NHL skater snapshots;", nrow(players), "players retained"),
       x = NULL, y = "Players", fill = "Position",
       caption = "All-strength rates; small TOI denominators can produce extreme rates.") +
  theme_minimal(base_size = 12)
ggsave(file.path(out, "distributions.png"), plot, width = 11, height = 7, dpi = 150)
writeLines(capture.output(sessionInfo()), file.path(out, "session_info.txt"))
print(coverage, n = Inf)
message("Descriptive outputs saved to ", out)
