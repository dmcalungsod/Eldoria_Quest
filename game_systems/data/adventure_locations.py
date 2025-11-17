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
        # --- NEW: High level spawn for stronger players ---
        "conditional_monsters": [
            {
                "monster_key": "monster_007", # Hollow Spiderling (Lvl 5 Elite)
                "weight": 10,                 # ~10% spawn chance if added
                "min_level": 3                # Only appears for Level 3+
            }
        ],
        "description": "The safe edge of the forest. Slimes and weak goblins lurk here."
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
        "description": "Sunlight struggles to pierce the canopy. The creatures here hunt in packs."
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
        "description": "The corrupted heart of the forest. Roots coil like serpents, and the air tastes of rot."
    },
    "guild_arena": {
        "name": "Guild Proving Grounds",
        "emoji": "🏟️",
        "min_rank": "F",
        "level_req": 1,
        "duration_options": [],
        "monsters": [], # Boss is custom-spawned
        "description": "The dedicated arena for Adventurer rank examinations."
    }
}