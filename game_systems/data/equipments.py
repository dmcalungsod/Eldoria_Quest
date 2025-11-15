"""
EQUIPMENTS — Eldoria Quest (General equipment pool)
---------------------------------------------------
Programmatically generates 50 equipment items (weapons, armor, accessories).
Stats: STR, END, DEX, AGI, MAG, LCK
"""

# --- THIS IS THE FIX (Part 1) ---
from math import ceil

# --- END OF FIX ---

WEAPON_POOL = [
    "Rusty Longsword",
    "Worn Shortbow",
    "Oak Staff",
    "Stalwart Mace",
    "Huntsman's Dagger",
]
ARMOR_POOL = [
    "Leather Jerkin",
    "Studded Coat",
    "Reinforced Gloves",
    "Travel Boots",
    "Woolen Trousers",
]
ACCESSORY_POOL = [
    "Copper Ring",
    "Braided Cord",
    "Feather Charm",
    "Hunter's Badge",
    "Apprentice Brooch",
]

RARITY_ORDER = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythical"]

EQUIPMENTS = {}
id_counter = 1
for i in range(50):
    # choose category cyclically
    slot = "weapon" if i % 3 == 0 else "armor" if i % 3 == 1 else "accessory"
    name_pool = (
        WEAPON_POOL
        if slot == "weapon"
        else ARMOR_POOL if slot == "armor" else ACCESSORY_POOL
    )
    base_name = name_pool[i % len(name_pool)]
    # rarity distribution skewed to common/uncommon for beginner
    if i < 25:
        rarity = RARITY_ORDER[0] if i % 2 == 0 else RARITY_ORDER[1]
    elif i < 40:
        rarity = RARITY_ORDER[2]
    else:
        rarity = RARITY_ORDER[3] if i < 48 else RARITY_ORDER[4]

    level_req = min(30, 1 + i // 2)
    # stat formula: rarer/higher index --> better stats
    rank_val = RARITY_ORDER.index(rarity) + 1

    # --- THIS IS THE FIX (Part 2) ---
    # build stats bonus (changed all 'floor' to 'ceil')
    if slot == "weapon":
        stats_bonus = {
            "STR": ceil(level_req * 0.4 * rank_val),
            "DEX": ceil(level_req * 0.15 * rank_val),
        }
    elif slot == "armor":
        stats_bonus = {
            "END": ceil(level_req * 0.35 * rank_val),
            "AGI": ceil(level_req * 0.25 * rank_val),
        }
    else:
        stats_bonus = {
            "LCK": ceil(level_req * 0.2 * rank_val),
            "MAG": ceil(level_req * 0.1 * rank_val),
        }
    # --- END OF FIX ---

    name = f"{base_name} {'+' + str(rank_val) if rank_val>1 else ''}".strip()
    EQUIPMENTS[f"eq_{id_counter:03d}"] = {
        "id": id_counter,
        "name": name,
        "slot": slot,
        "rarity": rarity,
        "level_req": level_req,
        "stats_bonus": stats_bonus,
        "description": f"A {rarity.lower()} {slot} named '{name}'. Worn by fledgling adventurers of the glade.",
    }
    id_counter += 1

__all__ = ["EQUIPMENTS"]
