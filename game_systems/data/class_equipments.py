"""
CLASS_EQUIPMENTS — Eldoria Quest (Class-specific item generator)
--------------------------------------------------------------
This script procedurally generates a complete item catalog for all
classes, rarities, and slots, balanced for the 999-stat system.

Total items generated: 5 Classes * 6 Rarities * 10 Slots = 300 items.
"""

from math import ceil

CLASSES = ["Warrior", "Mage", "Rogue", "Cleric", "Ranger"]

# 1. DEFINE SLOTS (Updated for Rogue Armor)
SLOTS = {
    "Warrior": [
        "sword",
        "greatsword",
        "mace",
        "shield",
        "helm",
        "heavy_armor",
        "heavy_gloves",
        "heavy_legs",
        "heavy_boots",
        "accessory",
    ],
    "Mage": [
        "staff",
        "tome",
        "orb",
        "hood",
        "robe",
        "gloves",
        "legs",
        "boots",
        "belt",
        "accessory",
    ],
    "Rogue": [
        "dagger",
        "offhand_dagger",
        "bow",
        "leather_hood",
        "rogue_armor",  # <--- CHANGED
        "medium_gloves",
        "medium_legs",
        "medium_boots",
        "belt",
        "accessory",
    ],
    "Cleric": [
        "mace",
        "shield",
        "staff",
        "tome",
        "miter",
        "vestments",
        "gloves",
        "legs",
        "boots",
        "accessory",
    ],
    "Ranger": [
        "bow",
        "dagger",
        "quiver",
        "leather_cap",
        "medium_armor",
        "medium_gloves",
        "medium_legs",
        "medium_boots",
        "belt",
        "accessory",
    ],
}

# 2. DEFINE RARITY DATA (Level Req, Power Multiplier, Name)
RARITY_DATA = {
    "Common": {"level": 1, "mult": 1.0, "name": "Novice's"},
    "Uncommon": {"level": 5, "mult": 1.5, "name": "Acolyte's"},
    "Rare": {"level": 10, "mult": 2.2, "name": "Veteran's"},
    "Epic": {"level": 20, "mult": 3.0, "name": "Master's"},
    "Legendary": {"level": 35, "mult": 4.0, "name": "Archon's"},
    "Mythical": {"level": 50, "mult": 5.5, "name": "God-Touched"},
}

# 3. DEFINE STAT BUDGETS (How to distribute 100% of stat points per slot)
#    (e.g., "sword" puts 70% of its points into STR, 30% into DEX)
STAT_BUDGETS = {
    # -- Weapons --
    "sword": {"STR": 0.7, "DEX": 0.3},
    "greatsword": {"STR": 1.0},
    "mace": {"STR": 0.8, "END": 0.2},
    "staff": {"MAG": 1.0},
    "tome": {"MAG": 0.8, "END": 0.2},
    "orb": {"MAG": 0.7, "MP_MULT": 0.3},  # 0.3 = 30% of budget as flat MP
    "dagger": {"DEX": 0.7, "AGI": 0.3},
    "offhand_dagger": {"DEX": 0.5, "AGI": 0.5},
    "bow": {"DEX": 0.9, "STR": 0.1},
    "quiver": {"DEX": 0.5, "AGI": 0.5},  # Quiver is an "off-hand"
    # -- Armor --
    "heavy_armor": {"END": 0.8, "STR": 0.2},
    "medium_armor": {"END": 0.5, "AGI": 0.5},
    "rogue_armor": {
        "AGI": 0.6,
        "END": 0.4,
    },  # <--- ADDED: Rogue Armor budget (High Agility)
    "robe": {"END": 0.5, "MAG": 0.5},
    "vestments": {"END": 0.6, "MAG": 0.4},
    # -- Helmets --
    "helm": {"END": 0.7, "STR": 0.3},
    "hood": {"MAG": 0.7, "AGI": 0.3},
    "leather_hood": {"DEX": 0.7, "AGI": 0.3},
    "miter": {"MAG": 0.7, "END": 0.3},
    "leather_cap": {"DEX": 0.6, "AGI": 0.4},
    # -- Gloves --
    "heavy_gloves": {"STR": 0.6, "END": 0.4},
    "medium_gloves": {"DEX": 0.6, "AGI": 0.4},
    "gloves": {"MAG": 0.6, "DEX": 0.4},  # Mage/Cleric gloves
    # -- Legs --
    "heavy_legs": {"END": 0.7, "STR": 0.3},
    "medium_legs": {"AGI": 0.7, "END": 0.3},
    "legs": {"AGI": 0.5, "MAG": 0.5},  # Mage/Cleric legs
    # -- Boots --
    "heavy_boots": {"END": 0.8, "STR": 0.2},
    "medium_boots": {"AGI": 0.8, "DEX": 0.2},
    "boots": {"AGI": 0.6, "MAG": 0.4},  # Mage/Cleric boots
    # -- Misc --
    "shield": {"END": 1.0},
    "belt": {
        "STR": 0.2,
        "END": 0.2,
        "DEX": 0.2,
        "AGI": 0.2,
        "MAG": 0.2,
    },  # Split budget
    "accessory": {"LCK": 1.0},  # Accessories are the primary source of LCK
}


# 4. THE GENERATION SCRIPT
CLASS_EQUIPMENTS = {}
eid = 1  # Use a simple counter for the unique key

print("--- Generating Class Equipment Catalog (300 items) ---")

for class_name in CLASSES:
    class_id = CLASSES.index(class_name) + 1

    for rarity_name, rarity_data in RARITY_DATA.items():
        level = rarity_data["level"]
        multiplier = rarity_data["mult"]
        name_prefix = rarity_data["name"]

        # Calculate the total stat points for this tier
        # Formula: (Level * Multiplier)
        total_stat_budget = ceil(level * multiplier)

        for slot in SLOTS[class_name]:
            # Get the stat distribution for this slot
            budget = STAT_BUDGETS.get(slot)
            if not budget:
                print(f"WARNING: No stat budget found for slot '{slot}'. Skipping.")
                continue

            # Generate the item name
            # e.g., "Veteran's Iron Heavy Armor"
            # e.g., "God-Touched Aether Staff"
            slot_name_parts = slot.split("_")
            if len(slot_name_parts) > 1:
                # "heavy_armor" -> "Iron Heavy Armor" (Use 1st part as descriptor)
                # "leather_hood" -> "Leather Hood"
                base_name = f"{slot_name_parts[0].title()} {slot_name_parts[1].title()}"
            else:
                # "sword" -> "Sword"
                base_name = slot.title()

            item_name = f"{name_prefix} {base_name}"

            # Calculate and distribute stats
            stats_bonus = {}
            for stat, percentage in budget.items():
                if stat == "MP_MULT":
                    # Special case: Add flat MP based on a multiplier of the budget
                    stats_bonus["MP"] = ceil(
                        total_stat_budget * percentage * 3
                    )  # 3 is an arbitrary value, feels good
                else:
                    # Normal stat
                    stats_bonus[stat] = ceil(total_stat_budget * percentage)

            # Generate a unique key_id
            key = f"c_{class_name.lower()}_{rarity_name.lower()}_{slot}"

            # Add the final item to the dictionary
            CLASS_EQUIPMENTS[key] = {
                "id": eid,
                "class": class_name,  # e.g., "Warrior"
                "name": item_name,
                "slot": slot,
                "rarity": rarity_name,
                "level_req": level,
                "stats_bonus": stats_bonus,
                "set": None,  # This system doesn't generate sets, but you could add them
                "description": f"A {rarity_name.lower()} {slot.replace('_', ' ')} forged for a {class_name}.",
            }

            eid += 1

print(f"--- Generated {len(CLASS_EQUIPMENTS)} class-specific items. ---")

# We no longer need to export CLASS_SETS
__all__ = ["CLASS_EQUIPMENTS"]
