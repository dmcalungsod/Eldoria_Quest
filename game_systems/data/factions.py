"""
factions.py

Defines the factions available for players to join.
Each faction has a unique identity, goals, and reward structure.

This file loads data from 'factions.json'.
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import FACTION_SCHEMA

logger = logging.getLogger("eldoria.data")


def load_factions():
    """
    Loads faction data from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "factions.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"CRITICAL: factions.json not found at {data_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: factions.json is invalid JSON: {e}")
        return {}

    # Validate Schema
    top_schema = {
        "type": dict,
        "values_schema": {"type": dict, "schema": FACTION_SCHEMA},
    }

    errors = DataValidator.validate(data, top_schema, "factions")
    if errors:
        for err in errors:
            logger.error(f"Validation Error: {err}")
        logger.warning("Loaded faction data contains schema errors.")

    # Convert ranks keys from string to int for backward compatibility
    validated_factions = {}
    for key, faction_data in data.items():
        if "ranks" in faction_data:
            new_ranks = {}
            for rank_level, rank_info in faction_data["ranks"].items():
                new_ranks[int(rank_level)] = rank_info
            faction_data["ranks"] = new_ranks

        # Add default interest for crafting if missing
        if "interests" in faction_data and "crafting" not in faction_data["interests"]:
            faction_data["interests"]["crafting"] = 1.0

        validated_factions[key] = faction_data

    logger.info(f"Loaded {len(validated_factions)} factions from {data_path.name}")
    return validated_factions


FACTIONS = load_factions()

__all__ = ["FACTIONS"]
