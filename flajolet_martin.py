import os
import math
import mmh3
from pymongo import MongoClient

# Configuration
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://<username>:<password>@cluster0.lljocca.mongodb.net/?appName=Cluster0"
)
DB_NAME = "bda_project"
COLLECTION_NAME = "web_logs"

def count_trailing_zeros(n, max_bits):
    """Counts the number of trailing zeros in a binary representation."""
    if n == 0:
        return max_bits
    count = 0
    while (n & 1) == 0 and count < max_bits:
        count += 1
        n >>= 1
    return count

def flajolet_martin_pcsa(collection, num_buckets=256):
    """
    Probabilistic Counting with Stochastic Averaging (PCSA)
    Flajolet-Martin Algorithm implementation.
    """
    print(f"Fetching streaming data for Flajolet-Martin (PCSA with {num_buckets} buckets)...")
    max_trailing_zeros = [0] * num_buckets

    logs_cursor = collection.find().sort("timestamp", 1)

    count = 0
    actual_unique_set = set()

    k = int(math.log2(num_buckets))
    mask = (1 << (32 - k)) - 1

    for log in logs_cursor:
        user_id = log["user_id"]
        actual_unique_set.add(user_id)

        # 32-bit unsigned hash
        hash_val = mmh3.hash(str(user_id), 0, signed=False)

        # First k bits determine bucket index
        bucket_index = hash_val >> (32 - k)

        # Remaining bits used for trailing zero count
        remaining_bits = hash_val & mask
        zeros = count_trailing_zeros(remaining_bits, 32 - k)

        if zeros > max_trailing_zeros[bucket_index]:
            max_trailing_zeros[bucket_index] = zeros

        count += 1
        if count % 10000 == 0:
            print(f"Processed {count} logs...")

    # PCSA formula: N = (m / phi) * 2^(sum(R) / m)
    # Magic constant phi ≈ 0.77351
    phi = 0.77351
    sum_R = sum(max_trailing_zeros)
    avg_R = sum_R / num_buckets

    final_estimate = int((num_buckets / phi) * (2 ** avg_R))
    actual_cardinality = len(actual_unique_set)

    print("\n--- Final Results (Flajolet-Martin PCSA) ---")
    print(f"Actual Unique Users (Ground Truth): {actual_cardinality}")
    print(f"Flajolet-Martin Estimated Unique Users: {final_estimate}")

    error = abs(actual_cardinality - final_estimate)
    accuracy = (1 - error / actual_cardinality) * 100
    print(f"Estimation Accuracy: {accuracy:.2f}%")

    # Export metrics for visualization
    with open("results.csv", "w") as f:
        f.write("metric,value\n")
        f.write(f"actual_unique,{actual_cardinality}\n")
        f.write(f"estimated_unique,{final_estimate}\n")
        f.write(f"accuracy,{accuracy:.2f}\n")

    print("\nResults exported to results.csv")
    return actual_cardinality, final_estimate

if __name__ == "__main__":
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    flajolet_martin_pcsa(collection, num_buckets=256)
