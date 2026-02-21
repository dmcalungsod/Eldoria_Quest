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
    },
}
