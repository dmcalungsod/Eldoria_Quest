"""
CONSUMABLES — Eldoria Quest
--------------------------------------------------
Loads consumable data from 'consumables.json'.
Items are defined by ID, name, type, effect, rarity, and description.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("eldoria.data")


def load_consumables():
    """
    Loads consumable data from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "consumables.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: consumables.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: consumables.json is invalid JSON: {e}")
        return {}

    validated_consumables = {}
    required_keys = {"id", "name", "type", "effect", "rarity", "description"}

    for key, item in data.items():
        # Check required keys
        missing_keys = required_keys - item.keys()
        if missing_keys:
            logger.warning(
                f"Consumable '{key}' missing required keys: {missing_keys}. Skipping."
            )
            continue

        # Additional Type Checks
        if not isinstance(item["effect"], dict):
            logger.warning(
                f"Consumable '{key}': 'effect' must be a dictionary. Skipping."
            )
            continue

        validated_consumables[key] = item

    logger.info(
        f"Loaded {len(validated_consumables)} consumables from {data_path.name}"
    )
    return validated_consumables


CONSUMABLES = load_consumables()

__all__ = ["CONSUMABLES"]
