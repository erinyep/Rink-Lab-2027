# Visualize held-out season-average error; Python fits the reusable forecast.
# Run: Rscript R/analysis/05_fantasy_projection_baseline.R <forecast directory>
library(ggplot2)
library(dplyr)
library(readr)
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("Supply a data/processed/forecasts/per_game_* directory")
input <- args[[1]]
metrics <- read_csv(file.path(input, "evaluation_metrics.csv"), show_col_types = FALSE) |>
  filter(split == "held_out_test", group == "all", category %in% c("goals", "assists", "shots"))
reference <- metrics |> filter(method == "last_season") |>
  select(category, reference_mae = mae)
season <- unique(metrics$target_season)
players <- unique(metrics$players)
if (length(season) != 1 || length(players) != 1) stop("Unexpected evaluation populations")
season_label <- paste0(substr(season, 1, 4), "–", substr(season, 7, 8))
plot_data <- metrics |> left_join(reference, by = "category", relationship = "many-to-one") |>
  mutate(relative_mae = mae / reference_mae,
         method = factor(method, levels = c("last_season", "weighted", "process"),
                         labels = c("Last-season rate", "Recency-weighted", "Opportunity × rate\nwith shrinkage")),
         category = factor(category, levels = c("goals", "assists", "shots"),
                           labels = c("Goals", "Assists", "Shots on goal")))
p <- ggplot(plot_data, aes(x = method, y = relative_mae, fill = method)) +
  geom_col(width = .65, show.legend = FALSE) +
  geom_hline(yintercept = 1, linetype = "dashed", color = "#64748b") +
  geom_text(aes(label = sprintf("%.1f%%", 100 * relative_mae)), vjust = -.4, size = 4) +
  facet_wrap(~category, nrow = 1) +
  scale_fill_manual(values = c("#64748b", "#167d8d", "#d58b29")) +
  scale_y_continuous(limits = c(0, 1.18), labels = function(x) paste0(round(100*x), "%")) +
  labs(title = "How well do historical rates predict next-season production per game?",
       subtitle = paste0(season_label, " held-out season · ", players,
                         " returning skaters · lower error is better"),
       x = NULL, y = "MAE relative to last-season rates",
       caption = paste("Model settings selected on the earlier validation season. Season-average error, not individual-game error.",
                       "Historical source vintages are unavailable; this is a retrospective evaluation.", sep = "\n")) +
  theme_minimal(base_size = 12) +
  theme(panel.grid.major.x = element_blank(), plot.title = element_text(face = "bold"),
        plot.caption = element_text(hjust = 0), axis.text.x = element_text(size = 10))
ggsave(file.path(input, "held_out_per_game_error.png"), p, width = 13, height = 5, dpi = 160)
writeLines(capture.output(sessionInfo()), file.path(input, "r_session_info.txt"))
message("Saved plot and R session information in ", input)
