"""
world_time.py

Defines the dynamic time-of-day system for Eldoria.
Used to influence monster spawns, event descriptions, and player immersion.
"""

import datetime
from enum import Enum


class TimePhase(Enum):
    DAWN = "Dawn"    # 05:00 - 07:59
    DAY = "Day"      # 08:00 - 17:59
    DUSK = "Dusk"    # 18:00 - 20:59
    NIGHT = "Night"  # 21:00 - 04:59


class WorldTime:
    """
    Centralized time management for the game world.
    """

    @staticmethod
    def get_current_phase() -> TimePhase:
        """Determines the current phase based on server time (UTC/Local)."""
        hour = datetime.datetime.now().hour

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
