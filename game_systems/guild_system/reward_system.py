"""
reward_system.py

Handles the distribution of rewards upon quest completion.
"""

import json
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
import game_systems.data.emojis as E

# --- NEW IMPORTS ---
from game_systems.items.inventory_manager import InventoryManager
from game_systems.data.consumables import CONSUMABLES
# --- END NEW IMPORTS ---


class RewardSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.inv_manager = InventoryManager(db_manager)

    # --- Look up consumable by display name ---
    def _get_consumable_data_by_name(self, item_name: str):
        """Find a consumable's key_id and data by its display name."""
        for key, data in CONSUMABLES.items():
            if data["name"] == item_name:
                return key, data
        return None, None

    def grant_rewards(self, discord_id: int, quest_id: int) -> str:
        conn = self.db.connect()
        cur = conn.cursor()

        # Fetch Quest Rewards
        cur.execute("SELECT rewards FROM quests WHERE id = ?", (quest_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return f"{E.ERROR} Error: Quest reward data not found."

        rewards_data = json.loads(row["rewards"])

        exp_reward = rewards_data.get("exp", 0)
        aurum_reward = rewards_data.get("aurum", 0)
        merit_reward = rewards_data.get("merit", 5)
        item_reward_name = rewards_data.get("item", None)

        # Fetch Player Data
        cur.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
        player_row = cur.fetchone()

        stats_json = self.db.get_player_stats_json(discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        level_system = LevelUpSystem(
            stats=player_stats,
            level=player_row["level"],
            exp=player_row["experience"],
            exp_to_next=player_row["exp_to_next"],
        )

        # Process EXP + Level Up
        leveled_up = level_system.add_exp(exp_reward)

        self.db.update_player_level_data(
            discord_id,
            level_system.level,
            level_system.exp,
            level_system.exp_to_next,
        )
        self.db.update_player_stats(discord_id, level_system.stats.to_dict())

        # Update Aurum
        cur.execute(
            "UPDATE players SET aurum = aurum + ? WHERE discord_id = ?",
            (aurum_reward, discord_id),
        )

        # Update Merit
        cur.execute(
            """
            UPDATE guild_members 
            SET merit_points = merit_points + ?,
                quests_completed = quests_completed + 1
            WHERE discord_id = ?
        """,
            (merit_reward, discord_id),
        )

        # Vestige mirrors EXP
        if exp_reward > 0:
            cur.execute(
                "UPDATE players SET vestige_pool = vestige_pool + ? WHERE discord_id = ?",
                (exp_reward, discord_id),
            )

        conn.commit()
        conn.close()

        # -------- ITEM REWARD PROCESS --------
        item_message_line = ""

        if item_reward_name:
            item_key, item_data = self._get_consumable_data_by_name(item_reward_name)

            if item_key and item_data:
                # Add to inventory
                self.inv_manager.add_item(
                    discord_id=discord_id,
                    item_key=item_key,
                    item_name=item_data["name"],
                    item_type="consumable",
                    rarity=item_data["rarity"],
                    amount=1
                )
                item_message_line = f"\n{E.ITEM_BOX} **Item Acquired:** `{item_data['name']}`"
            else:
                print(f"Error: Quest {quest_id} grants unknown item: {item_reward_name}")
                item_message_line = f"\n{E.WARNING} *Item '{item_reward_name}' could not be found.*"

        # -------- SUMMARY MESSAGE --------
        summary = (
            f"{E.MEDAL} **Quest Complete!**\n"
            "Your accomplishments have been formally recorded by the\n"
            "**Adventurer's Guild**.\n\n"
            f"{E.EXP} **Experience Earned:** `+{exp_reward}`\n"
            f"{E.VESTIGE} **Vestige Accrued:** `+{exp_reward}`\n"
            f"{E.AURUM} **Aurum Received:** `+{aurum_reward}`\n"
            f"{E.GUILD_MERIT} **Guild Merit Awarded:** `+{merit_reward}`"
        )

        summary += item_message_line

        if leveled_up:
            summary += (
                f"\n\n{E.LEVEL_UP} **A NEW THRESHOLD REACHED**\n"
                f"The weight of your deeds settles into your spirit, reshaping it.\n"
                f"You have ascended to **Level {level_system.level}**."
            )

        summary += (
            "\n\nGuild scribes commit the record of your success to the ledgers, "
            "while quiet murmurs drift through the hall at your return."
        )

        return summary
