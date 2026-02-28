"""
scripts/analysis/export_db.py

One-time export script: saves live MongoDB collections to local JSON snapshots
so analysis scripts can work offline or when the live DB is unavailable.

Usage:
    python scripts/analysis/export_db.py

Output files:
    scripts/analysis/data/players.json
    scripts/analysis/data/guild_members.json
"""

import json
import os
import sys

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Project root setup + .env loading (after stdlib/third-party imports)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, _PROJECT_ROOT)

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except ImportError:
    pass

DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "eldoria_quest"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def export_collection(db, collection_name: str, output_path: str):
    """Exports a MongoDB collection to a JSON file."""
    docs = list(db[collection_name].find({}, {"_id": 0}))
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, default=str)
    print(f"  ✅ Exported {len(docs)} documents -> {output_path}")
    return len(docs)


def main():
    mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
    db_name = os.getenv("DATABASE_NAME", DEFAULT_DB_NAME)

    # Mirror DatabaseManager's .db suffix stripping
    if db_name.endswith(".db"):
        db_name = db_name.replace(".db", "").replace(".", "_")

    print(f"Connecting to database: {db_name}")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("✅ Connection successful.\n")
    except ServerSelectionTimeoutError:
        print("❌ Could not connect to MongoDB.")
        print("   Set MONGO_URI in your .env file or as an environment variable and try again.")
        sys.exit(1)

    db = client[db_name]
    os.makedirs(DATA_DIR, exist_ok=True)

    print("Exporting collections...")
    export_collection(db, "players", os.path.join(DATA_DIR, "players.json"))
    export_collection(db, "guild_members", os.path.join(DATA_DIR, "guild_members.json"))

    client.close()
    print(f"\n✅ Snapshot saved to: {DATA_DIR}")
    print("   Analysis scripts will now use this data as a fallback when the live DB is unavailable.")


if __name__ == "__main__":
    main()
