"""
EQUIPMENTS — Eldoria Quest (General equipment pool)
---------------------------------------------------
This is a static dictionary of all general-pool equipment items.
Items are defined by rarity, slot, and stats.

Stats are now balanced for a 999-cap system using a
Level * Rarity formula.
"""

EQUIPMENT_DATA = {
    # --- COMMON (Tier 1, 1.0x Multiplier) ---
    "gen_sword_001": {
        "name": "Rusted Shortsword",
        "slot": "sword",
        "rarity": "Common",
        "level_req": 1,
        "stats_bonus": {"STR": 2},  # (1 * 1.0) * 2 = 2
        "description": "A pitted, rusted blade. It's better than a sharp rock.",
    },
    "gen_staff_001": {
        "name": "Gnarled Branch",
        "slot": "staff",
        "rarity": "Common",
        "level_req": 1,
        "stats_bonus": {"MAG": 2},  # (1 * 1.0) * 2 = 2
        "description": "A thick, gnarled branch picked up from the forest floor. It hums faintly.",
    },
    "gen_armor_001": {
        "name": "Tattered Tunic",
        "slot": "medium_armor",
        "rarity": "Common",
        "level_req": 1,
        "stats_bonus": {"END": 1, "AGI": 1},  # (1 * 1.0) * 2 = 2
        "description": "Moth-eaten and stained, but it's another layer between you and the world.",
    },
    "gen_rogue_armor_001": {
        "name": "Worn Leather Vest",
        "slot": "rogue_armor",
        "rarity": "Common",
        "level_req": 1,
        "stats_bonus": {"AGI": 2}, 
        "description": "Supple leather, worn thin by use, but allows freedom of movement.",
    },
    "gen_accessory_001": {
        "name": "Twine Bracelet",
        "slot": "accessory",
        "rarity": "Common",
        "level_req": 1,
        "stats_bonus": {"LCK": 1},
        "description": "A simple loop of twine. Smells faintly of moss.",
    },
    # --- UNCOMMON (Tier 2, 1.5x Multiplier) ---
    "gen_dagger_003": {
        "name": "Iron Dirk",
        "slot": "dagger",
        "rarity": "Uncommon",
        "level_req": 5,
        "stats_bonus": {"DEX": 8},  # (5 * 1.5) = 7.5
        "description": "A standard-issue iron dagger. Dependable and sharp.",
    },
    "gen_robe_003": {
        "name": "Acolyte's Robe",
        "slot": "robe",
        "rarity": "Uncommon",
        "level_req": 5,
        "stats_bonus": {"MAG": 5, "END": 3},  # (5 * 1.5) = 7.5
        "description": "A heavy wool robe dyed deep indigo.",
    },
    "gen_heavyarmor_003": {
        "name": "Iron Cuirass",
        "slot": "heavy_armor",
        "rarity": "Uncommon",
        "level_req": 5,
        "stats_bonus": {"END": 8},  # (5 * 1.5) = 7.5
        "description": "A breastplate of beaten iron.",
    },
    "gen_accessory_003c": {
        "name": "Polished Stone",
        "slot": "accessory",
        "rarity": "Uncommon",
        "level_req": 5,
        "stats_bonus": {"LCK": 4, "MP": 15},
        "description": "A smooth river stone warm to the touch.",
    },
    # --- RARE (Tier 3, 2.2x Multiplier) ---
    "gen_sword_005": {
        "name": "Hunter's Falchion",
        "slot": "sword",
        "rarity": "Rare",
        "level_req": 10,
        "stats_bonus": {"STR": 16, "DEX": 6},  # (10 * 2.2) = 22
        "description": "A curved heavy blade designed for hide and bone.",
    },
    "gen_staff_005": {
        "name": "Aether-Channeling Staff",
        "slot": "staff",
        "rarity": "Rare",
        "level_req": 10,
        "stats_bonus": {"MAG": 22, "MP": 40},  # (10 * 2.2) = 22
        "description": "A willow staff capped with raw magic stone.",
    },
    "gen_bow_005": {
        "name": "Elm Recurve Bow",
        "slot": "bow",
        "rarity": "Rare",
        "level_req": 10,
        "stats_bonus": {"DEX": 18, "AGI": 4},  # (10 * 2.2) = 22
        "description": "A beautifully crafted recurve bow.",
    },
    "gen_accessory_005c": {
        "name": "Signet of the Old Guild",
        "slot": "accessory",
        "rarity": "Rare",
        "level_req": 10,
        "stats_bonus": {"LCK": 10, "STR": 5, "MAG": 5},
        "description": "A silver ring bearing an ancient guild crest.",
    },
    # --- EPIC (Tier 4, 3.0x Multiplier) ---
    "gen_sword_007": {
        "name": "Kingslayer Claymore",
        "slot": "sword",
        "rarity": "Epic",
        "level_req": 20,
        "stats_bonus": {"STR": 45, "DEX": 15},  # (20 * 3.0) = 60
        "description": "A massive blade rumored to end dynasties.",
    },
    "gen_dagger_006": {
        "name": "Nightshade Stiletto",
        "slot": "dagger",
        "rarity": "Epic",
        "level_req": 20,
        "stats_bonus": {"DEX": 40, "AGI": 20},  # (20 * 3.0) = 60
        "description": "Coated in a poison feared by nobles.",
    },
    "gen_staff_007": {
        "name": "Eldertree Soulbranch",
        "slot": "staff",
        "rarity": "Epic",
        "level_req": 20,
        "stats_bonus": {"MAG": 50, "MP": 75},  # (20 * 3.0) = 60
        "description": "Carved from the roots of a mythical eldertree.",
    },
    "gen_accessory_007": {
        "name": "Charm of Windsong",
        "slot": "accessory",
        "rarity": "Epic",
        "level_req": 20,
        "stats_bonus": {"LCK": 20, "AGI": 10},
        "description": "Sings softly when fortune favors you.",
    },
    # --- LEGENDARY (Tier 5, 4.0x Multiplier) ---
    "gen_sword_008": {
        "name": "Blade of the Fallen Star",
        "slot": "sword",
        "rarity": "Legendary",
        "level_req": 35,
        "stats_bonus": {"STR": 110, "DEX": 30},  # (35 * 4.0) = 140
        "description": "Forged from celestial fragments.",
    },
    "gen_staff_008": {
        "name": "Cosmic Arcanum",
        "slot": "staff",
        "rarity": "Legendary",
        "level_req": 35,
        "stats_bonus": {"MAG": 120, "MP": 150},  # (35 * 4.0) = 140
        "description": "Pulses with astral scripture.",
    },
    "gen_heavyarmor_006c": {
        "name": "Colossusplate Shell",
        "slot": "heavy_armor",
        "rarity": "Legendary",
        "level_req": 35,
        "stats_bonus": {"END": 100, "STR": 40},  # (35 * 4.0) = 140
        "description": "Made from the remains of a colossal titan.",
    },
    "gen_accessory_008": {
        "name": "Emblem of Infinite Fortune",
        "slot": "accessory",
        "rarity": "Legendary",
        "level_req": 35,
        "stats_bonus": {"LCK": 50, "MAG": 25},
        "description": "Whispers with the winds of destiny.",
    },
    # --- MYTHICAL (Tier 6, 5.5x Multiplier) ---
    "gen_sword_009": {
        "name": "Eclipsebreaker",
        "slot": "sword",
        "rarity": "Mythical",
        "level_req": 50,
        "stats_bonus": {"STR": 200, "DEX": 75},  # (50 * 5.5) = 275
        "description": "Forged in the heart of a dying star.",
    },
    "gen_staff_009": {
        "name": "Staff of the Worldheart",
        "slot": "staff",
        "rarity": "Mythical",
        "level_req": 50,
        "stats_bonus": {"MAG": 225, "MP": 250},  # (50 * 5.5) = 275
        "description": "Contains a spark from creation itself.",
    },
    "gen_heavyarmor_007": {
        "name": "World-Titan Carapace",
        "slot": "heavy_armor",
        "rarity": "Mythical",
        "level_req": 50,
        "stats_bonus": {"END": 200, "STR": 75},  # (50 * 5.5) = 275
        "description": "Forged from the armor of an elder titan.",
    },
    "gen_accessory_009": {
        "name": "Mythic Soul Sigil",
        "slot": "accessory",
        "rarity": "Mythical",
        "level_req": 50,
        # --- THIS IS THE FIX ---
        "stats_bonus": {"LCK": 100, "MAG": 15},
        # --- END OF FIX ---
        "description": "Hums with the echo of a forgotten god.",
    },
}

# This is the only thing we export now
__all__ = ["EQUIPMENT_DATA"]