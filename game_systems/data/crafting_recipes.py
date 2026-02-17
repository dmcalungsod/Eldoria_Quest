"""
crafting_recipes.py

Defines equipment crafting recipes for the Alchemist's Workbench.
Maps materials to equipment outputs (found in EQUIPMENT_DATA).
"""

EQUIPMENT_RECIPES = {
    "craft_rusted_sword": {
        "id": "craft_rusted_sword",
        "name": "Rusted Shortsword",  # Must match EQUIPMENT_DATA name exactly for lookup
        "output_key": "gen_sword_001",
        "type": "equipment",
        "rarity": "Common",
        "materials": {"iron_ore": 3, "wolf_fang": 1},
        "cost": 50,
        "description": "Forge a basic iron blade from ore and fangs.",
    },
    "craft_gnarled_branch": {
        "id": "craft_gnarled_branch",
        "name": "Gnarled Branch",
        "output_key": "gen_staff_001",
        "type": "equipment",
        "rarity": "Common",
        "materials": {"magic_stone_fragment": 3, "slime_gel": 1},
        "cost": 40,
        "description": "Bind magic fragments to a sturdy branch.",
    },
    "craft_leather_vest": {
        "id": "craft_leather_vest",
        "name": "Worn Leather Vest",
        "output_key": "gen_rogue_armor_001",
        "type": "equipment",
        "rarity": "Common",
        "materials": {"wolf_fang": 2, "goblin_ear": 2},
        "cost": 40,
        "description": "Stitch together a simple vest from beast hides.",
    },
    "craft_tattered_tunic": {
        "id": "craft_tattered_tunic",
        "name": "Tattered Tunic",
        "output_key": "gen_armor_001",
        "type": "equipment",
        "rarity": "Common",
        "materials": {"spider_silk": 1, "goblin_ear": 2},
        "cost": 35,
        "description": "Weave a basic tunic for protection.",
    },
    # --- UNCOMMON (Tier 2) ---
    "craft_iron_dirk": {
        "id": "craft_iron_dirk",
        "name": "Iron Dirk",
        "output_key": "gen_dagger_003",
        "type": "equipment",
        "rarity": "Uncommon",
        "materials": {"iron_ore": 3, "wolf_fang": 2},
        "cost": 100,
        "description": "A sharp, reliable dagger forged from iron.",
    },
    "craft_acolyte_robe": {
        "id": "craft_acolyte_robe",
        "name": "Acolyte's Robe",
        "output_key": "gen_robe_003",
        "type": "equipment",
        "rarity": "Uncommon",
        "materials": {"spider_silk": 3, "magic_stone_small": 2},
        "cost": 120,
        "description": "A robe imbued with faint magical energy.",
    },
    "craft_iron_cuirass": {
        "id": "craft_iron_cuirass",
        "name": "Iron Cuirass",
        "output_key": "gen_heavyarmor_003",
        "type": "equipment",
        "rarity": "Uncommon",
        "materials": {"iron_ore": 5, "treant_branch": 1},
        "cost": 150,
        "description": "Sturdy iron plate reinforced with ancient wood.",
    },
    "craft_polished_stone": {
        "id": "craft_polished_stone",
        "name": "Polished Stone",
        "output_key": "gen_accessory_003c",
        "type": "equipment",
        "rarity": "Uncommon",
        "materials": {"magic_stone_medium": 1, "slime_gel": 1},
        "cost": 100,
        "description": "A smooth stone that feels warm to the touch.",
    },
}
