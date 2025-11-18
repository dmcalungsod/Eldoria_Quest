"""
update_schema_adventure.py

Adds the 'adventure_sessions' table to tracking ongoing explorations.
"""

import sqlite3

DB_NAME = "EQ_Game.db"

def update_schema():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print("--- Updating Database Schema (Adventures) ---")

    # Table to track active adventures
    # Note: Logs and Loot are stored as JSON strings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS adventure_sessions (
        discord_id INTEGER PRIMARY KEY,
        location_id TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        duration_minutes INTEGER NOT NULL,
        active INTEGER DEFAULT 1,
        logs TEXT DEFAULT '[]',
        loot_collected TEXT DEFAULT '{}'
    )
    """)
    print("✔ Table 'adventure_sessions' created/checked.")

    conn.commit()
    conn.close()
    print("--- Adventure Schema Update Complete ---")

if __name__ == "__main__":
    update_schema()
