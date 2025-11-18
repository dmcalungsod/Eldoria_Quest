"""
materials.py

Defines all 'Material' type items found in Eldoria.
Includes Magic Stones (core currency exchange source) and Monster Drops.
"""

MATERIALS = {
    # --- Magic Stones (The core income source for Adventurers) ---
    "magic_stone_fragment": {
        "name": "Magic Stone Fragment",
        "description": "A tiny, impure shard of mana. Barely worth exchanging, but it's a start.",
        "rarity": "Common",
        "value": 2,
    },
    "magic_stone_small": {
        "name": "Magic Stone (Small)",
        "description": "A small, cloudy stone from a low-level monster. The Guild exchanges these in bulk.",
        "rarity": "Common",
        "value": 8,
    },
    "magic_stone_medium": {
        "name": "Magic Stone (Medium)",
        "description": "A decent-sized stone with a faint pulse. The standard for a novice adventurer.",
        "rarity": "Uncommon",
        "value": 30,
    },
    "magic_stone_large": {
        "name": "Magic Stone (Large)",
        "description": "A heavy, fist-sized stone that hums with power. A valuable find from a dangerous beast.",
        "rarity": "Rare",
        "value": 120,
    },
    "magic_stone_flawless": {
        "name": "Magic Stone (Flawless)",
        "description": "A brilliant, pure crystal of condensed mana. This drop alone could fund an expedition.",
        "rarity": "Epic",
        "value": 500,
    },
    # --- Forest Zone Drops ---
    "goblin_ear": {
        "name": "Goblin Ear",
        "description": "Proof of defeating a goblin. The Guild pays a small bounty for these.",
        "rarity": "Common",
        "value": 5,
    },
    "wolf_fang": {
        "name": "Wolf Fang",
        "description": "A sharp, unbroken fang from a forest wolf. Used in crafting.",
        "rarity": "Common",
        "value": 10,
    },
    "slime_gel": {
        "name": "Slime Gel",
        "description": "Sticky, caustic residue from a slime. A common alchemical ingredient.",
        "rarity": "Common",
        "value": 3,
    },
    "spider_silk": {
        "name": "Spider Silk",
        "description": "Strong, lightweight thread from a forest spider. Prized by armorers.",
        "rarity": "Uncommon",
        "value": 15,
    },
    "treant_branch": {
        "name": "Treant Branch",
        "description": "A branch from a Treant, still thrumming with faint life magic.",
        "rarity": "Uncommon",
        "value": 20,
    },
    "boar_tusk": {
        "name": "Corrupted Tusk",
        "description": "A tusk from a Ravaged Boar, dark veins of corruption running through it.",
        "rarity": "Uncommon",
        "value": 22,
    },
    "boss_talon": {
        "name": "Forest Boss Talon",
        "description": "A massive talon from a guardian of the forest. Proof of a great victory.",
        "rarity": "Rare",
        "value": 250,
    },
}
