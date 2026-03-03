"""
MONSTERS — Eldoria Quest
------------------------
This module loads monster data from 'monsters.json'.
Monsters are defined by ID, name, level, stats, drops, and skills.
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import MONSTER_SCHEMA
from game_systems.monsters.monster_skills import MONSTER_SKILLS

logger = logging.getLogger("eldoria.data")


def load_monsters():
    """
    Loads monster data from JSON file, validates it, and rehydrates
    skill references into actual skill objects.
    """
    data_path = Path(__file__).parent / "monsters.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: monsters.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: monsters.json is invalid JSON: {e}")
        return {}

    # Validate Schema
    # Root is dict of {monster_key: monster_data}
    top_schema = {"type": dict, "values_schema": {"type": dict, "schema": MONSTER_SCHEMA}}

    errors = DataValidator.validate(data, top_schema, "monsters")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded monster data contains schema errors.")

    validated_monsters = {}

    for key, monster_data in data.items():
        # Rehydrate Skills
        # The JSON contains list of skill keys (strings)
        skill_keys = monster_data.get("skills", [])
        hydrated_skills = []
        for skill_key in skill_keys:
            if skill_key in MONSTER_SKILLS:
                hydrated_skills.append(MONSTER_SKILLS[skill_key])
            else:
                logger.warning(f"Monster '{key}' ({monster_data.get('name')}) references unknown skill '{skill_key}'")

        monster_data["skills"] = hydrated_skills

        # Convert drops back to tuples for backward compatibility
        # JSON loads as list of lists: [["item_id", chance], ...]
        if "drops" in monster_data:
            monster_data["drops"] = [tuple(d) for d in monster_data["drops"]]

        validated_monsters[key] = monster_data

    logger.info(f"Loaded {len(validated_monsters)} monsters from {data_path.name}")
    return validated_monsters


class MonsterData:
    _monsters = None

    @classmethod
    def get_all(cls):
        if cls._monsters is None:
            cls._monsters = load_monsters()
        return cls._monsters


def __getattr__(name):
    if name == "MONSTERS":
        return MonsterData.get_all()
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["MonsterData"]
