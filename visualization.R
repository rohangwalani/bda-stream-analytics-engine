# Visualise experiment results with ggplot2.
# Run `python experiments.py` first to produce results/*.csv, then: Rscript visualization.R
if (!require(ggplot2)) install.packages("ggplot2", repos = "https://cloud.r-project.org")
library(ggplot2)

if (!file.exists("results/cardinality.csv")) stop("Run `python experiments.py` first.")

card <- read.csv("results/cardinality.csv")
card <- card[card$algorithm != "Original FM (buggy)", ]
summary <- aggregate(rel_error_pct ~ algorithm + memory_bytes, data = card,
                     FUN = function(x) c(mean = mean(x), sd = sd(x)))
summary <- do.call(data.frame, summary)

p1 <- ggplot(summary, aes(x = memory_bytes, y = rel_error_pct.mean, colour = algorithm)) +
  geom_line() + geom_point(size = 2.5) +
  geom_errorbar(aes(ymin = pmax(0, rel_error_pct.mean - rel_error_pct.sd),
                    ymax = rel_error_pct.mean + rel_error_pct.sd), width = 0.1) +
  scale_x_log10() +
  theme_minimal() +
  labs(title = "Cardinality estimation: error vs memory",
       subtitle = "Mean ± SD over independent streams",
       x = "Sketch memory (bytes, log scale)", y = "Relative error (%)", colour = NULL)
ggsave("results/cardinality_error_vs_memory_r.png", p1, width = 8, height = 5, dpi = 200)

bloom <- read.csv("results/bloom.csv")
bloom_long <- rbind(
  data.frame(memory_kb = bloom$memory_kb, fp = bloom$measured_fp, kind = "Measured"),
  data.frame(memory_kb = bloom$memory_kb, fp = bloom$theoretical_fp, kind = "Theoretical")
)
p2 <- ggplot(bloom_long, aes(x = memory_kb, y = fp, colour = kind)) +
  stat_summary(fun = mean, geom = "line") + stat_summary(fun = mean, geom = "point", size = 2.5) +
  scale_y_log10() +
  theme_minimal() +
  labs(title = "Bloom filter: memory vs false-positive rate",
       x = "Memory (KB)", y = "False-positive rate (log scale)", colour = NULL)
ggsave("results/bloom_fp_vs_memory_r.png", p2, width = 8, height = 5, dpi = 200)

cat("Plots saved to results/\n")
