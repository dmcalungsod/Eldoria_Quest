"""
reward_system.py

Handles the distribution of rewards upon quest completion.
ATOMIC: Grants EXP, Gold, Items, and Guild Merit in a single transaction block.
This prevents exploits where a user could get rewards but not have the quest marked complete.
"""

import json
import logging

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.consumables import CONSUMABLES
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.rewards")


class RewardSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.inv_manager = InventoryManager(db_manager)

    def _get_consumable_data_by_name(self, item_name: str) -> tuple[str | None, dict | None]:
        """Helper to find a consumable's key_id and data by its display name."""
        for key, data in CONSUMABLES.items():
            if data["name"] == item_name:
                return key, data
        return None, None

    def grant_rewards(self, discord_id: int, quest_id: int) -> str:
        """
        Grants all rewards (EXP, Aurum, Merit, Items) for a quest within a single atomic transaction.
        Returns a formatted summary string.
        """
        try:
            with self.db.get_connection() as conn:
                # 1. Fetch Quest Reward Data
                quest_row = conn.execute("SELECT rewards, title FROM quests WHERE id = ?", (quest_id,)).fetchone()
                if not quest_row:
                    return f"{E.ERROR} Error: Quest definition not found."

                try:
                    rewards_data = json.loads(quest_row["rewards"])
                except json.JSONDecodeError:
                    logger.error(f"Corrupt reward JSON for quest {quest_id}")
                    return f"{E.ERROR} Error: Reward data corrupted."

                exp_reward = rewards_data.get("exp", 0)
                aurum_reward = rewards_data.get("aurum", 0)
                merit_reward = rewards_data.get("merit", 5)
                item_reward_name = rewards_data.get("item", None)

                # 2. Fetch Player Data (Locking row implicitly via transaction)
                player_row = conn.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,)).fetchone()
                if not player_row:
                    return f"{E.ERROR} Error: Player record missing."

                # 3. Process Level Up Logic
                # We read stats to calculate next level requirements
                stats_row = conn.execute("SELECT stats_json FROM stats WHERE discord_id = ?", (discord_id,)).fetchone()
                if stats_row and stats_row["stats_json"]:
                    stats = PlayerStats.from_dict(json.loads(stats_row["stats_json"]))
                else:
                    stats = PlayerStats()

                level_system = LevelUpSystem(
                    stats=stats,
                    level=player_row["level"],
                    exp=player_row["experience"],
                    exp_to_next=player_row["exp_to_next"],
                )

                # Apply EXP to the level system object
                leveled_up = level_system.add_exp(exp_reward)

                # 4. EXECUTE DB UPDATES (Player)
                # Updates Level, EXP, Aurum, and Vestige simultaneously
                conn.execute(
                    """
                    UPDATE players
                    SET level = ?, experience = ?, exp_to_next = ?,
                        aurum = aurum + ?, vestige_pool = vestige_pool + ?
                    WHERE discord_id = ?
                    """,
                    (
                        level_system.level,
                        level_system.exp,
                        level_system.exp_to_next,
                        aurum_reward,
                        exp_reward,
                        discord_id,
                    ),
                )

                # 5. EXECUTE DB UPDATES (Guild Merit)
                conn.execute(
                    """
                    UPDATE guild_members
                    SET merit_points = merit_points + ?,
                        quests_completed = quests_completed + 1
                    WHERE discord_id = ?
                    """,
                    (merit_reward, discord_id),
                )

                # 6. Update Stats JSON
                # Required because level_system might have modified internal state if that logic exists
                conn.execute(
                    "UPDATE stats SET stats_json = ? WHERE discord_id = ?",
                    (json.dumps(level_system.stats.to_dict()), discord_id),
                )

                # 7. Item Rewards (Must happen inside THIS transaction!)
                item_msg = ""
                if item_reward_name:
                    item_key, item_data = self._get_consumable_data_by_name(item_reward_name)
                    if item_key and item_data:
                        # Use direct SQL here since we are inside a transaction block
                        # and cannot call self.inv_manager.add_item (which starts its own transaction).
                        self._add_item_internal(conn, discord_id, item_key, item_data)
                        item_msg = f"\n{E.ITEM_BOX} **Item Acquired:** `{item_data['name']}`"
                    else:
                        logger.warning(f"Quest {quest_id} tried to give unknown item '{item_reward_name}'")
                        item_msg = f"\n{E.WARNING} *Reward item '{item_reward_name}' not found in database.*"

            # -------- SUMMARY GENERATION (Outside Transaction) --------
            summary = (
                f"{E.MEDAL} **Quest Complete!**\n"
                "Your accomplishments have been formally recorded.\n\n"
                f"{E.EXP} **Experience Earned:** `+{exp_reward}`\n"
                f"{E.VESTIGE} **Vestige Accrued:** `+{exp_reward}`\n"
                f"{E.AURUM} **Aurum Received:** `+{aurum_reward}`\n"
                f"{E.GUILD_MERIT} **Guild Merit Awarded:** `+{merit_reward}`"
            )
            summary += item_msg

            if leveled_up:
                summary += (
                    f"\n\n{E.LEVEL_UP} **A NEW THRESHOLD REACHED**\n"
                    f"The weight of your deeds settles into your spirit.\n"
                    f"You have ascended to **Level {level_system.level}**."
                )

            return summary

        except Exception as e:
            logger.error(f"Reward grant failed for {discord_id}: {e}", exc_info=True)
            return f"{E.ERROR} A system error occurred while claiming rewards."

    def _add_item_internal(self, conn, discord_id, item_key, item_data):
        """
        Internal helper to add items within an existing transaction cursor.
        This duplicates logic from InventoryManager but accepts an open cursor ('conn').
        """
        # Check for existing stack
        row = conn.execute(
            """
            SELECT id, count FROM inventory
            WHERE discord_id = ? AND item_key = ? AND rarity = ? AND equipped = 0 LIMIT 1
            """,
            (discord_id, item_key, item_data["rarity"]),
        ).fetchone()

        if row:
            conn.execute("UPDATE inventory SET count = count + 1 WHERE id = ?", (row["id"],))
        else:
            conn.execute(
                """
                INSERT INTO inventory (discord_id, item_key, item_name, item_type, rarity, count, equipped)
                VALUES (?, ?, ?, 'consumable', ?, 1, 0)
                """,
                (discord_id, item_key, item_data["name"], item_data["rarity"]),
            )
