"""
adventure_session.py

Represents a single active adventure session.
Handles the simulation of combat steps and log generation.
(Refactored for manual, step-by-step exploration)
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

from game_systems.data.materials import MATERIALS


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

    def simulate_step(self) -> dict:
        """
        Simulates one 'step' (e.g., one button press).
        Resolves combat, logs results, and updates quest progress.
        Returns a dictionary with the results.
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"log": ["Error: Location data missing."], "dead": True}

        # --- 1. Decide what happens ---
        # 60% chance of combat, 40% chance of nothing
        if random.randint(1, 100) > 40:
            # --- 2. COMBAT ENCOUNTER ---
            return self._resolve_combat(location)
        else:
            # --- 3. NO ENCOUNTER ---
            log_entry = f"{E.FOREST} You search the area but find nothing of interest."
            self.logs.append(log_entry)
            return {"log": [log_entry], "dead": False}

    def _resolve_combat(self, location: dict) -> dict:
        """
        Handles a single combat encounter and returns the result.
        """
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

        player_wrapper = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )
        player_wrapper.hp_current = player_stats.max_hp

        # 2. Pick a Monster
        monster_pool = location["monsters"]
        choices, weights = zip(*monster_pool)
        monster_key = random.choices(choices, weights=weights, k=1)[0]
        monster_template = MONSTERS.get(monster_key)
        if not monster_template:
            return {"log": ["Error: Monster data missing."], "dead": False}

        monster_instance = {
            "name": monster_template["name"],
            "level": monster_template["level"],
            "tier": monster_template["tier"],
            "HP": monster_template["hp"],
            "MP": 10,
            "ATK": monster_template["atk"],
            "DEF": monster_template["def"],
            "xp": monster_template["xp"],
            "drops": monster_template.get("drops", []),
        }

        # 3. Resolve Combat
        engine = CombatEngine(player_wrapper, monster_instance)
        result = engine.begin_combat()  # This is the automated combat

        # 4. Process Results
        combat_log = result["phrases"]  # Get the descriptive log
        is_dead = False

        if result["winner"] == "player":
            loot_text = []
            self.add_loot("exp", result["exp"])
            loot_text.append(f"`{result['exp']} EXP`")

            for drop_key, chance in result["drops"]:
                if random.randint(1, 100) <= chance:
                    self.add_loot(drop_key, 1)

                    mat_data = MATERIALS.get(drop_key)
                    item_name = mat_data["name"] if mat_data else drop_key
                    loot_text.append(f"`{item_name}`")

            if loot_text:
                # --- NEWLINE ADDED FOR SPACING ---
                combat_log.append(f"\n{E.ITEM_BOX} **Loot:** {', '.join(loot_text)}")

            # --- Update Quest Progress ---
            quest_updates = self._update_quests(
                monster_instance["name"], result["drops"]
            )
            if quest_updates:
                combat_log.append(
                    f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(quest_updates)}*"
                )

        else:
            # Player Died
            is_dead = True
            self.active = False  # End session immediately

        # 5. Save Log
        self.logs.extend(combat_log)
        return {"log": combat_log, "dead": is_dead}

    def _update_quests(self, monster_name: str, drops: list) -> list:
        """Checks and updates all active quests for this event."""
        updated_quests = []
        active_quests = self.quest_system.get_player_quests(self.discord_id)

        for quest in active_quests:
            updated = False
            # A. Check for monster kill objectives
            if (
                "defeat" in quest["objectives"]
                and monster_name in quest["objectives"]["defeat"]
            ):
                self.quest_system.update_progress(
                    self.discord_id, quest["id"], "defeat", monster_name
                )
                updated = True

            # B. Check for item collection objectives
            if "collect" in quest["objectives"]:
                for drop_key, _ in drops:
                    if drop_key in quest["objectives"]["collect"]:
                        self.quest_system.update_progress(
                            self.discord_id, quest["id"], "collect", drop_key
                        )
                        updated = True

            if updated and quest["title"] not in updated_quests:
                updated_quests.append(quest["title"])

        return updated_quests

    def add_loot(self, key, amount):
        """Adds loot to the session's temporary loot pool."""
        if key in self.loot:
            self.loot[key] += amount
        else:
            self.loot[key] = amount

    def save_state(self):
        """Saves the session's current state to the database."""
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE adventure_sessions 
            SET logs = ?, loot_collected = ?, active = ?
            WHERE discord_id = ? AND active = 1
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
