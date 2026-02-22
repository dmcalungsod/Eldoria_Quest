"""
world_time.py

Defines the dynamic time-of-day system for Eldoria.
Used to influence monster spawns, event descriptions, and player immersion.
"""

import datetime
import random
import zlib
from enum import Enum
from zoneinfo import ZoneInfo


class TimePhase(Enum):
    DAWN = "Dawn"  # 05:00 - 07:59
    DAY = "Day"  # 08:00 - 17:59
    DUSK = "Dusk"  # 18:00 - 20:59
    NIGHT = "Night"  # 21:00 - 04:59


class Weather(Enum):
    CLEAR = "Clear"
    RAIN = "Rain"
    STORM = "Storm"
    FOG = "Fog"
    SNOW = "Snow"
    ASH = "Ash Storm"


LOCATION_WEATHER_WEIGHTS = {
    # Default: Mostly clear, some rain/fog/storm
    "default": [(Weather.CLEAR, 60), (Weather.RAIN, 20), (Weather.FOG, 10), (Weather.STORM, 10)],
    # Specific Locations
    "molten_caldera": [(Weather.CLEAR, 50), (Weather.ASH, 40), (Weather.STORM, 10)],  # Storm = Firestorm
    "shrouded_fen": [(Weather.FOG, 50), (Weather.RAIN, 30), (Weather.CLEAR, 20)],
    "deepgrove_roots": [(Weather.CLEAR, 70), (Weather.FOG, 30)],  # Underground/roots
    "crystal_caverns": [(Weather.CLEAR, 80), (Weather.FOG, 20)],  # Glimmering mist
}


class WorldTime:
    """
    Centralized time management for the game world.
    """

    @staticmethod
    def now() -> datetime.datetime:
        """
        Returns the current time in Philippine Standard Time (PST, UTC+8).
        The returned datetime is naive (no timezone info) to maintain compatibility
        with existing database records and logic, but reflects the time in Manila.
        """
        pst = ZoneInfo("Asia/Manila")
        return datetime.datetime.now(pst).replace(tzinfo=None)

    @staticmethod
    def get_current_phase() -> TimePhase:
        """Determines the current phase based on server time (UTC/Local)."""
        hour = WorldTime.now().hour

        if 5 <= hour < 8:
            return TimePhase.DAWN
        elif 8 <= hour < 18:
            return TimePhase.DAY
        elif 18 <= hour < 21:
            return TimePhase.DUSK
        else:
            return TimePhase.NIGHT

    @staticmethod
    def is_night() -> bool:
        """Helper to quickly check if it is night (dangerous)."""
        return WorldTime.get_current_phase() == TimePhase.NIGHT

    @staticmethod
    def get_phase_flavor() -> str:
        """Returns a descriptive string for the current time phase."""
        phase = WorldTime.get_current_phase()

        if phase == TimePhase.DAWN:
            return "🌅 **Dawn** - The first light breaks the darkness."
        elif phase == TimePhase.DAY:
            return "☀️ **Day** - The sun stands high."
        elif phase == TimePhase.DUSK:
            return "🌇 **Dusk** - Shadows lengthen as the sun sets."
        else:
            return "🌑 **Night** - Darkness consumes the path."

    @staticmethod
    def get_current_weather(location_id: str) -> Weather:
        """
        Deterministically calculates the weather for a given location and hour.
        Ensures all players see the same weather at the same time.
        """
        if not location_id:
            return Weather.CLEAR

        # Seed based on hour + location hash
        # Use Adler32 for a fast, consistent hash across runs (unlike Python's hash())
        hour = WorldTime.now().hour
        loc_hash = zlib.adler32(location_id.encode())
        seed = hour + loc_hash

        # Use a local random instance to avoid affecting global random state
        rng = random.Random(seed)

        weights = LOCATION_WEATHER_WEIGHTS.get(location_id, LOCATION_WEATHER_WEIGHTS["default"])
        choices, probabilities = zip(*weights)

        # Pick one based on weights
        return rng.choices(choices, weights=probabilities, k=1)[0]

    @staticmethod
    def get_weather_flavor(weather: Weather) -> str:
        """Returns flavor text for the weather."""
        if weather == Weather.RAIN:
            return "🌧️ **Rain** - A steady downpour soaks the land."
        elif weather == Weather.STORM:
            return "⛈️ **Storm** - Thunder rolls and lightning cracks overhead!"
        elif weather == Weather.FOG:
            return "🌫️ **Fog** - Thick mist obscures your vision."
        elif weather == Weather.SNOW:
            return "❄️ **Snow** - Cold flakes drift down from a grey sky."
        elif weather == Weather.ASH:
            return "🌋 **Ash Storm** - Hot ash falls like grey snow, choking the air."
        else:
            return "☀️ **Clear** - The sky is open and visibility is good."

    @staticmethod
    def get_weather_modifiers(weather: Weather) -> dict:
        """
        Returns combat modifiers for the given weather.
        Keys:
            - fire_dmg: Multiplier for fire damage (1.0 = normal, 0.8 = -20%)
            - ice_dmg: Multiplier for ice damage
            - lightning_dmg: Multiplier for lightning damage
            - accuracy_mult: Multiplier for physical accuracy (1.0 = normal)
            - dot_hp_percent: % Max HP damage per turn (0.02 = 2%)
            - dot_message: Message to display when dot is applied
        """
        modifiers = {}
        if weather == Weather.RAIN:
            modifiers = {
                "fire_dmg": 0.8,
                "lightning_dmg": 1.2,
                "flavor": "🌧️ The rain weakens fire but conducts lightning!",
            }
        elif weather == Weather.STORM:
            modifiers = {
                "fire_dmg": 0.7,
                "lightning_dmg": 1.3,
                "flavor": "⛈️ The storm rages! Lightning is amplified!",
            }
        elif weather == Weather.FOG:
            modifiers = {
                "accuracy_mult": 0.85,
                "flavor": "🌫️ Thick fog obscures vision (-15% Accuracy).",
            }
        elif weather == Weather.SNOW:
            modifiers = {
                "ice_dmg": 1.2,
                "fire_dmg": 0.9,
                "flavor": "❄️ The cold strengthens frost magic.",
            }
        elif weather == Weather.ASH:
            modifiers = {
                "dot_hp_percent": 0.02,
                "dot_message": "🌋 The choking ash burns your lungs!",
                "fire_dmg": 1.1,
                "flavor": "🌋 Hot ash fills the air.",
            }
        return modifiers
