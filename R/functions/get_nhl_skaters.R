# =============================================================================
# Rink Lab
# Function: get_all_nhl_skaters()
#
# Purpose:
# Retrieve a complete season of NHL skater statistics from the NHL Stats API
# using fastRhockey.
#
# Notes:
# - Handles API pagination automatically.
# - Stops when the final page of results is reached.
# - Preserves one row per unique NHL player_id.
# - Does not apply analytical filters such as minimum GP or TOI.
# =============================================================================


get_all_nhl_skaters <- function(
    season,
    report_type = "summary",
    game_type = 2,
    page_size = 100
) {

  # Validate basic inputs
  stopifnot(
    is.character(season),
    length(season) == 1,
    game_type %in% c(1, 2, 3),
    page_size > 0
  )

  pages <- list()
  start <- 0

  message(
    "Retrieving NHL skaters for season ",
    season,
    "..."
  )

  repeat {

page <- fastRhockey::nhl_stats_skaters(
  report_type = report_type,
  season = season,
  game_type = game_type,
  limit = page_size,
  start = start,
  sort = "playerId",
  direction = "ASC"
)
    # No records returned
    if (is.null(page) || nrow(page) == 0) {
      break
    }

    pages[[length(pages) + 1]] <- page

    message(
      "  Retrieved rows ",
      start + 1,
      "–",
      start + nrow(page)
    )

    # A partial page means we've reached the end
    if (nrow(page) < page_size) {
      break
    }

    start <- start + page_size
  }

  if (length(pages) == 0) {
    warning(
      "No NHL skater data returned for season ",
      season,
      "."
    )

    return(tibble::tibble())
  }

  skaters <- dplyr::bind_rows(pages) |>
    dplyr::distinct(player_id, .keep_all = TRUE)

  message(
    "Complete: ",
    nrow(skaters),
    " unique skaters retrieved."
  )

  skaters
}