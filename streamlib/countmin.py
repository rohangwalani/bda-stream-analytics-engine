import heapq
import math

from .hashing import hash_pair


class CountMinSketch:
    """Count-Min Sketch for approximate frequency counts in a stream.

    width w = ceil(e / epsilon), depth d = ceil(ln(1 / delta)).
    Estimates never undercount; with prob. >= 1 - delta the overcount is
    at most epsilon * N (N = total stream length).
    """

    def __init__(self, epsilon=0.001, delta=0.01, top_k=10):
        self.epsilon = epsilon
        self.delta = delta
        self.width = math.ceil(math.e / epsilon)
        self.depth = math.ceil(math.log(1 / delta))
        self.table = [[0] * self.width for _ in range(self.depth)]
        self.total = 0
        self.top_k = top_k
        self._heavy = {}

    def _columns(self, item):
        h1, h2 = hash_pair(item, seed=7)
        return [(h1 + i * h2) % self.width for i in range(self.depth)]

    def add(self, item, count=1):
        self.total += count
        est = None
        for row, col in enumerate(self._columns(item)):
            self.table[row][col] += count
            v = self.table[row][col]
            est = v if est is None else min(est, v)
        self._track(item, est)

    def _track(self, item, est):
        """Keep a small candidate set of the top-k items seen so far."""
        if item in self._heavy or len(self._heavy) < self.top_k:
            self._heavy[item] = est
            return
        smallest = min(self._heavy, key=self._heavy.get)
        if est > self._heavy[smallest]:
            del self._heavy[smallest]
            self._heavy[item] = est

    def estimate(self, item):
        return min(self.table[row][col] for row, col in enumerate(self._columns(item)))

    def heavy_hitters(self):
        return heapq.nlargest(self.top_k, self._heavy.items(), key=lambda kv: kv[1])

    @property
    def memory_bytes(self):
        return self.width * self.depth * 4  # 32-bit counters
