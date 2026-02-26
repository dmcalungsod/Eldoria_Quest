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
    BLIZZARD = "Blizzard"
    SANDSTORM = "Sandstorm"
    GALE = "Gale"
    MIASMA = "Toxic Miasma"


LOCATION_WEATHER_WEIGHTS = {
    # Default: Mostly clear, some rain/fog/storm
    "default": [
        (Weather.CLEAR, 60),
        (Weather.RAIN, 20),
        (Weather.FOG, 10),
        (Weather.STORM, 10),
    ],
    # Specific Locations
    "molten_caldera": [
        (Weather.CLEAR, 50),
        (Weather.ASH, 40),
        (Weather.STORM, 10),
    ],  # Storm = Firestorm
    "the_ashlands": [
        (Weather.ASH, 60),
        (Weather.CLEAR, 30),
        (Weather.STORM, 10),
    ],
    "shrouded_fen": [(Weather.FOG, 50), (Weather.RAIN, 30), (Weather.CLEAR, 20)],
    "deepgrove_roots": [(Weather.MIASMA, 40), (Weather.FOG, 30), (Weather.CLEAR, 30)],  # Underground/roots
    "forgotten_ossuary": [(Weather.MIASMA, 50), (Weather.FOG, 30), (Weather.CLEAR, 20)],
    "crystal_caverns": [(Weather.CLEAR, 80), (Weather.FOG, 20)],  # Glimmering mist
    "frostfall_expanse": [
        (Weather.SNOW, 40),
        (Weather.BLIZZARD, 30),
        (Weather.CLEAR, 20),
        (Weather.FOG, 10),
    ],
    "shimmering_wastes": [
        (Weather.CLEAR, 50),
        (Weather.SANDSTORM, 40),
        (Weather.GALE, 10),
    ],
    "gale_scarred_heights": [
        (Weather.GALE, 50),
        (Weather.STORM, 30),
        (Weather.CLEAR, 20),
    ],
    "void_sanctum": [
        (Weather.MIASMA, 60),
        (Weather.FOG, 20),
        (Weather.STORM, 20),
    ],
    "sunken_grotto": [
        (Weather.FOG, 40),
        (Weather.RAIN, 30),
        (Weather.CLEAR, 30),
    ],
    "clockwork_halls": [
        (Weather.CLEAR, 70),
        (Weather.FOG, 30),  # Steam
    ],
    "celestial_archipelago": [
        (Weather.CLEAR, 50),
        (Weather.GALE, 30),
        (Weather.STORM, 20),
    ],
    "whispering_thicket": [
        (Weather.CLEAR, 40),
        (Weather.RAIN, 30),
        (Weather.FOG, 30),
    ],
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
        rng = random.Random(seed)  # nosec B311

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
        elif weather == Weather.BLIZZARD:
            return "🌨️ **Blizzard** - A whiteout of snow and ice whips around you!"
        elif weather == Weather.SANDSTORM:
            return "🌪️ **Sandstorm** - Gritting sand scours your skin and clouds your eyes."
        elif weather == Weather.GALE:
            return "💨 **Gale** - Powerful winds threaten to knock you off your feet."
        elif weather == Weather.MIASMA:
            return "☠️ **Miasma** - Toxic fumes rise from the ground, burning your lungs."
        else:
            return "☀️ **Clear** - The sky is open and visibility is good."
