"""
adventure_locations.py

Defines the exploration zones available to adventurers.
Each location dictates the monster pool, difficulty, and rewards.

This module loads location data from 'adventure_locations.json'.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("eldoria.data")


def load_locations():
    """
    Loads location data from JSON file, validates it, and performs necessary type conversions.
    """
    data_path = Path(__file__).parent / "adventure_locations.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: adventure_locations.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: adventure_locations.json is invalid JSON: {e}")
        return {}

    validated_locations = {}

    for key, location_data in data.items():
        # Basic Schema Validation
        if "name" not in location_data:
            logger.warning(f"Location '{key}' missing required field 'name'. Skipping.")
            continue

        # Convert lists back to tuples for backward compatibility
        # JSON loads as list of lists: [["monster_id", weight], ...]

        if "monsters" in location_data:
            location_data["monsters"] = [tuple(m) for m in location_data["monsters"]]

        if "night_monsters" in location_data:
            location_data["night_monsters"] = [tuple(m) for m in location_data["night_monsters"]]

        if "gatherables" in location_data:
            location_data["gatherables"] = [tuple(g) for g in location_data["gatherables"]]

        validated_locations[key] = location_data

    logger.info(f"Loaded {len(validated_locations)} locations from {data_path.name}")
    return validated_locations


LOCATIONS = load_locations()

__all__ = ["LOCATIONS"]
