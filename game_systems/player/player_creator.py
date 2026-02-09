"""
Player Creator for Eldoria Quest
--------------------------------
Handles character initialization.
Hardened with atomic transactions to ensure complete character setup.
"""

import json
import logging

from game_systems.data.class_data import CLASSES as CLASS_DEFINITIONS

from .player_stats import PlayerStats

logger = logging.getLogger("eldoria.creator")


class PlayerCreator:
    def __init__(self, db):
        self.db = db

    def create_player(self, discord_id: int, username: str, class_id: int, race: str = None, gender: str = None):
        """
        Creates a player profile.
        ATOMIC: Creates player, stats, and default skills in one transaction.
        """
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
            with self.db.get_connection() as conn:
                # 3. Insert Player Record & Stats (Handled by DB Manager logic or manually here for atomicity)
                # We use the raw queries here to bundle skills in the same transaction context

                # Insert Player
                conn.execute(
                    """
                    INSERT INTO players (
                        discord_id, name, class_id, race, gender,
                        level, experience, exp_to_next, current_hp, current_mp, vestige_pool, aurum
                    ) VALUES (?, ?, ?, ?, ?, 1, 0, 1000, ?, ?, 0, 0)
                    """,
                    (discord_id, username, class_id, race, gender, stats.max_hp, stats.max_mp),
                )

                # Insert Stats JSON
                conn.execute(
                    "INSERT INTO stats (discord_id, stats_json) VALUES (?, ?)",
                    (
                        discord_id,
                        json.dumps(stats.to_dict()),
                    ),
                )

                # 4. Add Default Skills
                # Find skills with learn_cost=0 for this class
                default_skills = conn.execute(
                    "SELECT key_id FROM skills WHERE class_id = ? AND learn_cost = 0", (class_id,)
                ).fetchall()

                for skill in default_skills:
                    conn.execute(
                        "INSERT INTO player_skills (discord_id, skill_key, skill_level) VALUES (?, ?, 1)",
                        (discord_id, skill["key_id"]),
                    )

                # 5. Register Guild Member (Starting Rank F)
                conn.execute(
                    "INSERT INTO guild_members (discord_id, rank, join_date) VALUES (?, 'F', datetime('now'))",
                    (discord_id,),
                )

            logger.info(f"Character created for {username} ({discord_id})")
            return True, f"Welcome **{username}**, you are now a **{class_name}**!"

        except Exception as e:
            logger.error(f"Failed to create player {discord_id}: {e}", exc_info=True)
            return False, "A system error occurred during character creation."
