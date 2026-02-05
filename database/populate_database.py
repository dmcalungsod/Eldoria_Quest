"""
populate_database.py

Loads data from all game dictionary modules and inserts them into EQ_Game.db.
Hardened: Bulk inserts and path safety.
"""

import json
import logging
import os
import sqlite3
import sys

# Only configure logging if running as main script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("db_populate")

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DATABASE_NAME = "EQ_Game.db"

try:
    from game_systems.data import consumables, materials, monsters, quest_data, quest_items, skills_data
    from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
    from game_systems.data.class_equipments import CLASS_EQUIPMENTS
    from game_systems.data.equipments import EQUIPMENT_DATA
except ImportError as e:
    logger.critical(f"Failed to import data modules: {e}")
    sys.exit(1)


def insert_classes(conn):
    logger.info("Inserting classes...")
    data = [(d["id"], name, d["description"]) for name, d in CLASS_DEFINITIONS.items()]
    conn.executemany("INSERT OR IGNORE INTO classes (id, name, description) VALUES (?, ?, ?);", data)
    conn.commit()


def insert_monsters(conn):
    logger.info("Inserting monsters...")
    conn.execute("DELETE FROM monsters;")

    data = []
    for m in monsters.MONSTERS.values():
        data.append(
            (
                m.get("name"),
                m.get("description", ""),
                m.get("tier", "Normal"),
                int(m.get("level", 1)),
                int(m.get("hp", 1)),
                int(m.get("atk", 1)),
                int(m.get("def", 0)),
                int(m.get("dex", 0)),
                int(m.get("magic", 0)),
                int(m.get("xp", 1)),
                m.get("biome", "Forest"),
            )
        )

    conn.executemany(
        """
        INSERT INTO monsters (name, description, tier, level, hp, attack, defense, dexterity, magic, exp_drop, biome)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )
    conn.commit()


def insert_quest_items(conn):
    logger.info("Inserting quest items...")
    conn.execute("DELETE FROM quest_items;")

    data = [
        (q["name"], q.get("notes", ""), q.get("rarity", "Common"), q.get("value", 0))
        for q in quest_items.QUEST_ITEMS.values()
    ]
    conn.executemany(
        "INSERT INTO quest_items (name, description, rarity, quest_id, value) VALUES (?, ?, ?, NULL, ?)", data
    )
    conn.commit()


def insert_consumables(conn):
    logger.info("Inserting consumables...")
    conn.execute("DELETE FROM consumables;")

    data = []
    for c in consumables.CONSUMABLES.values():
        data.append(
            (
                c["name"],
                c.get("description", ""),
                c.get("rarity", "Common"),
                json.dumps(c.get("effect", {})),
                c.get("value", 0),
            )
        )

    conn.executemany("INSERT INTO consumables (name, description, rarity, effect, value) VALUES (?, ?, ?, ?, ?)", data)
    conn.commit()


def insert_equipments(conn):
    logger.info("Inserting general equipment...")
    conn.execute("DELETE FROM equipment;")

    data = []
    for e in EQUIPMENT_DATA.values():
        s = e.get("stats_bonus", {})
        data.append(
            (
                e["name"],
                e.get("description", ""),
                e.get("rarity", "Common"),
                e.get("slot", "accessory"),
                s.get("STR", 0),
                s.get("END", 0),
                s.get("DEX", 0),
                s.get("AGI", 0),
                s.get("MAG", 0),
                s.get("LCK", 0),
                e.get("level_req", 1),
            )
        )

    conn.executemany(
        """
        INSERT INTO equipment (name, description, rarity, slot, str_bonus, end_bonus, dex_bonus, agi_bonus, mag_bonus, lck_bonus, min_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )
    conn.commit()


def insert_class_equipments(conn):
    logger.info("Inserting class equipment...")
    conn.execute("DELETE FROM class_equipment;")
    conn.execute("DELETE FROM item_sets;")

    class_map = {"Warrior": 1, "Mage": 2, "Rogue": 3, "Cleric": 4, "Ranger": 5}
    data = []

    for ce in CLASS_EQUIPMENTS.values():
        cid = class_map.get(ce.get("class"), 0)
        if cid == 0:
            continue
        s = ce.get("stats_bonus", {})
        data.append(
            (
                cid,
                ce["name"],
                ce.get("description", ""),
                ce.get("rarity", "Common"),
                ce.get("slot", "accessory"),
                s.get("STR", 0),
                s.get("END", 0),
                s.get("DEX", 0),
                s.get("AGI", 0),
                s.get("MAG", 0),
                s.get("LCK", 0),
                ce.get("set"),
                ce.get("level_req", 1),
            )
        )

    conn.executemany(
        """
        INSERT INTO class_equipment (class_id, name, description, rarity, slot, str_bonus, end_bonus, dex_bonus, agi_bonus, mag_bonus, lck_bonus, set_name, min_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )
    conn.commit()


def insert_quests(conn):
    logger.info("Inserting quests...")
    conn.executemany(
        """
        INSERT OR IGNORE INTO quests (id, title, tier, quest_giver, location, summary, description, objectives, rewards)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        quest_data.ALL_QUESTS,
    )
    conn.commit()


def insert_materials(conn):
    logger.info("Inserting materials...")
    data = [(k, m["name"], m["description"], m["rarity"], m["value"]) for k, m in materials.MATERIALS.items()]
    conn.executemany(
        "INSERT OR IGNORE INTO materials (key_id, name, description, rarity, value) VALUES (?, ?, ?, ?, ?)", data
    )
    conn.commit()


def insert_skills(conn):
    logger.info("Inserting skills...")

    # IMPORTANT: Delete old skills to ensure columns are repopulated correctly
    conn.execute("DELETE FROM skills;")

    data = []
    for s in skills_data.SKILLS.values():
        buff = s.get("buff") or s.get("debuff")
        buff_json = json.dumps(buff) if buff else None
        data.append(
            (
                s["key_id"],
                s["name"],
                s["description"],
                s["type"],
                s.get("class_id", 0),
                s.get("mp_cost", 0),
                s.get("power_multiplier", 1.0),
                s.get("heal_power", 0),
                buff_json,
                s.get("learn_cost", 0),
                s.get("upgrade_cost", 0),
            )
        )

    conn.executemany(
        """
        INSERT INTO skills (
            key_id, name, description, type, class_id,
            mp_cost, power_multiplier, heal_power, buff_data,
            learn_cost, upgrade_cost
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        data,
    )
    conn.commit()


def main():
    try:
        conn = sqlite3.connect(DATABASE_NAME)

        insert_monsters(conn)
        insert_quest_items(conn)
        insert_consumables(conn)
        insert_equipments(conn)
        insert_class_equipments(conn)

        insert_classes(conn)
        insert_quests(conn)
        insert_materials(conn)
        insert_skills(conn)

        logger.info("Population complete.")
        conn.close()
    except Exception as e:
        logger.error(f"Population failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
