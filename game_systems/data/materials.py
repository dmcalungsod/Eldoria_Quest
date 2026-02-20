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
    "boar_meat": {
        "name": "Raw Boar Meat",
        "description": "A slab of meat from a wild boar.",
        "rarity": "Common",
        "value": 15,
    },
    "boss_talon": {
        "name": "Forest Boss Talon",
        "description": "A massive talon from a guardian of the forest.",
        "rarity": "Rare",
        "value": 400,  # Up from 250
    },
    # --- Wild Gatherable Materials ---
    "medicinal_herb": {
        "name": "Medicinal Herb",
        "description": "A common herb with slight healing properties.",
        "rarity": "Common",
        "value": 5,
    },
    "iron_ore": {
        "name": "Iron Ore",
        "description": "A chunk of raw iron suitable for smelting.",
        "rarity": "Common",
        "value": 12,
    },
    "luminescent_crystal": {
        "name": "Luminescent Crystal",
        "description": "A crystal that glows with a cold inner light.",
        "rarity": "Uncommon",
        "value": 45,
    },
    "ancient_wood": {
        "name": "Ancient Wood",
        "description": "A dense piece of wood from an old tree.",
        "rarity": "Uncommon",
        "value": 25,
    },
    # --- RARE CRAFTING MATERIALS ---
    "shadow_essence": {
        "name": "Shadow Essence",
        "description": "A vial of swirling darkness gathered from spirits.",
        "rarity": "Rare",
        "value": 150,
    },
    "mithril_ore": {
        "name": "Mithril Ore",
        "description": "Lightweight, silvery ore prized by smiths.",
        "rarity": "Rare",
        "value": 120,
    },
    "ironwood_heart": {
        "name": "Ironwood Heart",
        "description": "The petrified heart of an Elder Treant.",
        "rarity": "Rare",
        "value": 200,
    },
    # --- EPIC CRAFTING MATERIALS ---
    "crystal_heart": {
        "name": "Crystal Heart",
        "description": "The pulsating core of a crystalline construct.",
        "rarity": "Epic",
        "value": 900,
    },
    "titan_shard": {
        "name": "Titan Shard",
        "description": "A fragment of metal so hard it feels impossible.",
        "rarity": "Epic",
        "value": 800,
    },
    "celestial_dust": {
        "name": "Celestial Dust",
        "description": "Glimmering dust that falls from the stars.",
        "rarity": "Epic",
        "value": 1000,
    },
}
