"""Distinct-user estimation with Flajolet-Martin PCSA and HyperLogLog.

Reads from MongoDB if MONGO_URI is set, otherwise from the local generator.
"""
import argparse

from streamlib import PCSA, HyperLogLog
from streamlib.source import load_events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--buckets", type=int, default=256, help="PCSA bucket count")
    parser.add_argument("--precision", type=int, default=10, help="HyperLogLog precision p (m = 2^p)")
    args = parser.parse_args()

    events, source = load_events()
    print(f"Source: {source} ({len(events):,} events)\n")

    pcsa, hll, exact = PCSA(args.buckets), HyperLogLog(args.precision), set()
    for e in events:
        uid = e["user_id"]
        pcsa.add(uid)
        hll.add(uid)
        exact.add(uid)

    true = len(exact)
    print(f"{'Method':<14}{'Estimate':>10}{'Error':>9}{'Expected SE':>13}{'Memory':>10}")
    print(f"{'Exact set':<14}{true:>10,}{'-':>9}{'-':>13}{'O(n)':>10}")
    for name, s in (("FM-PCSA", pcsa), ("HyperLogLog", hll)):
        est = s.estimate()
        print(f"{name:<14}{est:>10,}{abs(est - true) / true:>9.2%}{s.standard_error:>13.2%}{s.memory_bytes:>8,} B")


if __name__ == "__main__":
    main()
