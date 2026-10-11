import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configuration
# Set MONGO_URI in your environment or replace with your connection string
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://<username>:<password>@cluster0.lljocca.mongodb.net/?retryWrites=true&w=majority"
)
DB_NAME = "bda_project"
COLLECTION_NAME = "web_logs"
NUM_RECORDS = 50000

def generate_dummy_data(num_records):
    print(f"Generating {num_records} dummy web log records...")
    data = []
    base_users = [f"user_{i:05d}" for i in range(1, int(num_records * 0.6))]
    start_time = datetime.now() - timedelta(days=7)

    for i in range(num_records):
        # 80% chance of returning user, 20% new user
        if random.random() < 0.8:
            user_id = random.choice(base_users)
        else:
            user_id = f"user_new_{i:05d}"

        timestamp = start_time + timedelta(seconds=random.randint(0, 604800))
        record = {
            "log_id": f"log_{i}",
            "user_id": user_id,
            "timestamp": timestamp,
            "action": random.choice(["view", "click", "login", "purchase"]),
            "page": random.choice(["/home", "/product", "/cart", "/checkout", "/about"])
        }
        data.append(record)

    return data

def insert_to_mongodb(data):
    if "<username>" in MONGO_URI:
        print("WARNING: Please set the MONGO_URI environment variable or update the connection string in the script.")
        return

    try:
        print("Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("Connected successfully!")

        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        collection.delete_many({})
        print("Cleared existing collection.")

        print(f"Inserting {len(data)} records...")
        collection.insert_many(data)
        print("Insertion complete!")
        collection.create_index("user_id")

    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    records = generate_dummy_data(NUM_RECORDS)
    insert_to_mongodb(records)
