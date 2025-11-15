"""
MONSTERS (forest beginner zone) — Eldoria Quest
----------------------------------------------
Generates 50 forest-themed monsters (levels 1–30).
Drops are now procedurally added based on monster level, tier, and name
to align with the Danmachi-style (Quality + Size) economy.
"""

from math import ceil

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
    if idx in (17, 34, 50):  # Three designated boss positions
        tier = "Boss"
    elif level >= 18 or idx % 7 == 0:
        tier = "Elite"
    else:
        tier = "Normal"

    # --- Base Stats ---
    hp = 30 + level * (8 if tier == "Normal" else 14 if tier == "Elite" else 40)
    atk = 3 + level // (1 if tier == "Normal" else 1 if tier == "Elite" else 1)
    defense = 1 + (level // (2 if tier == "Normal" else 1))
    xp = int(
        (level * 8) * (1.0 if tier == "Normal" else 2.5 if tier == "Elite" else 10.0)
    )

    # --- New Thematic Drop Logic ---
    drops = []

    # 1. Magic Stone (Quality/Size based on Level and Tier)
    if tier == "Boss":
        drops.append(("magic_stone_large", 100))  # Guaranteed
        drops.append(("magic_stone_flawless", 15))  # Small chance for flawless
    elif tier == "Elite":
        drops.append(("magic_stone_medium", 80))
        drops.append(("magic_stone_large", 10))
    else:  # Normal Tier
        if level < 5:
            drops.append(("magic_stone_fragment", 75))
        elif level < 15:
            drops.append(("magic_stone_small", 80))
        else:
            drops.append(("magic_stone_medium", 50))  # High-level "Normal" mobs

    # 2. Monster-Specific Materials
    if "Slime" in name:
        drops.append(("slime_gel", 40))
    elif "Goblin" in name:
        drops.append(("goblin_ear", 35))
    elif "Wolf" in name or "Hound" in name:
        drops.append(("wolf_fang", 25))
    elif "Spider" in name:
        drops.append(("spider_silk", 30))
    elif "Boar" in name:
        drops.append(("boar_tusk", 20))
    elif "Treant" in name or "Ent" in name:
        drops.append(("treant_branch", 15))

    # Boss Drop
    if tier == "Boss":
        drops.append(("boss_talon", 50))

    # --- Description ---
    description = (
        f"In the whispering groves of the Shattered Veil, the {name} prowls. "
        f"At level {level} it is considered {tier.lower()} within the Adventurer's Dawn."
    )

    MONSTERS[f"monster_{idx:03d}"] = {
        "id": idx,
        "name": name,
        "level": level,
        "tier": tier,
        "hp": hp,
        "atk": atk,
        "def": defense,
        "xp": xp,
        "drops": drops,  # This list now contains all loot
        "description": description,
    }

__all__ = ["MONSTERS"]
