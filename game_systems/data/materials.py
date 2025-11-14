"""
materials.py

Defines all 'Material' type items found in Eldoria.
Includes Magic Stones (core currency exchange source) and Monster Drops.

Structure:
{
    "unique_id": {
        "name": str,
        "description": str,
        "rarity": str,
        "value": int  # Sell value in Gold (Valis)
    }
}
"""

MATERIALS = {
    # --- Magic Stones (The core income source for Adventurers) ---
    "magic_stone_small": {
        "name": "Magic Stone (Small)",
        "description": "A small shard of crystallized mana found in weak monsters. The Guild exchanges these for coin.",
        "rarity": "Common",
        "value": 5
    },
    "magic_stone_medium": {
        "name": "Magic Stone (Medium)",
        "description": "A pulsing stone containing decent magical energy. Standard income for E-Rank adventurers.",
        "rarity": "Uncommon",
        "value": 25
    },
    "magic_stone_large": {
        "name": "Magic Stone (Large)",
        "description": "A heavy stone humming with power. Highly valued by the Guild.",
        "rarity": "Rare",
        "value": 100
    },

    # --- Forest Zone Drops ---
    "goblin_ear": {
        "name": "Goblin Ear",
        "description": "Proof of defeating a goblin. Basic guild bounty item.",
        "rarity": "Common",
        "value": 8
    },
    "wolf_fang": {
        "name": "Wolf Fang",
        "description": "Sharp fang from a forest wolf. Used for crafting simple weapons.",
        "rarity": "Common",
        "value": 12
    },
    "slime_gel": {
        "name": "Slime Gel",
        "description": "Sticky residue used in alchemy and adhesives.",
        "rarity": "Common",
        "value": 6
    },
    "spider_silk": {
        "name": "Spider Silk",
        "description": "Strong, lightweight thread from a forest spider.",
        "rarity": "Uncommon",
        "value": 15
    },
    "yggdrasil_branch": {
        "name": "Yggdrasil Branch",
        "description": "A rare twig from a holy tree, thrumming with life.",
        "rarity": "Rare",
        "value": 200
    }
}