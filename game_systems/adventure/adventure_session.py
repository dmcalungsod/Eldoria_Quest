"""
adventure_session.py

Represents a single active adventure session.
Handles the "Game Loop" logic:
- Hybrid Combat (Auto for trash mobs, Manual for bosses)
- Exploration Events
- State persistence
"""

import json
import random
import datetime
import logging
from typing import Optional, Dict, List, Any

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from .adventure_events import AdventureEvents

# --- NEW IMPORT: Delegate rewards to the helper class ---
from .adventure_rewards import AdventureRewards

logger = logging.getLogger("discord")

class AdventureSession:
    REGEN_CHANCE = 40  # 40% chance to regen/find event if not in combat

    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_system,
        inventory_manager,
        discord_id: int,
        row_data=None,
    ):
        self.db = db_manager
        self.quest_system = quest_system
        self.discord_id = discord_id
        
        # Initialize the Rewards Manager (Handles XP, Loot, Stats, Skills)
        self.rewards_manager = AdventureRewards(db_manager, discord_id)
        
        # We pass inventory manager to rewards via the method call later, 
        # or we can store it here if needed. Storing it here is fine.
        self.inventory_manager = inventory_manager

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
            self.loot = {}

    # ==================================================================
    # MAIN SIMULATION LOOP
    # ==================================================================

    def simulate_step(self) -> Dict[str, Any]:
        """
        Simulates one step.
        - If Monster is Active: Runs combat (Auto or Manual).
        - If No Monster: Rolls for Encounter or Event.
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"log": ["Error: Location data missing."], "dead": True}

        # 1. CONTINUE COMBAT
        if self.active_monster:
            if self._should_auto():
                return self._resolve_auto_combat()
            else:
                return self._process_combat_turn()

        # 2. ROLL FOR NEW ENCOUNTER (60%)
        if random.randint(1, 100) > self.REGEN_CHANCE:
            # Create the monster and return the intro text.
            # We return immediately so the player sees the intro.
            return {"log": self._initiate_combat(location), "dead": False}

        # 3. NON-COMBAT EVENT (40%)
        else:
            return self._resolve_non_combat_step()

    # ==================================================================
    # COMBAT DECISION LOGIC
    # ==================================================================

    def _should_auto(self) -> bool:
        """Returns True if we should Auto-Combat (Normal mob + Healthy)."""
        if not self.active_monster:
            return False
        
        # Bosses/Elites are always Manual
        if self.active_monster.get("tier") in ["Boss", "Elite"]:
            return False
        
        # Check Player Health (Must be > 30%)
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)
        
        # Avoid division by zero
        max_hp = max(stats.max_hp, 1)
        hp_percent = vitals["current_hp"] / max_hp

        return hp_percent >= 0.30

    # ==================================================================
    # COMBAT MODES
    # ==================================================================

    def _resolve_auto_combat(self) -> Dict[str, Any]:
        """
        AUTO MODE: Runs up to 8 turns instantly.
        Stops if victory, defeat, or low HP.
        """
        battle_report = self._create_empty_battle_report()
        reports = []
        logs = []
        is_dead = False
        player_won = False

        # Run up to 8 turns loop
        for _ in range(8):
            result = self._resolve_combat_turn(battle_report)
            reports.append(result["turn_report"])
            
            # Check HP Safety Net
            stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
            current_hp_percent = result["hp_current"] / max(stats.max_hp, 1)
            
            if current_hp_percent < 0.30:
                logs.append("⚠️ **Combat paused:** Health critical (<30%). Switching to manual control.")
                break

            # Check Outcomes
            if result.get("winner") == "monster":
                is_dead = True
                self.active = False
                self.active_monster = None
                break
            
            if result.get("winner") == "player":
                player_won = True
                self.active_monster = None
                break

        # Process Results
        if player_won:
            # DELEGATE REWARDS
            reward_logs = self.rewards_manager.process_victory(
                battle_report, 
                reports, 
                result, 
                self.quest_system, 
                self.inventory_manager, 
                self.loot
            )
            logs.extend(reward_logs)
            logs.append(f"⚔️ **Victory:** You defeated the {result['monster_data']['name']} in {len(reports)} rounds.")
            
        elif is_dead:
            logs.append("💀 You have been defeated in auto-combat...")

        self.logs.extend(logs)
        self.save_state()
        
        return {"log": logs, "dead": is_dead}

    def _process_combat_turn(self) -> Dict[str, Any]:
        """
        MANUAL MODE: Executes exactly ONE round of combat.
        """
        battle_report = self._create_empty_battle_report()
        
        # Run 1 Turn
        result = self._resolve_combat_turn(battle_report)
        logs = result["phrases"]
        is_dead = False

        if result.get("winner") == "monster":
            is_dead = True
            self.active = False
            self.active_monster = None
            
        elif result.get("winner") == "player":
            # DELEGATE REWARDS
            reward_logs = self.rewards_manager.process_victory(
                battle_report, 
                [battle_report], # List of 1 report
                result, 
                self.quest_system, 
                self.inventory_manager, 
                self.loot
            )
            logs.extend(reward_logs)
            self.active_monster = None

        self.logs.extend(logs)
        self.save_state()
        
        return {"log": logs, "dead": is_dead}

    # ==================================================================
    # ENGINE INTERFACE
    # ==================================================================

    def _resolve_combat_turn(self, battle_report: dict) -> dict:
        """Prepares data and runs the CombatEngine for one turn."""
        
        # 1. Fetch Player Data
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)
        vitals = self.db.get_player_vitals(self.discord_id)

        # 2. Fetch Skills & Class
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT level, experience, exp_to_next, class_id FROM players WHERE discord_id=?", 
                (self.discord_id,)
            )
            p_row = cur.fetchone()
            
            cur.execute(
                """SELECT s.key_id, s.name, s.type, ps.skill_level, s.mp_cost, 
                          s.power_multiplier, s.heal_power, s.buff_data 
                   FROM player_skills ps 
                   JOIN skills s ON ps.skill_key=s.key_id 
                   WHERE ps.discord_id=? AND s.type='Active'""", 
                (self.discord_id,)
            )
            skills_raw = cur.fetchall()

        # 3. Format Skills
        skills = []
        for row in skills_raw:
            s = dict(row)
            if s.get("buff_data"):
                try: s["buff_data"] = json.loads(s["buff_data"])
                except: s["buff_data"] = {}
            skills.append(s)

        # 4. Build Wrapper
        player_wrapper = LevelUpSystem(
            player_stats, p_row["level"], p_row["experience"], p_row["exp_to_next"]
        )
        player_wrapper.hp_current = vitals["current_hp"]

        # 5. Run Engine
        # (We fetch boosts here if needed, passing empty dict for now or fetching from DB)
        active_boosts = self._fetch_active_boosts()
        
        engine = CombatEngine(
            player_wrapper, 
            self.active_monster, 
            skills, 
            vitals["current_mp"], 
            p_row["class_id"], 
            active_boosts
        )
        result = engine.run_combat_turn()

        # 6. Update State
        self.db.set_player_vitals(self.discord_id, result["hp_current"], result["mp_current"])
        self.active_monster["HP"] = result["monster_hp"]
        
        # 7. Aggregate Report
        self._aggregate_battle_report(battle_report, result.get("turn_report", {}))
        
        return result

    # ==================================================================
    # EVENT & STATE HELPERS
    # ==================================================================

    def _resolve_non_combat_step(self) -> Dict[str, Any]:
        if random.randint(1, 100) <= 70: 
            result = self._perform_regeneration()
        else:
            result = self._perform_quest_event()
        
        self.logs.extend(result["log"])
        self.save_state()
        return result

    def _perform_regeneration(self) -> Dict[str, Any]:
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)
        
        if vitals["current_hp"] >= stats.max_hp and vitals["current_mp"] >= stats.max_mp:
            return {"log": [AdventureEvents.no_event_found()], "dead": False}
            
        hp_regen = max(1, int(stats.endurance * 0.5) + 1)
        mp_regen = max(1, int(stats.magic * 0.5) + 1)
        
        new_hp = min(vitals["current_hp"] + hp_regen, stats.max_hp)
        new_mp = min(vitals["current_mp"] + mp_regen, stats.max_mp)
        
        self.db.set_player_vitals(self.discord_id, new_hp, new_mp)
        
        logs = AdventureEvents.regeneration()
        if new_hp > vitals["current_hp"]: 
            logs.append(f"You regenerated `{new_hp - vitals['current_hp']}` HP.")
        if new_mp > vitals["current_mp"]: 
            logs.append(f"You regenerated `{new_mp - vitals['current_mp']}` MP.")
            
        return {"log": logs, "dead": False}

    def _perform_quest_event(self) -> Dict[str, Any]:
        active_quests = self.quest_system.get_player_quests(self.discord_id)
        event_types = ["gather", "locate", "examine", "survey", "escort", "retrieve", "deliver"]
        
        for quest in active_quests:
            objectives = quest.get("objectives", {})
            progress = quest.get("progress", {})
            
            for obj_type in event_types:
                if obj_type in objectives:
                    tasks = objectives[obj_type]
                    task_dict = tasks if isinstance(tasks, dict) else {tasks: 1}
                    
                    for task, req in task_dict.items():
                        current = (progress.get(obj_type) or {}).get(task, 0)
                        if current < req:
                            self.quest_system.update_progress(self.discord_id, quest["id"], obj_type, task, 1)
                            return {
                                "log": [
                                    AdventureEvents.quest_event(obj_type, task), 
                                    f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*"
                                ], 
                                "dead": False
                            }
                            
        return {"log": [AdventureEvents.no_event_found()], "dead": False}

    def _initiate_combat(self, location: Dict[str, Any]) -> List[str]:
        monster_pool = location["monsters"]
        choices, weights = zip(*monster_pool)
        monster_key = random.choices(choices, weights=weights, k=1)[0]
        template = MONSTERS.get(monster_key)
        
        self.active_monster = {
            "name": template["name"], "level": template["level"], "tier": template["tier"],
            "HP": template["hp"], "max_hp": template["hp"], "MP": 10,
            "ATK": template["atk"], "DEF": template["def"], "xp": template["xp"], 
            "drops": template.get("drops", [])
        }
        
        phrase = CombatPhrases.opening(self.active_monster)
        self.logs.append(phrase)
        self.save_state()
        return [phrase]

    def save_state(self):
        m_json = json.dumps(self.active_monster) if self.active_monster else None
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(
                    """UPDATE adventure_sessions 
                       SET logs=?, loot_collected=?, active=?, active_monster_json=? 
                       WHERE discord_id=? AND active=1""",
                    (json.dumps(self.logs), json.dumps(self.loot), 1 if self.active else 0, m_json, self.discord_id)
                )
        except Exception as e:
            logger.error(f"Save error: {e}")

    def _fetch_active_boosts(self):
        try:
            return {b["boost_key"]: b["multiplier"] for b in self.db.get_active_boosts()}
        except:
            return {}

    @staticmethod
    def _create_empty_battle_report():
        return {
            "str_hits": 0, "dex_hits": 0, "mag_hits": 0, 
            "player_crit": 0, "player_dodge": 0, "damage_taken": 0, 
            "skills_used": 0, "skill_key_used": None
        }

    @staticmethod
    def _aggregate_battle_report(base, turn):
        for k in base:
            if k != "skill_key_used":
                base[k] += turn.get(k, 0)
        base["skill_key_used"] = turn.get("skill_key_used")