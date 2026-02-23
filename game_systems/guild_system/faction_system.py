"""
faction_system.py

Manages Faction membership, reputation, and progression.
"""

import datetime
import logging

from database.database_manager import DatabaseManager
from game_systems.world_time import WorldTime
from game_systems.data.emojis import ERROR, SUCCESS, WARNING
from game_systems.data.factions import FACTIONS

logger = logging.getLogger("eldoria.factions")


class FactionSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_player_faction(self, discord_id: int) -> dict | None:
        """
        Returns player's faction data merged with static faction definitions.
        """
        p_faction = self.db.get_player_faction_data(discord_id)
        if not p_faction:
            return None

        faction_id = p_faction.get("faction_id")
        faction_def = FACTIONS.get(faction_id)

        if not faction_def:
            return None

        # Determine current rank title
        rep = p_faction.get("reputation", 0)
        current_rank_tier = 1
        current_title = "Initiate"

        # Find highest rank achieved
        for tier, data in faction_def["ranks"].items():
            if rep >= data["reputation_needed"]:
                current_rank_tier = tier
                current_title = data["title"]
            else:
                break

        return {
            "faction_id": faction_id,
            "name": faction_def["name"],
            "emoji": faction_def["emoji"],
            "description": faction_def["description"],
            "reputation": rep,
            "rank_tier": current_rank_tier,
            "rank_title": current_title,
            "next_rank": faction_def["ranks"].get(current_rank_tier + 1),
            "interests": faction_def.get("interests", {}),
        }

    def join_faction(self, discord_id: int, faction_id: str) -> tuple[bool, str]:
        """
        Joins a faction. Fails if already in one.
        """
        if faction_id not in FACTIONS:
            return False, f"{ERROR} Unknown faction: {faction_id}"

        existing = self.db.get_player_faction_data(discord_id)
        if existing:
            current_id = existing.get("faction_id")
            name = FACTIONS.get(current_id, {}).get("name", "Unknown")
            return (
                False,
                f"{WARNING} You are already a member of **{name}**. Leave first.",
            )

        # Insert new membership
        try:
            self.db._col("player_factions").insert_one(
                {
                    "discord_id": discord_id,
                    "faction_id": faction_id,
                    "reputation": 0,
                    "join_date": WorldTime.now().isoformat(),
                }
            )
            name = FACTIONS[faction_id]["name"]
            return True, f"{SUCCESS} You have joined **{name}**!"
        except Exception as e:
            logger.error(f"Error joining faction: {e}")
            return False, f"{ERROR} System error."

    def leave_faction(self, discord_id: int) -> tuple[bool, str]:
        """
        Leaves current faction. Wipes reputation.
        """
        existing = self.db.get_player_faction_data(discord_id)
        if not existing:
            return False, f"{WARNING} You are not in a faction."

        try:
            self.db.leave_faction(discord_id)
            return True, f"{SUCCESS} You have left your faction."
        except Exception as e:
            logger.error(f"Error leaving faction: {e}")
            return False, f"{ERROR} System error."

    def add_reputation(
        self, discord_id: int, amount: int
    ) -> tuple[bool, str, list[str]]:
        """
        Adds reputation and checks for rank-up.
        Returns: (success, message, list_of_rank_up_messages)
        """
        existing = self.get_player_faction(discord_id)
        if not existing:
            return False, "Not in a faction", []

        new_rep = self.db.update_faction_reputation(discord_id, amount)
        faction_id = existing["faction_id"]
        faction_def = FACTIONS[faction_id]

        # Check for Rank Up
        rank_up_msgs = []
        old_tier = existing["rank_tier"]
        new_tier = old_tier

        # Re-evaluate rank
        for tier, data in faction_def["ranks"].items():
            if new_rep >= data["reputation_needed"]:
                new_tier = tier
            else:
                break

        if new_tier > old_tier:
            # Grant rewards for all skipped tiers (though likely just 1 at a time)
            for t in range(old_tier + 1, new_tier + 1):
                rank_data = faction_def["ranks"][t]
                title = rank_data["title"]
                rank_up_msgs.append(
                    f"{SUCCESS} **Rank Up!** You are now a **{title}** of {faction_def['name']}!"
                )

                # Auto-claim rewards? Or manual claim?
                # For simplicity, let's auto-claim item rewards here.
                reward = rank_data.get("reward")
                if reward:
                    self._grant_faction_reward(discord_id, reward, rank_up_msgs)

        return True, f"+{amount} Reputation", rank_up_msgs

    def _grant_faction_reward(self, discord_id: int, reward: dict, logs: list):
        """Helper to process rewards."""
        r_type = reward.get("type")
        if r_type == "item":
            item_key = reward["key"]
            amount = reward.get("amount", 1)
            # Fetch item details for adding
            # Assuming item keys exist in MATERIALS or standard item DB
            # We can use db.add_inventory_item if we know details.
            # Simplified: Use standard item addition logic.
            self.db.add_inventory_item(
                discord_id,
                item_key,
                item_name=item_key.replace("_", " ").title(),  # Fallback name
                item_type="consumable",  # Default
                rarity="Rare",  # Default
                amount=amount,
            )
            logs.append(
                f"Received reward: {amount}x {item_key.replace('_', ' ').title()}"
            )

        elif r_type == "buff":
            logs.append(
                f"Unlocked Passive Buff: {reward['key']} (Effect applied automatically)"
            )

        elif r_type == "title":
            title = reward["value"]
            self.db.add_title(discord_id, title)
            logs.append(f"Unlocked Title: **{title}**")

    def grant_reputation_for_kill(
        self, discord_id: int, monster_data: dict
    ) -> list[str]:
        """
        Calculates and grants reputation based on monster kill.
        """
        existing = self.get_player_faction(discord_id)
        if not existing:
            return []

        interests = existing["interests"]
        base_rep = 5  # Baseline for any kill

        # Apply multipliers
        multiplier = 1.0

        tier = monster_data.get("tier", "Normal")
        if tier == "Elite":
            base_rep = 15
            multiplier += interests.get("elite_kills", 0.0)
        elif tier == "Boss":
            base_rep = 50
            multiplier += interests.get("boss_kills", 0.0)

        # Type matching? (Requires monster type in data, assuming simple check for now)
        # Monster data usually has just name/stats. If we add 'type' later, we use it.

        final_rep = int(base_rep * multiplier)
        if final_rep > 0:
            success, msg, rank_msgs = self.add_reputation(discord_id, final_rep)
            if success and rank_msgs:
                return rank_msgs

        return []

    def grant_reputation_for_adventure(
        self, discord_id: int, duration_minutes: int, location_id: str
    ) -> list[str]:
        """
        Grants reputation for completing an adventure.
        """
        existing = self.get_player_faction(discord_id)
        if not existing:
            return []

        interests = existing["interests"]

        # Base: 1 rep per 5 minutes
        base_rep = duration_minutes // 5

        multiplier = 1.0
        # Check if location matches interests (Future expansion: add 'favored_locations' to faction data)
        # For now, Pathfinders like exploration (all locations)
        multiplier += interests.get("exploration", 0.0)

        final_rep = int(base_rep * multiplier)
        if final_rep > 0:
            success, msg, rank_msgs = self.add_reputation(discord_id, final_rep)
            if success and rank_msgs:
                return rank_msgs

        return []
