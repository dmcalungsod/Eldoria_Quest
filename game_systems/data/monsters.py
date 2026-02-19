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

    description = (
        f"In the whispering groves of the Shattered Veil, the {name} prowls. "
        f"At level {level} it is considered {tier.lower()} within the Adventurer's Dawn."
    )

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

__all__ = ["MONSTERS"]
