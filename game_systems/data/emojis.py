"""
emojis.py

Centralized repository for all Discord emojis used in Eldoria Quest.
Exports constants for both custom (ID-based) and standard unicode emojis.
"""

# --- Custom Emojis (Update these IDs if you re-upload emojis) ---
# Format: <:name:id> or standard unicode
AURUM = "🪙"
GUILD_MERIT = "<:guild_prestige:1194437270363701338>"

# --- Standard Unicode Emojis ---

# UI Icons
EXP = "✨"
LEVEL_UP = "🌟"
VESTIGE = "🧬"
ITEM_BOX = "📦"
LOCKED = "🔒"
ERROR = "❌"
MEDAL = "🏅"
CHECK = "✅"
SUCCESS = CHECK
WARNING = "⚠️"
BACKPACK = "🎒"
SCROLL = "📜"
QUEST_SCROLL = "📜"  # Alias for SCROLL
MAP = "🗺️"
EXCHANGE = "🔄"
PLAYER = "👤"  # <-- FIX: Added the missing PLAYER icon for Adventurer Status
POTION = "🧪"

# Combat
COMBAT = "⚔️"
PLAYER_ATTACK = "🗡️"
MONSTER_ATTACK = "💥"
MONSTER_SKILL = "🔥"
FIRE = "🔥"
BUFF = "✨"  # Alias for EXP
VICTORY = "🏆"
DEFEAT = "💀"
DODGE = "💨"
DAMAGE = "🩸"

# Stats (Eldoria System)
STR = "💪"  # Strength
END = "🛡️"  # Endurance
DEX = "🏹"  # Dexterity
AGI = "⚡"  # Agility
MAG = "🔮"  # Magic
LCK = "🍀"  # Luck

# Legacy Mappings (Safety for old code referencing D&D terms)
CON = END
INT = MAG
WIS = "📖"
CHA = "🗣️"

# Resources
HP = "❤️"
MP = "💧"

# Misc World
FOREST = "🌲"
THICKET = "🍃"
CAVE = "🍄"
OCEAN = "🌊"
CRYSTAL = "💎"
VOLCANO = "🌋"
GEAR = "⚙️"
HERB = "🌿"
SWORDS = "⚔️"
SKULL = "💀"
TRAP = "🪤"
LOOT = "💰"

# Narrative / Class Specific
HEART = "💔"
SHIELD = "🛡️"
MANA = "✨"
DAGGER = "🗡️"
HEAL = "⚕️"
BOW = "🏹"

# --- ANSI Color Definitions ---
RARITY_COLORS = {
    "Common": "\u001b[0;37m",  # Grey/White
    "Uncommon": "\u001b[0;32m",  # Green
    "Rare": "\u001b[0;34m",  # Blue
    "Epic": "\u001b[0;35m",  # Purple
    "Legendary": "\u001b[0;33m",  # Yellow/Gold
    "Mythical": "\u001b[0;31m",  # Red
    "DEFAULT": "\u001b[0;37m",  # Default to grey
}
ANSI_RESET = "\u001b[0m"


def get_rarity_ansi(rarity_name: str, text: str) -> str:
    """Wraps text in ANSI color codes for a given rarity."""
    if not rarity_name:
        rarity_name = "DEFAULT"

    # Get the color, defaulting to DEFAULT if not found
    color = RARITY_COLORS.get(rarity_name.title(), RARITY_COLORS["DEFAULT"])

    # Return the formatted string
    return f"{color}{text}{ANSI_RESET}"
