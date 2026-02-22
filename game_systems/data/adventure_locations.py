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
        "special_events": ["safe_room", "hidden_stash"],
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
        "special_events": ["hidden_stash", "trap_pit"],
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
        "night_monsters": [
            ("monster_010", 40),  # Briar Hound (More active at night)
            ("monster_020", 40),  # Ravaged Boar
            ("monster_016", 20),
        ],
        "description": "The corrupted heart of the forest. Roots coil like serpents, and the air tastes of rot.",
        "gatherables": [
            ("ancient_wood", 50),
            ("iron_ore", 30),
            ("magic_stone_medium", 20),
        ],
        "special_events": ["trap_pit", "ancient_shrine"],
    },
    "the_ashlands": {
        "name": "The Ashlands",
        "emoji": "🌋",
        "min_rank": "D",
        "level_req": 12,
        "duration_options": [60, 120, 240],
        "monsters": [
            ("monster_131", 30),  # Ash Rat
            ("monster_132", 30),  # Cinder Mite
            ("monster_133", 25),  # Ember Fox
            ("monster_134", 15),  # Scorched Scavenger
        ],
        "night_monsters": [
            ("monster_133", 40),  # Ember Fox (Active at night)
            ("monster_134", 40),  # Scorched Scavenger
            ("monster_132", 20),
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_135",  # Slag Golem (Boss)
                "weight": 5,
                "min_level": 16,
            }
        ],
        "description": "A grey wasteland of volcanic ash and skeletal trees. The heat is oppressive.",
        "gatherables": [
            ("obsidian_shard", 40),
            ("ash_blossom", 30),
            ("iron_ore", 20),
            ("magic_stone_medium", 10),
        ],
        "special_events": ["trap_pit", "hidden_stash", "safe_room"],
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
        "night_monsters": [
            ("monster_027", 50),  # Mire Lurker (Lurks in darkness)
            ("monster_022", 30),  # Marsh Crawler
            ("monster_025", 20),
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
        "special_events": ["safe_room", "trap_pit"],
    },
    "sunken_grotto": {
        "name": "The Sunken Grotto",
        "emoji": "🌊",
        "min_rank": "C",
        "level_req": 18,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_121", 30),  # Coral Golem
            ("monster_122", 30),  # Abyssal Eel
            ("monster_123", 25),  # Tide Siren
            ("monster_124", 15),  # Deep Crawler
        ],
        "night_monsters": [
            ("monster_122", 40),  # Abyssal Eel
            ("monster_124", 40),  # Deep Crawler (Comes out in dark)
            ("monster_123", 20),
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_125",  # Leviathan (Boss)
                "weight": 5,
                "min_level": 23,
            }
        ],
        "description": "A submerged cavern network lit by bioluminescence. The water here is deep and cold.",
        "gatherables": [
            ("coral_fragment", 40),
            ("pearl", 30),
            ("magic_stone_medium", 20),
            ("bioluminescent_scale", 10),
        ],
        "special_events": ["hidden_stash", "ancient_shrine"],
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
        "night_monsters": [
            ("monster_104", 40),  # Obsidian Gargoyle (Blends with dark)
            ("monster_103", 30),  # Shard Wisp
            ("monster_102", 30),
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
        "special_events": ["safe_room", "ancient_shrine"],
    },
    "clockwork_halls": {
        "name": "The Clockwork Halls",
        "emoji": "⚙️",
        "min_rank": "B",
        "level_req": 22,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_126", 30),  # Cogwork Spider
            ("monster_127", 30),  # Brass Golem
            ("monster_128", 25),  # Steam Wisp
            ("monster_129", 15),  # Automaton Knight
        ],
        "night_monsters": [
            ("monster_126", 40),  # Cogwork Spider
            ("monster_128", 40),  # Steam Wisp
            ("monster_129", 20),
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_130",  # The Gear Warden
                "weight": 5,
                "min_level": 26,
            }
        ],
        "description": "A labyrinth of grinding gears and hissing steam pipes. The ancient machines here are still running.",
        "gatherables": [
            ("brass_gear", 40),
            ("copper_wire", 30),
            ("spring_coil", 20),
            ("magic_stone_medium", 10),
        ],
        "special_events": ["trap_pit", "hidden_stash"],
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
        "night_monsters": [
            ("monster_108", 40),  # Ember Salamander
            ("monster_109", 30),  # Lava Drake
            ("monster_106", 30),
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
        "special_events": ["trap_pit", "safe_room"],
    },
    "frostfall_expanse": {
        "name": "The Frostfall Expanse",
        "emoji": "❄️",
        "min_rank": "A",
        "level_req": 25,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_111", 30),  # Frost Wolf
            ("monster_112", 25),  # Ice Golem
            ("monster_113", 30),  # Chill Wisp
            ("monster_114", 15),  # Glacial Drake
        ],
        "night_monsters": [
            ("monster_111", 40),  # Frost Wolf (Hunts at night)
            ("monster_113", 30),  # Chill Wisp
            ("monster_114", 30),  # Glacial Drake
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_115",  # Cryon
                "weight": 5,
                "min_level": 29,
            }
        ],
        "description": "A frozen wasteland where the wind cuts like a knife and only the strong survive.",
        "gatherables": [
            ("frost_crystal", 40),
            ("winter_wolf_pelt", 30),
            ("magic_stone_medium", 30),
        ],
        "special_events": ["safe_room", "hidden_stash"],
    },
    "void_sanctum": {
        "name": "The Void Sanctum",
        "emoji": "⚫",
        "min_rank": "S",
        "level_req": 40,
        "duration_options": [60, 120, 240, 480],
        "monsters": [
            ("monster_116", 30),  # Void Stalker
            ("monster_118", 30),  # Null Wisp
            ("monster_117", 25),  # Abyssal Construct
            ("monster_119", 15),  # Entropy Drake
        ],
        "night_monsters": [
            ("monster_116", 50),  # Void Stalker
            ("monster_119", 30),  # Entropy Drake
            ("monster_118", 20),
        ],
        "conditional_monsters": [
            {
                "monster_key": "monster_120",  # Omega (Boss)
                "weight": 5,
                "min_level": 44,
            }
        ],
        "description": "A realm where reality frays and silence screams. The final frontier of the known world.",
        "gatherables": [
            ("void_dust", 40),
            ("abyssal_shackle", 30),
            ("entropy_crystal", 20),
            ("magic_stone_flawless", 10),
        ],
        "special_events": ["trap_pit", "ancient_shrine"],
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
