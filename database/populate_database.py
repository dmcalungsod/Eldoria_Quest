"""
populate_database.py

Loads data from all game dictionary modules and inserts them into EQ_Game.db.
This script is modular and imports data from the /game_systems/data/ directory.
"""

import json
import os
import sqlite3
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DB = "EQ_Game.db"

# Attempt imports from the game_systems.data package
try:
    # --- END FIX ---
    from game_systems.data import consumables, materials, monsters, quest_data, quest_items, skills_data
    from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
    from game_systems.data.class_equipments import CLASS_EQUIPMENTS

    # --- FIX: We now import the new data dictionaries ---
    from game_systems.data.equipments import EQUIPMENT_DATA
except ImportError as e:
    print("Failed to import data modules from 'game_systems/data'.")
    print("Please ensure you are running this script from the root of the project.")
    print(f"Import error: {e}")
    sys.exit(1)


def insert_classes(conn):
    cur = conn.cursor()
    print("Inserting classes...")

    classes_to_insert = []
    for name, data in CLASS_DEFINITIONS.items():
        classes_to_insert.append((data["id"], name, data["description"]))

    cur.executemany(
        "INSERT OR IGNORE INTO classes (id, name, description) VALUES (?, ?, ?);",
        classes_to_insert,
    )
    conn.commit()


def insert_monsters(conn):
    cur = conn.cursor()
    print("Inserting monsters...")
    # Clear existing monsters to prevent duplicates on re-run
    cur.execute("DELETE FROM monsters;")
    for key, m in monsters.MONSTERS.items():
        name = m.get("name")
        description = m.get("description", "")
        tier = m.get("tier", "Normal")
        level = int(m.get("level", 1))
        hp = int(m.get("hp", 1))
        attack = int(m.get("atk", 1))
        defense = int(m.get("def", 0))
        dex = int(m.get("dex", 0)) if "dex" in m else level
        magic = int(m.get("magic", 0)) if "magic" in m else 0
        xp = int(m.get("xp", max(1, level * 5)))
        biome = m.get("biome", "Forest")

        cur.execute(
            """
            INSERT INTO monsters (name, description, tier, level, hp, attack, defense, dexterity, magic, exp_drop, biome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                name,
                description,
                tier,
                level,
                hp,
                attack,
                defense,
                dex,
                magic,
                xp,
                biome,
            ),
        )

    conn.commit()


def insert_quest_items(conn):
    cur = conn.cursor()
    print("Inserting quest items...")
    cur.execute("DELETE FROM quest_items;")
    for key, q in quest_items.QUEST_ITEMS.items():
        cur.execute(
            """
            INSERT INTO quest_items (name, description, rarity, quest_id, value)
            VALUES (?, ?, ?, NULL, ?)
        """,
            (
                q.get("name"),
                q.get("notes", ""),
                q.get("rarity", "Common"),
                q.get("value", 0),
            ),
        )
    conn.commit()


def insert_consumables(conn):
    cur = conn.cursor()
    print("Inserting consumables...")
    cur.execute("DELETE FROM consumables;")
    for key, c in consumables.CONSUMABLES.items():
        cur.execute(
            """
            INSERT INTO consumables (name, description, rarity, effect, value)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                c.get("name"),
                c.get("description", ""),
                c.get("rarity", "Common"),
                json.dumps(c.get("effect", {})),
                c.get("value", 0),
            ),
        )
    conn.commit()


# --- THIS FUNCTION IS REWRITTEN ---
def insert_equipments(conn):
    cur = conn.cursor()
    print("Inserting general equipments...")
    # Clear existing general equipment
    cur.execute("DELETE FROM equipment;")

    # Iterate over the new EQUIPMENT_DATA dictionary
    for key, e in EQUIPMENT_DATA.items():
        stats = e.get("stats_bonus", {})
        cur.execute(
            """
            INSERT INTO equipment (name, description, rarity, slot,
                                   str_bonus, end_bonus, dex_bonus, agi_bonus,
                                   mag_bonus, lck_bonus, min_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                e.get("name"),
                e.get("description", ""),
                e.get("rarity", "Common"),
                e.get("slot", "accessory"),
                stats.get("STR", 0),
                stats.get("END", 0),
                stats.get("DEX", 0),
                stats.get("AGI", 0),
                stats.get("MAG", 0),
                stats.get("LCK", 0),
                e.get("level_req", 1),
            ),
        )
    conn.commit()


# --- END OF REWRITE ---


# --- THIS FUNCTION IS REWRITTEN ---
def insert_class_equipments(conn):
    cur = conn.cursor()
    print("Inserting class-specific equipment...")
    # Clear existing class equipment and item sets
    cur.execute("DELETE FROM class_equipment;")
    cur.execute("DELETE FROM item_sets;")  # Clear old sets, as we don't use them yet

    class_map = {"Warrior": 1, "Mage": 2, "Rogue": 3, "Cleric": 4, "Ranger": 5}

    # Insert class equipment from the new generated dictionary
    for key, ce in CLASS_EQUIPMENTS.items():
        class_id = class_map.get(ce.get("class"), 0)
        if class_id == 0:
            continue

        stats = ce.get("stats_bonus", {})

        cur.execute(
            """
            INSERT INTO class_equipment (class_id, name, description, rarity, slot,
                                         str_bonus, end_bonus, dex_bonus, agi_bonus,
                                         mag_bonus, lck_bonus, set_name, min_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                class_id,
                ce.get("name"),
                ce.get("description", ""),
                ce.get("rarity", "Common"),
                ce.get("slot", "accessory"),
                stats.get("STR", 0),
                stats.get("END", 0),
                stats.get("DEX", 0),
                stats.get("AGI", 0),
                stats.get("MAG", 0),
                stats.get("LCK", 0),
                ce.get("set"),  # Will be None, which is correct
                ce.get("level_req", 1),
            ),
        )
    conn.commit()


# --- END OF REWRITE ---


def insert_quests(conn):
    cur = conn.cursor()
    print("Inserting quests...")

    cur.executemany(
        """
        INSERT OR IGNORE INTO quests (id, title, tier, quest_giver, location, summary, description, objectives, rewards)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        quest_data.ALL_QUESTS,
    )

    conn.commit()


def insert_materials(conn):
    cur = conn.cursor()
    print("Inserting materials...")
    count = 0
    for key, data in materials.MATERIALS.items():
        cur.execute(
            """
            INSERT OR IGNORE INTO materials (key_id, name, description, rarity, value)
            VALUES (?, ?, ?, ?, ?)
        """,
            (key, data["name"], data["description"], data["rarity"], data["value"]),
        )
        count += 1
    conn.commit()
    print(f"✔ Populated {count} material definitions.")


# FIX: Update insert_skills to include buff_data
def insert_skills(conn):
    cur = conn.cursor()
    print("Inserting skills...")
    count = 0
    for key, data in skills_data.SKILLS.items():
        # Combine buff and debuff data and serialize it
        buff_data = data.get("buff") or data.get("debuff")
        buff_data_json = json.dumps(buff_data) if buff_data else None

        cur.execute(
            """
            INSERT OR IGNORE INTO skills (key_id, name, description, type, class_id,
                                          mp_cost, power_multiplier, heal_power, buff_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["key_id"],
                data["name"],
                data["description"],
                data["type"],
                data.get("class_id", 0),  # 0 for 'all classes'
                data.get("mp_cost", 0),
                data.get("power_multiplier", 1.0),
                data.get("heal_power", 0),
                buff_data_json,  # <-- NEW: Insert JSON string of buff/debuff
            ),
        )
        count += 1
    conn.commit()
    print(f"✔ Populated {count} skill definitions.")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        # Note: We skip insert_classes as it's IGNORE
        # We skip insert_quests as it's IGNORE
        # We skip insert_materials as it's IGNORE
        # We skip insert_skills as it's IGNORE

        # These are the functions that need to run to clear old data
        insert_monsters(conn)
        insert_quest_items(conn)
        insert_consumables(conn)
        insert_equipments(conn)
        insert_class_equipments(conn)

        # These only add if missing, safe to run
        insert_classes(conn)
        insert_quests(conn)
        insert_materials(conn)
        insert_skills(conn)

        print("✔ Database population complete.")
    except Exception as e:
        print(f"Error populating database: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
