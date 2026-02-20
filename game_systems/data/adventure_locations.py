"""
adventure_locations.py

Defines the exploration zones available to adventurers.
Each location dictates the monster pool, difficulty, and rewards.
"""

LOCATIONS = {
    "forest_outskirts": {
        "name": "Willowcreek Outskirts",
        "emoji": "🌲",
        "min_rank": "F",
        "level_req": 1,
        "duration_options": [15, 30, 60],
        "monsters": [
            ("monster_001", 40),  # Verdant Slime
            ("monster_002", 40),  # Glimmer Slime
            ("monster_003", 20),  # Goblin Grunt
        ],
        "night_monsters": [
            ("monster_003", 60),  # Goblin Grunt (More active at night)
            ("monster_007", 40),  # Hollow Spiderling (Nocturnal)
        ],
        # --- NEW: High level spawn for stronger players ---
        "conditional_monsters": [
            {
                "monster_key": "monster_007",  # Hollow Spiderling (Lvl 5 Elite)
                "weight": 10,  # ~10% spawn chance if added
                "min_level": 3,  # Only appears for Level 3+
            }
        ],
        "description": "The safe edge of the forest. Slimes and weak goblins lurk here.",
        "gatherables": [
            ("medicinal_herb", 70),
            ("magic_stone_fragment", 30),
        ],
    },
    "whispering_thicket": {
        "name": "Whispering Thicket",
        "emoji": "🍃",
        "min_rank": "E",
        "level_req": 5,
        "duration_options": [30, 60, 120],
        "monsters": [
            ("monster_004", 30),  # Goblin Scout
            ("monster_005", 30),  # Bramble Goblin
            ("monster_006", 20),  # Forest Wolf Pup
            ("monster_008", 10),  # Thicket Spider
        ],
        "night_monsters": [
            ("monster_008", 40),  # Thicket Spider (Nocturnal hunter)
            ("monster_005", 20),  # Bramble Goblin
            ("monster_006", 20),  # Forest Wolf Pup
            ("monster_010", 20),  # Briar Hound (Roams at night)
        ],
        "description": "Sunlight struggles to pierce the canopy. The creatures here hunt in packs.",
        "gatherables": [
            ("medicinal_herb", 40),
            ("ancient_wood", 40),
            ("magic_stone_small", 20),
        ],
    },
    "deepgrove_roots": {
        "name": "Deepgrove Roots",
        "emoji": "🍄",
        "min_rank": "D",
        "level_req": 10,
        "duration_options": [60, 120, 240],
        "monsters": [
            ("monster_010", 25),  # Briar Hound
            ("monster_016", 25),  # Young Treant
            ("monster_017", 15),  # Feral Stag (Boss-like)
            ("monster_020", 20),  # Ravaged Boar
        ],
        "description": "The corrupted heart of the forest. Roots coil like serpents, and the air tastes of rot.",
        "gatherables": [
            ("ancient_wood", 50),
            ("iron_ore", 30),
            ("magic_stone_medium", 20),
        ],
    },
    "shrouded_fen": {
        "name": "The Shrouded Fen",
        "emoji": "🌫️",
        "min_rank": "C",
        "level_req": 15,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_022", 30),  # Marsh Crawler
            ("monster_023", 20),  # Sporeling
            ("monster_025", 20),  # Stormling
            ("monster_027", 15),  # Mire Lurker
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_028",  # Duskling (Elite)
                "weight": 10,
                "min_level": 16,
            },
            {
                "monster_key": "monster_034",  # Glade Empress (Boss)
                "weight": 5,
                "min_level": 18,
            },
        ],
        "description": "A mist-choked wetland where the veil is thin. Shadows move in the fog, and the ground hungers for the unwary.",
        "gatherables": [
            ("medicinal_herb", 30),
            ("ancient_wood", 30),
            ("iron_ore", 20),
            ("magic_stone_medium", 20),
        ],
    },
    "crystal_caverns": {
        "name": "The Crystal Caverns",
        "emoji": "💎",
        "min_rank": "B",
        "level_req": 20,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_101", 30),  # Crystal Golem
            ("monster_102", 30),  # Prism Spider
            ("monster_103", 25),  # Shard Wisp
            ("monster_104", 15),  # Obsidian Gargoyle
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_105",  # Crystalline Guardian (Boss)
                "weight": 5,
                "min_level": 25,
            }
        ],
        "description": "A breathtaking subterranean world of glowing crystals and ancient technology.",
        "gatherables": [
            ("luminescent_crystal", 40),
            ("mithril_ore", 30),
            ("magic_stone_medium", 30),
        ],
    },
    "molten_caldera": {
        "name": "The Molten Caldera",
        "emoji": "🌋",
        "min_rank": "A",
        "level_req": 30,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_106", 30),  # Fire Elemental
            ("monster_107", 30),  # Magma Golem
            ("monster_108", 25),  # Ember Salamander
            ("monster_109", 15),  # Lava Drake (Elite)
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_110",  # Ignis (Boss)
                "weight": 5,
                "min_level": 35,
            }
        ],
        "description": "A churning lake of fire and obsidian. The heat alone is enough to kill the unprepared.",
        "gatherables": [
            ("obsidian_shard", 40),
            ("fire_essence", 30),
            ("magma_core", 20),
            ("magic_stone_large", 10),
        ],
    },
    "guild_arena": {
        "name": "Guild Proving Grounds",
        "emoji": "🏟️",
        "min_rank": "F",
        "level_req": 1,
        "duration_options": [],
        "monsters": [],  # Boss is custom-spawned
        "description": "The dedicated arena for Adventurer rank examinations.",
    },
}
