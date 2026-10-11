"""Reproducible evaluation of every sketch in the project.

Each experiment is repeated over several random seeds so the reported error is
an average with a spread, not a single lucky run. Writes CSVs and PNG plots to
results/.

    python experiments.py            # full run
    python experiments.py --quick    # fewer seeds, for a fast check
"""
import argparse
import os
import statistics
import sys
import time
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from streamlib import PCSA, BloomFilter, CountMinSketch, HyperLogLog, generate_stream

OUT = "results"


def legacy_fm(user_ids, m=256):
    """The project's original estimator (max trailing zeros), kept for comparison."""
    import mmh3

    k = m.bit_length() - 1
    mask = (1 << (32 - k)) - 1
    best = [0] * m
    for uid in user_ids:
        h = mmh3.hash(uid, 0, signed=False)
        rest = h & mask
        z = 32 - k if rest == 0 else (rest & -rest).bit_length() - 1
        b = h >> (32 - k)
        best[b] = max(best[b], z)
    return int(m / 0.77351 * 2 ** (sum(best) / m))


def cardinality_experiment(seeds, n_events):
    rows = []
    configs = [("PCSA", m, lambda m=m: PCSA(m)) for m in (64, 128, 256, 512, 1024)]
    configs += [("HyperLogLog", 1 << p, lambda p=p: HyperLogLog(p)) for p in (6, 7, 8, 9, 10, 12)]
    for seed in seeds:
        users = [e["user_id"] for e in generate_stream(n_events, seed=seed)]
        true = len(set(users))
        rows.append(dict(algorithm="Original FM (buggy)", buckets=256, memory_bytes=1024,
                         seed=seed, true=true, estimate=legacy_fm(users)))
        for name, m, make in configs:
            sketch = make()
            for u in users:
                sketch.add(u)
            rows.append(dict(algorithm=name, buckets=m, memory_bytes=sketch.memory_bytes,
                             seed=seed, true=true, estimate=sketch.estimate()))
    df = pd.DataFrame(rows)
    df["rel_error_pct"] = (df.estimate - df.true).abs() / df.true * 100
    return df


def bloom_experiment(seeds, n_events):
    rows = []
    for seed in seeds:
        users = [e["user_id"] for e in generate_stream(n_events, seed=seed)]
        distinct = len(set(users))
        for p in (0.1, 0.05, 0.01, 0.005, 0.001):
            bf = BloomFilter(distinct, p)
            for u in dict.fromkeys(users):  # insert each distinct user once
                bf.add(u)
            # probe with ids guaranteed absent from the stream
            probes = [f"absent_{seed}_{i}" for i in range(50000)]
            fp = sum(1 for x in probes if x in bf)
            rows.append(dict(seed=seed, target_fp=p, memory_kb=bf.memory_bytes / 1024,
                             hash_count=bf.hash_count, measured_fp=fp / len(probes),
                             theoretical_fp=bf.theoretical_fp_rate(),
                             exact_set_kb=sys.getsizeof(set(users)) / 1024))
    return pd.DataFrame(rows)


def countmin_experiment(seeds, n_events):
    rows = []
    for seed in seeds:
        users = [e["user_id"] for e in generate_stream(n_events, seed=seed)]
        exact = Counter(users)
        for eps in (0.01, 0.005, 0.001, 0.0005):
            cms = CountMinSketch(epsilon=eps, delta=0.01, top_k=10)
            for u in users:
                cms.add(u)
            errs = [cms.estimate(u) - c for u, c in exact.items()]
            true_top = {u for u, _ in exact.most_common(10)}
            found_top = {u for u, _ in cms.heavy_hitters()}
            rows.append(dict(seed=seed, epsilon=eps, memory_kb=cms.memory_bytes / 1024,
                             mean_overcount=statistics.mean(errs), bound=eps * len(users),
                             # guarantee: P(overcount <= eps*N) >= 1 - delta, per item
                             pct_within_bound=100 * sum(e <= eps * len(users) for e in errs) / len(errs),
                             top10_recall=len(true_top & found_top) / 10))
    return pd.DataFrame(rows)


def plot_cardinality(df):
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, marker in (("PCSA", "o"), ("HyperLogLog", "s")):
        g = df[df.algorithm == name].groupby("memory_bytes").rel_error_pct.agg(["mean", "std"])
        ax.errorbar(g.index, g["mean"], yerr=g["std"], marker=marker, capsize=3, label=name)
    legacy = df[df.algorithm == "Original FM (buggy)"].rel_error_pct.mean()
    ax.axhline(legacy, color="crimson", linestyle="--", label=f"Original FM (buggy): {legacy:.1f}%")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("Sketch memory (bytes, log scale)")
    ax.set_ylabel("Relative error (%) — mean ± std over seeds")
    ax.set_title("Cardinality estimation: error vs memory")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "cardinality_error_vs_memory.png"), dpi=150)


def plot_bloom(df):
    g = df.groupby("target_fp")[["memory_kb", "measured_fp", "theoretical_fp"]].mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(g.memory_kb, g.theoretical_fp, "o--", label="Theoretical FP rate")
    ax.plot(g.memory_kb, g.measured_fp, "s-", label="Measured FP rate (50k absent probes)")
    ax.set_yscale("log")
    ax.set_xlabel("Bloom filter memory (KB)")
    ax.set_ylabel("False-positive rate (log scale)")
    ax.set_title("Bloom filter: memory vs false positives")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "bloom_fp_vs_memory.png"), dpi=150)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--events", type=int, default=50000)
    args = parser.parse_args()
    seeds = range(3) if args.quick else range(10)
    os.makedirs(OUT, exist_ok=True)

    for name, fn in (("cardinality", cardinality_experiment), ("bloom", bloom_experiment),
                     ("countmin", countmin_experiment)):
        t0 = time.time()
        df = fn(seeds, args.events)
        df.to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
        print(f"\n=== {name} ({time.time() - t0:.1f}s) ===")
        if name == "cardinality":
            summary = df.groupby(["algorithm", "buckets", "memory_bytes"]).rel_error_pct.agg(["mean", "std"])
            plot_cardinality(df)
        elif name == "bloom":
            summary = df.groupby("target_fp")[["memory_kb", "hash_count", "measured_fp", "theoretical_fp", "exact_set_kb"]].mean()
            plot_bloom(df)
        else:
            summary = df.groupby("epsilon")[["memory_kb", "mean_overcount", "bound", "pct_within_bound", "top10_recall"]].mean()
        print(summary.round(4).to_string())
    print(f"\nCSVs and plots written to {OUT}/")


if __name__ == "__main__":
    main()
