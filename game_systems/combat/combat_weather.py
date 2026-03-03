"""
combat_weather.py

Weather-related helpers for the combat engine.
Extracted from CombatEngine to reduce cyclomatic complexity.
"""

import random

from game_systems.core.world_time import Weather


def handle_weather_events(
    weather: Weather,
    player_hp: int,
    monster_hp: int,
    player_max_hp: int,
    monster_max_hp: int,
    monster_name: str,
    log: list,
) -> tuple[int, int]:
    """
    Processes start-of-turn weather damage events.
    Returns (updated_player_hp, updated_monster_hp).
    """
    if weather == Weather.STORM:
        # 15% chance for random lightning strike
        if random.random() < 0.15:  # nosec B311
            target_is_player = random.choice([True, False])  # nosec B311
            if target_is_player:
                dmg = max(10, int(player_max_hp * 0.05))
                player_hp = max(0, player_hp - dmg)
                log.append(f"⚡ **STORM:** A lightning bolt strikes YOU for `{dmg}` damage!")
            else:
                dmg = max(10, int(monster_max_hp * 0.05))
                monster_hp = max(0, monster_hp - dmg)
                log.append(f"⚡ **STORM:** A lightning bolt strikes the **{monster_name}** for `{dmg}` damage!")

    elif weather == Weather.ASH:
        # Ash Storm: 2% Max HP damage to Player (Choking Ash)
        dmg = max(1, int(player_max_hp * 0.02))
        player_hp = max(0, player_hp - dmg)
        log.append(f"🌋 **ASH:** The choking ash burns your lungs! (`{dmg}` dmg)")

    elif weather == Weather.BLIZZARD:
        # 20% chance for Frostbite (3% Max HP)
        if random.random() < 0.20:  # nosec B311
            dmg = max(1, int(player_max_hp * 0.03))
            player_hp = max(0, player_hp - dmg)
            log.append(f"❄️ **BLIZZARD:** The biting cold freezes your marrow! (`{dmg}` dmg)")

    elif weather == Weather.SANDSTORM:
        # 20% chance for Buffeting Sands (3% Max HP)
        if random.random() < 0.20:  # nosec B311
            dmg = max(1, int(player_max_hp * 0.03))
            player_hp = max(0, player_hp - dmg)
            log.append(f"🌪️ **SANDSTORM:** The abrasive sand flays your skin! (`{dmg}` dmg)")

    elif weather == Weather.MIASMA:
        # 25% chance for Toxic Fumes (2% Max HP)
        if random.random() < 0.25:  # nosec B311
            dmg = max(1, int(player_max_hp * 0.02))
            player_hp = max(0, player_hp - dmg)
            log.append(f"☠️ **MIASMA:** You inhale the toxic fumes! (`{dmg}` dmg)")

    return player_hp, monster_hp


def apply_weather_modifiers(dmg: int, element: str, weather: Weather) -> int:
    """
    Returns damage after applying weather-based elemental multipliers.
    """
    if weather == Weather.RAIN:
        if element == "fire":
            return int(dmg * 0.8)
        if element == "lightning":
            return int(dmg * 1.2)

    elif weather == Weather.FOG:
        return int(dmg * 0.9)

    elif weather == Weather.SNOW:
        if element == "ice":
            return int(dmg * 1.2)
        if element == "fire":
            return int(dmg * 0.9)

    elif weather == Weather.ASH:
        if element == "fire":
            return int(dmg * 1.1)

    elif weather == Weather.BLIZZARD:
        if element == "ice":
            return int(dmg * 1.2)
        if element == "fire":
            return int(dmg * 0.8)

    elif weather == Weather.SANDSTORM:
        if element == "earth":
            return int(dmg * 1.1)
        if element == "wind":
            return int(dmg * 1.2)

    elif weather == Weather.GALE:
        if element == "wind":
            return int(dmg * 1.3)

    elif weather == Weather.MIASMA:
        if element in ["poison", "dark"]:
            return int(dmg * 1.2)
        if element in ["holy", "light"]:
            return int(dmg * 0.8)

    return dmg


def detect_element(skill: dict) -> str:
    """Determines the elemental type of a skill."""
    if not skill:
        return "physical"

    s_type = skill.get("type", "").lower()
    if s_type in ["fire", "ice", "lightning", "water", "wind", "earth", "dark", "holy"]:
        return s_type

    name = skill.get("name", "").lower()
    emoji = skill.get("emoji", "")

    if "fire" in name or "flame" in name or "burn" in name or emoji == "🔥":
        return "fire"
    if "ice" in name or "frost" in name or "freeze" in name or emoji == "❄️":
        return "ice"
    if "lightning" in name or "thunder" in name or "shock" in name or emoji == "⚡":
        return "lightning"
    if "water" in name or "hydro" in name or emoji == "💧":
        return "water"
    if "wind" in name or "gale" in name or emoji == "🌬️":
        return "wind"
    if "earth" in name or "rock" in name or emoji == "🪨":
        return "earth"
    if "dark" in name or "shadow" in name or emoji == "🌑":
        return "dark"
    if "holy" in name or "light" in name or emoji == "✨":
        return "holy"

    return "physical"
