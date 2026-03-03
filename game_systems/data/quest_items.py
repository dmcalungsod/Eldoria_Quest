"""
QUEST_ITEMS — Eldoria Quest (Forest beginner zone)
--------------------------------------------------
A curated list of 30 quest items for early quests in the forest region.
Each quest item:
{
  "id": "quest_key",
  "name": str,
  "rarity": str,
  "notes": str
}
Rarities: Common, Uncommon, Rare, Epic, Legendary, Mythical (quests may demand high rarities)
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import QUEST_ITEM_SCHEMA

logger = logging.getLogger("eldoria.data")


def load_quest_items():
    """
    Loads quest item data from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "quest_items.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: quest_items.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: quest_items.json is invalid JSON: {e}")
        return {}

    # Validate Schema
    top_schema = {
        "type": dict,
        "values_schema": {"type": dict, "schema": QUEST_ITEM_SCHEMA},
    }

    errors = DataValidator.validate(data, top_schema, "quest_items")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded quest item data contains schema errors.")

    validated_quest_items = data
    logger.info(
        f"Loaded {len(validated_quest_items)} quest items from {data_path.name}"
    )
    return validated_quest_items


QUEST_ITEMS = load_quest_items()

__all__ = ["QUEST_ITEMS"]
