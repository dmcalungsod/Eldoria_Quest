"""
adventure_session.py

Represents a single active adventure session.
Refactored for TURN-BASED manual exploration.
"""

import json
import random
import datetime
import logging
from typing import Optional, Dict, List, Tuple, Any

from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.materials import MATERIALS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from game_systems.guild_system.quest_system import QuestSystem
from game_systems.items.inventory_manager import InventoryManager
from game_systems.items.item_manager import item_manager
from game_systems.data.emojis import get_rarity_ansi
import game_systems.data.emojis as E

from .adventure_events import AdventureEvents

# ============================================================================
# CONSTANTS
# ============================================================================

HIGH_RARITY_TIERS = {"Epic", "Legendary", "Mythical"}
STAT_EXP_THRESHOLD = 100
SKILL_EXP_THRESHOLD = 100
SKILL_EXP_PER_USE = 2.5

STAT_UP_MESSAGES = {
    "STR": f"{E.STR} Your arm feels stronger after the struggle. (STR +1)",
    "END": f"{E.CON} You feel more resilient, having weathered the blows. (END +1)",
    "DEX": f"{E.DEX} Your focus sharpens, finding new openings. (DEX +1)",
    "AGI": f"{E.AGI} Your body feels lighter, more attuned to the flow of battle. (AGI +1)",
    "MAG": f"{E.INT} Your understanding of the arcane deepens. (MAG +1)",
    "LCK": f"{E.LCK} The world seems to bend slightly to your will. (LCK +1)",
}

STAT_EXP_GAINS = {
    "str_exp": lambda br: br.get("str_hits", 0) * 0.5,
    "dex_exp": lambda br: (br.get("dex_hits", 0) * 0.5) + (br.get("player_crit", 0) * 2.0),
    "agi_exp": lambda br: br.get("player_dodge", 0) * 1.5,
    "end_exp": lambda br: br.get("damage_taken", 0) * 0.2,
    "mag_exp": lambda br: br.get("mag_hits", 0) * 1.0,
    "lck_exp": lambda br: 0.5,
}

logger = logging.getLogger("discord")


# ============================================================================
# ADVENTURE SESSION CLASS
# ============================================================================

class AdventureSession:
    """
    Manages a single active adventure session with turn-based combat
    and event resolution.
    """

    REGEN_CHANCE = 40  # 40% chance to regen/find event if not in combat

    def __init__(
        self,
        db_manager: DatabaseManager,
        quest_system: QuestSystem,
        inventory_manager: InventoryManager,
        discord_id: int,
        row_data: Optional[Dict[str, Any]] = None,
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

    # ========================================================================
    # PRIMARY STEP SIMULATION (MODIFIED FOR TURN-BASED)
    # ========================================================================

    def simulate_step(self) -> Dict[str, Any]:
        """
        Simulates one 'step'.
        - If Monster is Active: Runs ONE combat turn.
        - If No Monster: Rolls for Encounter (60%) or Event (40%).
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"log": ["Error: Location data missing."], "dead": True}

        # --- 1. CONTINUE COMBAT ---
        # If a monster is already fighting us, process the next turn
        if self.active_monster:
            return self._process_combat_turn()

        # --- 2. ROLL FOR NEW ENCOUNTER ---
        # 60% Chance for Combat
        if random.randint(1, 100) > self.REGEN_CHANCE:
            logger.info("Simulate Step: Initiating new combat.")
            # Create the monster and return the "A wild goblin appears!" text
            log_entries = self._initiate_combat(location)
            
            # We return immediately so the player sees the intro. 
            # They must click "Press Forward" again to actually fight.
            return {"log": log_entries, "dead": False}

        # --- 3. NON-COMBAT EVENT ---
        else:
            logger.info("Simulate Step: Initiating non-combat step.")
            return self._resolve_non_combat_step()

    def _process_combat_turn(self) -> Dict[str, Any]:
        """
        Executes exactly ONE round of combat (Player Action -> Monster Action).
        Handles victory/defeat checks and saving state.
        """
        logger.info("Simulate Step: Processing single combat turn...")
        
        # Initialize a report just for this turn
        battle_report = self._create_empty_battle_report()

        # 1. Run the Combat Engine for one turn
        combat_result = self._resolve_combat_turn(battle_report) 
        log_entries = combat_result["phrases"]
        is_dead = False

        # 2. Check Outcomes
        if combat_result.get("winner") == "monster":
            is_dead = True
            self.active = False # End session
            
        elif combat_result.get("winner") == "player":
            # Player won: Process rewards immediately
            # We pass [battle_report] as a list because _process_skill_exp expects a list
            self._process_victory_rewards(battle_report, [battle_report], combat_result, log_entries)
            self.active_monster = None

        # 3. Save the new state
        self.logs.extend(log_entries)
        self.save_state()
        
        return {"log": log_entries, "dead": is_dead}

    def _resolve_non_combat_step(self) -> Dict[str, Any]:
        """Execute a non-combat event (regeneration or quest progress)."""
        if random.randint(1, 100) <= 70: # 70% chance regen inside non-combat pool
            result = self._perform_regeneration()
        else:
            result = self._perform_quest_event()

        self.logs.extend(result["log"])
        self.save_state()
        return result

    # ========================================================================
    # COMBAT MECHANICS
    # ========================================================================

    def _initiate_combat(self, location: Dict[str, Any]) -> List[str]:
        """Spawn a monster from the location pool."""
        try:
            monster_pool = location["monsters"]
            choices, weights = zip(*monster_pool)
            monster_key = random.choices(choices, weights=weights, k=1)[0]

            monster_template = MONSTERS.get(monster_key)
            if not monster_template:
                return ["Error: Monster data missing."]

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

            log_entry = CombatPhrases.opening(self.active_monster)
            self.logs.append(log_entry)
            self.save_state()
            return [log_entry]

        except Exception as e:
            logger.error(f"Error initiating combat: {e}")
            return ["Error: Failed to initiate combat."]

    def _resolve_combat_turn(self, battle_report: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single combat turn using CombatEngine."""
        # Load player data
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)
        vitals = self.db.get_player_vitals(self.discord_id)

        # Fetch Player & Skills
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT level, experience, exp_to_next, class_id FROM players WHERE discord_id = ?",
                (self.discord_id,),
            )
            p_row = cur.fetchone()
            
            cur.execute(
                """
                SELECT s.key_id, s.name, s.type, ps.skill_level,
                       s.mp_cost, s.power_multiplier, s.heal_power, s.buff_data
                FROM player_skills ps
                JOIN skills s ON ps.skill_key = s.key_id
                WHERE ps.discord_id = ? AND s.type = 'Active'
                """,
                (self.discord_id,),
            )
            player_skills_raw = cur.fetchall()

        # Process skills JSON
        player_skills = []
        for row in player_skills_raw:
            skill = dict(row)
            if skill.get("buff_data"):
                try:
                    skill["buff_data"] = json.loads(skill["buff_data"])
                except (json.JSONDecodeError, TypeError):
                    skill["buff_data"] = {}
            player_skills.append(skill)

        # Build Player Object
        player_wrapper = LevelUpSystem(
            stats=player_stats,
            level=p_row["level"],
            exp=p_row["experience"],
            exp_to_next=p_row["exp_to_next"],
        )
        player_wrapper.hp_current = vitals["current_hp"]

        active_boosts = self._fetch_active_boosts()

        # Run Engine
        engine = CombatEngine(
            player=player_wrapper,
            monster=self.active_monster,
            player_skills=player_skills,
            player_mp=vitals["current_mp"],
            player_class_id=p_row["class_id"],
            active_boosts=active_boosts,
        )

        result = engine.run_combat_turn()

        # Update Database
        self.db.set_player_vitals(
            self.discord_id, result["hp_current"], result["mp_current"]
        )
        self.active_monster["HP"] = result["monster_hp"]

        # Update Report
        turn_report = result.get("turn_report", {})
        self._aggregate_battle_report(battle_report, turn_report)

        # Handle Loot on Win
        if result.get("winner") == "player":
            self._process_loot_and_quests(result)

        return result

    def _process_loot_and_quests(self, combat_result: Dict[str, Any]):
        """Process loot drops and quest updates from combat victory."""
        colored_loot_lines = []

        # EXP
        self.add_loot("exp", combat_result["exp"])
        colored_loot_lines.append(get_rarity_ansi("Common", f"• {combat_result['exp']} EXP"))

        # Stats & Boosts
        player_stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        luck_bonus = (player_stats.luck / 999) * 50.0
        loot_boost_mult = combat_result.get("active_boosts", {}).get("loot_boost", 1.0)

        # Materials
        for drop_key, base_chance in combat_result["drops"]:
            mat_data = MATERIALS.get(drop_key)
            item_rarity = mat_data.get("rarity", "Common") if mat_data else "Common"
            
            final_chance = base_chance * loot_boost_mult
            if item_rarity in HIGH_RARITY_TIERS:
                final_chance += luck_bonus

            if random.randint(1, 100) <= final_chance:
                self.add_loot(drop_key, 1)
                item_name = mat_data.get("name", drop_key) if mat_data else drop_key
                colored_loot_lines.append(get_rarity_ansi(item_rarity, f"• {item_name}"))

        # Equipment
        equipment_drops = item_manager.generate_monster_loot(combat_result["monster_data"])
        for item in equipment_drops:
            try:
                self.inventory_manager.add_item(
                    discord_id=self.discord_id,
                    item_key=str(item["id"]),
                    item_name=item["name"],
                    item_type="equipment",
                    rarity=item["rarity"],
                    amount=1,
                    slot=item["slot"],
                    item_source_table=item["source"],
                )
                colored_loot_lines.append(get_rarity_ansi(item["rarity"], f"• {item['name']}"))
            except Exception as e:
                logger.error(f"Failed to add equipment: {e}")

        if colored_loot_lines:
            loot_block = "\n".join(colored_loot_lines)
            combat_result["phrases"].append(f"\n{E.ITEM_BOX} **Loot**\n```ansi\n{loot_block}\n```")

        # Quests
        quest_updates = self._update_quests(combat_result["monster_data"]["name"], combat_result["drops"])
        if quest_updates:
            combat_result["phrases"].append(f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(quest_updates)}*")

    def _process_victory_rewards(self, battle_report, battle_reports_list, combat_result, log_entries):
        self._process_stat_exp(battle_report, log_entries)
        self._process_skill_exp(battle_reports_list, log_entries)
        self._increment_kill_counter(combat_result["monster_data"]["tier"])

    # ========================================================================
    # STAT & SKILL PROGRESSION (Unchanged logic, just pasted into new structure)
    # ========================================================================

    def _process_stat_exp(self, battle_report: Dict[str, Any], log_entries: List[str]):
        # ... (Same logic as provided in previous artifacts) ...
        gains = {key: calc(battle_report) for key, calc in STAT_EXP_GAINS.items()}
        
        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp FROM stats WHERE discord_id = ?", (self.discord_id,))
                row = cur.fetchone()
                if not row: return

                stats_data = json.loads(row["stats_json"])
                base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}
                
                current_exp = {
                    "str_exp": row["str_exp"], "end_exp": row["end_exp"], "dex_exp": row["dex_exp"],
                    "agi_exp": row["agi_exp"], "mag_exp": row["mag_exp"], "lck_exp": row["lck_exp"]
                }
                stat_up_messages = []

                for exp_key, gain in gains.items():
                    if gain <= 0: continue
                    stat_abbrev = exp_key.split("_")[0].upper()
                    current_exp[exp_key] += gain
                    
                    while current_exp[exp_key] >= STAT_EXP_THRESHOLD:
                        current_exp[exp_key] -= STAT_EXP_THRESHOLD
                        base_stats[stat_abbrev] += 1
                        stat_up_messages.append(STAT_UP_MESSAGES.get(stat_abbrev, ""))

                for stat, base_val in base_stats.items():
                    if stat in stats_data: stats_data[stat]["base"] = base_val

                cur.execute(
                    "UPDATE stats SET stats_json = ?, str_exp = ?, end_exp = ?, dex_exp = ?, agi_exp = ?, mag_exp = ?, lck_exp = ? WHERE discord_id = ?",
                    (json.dumps(stats_data), current_exp["str_exp"], current_exp["end_exp"], current_exp["dex_exp"], current_exp["agi_exp"], current_exp["mag_exp"], current_exp["lck_exp"], self.discord_id)
                )
                if stat_up_messages: log_entries.append("\n" + "\n".join(stat_up_messages))
        except Exception as e:
            logger.error(f"Error processing stat exp: {e}")

    def _process_skill_exp(self, battle_reports_list: List[Dict[str, Any]], log_entries: List[str]):
        skill_uses = {}
        for report in battle_reports_list:
            skill_key = report.get("skill_key_used")
            if skill_key: skill_uses[skill_key] = skill_uses.get(skill_key, 0) + 1
        
        if not skill_uses: return

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                skill_up_messages = []
                for skill_key, times_used in skill_uses.items():
                    exp_gain = times_used * SKILL_EXP_PER_USE
                    cur.execute("SELECT skill_level, skill_exp, s.name FROM player_skills ps JOIN skills s ON ps.skill_key = s.key_id WHERE ps.discord_id = ? AND ps.skill_key = ?", (self.discord_id, skill_key))
                    skill_row = cur.fetchone()
                    if not skill_row: continue
                    
                    curr_lvl, curr_exp, s_name = skill_row["skill_level"], skill_row["skill_exp"], skill_row["name"]
                    curr_exp += exp_gain
                    
                    while curr_exp >= SKILL_EXP_THRESHOLD:
                        curr_exp -= SKILL_EXP_THRESHOLD
                        curr_lvl += 1
                        skill_up_messages.append(f"{E.LEVEL_UP} Your **{s_name}** has reached **Level {curr_lvl}**!")
                    
                    cur.execute("UPDATE player_skills SET skill_level = ?, skill_exp = ? WHERE discord_id = ? AND skill_key = ?", (curr_lvl, curr_exp, self.discord_id, skill_key))
                
                if skill_up_messages: log_entries.append("\n" + "\n".join(skill_up_messages))
        except Exception as e:
            logger.error(f"Error processing skill exp: {e}")

    # ========================================================================
    # NON-COMBAT EVENTS (Regen logic pasted)
    # ========================================================================
    
    def _perform_regeneration(self) -> Dict[str, Any]:
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)
        curr_hp, curr_mp = vitals["current_hp"], vitals["current_mp"]
        max_hp, max_mp = stats.max_hp, stats.max_mp

        if curr_hp >= max_hp and curr_mp >= max_mp:
            return {"log": [AdventureEvents.no_event_found()], "dead": False}

        new_hp = min(curr_hp + max(1, int(stats.endurance * 0.5) + 1), max_hp)
        new_mp = min(curr_mp + max(1, int(stats.magic * 0.5) + 1), max_mp)
        
        self.db.set_player_vitals(self.discord_id, new_hp, new_mp)
        
        log_lines = AdventureEvents.regeneration()
        if new_hp > curr_hp: log_lines.append(f"You regenerated `{new_hp - curr_hp}` HP.")
        if new_mp > curr_mp: log_lines.append(f"You regenerated `{new_mp - curr_mp}` MP.")
        return {"log": log_lines, "dead": False}
    
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
                            return {"log": [AdventureEvents.quest_event(obj_type, task), f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*"], "dead": False}
        return {"log": [AdventureEvents.no_event_found()], "dead": False}

    # ========================================================================
    # UTILITY & HELPERS
    # ========================================================================

    def _fetch_active_boosts(self) -> Dict[str, float]:
        try:
            return {b["boost_key"]: b["multiplier"] for b in self.db.get_active_boosts()}
        except: return {}

    @staticmethod
    def _create_empty_battle_report() -> Dict[str, Any]:
        return {"str_hits": 0, "dex_hits": 0, "mag_hits": 0, "player_crit": 0, "player_dodge": 0, "damage_taken": 0, "skills_used": 0, "skill_key_used": None}

    @staticmethod
    def _aggregate_battle_report(battle_report, turn_report):
        for key in battle_report:
            if key != "skill_key_used": battle_report[key] += turn_report.get(key, 0)
        battle_report["skill_key_used"] = turn_report.get("skill_key_used")

    def _increment_kill_counter(self, tier):
        col = {"Normal": "normal_kills", "Elite": "elite_kills", "Boss": "boss_kills"}.get(tier)
        if col:
            try:
                with self.db.get_connection() as conn:
                    conn.cursor().execute(f"UPDATE guild_members SET {col} = {col} + 1 WHERE discord_id = ?", (self.discord_id,))
            except: pass

    def _update_quests(self, name, drops):
        updated = []
        quests = self.quest_system.get_player_quests(self.discord_id)
        for q in quests:
            objs = q.get("objectives", {})
            hit = False
            if "defeat" in objs and name in objs["defeat"]:
                self.quest_system.update_progress(self.discord_id, q["id"], "defeat", name)
                hit = True
            if "collect" in objs:
                for k, _ in drops:
                    if k in objs["collect"]:
                        self.quest_system.update_progress(self.discord_id, q["id"], "collect", k)
                        hit = True
            if hit and q["title"] not in updated: updated.append(q["title"])
        return updated

    def add_loot(self, key, amount):
        self.loot[key] = self.loot.get(key, 0) + amount

    def save_state(self):
        monster_json = json.dumps(self.active_monster) if self.active_monster else None
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE adventure_sessions SET logs = ?, loot_collected = ?, active = ?, active_monster_json = ? WHERE discord_id = ? AND active = 1",
                    (json.dumps(self.logs), json.dumps(self.loot), 1 if self.active else 0, monster_json, self.discord_id)
                )
        except Exception as e: logger.error(f"Save error: {e}")
