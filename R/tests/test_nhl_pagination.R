# Offline contract tests; no network or raw-file writes.
source("R/functions/get_nhl_skaters.R")
page <- function(ids, total = 3) list(total = total, data = data.frame(
  playerId = ids, seasonId = 20252026, gamesPlayed = 1, positionCode = "C"))
run <- function(responses) {
  i <- 0
  get_all_nhl_skaters("20252026", page_size = 2, fetch_page = function(...) {
    i <<- i + 1
    if (i > length(responses)) stop("Unexpected extra request")
    responses[[i]]
  })
}
x <- run(list(page(1:2), page(3)))
stopifnot(nrow(x) == 3, attr(x, "retrieval_metadata")$api_total == 3)
x <- run(list(page(1:2, 4), page(3:4, 4)))
stopifnot(nrow(x) == 4) # Exact multiple requires no ambiguous terminal NULL call.
cases <- list(
  null = list(NULL),
  duplicate = list(page(1:2), page(2)),
  truncated = list(page(1:2), list(total = 3, data = data.frame())),
  changed_total = list(page(1:2), page(3, 4)),
  missing_total = list(list(data = page(1:2)$data)),
  unordered = list(page(c(2, 1))),
  wrong_season = list(list(total = 1, data = data.frame(
    playerId = 1, seasonId = 20242025, gamesPlayed = 1, positionCode = "C"))),
  empty = list(list(total = 0, data = list()))
)
for (name in names(cases)) {
  result <- tryCatch(run(cases[[name]]), error = identity)
  stopifnot(inherits(result, "error"))
  cat(name, "rejected:", conditionMessage(result), "\n")
}
cat("Pagination tests passed\n")

# Goalies share pagination/ID checks but do not have skater position codes.
goalie_page <- function(...) list(total = 1, data = data.frame(
  playerId = 1, seasonId = 20252026, gamesPlayed = 2))
g <- get_all_nhl_players("20252026", population = "goalie", fetch_page = goalie_page)
stopifnot(nrow(g) == 1,
          attr(g, "retrieval_metadata")$population == "goalie",
          grepl("/goalie/summary$", attr(g, "retrieval_metadata")$source))
bad <- tryCatch(get_all_nhl_skaters("20252026", fetch_page = goalie_page), error = identity)
stopifnot(inherits(bad, "error"))
cat("Goalie population and skater position contracts passed\n")
