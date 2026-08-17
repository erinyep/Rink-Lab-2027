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