# Purpose: exploratory analysis of NHL player landscape

library(tidyverse)
library(fastRhockey)

source("R/functions/get_nhl_skaters.R")

season <- "20252026"

nhl_skaters <- get_all_nhl_skaters(season)

dim(nhl_skaters)

# Raw NHL Stats API "summary" report.
# Retrieved via fastRhockey::nhl_stats_skaters().
# Do not manually modify the saved raw file.
write_csv(
  nhl_skaters,
  "data/raw/nhl/nhl_skaters_2025_26.csv"
)

# Position counts
nhl_skaters |>
  count(position_code)

# Games played distribution
summary(nhl_skaters$games_played)

# Check IDs and duplicates
sum(is.na(nhl_skaters$player_id))
n_distinct(nhl_skaters$player_id)
nrow(nhl_skaters)

# Inspect players with the fewest games
nhl_skaters |>
  arrange(games_played) |>
  select(
    skater_full_name,
    team_abbrevs,
    position_code,
    games_played,
    goals,
    assists,
    points
  ) |>
  head(20)
