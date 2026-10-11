import mmh3


def hash64(item, seed=0):
    """Unsigned 64-bit MurmurHash3 of an item."""
    return mmh3.hash64(str(item), seed, signed=False)[0]


def hash_pair(item, seed=0):
    """Two independent unsigned 64-bit hashes (for double hashing)."""
    return mmh3.hash64(str(item), seed, signed=False)


def trailing_zeros(x, max_bits=64):
    if x == 0:
        return max_bits
    return (x & -x).bit_length() - 1
