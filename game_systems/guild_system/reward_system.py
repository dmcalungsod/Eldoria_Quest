"""
reward_system.py

Handles the distribution of rewards upon quest completion.
ATOMIC: Grants EXP, Gold, Items, and Guild Merit via dedicated DatabaseManager methods.
"""

import json
import logging

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.achievement_system import AchievementSystem
from game_systems.data.consumables import CONSUMABLES
from game_systems.items.inventory_manager import InventoryManager
from game_systems.player.level_up import LevelUpSystem
from game_systems.player.player_stats import PlayerStats

logger = logging.getLogger("eldoria.rewards")


class RewardSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.inv_manager = InventoryManager(db_manager)
        self.achievement_system = AchievementSystem(db_manager)

    def _get_consumable_data_by_name(
        self, item_name: str
    ) -> tuple[str | None, dict | None]:
        """Helper to find a consumable's key_id and data by its display name."""
        for key, data in CONSUMABLES.items():
            if data["name"] == item_name:
                return key, data
        return None, None

    def grant_rewards(self, discord_id: int, quest_id: int) -> str:
        """
        Grants all rewards (EXP, Aurum, Merit, Items) for a quest.
        Returns a formatted summary string.
        """
        try:
            # 1. Fetch Quest Reward Data
            quest_row = self.db._col("quests").find_one(
                {"id": quest_id}, {"_id": 0, "rewards": 1, "title": 1}
            )
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

            # 2. Fetch Player Data
            player_row = self.db.get_player(discord_id)
            if not player_row:
                return f"{E.ERROR} Error: Player record missing."

            # 3. Process Level Up Logic
            stats_json = self.db.get_player_stats_json(discord_id)
            if stats_json:
                stats = PlayerStats.from_dict(stats_json)
            else:
                stats = PlayerStats()

            level_system = LevelUpSystem(
                stats=stats,
                level=player_row["level"],
                exp=player_row["experience"],
                exp_to_next=player_row["exp_to_next"],
            )

            leveled_up = level_system.add_exp(exp_reward)

            # 4. Grant rewards via dedicated DatabaseManager method
            self.db.grant_quest_rewards(
                discord_id,
                level=level_system.level,
                exp=level_system.exp,
                exp_to_next=level_system.exp_to_next,
                aurum_add=aurum_reward,
                vestige_add=exp_reward,
                merit_add=merit_reward,
                stats_json_str=json.dumps(level_system.stats.to_dict()),
            )

            # 5. Item Rewards
            item_msg = ""
            if item_reward_name:
                item_key, item_data = self._get_consumable_data_by_name(
                    item_reward_name
                )
                if item_key and item_data:
                    self.db.add_inventory_item(
                        discord_id,
                        item_key,
                        item_data["name"],
                        "consumable",
                        item_data["rarity"],
                        1,
                    )
                    item_msg = (
                        f"\n{E.ITEM_BOX} **Item Acquired:** `{item_data['name']}`"
                    )
                else:
                    logger.warning(
                        f"Quest {quest_id} tried to give unknown item '{item_reward_name}'"
                    )
                    item_msg = f"\n{E.WARNING} *Reward item '{item_reward_name}' not found in database.*"

            # -------- SUMMARY GENERATION --------
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

            # Achievements
            ach_msg = self.achievement_system.check_quest_achievements(discord_id)
            if ach_msg:
                summary += f"\n\n{ach_msg}"

            return summary

        except Exception as e:
            logger.error(f"Reward grant failed for {discord_id}: {e}", exc_info=True)
            return f"{E.ERROR} A system error occurred while claiming rewards."
