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
from game_systems.combat.combat_phrases import CombatPhrases  # <-- THIS IS THE FIX
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from game_systems.guild_system.quest_system import QuestSystem
import game_systems.data.emojis as E

from game_systems.data.materials import MATERIALS
from game_systems.items.inventory_manager import InventoryManager
from game_systems.items.item_manager import item_manager

# --- NEW IMPORT ---
from .adventure_events import AdventureEvents


class AdventureSession:

    # --- NEW: Event Chances ---
    REGEN_CHANCE = 70  # 70% chance to regen
    # (The remaining 30% is for a quest event)

    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_system: QuestSystem,
        inventory_manager: InventoryManager,
        discord_id: int,
        row_data=None,
    ):
        self.db = db_manager
        self.quest_system = quest_system
        self.inventory_manager = inventory_manager
        self.discord_id = discord_id

        if row_data:
            self.location_id = row_data["location_id"]
            self.end_time = datetime.datetime.fromisoformat(row_data["end_time"])
            self.logs = json.loads(row_data["logs"])
            self.loot = json.loads(row_data["loot_collected"])
            self.active = bool(row_data["active"])
            self.active_monster = (
                json.loads(row_data["active_monster_json"])
                if row_data["active_monster_json"]
                else None
            )
        else:
            self.active = False
            self.active_monster = None

    def simulate_step(self) -> dict:
        """
        Simulates one 'step' (e.g., one button press).
        Resolves combat, logs results, and updates quest progress.
        Returns a dictionary with the results.
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"log": ["Error: Location data missing."], "dead": True}

        if self.active_monster:
            # We are in combat, so the "Explore" button means "Attack"
            return self._resolve_combat_turn()

        # Not in combat, so explore
        if random.randint(1, 100) > 40:
            # 60% chance of combat
            return self._initiate_combat(location)
        else:
            # 40% chance of a non-combat event
            return self._resolve_non_combat_step()

    # --- NEW METHOD ---
    def _resolve_non_combat_step(self) -> dict:
        """
        Handles non-combat events.
        Decides between regeneration or a quest-specific event.
        """
        if random.randint(1, 100) <= self.REGEN_CHANCE:
            result = self._perform_regeneration()
        else:
            result = self._perform_quest_event()

        self.logs.extend(result["log"])
        return result

    def _perform_regeneration(self) -> dict:
        """
        Player finds no monster and regenerates HP/MP.
        """
        stats_json = self.db.get_player_stats_json(self.discord_id)
        stats = PlayerStats.from_dict(stats_json)
        vitals = self.db.get_player_vitals(self.discord_id)

        current_hp = vitals["current_hp"]
        current_mp = vitals["current_mp"]
        max_hp = stats.max_hp
        max_mp = stats.max_mp

        if current_hp >= max_hp and current_mp >= max_mp:
            # No regen needed, just post a simple message
            log_entry = AdventureEvents.no_event_found()
            return {"log": [log_entry], "dead": False}

        # Regen Formula: 1 + (5% of END/MAG stat)
        hp_regen = 1 + int(stats.endurance * 0.5)
        mp_regen = 1 + int(stats.magic * 0.5)

        new_hp = min(current_hp + hp_regen, max_hp)
        new_mp = min(current_mp + mp_regen, max_mp)

        hp_gained = new_hp - current_hp
        mp_gained = new_mp - current_mp

        self.db.set_player_vitals(self.discord_id, new_hp, new_mp)

        log_lines = AdventureEvents.regeneration()
        if hp_gained > 0:
            log_lines.append(f"You regenerated `{hp_gained}` HP.")
        if mp_gained > 0:
            log_lines.append(f"You regenerated `{mp_gained}` MP.")

        return {"log": log_lines, "dead": False}

    # --- NEW METHOD ---
    def _perform_quest_event(self) -> dict:
        """
        Finds a non-combat quest objective (gather, locate, etc.)
        """
        active_quests = self.quest_system.get_player_quests(self.discord_id)

        # Define the types of objectives we're looking for
        event_types = ["gather", "locate", "examine", "survey"]

        for quest in active_quests:
            objectives = quest.get("objectives", {})
            progress = quest.get("progress", {})

            for obj_type in event_types:
                if obj_type in objectives:
                    # Find the first task of this type that is not complete
                    for task, required in objectives[obj_type].items():
                        current = progress.get(obj_type, {}).get(task, 0)
                        if current < required:
                            # We found an event!
                            self.quest_system.update_progress(
                                self.discord_id, quest["id"], obj_type, task, 1
                            )
                            log_entry = AdventureEvents.quest_event(obj_type, task)
                            quest_update = (
                                f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*"
                            )
                            return {"log": [log_entry, quest_update], "dead": False}

        # If we get here, no non-combat quest events were found
        log_entry = AdventureEvents.no_event_found()
        return {"log": [log_entry], "dead": False}

    def _initiate_combat(self, location: dict) -> dict:
        """
        Finds a new monster and begins combat.
        """
        monster_pool = location["monsters"]
        choices, weights = zip(*monster_pool)
        monster_key = random.choices(choices, weights=weights, k=1)[0]
        monster_template = MONSTERS.get(monster_key)
        if not monster_template:
            return {"log": ["Error: Monster data missing."], "dead": False}

        self.active_monster = {
            "name": monster_template["name"],
            "level": monster_template["level"],
            "tier": monster_template["tier"],
            "HP": monster_template["hp"],
            "max_hp": monster_template["hp"],
            "MP": 10,
            "ATK": monster_template["atk"],
            "DEF": monster_template["def"],
            "xp": monster_template["xp"],
            "drops": monster_template.get("drops", []),
        }

        self.save_state()

        log_entry = CombatPhrases.opening(self.active_monster)
        self.logs.append(log_entry)
        return {"log": [log_entry], "dead": False}

    def _resolve_combat_turn(self) -> dict:
        """
        Resolves ONE turn of combat against self.active_monster.
        """
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        vitals = self.db.get_player_vitals(self.discord_id)
        current_hp = vitals["current_hp"]
        current_mp = vitals["current_mp"]

        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT level, experience, exp_to_next FROM players WHERE discord_id = ?",
            (self.discord_id,),
        )
        p_row = cur.fetchone()

        cur.execute(
            """
            SELECT s.key_id, s.name, s.type, ps.skill_level,
                   s.mp_cost, s.power_multiplier, s.heal_power
            FROM player_skills ps
            JOIN skills s ON ps.skill_key = s.key_id
            WHERE ps.discord_id = ? AND s.type = 'Active'
        """,
            (self.discord_id,),
        )
        player_skills_raw = cur.fetchall()
        conn.close()

        player_skills = [dict(row) for row in player_skills_raw]

        player_wrapper = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )
        player_wrapper.hp_current = current_hp

        engine = CombatEngine(
            player=player_wrapper,
            monster=self.active_monster,
            player_skills=player_skills,
            player_mp=current_mp,
        )

        result = engine.run_combat_turn()

        self.db.set_player_vitals(
            self.discord_id, result["hp_current"], result["mp_current"]
        )

        self.active_monster["HP"] = result["monster_hp"]

        is_dead = False
        combat_log = result["phrases"]

        if result["winner"] == "player":
            self.active_monster = None
            loot_text = []
            self.add_loot("exp", result["exp"])
            loot_text.append(f"`{result['exp']} EXP`")

            for drop_key, chance in result["drops"]:
                if random.randint(1, 100) <= chance:
                    self.add_loot(drop_key, 1)
                    mat_data = MATERIALS.get(drop_key)
                    item_name = mat_data["name"] if mat_data else drop_key
                    loot_text.append(f"`{item_name}`")

            equipment_drops = item_manager.generate_monster_loot(result["monster_data"])
            for item in equipment_drops:
                self.inventory_manager.add_item(
                    discord_id=self.discord_id,
                    item_key=str(item["id"]),
                    item_name=item["name"],
                    item_type="equipment",
                    amount=1,
                    slot=item["slot"],
                    item_source_table=item["source"],
                )
                loot_text.append(f"`{item['name']}`")

            if loot_text:
                combat_log.append(f"\n{E.ITEM_BOX} **Loot:** {', '.join(loot_text)}")

            quest_updates = self._update_quests(
                result["monster_data"]["name"], result["drops"]
            )
            if quest_updates:
                combat_log.append(
                    f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(quest_updates)}*"
                )

        elif result["winner"] == "monster":
            is_dead = True
            self.active = False
            self.active_monster = None

        self.logs.extend(combat_log)
        self.save_state()
        return {"log": combat_log, "dead": is_dead}

    def _update_quests(self, monster_name: str, drops: list) -> list:
        """
        Checks and updates 'defeat' and 'collect' quest objectives.
        """
        updated_quests = []
        active_quests = self.quest_system.get_player_quests(self.discord_id)

        for quest in active_quests:
            updated = False
            objectives = quest.get("objectives", {})

            # A. Check for monster kill objectives
            if "defeat" in objectives and monster_name in objectives["defeat"]:
                self.quest_system.update_progress(
                    self.discord_id, quest["id"], "defeat", monster_name
                )
                updated = True

            # B. Check for item collection objectives
            if "collect" in objectives:
                for drop_key, _ in drops:
                    if drop_key in objectives["collect"]:
                        self.quest_system.update_progress(
                            self.discord_id, quest["id"], "collect", drop_key
                        )
                        updated = True

            if updated and quest["title"] not in updated_quests:
                updated_quests.append(quest["title"])

        return updated_quests

    def add_loot(self, key, amount):
        if key in self.loot:
            self.loot[key] += amount
        else:
            self.loot[key] = amount

    def save_state(self):
        """Saves the session's current state to the database."""
        conn = self.db.connect()
        cur = conn.cursor()

        monster_json = json.dumps(self.active_monster) if self.active_monster else None

        cur.execute(
            """
            UPDATE adventure_sessions 
            SET logs = ?, loot_collected = ?, active = ?, active_monster_json = ?
            WHERE discord_id = ? AND active = 1
        """,
            (
                json.dumps(self.logs),
                json.dumps(self.loot),
                1 if self.active else 0,
                monster_json,
                self.discord_id,
            ),
        )
        conn.commit()
        conn.close()
