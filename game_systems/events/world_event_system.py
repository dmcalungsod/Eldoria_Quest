"""
world_event_system.py

Manages global world events like "The Blood Moon" or "Celestial Convergence".
These events apply global modifiers to combat, loot, and experience.
"""

import datetime
import logging
from typing import Any

from database.database_manager import DatabaseManager
from game_systems.core.world_time import WorldTime

logger = logging.getLogger("eldoria.events")


class WorldEventSystem:
    # Event Types
    BLOOD_MOON = "blood_moon"
    CELESTIAL_CONVERGENCE = "celestial_convergence"
    VOID_INCURSION = "void_incursion"
    HARVEST_FESTIVAL = "harvest_festival"
    ELEMENTAL_SURGE = "elemental_surge"
    MYSTIC_MERCHANT = "mystic_merchant"
    FROSTFALL_EXPEDITION = "frostfall_expedition"
    SPECTRAL_TIDE = "spectral_tide"
    ECHOES_OF_THE_DEEP = "echoes_of_the_deep"
    TIME_QUAKE = "time_quake"
    BUILDERS_BOON = "builders_boon"
    FUNGAL_BLOOM = "fungal_bloom"
    PERMAFROST_THAW = "permafrost_thaw"
    ABYSSAL_TIDE = "abyssal_tide"

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
        MYSTIC_MERCHANT: {
            "name": "The Mystic Merchant",
            "description": "A mysterious traveler has arrived, offering rare goods for those with coin.",
            "modifiers": {
                "loot_boost": 1.2,
            },
        },
        FROSTFALL_EXPEDITION: {
            "name": "The Frostfall Expedition",
            "description": "The Guild is sponsoring expeditions to the Frostfall Expanse. Danger is high, but the rewards are frozen in time.",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "frostfall_threat_reduction": 0.9,  # 10% reduction in damage taken in Frostfall
                "frostfall_loot_bonus": 1.5,  # 50% more loot from Frostfall
            },
        },
        SPECTRAL_TIDE: {
            "name": "The Spectral Tide",
            "description": "The veil thins. Spirits wander freely, and the night is full of terrors.",
            "modifiers": {
                "exp_boost": 1.2,
                "loot_boost": 1.1,
                "spectral_ambush_chance": 0.15,  # +15% ambush chance at night
                "night_danger_mod": 0.10,  # +10% combat chance at night
            },
        },
        ECHOES_OF_THE_DEEP: {
            "name": "Echoes of the Deep",
            "description": "The Wailing Chasm reverberates with ancient, lost power. Explorers report increased resilience and greater treasures in its depths.",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "wailing_chasm_threat_reduction": 0.9,  # 10% reduction in damage taken in Wailing Chasm
                "wailing_chasm_loot_bonus": 1.5,  # 50% more loot from Wailing Chasm
            },
        },
        BUILDERS_BOON: {
            "name": "The Builder's Boon",
            "description": "The Guild is preparing for a massive expansion! To encourage gathering, all building material yields are tripled, and exploration yields more Aurum.",
            "modifiers": {
                "builder_boost": 3.0,
                "aurum_boost": 1.5,
            },
        },
        TIME_QUAKE: {
            "name": "Time Quake",
            "description": "A Time Quake ripples through Eldoria. The Silent City of Ouros briefly awakens, its temporal anomalies stabilizing. Explorers report lessened danger and incredible treasures.",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "ouros_threat_reduction": 0.8,
                "ouros_loot_bonus": 2.0,
            },
        },
        FUNGAL_BLOOM: {
            "name": "The Fungal Bloom",
            "description": "Bioluminescent spores cascade through the subterranean depths. Toxin accumulation is slowed, and monstrous flora drop unprecedented bounties.",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "undergrove_threat_reduction": 0.8,
                "undergrove_loot_bonus": 2.0,
            },
        },
        PERMAFROST_THAW: {
            "name": "The Permafrost Thaw",
            "description": "A rare warming trend touches the frozen wastes. The biting cold lessens, revealing ancient relics long trapped beneath the ice.",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "frostmire_threat_reduction": 0.8,
                "frostmire_loot_bonus": 2.0,
            },
        },
        ABYSSAL_TIDE: {
            "name": "The Abyssal Tide",
            "description": "Unnatural currents pull treasures from the deep. The Sunken Grotto is less treacherous and overflowing with lost riches.",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "sunken_grotto_threat_reduction": 0.8,
                "sunken_grotto_loot_bonus": 2.0,
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
            if WorldTime.now() > end_time:
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

        start_time = WorldTime.now()
        end_time = start_time + datetime.timedelta(hours=duration_hours)

        self.db.set_active_world_event(
            event_type, start_time.isoformat(), end_time.isoformat()
        )
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
