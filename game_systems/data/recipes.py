"""
recipes.py

Defines the Alchemist's crafting recipes.
Maps materials to consumable outputs.
"""

RECIPES = {
    "hp_potion_1": {
        "id": "hp_potion_1",
        "name": "Dewfall Tonic",
        "output_key": "hp_potion_1",
        "output_amount": 1,
        "materials": {"medicinal_herb": 2},
        "cost": 15,
        "description": "Brew common herbs into a basic healing tonic.",
    },
    "hp_potion_2": {
        "id": "hp_potion_2",
        "name": "Glade Salve Vial",
        "output_key": "hp_potion_2",
        "output_amount": 1,
        "materials": {"medicinal_herb": 4, "slime_gel": 2},
        "cost": 50,
        "description": "Refine herbs with slime gel for a potent salve.",
    },
    "mp_potion_1": {
        "id": "mp_potion_1",
        "name": "Scholar's Draught",
        "output_key": "mp_potion_1",
        "output_amount": 1,
        "materials": {"magic_stone_fragment": 3},
        "cost": 25,
        "description": "Distill magic fragments into liquid mana.",
    },
    "mp_potion_2": {
        "id": "mp_potion_2",
        "name": "Lunaris Tonic",
        "output_key": "mp_potion_2",
        "output_amount": 1,
        "materials": {"magic_stone_small": 2, "medicinal_herb": 2},
        "cost": 75,
        "description": "Combine magic stones and herbs for greater mana recovery.",
    },
    "antidote_basic": {
        "id": "antidote_basic",
        "name": "Thicket Antidote",
        "output_key": "antidote_basic",
        "output_amount": 1,
        "materials": {"medicinal_herb": 1, "slime_gel": 1},
        "cost": 20,
        "description": "A simple mixture to neutralize poisons.",
    },
    "stamina_tonic": {
        "id": "stamina_tonic",
        "name": "Runner's Cordial",
        "output_key": "stamina_tonic",
        "output_amount": 1,
        "materials": {"spider_silk": 2, "wolf_fang": 1},
        "cost": 40,
        "description": "A stimulant brewed from spider silk and fangs.",
    },
    "throwing_bomb": {
        "id": "throwing_bomb",
        "name": "Sporebomb",
        "output_key": "throwing_bomb",
        "output_amount": 2,
        "materials": {"slime_gel": 3, "iron_ore": 1},
        "cost": 60,
        "description": "Pack volatile slime into an iron casing.",
    },
}
