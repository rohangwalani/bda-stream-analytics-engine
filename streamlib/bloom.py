import math

from bitarray import bitarray

from .hashing import hash_pair


class BloomFilter:
    """Bloom filter with optimal sizing and Kirsch-Mitzenmacher double hashing.

    Only two hash computations are needed per item regardless of k:
    g_i(x) = h1(x) + i * h2(x)  (mod m)
    """

    def __init__(self, expected_items, fp_probability):
        if expected_items <= 0 or not 0 < fp_probability < 1:
            raise ValueError("expected_items must be > 0 and 0 < fp_probability < 1")
        self.expected_items = expected_items
        self.fp_prob = fp_probability
        self.size = self.optimal_size(expected_items, fp_probability)
        self.hash_count = self.optimal_hash_count(self.size, expected_items)
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)
        self.count = 0

    @staticmethod
    def optimal_size(n, p):
        """m = -(n ln p) / (ln 2)^2"""
        return math.ceil(-(n * math.log(p)) / (math.log(2) ** 2))

    @staticmethod
    def optimal_hash_count(m, n):
        """k = (m / n) ln 2, at least 1"""
        return max(1, round((m / n) * math.log(2)))

    def _positions(self, item):
        h1, h2 = hash_pair(item)
        h2 |= 1  # odd step so positions don't collapse when m is even
        return [(h1 + i * h2) % self.size for i in range(self.hash_count)]

    def add(self, item):
        """Insert item. Returns True if it was (probably) already present."""
        present = True
        for pos in self._positions(item):
            if not self.bit_array[pos]:
                present = False
                self.bit_array[pos] = 1
        if not present:
            self.count += 1
        return present

    def __contains__(self, item):
        return all(self.bit_array[pos] for pos in self._positions(item))

    check = __contains__

    @property
    def fill_ratio(self):
        return self.bit_array.count(1) / self.size

    def theoretical_fp_rate(self, n=None):
        """(1 - e^(-kn/m))^k for n inserted items (defaults to items added so far)."""
        n = self.count if n is None else n
        return (1 - math.exp(-self.hash_count * n / self.size)) ** self.hash_count

    @property
    def memory_bytes(self):
        return math.ceil(self.size / 8)
