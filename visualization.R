# Data Visualization using R (ggplot2)
if (!require(ggplot2)) install.packages("ggplot2")
library(ggplot2)

if (file.exists("results.csv")) {
  data <- read.csv("results.csv")
  actual <- data$value[data$metric == "actual_unique"]
  estimated <- data$value[data$metric == "estimated_unique"]
  accuracy <- data$value[data$metric == "accuracy"]
} else {
  actual <- 32091
  estimated <- 49032
  accuracy <- 47.2
}

plot_data <- data.frame(
  Metric = c("Actual Unique Users", "Estimated (Flajolet-Martin)"),
  Count = c(actual, estimated)
)

p <- ggplot(plot_data, aes(x = Metric, y = Count, fill = Metric)) +
  geom_bar(stat = "identity", width = 0.5) +
  geom_text(aes(label = round(Count)), vjust = -0.5, size = 5) +
  scale_fill_manual(values = c("Actual Unique Users" = "#2c3e50", "Estimated (Flajolet-Martin)" = "#3498db")) +
  theme_minimal() +
  labs(
    title = "Cardinality Estimation: Flajolet-Martin vs Actual",
    subtitle = paste("Estimation Accuracy:", round(accuracy, 2), "%"),
    x = "",
    y = "Number of Unique Users"
  ) +
  theme(
    plot.title = element_text(size = 16, face = "bold"),
    plot.subtitle = element_text(size = 12, color = "darkgray"),
    axis.text.x = element_text(size = 12, face = "bold"),
    legend.position = "none"
  )

ggsave("fm_accuracy_plot_r.png", plot = p, width = 8, height = 6, dpi = 300)
cat("Plot saved to fm_accuracy_plot_r.png\n")
