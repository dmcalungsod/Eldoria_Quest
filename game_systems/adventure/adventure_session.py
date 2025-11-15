"""
adventure_session.py

Represents a single active adventure session.
Handles the simulation of combat steps and log generation.
(Refactored for material-based economy)
"""

import json
import random
import datetime
from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from game_systems.guild_system.quest_system import QuestSystem
import game_systems.data.emojis as E


class AdventureSession:
    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_system: QuestSystem,
        discord_id: int,
        row_data=None,
    ):
        self.db = db_manager
        self.quest_system = quest_system  # For updating progress
        self.discord_id = discord_id

        if row_data:
            self.location_id = row_data["location_id"]
            self.end_time = datetime.datetime.fromisoformat(row_data["end_time"])
            self.logs = json.loads(row_data["logs"])
            self.loot = json.loads(row_data["loot_collected"])
            self.active = bool(row_data["active"])
        else:
            self.active = False  # Should be initialized by manager

    async def simulate_step(self):
        """
        Simulates one 'step' (e.g., 5 minutes interval).
        Resolves combat, logs results, and updates quest progress.
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return

        # 1. Fetch Player
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT level, experience, exp_to_next FROM players WHERE discord_id = ?",
            (self.discord_id,),
        )
        p_row = cur.fetchone()
        conn.close()

        # Create a fresh player wrapper for this combat
        player_wrapper = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )
        # Set current HP for this fight
        player_wrapper.hp_current = player_stats.max_hp

        # 2. Pick a Monster
        monster_pool = location["monsters"]
        choices, weights = zip(*monster_pool)
        monster_key = random.choices(choices, weights=weights, k=1)[0]

        monster_template = MONSTERS.get(monster_key)
        if not monster_template:
            return True  # Failed to find monster, but session continues

        # Create a combat-ready monster instance
        monster_instance = {
            "name": monster_template["name"],
            "level": monster_template["level"],
            "tier": monster_template["tier"],
            "HP": monster_template["hp"],
            "MP": 10,  # Default MP
            "ATK": monster_template["atk"],
            "DEF": monster_template["def"],
            "xp": monster_template["xp"],
            "drops": monster_template.get("drops", []),
        }

        # 3. Resolve Combat
        engine = CombatEngine(player_wrapper, monster_instance)
        result = engine.begin_combat()

        # 4. Process Results
        timestamp = datetime.datetime.now().strftime("%H:%M")

        if result["winner"] == "player":
            # --- This is the new loot logic ---
            loot_text = []

            # Add EXP
            self.add_loot("exp", result["exp"])
            loot_text.append(f"{result['exp']} EXP")

            # Roll for Monster Drops
            for drop_key, chance in result["drops"]:
                if random.randint(1, 100) <= chance:
                    self.add_loot(drop_key, 1)  # Add the material key
                    loot_text.append(f"{drop_key}")

            log_entry = (
                f"`[{timestamp}]` {E.COMBAT} Encountered: **{monster_instance['name']}**\n"
                f"> {E.VICTORY} Defeated! Gained: {', '.join(loot_text)}.\n"
                f"> *HP remaining: {player_wrapper.hp_current} / {player_stats.max_hp}* (Recovers)"
            )

            # --- CRITICAL: Update Quest Progress ---
            # We get all active quests
            active_quests = self.quest_system.get_player_quests(self.discord_id)
            for quest in active_quests:
                # Check if this monster is an objective
                if (
                    "defeat" in quest["objectives"]
                    and monster_instance["name"] in quest["objectives"]["defeat"]
                ):
                    self.quest_system.update_progress(
                        self.discord_id, quest["id"], "defeat", monster_instance["name"]
                    )
                    log_entry += f"\n> *Quest Updated: {quest['title']}*"

        else:
            # Player Died
            log_entry = (
                f"`[{timestamp}]` {E.DEFEAT} **Defeat:** Overwhelmed by {monster_instance['name']}.\n"
                f"> The Guild sends a rescue party. Adventure ends early."
            )
            self.active = False  # End session immediately

        # 5. Save Log
        self.logs.append(log_entry)
        self.save_state()
        return self.active

    def add_loot(self, key, amount):
        if key in self.loot:
            self.loot[key] += amount
        else:
            self.loot[key] = amount

    def save_state(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE adventure_sessions 
            SET logs = ?, loot_collected = ?, active = ?
            WHERE discord_id = ?
        """,
            (
                json.dumps(self.logs),
                json.dumps(self.loot),
                1 if self.active else 0,
                self.discord_id,
            ),
        )
        conn.commit()
        conn.close()
