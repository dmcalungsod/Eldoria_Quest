"""
Player Creator for Eldoria Quest
--------------------------------
Handles character initialization.
Hardened with atomic transactions to ensure complete character setup.
"""

import json
import logging
import re

from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS

from .player_stats import PlayerStats

logger = logging.getLogger("eldoria.creator")


class PlayerCreator:
    def __init__(self, db):
        self.db = db

    def create_player(
        self,
        discord_id: int,
        username: str,
        class_id: int,
        race: str = None,
        gender: str = None,
    ):
        """
        Creates a player profile.
        ATOMIC: Creates player, stats, and default skills in one transaction.
        """
        # --- SECURITY FIX: Sanitize Username ---
        # 1. Remove Markdown characters (including link syntax)
        username = re.sub(r"[\*_~`|>\[\]\(\)]", "", username)
        # 2. Trim whitespace
        username = username.strip()
        # 3. Enforce max length
        username = username[:32]
        # 4. Ensure not empty
        if not username:
            username = "Adventurer"

        if self.db.player_exists(discord_id):
            return False, "You already have a character."

        # 1. Validate Class
        class_name = None
        for name, data in CLASS_DEFINITIONS.items():
            if data["id"] == class_id:
                class_name = name
                break

        if not class_name:
            return False, "Invalid class selection."

        class_data = CLASS_DEFINITIONS[class_name]

        # 2. Initialize Stats
        stats = PlayerStats(
            str_base=class_data["stats"]["STR"],
            end_base=class_data["stats"]["END"],
            dex_base=class_data["stats"]["DEX"],
            agi_base=class_data["stats"]["AGI"],
            mag_base=class_data["stats"]["MAG"],
            lck_base=class_data["stats"]["LCK"],
        )

        try:
            # 3. Fetch default skills for this class
            default_skill_keys = self.db.get_default_skill_keys(class_id)

            # 4. Create player, stats, skills, and guild membership atomically
            self.db.create_player_full(
                discord_id=discord_id,
                username=username,
                class_id=class_id,
                stats_json_str=json.dumps(stats.to_dict()),
                max_hp=stats.max_hp,
                max_mp=stats.max_mp,
                race=race,
                gender=gender,
                default_skill_keys=default_skill_keys,
            )

            logger.info(f"Character created for {username} ({discord_id})")
            return True, f"Welcome **{username}**, you are now a **{class_name}**!"

        except Exception as e:
            logger.error(f"Failed to create player {discord_id}: {e}", exc_info=True)
            return False, "A system error occurred during character creation."
