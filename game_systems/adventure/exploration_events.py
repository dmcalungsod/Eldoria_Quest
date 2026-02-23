"""
exploration_events.py

Handles logic for special exploration events:
- Safe Rooms (Healing)
- Hidden Stashes (Loot)
- Ancient Shrines (XP)
- Traps (Damage)
"""

import logging
import random
from typing import Any

import game_systems.data.emojis as E
from game_systems.data.materials import MATERIALS
from game_systems.world_time import Weather, TimePhase

from .adventure_events import AdventureEvents

logger = logging.getLogger("eldoria.exploration")


class ExplorationEvents:
    def __init__(self, db: Any):
        self.db = db

    def handle_event(
        self,
        event_key: str,
        context: dict[str, Any],
        location_id: str | None = None,
        time_phase: TimePhase | None = None,
        weather: Weather | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        """
        Dispatches to specific event handlers based on key.
        """
        try:
            if event_key == "safe_room":
                return self._handle_safe_room(
                    context, location_id, time_phase, weather, event_type
                )
            elif event_key == "hidden_stash":
                return self._handle_hidden_stash(
                    context, location_id, time_phase, weather, event_type
                )
            elif event_key == "ancient_shrine":
                return self._handle_ancient_shrine(
                    context, location_id, time_phase, weather, event_type
                )
            elif event_key == "trap_pit":
                return self._handle_trap(
                    context, location_id, time_phase, weather, event_type
                )

            # Fallback
            return {"log": [], "vitals": context["vitals"], "loot": {}, "dead": False}

        except Exception as e:
            logger.error(f"Error handling event {event_key}: {e}", exc_info=True)
            return {
                "log": ["*Something shifts in the darkness, but nothing happens.*"],
                "vitals": context["vitals"],
                "loot": {},
                "dead": False,
            }

    def _handle_safe_room(
        self,
        context: dict[str, Any],
        location_id: str | None,
        time_phase: TimePhase | None,
        weather: Weather | None,
        event_type: str | None,
    ) -> dict[str, Any]:
        stats = context["player_stats"]
        vitals = context["vitals"]

        # Heal 50-100% of Max HP/MP
        heal_percent = random.uniform(0.5, 1.0)

        new_hp = min(
            stats.max_hp, int(vitals["current_hp"] + stats.max_hp * heal_percent)
        )
        new_mp = min(
            stats.max_mp, int(vitals["current_mp"] + stats.max_mp * heal_percent)
        )

        hp_gain = new_hp - vitals["current_hp"]
        mp_gain = new_mp - vitals["current_mp"]

        # Update DB
        self.db.set_player_vitals(context["player_row"]["discord_id"], new_hp, new_mp)

        # Update Context
        vitals["current_hp"] = new_hp
        vitals["current_mp"] = new_mp

        log = [
            AdventureEvents.special_event_flavor(
                "safe_room", location_id, time_phase, weather, event_type
            ),
            f"{E.HEAL} Restored **{hp_gain}** HP and **{mp_gain}** MP.",
        ]

        return {"log": log, "vitals": vitals, "loot": {}, "dead": False}

    def _handle_hidden_stash(
        self,
        context: dict[str, Any],
        location_id: str | None,
        time_phase: TimePhase | None,
        weather: Weather | None,
        event_type: str | None,
    ) -> dict[str, Any]:
        # Aurum or Material
        loot = {}
        log = [
            AdventureEvents.special_event_flavor(
                "hidden_stash", location_id, time_phase, weather, event_type
            )
        ]

        if random.random() < 0.6:
            # Aurum
            amount = random.randint(50, 200)
            loot["aurum"] = amount
            log.append(f"{E.AURUM} Found **{amount} Aurum**.")
        else:
            # Material - Pick a Rare material
            rare_mats = [k for k, v in MATERIALS.items() if v.get("rarity") == "Rare"]
            if rare_mats:
                item_key = random.choice(rare_mats)
                mat_name = MATERIALS[item_key]["name"]
                loot[item_key] = 1
                log.append(f"{E.LOOT} Found **{mat_name}**!")

        return {"log": log, "vitals": context["vitals"], "loot": loot, "dead": False}

    def _handle_ancient_shrine(
        self,
        context: dict[str, Any],
        location_id: str | None,
        time_phase: TimePhase | None,
        weather: Weather | None,
        event_type: str | None,
    ) -> dict[str, Any]:
        # Grant XP
        amount = random.randint(100, 300)
        loot = {"exp": amount}

        log = [
            AdventureEvents.special_event_flavor(
                "ancient_shrine", location_id, time_phase, weather, event_type
            ),
            f"{E.EXP} You gain **{amount} XP** from the ancient knowledge.",
        ]

        return {"log": log, "vitals": context["vitals"], "loot": loot, "dead": False}

    def _handle_trap(
        self,
        context: dict[str, Any],
        location_id: str | None,
        time_phase: TimePhase | None,
        weather: Weather | None,
        event_type: str | None,
    ) -> dict[str, Any]:
        stats = context["player_stats"]
        vitals = context["vitals"]

        # Damage 10-25% of Max HP
        damage_percent = random.uniform(0.10, 0.25)
        damage = int(stats.max_hp * damage_percent)
        damage = max(1, damage)

        # Check Agility for mitigation
        # Chance to dodge half damage: 1% per 2 Agility
        dodge_chance = min(50, context["player_stats"].agility // 2)
        mitigated = False
        if random.randint(1, 100) <= dodge_chance:
            damage = damage // 2
            mitigated = True

        current_hp = vitals["current_hp"]
        new_hp = max(0, current_hp - damage)

        # Update DB
        self.db.set_player_vitals(
            context["player_row"]["discord_id"], new_hp, vitals["current_mp"]
        )

        vitals["current_hp"] = new_hp

        flavor = AdventureEvents.special_event_flavor(
            "trap_pit", location_id, time_phase, weather, event_type
        )
        if mitigated:
            flavor += f"\n{E.DODGE} You reacted quickly, reducing the impact!"

        log = [flavor, f"{E.DAMAGE} You took **{damage}** damage."]

        dead = new_hp <= 0

        return {"log": log, "vitals": vitals, "loot": {}, "dead": dead}
