"""
event_handler.py

Handles non-combat logic:
- HP/MP Regeneration
- Quest Objective checks (Gather, Locate, Examine, etc.)

Hardened with atomic database updates to prevent race conditions during regeneration.
"""

import random
import logging
from typing import Any, Dict

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.player.player_stats import PlayerStats
from .adventure_events import AdventureEvents

logger = logging.getLogger("eldoria.events")


class EventHandler:
    def __init__(self, db: DatabaseManager, quest_system, discord_id: int):
        self.db = db
        self.quest_system = quest_system
        self.discord_id = discord_id

    def resolve_non_combat(self, regen_chance: int = 70) -> Dict[str, Any]:
        """Decides between Regen or Quest Event."""
        try:
            if random.randint(1, 100) <= regen_chance:
                return self._perform_regeneration()
            else:
                return self._perform_quest_event()
        except Exception as e:
            logger.error(f"Event resolution error for {self.discord_id}: {e}", exc_info=True)
            # Fallback safe state
            return {"log": ["*You wander in silence, finding nothing.*"], "dead": False}

    def _perform_regeneration(self) -> Dict[str, Any]:
        """
        Calculates and applies regeneration safely.
        Uses an atomic transaction to ensure HP/MP updates are consistent.
        """
        try:
            # Fetch static stats (read-only, safe outside transaction)
            stats_json = self.db.get_player_stats_json(self.discord_id)
            stats = PlayerStats.from_dict(stats_json)
            
            with self.db.get_connection() as conn:
                # Fetch current vitals inside transaction to ensure currency
                row = conn.execute(
                    "SELECT current_hp, current_mp FROM players WHERE discord_id = ?", 
                    (self.discord_id,)
                ).fetchone()
                
                if not row:
                    return {"log": ["Error: Player data not found."], "dead": False}

                current_hp = row["current_hp"]
                current_mp = row["current_mp"]

                # If already full, return "no event" flavor text
                if current_hp >= stats.max_hp and current_mp >= stats.max_mp:
                    msg = f"\n{AdventureEvents.no_event_found()}"
                    return {"log": [msg], "dead": False}

                # Calculate Regen Amounts
                hp_regen = max(1, int(stats.endurance * 0.5) + 1)
                mp_regen = max(1, int(stats.magic * 0.5) + 1)

                new_hp = min(current_hp + hp_regen, stats.max_hp)
                new_mp = min(current_mp + mp_regen, stats.max_mp)

                # Apply Update Atomically
                conn.execute(
                    "UPDATE players SET current_hp = ?, current_mp = ? WHERE discord_id = ?",
                    (new_hp, new_mp, self.discord_id)
                )

            # Build Log Messages
            base_logs = AdventureEvents.regeneration()
            # Add newline to the first element for spacing
            if base_logs:
                base_logs[0] = f"\n{base_logs[0]}"
            
            if new_hp > current_hp:
                base_logs.append(f"You regenerated `{new_hp - current_hp}` HP.")
            if new_mp > current_mp:
                base_logs.append(f"You regenerated `{new_mp - current_mp}` MP.")

            return {"log": base_logs, "dead": False}

        except Exception as e:
            logger.error(f"Regen error for {self.discord_id}: {e}")
            return {"log": ["*You try to rest, but something feels wrong.*"], "dead": False}

    def _perform_quest_event(self) -> Dict[str, Any]:
        """
        Checks active quests for exploration objectives.
        Updates quest progress if a relevant event is triggered.
        """
        try:
            active_quests = self.quest_system.get_player_quests(self.discord_id)
            event_types = ["gather", "locate", "examine", "survey", "escort", "retrieve", "deliver"]

            for quest in active_quests:
                objectives = quest.get("objectives", {})
                progress = quest.get("progress", {})

                for obj_type in event_types:
                    if obj_type in objectives:
                        tasks = objectives[obj_type]
                        # Normalize single string task to dict
                        task_dict = tasks if isinstance(tasks, dict) else {tasks: 1}

                        for task, req in task_dict.items():
                            current = (progress.get(obj_type) or {}).get(task, 0)
                            
                            if current < req:
                                # Found a relevant incomplete objective
                                success = self.quest_system.update_progress(
                                    self.discord_id, quest["id"], obj_type, task, 1
                                )
                                
                                if success:
                                    event_text = f"\n{AdventureEvents.quest_event(obj_type, task)}"
                                    return {
                                        "log": [event_text, f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*"],
                                        "dead": False,
                                    }

            # If no matching quest event was found, return generic flavor text
            msg = f"\n{AdventureEvents.no_event_found()}"
            return {"log": [msg], "dead": False}
            
        except Exception as e:
            logger.error(f"Quest event error for {self.discord_id}: {e}")
            return {"log": ["*The path ahead is unclear.*"], "dead": False}