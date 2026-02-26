"""
materials.py

Defines all 'Material' type items found in Eldoria.
Loads material data from 'materials.json'.
REBALANCED: Sell values increased to improve economy flow.
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import MATERIAL_SCHEMA

logger = logging.getLogger("eldoria.data")


def load_materials():
    """
    Loads material data from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "materials.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: materials.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: materials.json is invalid JSON: {e}")
        return {}

    # Validate Schema
    top_schema = {"type": dict, "values_schema": {"type": dict, "schema": MATERIAL_SCHEMA}}

    errors = DataValidator.validate(data, top_schema, "materials")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded material data contains schema errors.")

    validated_materials = data
    logger.info(f"Loaded {len(validated_materials)} materials from {data_path.name}")
    return validated_materials


MATERIALS = load_materials()
