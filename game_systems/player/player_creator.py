"""
Player Creator for Eldoria Quest

Handles:
- Creating player profiles
- Creating base stats from class definitions
- Validating class IDs
"""

from .player_stats import PlayerStats
from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS


class PlayerCreator:
    def __init__(self, db):
        self.db = db

    def create_player(self, discord_id: int, username: str, class_id: int):
        """Creates a new player after validating class ID and ensuring no duplicates."""

        # Check if player already exists
        if self.db.player_exists(discord_id):
            return False, "You already created a character."

        # Locate class by ID
        class_name = None
        for name, data in CLASS_DEFINITIONS.items():
            if data["id"] == class_id:
                class_name = name
                break

        if not class_name:
            return False, "Invalid class ID."

        class_data = CLASS_DEFINITIONS[class_name]

        # Build stats object
        stats = PlayerStats(
            str_base=class_data["stats"]["STR"],
            dex_base=class_data["stats"]["DEX"],
            con_base=class_data["stats"]["CON"],
            int_base=class_data["stats"]["INT"],
            wis_base=class_data["stats"]["WIS"],
            cha_base=class_data["stats"]["CHA"],
            lck_base=class_data["stats"]["LCK"],
        )

        # Save to database
        self.db.create_player(
            discord_id=discord_id,
            name=username,
            class_id=class_id,
            stats_data=stats.to_dict(),
        )

        return True, f"Welcome **{username}**, you are now a **{class_name}**!"
