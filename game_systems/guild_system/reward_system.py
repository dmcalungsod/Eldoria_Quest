"""
reward_system.py

Handles the distribution of rewards upon quest completion.
"""

import json
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
import game_systems.data.emojis as E


class RewardSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

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
        item_reward = rewards_data.get("item", None)

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

        # Process EXP
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

        conn.commit()
        conn.close()

        # Build Narrative Summary
        summary = (
            f"{E.MEDAL} **Quest Complete!**\n"
            "Your achievements have been recorded in the annals of the\n"
            "**Adventurer's Guild**.\n\n"
            f"{E.EXP} **EXP Gained:** `+{exp_reward}`\n"
            f"{E.VESTIGE} **Vestige Gained:** `+{exp_reward}`\n" # FIX: Added Vestige reward line with new emoji
            f"{E.AURUM} **Aurum Earned:** `+{aurum_reward}`\n"
            f"{E.GUILD_MERIT} **Guild Merit:** `+{merit_reward}`"
        )

        if leveled_up:
            summary += (
                f"\n\n{E.LEVEL_UP} **Level Up!**\n"
                f"Your soul resonates with newfound strength — you are now **Level {level_system.level}**!"
            )

        if item_reward:
            summary += (
                f"\n{E.ITEM_BOX} **Item Acquired:** `{item_reward}`\n"
                "_(*Inventory system pending implementation*)_"
            )

        summary += (
            "\n\nThe guild clerks inscribe your progress, while whispers of your deed ripple "
            "through the guild hall."
        )

        return summary