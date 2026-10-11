"""Event source: MongoDB when MONGO_URI is configured, otherwise the local generator."""
import os
from collections import Counter

from .generator import generate_stream

DB_NAME = "bda_project"
COLLECTION_NAME = "web_logs"


def get_collection():
    """Return the MongoDB collection, or None if MongoDB is not configured/reachable."""
    uri = os.environ.get("MONGO_URI", "")
    if not uri or "<username>" in uri:
        return None
    try:
        from pymongo import MongoClient

        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        return client[DB_NAME][COLLECTION_NAME]
    except Exception:
        return None


def load_events(num_events=50000, seed=42):
    """Return (events, source_name)."""
    col = get_collection()
    if col is not None and col.estimated_document_count() > 0:
        events = list(col.find({}, {"_id": 0}).sort("timestamp", 1))
        return events, "MongoDB Atlas"
    return list(generate_stream(num_events, seed=seed)), "Local generator (MongoDB not configured)"


def aggregate(field, events=None):
    """Group-by count on a field, executed server-side in MongoDB when available."""
    col = get_collection()
    if col is not None:
        pipeline = [{"$group": {"_id": f"${field}", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
        return [(d["_id"], d["count"]) for d in col.aggregate(pipeline)]
    return Counter(e[field] for e in events).most_common()
