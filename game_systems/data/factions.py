"""
factions.py

Defines the factions available for players to join.
Each faction has a unique identity, goals, and reward structure.
"""

FACTIONS = {
    "pathfinders": {
        "name": "The Pathfinders",
        "emoji": "🧭",
        "description": "Explorers dedicated to mapping the unknown depths of the dungeon.",
        "ranks": {
            1: {"title": "Initiate", "reputation_needed": 0, "reward": None},
            2: {
                "title": "Scout",
                "reputation_needed": 500,
                "reward": {"type": "item", "key": "map_fragment", "amount": 1},
            },
            3: {
                "title": "Wayfarer",
                "reputation_needed": 1500,
                "reward": {"type": "item", "key": "compass", "amount": 1},
            },
            4: {
                "title": "Trailblazer",
                "reputation_needed": 3000,
                "reward": {"type": "buff", "key": "gathering_boost", "value": 0.1},
            },
            5: {
                "title": "Cartographer",
                "reputation_needed": 5000,
                "reward": {"type": "title", "value": "Master Cartographer"},
            },
        },
        "interests": {
            "exploration": 1.5,  # Multiplier for exploration rep
            "gathering": 1.2,
            "monster_types": ["Beast", "Plant"],
        },
        "favored_locations": [
            "forest_outskirts",
            "whispering_thicket",
            "deepgrove_roots",
            "shrouded_fen",
        ],
    },
    "iron_vanguard": {
        "name": "The Iron Vanguard",
        "emoji": "🛡️",
        "description": "Protectors of Eldoria who specialize in eliminating dangerous threats.",
        "ranks": {
            1: {"title": "Recruit", "reputation_needed": 0, "reward": None},
            2: {
                "title": "Guard",
                "reputation_needed": 500,
                "reward": {"type": "item", "key": "whetstone", "amount": 3},
            },
            3: {
                "title": "Sentinel",
                "reputation_needed": 1500,
                "reward": {"type": "item", "key": "potion_large", "amount": 5},
            },
            4: {
                "title": "Vanguard",
                "reputation_needed": 3000,
                "reward": {"type": "buff", "key": "defense_boost", "value": 0.1},
            },
            5: {
                "title": "Champion",
                "reputation_needed": 5000,
                "reward": {"type": "title", "value": "Shield of Eldoria"},
            },
        },
        "interests": {
            "boss_kills": 2.0,
            "elite_kills": 1.5,
            "monster_types": ["Undead", "Construct"],
        },
        "favored_locations": [
            "forgotten_ossuary",
            "void_sanctum",
            "gale_scarred_heights",
            "deepgrove_roots",
        ],
    },
    "arcane_assembly": {
        "name": "The Arcane Assembly",
        "emoji": "🔮",
        "description": "Scholars seeking to understand the magical mysteries of the dungeon.",
        "ranks": {
            1: {"title": "Novice", "reputation_needed": 0, "reward": None},
            2: {
                "title": "Adept",
                "reputation_needed": 500,
                "reward": {"type": "item", "key": "magic_stone_small", "amount": 5},
            },
            3: {
                "title": "Scholar",
                "reputation_needed": 1500,
                "reward": {"type": "item", "key": "scroll_exp", "amount": 1},
            },
            4: {
                "title": "Magister",
                "reputation_needed": 3000,
                "reward": {"type": "buff", "key": "magic_boost", "value": 0.1},
            },
            5: {
                "title": "Archmage",
                "reputation_needed": 5000,
                "reward": {"type": "title", "value": "Keeper of Secrets"},
            },
        },
        "interests": {
            "magic_kills": 1.5,
            "collecting": 1.2,
            "monster_types": ["Elemental", "Demon"],
        },
        "favored_locations": [
            "crystal_caverns",
            "celestial_archipelago",
            "shimmering_wastes",
            "sunken_grotto",
            "whispering_archives",
        ],
    },
    "stone_harvesters": {
        "name": "The Stone Harvesters",
        "emoji": "⛏️",
        "description": "Hardy miners and smiths who extract the dungeon's material wealth.",
        "ranks": {
            1: {"title": "Laborer", "reputation_needed": 0, "reward": None},
            2: {
                "title": "Prospector",
                "reputation_needed": 500,
                "reward": {"type": "item", "key": "iron_ingot", "amount": 3},
            },
            3: {
                "title": "Excavator",
                "reputation_needed": 1500,
                "reward": {"type": "item", "key": "obsidian_shard", "amount": 5},
            },
            4: {
                "title": "Foreman",
                "reputation_needed": 3000,
                "reward": {"type": "buff", "key": "gathering_boost", "value": 0.1},
            },
            5: {
                "title": "Geo-Master",
                "reputation_needed": 5000,
                "reward": {"type": "title", "value": "Earthshaker"},
            },
        },
        "interests": {
            "gathering": 1.5,
            "monster_types": ["Construct", "Elemental"],
        },
        "favored_locations": [
            "molten_caldera",
            "clockwork_halls",
            "frostfall_expanse",
            "the_ashlands",
        ],
    },
    "grey_ward": {
        "name": "Grey Ward",
        "emoji": "⚕️",
        "description": "A pragmatic order of alchemists and doctors who believe the only way to survive the Veil is to adapt to it. They operate the city's quarantine zones.",
        "ranks": {
            1: {"title": "Scavenger", "reputation_needed": 0, "reward": None},
            2: {
                "title": "Mixologist",
                "reputation_needed": 500,
                "reward": {"type": "item", "key": "bitter_panacea", "amount": 3},
            },
            3: {
                "title": "Apothecary",
                "reputation_needed": 1500,
                "reward": {"type": "item", "key": "phial_of_vitriol", "amount": 3},
            },
            4: {
                "title": "Chirurgeon",
                "reputation_needed": 3000,
                "reward": {"type": "buff", "key": "gathering_boost", "value": 0.1},
            },
            5: {
                "title": "Transmuter",
                "reputation_needed": 5000,
                "reward": {"type": "title", "value": "Master Apothecary"},
            },
        },
        "interests": {
            "gathering": 1.5,
            "crafting": 1.5,
            "monster_types": ["Plant", "Slime"],
        },
        "favored_locations": [
            "whispering_thicket",
            "deepgrove_roots",
            "shrouded_fen",
            "forgotten_ossuary",
            "the_ashlands",
        ],
    },
}
