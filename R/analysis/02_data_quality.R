# =============================================================================
# Rink Lab
# 02_data_quality.R
#
# Purpose:
# Validate the 2025-26 NHL skater summary dataset, understand the observed
# player population, evaluate games-played thresholds, investigate traded-player
# representation, and validate the NHL Stats time-on-ice report before joining
# it to the summary data.
#
# Important findings so far:
# - Summary report contains 935 unique skaters.
# - No duplicate or missing player IDs were found in the summary report.
# - NHL Stats report populations are not identical:
#     summary = 935 unique skaters
#     timeonice = 927 unique skaters
#     summary-only = 13
#     timeonice-only = 5
# - Multiple teams are represented in team_abbrevs as comma-separated values.
# - TOI fields are stored in seconds.
# - Total TOI = EV TOI + PP TOI + SH TOI for all rows in the timeonice report.
# - ot_time_on_ice overlaps with the strength-state totals and must NOT be
#   added to EV + PP + SH when calculating total TOI.
# =============================================================================

library(tidyverse)

# The reusable NHL retrieval function should be available to this script.
# Adjust this path only if the project structure changes.
source("R/functions/get_nhl_skaters.R")


# =============================================================================
# 1. LOAD RAW SUMMARY DATA
# =============================================================================

nhl <- read_csv(
  "data/raw/nhl/nhl_skaters_2025_26.csv",
  show_col_types = FALSE
)


# =============================================================================
# 2. BASIC DATASET VALIDATION
# =============================================================================

# Dimensions
dim(nhl)

# Unique / missing player IDs
nrow(nhl)
n_distinct(nhl$player_id)
sum(is.na(nhl$player_id))

# Duplicate player IDs
nhl |>
  count(player_id) |>
  filter(n > 1)

# Missingness by variable
missingness <- nhl |>
  summarise(
    across(
      everything(),
      ~ sum(is.na(.))
    )
  ) |>
  pivot_longer(
    everything(),
    names_to = "variable",
    values_to = "missing"
  ) |>
  arrange(desc(missing))

missingness


# =============================================================================
# 3. PLAYER POPULATION
# =============================================================================

# Position distribution
nhl |>
  count(position_code)

# Games-played distribution
summary(nhl$games_played)

# Visualize games played
nhl |>
  ggplot(aes(x = games_played)) +
  geom_histogram(binwidth = 5) +
  labs(
    title = "Games Played Distribution",
    subtitle = "NHL skaters, 2025-26 regular season",
    x = "Games Played",
    y = "Number of Players"
  ) +
  theme_minimal()


# =============================================================================
# 4. MISSING-VALUE INVESTIGATION
# =============================================================================

# Shooting percentage:
# Inspect rather than automatically replacing missing values.
nhl |>
  filter(is.na(shooting_pct)) |>
  select(
    skater_full_name,
    position_code,
    games_played,
    goals,
    shots,
    shooting_pct
  ) |>
  arrange(desc(games_played))

# Faceoff percentage:
# Missingness is expected to vary substantially by position.
nhl |>
  group_by(position_code) |>
  summarise(
    players = n(),
    missing_faceoff_pct = sum(is.na(faceoff_win_pct)),
    pct_missing = mean(is.na(faceoff_win_pct)),
    .groups = "drop"
  )


# =============================================================================
# 5. GP THRESHOLD SENSITIVITY
# =============================================================================

# Do not filter the raw population.
# These thresholds are being compared to understand how eligibility rules
# change the population used in later analyses.

gp_thresholds <- tibble(
  threshold = c(1, 10, 20, 40, 60),
  players = c(
    sum(nhl$games_played >= 1),
    sum(nhl$games_played >= 10),
    sum(nhl$games_played >= 20),
    sum(nhl$games_played >= 40),
    sum(nhl$games_played >= 60)
  )
) |>
  mutate(
    pct_of_population = players / nrow(nhl)
  )

gp_thresholds

ggplot(
  gp_thresholds,
  aes(x = factor(threshold), y = players)
) +
  geom_col() +
  geom_text(
    aes(label = players),
    vjust = -0.5
  ) +
  labs(
    title = "How Eligibility Thresholds Change the NHL Player Population",
    subtitle = "2025-26 regular season",
    x = "Minimum Games Played",
    y = "Players Included"
  ) +
  theme_minimal()


# =============================================================================
# 6. SUSPICIOUS / EDGE-CASE VALUES
# =============================================================================

# Players exceeding 82 GP.
# Investigate rather than treating >82 as an automatic data error.
nhl |>
  filter(games_played > 82) |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    position_code,
    games_played,
    goals,
    assists,
    points
  )

# Broad numeric range check
nhl |>
  summarise(
    min_gp = min(games_played),
    max_gp = max(games_played),
    min_goals = min(goals),
    max_goals = max(goals),
    min_assists = min(assists),
    max_assists = max(assists),
    min_points = min(points),
    max_points = max(points),
    min_shots = min(shots),
    max_shots = max(shots),
    min_shooting_pct = min(shooting_pct, na.rm = TRUE),
    max_shooting_pct = max(shooting_pct, na.rm = TRUE),
    min_toi_game_seconds = min(time_on_ice_per_game),
    max_toi_game_seconds = max(time_on_ice_per_game)
  )


# =============================================================================
# 7. TEAM / TRADED-PLAYER REPRESENTATION
# =============================================================================

# The NHL summary report can represent multiple teams in a single season-level
# player row using comma-separated abbreviations.

multi_team_players <- nhl |>
  filter(str_detect(team_abbrevs, ",")) |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    games_played,
    goals,
    assists,
    points
  ) |>
  arrange(skater_full_name)

multi_team_players

# Inspect all observed team-abbreviation combinations.
sort(unique(nhl$team_abbrevs))

nhl |>
  count(team_abbrevs, sort = TRUE) |>
  print(n = Inf)


# =============================================================================
# 8. RETRIEVE AND INSPECT TIME-ON-ICE REPORT
# =============================================================================

nhl_toi <- get_all_nhl_skaters(
  season = "20252026",
  report_type = "timeonice"
)

dim(nhl_toi)
names(nhl_toi)
glimpse(nhl_toi)

# NOTE:
# Once saved, future analysis scripts should read the raw TOI snapshot from disk
# instead of depending on an object from an earlier interactive R session.
#
# Save after confirming the retrieval is the intended raw snapshot:
#
 write_csv(
  nhl_toi,
  "data/raw/nhl/nhl_skaters_toi_2025_26.csv"
 )


# =============================================================================
# 9. COMPARE SUMMARY VS. TIME-ON-ICE COVERAGE
# =============================================================================

# Summary players absent from the timeonice report.
missing_from_toi <- nhl |>
  anti_join(
    nhl_toi,
    by = "player_id"
  ) |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    position_code,
    games_played,
    goals,
    assists,
    points,
    time_on_ice_per_game
  ) |>
  arrange(games_played)

missing_from_toi
nrow(missing_from_toi)

# Timeonice players absent from the summary report.
missing_from_summary <- nhl_toi |>
  anti_join(
    nhl,
    by = "player_id"
  ) |>
  select(
    player_id,
    skater_full_name,
    team_abbrevs,
    position_code,
    games_played,
    time_on_ice
  ) |>
  arrange(games_played)

missing_from_summary
nrow(missing_from_summary)

# Coverage summary
tibble(
  report = c(
    "summary",
    "timeonice",
    "summary_only",
    "timeonice_only"
  ),
  unique_players = c(
    n_distinct(nhl$player_id),
    n_distinct(nhl_toi$player_id),
    nrow(missing_from_toi),
    nrow(missing_from_summary)
  )
)


# =============================================================================
# 10. VALIDATE TIME-ON-ICE DEFINITIONS
# =============================================================================

# TOI values are stored in seconds.
#
# Validate the mutually exclusive strength-state relationship:
#
# total TOI = even-strength TOI + power-play TOI + shorthanded TOI
#
# Overtime TOI is NOT added here. Earlier validation showed that adding
# ot_time_on_ice double-counts time.

toi_validation <- nhl_toi |>
  mutate(
    strength_toi =
      ev_time_on_ice +
      pp_time_on_ice +
      sh_time_on_ice,
    difference =
      time_on_ice - strength_toi
  ) |>
  summarise(
    min_difference = min(difference),
    max_difference = max(difference),
    mean_difference = mean(difference),
    nonzero_differences = sum(difference != 0)
  )

toi_validation


# =============================================================================
# 11. CURRENT DATA-QUALITY CONCLUSIONS
# =============================================================================

# 1. The summary dataset is internally consistent at the player-ID level.
# 2. Low-GP players are legitimate members of the raw observed population and
#    should not be removed from raw data.
# 3. GP eligibility thresholds materially change the analytical population.
# 4. Missing faceoff percentage should not be interpreted as zero.
# 5. Multi-team players remain one season-level player row; team_abbrevs can
#    contain comma-separated team codes.
# 6. Separate NHL Stats reports can contain different player populations.
# 7. TOI is measured in seconds in the timeonice report.
# 8. Total TOI is exactly EV + PP + SH TOI in the retrieved report.
# 9. OT TOI is overlapping information and must not be added to those three
#    components when constructing total TOI.
# 10. When the summary and TOI reports are joined later, preserve the summary
#     population and explicitly inspect unmatched TOI rather than silently
#     dropping players with an inner join.
#
# Remaining Phase 1 validation:
# - Confirm position coding against NHL source data.
# - Examine the total-TOI distribution.
# - Evaluate TOI-based eligibility thresholds.
# - Build and validate the processed player-season dataset.

write_csv(
  nhl_toi,
  "data/raw/nhl/nhl_skaters_toi_2025_26.csv"
)