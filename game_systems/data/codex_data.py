"""
codex_data.py

Defines the foundational Codex data layer for Eldoria Quest.
Loads and validates codex structural metadata (lore, unlock thresholds).
"""

import json
import logging
from pathlib import Path

from game_systems.data.data_validator import DataValidator
from game_systems.data.schemas import CODEX_SCHEMA

logger = logging.getLogger("eldoria.data")


def load_codex_data() -> dict:
    """
    Loads codex metadata from JSON file, validates it, and returns the dictionary.
    """
    data_path = Path(__file__).parent / "codex.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.warning(
            f"Codex data file not found at {data_path}, returning empty schema."
        )
        return {"monsters": {}, "items": {}, "locations": {}, "factions": {}}
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: codex.json is invalid JSON: {e}")
        return {"monsters": {}, "items": {}, "locations": {}, "factions": {}}

    # Validate Schema
    errors = DataValidator.validate(
        data, {"type": dict, "schema": CODEX_SCHEMA}, "codex_data"
    )
    if errors:
        for err in errors:
            logger.error(f"Validation Error in codex data: {err}")
        logger.warning("Loaded codex data contains schema errors.")

    validated_codex_data = data
    logger.info(
        f"Loaded codex definitions for {len(validated_codex_data.get('monsters', {}))} monsters."
    )
    return validated_codex_data


CODEX_DATA = load_codex_data()
