import math

from .hashing import hash64, trailing_zeros

PHI = 0.77351  # Flajolet-Martin correction constant


class PCSA:
    """Flajolet-Martin Probabilistic Counting with Stochastic Averaging.

    Each of m buckets keeps a bitmap; bit r is set when some item routed to
    the bucket had exactly r trailing zeros. R_j is the position of the lowest
    UNSET bit in bitmap j, and the estimate is (m / phi) * 2^(mean R_j).
    Standard error ~ 0.78 / sqrt(m).

    Note: using the *maximum* trailing-zero count instead of the lowest unset
    bit (as the original version of this project did) does not match the phi
    constant and overestimates heavily.
    """

    def __init__(self, num_buckets=256, bits=32):
        if num_buckets < 1:
            raise ValueError("num_buckets must be >= 1")
        self.m = num_buckets
        self.bits = bits
        self.bitmaps = [0] * num_buckets

    def add(self, item):
        h = hash64(item)
        bucket = h % self.m
        r = trailing_zeros(h // self.m, self.bits - 1)
        self.bitmaps[bucket] |= 1 << r

    @staticmethod
    def _lowest_unset(bitmap):
        return trailing_zeros(~bitmap & (bitmap + 1))

    def estimate(self):
        mean_r = sum(self._lowest_unset(b) for b in self.bitmaps) / self.m
        # The 2^(-kappa * R) term is the standard small-range bias correction (kappa = 1.75)
        return int(self.m / PHI * (2 ** mean_r - 2 ** (-1.75 * mean_r)))

    def merge(self, other):
        if other.m != self.m:
            raise ValueError("Can only merge sketches with equal bucket counts")
        self.bitmaps = [a | b for a, b in zip(self.bitmaps, other.bitmaps)]

    @property
    def memory_bytes(self):
        return self.m * self.bits // 8

    @property
    def standard_error(self):
        return 0.78 / math.sqrt(self.m)


class HyperLogLog:
    """HyperLogLog (Flajolet et al. 2007) with linear-counting small-range correction.

    Uses m = 2^p registers of 6 bits each. Standard error ~ 1.04 / sqrt(m).
    """

    def __init__(self, precision=12):
        if not 4 <= precision <= 18:
            raise ValueError("precision must be between 4 and 18")
        self.p = precision
        self.m = 1 << precision
        self.registers = [0] * self.m
        self.alpha = {16: 0.673, 32: 0.697, 64: 0.709}.get(self.m, 0.7213 / (1 + 1.079 / self.m))

    def add(self, item):
        h = hash64(item)
        idx = h >> (64 - self.p)
        w = h & ((1 << (64 - self.p)) - 1)
        rho = (64 - self.p) - w.bit_length() + 1  # leading zeros + 1
        if rho > self.registers[idx]:
            self.registers[idx] = rho

    def estimate(self):
        raw = self.alpha * self.m ** 2 / sum(2.0 ** -r for r in self.registers)
        zeros = self.registers.count(0)
        if raw <= 2.5 * self.m and zeros:
            return int(self.m * math.log(self.m / zeros))
        return int(raw)

    def merge(self, other):
        if other.p != self.p:
            raise ValueError("Can only merge sketches with equal precision")
        self.registers = [max(a, b) for a, b in zip(self.registers, other.registers)]

    @property
    def memory_bytes(self):
        return math.ceil(self.m * 6 / 8)

    @property
    def standard_error(self):
        return 1.04 / math.sqrt(self.m)
