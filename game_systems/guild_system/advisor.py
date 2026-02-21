"""
game_systems/guild_system/advisor.py
The Guild Advisor system, providing context-aware guidance to new players.
"""

import random
from typing import Optional

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
                    return random.choice([
                        "You look pale, adventurer. Visit the **Infirmary** before you collapse.",
                        "Bleeding out is bad for business. Get patched up at the **Infirmary**.",
                        "Don't be a hero. Heal your wounds before heading out again."
                    ])

        # 2. Check Experience / First Quest
        guild_stats = self.db.get_guild_member_data(self.user_id)
        quests_completed = guild_stats.get("quests_completed", 0) if guild_stats else 0

        if quests_completed == 0:
            return random.choice([
                "Welcome to the Guild. The **Quest Board** is to your left. Don't stare at it all day.",
                "First time? Pick a simple contract from the **Quests** menu. Try not to die.",
                "Your reputation is non-existent. Complete a **Quest** to change that."
            ])

        # 3. Check Active Quest
        active_quests = self.db.get_player_quests_joined(self.user_id)
        if not active_quests:
            return random.choice([
                "You have no active contracts. The Guild doesn't pay for loitering.",
                "Idle hands earn no coin. Check the **Quest Board**.",
                "The monsters are waiting. You should pick up a **Quest**."
            ])

        # 4. Check Wealth & Gear (Rich but Unprepared)
        player = self.db.get_player(self.user_id)
        aurum = player.get("aurum", 0) if player else 0

        if aurum > 500:
            # Check for weapon in main_hand
            equipped = self.db.get_equipped_items(self.user_id)
            has_weapon = any(item.get("slot") == "main_hand" for item in equipped)

            if not has_weapon:
                return random.choice([
                    "You have coin, but no weapon. Visit the **Shop** before you become monster chow.",
                    "A full purse won't protect you like a good sword. Buy gear at the **Shop**.",
                    "Invest in your survival. The **Shop** has what you need."
                ])

        # 5. Generic Advice (Fallback)
        return random.choice([
            "Always check your supplies before leaving the city.",
            "If you find yourself overwhelmed, retreat is a valid strategy.",
            "The deeper you go, the darker it gets. Bring a torch... or a wizard.",
            "Keep your blade sharp and your wits sharper.",
            "Report your success at the Quest Board to claim your rewards."
        ])
