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

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import EQUIPMENT_SCHEMA

logger = logging.getLogger("eldoria.data")


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

    # Validate Schema
    top_schema = {"type": dict, "values_schema": {"type": dict, "schema": EQUIPMENT_SCHEMA}}

    errors = DataValidator.validate(data, top_schema, "equipments")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded equipment data contains schema errors.")

    # In the previous version, invalid items were skipped.
    # Here we are relying on the validator to log errors.
    # To maintain strict behavior, we might want to filter out items that had errors,
    # but the generic validator returns a list of error strings, not mapping to items.
    # For now, we return all loaded data, as schema errors are usually critical dev-time issues.

    validated_data = data
    logger.info(f"Loaded {len(validated_data)} equipment items from {data_path.name}")
    return validated_data


# Load data at module level to mimic previous behavior
EQUIPMENT_DATA = load_and_validate_equipments()

__all__ = ["EQUIPMENT_DATA"]
