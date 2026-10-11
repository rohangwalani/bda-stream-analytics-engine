"""Load the synthetic clickstream into MongoDB Atlas.

    set MONGO_URI=mongodb+srv://...      (Windows)   /  export MONGO_URI=... (Linux/macOS)
    python ingest_data.py --events 50000
"""
import argparse
import os
import sys

from pymongo import ASCENDING, MongoClient
from pymongo.errors import PyMongoError

from streamlib import generate_stream
from streamlib.source import COLLECTION_NAME, DB_NAME


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--batch", type=int, default=5000)
    args = parser.parse_args()

    uri = os.environ.get("MONGO_URI", "")
    if not uri or "<username>" in uri:
        sys.exit("MONGO_URI is not set. Copy .env.example and export your Atlas connection string.")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        col = client[DB_NAME][COLLECTION_NAME]
        col.delete_many({})

        batch, inserted = [], 0
        for event in generate_stream(args.events, seed=args.seed):
            batch.append(event)
            if len(batch) == args.batch:
                col.insert_many(batch, ordered=False)
                inserted += len(batch)
                batch = []
                print(f"Inserted {inserted:,}/{args.events:,}")
        if batch:
            col.insert_many(batch, ordered=False)
            inserted += len(batch)

        col.create_index([("timestamp", ASCENDING)])
        col.create_index("user_id")
        print(f"Done: {inserted:,} events in {DB_NAME}.{COLLECTION_NAME} (indexed on timestamp, user_id)")
    except PyMongoError as e:
        sys.exit(f"MongoDB error: {e}")


if __name__ == "__main__":
    main()
