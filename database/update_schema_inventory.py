"""
update_schema_inventory.py

Adds 'materials' and 'inventory' tables to EQ_Game.db.
Populates the materials table using data from game_systems/data/materials.py.
"""

import sqlite3
import sys
import os

# Ensure we can import from game_systems
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_systems.data.materials import MATERIALS

DB_NAME = "EQ_Game.db"

def update_schema():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    print("--- Updating Database Schema ---")

    # 1. Create Materials Table (Loot definitions)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id TEXT UNIQUE,  -- internal key like 'magic_stone_small'
        name TEXT NOT NULL,
        description TEXT,
        rarity TEXT DEFAULT 'Common',
        value INTEGER DEFAULT 0
    )
    """)
    print("✔ Table 'materials' checked/created.")

    # 2. Create Inventory Table (Player backpack)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id INTEGER NOT NULL,
        item_key TEXT NOT NULL,   -- Links to materials.key_id or equipment.id
        item_name TEXT NOT NULL,  -- Cached name for display
        item_type TEXT NOT NULL,  -- 'material', 'consumable', 'equipment'
        count INTEGER DEFAULT 1,
        equipped INTEGER DEFAULT 0, -- 0 = False, 1 = True
        
        FOREIGN KEY(discord_id) REFERENCES players(discord_id)
    )
    """)
    print("✔ Table 'inventory' checked/created.")

    # 3. Populate Materials from the Data File
    print("--- Populating Materials ---")
    count = 0
    for key, data in MATERIALS.items():
        # We use INSERT OR REPLACE to update values if you change balancing in materials.py
        cur.execute("""
            INSERT OR REPLACE INTO materials (key_id, name, description, rarity, value)
            VALUES (?, ?, ?, ?, ?)
        """, (key, data['name'], data['description'], data['rarity'], data['value']))
        count += 1
    
    print(f"✔ Populated {count} material definitions.")

    conn.commit()
    conn.close()
    print("--- Update Complete ---")

if __name__ == "__main__":
    update_schema()