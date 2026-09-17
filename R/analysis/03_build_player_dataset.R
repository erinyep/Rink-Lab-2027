library(tidyverse)

# -------------------------------------------------------------------------
# Load raw data
# -------------------------------------------------------------------------

nhl <- read_csv(
  "data/raw/nhl/nhl_skaters_2025_26.csv",
  show_col_types = FALSE
)

nhl_toi <- read_csv(
  "data/raw/nhl/nhl_skaters_toi_2025_26.csv",
  show_col_types = FALSE
)

toi_features <- nhl_toi |>
  select(
    player_id,
    time_on_ice,
    ev_time_on_ice,
    pp_time_on_ice,
    sh_time_on_ice,
    ot_time_on_ice,
    shifts,
    shifts_per_game,
    time_on_ice_per_shift
  )

  nhl_players <- nhl |>
  left_join(
    toi_features,
    by = "player_id"
  )

dim(nhl_players)

n_distinct(nhl_players$player_id)

sum(is.na(nhl_players$time_on_ice))

nhl_players |>
  filter(is.na(time_on_ice)) |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    position_code,
    games_played,
    time_on_ice_per_game
  ) |>
  arrange(games_played)

nhl_toi |>
  filter(is.na(time_on_ice)) |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    games_played,
    time_on_ice,
    ev_time_on_ice,
    pp_time_on_ice,
    sh_time_on_ice
  )

sum(is.na(nhl_toi$time_on_ice))    

# Check player_id types in all three objects
class(nhl$player_id)
class(nhl_toi$player_id)
class(toi_features$player_id)

# Recalculate the unmatched population using the exact
# toi_features object that was used in the join
nhl |>
  anti_join(toi_features, by = "player_id") |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    games_played
  ) |>
  arrange(games_played)

# Count them
nhl |>
  anti_join(toi_features, by = "player_id") |>
  nrow()

# Did our TOI selection itself lose any players?
nrow(nhl_toi)
nrow(toi_features)

n_distinct(nhl_toi$player_id)
n_distinct(toi_features$player_id)  
