"""
event_handler.py

Handles non-combat logic:
- HP/MP Regeneration
- Quest Objective checks

Refactored to add spacing (\n) for better readability.
"""

import random
from typing import Dict, Any, Tuple
from game_systems.player.player_stats import PlayerStats
from .adventure_events import AdventureEvents
import game_systems.data.emojis as E

class EventHandler:
    def __init__(self, db, quest_system, discord_id):
        self.db = db
        self.quest_system = quest_system
        self.discord_id = discord_id

    def resolve_non_combat(self, regen_chance: int = 70) -> Dict[str, Any]:
        """Decides between Regen or Quest Event."""
        if random.randint(1, 100) <= regen_chance:
            return self._perform_regeneration()
        else:
            return self._perform_quest_event()

    def _perform_regeneration(self) -> Dict[str, Any]:
        stats = PlayerStats.from_dict(self.db.get_player_stats_json(self.discord_id))
        vitals = self.db.get_player_vitals(self.discord_id)
        
        if vitals["current_hp"] >= stats.max_hp and vitals["current_mp"] >= stats.max_mp:
            # Add spacing
            msg = f"\n{AdventureEvents.no_event_found()}"
            return {"log": [msg], "dead": False}
            
        hp_regen = max(1, int(stats.endurance * 0.5) + 1)
        mp_regen = max(1, int(stats.magic * 0.5) + 1)
        
        new_hp = min(vitals["current_hp"] + hp_regen, stats.max_hp)
        new_mp = min(vitals["current_mp"] + mp_regen, stats.max_mp)
        
        self.db.set_player_vitals(self.discord_id, new_hp, new_mp)
        
        # Fetch base logs and add spacing to the first line
        base_logs = AdventureEvents.regeneration()
        if base_logs:
            base_logs[0] = f"\n{base_logs[0]}"
        logs = base_logs

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
                            
                            # Format event text with spacing
                            event_text = f"\n{AdventureEvents.quest_event(obj_type, task)}"
                            
                            return {
                                "log": [
                                    event_text, 
                                    f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*"
                                ], 
                                "dead": False
                            }
        
        # No event found -> Spaced generic message
        msg = f"\n{AdventureEvents.no_event_found()}"
        return {"log": [msg], "dead": False}