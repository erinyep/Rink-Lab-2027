# Retrieve season-level skaters directly so API total and transport errors remain
# visible. fastRhockey's wrapper maps both errors and empty results to NULL and
# discards total, so it cannot supply independent completion evidence.
fetch_nhl_skater_page <- function(season, report_type, game_type, page_size, start) {
  url <- paste0("https://api.nhle.com/stats/rest/en/skater/", report_type)
  response <- httr2::request(url) |>
    httr2::req_url_query(
      isAggregate = "false", isGame = "false",
      sort = '[{"property":"playerId","direction":"ASC"}]',
      start = start, limit = page_size,
      cayenneExp = paste0("gameTypeId=", game_type, " and seasonId=", season)
    ) |>
    httr2::req_timeout(60) |>
    httr2::req_retry(max_tries = 3) |>
    httr2::req_perform()
  jsonlite::fromJSON(httr2::resp_body_string(response), flatten = TRUE)
}

get_all_nhl_skaters <- function(season, report_type = "summary", game_type = 2,
                                page_size = 100,
                                fetch_page = fetch_nhl_skater_page) {
  check <- function(ok, message) if (!isTRUE(ok)) stop(message, call. = FALSE)
  integer_scalar <- function(x) is.numeric(x) && length(x) == 1 &&
    is.finite(x) && x == floor(x)
  check(is.character(season) && length(season) == 1 && !is.na(season) &&
          grepl("^[0-9]{8}$", season), "season must be an eight-digit string")
  check(as.integer(substr(season, 5, 8)) == as.integer(substr(season, 1, 4)) + 1,
        "season must contain consecutive years")
  check(is.character(report_type) && length(report_type) == 1 &&
          !is.na(report_type) && grepl("^[A-Za-z]+$", report_type), "Invalid report_type")
  check(integer_scalar(game_type) && game_type %in% 1:3, "Invalid game_type")
  check(integer_scalar(page_size) && page_size >= 1 && page_size <= 100,
        "page_size must be an integer from 1 to 100")
  started <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  pages <- list()
  log <- list()
  start <- 0
  expected <- NULL
  previous_id <- -Inf
  repeat {
    raw <- fetch_page(season, report_type, game_type, page_size, start)
    check(is.list(raw) && all(c("data", "total") %in% names(raw)),
          "Malformed response: data and total are required")
    check(integer_scalar(raw$total) && raw$total >= 0, "Invalid API total")
    if (is.null(expected)) expected <- raw$total
    check(raw$total == expected, "API total changed during pagination; retry snapshot")
    check(expected > 0, "Empty population; no snapshot will be accepted")
    check(is.data.frame(raw$data), "Empty or malformed page before expected total")
    page <- janitor::clean_names(raw$data)
    needed <- min(page_size, expected - start)
    check(nrow(page) == needed, "Page size disagrees with API total; incomplete retrieval")
    check(all(c("player_id", "season_id", "games_played", "position_code") %in%
                names(page)), "Missing required report columns")
    check(is.numeric(page$player_id) && all(is.finite(page$player_id)) &&
            all(page$player_id == floor(page$player_id)) &&
            all(diff(c(previous_id, page$player_id)) > 0),
          "Duplicate, unordered, or invalid player IDs across pages")
    check(all(page$season_id == as.numeric(season)), "Unexpected season in response")
    check(all(page$position_code %in% c("C", "L", "R", "D")), "Invalid skater position")
    check(all(is.finite(page$games_played) & page$games_played >= 1), "Invalid GP")
    pages[[length(pages) + 1]] <- page
    log[[length(log) + 1]] <- data.frame(start = start, rows = nrow(page), total = raw$total)
    previous_id <- tail(page$player_id, 1)
    start <- start + nrow(page)
    message(report_type, ": ", start, "/", expected, " rows")
    if (start == expected) break
  }
  skaters <- dplyr::bind_rows(pages)
  check(nrow(skaters) == expected && !anyDuplicated(skaters$player_id),
        "Final row count or uniqueness check failed")
  attr(skaters, "retrieval_metadata") <- list(
    source = paste0("https://api.nhle.com/stats/rest/en/skater/", report_type),
    method = "Direct NHL Stats API via httr2; JSON parsed by jsonlite",
    season_id = season, game_type = game_type, report_type = report_type,
    isAggregate = FALSE, isGame = FALSE, sort = "playerId ASC",
    started_at_utc = started, completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
    page_size = page_size, pages = dplyr::bind_rows(log),
    api_total = expected, rows = nrow(skaters), unique_players = dplyr::n_distinct(skaters$player_id),
    completion = "Retrieved API total with stable total and strictly increasing unique IDs",
    r_version = R.version.string,
    packages = lapply(c("httr2", "jsonlite", "janitor", "dplyr", "readr"),
                      function(x) list(package = x, version = as.character(utils::packageVersion(x))))
  )
  skaters
}
