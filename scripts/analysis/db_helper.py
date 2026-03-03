"""
scripts/analysis/db_helper.py

Shared database helper for analysis scripts.
Tries to connect to a live MongoDB (via MONGO_URI in .env or env var).
If the connection fails or the collection is empty, falls back to locally
exported JSON snapshots in scripts/analysis/data/.

Usage:
    from db_helper import get_players, get_guild_members

Export a fresh snapshot from the live DB first:
    python scripts/analysis/export_db.py
"""

import json
import os
import sys

# Make project root importable
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, _PROJECT_ROOT)

# Load .env from project root so MONGO_URI etc. are available
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))
except ImportError:
    pass  # python-dotenv not installed; fall back to shell env vars

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_PLAYERS_FILE = os.path.join(_DATA_DIR, "players.json")
_GUILD_MEMBERS_FILE = os.path.join(_DATA_DIR, "guild_members.json")

DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "eldoria_quest"


def _try_live_db():
    """
    Attempts to connect to the live MongoDB.
    Returns (db_client, db) on success, or (None, None) on failure.
    """
    try:
        from pymongo import MongoClient

        mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
        db_name = os.getenv("DATABASE_NAME", DEFAULT_DB_NAME)

        # Mirror DatabaseManager's .db suffix stripping
        if db_name.endswith(".db"):
            db_name = db_name.replace(".db", "").replace(".", "_")

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Force a connection check
        client.admin.command("ping")
        print(f"[db_helper] 🔗 Connected to database: {db_name}")
        return client, client[db_name]
    except Exception:
        return None, None


def _fetch_collection(collection_name: str, fallback_path: str) -> list:
    """
    Tries to load documents from the live MongoDB collection.
    Falls back to a local JSON snapshot if the DB is unavailable or empty.
    """
    client, db = _try_live_db()

    if db is not None:
        documents = list(db[collection_name].find({}, {"_id": 0}))
        client.close()
        if documents:
            print(f"[db_helper] ✅ Live DB — {len(documents)} {collection_name} loaded.")
            return documents
        print(f"[db_helper] ⚠️  Live DB connected but {collection_name} collection is empty.")

    # Fallback to stored snapshot
    if os.path.exists(fallback_path):
        with open(fallback_path, encoding="utf-8") as f:
            documents = json.load(f)
        print(f"[db_helper] 📂 Stored snapshot — {len(documents)} {collection_name} loaded from {fallback_path}")
        return documents

    print(f"[db_helper] ❌ No data available for {collection_name}. Run export_db.py to create a local snapshot.")
    return []


def get_players() -> list:
    """
    Returns a list of player documents.
    Prefers live DB; falls back to data/players.json.
    """
    return _fetch_collection("players", _PLAYERS_FILE)


def get_guild_members() -> list:
    """
    Returns a list of guild_members documents.
    Prefers live DB; falls back to data/guild_members.json.
    """
    return _fetch_collection("guild_members", _GUILD_MEMBERS_FILE)
