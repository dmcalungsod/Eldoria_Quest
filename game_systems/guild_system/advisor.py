"""
game_systems/guild_system/advisor.py
The Guild Advisor system, providing context-aware guidance to new players.
"""

import random

import discord

from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats


class GuildAdvisor:
    def __init__(self, db: DatabaseManager, user_id: int):
        self.db = db
        self.user_id = user_id

    def get_advice(self) -> str:
        """
        Analyzes the player's state (Vitals, Quests, Wealth, Gear)
        and returns a helpful, atmospheric tip.
        """
        # 1. Check Vitals (Safety First)
        vitals = self.db.get_player_vitals(self.user_id)
        if vitals:
            current_hp = vitals.get("current_hp", 0)

            # Fetch stats to calculate Max HP
            stats_json = self.db.get_player_stats_json(self.user_id)
            if stats_json:
                stats = PlayerStats.from_dict(stats_json)
                max_hp = stats.max_hp

                if max_hp > 0 and (current_hp / max_hp) < 0.3:
                    return random.choice(
                        [
                            "You look pale, adventurer. Visit the **Infirmary** before you collapse.",
                            "Bleeding out is bad for business. Get patched up at the **Infirmary**.",
                            "Don't be a hero. Heal your wounds before heading out again.",
                        ]
                    )

        # 2. Check Experience / First Quest
        guild_stats = self.db.get_guild_member_data(self.user_id)
        quests_completed = guild_stats.get("quests_completed", 0) if guild_stats else 0

        if quests_completed == 0:
            return random.choice(
                [
                    "Welcome to the Guild. The **Quest Board** is to your left. Don't stare at it all day.",
                    "First time? Pick a simple contract from the **Quests** menu. Try not to die.",
                    "Your reputation is non-existent. Complete a **Quest** to change that.",
                ]
            )

        # 3. Check Active Quest
        active_quests = self.db.get_player_quests_joined(self.user_id)
        if not active_quests:
            return random.choice(
                [
                    "You have no active contracts. The Guild doesn't pay for loitering.",
                    "Idle hands earn no coin. Check the **Quest Board**.",
                    "The monsters are waiting. You should pick up a **Quest**.",
                ]
            )

        # 4. Check Wealth & Gear (Rich but Unprepared)
        player = self.db.get_player(self.user_id)
        aurum = player.get("aurum", 0) if player else 0

        if aurum > 500:
            # Check for weapon in main_hand
            equipped = self.db.get_equipped_items(self.user_id)
            has_weapon = any(item.get("slot") == "main_hand" for item in equipped)

            if not has_weapon:
                return random.choice(
                    [
                        "You have coin, but no weapon. Visit the **Shop** before you become monster chow.",
                        "A full purse won't protect you like a good sword. Buy gear at the **Shop**.",
                        "Invest in your survival. The **Shop** has what you need.",
                    ]
                )

        # 5. Generic Advice (Fallback)
        return random.choice(
            [
                "Always check your supplies before leaving the city.",
                "If you find yourself overwhelmed, retreat is a valid strategy.",
                "The deeper you go, the darker it gets. Bring a torch... or a wizard.",
                "Keep your blade sharp and your wits sharper.",
                "Report your success at the Quest Board to claim your rewards.",
            ]
        )

    def get_checklist_embed(self) -> discord.Embed:
        """
        Generates a New Player Checklist embed showing onboarding progress.
        """
        # --- DATA FETCHING ---
        equipped_items = self.db.get_equipped_items(self.user_id)
        guild_data = self.db.get_guild_member_data(self.user_id)
        active_quests = self.db.get_player_quests_joined(self.user_id)
        exploration_stats = self.db.get_exploration_stats(self.user_id)

        # --- CHECKS ---
        # 1. Gear Up: Has any weapon equipped?
        weapon_slots = {"sword", "mace", "wand", "staff", "dagger", "bow", "greatsword"}
        has_weapon = any(item.get("slot") in weapon_slots for item in equipped_items)

        # 2. First Contract: Quests completed > 0 or has active quest
        quests_completed = guild_data.get("quests_completed", 0) if guild_data else 0
        has_active_quest = len(active_quests) > 0

        # 3. First Expedition: Total expeditions > 0
        total_expeditions = exploration_stats.get("total_expeditions", 0)
        has_expedition = total_expeditions > 0

        # --- EMBED BUILDING ---
        embed = discord.Embed(
            title="📜 New Recruit Checklist",
            description="*The Guildmaster has outlined these steps for your initiation.*",
            color=discord.Color.blue(),
        )

        # Step 1: Registration
        embed.add_field(
            name="1. Registration",
            value="✅ **Complete**\n*You are officially registered.*",
            inline=False,
        )

        # Step 2: Gear Up
        if has_weapon:
            embed.add_field(
                name="2. Gear Up",
                value="✅ **Complete**\n*Your weapon is ready.*",
                inline=False,
            )
        else:
            embed.add_field(
                name="2. Gear Up",
                value="❌ **Pending**\n*Equip a weapon via **Profile** -> **Inventory**.*",
                inline=False,
            )

        # Step 3: First Contract
        if quests_completed > 0:
            embed.add_field(
                name="3. First Contract",
                value="✅ **Complete**\n*You have proven your worth.*",
                inline=False,
            )
        elif has_active_quest:
            embed.add_field(
                name="3. First Contract",
                value="⚠️ **In Progress**\n*Complete your active quest.*",
                inline=False,
            )
        else:
            embed.add_field(
                name="3. First Contract",
                value="❌ **Pending**\n*Accept a contract from the **Quest Board**.*",
                inline=False,
            )

        # Step 4: First Expedition
        if has_expedition:
            embed.add_field(
                name="4. First Expedition",
                value="✅ **Complete**\n*You have survived the wilds.*",
                inline=False,
            )
        else:
            embed.add_field(
                name="4. First Expedition",
                value="❌ **Pending**\n*Start an adventure via **Profile** -> **Adventure**.*",
                inline=False,
            )

        # Graduation Check
        if has_weapon and (quests_completed > 0) and has_expedition:
            embed.color = discord.Color.gold()
            embed.description = (
                "**🎉 INITIATION COMPLETE!**\n"
                "*You are now a true Adventurer. Rank up to unlock more guild privileges.*"
            )

        return embed
