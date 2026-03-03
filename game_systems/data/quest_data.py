"""
quest_data.py

Contains all quest definitions for Eldoria Quest.
Data is loaded from 'quests.json'.

Schema for 'quests.json':
[
  {
    "id": int,
    "title": str,
    "tier": str,
    "quest_giver": str,
    "location": str,
    "summary": str,
    "description": str,
    "objectives": dict,  # e.g. {"defeat": {"Goblin": 5}}
    "rewards": dict      # e.g. {"exp": 100, "aurum": 50}
  }
]
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("eldoria.data")


def load_quests():
    """
    Loads quest data from JSON file.
    """
    data_path = Path(__file__).parent / "quests.json"

    try:
        with open(data_path, encoding="utf-8") as f:
            quests = json.load(f)
        logger.info(f"Loaded {len(quests)} quests from {data_path.name}")
        return quests
    except FileNotFoundError:
        logger.error(f"CRITICAL: quests.json not found at {data_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: quests.json is invalid JSON: {e}")
        return []


ALL_QUESTS = load_quests()

# Filter by Tier for backward compatibility and organized access
QUESTS_F_TIER = [q for q in ALL_QUESTS if q["tier"] == "F"]
QUESTS_E_TIER = [q for q in ALL_QUESTS if q["tier"] == "E"]
QUESTS_D_TIER = [q for q in ALL_QUESTS if q["tier"] == "D"]
QUESTS_C_TIER = [q for q in ALL_QUESTS if q["tier"] == "C"]
QUESTS_B_TIER = [q for q in ALL_QUESTS if q["tier"] == "B"]
QUESTS_A_TIER = [q for q in ALL_QUESTS if q["tier"] == "A"]
QUESTS_S_TIER = [q for q in ALL_QUESTS if q["tier"] == "S"]

__all__ = [
    "ALL_QUESTS",
    "QUESTS_F_TIER",
    "QUESTS_E_TIER",
    "QUESTS_D_TIER",
    "QUESTS_C_TIER",
    "QUESTS_B_TIER",
    "QUESTS_A_TIER",
    "QUESTS_S_TIER",
]
