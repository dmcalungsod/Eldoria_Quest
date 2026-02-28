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


def get_players():
    """
    Returns a list of player documents.
    Prefers live DB; falls back to data/players.json.
    """
    client, db = _try_live_db()

    if db is not None:
        players = list(db["players"].find({}, {"_id": 0}))
        if players:
            print(f"[db_helper] ✅ Live DB — {len(players)} players loaded.")
            client.close()
            return players
        else:
            print("[db_helper] ⚠️  Live DB connected but players collection is empty.")
            client.close()

    # Fallback to stored snapshot
    if os.path.exists(_PLAYERS_FILE):
        with open(_PLAYERS_FILE, encoding="utf-8") as f:
            players = json.load(f)
        print(f"[db_helper] 📂 Stored snapshot — {len(players)} players loaded from {_PLAYERS_FILE}")
        return players

    print("[db_helper] ❌ No data available. Run export_db.py to create a local snapshot.")
    return []


def get_guild_members():
    """
    Returns a list of guild_members documents.
    Prefers live DB; falls back to data/guild_members.json.
    """
    client, db = _try_live_db()

    if db is not None:
        members = list(db["guild_members"].find({}, {"_id": 0}))
        if members:
            print(f"[db_helper] ✅ Live DB — {len(members)} guild members loaded.")
            client.close()
            return members
        else:
            print("[db_helper] ⚠️  Live DB connected but guild_members collection is empty.")
            client.close()

    # Fallback to stored snapshot
    if os.path.exists(_GUILD_MEMBERS_FILE):
        with open(_GUILD_MEMBERS_FILE, encoding="utf-8") as f:
            members = json.load(f)
        print(f"[db_helper] 📂 Stored snapshot — {len(members)} guild members loaded from {_GUILD_MEMBERS_FILE}")
        return members

    print("[db_helper] ❌ No data available. Run export_db.py to create a local snapshot.")
    return []
