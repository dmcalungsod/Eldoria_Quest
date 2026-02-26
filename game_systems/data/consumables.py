"""
CONSUMABLES — Eldoria Quest
--------------------------------------------------
Loads consumable data from 'consumables.json'.
Items are defined by ID, name, type, effect, rarity, and description.
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import CONSUMABLE_SCHEMA

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

    # Validate Schema
    top_schema = {
        "type": dict,
        "values_schema": {
            "type": dict,
            "schema": CONSUMABLE_SCHEMA
        }
    }

    errors = DataValidator.validate(data, top_schema, "consumables")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded consumable data contains schema errors.")

    # Pass through data if valid (or partially valid, validator only logs)
    # The validator iterates and finds errors but doesn't filter.
    # We could implement filtering of invalid items if desired, but for now we keep behavior consistent.

    validated_consumables = data
    logger.info(f"Loaded {len(validated_consumables)} consumables from {data_path.name}")
    return validated_consumables


CONSUMABLES = load_consumables()

__all__ = ["CONSUMABLES"]
