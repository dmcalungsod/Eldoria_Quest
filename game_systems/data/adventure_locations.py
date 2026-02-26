"""
adventure_locations.py

Defines the exploration zones available to adventurers.
Each location dictates the monster pool, difficulty, and rewards.

This file now loads data from 'adventure_locations.json' for better maintainability.
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator

logger = logging.getLogger("eldoria.data")


def load_locations():
    """
    Loads location data from JSON file, validates it, and processes it
    for backward compatibility (converting lists to tuples).
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

    # Validate Schema
    errors = DataValidator.validate_location_schema(data)
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        # We might want to raise an error or continue with partial data.
        # For now, we log errors but try to proceed if possible, though schema errors usually mean broken data.
        logger.warning("Loaded location data contains schema errors.")

    processed_locations = {}

    for loc_id, loc_data in data.items():
        # Convert lists back to tuples for backward compatibility
        # 'monsters', 'night_monsters', 'gatherables' are defined as lists of lists in JSON
        # effectively [[id, weight], ...]
        # We convert them to [(id, weight), ...]

        if "monsters" in loc_data and isinstance(loc_data["monsters"], list):
            loc_data["monsters"] = [tuple(m) for m in loc_data["monsters"]]

        if "night_monsters" in loc_data and isinstance(loc_data["night_monsters"], list):
            loc_data["night_monsters"] = [tuple(m) for m in loc_data["night_monsters"]]

        if "gatherables" in loc_data and isinstance(loc_data["gatherables"], list):
            loc_data["gatherables"] = [tuple(g) for g in loc_data["gatherables"]]

        # 'conditional_monsters' is a list of dicts, which is fine as is.
        # 'duration_options' is a list of ints, fine as is.
        # 'special_events' is list of strings, fine as is.

        processed_locations[loc_id] = loc_data

    logger.info(f"Loaded {len(processed_locations)} adventure locations from {data_path.name}")
    return processed_locations


LOCATIONS = load_locations()

__all__ = ["LOCATIONS"]
