import json
import logging
import os
import sys

# Add repo root to path so we can import game_systems
sys.path.append(os.getcwd())

from game_systems.data.monsters import MONSTERS

logger = logging.getLogger("eldoria.data.export")
logging.basicConfig(level=logging.INFO)

def export_monsters():
    json_monsters = {}

    for key, monster in MONSTERS.items():
        m_data = monster.copy()

        # Convert skills list of dicts to list of key_ids
        skill_keys = []
        if "skills" in m_data:
            for skill in m_data["skills"]:
                if isinstance(skill, dict) and "key_id" in skill:
                    skill_keys.append(skill["key_id"])
                else:
                    logger.warning(f"Warning: Skill in {key} missing key_id or not a dict: {skill}")
            m_data["skills"] = skill_keys

        # drops are list of tuples, json dump handles this automatically (converts to list of lists)

        json_monsters[key] = m_data

    output_path = "game_systems/data/monsters.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_monsters, f, indent=4)
        logger.info(f"Successfully exported {len(json_monsters)} monsters to {output_path}")
    except Exception as e:
        logger.error(f"Failed to export monsters: {e}")

if __name__ == "__main__":
    export_monsters()
