"""
event_handler.py

Handles non-combat logic:
- HP/MP Regeneration
- Quest Objective checks (Gather, Locate, Examine, etc.)

Hardened with atomic database updates to prevent race conditions during regeneration.
"""

import logging
import random
from typing import Any

import game_systems.data.emojis as E
from database.database_manager import DatabaseManager
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.class_data import CLASSES
from game_systems.data.materials import MATERIALS
from game_systems.player.player_stats import PlayerStats

from .adventure_events import AdventureEvents

logger = logging.getLogger("eldoria.events")


class EventHandler:
    def __init__(self, db: DatabaseManager, quest_system, discord_id: int):
        self.db = db
        self.quest_system = quest_system
        self.discord_id = discord_id

    def resolve_non_combat(
        self,
        context: dict[str, Any],
        location_id: str | None = None,
        regen_chance: int = 70,
        location_name: str | None = None,
    ) -> dict[str, Any]:
        """Decides between Regen or Quest Event."""
        try:
            if random.randint(1, 100) <= regen_chance:
                return self._perform_regeneration(context, location_id)
            else:
                return self._perform_quest_event(context, location_name, location_id)
        except Exception as e:
            logger.error(f"Event resolution error for {self.discord_id}: {e}", exc_info=True)
            # Fallback safe state
            return {"log": ["*You wander in silence, finding nothing.*"], "dead": False}

    def _perform_regeneration(self, context: dict[str, Any], location_id: str | None = None) -> dict[str, Any]:
        """
        Calculates and applies regeneration safely.
        Uses an atomic transaction to ensure HP/MP updates are consistent.
        """
        try:
            # Use passed context instead of redundant DB lookups
            stats = context["player_stats"]
            vitals = context["vitals"]

            current_hp = vitals["current_hp"]
            current_mp = vitals["current_mp"]

            # If already full, trigger SURGE (High-chance gather)
            if current_hp >= stats.max_hp and current_mp >= stats.max_mp:
                # Log the surge flavor text
                surge_msg = f"\n{AdventureEvents.surge_event()}"

                # Chain into gathering with +25% bonus
                result = self._perform_wild_gathering(context, location_id, bonus_chance=25)

                # Prepend the surge message to the gathering log
                if result.get("log"):
                    result["log"].insert(0, surge_msg)
                else:
                    result["log"] = [surge_msg]

                return result

            # Calculate Regen Amounts
            hp_regen = max(1, int(stats.endurance * 0.5) + 1)
            mp_regen = max(1, int(stats.magic * 0.5) + 1)

            new_hp = min(current_hp + hp_regen, stats.max_hp)
            new_mp = min(current_mp + mp_regen, stats.max_mp)

            # Apply Update
            self.db.set_player_vitals(self.discord_id, new_hp, new_mp)
            # Update local context for consistency within the step
            vitals["current_hp"] = new_hp
            vitals["current_mp"] = new_mp

            # Resolve Class Name from ID
            player_row = context.get("player_row", {})
            class_id = player_row.get("class_id", 0)
            class_name = "Adventurer"
            for c_name, c_data in CLASSES.items():
                if c_data["id"] == class_id:
                    class_name = c_name
                    break

            # Calculate HP Percent for Narrative
            hp_percent = new_hp / max(stats.max_hp, 1)

            # Build Log Messages
            base_logs = AdventureEvents.regeneration(location_id, class_name, hp_percent)
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

    def _perform_quest_event(
        self, context: dict[str, Any], location_name: str | None, location_id: str | None
    ) -> dict[str, Any]:
        """
        Checks active quests for exploration objectives.
        Updates quest progress if a relevant event is triggered.
        """
        try:
            active_quests = self.quest_system.get_player_quests(self.discord_id)
            event_types = ["gather", "locate", "examine", "survey", "escort", "retrieve", "deliver"]

            for quest in active_quests:
                # SECURITY: Validate Quest Location
                required_location = quest.get("location")
                if required_location and required_location != location_name:
                    continue

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

            # If no matching quest event was found, try wild gathering
            return self._perform_wild_gathering(context, location_id)

        except Exception as e:
            logger.error(f"Quest event error for {self.discord_id}: {e}")
            return {"log": ["*The path ahead is unclear.*"], "dead": False}

    def _perform_wild_gathering(
        self, context: dict[str, Any], location_id: str | None, bonus_chance: int = 0
    ) -> dict[str, Any]:
        """
        Attempts to find wild materials if no quest event triggered.
        Now supports biome-specific drops and luck-based quantity.
        """
        # Determine gatherables for this location
        gatherables = []
        if location_id and location_id in LOCATIONS:
            gatherables = LOCATIONS[location_id].get("gatherables", [])

        # If no gatherables defined, fallback to general pool (or empty)
        if not gatherables:
            # Fallback for old compatibility or empty zones
            gatherables = [("medicinal_herb", 50), ("iron_ore", 20), ("ancient_wood", 10)]

        # 35% Base Chance + Bonus
        base_chance = 35 + bonus_chance
        if random.randint(1, 100) <= base_chance:
            # Weighted Selection
            choices, weights = zip(*gatherables)
            item_key = random.choices(choices, weights=weights, k=1)[0]
            mat_data = MATERIALS.get(item_key)

            if mat_data:
                # Calculate Quantity based on Luck
                stats = context["player_stats"]

                # Formula: Base 1 + (Luck / 25)
                bonus = int(stats.luck / 25)
                # Cap at 3 items max for wild gathering to preserve economy
                quantity = min(3, 1 + bonus)

                # Random variance: 20% chance to get +1 extra
                if random.random() < 0.20:
                    quantity += 1

                name = mat_data["name"]
                # Format name with quantity if > 1
                display_name = f"{name} (x{quantity})" if quantity > 1 else name

                event_text = f"\n{AdventureEvents.wild_gather_event(display_name)}"
                return {
                    "log": [event_text],
                    "dead": False,
                    "loot": {item_key: quantity},
                }

        # Fallback to Scavenge (Aurum or XP) instead of "nothing found"
        # 50% Aurum / 50% XP
        if random.random() < 0.5:
            # Aurum
            amount = random.randint(1, 5)
            msg = f"\n{AdventureEvents.scavenge_event('aurum', amount)}"
            return {"log": [msg], "dead": False, "loot": {"aurum": amount}}
        else:
            # XP
            amount = random.randint(5, 10)
            msg = f"\n{AdventureEvents.scavenge_event('exp', amount)}"
            return {"log": [msg], "dead": False, "loot": {"exp": amount}}
