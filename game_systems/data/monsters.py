"""
MONSTERS (forest beginner zone) — Eldoria Quest
----------------------------------------------
Generates 50 forest-themed monsters (levels 1–30).
REBALANCED: XP Rewards increased to match the steep leveling curve.
"""

from math import ceil

from game_systems.monsters.monster_skills import MONSTER_SKILLS

NAME_POOL = [
    "Verdant Slime",
    "Glimmer Slime",
    "Goblin Grunt",
    "Goblin Scout",
    "Bramble Goblin",
    "Forest Wolf Pup",
    "Hollow Spiderling",
    "Thicket Spider",
    "Fen Wisp",
    "Briar Hound",
    "Mossback Tortoise",
    "Vineling",
    "Burbling Sprite",
    "Rookwood Shade",
    "Gloam Hare",
    "Young Treant",
    "Feral Stag",
    "Sapling Ent",
    "Ragged Urch",
    "Ravaged Boar",
    "Pine Wight",
    "Marsh Crawler",
    "Sporeling",
    "Ridge Wolf",
    "Stormling",
    "Thornback Boar",
    "Mire Lurker",
    "Duskling",
    "Wisp-Sentinel",
    "Gnarled Brute",
    "Shade Warden",
    "Fen Revenant",
    "Bramble King",
    "Glade Empress",
    "Sylvan Herald",
    "Elder Treant",
    "Abyssal Wolf",
    "Blight Stag",
    "Wretched Entling",
    "Nightbloom",
]

def _get_monster_description(name, level, tier):
    """Generates a lore-appropriate description based on monster type."""
    if "Slime" in name:
        return f"A gelatinous mass of corrupted mana. It digests anything it touches, leaving only clean bone."
    elif "Goblin" in name:
        return f"A stunted, vicious scavenger born from the Sundering. It covets shiny objects and fresh meat."
    elif "Wolf" in name or "Hound" in name:
        return f"A predator twisted by the Veil, its eyes glowing with unnatural hunger."
    elif "Spider" in name:
        return f"A multi-legged horror that spins webs of sticky, mana-infused silk to entrap the unwary."
    elif "Wisp" in name or "Shade" in name or "Duskling" in name or "Revenant" in name:
        return f"A flickering remnant of a soul lost to the Void, now seeking warmth to steal."
    elif "Treant" in name or "Ent" in name or "Sapling" in name or "Vineling" in name or "Nightbloom" in name:
        return f"The forest itself, awakened by dark magic and twisted into a guardian of rot."
    elif "Boar" in name or "Stag" in name or "Hare" in name or "Tortoise" in name:
        return f"Once a natural beast, now warped by the leaking energies of the Broken Veil."
    elif "Sprite" in name:
        return f"A small, malicious fey creature that delights in leading travelers to their doom."
    elif "Urch" in name or "Crawler" in name or "Lurker" in name:
        return f"A spiny, bottom-feeding scavenger that has grown to monstrous size."
    elif "Boss" in tier or "King" in name or "Empress" in name:
        return f"A massive, ancient entity that dominates its territory. Its very presence warps the air around it."
    else:
        return f"A creature of the Shattered Veil, prowling the wilds in search of prey."

MONSTERS = {}
for idx in range(1, 51):
    name = NAME_POOL[(idx - 1) % len(NAME_POOL)]
    level = min(30, ceil(idx * 0.6))

    # --- Tier Assignment ---
    if idx in (17, 34, 50):
        tier = "Boss"
    elif level >= 18 or idx % 7 == 0:
        tier = "Elite"
    else:
        tier = "Normal"

    # --- Base Stats ---
    base_hp = 35 + (level * 12)
    base_atk = 5 + (level * 2)
    base_def = 1 + level

    # --- Tier Multipliers ---
    if tier == "Boss":
        hp = base_hp * 12
        atk = base_atk * 2.5
        defense = base_def * 2
        xp_mult = 15.0
    elif tier == "Elite":
        hp = base_hp * 4
        atk = base_atk * 1.5
        defense = base_def * 1.5
        xp_mult = 4.0
    else:
        # Normal Mobs:
        # HP Multiplier kept at 2.5x as per user preference for difficulty model
        hp = base_hp * 2.5
        atk = base_atk
        defense = base_def
        xp_mult = 1.2

    # --- XP Calculation (FIXED) ---
    # OLD: level * 12
    # NEW: level * 25 (Doubled reward for the effort)
    xp = int((level * 25) * xp_mult)

    # --- Drops ---
    drops = []
    if tier == "Boss":
        drops.append(("magic_stone_large", 100))
        drops.append(("magic_stone_flawless", 25))
        drops.append(("boss_talon", 100))
        drops.append(("celestial_dust", 15))
    elif tier == "Elite":
        drops.append(("magic_stone_medium", 80))
        drops.append(("magic_stone_large", 15))
    else:
        if level < 5:
            drops.append(("magic_stone_fragment", 75))
        else:
            drops.append(("magic_stone_small", 80))

    # --- Skills Assignment ---
    skills = []
    if "Slime" in name:
        skills.append(MONSTER_SKILLS["mend"])
        skills.append(MONSTER_SKILLS["poison_spit"])
    elif "Goblin" in name:
        skills.append(MONSTER_SKILLS["rapid_strike"])
        if level > 5:
            skills.append(MONSTER_SKILLS["heavy_blow"])
    elif "Wolf" in name or "Hound" in name:
        skills.append(MONSTER_SKILLS["vicious_bite"])
        skills.append(MONSTER_SKILLS["rapid_strike"])
    elif "Treant" in name or "Ent" in name:
        skills.append(MONSTER_SKILLS["crushing_slam"])
        skills.append(MONSTER_SKILLS["regenerate"])
    elif "Wisp" in name or "Shade" in name:
        skills.append(MONSTER_SKILLS["ember"])
    elif "Boss" in tier or "King" in name or "Empress" in name:
        skills.append(MONSTER_SKILLS["heavy_blow"])
        skills.append(MONSTER_SKILLS["flame_breath"])
        skills.append(MONSTER_SKILLS["regenerate"])
    else:
        # Default skills for others
        if level >= 10:
            skills.append(MONSTER_SKILLS["heavy_blow"])
        else:
            skills.append(MONSTER_SKILLS["rapid_strike"])

    # Additional drops based on type
    if "Slime" in name:
        drops.append(("slime_gel", 40))
    elif "Goblin" in name:
        drops.append(("goblin_ear", 35))
    elif "Wolf" in name:
        drops.append(("wolf_fang", 25))
    elif "Spider" in name:
        drops.append(("spider_silk", 30))
    elif "Treant" in name:
        drops.append(("treant_branch", 15))
        if tier in ["Elite", "Boss"]:
            drops.append(("ironwood_heart", 20))
    elif "Boar" in name:
        drops.append(("boar_meat", 40))
        drops.append(("boar_tusk", 25))
    elif any(x in name for x in ["Wisp", "Shade", "Duskling", "Revenant", "Wight"]):
        drops.append(("shadow_essence", 15))
    elif any(x in name for x in ["Brute", "Sentinel", "King", "Empress"]):
        drops.append(("titan_shard", 10))

    description = _get_monster_description(name, level, tier)

    MONSTERS[f"monster_{idx:03d}"] = {
        "id": idx,
        "name": name,
        "level": level,
        "tier": tier,
        "hp": int(hp),
        "atk": int(atk),
        "def": int(defense),
        "xp": xp,
        "drops": drops,
        "skills": skills,
        "description": description,
    }

# --- CRYSTAL CAVERNS MONSTERS (Rank B) ---

# 101: Crystal Golem (Tank)
MONSTERS["monster_101"] = {
    "id": 101,
    "name": "Crystal Golem",
    "level": 22,
    "tier": "Normal",
    "hp": 700,
    "atk": 50,
    "def": 35,
    "xp": 550,
    "drops": [("magic_stone_medium", 80), ("luminescent_crystal", 40)],
    "skills": [MONSTER_SKILLS["heavy_blow"], MONSTER_SKILLS["crystal_shard"]],
    "description": "A lumbering construct of jagged quartz, ancient and unyielding.",
}

# 102: Prism Spider (Fast)
MONSTERS["monster_102"] = {
    "id": 102,
    "name": "Prism Spider",
    "level": 20,
    "tier": "Normal",
    "hp": 450,
    "atk": 60,
    "def": 15,
    "xp": 500,
    "drops": [("spider_silk", 50), ("luminescent_crystal", 30)],
    "skills": [MONSTER_SKILLS["rapid_strike"], MONSTER_SKILLS["crystal_shard"]],
    "description": "Its translucent carapace makes it hard to track in the shimmering light.",
}

# 103: Shard Wisp (Magic)
MONSTERS["monster_103"] = {
    "id": 103,
    "name": "Shard Wisp",
    "level": 21,
    "tier": "Normal",
    "hp": 400,
    "atk": 70,
    "def": 10,
    "xp": 525,
    "drops": [("magic_stone_medium", 90), ("mithril_ore", 20)],
    "skills": [MONSTER_SKILLS["prism_beam"], MONSTER_SKILLS["ember"]],
    "description": "A floating orb of condensed mana and light.",
}

# 104: Obsidian Gargoyle (Flying/Elite)
MONSTERS["monster_104"] = {
    "id": 104,
    "name": "Obsidian Gargoyle",
    "level": 23,
    "tier": "Elite",
    "hp": 1200,
    "atk": 80,
    "def": 40,
    "xp": 2000,
    "drops": [("magic_stone_large", 50), ("mithril_ore", 40)],
    "skills": [MONSTER_SKILLS["crushing_slam"], MONSTER_SKILLS["flame_breath"]],
    "description": "Carved from volcanic glass, it swoops down with crushing weight.",
}

# 105: Crystalline Guardian (Boss)
MONSTERS["monster_105"] = {
    "id": 105,
    "name": "Crystalline Guardian",
    "level": 25,
    "tier": "Boss",
    "hp": 5000,
    "atk": 110,
    "def": 60,
    "xp": 8000,
    "drops": [("magic_stone_flawless", 100), ("crystal_heart", 100), ("mithril_ore", 50)],
    "skills": [MONSTER_SKILLS["prism_beam"], MONSTER_SKILLS["crystal_shard"], MONSTER_SKILLS["regenerate"]],
    "description": "The heart of the caverns, a massive entity of living light and stone.",
}

# --- MOLTEN CALDERA MONSTERS (Rank A) ---

# 106: Fire Elemental (Magic)
MONSTERS["monster_106"] = {
    "id": 106,
    "name": "Fire Elemental",
    "level": 30,
    "tier": "Normal",
    "hp": 1000,
    "atk": 90,
    "def": 20,
    "xp": 900,
    "drops": [("fire_essence", 60), ("magic_stone_medium", 40)],
    "skills": [MONSTER_SKILLS["ember"], MONSTER_SKILLS["flame_breath"]],
    "description": "A living pillar of flame that scorches the air around it.",
}

# 107: Magma Golem (Tank)
MONSTERS["monster_107"] = {
    "id": 107,
    "name": "Magma Golem",
    "level": 32,
    "tier": "Normal",
    "hp": 1500,
    "atk": 70,
    "def": 80,
    "xp": 950,
    "drops": [("obsidian_shard", 70), ("magma_core", 25)],
    "skills": [MONSTER_SKILLS["heavy_blow"], MONSTER_SKILLS["regenerate"]],
    "description": "Molten rock given form, its steps shake the ground.",
}

# 108: Ember Salamander (Fast)
MONSTERS["monster_108"] = {
    "id": 108,
    "name": "Ember Salamander",
    "level": 31,
    "tier": "Normal",
    "hp": 900,
    "atk": 100,
    "def": 30,
    "xp": 925,
    "drops": [("obsidian_shard", 50), ("fire_essence", 40)],
    "skills": [MONSTER_SKILLS["rapid_strike"], MONSTER_SKILLS["vicious_bite"]],
    "description": "A quick, lizard-like creature that scurries through lava pools.",
}

# 109: Lava Drake (Elite)
MONSTERS["monster_109"] = {
    "id": 109,
    "name": "Lava Drake",
    "level": 34,
    "tier": "Elite",
    "hp": 2500,
    "atk": 120,
    "def": 50,
    "xp": 3500,
    "drops": [("dragon_scale", 40), ("magic_stone_large", 60)],
    "skills": [MONSTER_SKILLS["flame_breath"], MONSTER_SKILLS["crushing_slam"]],
    "description": "A lesser dragon with scales like cooled volcanic rock.",
}

# 110: Ignis, Lord of Cinders (Boss)
MONSTERS["monster_110"] = {
    "id": 110,
    "name": "Ignis, Lord of Cinders",
    "level": 35,
    "tier": "Boss",
    "hp": 8000,
    "atk": 150,
    "def": 90,
    "xp": 12000,
    "drops": [("magic_stone_flawless", 100), ("magma_core", 100), ("dragon_scale", 50)],
    "skills": [MONSTER_SKILLS["flame_breath"], MONSTER_SKILLS["heavy_blow"], MONSTER_SKILLS["ember"]],
    "description": "An ancient spirit of fire, clad in armor of obsidian and hate.",
}

# --- FROSTFALL EXPANSE MONSTERS (Rank A) ---

# 111: Frost Wolf (Fast)
MONSTERS["monster_111"] = {
    "id": 111,
    "name": "Frost Wolf",
    "level": 26,
    "tier": "Normal",
    "hp": 850,
    "atk": 85,
    "def": 25,
    "xp": 800,
    "drops": [("winter_wolf_pelt", 60), ("magic_stone_medium", 30)],
    "skills": [MONSTER_SKILLS["vicious_bite"], MONSTER_SKILLS["rapid_strike"]],
    "description": "Its white fur blends perfectly with the snow, hiding its deadly intent.",
}

# 112: Ice Golem (Tank)
MONSTERS["monster_112"] = {
    "id": 112,
    "name": "Ice Golem",
    "level": 27,
    "tier": "Normal",
    "hp": 1400,
    "atk": 65,
    "def": 70,
    "xp": 850,
    "drops": [("frost_crystal", 70), ("ice_core", 20)],
    "skills": [MONSTER_SKILLS["heavy_blow"], MONSTER_SKILLS["ice_shard"]],
    "description": "A construct of animate permafrost, slow but relentless.",
}

# 113: Chill Wisp (Magic)
MONSTERS["monster_113"] = {
    "id": 113,
    "name": "Chill Wisp",
    "level": 26,
    "tier": "Normal",
    "hp": 750,
    "atk": 95,
    "def": 15,
    "xp": 820,
    "drops": [("magic_stone_medium", 80), ("frost_crystal", 40)],
    "skills": [MONSTER_SKILLS["ice_shard"], MONSTER_SKILLS["frost_breath"]],
    "description": "A flickering spirit of cold light that saps warmth from the air.",
}

# 114: Glacial Drake (Elite)
MONSTERS["monster_114"] = {
    "id": 114,
    "name": "Glacial Drake",
    "level": 28,
    "tier": "Elite",
    "hp": 2200,
    "atk": 110,
    "def": 45,
    "xp": 3000,
    "drops": [("frozen_scale", 30), ("magic_stone_large", 50)],
    "skills": [MONSTER_SKILLS["frost_breath"], MONSTER_SKILLS["vicious_bite"]],
    "description": "A winged predator with scales of blue ice, hunting the frozen wastes.",
}

# 115: Cryon, the Frozen King (Boss)
MONSTERS["monster_115"] = {
    "id": 115,
    "name": "Cryon, the Frozen King",
    "level": 29,
    "tier": "Boss",
    "hp": 7000,
    "atk": 135,
    "def": 80,
    "xp": 10000,
    "drops": [("magic_stone_flawless", 100), ("ice_core", 100), ("frozen_scale", 50)],
    "skills": [MONSTER_SKILLS["glacial_roar"], MONSTER_SKILLS["frost_breath"], MONSTER_SKILLS["heavy_blow"]],
    "description": "An ancient giant clad in glacial armor, ruling the eternal winter.",
}

# --- THE VOID SANCTUM MONSTERS (Rank S) ---

# 116: Void Stalker (Fast)
MONSTERS["monster_116"] = {
    "id": 116,
    "name": "Void Stalker",
    "level": 41,
    "tier": "Normal",
    "hp": 2800,
    "atk": 160,
    "def": 40,
    "xp": 3500,
    "drops": [("void_dust", 70), ("magic_stone_large", 40)],
    "skills": [MONSTER_SKILLS["void_slash"], MONSTER_SKILLS["rapid_strike"]],
    "description": "A silhouette that moves between shadows, striking with unseen blades.",
}

# 117: Abyssal Construct (Tank)
MONSTERS["monster_117"] = {
    "id": 117,
    "name": "Abyssal Construct",
    "level": 42,
    "tier": "Normal",
    "hp": 5000,
    "atk": 130,
    "def": 120,
    "xp": 3800,
    "drops": [("abyssal_shackle", 60), ("magic_stone_large", 50)],
    "skills": [MONSTER_SKILLS["heavy_blow"], MONSTER_SKILLS["crushing_slam"]],
    "description": "Armor animated by a void spirit, relentless and unfeeling.",
}

# 118: Null Wisp (Magic)
MONSTERS["monster_118"] = {
    "id": 118,
    "name": "Null Wisp",
    "level": 41,
    "tier": "Normal",
    "hp": 2500,
    "atk": 180,
    "def": 30,
    "xp": 3600,
    "drops": [("entropy_crystal", 50), ("void_dust", 40)],
    "skills": [MONSTER_SKILLS["entropy_wave"], MONSTER_SKILLS["prism_beam"]],
    "description": "A sphere of anti-light that distorts the air around it.",
}

# 119: Entropy Drake (Elite)
MONSTERS["monster_119"] = {
    "id": 119,
    "name": "Entropy Drake",
    "level": 44,
    "tier": "Elite",
    "hp": 8500,
    "atk": 200,
    "def": 80,
    "xp": 15000,
    "drops": [("null_stone", 40), ("magic_stone_flawless", 30)],
    "skills": [MONSTER_SKILLS["void_slash"], MONSTER_SKILLS["entropy_wave"]],
    "description": "A twisted dragon whose scales seem to devour reality itself.",
}

# 120: Omega, The Void Heart (Boss)
MONSTERS["monster_120"] = {
    "id": 120,
    "name": "Omega, The Void Heart",
    "level": 45,
    "tier": "Boss",
    "hp": 25000,
    "atk": 250,
    "def": 150,
    "xp": 50000,
    "drops": [("void_heart", 100), ("magic_stone_flawless", 100), ("null_stone", 80)],
    "skills": [MONSTER_SKILLS["annihilate"], MONSTER_SKILLS["entropy_wave"], MONSTER_SKILLS["regenerate"]],
    "description": "The center of the void. To look upon it is to know the end.",
}

__all__ = ["MONSTERS"]
