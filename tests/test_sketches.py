import os
import sys
from collections import Counter

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlib import PCSA, BloomFilter, CountMinSketch, HyperLogLog, generate_stream  # noqa: E402

ITEMS = [f"item_{i}" for i in range(20000)]


def test_bloom_no_false_negatives():
    bf = BloomFilter(len(ITEMS), 0.01)
    for x in ITEMS:
        bf.add(x)
    assert all(x in bf for x in ITEMS)


def test_bloom_fp_rate_near_target():
    bf = BloomFilter(len(ITEMS), 0.01)
    for x in ITEMS:
        bf.add(x)
    fp = sum(f"absent_{i}" in bf for i in range(20000)) / 20000
    assert fp < 0.02


def test_bloom_add_reports_duplicates():
    bf = BloomFilter(100, 0.01)
    assert bf.add("a") is False
    assert bf.add("a") is True


@pytest.mark.parametrize("m", [256, 1024])
def test_pcsa_within_four_standard_errors(m):
    s = PCSA(m)
    for x in ITEMS:
        s.add(x)
    assert abs(s.estimate() - len(ITEMS)) / len(ITEMS) < 4 * s.standard_error


@pytest.mark.parametrize("p", [10, 12, 14])
def test_hll_within_four_standard_errors(p):
    s = HyperLogLog(p)
    for x in ITEMS:
        s.add(x)
    assert abs(s.estimate() - len(ITEMS)) / len(ITEMS) < 4 * s.standard_error


def test_hll_small_range_is_near_exact():
    s = HyperLogLog(12)
    for x in ITEMS[:100]:
        s.add(x)
    assert abs(s.estimate() - 100) <= 3


def test_duplicates_do_not_change_estimates():
    a, b = HyperLogLog(10), HyperLogLog(10)
    for x in ITEMS[:5000]:
        a.add(x)
        b.add(x)
        b.add(x)
    assert a.estimate() == b.estimate()


def test_merge_equals_union():
    a, b, u = HyperLogLog(10), HyperLogLog(10), HyperLogLog(10)
    for x in ITEMS[:12000]:
        a.add(x)
        u.add(x)
    for x in ITEMS[8000:]:
        b.add(x)
        u.add(x)
    a.merge(b)
    assert a.registers == u.registers

    p1, p2, pu = PCSA(64), PCSA(64), PCSA(64)
    for x in ITEMS[:12000]:
        p1.add(x)
        pu.add(x)
    for x in ITEMS[8000:]:
        p2.add(x)
        pu.add(x)
    p1.merge(p2)
    assert p1.bitmaps == pu.bitmaps


def test_countmin_never_undercounts_and_finds_top():
    users = [e["user_id"] for e in generate_stream(20000, seed=1)]
    exact = Counter(users)
    cms = CountMinSketch(epsilon=0.001, delta=0.01, top_k=5)
    for u in users:
        cms.add(u)
    assert all(cms.estimate(u) >= c for u, c in exact.items())
    assert {u for u, _ in exact.most_common(3)} <= {u for u, _ in cms.heavy_hitters()}


def test_generator_is_reproducible():
    a = list(generate_stream(100, seed=5))
    b = list(generate_stream(100, seed=5))
    assert a == b
    assert all(a[i]["timestamp"] <= a[i + 1]["timestamp"] for i in range(99))
