"""
MONSTERS (forest beginner zone) — Eldoria Quest
----------------------------------------------
Programmatically generates 50 forest-themed monsters (levels 1–30).
Tiers: Normal, Elite, Boss (3 bosses in this region).
Each monster entry:
{
  "id": int,
  "name": str,
  "level": int,
  "tier": "Normal"|"Elite"|"Boss",
  "hp": int,
  "atk": int,
  "def": int,
  "xp": int,
  "drops": [("item_key", chance_percent), ...],
  "description": str
}
Tone: high-fantasy, bookish.
"""

from math import ceil

NAME_POOL = [
    "Verdant Slime", "Glimmer Slime", "Goblin Grunt", "Goblin Scout", "Bramble Goblin",
    "Forest Wolf Pup", "Hollow Spiderling", "Thicket Spider", "Fen Wisp", "Briar Hound",
    "Mossback Tortoise", "Vineling", "Burbling Sprite", "Rookwood Shade", "Gloam Hare",
    "Young Treant", "Feral Stag", "Sapling Ent", "Ragged Urch", "Ravaged Boar",
    "Pine Wight", "Marsh Crawler", "Sporeling", "Ridge Wolf", "Stormling",
    "Thornback Boar", "Mire Lurker", "Duskling", "Wisp-Sentinel", "Gnarled Brute",
    "Shade Warden", "Fen Revenant", "Bramble King", "Glade Empress", "Sylvan Herald",
    "Elder Treant", "Abyssal Wolf", "Blight Stag", "Wretched Entling", "Nightbloom"
]

# We'll deterministically produce 50 monsters, mapping names in order.
MONSTERS = {}
for idx in range(1, 51):
    name = NAME_POOL[(idx - 1) % len(NAME_POOL)]
    # level progression: more monsters near early levels, some up to 30
    # Use repeated pattern: 1..30 then clamp
    level = min(30, ceil(idx * 0.6))  # spreads across 1..30 for 50 entries
    # Tier rules: bosses at specific indices (3 bosses), elites when level >= 18 or idx % 7 == 0
    if idx in (17, 34, 50):  # three designated boss positions for beginner forest
        tier = "Boss"
    elif level >= 18 or idx % 7 == 0:
        tier = "Elite"
    else:
        tier = "Normal"

    # Base formulas — tuned for beginner forest (easy)
    hp = 30 + level * (8 if tier == "Normal" else 14 if tier == "Elite" else 40)
    atk = 3 + level // (1 if tier == "Normal" else 1 if tier == "Elite" else 1)
    defense = 1 + (level // (2 if tier == "Normal" else 1))
    xp = int((level * 8) * (1.0 if tier == "Normal" else 2.5 if tier == "Elite" else 10.0))

    drops = []
    # common drops
    drops.append(("forest_herb", 40))
    drops.append(("beast_hide", 20 if tier != "Boss" else 60))
    # small chance for set-specific placeholder drop on elites/bosses
    if tier == "Elite":
        drops.append(("elite_shard", 8))
    if tier == "Boss":
        drops.append(("boss_talon", 30))
        drops.append(("forest_relic_fragment", 20))

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
        "drops": drops,
        "description": description
    }

# Human-friendly export list
__all__ = ["MONSTERS"]
