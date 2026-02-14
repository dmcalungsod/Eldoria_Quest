"""
create_database.py

Creates MongoDB collections and indexes for the Eldoria Quest database.
Replaces the SQLite schema creation.
"""

import logging
import os

from pymongo import ASCENDING, MongoClient
from pymongo.errors import CollectionInvalid

# Only configure logging if running as main script to avoid duplicates
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("db_create")

DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "eldoria_quest"


def create_tables(db=None):
    """Creates all MongoDB collections and indexes.

    If `db` is None, connects using environment variables.
    """
    if db is None:
        mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
        db_name = os.getenv("DATABASE_NAME", DEFAULT_DB_NAME)
        if db_name.endswith(".db"):
            db_name = db_name.replace(".db", "").replace(".", "_")
        client = MongoClient(mongo_uri)
        db = client[db_name]

    # -------------------------
    # COLLECTIONS & INDEXES
    # -------------------------

    # --- players ---
    db["players"].create_index("discord_id", unique=True)

    # --- stats ---
    db["stats"].create_index("discord_id", unique=True)

    # --- monsters ---
    db["monsters"].create_index("id", unique=True)
    db["monsters"].create_index("biome")
    db["monsters"].create_index("tier")

    # --- quest_items ---
    db["quest_items"].create_index("id", unique=True)

    # --- consumables ---
    db["consumables"].create_index("id", unique=True)

    # --- equipment ---
    db["equipment"].create_index("id", unique=True)

    # --- class_equipment ---
    db["class_equipment"].create_index("id", unique=True)

    # --- item_sets ---
    db["item_sets"].create_index("id", unique=True)

    # --- guild_members ---
    db["guild_members"].create_index("discord_id", unique=True)

    # --- quests ---
    db["quests"].create_index("id", unique=True)
    db["quests"].create_index("tier")

    # --- player_quests ---
    db["player_quests"].create_index([("discord_id", ASCENDING), ("quest_id", ASCENDING)])
    db["player_quests"].create_index("discord_id")

    # --- materials ---
    db["materials"].create_index("id", unique=True)
    db["materials"].create_index("key_id", unique=True)

    # --- inventory ---
    db["inventory"].create_index("id", unique=True)
    db["inventory"].create_index("discord_id")
    db["inventory"].create_index(
        [("discord_id", ASCENDING), ("item_key", ASCENDING), ("rarity", ASCENDING), ("equipped", ASCENDING)]
    )

    # --- adventure_sessions ---
    db["adventure_sessions"].create_index("discord_id", unique=True)
    db["adventure_sessions"].create_index([("discord_id", ASCENDING), ("active", ASCENDING)])

    # --- skills ---
    db["skills"].create_index("id", unique=True)
    db["skills"].create_index("key_id", unique=True)

    # --- player_skills ---
    db["player_skills"].create_index([("discord_id", ASCENDING), ("skill_key", ASCENDING)], unique=True)
    db["player_skills"].create_index("discord_id")

    # --- global_boosts ---
    db["global_boosts"].create_index("boost_key", unique=True)
    db["global_boosts"].create_index("end_time")

    # --- active_buffs ---
    db["active_buffs"].create_index("discord_id")
    db["active_buffs"].create_index([("discord_id", ASCENDING), ("end_time", ASCENDING)])

    # --- classes ---
    db["classes"].create_index("id", unique=True)

    # --- counters (for auto-increment IDs) ---
    # Seeded automatically by _next_inventory_id in database_manager

    # --- locations ---
    db["locations"].create_index("id", unique=True)

    logger.info("MongoDB collections and indexes verified/created.")


if __name__ == "__main__":
    create_tables()
