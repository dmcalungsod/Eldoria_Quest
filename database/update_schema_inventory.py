"""
update_schema_inventory.py

Adds 'materials' and 'inventory' tables to EQ_Game.db.
Populates the materials table using data from game_systems/data/materials.py.
Hardened: Uses logging, path safety, and atomic commits.
"""

import logging
import os
import sqlite3
import sys

# Configure logging only if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("db_update_inv")

# Ensure we can import from game_systems
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DATABASE_NAME = "EQ_Game.db"

try:
    from game_systems.data.materials import MATERIALS
except ImportError as e:
    logger.critical(f"Failed to import MATERIALS: {e}")
    sys.exit(1)


def update_schema():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cur = conn.cursor()

        logger.info("Updating Database Schema (Inventory)...")

        # 1. Create Materials Table (Loot definitions)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            rarity TEXT DEFAULT 'Common',
            value INTEGER DEFAULT 0
        )
        """)
        logger.info("✔ Table 'materials' checked/created.")

        # 2. Create Inventory Table (Player backpack)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            item_key TEXT NOT NULL,
            item_name TEXT NOT NULL,
            item_type TEXT NOT NULL,
            rarity TEXT DEFAULT 'Common',
            slot TEXT,
            item_source_table TEXT,
            count INTEGER DEFAULT 1,
            equipped INTEGER DEFAULT 0,
            FOREIGN KEY(discord_id) REFERENCES players(discord_id)
        )
        """)
        logger.info("✔ Table 'inventory' checked/created.")

        # 3. Populate Materials
        logger.info("Populating Materials...")

        data = [(key, d["name"], d["description"], d["rarity"], d["value"]) for key, d in MATERIALS.items()]

        cur.executemany(
            """
            INSERT OR REPLACE INTO materials (key_id, name, description, rarity, value)
            VALUES (?, ?, ?, ?, ?)
        """,
            data,
        )

        logger.info(f"✔ Populated/Updated {len(data)} material definitions.")

        conn.commit()
        conn.close()
        logger.info("Inventory Schema Update Complete.")

    except Exception as e:
        logger.critical(f"Update failed: {e}", exc_info=True)


if __name__ == "__main__":
    update_schema()
