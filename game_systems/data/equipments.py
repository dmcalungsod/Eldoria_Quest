"""
EQUIPMENTS — Eldoria Quest (General equipment pool)
---------------------------------------------------
This module loads equipment data from 'equipments.json'.
Items are defined by rarity, slot, and stats.

Stats are now balanced for a 999-cap system using a
Level * Rarity formula.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("eldoria.data")

# --- Validation Constants ---
VALID_RARITIES = {
    "Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"
}

VALID_SLOTS = {
    # Weapons
    "sword", "greatsword", "mace", "shield", "staff", "tome", "orb",
    "dagger", "offhand_dagger", "bow", "quiver",
    # Armor (Heavy)
    "helm", "heavy_armor", "heavy_gloves", "heavy_boots", "heavy_legs",
    # Armor (Medium / Leather)
    "leather_cap", "medium_armor", "rogue_armor", "medium_gloves",
    "medium_boots", "medium_legs", "leather_hood",
    # Armor (Light / Cloth)
    "hood", "robe", "gloves", "boots", "legs", "vestments", "miter",
    # Misc
    "belt", "accessory"
}


def load_and_validate_equipments():
    """
    Loads equipment data from JSON file, validates it against the schema,
    and returns a dictionary of valid items.
    """
    data_path = Path(__file__).parent / "equipments.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: equipments.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: equipments.json is invalid JSON: {e}")
        return {}

    validated_data = {}

    for key, item in data.items():
        # 1. Check required keys
        required_keys = {"name", "slot", "rarity", "level_req", "stats_bonus", "description"}
        missing_keys = required_keys - item.keys()
        if missing_keys:
            logger.warning(f"Item '{key}' missing required keys: {missing_keys}. Skipping.")
            continue

        # 2. Check types
        if not isinstance(item["name"], str):
            logger.warning(f"Item '{key}': 'name' must be a string. Skipping.")
            continue
        if not isinstance(item["level_req"], int) or item["level_req"] < 1:
            logger.warning(f"Item '{key}': 'level_req' must be a positive integer. Skipping.")
            continue
        if not isinstance(item["stats_bonus"], dict):
            logger.warning(f"Item '{key}': 'stats_bonus' must be a dictionary. Skipping.")
            continue
        if not isinstance(item["description"], str):
            logger.warning(f"Item '{key}': 'description' must be a string. Skipping.")
            continue

        # 3. Check allowed values (Enums)
        if item["rarity"] not in VALID_RARITIES:
             logger.warning(f"Item '{key}': Invalid rarity '{item['rarity']}'. Valid: {VALID_RARITIES}. Skipping.")
             continue

        if item["slot"] not in VALID_SLOTS:
             logger.warning(f"Item '{key}': Invalid slot '{item['slot']}'. Skipping.")
             continue

        # If all checks pass, add to validated data
        validated_data[key] = item

    logger.info(f"Loaded {len(validated_data)} equipment items from {data_path.name}")
    return validated_data

# Load data at module level to mimic previous behavior
EQUIPMENT_DATA = load_and_validate_equipments()

__all__ = ["EQUIPMENT_DATA"]
