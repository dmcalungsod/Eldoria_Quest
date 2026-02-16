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
}
