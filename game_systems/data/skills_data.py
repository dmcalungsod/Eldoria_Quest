"""
skills_data.py

Contains all skill definitions for Eldoria Quest.
This data is now loaded from 'skills.json'.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("eldoria.data")

MAGIC_SKILL_TYPES = [
    "magical",
    "fire",
    "ice",
    "poison",
    "water",
    "wind",
    "earth",
    "dark",
    "holy",
]


def load_skills():
    """
    Loads skill data from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "skills.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: skills.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: skills.json is invalid JSON: {e}")
        return {}

    validated_skills = {}
    required_keys = {"key_id", "name", "type", "class_id", "mp_cost"}

    for key, skill in data.items():
        # Check required keys
        missing_keys = required_keys - skill.keys()
        if missing_keys:
            logger.warning(f"Skill '{key}' missing required keys: {missing_keys}. Skipping.")
            continue

        # Type Validation
        if not isinstance(skill["name"], str):
            logger.warning(f"Skill '{key}': 'name' must be a string. Skipping.")
            continue
        if not isinstance(skill["mp_cost"], int) or skill["mp_cost"] < 0:
            logger.warning(f"Skill '{key}': 'mp_cost' must be a non-negative integer. Skipping.")
            continue
        if not isinstance(skill["class_id"], int):
            logger.warning(f"Skill '{key}': 'class_id' must be an integer. Skipping.")
            continue

        # Validated
        validated_skills[key] = skill

    logger.info(f"Loaded {len(validated_skills)} skills from {data_path.name}")
    return validated_skills


SKILLS = load_skills()

__all__ = ["SKILLS", "MAGIC_SKILL_TYPES"]
