"""
populate_database.py

Loads data from all game dictionary modules and inserts them into EQ_Game.db.
This script is modular and imports data from the /game_systems/data/ directory.
"""

import sqlite3
import json
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DB = "EQ_Game.db"

# Attempt imports from the game_systems.data package
try:
    from game_systems.data import monsters
    from game_systems.data import quest_items
    from game_systems.data import consumables
    from game_systems.data import equipments
    from game_systems.data import class_equipments
    from game_systems.data import materials
    from game_systems.data import quest_data

    # --- NEW IMPORT ---
    from game_systems.data import skills_data
    from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
except ImportError as e:
    print(f"Failed to import data modules from 'game_systems/data'.")
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


def insert_equipments(conn):
    cur = conn.cursor()
    print("Inserting general equipments...")
    for key, e in equipments.EQUIPMENTS.items():
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


def insert_class_equipments(conn):
    cur = conn.cursor()
    print("Inserting class-specific equipment...")
    class_map = {"Warrior": 1, "Mage": 2, "Rogue": 3, "Cleric": 4, "Ranger": 5}

    # Insert item sets
    try:
        class_sets = getattr(class_equipments, "CLASS_SETS", {})
        if class_sets:
            print("Inserting item sets...")
            for set_name, meta in class_sets.items():
                cur.execute(
                    "INSERT INTO item_sets (set_name, bonus_description) VALUES (?, ?)",
                    (set_name, json.dumps(meta.get("set_bonus", {}))),
                )
            conn.commit()
    except Exception:
        pass  # Silently skip if data is malformed

    # Insert class equipment
    for key, ce in class_equipments.CLASS_EQUIPMENTS.items():
        class_id = class_map.get(ce.get("class"), 0)
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
                ce.get("set"),
                ce.get("level_req", 1),
            ),
        )
    conn.commit()


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


# --- NEW FUNCTION ---
def insert_skills(conn):
    cur = conn.cursor()
    print("Inserting skills...")
    count = 0
    for key, data in skills_data.SKILLS.items():
        cur.execute(
            """
            INSERT OR IGNORE INTO skills (key_id, name, description, type, class_id)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                data["key_id"],
                data["name"],
                data["description"],
                data["type"],
                data.get("class_id", 0),  # 0 for 'all classes'
            ),
        )
        count += 1
    conn.commit()
    print(f"✔ Populated {count} skill definitions.")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        insert_classes(conn)
        insert_monsters(conn)
        insert_quest_items(conn)
        insert_consumables(conn)
        insert_equipments(conn)
        insert_class_equipments(conn)
        insert_quests(conn)
        insert_materials(conn)
        # --- NEW FUNCTION CALL ---
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
