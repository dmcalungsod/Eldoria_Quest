"""
game_systems/adventure/adventure_session.py

Coordinates adventure flow for a single player.
Hardened: Crash recovery, atomic state saving, and robust JSON handling.
"""

import json
import logging
import random
from typing import Any, Dict, List, Optional

from database.database_manager import DatabaseManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats

# Subsystems
from .adventure_rewards import AdventureRewards
from .combat_handler import CombatHandler
from .event_handler import EventHandler

logger = logging.getLogger("eldoria.session")


class AdventureSession:
    """
    Represents an ongoing adventure run for one player.
    The DB holds: location_id, logs, loot, active state, active monster json
    """

    REGEN_CHANCE = 40  # % chance the step becomes a non-combat event

    def __init__(
        self, 
        db: DatabaseManager, 
        quest_system, 
        inventory_manager, 
        discord_id: int, 
        row_data: Optional[dict] = None
    ):
        self.db = db
        self.discord_id = discord_id

        # Helpers
        self.rewards = AdventureRewards(db, discord_id)
        self.combat = CombatHandler(db, discord_id)
        self.events = EventHandler(db, quest_system, discord_id)

        self.quest_system = quest_system
        self.inventory_manager = inventory_manager

        # Safe State Restoration
        if row_data:
            self.location_id = row_data["location_id"]
            self.active = bool(row_data["active"])
            
            # Safe JSON Load
            try:
                self.logs = json.loads(row_data["logs"]) if row_data["logs"] else []
            except json.JSONDecodeError:
                self.logs = []

            try:
                self.loot = json.loads(row_data["loot_collected"]) if row_data["loot_collected"] else {}
            except json.JSONDecodeError:
                self.loot = {}

            try:
                self.active_monster = (
                    json.loads(row_data["active_monster_json"]) if row_data["active_monster_json"] else None
                )
            except json.JSONDecodeError:
                self.active_monster = None
        else:
            self.active = False
            self.active_monster = None
            self.loot = {}
            self.logs = []
            self.location_id = None

    # ======================================================================
    # MAIN STEP LOGIC
    # ======================================================================

    def simulate_step(self) -> Dict[str, Any]:
        """
        Executes one segment of an adventure.
        Returns: { "sequence": List[List[str]], "dead": bool }
        """
        location = LOCATIONS.get(self.location_id)
        if not location:
            return {"sequence": [["Error: Unknown location data."]], "dead": True}

        try:
            # --- 1. Continue Combat ---
            if self.active_monster:
                if self._should_auto():
                    return self._resolve_auto_combat()
                return self._process_combat_turn()

            # --- 2. Trigger New Encounter ---
            if random.randint(1, 100) > self.REGEN_CHANCE:
                monster, phrase = self.combat.initiate_combat(location)

                if monster:
                    # Start new combat
                    self.active_monster = monster
                    self.logs.append(phrase)
                    self.save_state()
                    return {"sequence": [[phrase]], "dead": False}

                # Location has no monster this tick
                msg = phrase or "The path is clear for now."
                self.logs.append(msg)
                self.save_state()
                return {"sequence": [[msg]], "dead": False}

            # --- 3. Non-Combat Event ---
            result = self.events.resolve_non_combat(regen_chance=70)
            self.logs.extend(result["log"])
            self.save_state()

            return {"sequence": [result["log"]], "dead": False}

        except Exception as e:
            logger.error(f"Simulation error for {self.discord_id}: {e}", exc_info=True)
            return {"sequence": [["*An ominous force interrupts your journey (System Error).*"]], "dead": False}

    # ======================================================================
    # AUTO COMBAT AI LOGIC
    # ======================================================================

    def _should_auto(self) -> bool:
        """
        Determines whether the player should use auto-combat.
        """
        if not self.active_monster:
            return False

        # Force manual for Bosses/Elites
        if self.active_monster.get("tier") in ("Boss", "Elite"):
            return False

        try:
            stats_json = self.db.get_player_stats_json(self.discord_id)
            stats = PlayerStats.from_dict(stats_json)
            vitals = self.db.get_player_vitals(self.discord_id)
            
            if not vitals: return False

            # Only auto if HP > 30%
            current_hp = vitals["current_hp"]
            max_hp = max(stats.max_hp, 1)
            return (current_hp / max_hp) >= 0.30
        except Exception:
            return False

    # ======================================================================
    # AUTO COMBAT SEQUENCE
    # ======================================================================

    def _resolve_auto_combat(self) -> Dict[str, Any]:
        """
        Plays multiple combat turns automatically.
        """
        report = self.combat.create_empty_battle_report()
        turn_reports = []
        sequence: List[List[str]] = []
        is_dead = False
        player_won = False

        # Get accumulated XP to prevent duplicate level up messages
        current_session_exp = self.loot.get("exp", 0)

        # Max 8 turns to avoid infinite loops
        for _ in range(8):
            # FIX: Pass session XP
            result = self.combat.resolve_turn(self.active_monster, report, current_session_exp)
            turn_reports.append(result.get("turn_report", {}))

            # Add narration for this turn
            if result["phrases"]:
                sequence.append(result["phrases"])

            # Safety: Drop to manual if HP is too low
            stats_json = self.db.get_player_stats_json(self.discord_id)
            stats = PlayerStats.from_dict(stats_json)
            
            if result["hp_current"] / max(stats.max_hp, 1) < 0.30:
                sequence.append(["\n⚠️ **Combat paused:** HP critical. Manual mode engaged."])
                break

            if result.get("winner") == "monster":
                is_dead = True
                self.active_monster = None
                break

            if result.get("winner") == "player":
                player_won = True
                self.active_monster = None
                break

        # Final Results Block
        final_block = []
        if player_won:
            final_block.append(
                f"\n⚔️ **Victory:** Defeated {result['monster_data']['name']} in {len(turn_reports)} rounds."
            )
            
            # Grant Rewards
            reward_texts = self.rewards.process_victory(
                battle_report=report,
                report_list=turn_reports,
                combat_result=result,
                quest_system=self.quest_system,
                inventory_manager=self.inventory_manager,
                session_loot=self.loot,
            )
            final_block.extend(reward_texts)

        elif is_dead:
            final_block.append("\n💀 **You have been defeated.**")

        if final_block:
            sequence.append(final_block)

        # Add to master log
        for frame in sequence:
            self.logs.extend(frame)

        self.save_state()
        return {"sequence": sequence, "dead": is_dead}

    # ======================================================================
    # MANUAL COMBAT TURN
    # ======================================================================

    def _process_combat_turn(self) -> Dict[str, Any]:
        """
        Executes a single combat turn for manual mode.
        """
        report = self.combat.create_empty_battle_report()
        
        # FIX: Pass session XP
        current_session_exp = self.loot.get("exp", 0)
        result = self.combat.resolve_turn(self.active_monster, report, current_session_exp)

        turn_logs = result["phrases"]
        is_dead = False

        # Determine outcome
        if result.get("winner") == "monster":
            is_dead = True
            self.active_monster = None
            turn_logs.append("\n💀 **You have been defeated.**")

        elif result.get("winner") == "player":
            self.active_monster = None
            turn_logs.append("\n⚔️ **Victory!**")

            reward_texts = self.rewards.process_victory(
                battle_report=report,
                report_list=[report],
                combat_result=result,
                quest_system=self.quest_system,
                inventory_manager=self.inventory_manager,
                session_loot=self.loot,
            )
            turn_logs.extend(reward_texts)

        self.logs.extend(turn_logs)
        self.save_state()

        return {"sequence": [turn_logs], "dead": is_dead}

    # ======================================================================
    # PERSISTENCE
    # ======================================================================

    def save_state(self):
        """
        Writes the current adventure state to the database.
        """
        m_json = json.dumps(self.active_monster) if self.active_monster else None
        
        # Limit logs to prevent DB bloat
        trimmed_logs = self.logs[-30:]

        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """
                    UPDATE adventure_sessions
                    SET logs=?, loot_collected=?, active=?, active_monster_json=?
                    WHERE discord_id=? AND active=1
                    """,
                    (
                        json.dumps(trimmed_logs),
                        json.dumps(self.loot),
                        1 if self.active else 0,
                        m_json,
                        self.discord_id,
                    ),
                )
        except Exception as e:
            logger.error(f"[AdventureSession] Failed to save state for {self.discord_id}: {e}")