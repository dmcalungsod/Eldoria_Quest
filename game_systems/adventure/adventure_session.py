"""
adventure_session.py

Represents a single active adventure session.
Handles the simulation of combat steps and log generation.
(Refactored for manual, step-by-step exploration)
"""

import json
import random
import datetime
import logging
import math # <-- NEW: IMPORTED MATH
from database.database_manager import DatabaseManager
from game_systems.combat.combat_engine import CombatEngine
from game_systems.combat.combat_phrases import CombatPhrases
from game_systems.data.monsters import MONSTERS
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats
from game_systems.player.level_up import LevelUpSystem
from game_systems.guild_system.quest_system import QuestSystem
import game_systems.data.emojis as E

from game_systems.data.materials import MATERIALS
from game_systems.items.inventory_manager import InventoryManager
from game_systems.items.item_manager import item_manager

from .adventure_events import AdventureEvents

from game_systems.data.emojis import get_rarity_ansi

# --- 1. DEFINE HIGH-TIER RARITIES (NEW) ---
HIGH_RARITY_TIERS = ["Epic", "Legendary", "Mythical"]
# --- END OF NEW CODE ---

# --- NEW: STAT EXP THRESHOLD ---
STAT_EXP_THRESHOLD = 100
# --- END NEW ---

# Get the logger
logger = logging.getLogger("discord")


class AdventureSession:

    REGEN_CHANCE = 70  # 70% chance to regen

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
        This will either be a non-combat event OR a full auto-battle.
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"log": ["Error: Location data missing."], "dead": True}

        # This function is only called when not in combat.
        # We roll for an event.

        if random.randint(1, 100) > 40:
            # 60% chance: FULL COMBAT
            logger.info("Simulate Step: Initiating full combat.")

            # 1. Get the "encounter" line
            log_entries = self._initiate_combat(location)

            if not self.active_monster:
                logger.error(
                    "Simulate Step: _initiate_combat failed to create monster."
                )
                self.save_state()  # Save error log
                return {"log": log_entries, "dead": False}

            # --- NEW: Initialize aggregated battle report ---
            battle_report = {
                "str_hits": 0,
                "dex_hits": 0,
                "mag_hits": 0,
                "player_crit": 0,
                "player_dodge": 0,
                "damage_taken": 0,
                "skills_used": 0,
            }
            # --- END NEW ---

            # 2. Run the battle loop until there is a winner
            is_dead = False
            while self.active_monster and not is_dead:
                logger.info("Simulate Step: Running combat turn...")
                
                # --- MODIFIED: Pass the battle_report to be updated ---
                combat_result = self._resolve_combat_turn(battle_report)  # This runs one turn

                log_entries.extend(combat_result["phrases"])

                # --- NEW: Aggregate turn report into battle report ---
                turn_report = combat_result.get("turn_report", {})
                for key in battle_report:
                    battle_report[key] += turn_report.get(key, 0)
                # --- END NEW ---

                if combat_result.get("winner") == "monster":
                    is_dead = True
            
            # --- NEW: If player won, process stat exp ---
            if not is_dead and combat_result.get("winner") == "player":
                # We pass the final combat_result log to append stat-up messages
                self._process_stat_exp(battle_report, combat_result["phrases"])
                
                # --- THIS IS THE FIX ---
                # Increment the kill counter for Guild Rank
                self._increment_kill_counter(combat_result["monster_data"]["tier"])
                # --- END OF FIX ---
                
            # --- END NEW ---

            logger.info(f"Simulate Step: Combat finished. Dead: {is_dead}")
            return {"log": log_entries, "dead": is_dead}

        else:
            # 40% chance: Non-combat event
            logger.info("Simulate Step: Initiating non-combat step.")
            return self._resolve_non_combat_step()

    def _resolve_non_combat_step(self) -> dict:
        """
        Handles a single non-combat event.
        """
        if random.randint(1, 100) <= self.REGEN_CHANCE:
            result = self._perform_regeneration()
        else:
            result = self._perform_quest_event()

        self.logs.extend(result["log"])
        self.save_state()  # Save state after the event
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
            log_entry = AdventureEvents.no_event_found()
            return {"log": [log_entry], "dead": False}

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

    def _perform_quest_event(self) -> dict:
        """
        Finds a non-combat quest objective (gather, locate, etc.)
        """
        active_quests = self.quest_system.get_player_quests(self.discord_id)
        event_types = ["gather", "locate", "examine", "survey"]

        for quest in active_quests:
            objectives = quest.get("objectives", {})
            progress = quest.get("progress", {})

            for obj_type in event_types:
                if obj_type in objectives:
                    for task, required in objectives[obj_type].items():
                        current = progress.get(obj_type, {}).get(task, 0)
                        if current < required:
                            self.quest_system.update_progress(
                                self.discord_id, quest["id"], obj_type, task, 1
                            )
                            log_entry = AdventureEvents.quest_event(obj_type, task)
                            quest_update = (
                                f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*"
                            )
                            return {"log": [log_entry, quest_update], "dead": False}

        log_entry = AdventureEvents.no_event_found()
        return {"log": [log_entry], "dead": False}

    def _initiate_combat(self, location: dict) -> list:
        """
        Finds a new monster, sets it as active, and saves the state.
        Returns the opening log entry as a list.
        """
        monster_pool = location["monsters"]
        choices, weights = zip(*monster_pool)
        monster_key = random.choices(choices, weights=weights, k=1)[0]
        monster_template = MONSTERS.get(monster_key)
        if not monster_template:
            logger.error(f"Monster data missing for key: {monster_key}")
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

        logger.info(f"Combat Initiated: {self.active_monster['name']}")

        # Save the *start* of the combat
        self.save_state()

        return [log_entry]

    def _resolve_combat_turn(self, battle_report: dict) -> dict:
        """
        Resolves ONE turn of combat and saves the new state.
        """
        stats_json = self.db.get_player_stats_json(self.discord_id)
        player_stats = PlayerStats.from_dict(stats_json)

        vitals = self.db.get_player_vitals(self.discord_id)
        current_hp = vitals["current_hp"]
        current_mp = vitals["current_mp"]

        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT level, experience, exp_to_next, class_id FROM players WHERE discord_id = ?",
            (self.discord_id,),
        )
        p_row = cur.fetchone()

        player_class_id = p_row["class_id"] if p_row else 0

        # FIX: Added s.buff_data to the skill fetch query
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
        conn.close()

        player_skills = [dict(row) for row in player_skills_raw]

        # FIX: Deserialize buff_data for combat engine
        for skill in player_skills:
            if skill["buff_data"]:
                try:
                    skill["buff_data"] = json.loads(skill["buff_data"])
                except json.JSONDecodeError:
                    skill["buff_data"] = {}
        # END FIX

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
            player_class_id=player_class_id,
        )

        result = engine.run_combat_turn()

        self.db.set_player_vitals(
            self.discord_id, result["hp_current"], result["mp_current"]
        )

        self.active_monster["HP"] = result["monster_hp"]

        combat_log = result["phrases"]

        if result.get("winner") == "player":
            self.active_monster = None  # Clear monster for next loop check

            colored_loot_lines = []
            self.add_loot("exp", result["exp"])
            # Add EXP to the list, formatted with "Common" color
            colored_loot_lines.append(
                get_rarity_ansi("Common", f"• {result['exp']} EXP")
            )

            # --- 2. LUCK CALCULATION (NEW FORMULA) ---
            player_luck = player_wrapper.stats.luck
            # Formula: Scales to +50% at 999 LCK
            # (player_luck / 999) gives a 0-1 multiplier
            luck_bonus = (player_luck / 999) * 50.0
            # --- END OF NEW FORMULA ---

            # 1. Handle Material Drops
            for drop_key, chance in result["drops"]:

                # --- 3. APPLY LUCK BONUS CONDITIONALLY (NEW LOGIC) ---
                final_chance = chance
                mat_data = MATERIALS.get(drop_key)

                item_rarity = "Common"  # Default rarity
                if mat_data:
                    item_rarity = mat_data.get("rarity", "Common")
                    # Apply bonus only if the item rarity is Epic or higher
                    if item_rarity in HIGH_RARITY_TIERS:
                        final_chance += luck_bonus

                if random.randint(1, 100) <= final_chance:
                    self.add_loot(drop_key, 1)
                    item_name = mat_data.get("name", drop_key) if mat_data else drop_key

                    # --- THIS IS THE FIX ---
                    # Removed rarity text from the log
                    text = f"• {item_name}"
                    colored_loot_lines.append(get_rarity_ansi(item_rarity, text))
                # --- END OF NEW LOGIC ---

            # 2. Handle Equipment Drops
            equipment_drops = item_manager.generate_monster_loot(result["monster_data"])
            for item in equipment_drops:
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

                # --- THIS IS THE FIX ---
                # Removed rarity text from the log
                text = f"• {item['name']}"
                colored_loot_lines.append(get_rarity_ansi(item["rarity"], text))

            if colored_loot_lines:
                # Build the final ANSI block
                loot_block = "\n".join(colored_loot_lines)
                combat_log.append(
                    f"\n{E.ITEM_BOX} **Loot**\n```ansi\n{loot_block}\n```"
                )

            quest_updates = self._update_quests(
                result["monster_data"]["name"], result["drops"]
            )
            if quest_updates:
                combat_log.append(
                    f"{E.QUEST_SCROLL} *Quest Updated: {', '.join(quest_updates)}*"
                )

        elif result.get("winner") == "monster":
            self.active = False  # Player is dead, end session
            self.active_monster = None

        self.logs.extend(combat_log)
        self.save_state()  # Save the result of this turn
        return result

    # --- NEW FUNCTION: _process_stat_exp ---
    def _process_stat_exp(self, battle_report: dict, log_entries: list):
        """
        Processes the aggregated battle report, grants stat exp,
        and handles automatic stat level-ups.
        Appends messages to the log_entries list.
        """
        
        # --- THIS IS THE FIX: Updated formulas ---
        gains = {
            "str_exp": battle_report.get("str_hits", 0) * 0.5,
            "dex_exp": (battle_report.get("dex_hits", 0) * 0.5) + (battle_report.get("player_crit", 0) * 2.0),
            "agi_exp": battle_report.get("player_dodge", 0) * 1.5,
            "end_exp": battle_report.get("damage_taken", 0) * 0.2,
            "mag_exp": battle_report.get("mag_hits", 0) * 1.0,
            "lck_exp": 0.5,  # Flat 0.5 LCK exp for *surviving* a battle
        }
        # --- END OF FIX ---

        # 2. Get current stats and stat_exp from DB
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT stats_json, str_exp, end_exp, dex_exp, agi_exp, mag_exp, lck_exp FROM stats WHERE discord_id = ?", 
                (self.discord_id,)
            )
            row = cur.fetchone()
            if not row:
                return

            stats_data = json.loads(row["stats_json"])
            base_stats = {k: v.get("base", 1) for k, v in stats_data.items()}
            
            current_exp = {
                "str_exp": row["str_exp"],
                "end_exp": row["end_exp"],
                "dex_exp": row["dex_exp"],
                "agi_exp": row["agi_exp"],
                "mag_exp": row["mag_exp"],
                "lck_exp": row["lck_exp"],
            }

            stat_up_messages = []

            # 3. Calculate new totals and check for level-ups
            for key, gain in gains.items():
                if gain > 0:
                    stat_name = key.split("_")[0].upper() # e.g., "STR"
                    
                    # Add gain to current exp
                    current_exp[key] += gain
                    
                    # Check for stat level up
                    if current_exp[key] >= STAT_EXP_THRESHOLD:
                        current_exp[key] -= STAT_EXP_THRESHOLD # Subtract threshold
                        base_stats[stat_name] += 1 # Increase base stat
                        
                        # Add a thematic message
                        if stat_name == "STR":
                            stat_up_messages.append(f"{E.STR} Your arm feels stronger after the struggle. (STR +1)")
                        elif stat_name == "END":
                            stat_up_messages.append(f"{E.CON} You feel more resilient, having weathered the blows. (END +1)")
                        elif stat_name == "DEX":
                            stat_up_messages.append(f"{E.DEX} Your focus sharpens, finding new openings. (DEX +1)")
                        elif stat_name == "AGI":
                            stat_up_messages.append(f"{E.AGI} Your body feels lighter, more attuned to the flow of battle. (AGI +1)")
                        elif stat_name == "MAG":
                            stat_up_messages.append(f"{E.INT} Your understanding of the arcane deepens. (MAG +1)")
                        elif stat_name == "LCK":
                            stat_up_messages.append(f"{E.LCK} The world seems to bend slightly to your will. (LCK +1)")

            # 4. Save everything back to the DB
            
            # Update the stats_json with new base stats
            for stat, base_val in base_stats.items():
                if stat in stats_data:
                    stats_data[stat]["base"] = base_val
            
            # Update the stats table with new EXP and new stats_json
            cur.execute(
                """
                UPDATE stats
                SET 
                    stats_json = ?,
                    str_exp = ?,
                    end_exp = ?,
                    dex_exp = ?,
                    agi_exp = ?,
                    mag_exp = ?,
                    lck_exp = ?
                WHERE discord_id = ?
                """,
                (
                    json.dumps(stats_data),
                    current_exp["str_exp"],
                    current_exp["end_exp"],
                    current_exp["dex_exp"],
                    current_exp["agi_exp"],
                    current_exp["mag_exp"],
                    current_exp["lck_exp"],
                    self.discord_id
                )
            )
            
            # 5. Add messages to the log
            if stat_up_messages:
                log_entries.append("\n" + "\n".join(stat_up_messages))

    # --- END NEW FUNCTION ---
    
    # --- NEW FUNCTION: _increment_kill_counter ---
    def _increment_kill_counter(self, monster_tier: str):
        """
        Increments the correct kill counter in the guild_members table
        based on the monster's tier.
        """
        
        # Determine which column to update
        if monster_tier == "Normal":
            column_to_update = "normal_kills"
        elif monster_tier == "Elite":
            column_to_update = "elite_kills"
        elif monster_tier == "Boss":
            column_to_update = "boss_kills"
        else:
            return # Don't update for unknown tiers

        try:
            with self.db.get_connection() as conn:
                cur = conn.cursor()
                # Use f-string safely here because we've controlled the input
                cur.execute(
                    f"""
                    UPDATE guild_members
                    SET {column_to_update} = {column_to_update} + 1
                    WHERE discord_id = ?
                    """,
                    (self.discord_id,)
                )
        except Exception as e:
            logger.error(f"Failed to increment kill counter for {self.discord_id}: {e}")
    # --- END NEW FUNCTION ---

    def _update_quests(self, monster_name: str, drops: list) -> list:
        """
        Checks and updates 'defeat' and 'collect' quest objectives.
        """
        updated_quests = []
        active_quests = self.quest_system.get_player_quests(self.discord_id)

        for quest in active_quests:
            updated = False
            objectives = quest.get("objectives", {})

            if "defeat" in objectives and monster_name in objectives["defeat"]:
                self.quest_system.update_progress(
                    self.discord_id, quest["id"], "defeat", monster_name
                )
                updated = True

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