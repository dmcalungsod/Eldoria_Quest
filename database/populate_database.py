"""
populate_database.py

Loads data from all game dictionary modules and inserts them into MongoDB.
Hardened: Bulk upserts for idempotent seeding.
"""

import json
import logging
import os
import sys

from pymongo import MongoClient

# Only configure logging if running as main script
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger("db_populate")

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "eldoria_quest"

try:
    from game_systems.data import (
        consumables,
        materials,
        monsters,
        quest_data,
        quest_items,
        skills_data,
    )
    from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS
    from game_systems.data.class_equipments import CLASS_EQUIPMENTS
    from game_systems.data.equipments import EQUIPMENT_DATA
except ImportError as e:
    logger.critical(f"Failed to import data modules: {e}")
    sys.exit(1)


def _upsert_many(col, key_field, docs):
    """Helper: upserts a list of docs by key_field."""
    from pymongo import UpdateOne

    if not docs:
        return
    ops = [UpdateOne({key_field: d[key_field]}, {"$set": d}, upsert=True) for d in docs]
    col.bulk_write(ops)


def insert_classes(db):
    logger.info("Inserting classes...")
    data = []
    for name, d in CLASS_DEFINITIONS.items():
        data.append({"id": d["id"], "name": name, "description": d["description"]})
    _upsert_many(db["classes"], "id", data)


def insert_monsters(db):
    logger.info("Inserting monsters...")
    db["monsters"].delete_many({})

    data = []
    auto_id = 1
    for m in monsters.MONSTERS.values():
        data.append(
            {
                "id": auto_id,
                "name": m.get("name"),
                "description": m.get("description", ""),
                "tier": m.get("tier", "Normal"),
                "level": int(m.get("level", 1)),
                "hp": int(m.get("hp", 1)),
                "attack": int(m.get("atk", 1)),
                "defense": int(m.get("def", 0)),
                "dexterity": int(m.get("dex", 0)),
                "magic": int(m.get("magic", 0)),
                "exp_drop": int(m.get("xp", 1)),
                "biome": m.get("biome", "Forest"),
            }
        )
        auto_id += 1

    if data:
        db["monsters"].insert_many(data)


def insert_quest_items(db):
    logger.info("Inserting quest items...")
    db["quest_items"].delete_many({})

    data = []
    auto_id = 1
    for q in quest_items.QUEST_ITEMS.values():
        data.append(
            {
                "id": auto_id,
                "name": q["name"],
                "description": q.get("notes", ""),
                "rarity": q.get("rarity", "Common"),
                "quest_id": None,
                "value": q.get("value", 0),
            }
        )
        auto_id += 1

    if data:
        db["quest_items"].insert_many(data)


def insert_consumables(db):
    logger.info("Inserting consumables...")
    db["consumables"].delete_many({})

    data = []
    auto_id = 1
    for c in consumables.CONSUMABLES.values():
        data.append(
            {
                "id": auto_id,
                "name": c["name"],
                "description": c.get("description", ""),
                "rarity": c.get("rarity", "Common"),
                "effect": json.dumps(c.get("effect", {})),
                "value": c.get("value", 0),
            }
        )
        auto_id += 1

    if data:
        db["consumables"].insert_many(data)


def insert_equipments(db):
    logger.info("Inserting general equipment...")
    db["equipment"].delete_many({})

    data = []
    auto_id = 1
    for e in EQUIPMENT_DATA.values():
        s = e.get("stats_bonus", {})
        data.append(
            {
                "id": auto_id,
                "name": e["name"],
                "description": e.get("description", ""),
                "rarity": e.get("rarity", "Common"),
                "slot": e.get("slot", "accessory"),
                "str_bonus": s.get("STR", 0),
                "end_bonus": s.get("END", 0),
                "dex_bonus": s.get("DEX", 0),
                "agi_bonus": s.get("AGI", 0),
                "mag_bonus": s.get("MAG", 0),
                "lck_bonus": s.get("LCK", 0),
                "min_level": e.get("level_req", 1),
            }
        )
        auto_id += 1

    if data:
        db["equipment"].insert_many(data)


def insert_class_equipments(db):
    logger.info("Inserting class equipment...")
    db["class_equipment"].delete_many({})
    db["item_sets"].delete_many({})

    class_map = {"Warrior": 1, "Mage": 2, "Rogue": 3, "Cleric": 4, "Ranger": 5}
    data = []
    auto_id = 1

    for ce in CLASS_EQUIPMENTS.values():
        cid = class_map.get(ce.get("class"), 0)
        if cid == 0:
            continue
        s = ce.get("stats_bonus", {})
        data.append(
            {
                "id": auto_id,
                "class_id": cid,
                "name": ce["name"],
                "description": ce.get("description", ""),
                "rarity": ce.get("rarity", "Common"),
                "slot": ce.get("slot", "accessory"),
                "str_bonus": s.get("STR", 0),
                "end_bonus": s.get("END", 0),
                "dex_bonus": s.get("DEX", 0),
                "agi_bonus": s.get("AGI", 0),
                "mag_bonus": s.get("MAG", 0),
                "lck_bonus": s.get("LCK", 0),
                "set_name": ce.get("set"),
                "min_level": ce.get("level_req", 1),
            }
        )
        auto_id += 1

    if data:
        db["class_equipment"].insert_many(data)


def insert_quests(db):
    logger.info("Inserting quests...")
    quests = []
    for q in quest_data.ALL_QUESTS:
        quests.append(
            {
                "id": q["id"],
                "title": q["title"],
                "tier": q["tier"],
                "quest_giver": q["quest_giver"],
                "location": q["location"],
                "summary": q["summary"],
                "description": q["description"],
                "objectives": q["objectives"],
                "rewards": q["rewards"],
                "prerequisites": q.get("prerequisites", []),
                "flavor_text": q.get("flavor_text", {}),
                "exclusive_group": q.get("exclusive_group"),
            }
        )
    _upsert_many(db["quests"], "id", quests)


def insert_materials(db):
    logger.info("Inserting materials...")
    data = []
    auto_id = 1
    for k, m in materials.MATERIALS.items():
        data.append(
            {
                "id": auto_id,
                "key_id": k,
                "name": m["name"],
                "description": m["description"],
                "rarity": m["rarity"],
                "value": m["value"],
            }
        )
        auto_id += 1
    _upsert_many(db["materials"], "key_id", data)


def insert_skills(db):
    logger.info("Inserting skills...")
    db["skills"].delete_many({})

    data = []
    auto_id = 1
    for s in skills_data.SKILLS.values():
        buff = s.get("buff") or s.get("debuff")
        buff_json = json.dumps(buff) if buff else None
        data.append(
            {
                "id": auto_id,
                "key_id": s["key_id"],
                "name": s["name"],
                "description": s["description"],
                "type": s["type"],
                "class_id": s.get("class_id", 0),
                "mp_cost": s.get("mp_cost", 0),
                "power_multiplier": s.get("power_multiplier", 1.0),
                "heal_power": s.get("heal_power", 0),
                "buff_data": buff_json,
                "learn_cost": s.get("learn_cost", 0),
                "upgrade_cost": s.get("upgrade_cost", 0),
                "scaling_stat": s.get("scaling_stat", "MAG"),
                "scaling_factor": s.get("scaling_factor", 1.0),
            }
        )
        auto_id += 1

    if data:
        db["skills"].insert_many(data)


def main():
    try:
        mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
        db_name = os.getenv("DATABASE_NAME", DEFAULT_DB_NAME)
        if db_name.endswith(".db"):
            db_name = db_name.replace(".db", "").replace(".", "_")

        client = MongoClient(mongo_uri)
        db = client[db_name]

        insert_monsters(db)
        insert_quest_items(db)
        insert_consumables(db)
        insert_equipments(db)
        insert_class_equipments(db)
        insert_classes(db)
        insert_quests(db)
        insert_materials(db)
        insert_skills(db)

        logger.info("Population complete.")
    except Exception as e:
        logger.error(f"Population failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
