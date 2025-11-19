"""
materials.py

Defines all 'Material' type items found in Eldoria.
REBALANCED: Sell values increased to improve economy flow.
"""

MATERIALS = {
    # --- Magic Stones (Core Income) ---
    "magic_stone_fragment": {
        "name": "Magic Stone Fragment",
        "description": "A tiny, impure shard of mana.",
        "rarity": "Common",
        "value": 5,  # Up from 2
    },
    "magic_stone_small": {
        "name": "Magic Stone (Small)",
        "description": "A small, cloudy stone from a low-level monster.",
        "rarity": "Common",
        "value": 15,  # Up from 8
    },
    "magic_stone_medium": {
        "name": "Magic Stone (Medium)",
        "description": "A decent-sized stone with a faint pulse.",
        "rarity": "Uncommon",
        "value": 50,  # Up from 30
    },
    "magic_stone_large": {
        "name": "Magic Stone (Large)",
        "description": "A heavy, fist-sized stone that hums with power.",
        "rarity": "Rare",
        "value": 180,  # Up from 120
    },
    "magic_stone_flawless": {
        "name": "Magic Stone (Flawless)",
        "description": "A brilliant, pure crystal of condensed mana.",
        "rarity": "Epic",
        "value": 750,  # Up from 500
    },
    # --- Forest Zone Drops ---
    "goblin_ear": {
        "name": "Goblin Ear",
        "description": "Proof of defeating a goblin.",
        "rarity": "Common",
        "value": 10,  # Up from 5
    },
    "wolf_fang": {
        "name": "Wolf Fang",
        "description": "A sharp, unbroken fang from a forest wolf.",
        "rarity": "Common",
        "value": 18,  # Up from 10
    },
    "slime_gel": {
        "name": "Slime Gel",
        "description": "Sticky, caustic residue from a slime.",
        "rarity": "Common",
        "value": 8,  # Up from 3
    },
    "spider_silk": {
        "name": "Spider Silk",
        "description": "Strong, lightweight thread from a forest spider.",
        "rarity": "Uncommon",
        "value": 25,  # Up from 15
    },
    "treant_branch": {
        "name": "Treant Branch",
        "description": "A branch from a Treant, still thrumming with faint life magic.",
        "rarity": "Uncommon",
        "value": 35,  # Up from 20
    },
    "boar_tusk": {
        "name": "Corrupted Tusk",
        "description": "A tusk from a Ravaged Boar.",
        "rarity": "Uncommon",
        "value": 40,  # Up from 22
    },
    "boss_talon": {
        "name": "Forest Boss Talon",
        "description": "A massive talon from a guardian of the forest.",
        "rarity": "Rare",
        "value": 400,  # Up from 250
    },
}
