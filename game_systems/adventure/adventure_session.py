"""
adventure_session.py

The Coordinator for adventure logic.
Refactored to support "Dramatic Timing" by returning sequences of events
rather than a flat log list.
"""

import json
import random
import datetime
import logging
from typing import Optional, Dict, Any, List

from database.database_manager import DatabaseManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.player.player_stats import PlayerStats

# --- Modular Imports ---
from .adventure_rewards import AdventureRewards
from .combat_handler import CombatHandler
from .event_handler import EventHandler

logger = logging.getLogger("discord")

class AdventureSession:
    REGEN_CHANCE = 40

    def __init__(self, db: DatabaseManager, quest_system, inventory_manager, discord_id: int, row_data=None):
        self.db = db
        self.discord_id = discord_id
        
        # --- Initialize Helpers ---
        self.rewards = AdventureRewards(db, discord_id)
        self.combat = CombatHandler(db, discord_id)
        self.events = EventHandler(db, quest_system, discord_id)
        
        # We need quest/inventory systems for passing to rewards
        self.quest_system = quest_system
        self.inventory_manager = inventory_manager

        # --- Load State ---
        if row_data:
            self.location_id = row_data["location_id"]
            self.logs = json.loads(row_data["logs"])
            self.loot = json.loads(row_data["loot_collected"])
            self.active = bool(row_data["active"])
            self.active_monster = json.loads(row_data["active_monster_json"]) if row_data["active_monster_json"] else None
        else:
            self.active = False
            self.active_monster = None
            self.loot = {}

    def simulate_step(self) -> Dict[str, Any]:
        """
        Main Step Logic.
        Returns a dict containing 'sequence': List[List[str]].
        UI will print each inner list as a separate update with a delay.
        """
        location = LOCATIONS.get(self.location_id)
        if not location: 
            return {"sequence": [["Error: Location missing."]], "dead": True}

        # 1. CONTINUE COMBAT
        if self.active_monster:
            if self._should_auto():
                return self._resolve_auto_combat()
            else:
                return self._process_combat_turn()

        # 2. NEW ENCOUNTER
        if random.randint(1, 100) > self.REGEN_CHANCE:
            monster, phrase = self.combat.initiate_combat(location)
            if monster:
                self.active_monster = monster
                self.logs.append(phrase)
                self.save_state()
                # Return as single sequence (instant print)
                return {"sequence": [[phrase]], "dead": False}
            
            # Handle Empty Arena / No Monster
            message = phrase if phrase else "The path is clear for now."
            self.logs.append(message)
            self.save_state()
            return {"sequence": [[message]], "dead": False}

        # 3. NON-COMBAT EVENT (Regen / Quest)
        else:
            result = self.events.resolve_non_combat(70)
            self.logs.extend(result["log"])
            self.save_state()
            # Wrap the log in a list of lists so it prints instantly as one block
            return {"sequence": [result["log"]], "dead": False}

    def _should_auto(self) -> bool:
        if not self.active_monster: return False
        if self.active_monster.get("tier") in ["Boss", "Elite"]: return False
        
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)
        return (vitals["current_hp"] / max(stats.max_hp, 1)) >= 0.30

    def _resolve_auto_combat(self) -> Dict[str, Any]:
        """
        Auto-Combat Loop with DRAMA.
        Returns a sequence of turns so the UI can animate them.
        """
        report = self.combat.create_empty_battle_report()
        report_list = []
        
        # This will hold List[str], where each inner list is one "frame" of animation
        sequence = [] 
        
        is_dead, player_won = False, False

        for _ in range(8): # Max 8 turns
            # Run one turn
            result = self.combat.resolve_turn(self.active_monster, report)
            report_list.append(result["turn_report"])
            
            # Add this turn's logs as a distinct block in the sequence
            # We add a newline at the start of the block for spacing
            turn_logs = result["phrases"]
            if turn_logs:
                sequence.append(turn_logs)

            # Check Safety
            stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
            if result["hp_current"] / stats.max_hp < 0.30:
                sequence.append(["\n⚠️ **Combat paused:** Health critical. Manual mode engaged."])
                break

            if result.get("winner") == "monster":
                is_dead = True; self.active = False; self.active_monster = None; break
            if result.get("winner") == "player":
                player_won = True; self.active_monster = None; break

        # Handle End of Battle (Victory/Defeat)
        final_block = []
        if player_won:
            final_block.append(f"\n⚔️ **Victory:** Defeated {result['monster_data']['name']} in {len(report_list)} rounds.")
            # Calculate rewards
            reward_logs = self.rewards.process_victory(
                report, report_list, result, self.quest_system, self.inventory_manager, self.loot
            )
            final_block.extend(reward_logs)
            
        elif is_dead:
            final_block.append("\n💀 **You have been defeated.**")

        # Append final results as the last "frame"
        if final_block:
            sequence.append(final_block)

        # Update master log with everything that happened
        for block in sequence:
            self.logs.extend(block)
            
        self.save_state()
        return {"sequence": sequence, "dead": is_dead}

    def _process_combat_turn(self) -> Dict[str, Any]:
        """Manual Turn (Single Step)."""
        report = self.combat.create_empty_battle_report()
        result = self.combat.resolve_turn(self.active_monster, report)
        
        turn_logs = result["phrases"]
        is_dead = False
        
        # Check results immediately
        if result.get("winner") == "monster":
            is_dead = True; self.active = False; self.active_monster = None
            turn_logs.append("\n💀 **You have been defeated.**")
            
        elif result.get("winner") == "player":
            turn_logs.append(f"\n⚔️ **Victory!**")
            reward_logs = self.rewards.process_victory(
                report, [report], result, self.quest_system, self.inventory_manager, self.loot
            )
            turn_logs.extend(reward_logs)
            self.active_monster = None

        self.logs.extend(turn_logs)
        self.save_state()
        
        # Return as a single sequence block (no delay needed for manual clicks)
        return {"sequence": [turn_logs], "dead": is_dead}

    def save_state(self):
        m_json = json.dumps(self.active_monster) if self.active_monster else None
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute(
                    "UPDATE adventure_sessions SET logs=?, loot_collected=?, active=?, active_monster_json=? WHERE discord_id=? AND active=1",
                    (json.dumps(self.logs), json.dumps(self.loot), 1 if self.active else 0, m_json, self.discord_id)
                )
        except Exception as e: logger.error(f"Save error: {e}")