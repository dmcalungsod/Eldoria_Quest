"""
create_database.py

Creates the full Eldoria Quest database schema.
Hardened: Safe schema migration and error reporting.
"""

import logging
import sqlite3

# Only configure logging if running as main script to avoid duplicates
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("db_create")

DATABASE_NAME = "EQ_Game.db"


def create_tables():
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        # -------------------------
        # CREATE TABLES
        # -------------------------
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS players (
            discord_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            race TEXT,
            gender TEXT,
            level INTEGER DEFAULT 1,
            experience INTEGER DEFAULT 0,
            exp_to_next INTEGER DEFAULT 1000,
            vestige_pool INTEGER DEFAULT 0,
            aurum INTEGER DEFAULT 0,
            current_hp INTEGER DEFAULT 100,
            current_mp INTEGER DEFAULT 20,
            last_action_time TEXT,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        );

        CREATE TABLE IF NOT EXISTS stats (
            discord_id INTEGER PRIMARY KEY,
            stats_json TEXT,
            str_exp REAL DEFAULT 0,
            end_exp REAL DEFAULT 0,
            dex_exp REAL DEFAULT 0,
            agi_exp REAL DEFAULT 0,
            mag_exp REAL DEFAULT 0,
            lck_exp REAL DEFAULT 0,
            FOREIGN KEY(discord_id) REFERENCES players(discord_id)
        );

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

        CREATE TABLE IF NOT EXISTS quest_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            rarity TEXT NOT NULL,
            quest_id INTEGER,
            value INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS consumables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            rarity TEXT NOT NULL,
            effect TEXT NOT NULL,
            value INTEGER DEFAULT 0
        );

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

        CREATE TABLE IF NOT EXISTS item_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            set_name TEXT NOT NULL,
            bonus_description TEXT
        );

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

        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            tier TEXT NOT NULL,
            quest_giver TEXT,
            location TEXT,
            summary TEXT,
            description TEXT,
            objectives TEXT,
            rewards TEXT
        );

        CREATE TABLE IF NOT EXISTS player_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            quest_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            progress TEXT,
            FOREIGN KEY(discord_id) REFERENCES players(discord_id),
            FOREIGN KEY(quest_id) REFERENCES quests(id)
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            rarity TEXT DEFAULT 'Common',
            value INTEGER DEFAULT 0
        );

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
            buff_data TEXT,
            learn_cost INTEGER DEFAULT 0,
            upgrade_cost INTEGER DEFAULT 0,
            FOREIGN KEY(class_id) REFERENCES classes(id)
        );

        CREATE TABLE IF NOT EXISTS player_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            skill_key TEXT NOT NULL,
            skill_level INTEGER DEFAULT 1,
            skill_exp REAL DEFAULT 0,
            FOREIGN KEY(discord_id) REFERENCES players(discord_id),
            FOREIGN KEY(skill_key) REFERENCES skills(key_id)
        );

        CREATE TABLE IF NOT EXISTS global_boosts (
            boost_key TEXT PRIMARY KEY,
            multiplier REAL DEFAULT 1.0,
            end_time TEXT NOT NULL
        );

        -- Performance Indexes
        CREATE INDEX IF NOT EXISTS idx_inventory_discord_id ON inventory(discord_id);
        CREATE INDEX IF NOT EXISTS idx_player_skills_discord_id ON player_skills(discord_id);
        CREATE INDEX IF NOT EXISTS idx_player_skills_skill_key ON player_skills(skill_key);
        CREATE INDEX IF NOT EXISTS idx_player_quests_discord_id ON player_quests(discord_id);
        CREATE INDEX IF NOT EXISTS idx_player_quests_quest_id ON player_quests(quest_id);
        """)

        # ---------------------------------------------------
        # SCHEMA MIGRATION (Safe Column Adding)
        # ---------------------------------------------------

        # List of columns to ensure exist in 'skills'
        skills_columns = [
            ("buff_data", "TEXT"),
            ("learn_cost", "INTEGER DEFAULT 0"),
            ("upgrade_cost", "INTEGER DEFAULT 0"),
        ]

        for col_name, col_type in skills_columns:
            try:
                cursor.execute(f"ALTER TABLE skills ADD COLUMN {col_name} {col_type};")
                logger.info(f"✔ Column '{col_name}' added to 'skills' table.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    pass  # Column exists, safe to ignore
                else:
                    logger.warning(f"Migration warning for {col_name}: {e}")

        # Ensure stat_exp columns in 'stats'
        stat_exp_columns = [
            "str_exp REAL DEFAULT 0",
            "end_exp REAL DEFAULT 0",
            "dex_exp REAL DEFAULT 0",
            "agi_exp REAL DEFAULT 0",
            "mag_exp REAL DEFAULT 0",
            "lck_exp REAL DEFAULT 0",
        ]
        for column_def in stat_exp_columns:
            try:
                cursor.execute(f"ALTER TABLE stats ADD COLUMN {column_def};")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    pass
                else:
                    logger.warning(f"Migration warning for stats: {e}")

        # Ensure skill_exp in 'player_skills'
        try:
            cursor.execute("ALTER TABLE player_skills ADD COLUMN skill_exp REAL DEFAULT 0;")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                logger.warning(f"Migration warning: {e}")

        logger.info("Database schema checked/created.")
        conn.commit()
        conn.close()

    except Exception as e:
        logger.critical(f"Schema creation failed: {e}")
        raise


if __name__ == "__main__":
    create_tables()
