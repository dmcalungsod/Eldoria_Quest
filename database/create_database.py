"""
create_database.py

Creates MongoDB collections and indexes for the Eldoria Quest database.
Replaces the SQLite schema creation.
"""

import logging
import os

from pymongo import ASCENDING, MongoClient

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
    # Format: "collection_name": [ (keys, unique, partialFilter) ]
    INDEX_DEFINITIONS = {
        "players": [([("discord_id", ASCENDING)], True, None)],
        "stats": [([("discord_id", ASCENDING)], True, None)],
        "monsters": [
            ([("id", ASCENDING)], True, None),
            ([("biome", ASCENDING)], False, None),
            ([("tier", ASCENDING)], False, None),
        ],
        "quest_items": [([("id", ASCENDING)], True, None)],
        "consumables": [([("id", ASCENDING)], True, None)],
        "equipment": [([("id", ASCENDING)], True, None)],
        "class_equipment": [([("id", ASCENDING)], True, None)],
        "item_sets": [([("id", ASCENDING)], True, None)],
        "guild_members": [([("discord_id", ASCENDING)], True, None)],
        "quests": [
            ([("id", ASCENDING)], True, None),
            ([("tier", ASCENDING)], False, None),
        ],
        "player_quests": [
            ([("discord_id", ASCENDING), ("quest_id", ASCENDING)], False, None),
            ([("discord_id", ASCENDING)], False, None),
        ],
        "materials": [
            ([("id", ASCENDING)], True, None),
            ([("key_id", ASCENDING)], True, None),
        ],
        "inventory": [
            ([("id", ASCENDING)], True, None),
            ([("discord_id", ASCENDING)], False, None),
            (
                [
                    ("discord_id", ASCENDING),
                    ("item_key", ASCENDING),
                    ("rarity", ASCENDING),
                    ("equipped", ASCENDING),
                ],
                False,
                None,
            ),
            (
                [("discord_id", ASCENDING), ("slot", ASCENDING)],
                True,
                {"equipped": 1},
            ),
        ],
        "adventure_sessions": [
            ([("discord_id", ASCENDING)], True, None),
            ([("discord_id", ASCENDING), ("active", ASCENDING)], False, None),
            (
                [("active", ASCENDING), ("status", ASCENDING), ("end_time", ASCENDING)],
                False,
                None,
            ),
        ],
        "skills": [
            ([("id", ASCENDING)], True, None),
            ([("key_id", ASCENDING)], True, None),
        ],
        "player_skills": [
            ([("discord_id", ASCENDING), ("skill_key", ASCENDING)], True, None),
            ([("discord_id", ASCENDING)], False, None),
        ],
        "global_boosts": [
            ([("boost_key", ASCENDING)], True, None),
            ([("end_time", ASCENDING)], False, None),
        ],
        "active_buffs": [
            ([("discord_id", ASCENDING)], False, None),
            ([("discord_id", ASCENDING), ("end_time", ASCENDING)], False, None),
        ],
        "classes": [([("id", ASCENDING)], True, None)],
        "locations": [([("id", ASCENDING)], True, None)],
        "tournaments": [
            ([("id", ASCENDING)], True, None),
            ([("active", ASCENDING)], False, None),
            ([("end_time", ASCENDING)], False, None),
        ],
        "tournament_scores": [
            (
                [("discord_id", ASCENDING), ("tournament_id", ASCENDING)],
                True,
                None,
            ),
            ([("tournament_id", ASCENDING), ("score", -1)], False, None),
        ],
        "world_events": [
            ([("active", ASCENDING)], False, None),
            ([("end_time", ASCENDING)], False, None),
        ],
    }

    for col_name, indexes in INDEX_DEFINITIONS.items():
        collection = db[col_name]
        for keys, is_unique, partial in indexes:
            args = {"unique": is_unique}
            if partial:
                args["partialFilterExpression"] = partial
            collection.create_index(keys, **args)

    logger.info("MongoDB collections and indexes verified/created.")


if __name__ == "__main__":
    create_tables()
