import os
import math
import mmh3
from bitarray import bitarray
from pymongo import MongoClient

# Configuration
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://<username>:<password>@cluster0.lljocca.mongodb.net/?retryWrites=true&w=majority"
)
DB_NAME = "bda_project"
COLLECTION_NAME = "web_logs"

class BloomFilter:
    def __init__(self, expected_items, fp_probability):
        """
        Initialize the Bloom filter.
        :param expected_items: Expected number of items to be stored (n)
        :param fp_probability: Desired false positive probability (p)
        """
        self.fp_prob = fp_probability
        self.size = self._get_size(expected_items, fp_probability)
        self.hash_count = self._get_hash_count(self.size, expected_items)
        self.bit_array = bitarray(self.size)
        self.bit_array.setall(0)

    def add(self, item):
        """Add an item into the filter by setting k hash positions to 1."""
        for i in range(self.hash_count):
            digest = mmh3.hash(str(item), i) % self.size
            self.bit_array[digest] = 1

    def check(self, item):
        """
        Check if an item is present.
        Returns False -> definitely not seen.
        Returns True  -> probably seen (possible false positive).
        """
        for i in range(self.hash_count):
            digest = mmh3.hash(str(item), i) % self.size
            if self.bit_array[digest] == 0:
                return False
        return True

    @classmethod
    def _get_size(cls, n, p):
        """Optimal bit array size: m = -(n * ln(p)) / (ln(2)^2)"""
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return int(m)

    @classmethod
    def _get_hash_count(cls, m, n):
        """Optimal number of hash functions: k = (m / n) * ln(2)"""
        k = (m / n) * math.log(2)
        return int(k)

def run_bloom_filter_analytics():
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    total_records = collection.count_documents({})
    print(f"Found {total_records} logs in the database.\n")

    bloom = BloomFilter(expected_items=35000, fp_probability=0.01)

    print("Initialized Bloom Filter:")
    print(f" - Bit Array Size: {bloom.size} bits ({bloom.size / 8 / 1024:.2f} KB)")
    print(f" - Number of Hash Functions: {bloom.hash_count}")
    print("\nProcessing streaming data...\n")

    logs_cursor = collection.find().sort("timestamp", 1)

    unique_count = 0
    duplicate_count = 0

    for i, log in enumerate(logs_cursor):
        user_id = log["user_id"]
        if bloom.check(user_id):
            duplicate_count += 1
        else:
            bloom.add(user_id)
            unique_count += 1

        if (i + 1) % 10000 == 0:
            print(f"Processed {i + 1} logs -> Found {unique_count} unique users, {duplicate_count} duplicates (estimated)")

    print("\n--- Final Results (Bloom Filter) ---")
    print(f"Total Logs Processed: {total_records}")
    print(f"Estimated Unique Users: {unique_count}")
    print(f"Estimated Duplicate Logs (Returning Visitors): {duplicate_count}")

if __name__ == "__main__":
    run_bloom_filter_analytics()
