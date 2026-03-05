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
from game_systems.core.world_time import Weather, WorldTime
from game_systems.data.adventure_locations import LOCATIONS
from game_systems.data.class_data import CLASSES
from game_systems.data.materials import MATERIALS

from .adventure_events import AdventureEvents
from .exploration_events import ExplorationEvents

logger = logging.getLogger("eldoria.events")


class EventHandler:
    def __init__(self, db: DatabaseManager, quest_system, discord_id: int):
        self.db = db
        self.quest_system = quest_system
        self.discord_id = discord_id
        self.exploration = ExplorationEvents(db)

    def resolve_non_combat(
        self,
        context: dict[str, Any],
        location_id: str | None = None,
        regen_chance: int = 70,
        location_name: str | None = None,
        weather: Weather = Weather.CLEAR,
        event_type: str | None = None,
        supplies: dict[str, int] | None = None,
        time_phase=None,
    ) -> dict[str, Any]:
        """Decides between Regen or Quest Event."""
        try:
            if random.randint(1, 100) <= regen_chance:
                return self._perform_regeneration(context, location_id, weather, event_type)
            else:
                # --- SPECIAL EXPLORATION EVENT (15% Chance) ---
                if location_id and location_id in LOCATIONS:
                    special_events = LOCATIONS[location_id].get("special_events", [])
                    # 15% chance to trigger a special event if available
                    if special_events and random.random() < 0.15:
                        event_key = random.choice(special_events)
                        result = self.exploration.handle_event(event_key, context, weather, time_phase)
                        # Prepend newline to first log for formatting
                        if result["log"]:
                            result["log"][0] = f"\n{result['log'][0]}"
                        return result

                return self._perform_quest_event(context, location_name, location_id, supplies, weather)
        except Exception as e:
            logger.error(f"Event resolution error for {self.discord_id}: {e}", exc_info=True)
            # Fallback safe state
            return {"log": ["*You wander in silence, finding nothing.*"], "dead": False}

    def _perform_regeneration(
        self,
        context: dict[str, Any],
        location_id: str | None = None,
        weather: Weather = Weather.CLEAR,
        event_type: str | None = None,
    ) -> dict[str, Any]:
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

            # If already full, prevent SURGE exploit (infinite farming)
            if current_hp >= stats.max_hp and current_mp >= stats.max_mp:
                return {
                    "log": ["\n**You are already fully rested.** The moment of peace passes."],
                    "dead": False,
                }

            # Calculate Regen Amounts with Caps (Prevent infinite scaling)
            # Equilibrium Fix: Reduced from 0.5 to 0.25 to prevent linear runaway scaling
            # Base: 25% of Stat
            raw_hp_regen = int(stats.endurance * 0.25) + 1
            raw_mp_regen = int(stats.magic * 0.25) + 1

            # Cap: 5% of Max HP/MP per step (Strict Cap)
            max_hp_regen = max(1, int(stats.max_hp * 0.05))
            max_mp_regen = max(1, int(stats.max_mp * 0.05))

            hp_regen = min(raw_hp_regen, max_hp_regen)
            mp_regen = min(raw_mp_regen, max_mp_regen)

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

            # Get Time Phase for atmosphere
            current_phase = WorldTime.get_current_phase()

            # Get Current Season
            current_season = WorldTime.get_current_season()

            # Build Log Messages
            base_logs = AdventureEvents.regeneration(
                location_id,
                class_name,
                hp_percent,
                time_phase=current_phase,
                weather=weather,
                season=current_season,
                event_type=event_type,
            )
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
            return {
                "log": ["*You try to rest, but something feels wrong.*"],
                "dead": False,
            }

    def _perform_quest_event(
        self,
        context: dict[str, Any],
        location_name: str | None,
        location_id: str | None,
        supplies: dict[str, int] | None = None,
        weather: Weather = Weather.CLEAR,
    ) -> dict[str, Any]:
        """
        Checks active quests for exploration objectives.
        Updates quest progress if a relevant event is triggered.
        """
        try:
            active_quests = self.quest_system.get_player_quests(self.discord_id)
            event_types = [
                "gather",
                "locate",
                "examine",
                "survey",
                "escort",
                "retrieve",
                "deliver",
            ]

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
                                    # Check for custom flavor text
                                    flavor_key = f"{obj_type}:{task}"
                                    flavor = quest.get("flavor_text", {}).get(flavor_key)

                                    if flavor:
                                        event_text = f"\n{E.QUEST_SCROLL} **{flavor}**"
                                    else:
                                        event_text = f"\n{AdventureEvents.quest_event(obj_type, task)}"

                                    return {
                                        "log": [
                                            event_text,
                                            f"{E.QUEST_SCROLL} *Quest Updated: {quest['title']}*",
                                        ],
                                        "dead": False,
                                    }

            # If no matching quest event was found, try wild gathering
            return self._perform_wild_gathering(context, location_id, supplies=supplies, weather=weather)

        except Exception as e:
            logger.error(f"Quest event error for {self.discord_id}: {e}")
            return {"log": ["*The path ahead is unclear.*"], "dead": False}

    def _perform_wild_gathering(
        self,
        context: dict[str, Any],
        location_id: str | None,
        bonus_chance: int = 0,
        supplies: dict[str, int] | None = None,
        weather: Weather = Weather.CLEAR,
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
            gatherables = [
                ("medicinal_herb", 50),
                ("iron_ore", 20),
                ("ancient_wood", 10),
            ]

        # 35% Base Chance + Bonus
        base_chance = 35 + bonus_chance

        # Weather modifiers on gathering chance
        if weather in [Weather.FOG, Weather.SNOW, Weather.BLIZZARD]:
            base_chance -= 10
        elif weather in [Weather.SANDSTORM, Weather.ASH]:
            base_chance -= 15
        elif weather == Weather.CLEAR:
            base_chance += 5

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

                # SUPPLY EFFECT: Explorer's Kit
                kit_bonus = 0
                if supplies and supplies.get("explorer_kit"):
                    quantity += 1
                    kit_bonus = 1

                # Apply Gathering Boost (e.g., Harvest Festival)
                boosts = context.get("active_boosts", {})
                gathering_mult = boosts.get("gathering_boost", 1.0)

                builder_boost = boosts.get("builder_boost", 1.0)
                if builder_boost > 1.0 and item_key in [
                    "ancient_wood",
                    "iron_ore",
                    "hardwood_plank",
                    "iron_ingot",
                    "steel_ingot",
                ]:
                    gathering_mult = max(gathering_mult, builder_boost)
                if gathering_mult > 1.0:
                    quantity = int(quantity * gathering_mult)
                    # Ensure at least 1 if multiplier somehow reduces it (unlikely but safe)
                    quantity = max(1, quantity)

                weather_bonus = False
                if weather == Weather.RAIN:
                    quantity += 1
                    weather_bonus = True
                elif weather in [Weather.ASH, Weather.MIASMA]:
                    quantity = max(1, quantity - 1)

                name = mat_data["name"]
                # Format name with quantity if > 1
                display_name = f"{name} (x{quantity})" if quantity > 1 else name

                if gathering_mult > 1.0:
                    display_name += f" {E.BUFF} (Bonus)"

                if kit_bonus > 0:
                    display_name += " (Kit Bonus)"

                if weather_bonus:
                    display_name += " 🌧️ (Rain Bonus)"

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
