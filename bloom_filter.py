"""Returning-visitor detection on the event stream with a Bloom filter.

Compares against an exact Python set so false positives are measured, not assumed.
Reads from MongoDB if MONGO_URI is set, otherwise from the local generator.
"""
import argparse
import sys

from streamlib import BloomFilter
from streamlib.source import load_events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=int, default=20000, help="expected distinct users (n)")
    parser.add_argument("--fp", type=float, default=0.01, help="target false-positive rate (p)")
    args = parser.parse_args()

    events, source = load_events()
    print(f"Source: {source} ({len(events):,} events)")

    bloom = BloomFilter(args.expected, args.fp)
    print(f"Bloom filter: m={bloom.size:,} bits ({bloom.memory_bytes / 1024:.1f} KB), k={bloom.hash_count}\n")

    exact = set()
    new_users = returning = false_returning = 0
    for i, e in enumerate(events, 1):
        uid = e["user_id"]
        if bloom.add(uid):
            returning += 1
            if uid not in exact:
                false_returning += 1  # filter said "seen" but user is actually new
        else:
            new_users += 1
        exact.add(uid)
        if i % 10000 == 0:
            print(f"{i:>7,} events | new={new_users:,} returning={returning:,} | fill={bloom.fill_ratio:.1%}")

    print("\n--- Results ---")
    print(f"Distinct users (exact):           {len(exact):,}")
    print(f"New users flagged by Bloom:       {new_users:,}")
    print(f"False 'returning' flags:          {false_returning:,} "
          f"({false_returning / len(exact):.3%} of new users; target {args.fp:.2%})")
    print(f"False negatives:                  0 (impossible by construction)")
    print(f"Memory: Bloom {bloom.memory_bytes / 1024:.1f} KB vs exact set {sys.getsizeof(exact) / 1024:.1f} KB "
          f"(set size excludes the strings themselves)")


if __name__ == "__main__":
    main()
