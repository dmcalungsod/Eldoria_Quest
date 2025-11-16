"""
emojis.py

Centralized repository for all Discord emojis used in Eldoria Quest.
Exports constants for both custom (ID-based) and standard unicode emojis.
"""

# --- Custom Emojis (Update these IDs if you re-upload emojis) ---
# Format: <:name:id>
AURUM = "<:gold_coin:1194437266903404596>"
GUILD_MERIT = "<:guild_prestige:1194437270363701338>"
# VESTIGE = "<:vestige:1439461714541150310>" # No longer a custom emoji

# --- Standard Unicode Emojis ---

# UI Icons
EXP = "✨"
LEVEL_UP = "🌟"
# FIX: Vestige is now the standard DNA emoji
VESTIGE = "🧬" 
ITEM_BOX = "📦"
ERROR = "❌"
MEDAL = "🏅"
CHECK = "✅"
WARNING = "⚠️"
BACKPACK = "🎒"
SCROLL = "📜"
QUEST_SCROLL = "📜"  # Alias for SCROLL
MAP = "🗺️"
EXCHANGE = "🔄"

# Combat
COMBAT = "⚔️"
PLAYER_ATTACK = "🗡️"
MONSTER_ATTACK = "💥"
MONSTER_SKILL = "🔥"
BUFF = "✨"  # Alias for EXP
VICTORY = "🏆"
DEFEAT = "💀"

# Stats
STR = "💪"
DEX = "🏹"
CON = "🛡️"
INT = "🔮"
WIS = "📖"
CHA = "🗣️"
LCK = "🍀"

# Resources
HP = "❤️"
MP = "💧"

# Misc World
FOREST = "🌲"
THICKET = "🍃"
CAVE = "🍄"
HERB = "🌿"


# --- NEW: ANSI Color Definitions ---
# --- THIS IS THE FIX: Replaced " [0;37m" with "\u001b[0;37m" ---
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
# --- END OF FIX ---


def get_rarity_ansi(rarity_name: str, text: str) -> str:
    """Wraps text in ANSI color codes for a given rarity."""
    if not rarity_name:
        rarity_name = "DEFAULT"

    # Get the color, defaulting to DEFAULT if not found
    color = RARITY_COLORS.get(rarity_name.title(), RARITY_COLORS["DEFAULT"])

    # Return the formatted string
    return f"{color}{text}{ANSI_RESET}"


# --- END NEW ---