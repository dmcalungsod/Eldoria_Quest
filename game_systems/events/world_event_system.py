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

    # Event Configurations
    EVENT_CONFIGS = {
        BLOOD_MOON: {
            "name": "The Blood Moon",
            "description": "A crimson stain spreads across the night sky. The beasts of the wild grow frenzied, and long-lost treasures glint in the red light.",
            "announcement": "🚨 **THE BLOOD MOON RISES!** 🚨\n\nThe sky bleeds as a crimson light washes over the realm. Monsters grow frenzied with newfound power, but the red hue also catches the glint of long-lost treasures. Draw your steel, adventurers—tonight we hunt or are hunted.\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 1.5,
                "exp_boost": 1.2,
                "monster_buff": 1.2,  # 20% stats increase
            },
        },
        CELESTIAL_CONVERGENCE: {
            "name": "Celestial Convergence",
            "description": "The heavens align in a breathtaking display of cosmic power. Magic flows freely, and fortune smiles upon the bold.",
            "announcement": "✨ **A CELESTIAL CONVERGENCE BEGINS!** ✨\n\nThe stars align in perfect harmony, bathing the land in an ethereal glow. Magical energies surge through the leylines, granting immense power and unimaginable fortune to those brave enough to claim it.\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 2.0,
                "exp_boost": 1.5,
                "monster_buff": 1.0,
            },
        },
        VOID_INCURSION: {
            "name": "Void Incursion",
            "description": "The fabric of reality tears. The whispering abyss bleeds into our world, bringing unimaginable horrors and dark rewards.",
            "announcement": "🌌 **VOID INCURSION DETECTED!** 🌌\n\nReality thins. The whispering abyss of the Void seeps into our world, bringing unimaginable horrors. The danger is extreme, but the experience gained from defeating these otherworldly anomalies is unparalleled. Stand fast, Guild members!\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 1.2,
                "exp_boost": 2.0,
                "monster_buff": 1.5,
            },
        },
        HARVEST_FESTIVAL: {
            "name": "Grand Harvest Festival",
            "description": "A crisp autumn breeze carries the scent of ripe crops and festive cheer. The land offers its bounty freely.",
            "announcement": "🍂 **SEASONAL EVENT STARTED!** 🍂\n\n**The Grand Harvest Festival** has arrived! The fields are golden, the weather is crisp, and nature's bounty overflows. Gatherers, take heart—your yields will be doubled for the duration of the festival! 🌾\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 1.2,
                "exp_boost": 1.1,
                "monster_buff": 1.0,
                "gathering_boost": 2.0,
            },
        },
        ELEMENTAL_SURGE: {
            "name": "Elemental Surge",
            "description": "The very earth trembles and the winds howl as primal elemental forces run rampant across the wild.",
            "announcement": "🌪️ **AN ELEMENTAL SURGE IS UPON US!** 🔥\n\nThe primal forces of the world have grown unstable. Fire burns hotter, winds cut deeper, and the earth trembles beneath our feet. Monsters empowered by this energy are far deadlier, but they may yield precious Elemental Motes upon defeat.\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 1.3,
                "exp_boost": 1.2,
                "monster_buff": 1.2,
            },
        },
        MYSTIC_MERCHANT: {
            "name": "The Mystic Merchant",
            "description": "A cloaked traveler emerges from the mists, offering strange and wondrous goods to those with the coin to spare.",
            "announcement": "🔮 **THE MYSTIC MERCHANT ARRIVES!** 🔮\n\nA mysterious, cloaked traveler has been spotted on the outskirts of Astraeon. They offer rare and wondrous goods, but their patience is short and their prices steep. Visit the **Guild Services** menu to find them before they vanish back into the mists! 🪙\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 1.2,
            },
        },
        FROSTFALL_EXPEDITION: {
            "name": "The Frostfall Expedition",
            "description": "The Guild calls for brave souls to chart the unforgiving Frostfall Expanse. The cold is deadly, but the ancient spoils are vast.",
            "announcement": "❄️ **THE FROSTFALL EXPEDITION HAS BEGUN!** ❄️\n\nAttention, Pathfinders and mercenaries! The Guild is officially sponsoring expeditions into the treacherous **Frostfall Expanse**. The Guild has provided specialized rations and intelligence, reducing the lethal threat of the region's denizens.\n\nFurthermore, merchants are paying a premium for glacial relics—expect a massive 50% increase in loot drops from the frozen wastes, alongside global boosts to morale and spoils!\n\nBundle up. The cold bites, but the glory is forever.\n\nCheck `/event_status` for details!",
            "modifiers": {
                "loot_boost": 1.25,
                "exp_boost": 1.1,
                "frostfall_threat_reduction": 0.9,  # 10% reduction in damage taken in Frostfall
                "frostfall_loot_bonus": 1.5,  # 50% more loot from Frostfall
            },
        },
        SPECTRAL_TIDE: {
            "name": "The Spectral Tide",
            "description": "A chilling mist rolls in as the veil between the living and the dead grows terrifyingly thin. Spirits walk among us.",
            "announcement": "👻 **THE SPECTRAL TIDE ROLLS IN!** 👻\n\nA bone-chilling mist pours across the land. The veil has torn. Restless spirits and phantoms now wander freely through the dark, waiting to ambush the unwary. The night is full of terrors, but those who brave the dark may find ectoplasmic remnants of immense value.\n\nKeep your torches lit, and watch your shadows.\n\nCheck `/event_status` for details!",
            "modifiers": {
                "exp_boost": 1.2,
                "loot_boost": 1.1,
                "spectral_ambush_chance": 0.15,  # +15% ambush chance at night
                "night_danger_mod": 0.10,  # +10% combat chance at night
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
