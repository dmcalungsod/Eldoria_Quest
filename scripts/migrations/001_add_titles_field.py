"""
Migration Script: 001_add_titles_field.py

Adds 'titles' (list) and 'active_title' (string or null) fields to all player documents
in the 'players' collection if they do not already exist.

This ensures compatibility with the new Title System.
"""

import os
import sys
from pymongo import MongoClient

# Add project root to sys.path to allow imports if needed, though this script is standalone.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from database.database_manager import DEFAULT_MONGO_URI, DEFAULT_DB_NAME

def run_migration():
    mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
    db_name = os.getenv("DATABASE_NAME", DEFAULT_DB_NAME)

    if db_name.endswith(".db"):
        db_name = db_name.replace(".db", "").replace(".", "_")

    print(f"Connecting to MongoDB: {db_name} at {mongo_uri}")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    players_col = db["players"]

    # Bulk update to add fields if missing
    print("Migrating players collection...")

    # 1. Initialize 'titles' as empty list
    result_titles = players_col.update_many(
        {"titles": {"$exists": False}},
        {"$set": {"titles": []}}
    )
    print(f"Initialized 'titles' for {result_titles.modified_count} players.")

    # 2. Initialize 'active_title' as null
    result_active = players_col.update_many(
        {"active_title": {"$exists": False}},
        {"$set": {"active_title": None}}
    )
    print(f"Initialized 'active_title' for {result_active.modified_count} players.")

    print("Migration complete.")

if __name__ == "__main__":
    run_migration()
