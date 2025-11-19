"""
update_schema_adventure.py

Adds the 'adventure_sessions' table to tracking ongoing explorations.
Hardened: Uses logging and safe execution block.
"""

import logging
import sqlite3

# Configure logging only if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("db_update_adv")

DATABASE_NAME = "EQ_Game.db"


def update_schema():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        logger.info("Updating Database Schema (Adventures)...")

        # Table to track active adventures
        # Note: Logs and Loot are stored as JSON strings
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS adventure_sessions (
            discord_id INTEGER PRIMARY KEY,
            location_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            active INTEGER DEFAULT 1,
            logs TEXT DEFAULT '[]',
            loot_collected TEXT DEFAULT '{}',
            active_monster_json TEXT DEFAULT NULL
        )
        """)

        logger.info("✔ Table 'adventure_sessions' created/checked.")
        conn.commit()
        conn.close()
        logger.info("Adventure Schema Update Complete.")

    except Exception as e:
        logger.critical(f"Schema update failed: {e}")


if __name__ == "__main__":
    update_schema()
