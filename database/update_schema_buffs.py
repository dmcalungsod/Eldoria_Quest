import logging
import sqlite3

DATABASE_NAME = "EQ_Game.db"

def update_schema():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("db_update")

    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        logger.info("Creating 'active_buffs' table if not exists...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_buffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            buff_id TEXT NOT NULL,
            name TEXT NOT NULL,
            stat TEXT NOT NULL,
            amount REAL NOT NULL,
            end_time TEXT NOT NULL,
            FOREIGN KEY(discord_id) REFERENCES players(discord_id)
        );
        """)

        logger.info("Creating index on discord_id...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_active_buffs_discord_id ON active_buffs(discord_id);")

        conn.commit()
        conn.close()
        logger.info("Schema update complete.")

    except Exception as e:
        logger.error(f"Schema update failed: {e}")

if __name__ == "__main__":
    update_schema()
