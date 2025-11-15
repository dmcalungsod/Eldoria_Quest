"""
create_database.py

Creates the full Eldoria Quest database schema from scratch
IF IT DOES NOT ALREADY EXIST.
"""

import sqlite3

DATABASE_NAME = "EQ_Game.db"


def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # -------------------------
    # DROP OLD TABLES (REMOVED)
    # -------------------------
    # All "DROP TABLE" commands have been removed to ensure data persistence.
    # The script will now only create tables if they are missing.

    # -------------------------
    # CREATE TABLES
    # -------------------------
    cursor.executescript(
        """
    -- 1. Class Definitions
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    );

    -- 2. Player Data
    CREATE TABLE IF NOT EXISTS players (
        discord_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        class_id INTEGER NOT NULL,
        race TEXT,
        gender TEXT,
        level INTEGER DEFAULT 1,
        experience INTEGER DEFAULT 0,
        
        -- --- CHANGE 1: Set new default ---
        exp_to_next INTEGER DEFAULT 1000,
        
        -- --- CHANGE 2: Add new Vestige pool ---
        vestige_pool INTEGER DEFAULT 0,

        aurum INTEGER DEFAULT 0,
        current_hp INTEGER DEFAULT 100,
        current_mp INTEGER DEFAULT 20,
        last_action_time TEXT,
        
        FOREIGN KEY(class_id) REFERENCES classes(id)
    );

    -- 3. Player Stats
    CREATE TABLE IF NOT EXISTS stats (
        discord_id INTEGER PRIMARY KEY,
        stats_json TEXT,

        FOREIGN KEY(discord_id) REFERENCES players(discord_id)
    );

    -- 4. Monsters
    CREATE TABLE IF NOT EXISTS monsters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        tier TEXT NOT NULL,
        level INTEGER NOT NULL,
        hp INTEGER NOT NULL,
        attack INTEGER NOT NULL,
        defense INTEGER NOT NULL,
        dexterity INTEGER NOT NULL,
        magic INTEGER NOT NULL,
        exp_drop INTEGER NOT NULL,
        biome TEXT NOT NULL
    );

    -- 5. Quest Items
    CREATE TABLE IF NOT EXISTS quest_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        rarity TEXT NOT NULL,
        quest_id INTEGER,
        value INTEGER DEFAULT 0
    );

    -- 6. Consumables
    CREATE TABLE IF NOT EXISTS consumables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        rarity TEXT NOT NULL,
        effect TEXT NOT NULL,
        value INTEGER DEFAULT 0
    );

    -- 7. General Equipment (6-stat system)
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        rarity TEXT NOT NULL,
        slot TEXT NOT NULL,
        str_bonus INTEGER DEFAULT 0,
        end_bonus INTEGER DEFAULT 0,
        dex_bonus INTEGER DEFAULT 0,
        agi_bonus INTEGER DEFAULT 0,
        mag_bonus INTEGER DEFAULT 0,
        lck_bonus INTEGER DEFAULT 0,
        min_level INTEGER DEFAULT 1
    );

    -- 8. Class-Specific Equipment (6-stat system)
    CREATE TABLE IF NOT EXISTS class_equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        rarity TEXT NOT NULL,
        slot TEXT NOT NULL,
        str_bonus INTEGER DEFAULT 0,
        end_bonus INTEGER DEFAULT 0,
        dex_bonus INTEGER DEFAULT 0,
        agi_bonus INTEGER DEFAULT 0,
        mag_bonus INTEGER DEFAULT 0,
        lck_bonus INTEGER DEFAULT 0,
        set_name TEXT,
        min_level INTEGER DEFAULT 1,

        FOREIGN KEY(class_id) REFERENCES classes(id)
    );

    -- 9. Item Sets
    CREATE TABLE IF NOT EXISTS item_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        set_name TEXT NOT NULL,
        bonus_description TEXT
    );

    -- 10. Guild Members
    CREATE TABLE IF NOT EXISTS guild_members (
        discord_id INTEGER PRIMARY KEY,
        rank TEXT DEFAULT 'F',
        join_date TEXT NOT NULL,
        merit_points INTEGER DEFAULT 0,
        quests_completed INTEGER DEFAULT 0,
        normal_kills INTEGER DEFAULT 0,
        elite_kills INTEGER DEFAULT 0,
        boss_kills INTEGER DEFAULT 0,
        special_notes TEXT,

        FOREIGN KEY(discord_id) REFERENCES players(discord_id)
    );

    -- 11. Quests
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        tier TEXT NOT NULL,
        quest_giver TEXT,
        location TEXT,
        summary TEXT,
        description TEXT,
        objectives TEXT, -- JSON
        rewards TEXT -- JSON
    );

    -- 12. Player Quests
    CREATE TABLE IF NOT EXISTS player_quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id INTEGER NOT NULL,
        quest_id INTEGER NOT NULL,
        status TEXT NOT NULL, -- "in_progress", "completed"
        progress TEXT, -- JSON

        FOREIGN KEY(discord_id) REFERENCES players(discord_id),
        FOREIGN KEY(quest_id) REFERENCES quests(id)
    );
    
    -- 13. Materials (Loot Definitions)
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id TEXT UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        rarity TEXT DEFAULT 'Common',
        value INTEGER DEFAULT 0
    );

    -- 14. Inventory (Player Backpack)
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
    );
    
    -- 15. Adventure Sessions
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
    );
    
    -- 16. Skill Definitions
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_id TEXT UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT DEFAULT 'Active',
        class_id INTEGER,
        
        mp_cost INTEGER DEFAULT 0,
        power_multiplier REAL DEFAULT 1.0,
        heal_power INTEGER DEFAULT 0,
        
        FOREIGN KEY(class_id) REFERENCES classes(id)
    );
    
    -- 17. Player Skills
    CREATE TABLE IF NOT EXISTS player_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id INTEGER NOT NULL,
        skill_key TEXT NOT NULL,
        skill_level INTEGER DEFAULT 1,
        
        FOREIGN KEY(discord_id) REFERENCES players(discord_id),
        FOREIGN KEY(skill_key) REFERENCES skills(key_id)
    );
    """
    )

    conn.commit()
    conn.close()
    print("✔ Eldoria Quest database schema checked/created successfully.")


if __name__ == "__main__":
    create_tables()
