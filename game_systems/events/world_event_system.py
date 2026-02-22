"""
world_event_system.py

Manages global world events like "The Blood Moon" or "Celestial Convergence".
These events apply global modifiers to combat, loot, and experience.
"""

import datetime
import logging
from typing import Any

from database.database_manager import DatabaseManager

logger = logging.getLogger("eldoria.events")


class WorldEventSystem:
    # Event Types
    BLOOD_MOON = "blood_moon"
    CELESTIAL_CONVERGENCE = "celestial_convergence"
    VOID_INCURSION = "void_incursion"
    HARVEST_FESTIVAL = "harvest_festival"
    ELEMENTAL_SURGE = "elemental_surge"

    # Event Configurations
    EVENT_CONFIGS = {
        BLOOD_MOON: {
            "name": "The Blood Moon",
            "description": "The moon turns crimson, empowering monsters and revealing hidden treasures.",
            "modifiers": {
                "loot_boost": 1.5,
                "exp_boost": 1.2,
                "monster_buff": 1.2,  # 20% stats increase
            },
        },
        CELESTIAL_CONVERGENCE: {
            "name": "Celestial Convergence",
            "description": "The stars align, granting immense magical power and fortune.",
            "modifiers": {
                "loot_boost": 2.0,
                "exp_boost": 1.5,
                "monster_buff": 1.0,
            },
        },
        VOID_INCURSION: {
            "name": "Void Incursion",
            "description": "Reality thins. The Void seeps in. Danger is extreme.",
            "modifiers": {
                "loot_boost": 1.2,
                "exp_boost": 2.0,
                "monster_buff": 1.5,
            },
        },
        HARVEST_FESTIVAL: {
            "name": "Grand Harvest Festival",
            "description": "The fields are golden and nature's bounty overflows. Gathering yields are doubled!",
            "modifiers": {
                "loot_boost": 1.2,
                "exp_boost": 1.1,
                "monster_buff": 1.0,
                "gathering_boost": 2.0,
            },
        },
        ELEMENTAL_SURGE: {
            "name": "Elemental Surge",
            "description": "Elemental energies are unstable. Monsters are stronger but drop Elemental Motes.",
            "modifiers": {
                "loot_boost": 1.3,
                "exp_boost": 1.2,
                "monster_buff": 1.2,
            },
        },
    }

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_current_event(self) -> dict[str, Any] | None:
        """
        Returns the currently active event if it hasn't expired.
        Auto-expires events if the end time has passed.
        """
        event = self.db.get_active_world_event()
        if not event:
            return None

        # Check expiration
        try:
            end_time = datetime.datetime.fromisoformat(event["end_time"])
            if datetime.datetime.now() > end_time:
                self.end_current_event()
                return None
        except ValueError:
            logger.error(f"Invalid end_time format for event {event.get('type')}")
            self.end_current_event()
            return None

        # Inject config data
        config = self.EVENT_CONFIGS.get(event["type"], {})
        # Merge config into event dict (non-destructive to DB data)
        # We return a new dict to avoid modifying the DB result directly if it was cached (though find_one returns a new dict)
        full_event = event.copy()
        full_event.update(config)

        return full_event

    def start_event(self, event_type: str, duration_hours: int) -> bool:
        """Starts a new world event."""
        if event_type not in self.EVENT_CONFIGS:
            logger.warning(f"Attempted to start unknown event: {event_type}")
            return False

        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(hours=duration_hours)

        self.db.set_active_world_event(event_type, start_time.isoformat(), end_time.isoformat())
        logger.info(f"Started World Event: {event_type} for {duration_hours}h")
        return True

    def end_current_event(self):
        """Ends the current event."""
        self.db.end_active_world_event()
        logger.info("Ended active World Event.")

    def get_modifiers(self) -> dict[str, float]:
        """Returns the active modifiers dict."""
        event = self.get_current_event()
        if not event:
            return {}

        return event.get("modifiers", {})
